#!/usr/bin/env python3
"""MCP Workbench Unified Server
Single-port server that serves static files (HTTP) and MCP proxy (WebSocket).

Usage: python3 server.py [port]
"""
import asyncio
import json
import mimetypes
import os
import sys
import uuid
from urllib.parse import urlparse

import websockets
from websockets.server import WebSocketServerProtocol

STATIC_DIR = os.path.join(os.path.dirname(__file__), "dist")
ALLOWED_COMMANDS = {"npx", "node", "python3"}
ALLOWED_PACKAGES = {"@modelcontextprotocol/"}

def log(session: str, msg: str):
    print(f"[{session}] {msg}", flush=True)

# ─── Session Recording ────────────────────────────────────────────
class SessionRecorder:
    """Records all JSON-RPC traffic for replay/debugging."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.entries: list[dict] = []
        self.started_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()

    def record(self, direction: str, payload: dict):
        self.entries.append({"ts": __import__("time").time(), "direction": direction, "payload": payload})

    def save(self, command: str = ""):
        try:
            os.makedirs("sessions", exist_ok=True)
            path = f"sessions/{self.session_id}.json"
            with open(path, "w") as f:
                json.dump({
                    "session_id": self.session_id, "started_at": self.started_at,
                    "command": command, "entries": self.entries,
                }, f, indent=2)
            return path
        except Exception as e:
            print(f"[recorder] Failed to save: {e}")
            return None

# ─── Metrics ──────────────────────────────────────────────────────
class ProxyMetrics:
    def __init__(self):
        self.connections_total = 0
        self.connections_success = 0
        self.connections_failed = 0
        self.init_latencies: list[float] = []
        self.tool_counts: list[int] = []
        self.errors: list[str] = []

    def record_connection(self, success: bool):
        self.connections_total += 1
        (self.connections_success if success else self.connections_failed).__add__(1)
        if success:
            self.connections_success += 1
        else:
            self.connections_failed += 1

    def record_init_latency(self, latency_ms: float):
        self.init_latencies.append(latency_ms)

    def record_tool_count(self, count: int):
        self.tool_counts.append(count)

    def record_error(self, error: str):
        self.errors.append(error)

    def summary(self) -> dict:
        import statistics
        return {
            "connections": {
                "total": self.connections_total,
                "success": self.connections_success,
                "failed": self.connections_failed,
                "success_rate_pct": round(self.connections_success / max(self.connections_total, 1) * 100, 2),
            },
            "init_latency_ms": {
                "count": len(self.init_latencies),
                "avg": round(statistics.mean(self.init_latencies), 2) if self.init_latencies else 0,
                "min": round(min(self.init_latencies), 2) if self.init_latencies else 0,
                "max": round(max(self.init_latencies), 2) if self.init_latencies else 0,
            },
            "tool_discovery": {
                "count": len(self.tool_counts),
                "avg": round(statistics.mean(self.tool_counts), 2) if self.tool_counts else 0,
                "max": max(self.tool_counts) if self.tool_counts else 0,
            },
            "errors_last_10": self.errors[-10:],
        }

metrics = ProxyMetrics()

def validate_command(command: str, args: list) -> str | None:
    if command not in ALLOWED_COMMANDS:
        return f"Command '{command}' not allowed"
    if command == "npx":
        for arg in args:
            if isinstance(arg, str) and arg.startswith("-"):
                continue
            if any(str(arg).startswith(pkg) for pkg in ALLOWED_PACKAGES):
                return None
        return "Only @modelcontextprotocol/* packages allowed"
    return None

async def spawn_mcp(command: str, args: list, env: dict | None = None):
    merged_env = {**dict(os.environ), **(env or {})}
    merged_env.setdefault("PYTHONUNBUFFERED", "1")
    merged_env.setdefault("NODE_NO_WARNINGS", "1")
    proc = await asyncio.create_subprocess_exec(
        command, *[str(a) for a in args],
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=merged_env,
    )
    return proc

async def read_jsonrpc_lines(stream):
    buffer = b""
    while True:
        chunk = await stream.read(4096)
        if not chunk:
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
                except json.JSONDecodeError:
                    pass

async def write_jsonrpc(proc, msg: dict):
    data = json.dumps(msg).encode("utf-8") + b"\n"
    proc.stdin.write(data)
    await proc.stdin.drain()

async def drain_stderr(proc, session: str):
    while True:
        line = await proc.stderr.readline()
        if not line:
            break
        text = line.decode("utf-8", errors="replace").rstrip()
        if text:
            log(session, f"[stderr] {text}")

async def handle_mcp_ws(websocket: WebSocketServerProtocol):
    session = str(uuid.uuid4())[:8]
    recorder = SessionRecorder(session)
    init_start = __import__("time").time()
    conn_success = False
    log(session, f"MCP client connected from {websocket.remote_address}")
    proc = None
    stderr_task = None
    try:
        raw = await asyncio.wait_for(websocket.recv(), timeout=30.0)
        init = json.loads(raw)
        command = init.get("command", "npx")
        args = init.get("args", [])
        env = init.get("env")
        recorder.save(command=f"{command} {' '.join(str(a) for a in args)}")

        log(session, f"Spawning: {command} {' '.join(str(a) for a in args)}")
        err = validate_command(command, args)
        if err:
            log(session, f"BLOCKED: {err}")
            await websocket.send(json.dumps({"type": "error", "message": err}))
            metrics.record_connection(False)
            metrics.record_error(err)
            return
        proc = await spawn_mcp(command, args, env)
        log(session, f"PID {proc.pid} started")
        stderr_task = asyncio.create_task(drain_stderr(proc, session))

        init_req = {
            "jsonrpc": "2.0", "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-workbench", "version": "0.1.0"}
            }
        }
        await write_jsonrpc(proc, init_req)
        log(session, "Sent initialize")
        recorder.record("client->server", init_req)

        async def mcp_to_ws():
            tool_count = 0
            async for msg in read_jsonrpc_lines(proc.stdout):
                recorder.record("server->client", msg)
                log(session, f"stdout -> {json.dumps(msg)[:160]}")
                # Track init latency
                if msg.get("id") == 0 and "result" in msg:
                    latency = (__import__("time").time() - init_start) * 1000
                    metrics.record_init_latency(latency)
                    log(session, f"Init latency: {latency:.0f}ms")
                # Track tool count
                if msg.get("id") == 1 and "result" in msg:
                    tools = msg.get("result", {}).get("tools", [])
                    tool_count = len(tools)
                    metrics.record_tool_count(tool_count)
                try:
                    await websocket.send(json.dumps({"type": "message", "payload": msg}))
                except Exception:
                    break
            log(session, "MCP stdout closed")

        async def ws_to_mcp():
            async for raw_ws in websocket:
                try:
                    data = json.loads(raw_ws)
                    recorder.record("client->server", data)
                    log(session, f"ws -> {json.dumps(data)[:160]}")
                    await write_jsonrpc(proc, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"type": "error", "message": "Invalid JSON"}))
            log(session, "WebSocket client closed")

        mcp_task = asyncio.create_task(mcp_to_ws())
        ws_task = asyncio.create_task(ws_to_mcp())
        done, pending = await asyncio.wait([mcp_task, ws_task], return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        conn_success = True

    except asyncio.TimeoutError:
        await websocket.send(json.dumps({"type": "error", "message": "Timeout waiting for init"}))
        metrics.record_error("timeout")
    except websockets.exceptions.ConnectionClosed:
        log(session, "WebSocket closed")
        conn_success = True
    except Exception as e:
        log(session, f"Error: {type(e).__name__}: {e}")
        metrics.record_error(f"{type(e).__name__}: {e}")
    finally:
        log(session, "Cleaning up...")
        recorder.save()
        metrics.record_connection(conn_success)
        if stderr_task:
            stderr_task.cancel()
        if proc:
            try:
                proc.kill()
                await proc.wait()
                log(session, f"PID {proc.pid} terminated")
            except Exception:
                pass
        log(session, "Disconnected")

async def handle_http(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        request_line = await reader.readline()
        if not request_line:
            return
        method, path, _ = request_line.decode("utf-8").strip().split(" ", 2)
        # Discard headers
        while True:
            line = await reader.readline()
            if line == b"\r\n" or line == b"\n":
                break

        # API endpoints
        if path == "/api/health":
            body = json.dumps({"status": "ok", "timestamp": __import__("time").time()}).encode("utf-8")
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
            await writer.drain()
            return

        if path == "/api/metrics":
            body = json.dumps(metrics.summary(), indent=2).encode("utf-8")
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
            await writer.drain()
            return

        if path == "/api/sessions":
            try:
                sessions = []
                if os.path.isdir("sessions"):
                    for fn in sorted(os.listdir("sessions"))[:20]:
                        fp = os.path.join("sessions", fn)
                        with open(fp) as f:
                            sessions.append(json.load(f))
                body = json.dumps({"count": len(sessions), "sessions": sessions}, indent=2).encode("utf-8")
            except Exception as e:
                body = json.dumps({"error": str(e)}).encode("utf-8")
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
            await writer.drain()
            return

        parsed = urlparse(path)
        filepath = os.path.join(STATIC_DIR, parsed.path.lstrip("/"))
        if os.path.isdir(filepath):
            filepath = os.path.join(filepath, "index.html")
        if not os.path.exists(filepath):
            filepath = os.path.join(STATIC_DIR, "404.html")
            if not os.path.exists(filepath):
                writer.write(b"HTTP/1.1 404 Not Found\r\nContent-Length: 9\r\n\r\nNot Found")
                await writer.drain()
                return

        content_type, _ = mimetypes.guess_type(filepath)
        content_type = content_type or "application/octet-stream"
        with open(filepath, "rb") as f:
            body = f.read()

        writer.write(
            f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode("utf-8")
            + body
        )
        await writer.drain()
    except Exception as e:
        print(f"HTTP error: {e}")
    finally:
        writer.close()

async def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3456
    ws_port = port + 1

    # Start WebSocket server
    ws_server = await websockets.serve(handle_mcp_ws, "0.0.0.0", ws_port)
    log("server", f"MCP WebSocket proxy on ws://0.0.0.0:{ws_port}")

    # Start HTTP server for static files
    http_server = await asyncio.start_server(handle_http, "0.0.0.0", port)
    log("server", f"HTTP server on http://0.0.0.0:{port}")
    log("server", f"Serving static files from {STATIC_DIR}")

    async with http_server:
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
