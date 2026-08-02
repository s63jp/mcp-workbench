#!/usr/bin/env python3
"""MCP Workbench Server — aiohttp-based, single port for HTTP + WebSocket.

Usage: python3 server.py [port]
"""
import asyncio
import json
import mimetypes
import os
import sys
import uuid

from aiohttp import web, WSMsgType

STATIC_DIR = os.path.join(os.path.dirname(__file__), "dist")
ALLOWED_COMMANDS = {"npx", "node", "python3"}
ALLOWED_PACKAGES = {"@modelcontextprotocol/"}

def log(session: str, msg: str):
    print(f"[{session}] {msg}", flush=True)

# ─── Session Recording ────────────────────────────────────────────
class SessionRecorder:
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
        self.connections_total = 0; self.connections_success = 0; self.connections_failed = 0
        self.init_latencies: list[float] = []; self.tool_counts: list[int] = []; self.errors: list[str] = []

    def record_connection(self, success: bool):
        self.connections_total += 1
        if success: self.connections_success += 1
        else: self.connections_failed += 1

    def record_init_latency(self, latency_ms: float): self.init_latencies.append(latency_ms)
    def record_tool_count(self, count: int): self.tool_counts.append(count)
    def record_error(self, error: str): self.errors.append(error)

    def summary(self) -> dict:
        import statistics
        return {
            "connections": {"total": self.connections_total, "success": self.connections_success, "failed": self.connections_failed, "success_rate_pct": round(self.connections_success / max(self.connections_total, 1) * 100, 2)},
            "init_latency_ms": {"count": len(self.init_latencies), "avg": round(statistics.mean(self.init_latencies), 2) if self.init_latencies else 0, "min": round(min(self.init_latencies), 2) if self.init_latencies else 0, "max": round(max(self.init_latencies), 2) if self.init_latencies else 0},
            "tool_discovery": {"count": len(self.tool_counts), "avg": round(statistics.mean(self.tool_counts), 2) if self.tool_counts else 0, "max": max(self.tool_counts) if self.tool_counts else 0},
            "errors_last_10": self.errors[-10:],
        }

metrics = ProxyMetrics()

# ─── Security ─────────────────────────────────────────────────────
def validate_command(command: str, args: list) -> str | None:
    if command not in ALLOWED_COMMANDS:
        return f"Command '{command}' not allowed"
    if command == "npx":
        for arg in args:
            if isinstance(arg, str) and arg.startswith("-"): continue
            if any(str(arg).startswith(pkg) for pkg in ALLOWED_PACKAGES): return None
        return "Only @modelcontextprotocol/* packages allowed"
    return None

# ─── MCP Process Management ───────────────────────────────────────
async def spawn_mcp(command: str, args: list, env: dict | None = None):
    merged_env = {**dict(os.environ), **(env or {})}
    merged_env.setdefault("PYTHONUNBUFFERED", "1")
    merged_env.setdefault("NODE_NO_WARNINGS", "1")
    return await asyncio.create_subprocess_exec(
        command, *[str(a) for a in args],
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        env=merged_env,
    )

async def read_jsonrpc_lines(stream):
    buffer = b""
    while True:
        chunk = await stream.read(4096)
        if not chunk:
            if buffer.strip():
                try: yield json.loads(buffer.decode("utf-8").strip())
                except json.JSONDecodeError: pass
            break
        buffer += chunk
        while b"\n" in buffer:
            line, _, buffer = buffer.partition(b"\n")
            if line.strip():
                try: yield json.loads(line.decode("utf-8").strip())
                except json.JSONDecodeError: pass

async def write_jsonrpc(proc, msg: dict):
    proc.stdin.write(json.dumps(msg).encode("utf-8") + b"\n")
    await proc.stdin.drain()

async def drain_stderr(proc, session: str):
    while True:
        line = await proc.stderr.readline()
        if not line: break
        text = line.decode("utf-8", errors="replace").rstrip()
        if text: log(session, f"[stderr] {text}")

# ─── Active Process Tracking ──────────────────────────────────────
active_processes: dict[str, asyncio.subprocess.Process] = {}

async def cleanup_orphaned_processes():
    """Kill any lingering MCP processes from previous sessions."""
    import signal
    import psutil
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = proc.info["cmdline"] or []
            if any("@modelcontextprotocol" in str(c) for c in cmdline):
                os.kill(proc.info["pid"], signal.SIGKILL)
                log("cleanup", f"Killed orphaned MCP process {proc.info['pid']}")
        except (psutil.NoSuchProcess, PermissionError, ProcessLookupError):
            pass

def track_process(session: str, proc):
    active_processes[session] = proc

def untrack_process(session: str):
    active_processes.pop(session, None)

async def kill_all_active():
    """Kill all active MCP processes on shutdown."""
    for session, proc in list(active_processes.items()):
        try:
            proc.kill()
            await asyncio.wait_for(proc.wait(), timeout=5.0)
            log("shutdown", f"Killed PID {proc.pid}")
        except Exception:
            pass
    active_processes.clear()
async def api_health(request):
    return web.json_response({"status": "ok", "timestamp": __import__("time").time()})

async def api_metrics(request):
    return web.json_response(metrics.summary())

async def api_sessions(request):
    sessions = []
    if os.path.isdir("sessions"):
        for fn in sorted(os.listdir("sessions"))[:20]:
            with open(os.path.join("sessions", fn)) as f: sessions.append(json.load(f))
    return web.json_response({"count": len(sessions), "sessions": sessions})

async def static_handler(request):
    path = request.match_info.get("path", "")
    filepath = os.path.join(STATIC_DIR, path.lstrip("/"))
    if os.path.isdir(filepath): filepath = os.path.join(filepath, "index.html")
    if not os.path.exists(filepath): filepath = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(filepath): return web.Response(status=404, text="Not Found")

    content_type, _ = mimetypes.guess_type(filepath)
    content_type = content_type or "application/octet-stream"
    with open(filepath, "rb") as f:
        return web.Response(body=f.read(), content_type=content_type)

# ─── WebSocket MCP Handler ──────────────────────────────────────
async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    session = str(uuid.uuid4())[:8]
    recorder = SessionRecorder(session)
    init_start = __import__("time").time()
    conn_success = False
    log(session, f"MCP client connected from {request.remote}")
    proc = None; stderr_task = None

    try:
        raw = await asyncio.wait_for(ws.receive_str(), timeout=30.0)
        init = json.loads(raw)
        command = init.get("command", "npx"); args = init.get("args", []); env = init.get("env")

        log(session, f"Spawning: {command} {' '.join(str(a) for a in args)}")
        err = validate_command(command, args)
        if err:
            log(session, f"BLOCKED: {err}")
            await ws.send_str(json.dumps({"type": "error", "message": err}))
            metrics.record_connection(False); metrics.record_error(err); return ws

        proc = await spawn_mcp(command, args, env)
        track_process(session, proc)
        log(session, f"PID {proc.pid} started")
        stderr_task = asyncio.create_task(drain_stderr(proc, session))

        init_req = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "mcp-workbench", "version": "0.1.0"}}}
        await write_jsonrpc(proc, init_req)
        log(session, "Sent initialize")
        recorder.record("client->server", init_req)

        async def mcp_to_ws():
            async for msg in read_jsonrpc_lines(proc.stdout):
                recorder.record("server->client", msg)
                log(session, f"stdout -> {json.dumps(msg)[:160]}")
                if msg.get("id") == 0 and "result" in msg:
                    metrics.record_init_latency((__import__("time").time() - init_start) * 1000)
                if msg.get("id") == 1 and "result" in msg:
                    metrics.record_tool_count(len(msg.get("result", {}).get("tools", [])))
                if not ws.closed: await ws.send_str(json.dumps({"type": "message", "payload": msg}))
            log(session, "MCP stdout closed")

        async def ws_to_mcp():
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        recorder.record("client->server", data)
                        log(session, f"ws -> {json.dumps(data)[:160]}")
                        await write_jsonrpc(proc, data)
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({"type": "error", "message": "Invalid JSON"}))
                elif msg.type == WSMsgType.ERROR:
                    log(session, f"WebSocket error: {ws.exception()}")
            log(session, "WebSocket client closed")

        mcp_task = asyncio.create_task(mcp_to_ws())
        ws_task = asyncio.create_task(ws_to_mcp())
        done, pending = await asyncio.wait([mcp_task, ws_task], return_when=asyncio.FIRST_COMPLETED)
        for task in pending: task.cancel()
        conn_success = True

    except asyncio.TimeoutError:
        if not ws.closed: await ws.send_str(json.dumps({"type": "error", "message": "Timeout waiting for init"}))
        metrics.record_error("timeout")
    except Exception as e:
        log(session, f"Error: {type(e).__name__}: {e}")
        metrics.record_error(f"{type(e).__name__}: {e}")
    finally:
        log(session, "Cleaning up...")
        recorder.save(); metrics.record_connection(conn_success)
        if stderr_task: stderr_task.cancel()
        if proc:
            try:
                proc.kill()
                await asyncio.wait_for(proc.wait(), timeout=5.0)
                log(session, f"PID {proc.pid} terminated")
            except asyncio.TimeoutError:
                log(session, f"PID {proc.pid} kill timeout — forcing SIGKILL")
                try: os.kill(proc.pid, signal.SIGKILL)
                except ProcessLookupError: pass
            except Exception: pass
            finally:
                untrack_process(session)
        log(session, "Disconnected")
        if not ws.closed: await ws.close()

    return ws

# ─── Main ─────────────────────────────────────────────────────────
async def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3456
    app = web.Application()
    app.router.add_get("/api/health", api_health)
    app.router.add_get("/api/metrics", api_metrics)
    app.router.add_get("/api/sessions", api_sessions)
    app.router.add_get("/ws", ws_handler)
    app.router.add_get("/{path:.*}", static_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log("server", f"MCP Workbench on http://0.0.0.0:{port} (HTTP + WebSocket /ws)")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
