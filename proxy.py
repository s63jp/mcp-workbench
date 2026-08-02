#!/usr/bin/env python3
"""MCP Workbench Proxy Server — Real stdio-to-WebSocket bridge.

Implements proper MCP stdio transport framing:
- Each message is a single-line JSON object terminated by \n
- Reads from stdout, writes to stdin

Usage: python3 proxy.py [port]
"""
import asyncio
import json
import subprocess
import sys
import uuid
import os

import websockets
from websockets.server import WebSocketServerProtocol

# ─── Session Logger ───────────────────────────────────────────────
class SessionLogger:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logs: list[dict] = []
        self.started_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()

    def append(self, direction: str, payload: dict):
        self.logs.append({
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "direction": direction,
            "payload": payload,
        })

    def to_json(self) -> dict:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "entries": self.logs,
        }

# ─── Security: Allowed Commands ───────────────────────────────────
ALLOWED_COMMANDS = {"npx", "node", "python3"}
ALLOWED_PACKAGES = {"@modelcontextprotocol/"}

# ─── Session Storage ──────────────────────────────────────────────
active_sessions: dict[str, SessionLogger] = {}

def validate_command(command: str, args: list[str]) -> str | None:
    """Validate that the command is safe to execute. Returns error message or None."""
    if command not in ALLOWED_COMMANDS:
        return f"Command '{command}' is not allowed. Allowed: {ALLOWED_COMMANDS}"
    if command == "npx":
        for arg in args:
            if arg.startswith("-"):
                continue
            if any(arg.startswith(pkg) for pkg in ALLOWED_PACKAGES):
                return None
        return "Only @modelcontextprotocol/* packages are allowed with npx"
    if command in ("node", "python3"):
        return None
    return None

# ─── Logging ──────────────────────────────────────────────────────
def log(session: str, msg: str):
    print(f"[{session}] {msg}", flush=True)

# ─── MCP Process Management ───────────────────────────────────────
async def spawn_mcp(command: str, args: list[str], env: dict | None = None) -> asyncio.subprocess.Process:
    """Spawn MCP server with unbuffered stdio."""
    merged_env = {**dict(os.environ), **(env or {})}
    # Force unbuffered output so we get real-time lines
    merged_env["PYTHONUNBUFFERED"] = "1"
    merged_env["NODE_NO_WARNINGS"] = "1"
    proc = await asyncio.create_subprocess_exec(
        command, *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=merged_env,
    )
    return proc

async def read_jsonrpc_lines(stream):
    """Yield complete JSON-RPC messages from an asyncio stream."""
    buffer = b""
    while True:
        chunk = await stream.read(4096)
        if not chunk:
            # Stream closed — flush remaining buffer
            if buffer.strip():
                try:
                    yield json.loads(buffer.decode("utf-8").strip())
                except json.JSONDecodeError:
                    pass
            break
        buffer += chunk
        while b"\n" in buffer:
            line, _, buffer = buffer.partition(b"\n")
            if line.strip():
                try:
                    yield json.loads(line.decode("utf-8").strip())
                except json.JSONDecodeError as e:
                    log("proxy", f"JSON decode error: {e} for line: {line[:200]}")

async def write_jsonrpc(proc: asyncio.subprocess.Process, msg: dict):
    """Send a JSON-RPC message to MCP server stdin."""
    data = json.dumps(msg).encode("utf-8") + b"\n"
    proc.stdin.write(data)
    await proc.stdin.drain()

async def drain_stderr(proc: asyncio.subprocess.Process, session: str):
    """Forward stderr to logs for debugging."""
    while True:
        line = await proc.stderr.readline()
        if not line:
            break
        text = line.decode("utf-8", errors="replace").rstrip()
        if text:
            log(session, f"[stderr] {text}")

# ─── WebSocket Handler ────────────────────────────────────────────
async def handle_client(websocket: WebSocketServerProtocol, path: str):
    session = str(uuid.uuid4())[:8]
    peer = websocket.remote_address
    log(session, f"Client connected from {peer}")

    proc: asyncio.subprocess.Process | None = None
    reader_task: asyncio.Task | None = None
    stderr_task: asyncio.Task | None = None

    try:
        # ── 1. Receive init message from client ──────────────────
        raw = await asyncio.wait_for(websocket.recv(), timeout=30.0)
        init = json.loads(raw)
        command = init.get("command", "npx")
        args = init.get("args", [])
        env = init.get("env")

        log(session, f"Spawning: {command} {' '.join(args)}")
        err = validate_command(command, args)
        if err:
            log(session, f"SECURITY BLOCKED: {err}")
            await websocket.send(json.dumps({"error": f"Security: {err}"}))
            return
        proc = await spawn_mcp(command, args, env)
        log(session, f"PID {proc.pid} started")

        # Start stderr reader for debugging
        stderr_task = asyncio.create_task(drain_stderr(proc, session))

        # ── 2. Send initialize request ────────────────────────────
        init_request = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-workbench", "version": "0.1.0"}
            }
        }
        await write_jsonrpc(proc, init_request)
        log(session, "Sent initialize request")

        # ── 3. Read initialize response ───────────────────────────
        response = None
        async for msg in read_jsonrpc_lines(proc.stdout):
            log(session, f"stdout -> {json.dumps(msg)[:200]}")
            await websocket.send(json.dumps({"direction": "server->client", "payload": msg}))
            if msg.get("id") == 0:
                response = msg
                break

        if response is None:
            await websocket.send(json.dumps({"error": "No initialize response from MCP server"}))
            return

        log(session, "Received initialize response")

        # Send notifications/initialized
        await write_jsonrpc(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        log(session, "Sent notifications/initialized")

        # ── 4. List tools ─────────────────────────────────────────
        await write_jsonrpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        log(session, "Sent tools/list")

        tools_response = None
        async for msg in read_jsonrpc_lines(proc.stdout):
            log(session, f"stdout -> {json.dumps(msg)[:200]}")
            await websocket.send(json.dumps({"direction": "server->client", "payload": msg}))
            if msg.get("id") == 1:
                tools_response = msg
                break

        if tools_response:
            log(session, f"Discovered {len(tools_response.get('result', {}).get('tools', []))} tools")

        # ── 5. Bidirectional relay ────────────────────────────────
        async def ws_to_mcp():
            async for raw_ws in websocket:
                try:
                    data = json.loads(raw_ws)
                    log(session, f"ws -> {json.dumps(data)[:200]}")
                    await write_jsonrpc(proc, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"error": "Invalid JSON from client"}))

        async def mcp_to_ws():
            async for msg in read_jsonrpc_lines(proc.stdout):
                await websocket.send(json.dumps({"direction": "server->client", "payload": msg}))
            log(session, "MCP stdout closed (process exited?)")

        # Run both directions concurrently
        ws_task = asyncio.create_task(ws_to_mcp())
        mcp_task = asyncio.create_task(mcp_to_ws())

        done, pending = await asyncio.wait(
            [ws_task, mcp_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

    except asyncio.TimeoutError:
        await websocket.send(json.dumps({"error": "Timeout waiting for init message"}))
    except websockets.exceptions.ConnectionClosed:
        log(session, "WebSocket closed by client")
    except Exception as e:
        log(session, f"Error: {type(e).__name__}: {e}")
        try:
            await websocket.send(json.dumps({"error": f"{type(e).__name__}: {e}"}))
        except Exception:
            pass
    finally:
        log(session, "Cleaning up...")
        if stderr_task:
            stderr_task.cancel()
        if proc:
            try:
                proc.kill()
                await proc.wait()
                log(session, f"Process {proc.pid} terminated")
            except Exception:
                pass
        log(session, "Disconnected")

# ─── Main ─────────────────────────────────────────────────────────
async def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    log("proxy", f"MCP Workbench Proxy starting on ws://localhost:{port}")
    async with websockets.serve(handle_client, "localhost", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
