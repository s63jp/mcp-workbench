#!/usr/bin/env python3
"""MCP Workbench Server v2 — Session Manager + Structured Logging.

Usage: python3 server.py [port]
"""
import asyncio
import json
import mimetypes
import os
import signal
import sys
import time
import uuid

import psutil
from aiohttp import web, WSMsgType

STATIC_DIR = os.path.join(os.path.dirname(__file__), "dist")
ALLOWED_COMMANDS = {"npx", "node", "python3"}
ALLOWED_PACKAGES = {"@modelcontextprotocol/"}

# ─── Structured Logging ───────────────────────────────────────────
def slog(event: str, session: str = "", **kwargs):
    """Write a structured log line to stdout."""
    entry = {"ts": time.time(), "event": event, "session": session or None}
    entry.update(kwargs)
    print(json.dumps(entry, default=str), flush=True)

# ─── Session Manager ──────────────────────────────────────────────
class Session:
    """Encapsulates all state for a single MCP proxy session."""
    STATES = {"created", "starting", "initialized", "running", "closing", "exited", "error"}

    def __init__(self, session_id: str, remote: str):
        self.session_id = session_id
        self.remote = remote
        self.state = "created"
        self.start_time = time.time()
        self.end_time: float | None = None
        self.process: asyncio.subprocess.Process | None = None
        self.websocket: web.WebSocketResponse | None = None
        self.recorder = SessionRecorder(session_id)
        self.metrics = {"init_latency_ms": None, "tool_count": 0, "messages": 0, "tool_calls": 0}
        self.log_buffer: list[dict] = []
        self.pending_requests: dict[int, str] = {}  # id -> tool_name

    def transition(self, to: str):
        assert to in self.STATES, f"Invalid state: {to}"
        slog("session.transition", self.session_id, from_state=self.state, to_state=to)
        self.state = to

    def log(self, level: str, message: str):
        self.log_buffer.append({"ts": time.time(), "level": level, "message": message})

    async def cleanup(self):
        if self.state in ("closing", "exited"):
            return
        self.transition("closing")
        if self.process:
            try:
                self.process.kill()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
                slog("process.terminated", self.session_id, pid=self.process.pid)
            except asyncio.TimeoutError:
                slog("process.kill_timeout", self.session_id, pid=self.process.pid)
                try: os.kill(self.process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
            except Exception as e:
                slog("process.kill_error", self.session_id, error=str(e))
            finally:
                self.process = None
        self.recorder.save()
        self.end_time = time.time()
        self.transition("exited")

class SessionManager:
    def __init__(self):
        self.sessions: dict[str, Session] = {}

    def create(self, remote: str) -> Session:
        sid = str(uuid.uuid4())[:8]
        sess = Session(sid, remote)
        self.sessions[sid] = sess
        return sess

    def remove(self, sid: str):
        self.sessions.pop(sid, None)

    async def cleanup_all(self):
        await asyncio.gather(*[s.cleanup() for s in list(self.sessions.values())], return_exceptions=True)
        self.sessions.clear()

    async def kill_orphaned(self):
        """Kill any MCP processes not tracked by active sessions."""
        tracked_pids = {s.process.pid for s in self.sessions.values() if s.process}
        for proc in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmdline = proc.info["cmdline"] or []
                if any("@modelcontextprotocol" in str(c) for c in cmdline):
                    if proc.info["pid"] not in tracked_pids:
                        os.kill(proc.info["pid"], signal.SIGKILL)
                        slog("orphan.kill", pid=proc.info["pid"])
            except (psutil.NoSuchProcess, PermissionError, ProcessLookupError):
                pass

# ─── Session Recorder ────────────────────────────────────────────
class SessionRecorder:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.entries: list[dict] = []
        self.started_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()

    def record(self, direction: str, payload: dict):
        self.entries.append({"ts": time.time(), "direction": direction, "payload": payload})

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
            slog("recorder.save_failed", self.session_id, error=str(e))
            return None

# ─── Proxy Metrics ──────────────────────────────────────────────
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
session_mgr = SessionManager()

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

async def drain_stderr(proc, session: Session):
    while True:
        line = await proc.stderr.readline()
        if not line: break
        text = line.decode("utf-8", errors="replace").rstrip()
        if text: session.log("stderr", text)

# ─── HTTP Handlers ──────────────────────────────────────────────
async def api_health(request):
    return web.json_response({"status": "ok", "timestamp": time.time()})

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

    sess = session_mgr.create(request.remote)
    sess.websocket = ws
    init_start = time.time()
    conn_success = False
    slog("session.connected", sess.session_id, remote=request.remote)
    stderr_task = None

    try:
        raw = await asyncio.wait_for(ws.receive_str(), timeout=30.0)
        init = json.loads(raw)
        command = init.get("command", "npx"); args = init.get("args", []); env = init.get("env")
        sess.recorder.save(command=f"{command} {' '.join(str(a) for a in args)}")

        slog("process.spawn", sess.session_id, command=command, args=args)
        err = validate_command(command, args)
        if err:
            slog("security.blocked", sess.session_id, reason=err)
            await ws.send_str(json.dumps({"type": "error", "message": err}))
            metrics.record_connection(False); metrics.record_error(err); return ws

        sess.transition("starting")
        proc = await spawn_mcp(command, args, env)
        sess.process = proc
        slog("process.started", sess.session_id, pid=proc.pid)
        stderr_task = asyncio.create_task(drain_stderr(proc, sess))

        init_req = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "mcp-workbench", "version": "0.1.0"}}}
        await write_jsonrpc(proc, init_req)
        sess.recorder.record("client->server", init_req)

        async def mcp_to_ws():
            async for msg in read_jsonrpc_lines(proc.stdout):
                sess.recorder.record("server->client", msg)
                sess.metrics["messages"] += 1
                if msg.get("id") == 0 and "result" in msg:
                    sess.metrics["init_latency_ms"] = (time.time() - init_start) * 1000
                    metrics.record_init_latency(sess.metrics["init_latency_ms"])
                    sess.transition("initialized")
                if msg.get("id") == 1 and "result" in msg:
                    tools = msg.get("result", {}).get("tools", [])
                    sess.metrics["tool_count"] = len(tools)
                    metrics.record_tool_count(len(tools))
                    sess.transition("running")
                if not ws.closed: await ws.send_str(json.dumps({"type": "message", "payload": msg}))
            slog("process.stdout_closed", sess.session_id)

        async def ws_to_mcp():
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        sess.recorder.record("client->server", data)
                        sess.metrics["messages"] += 1
                        if data.get("method") == "tools/call":
                            sess.metrics["tool_calls"] += 1
                        await write_jsonrpc(proc, data)
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({"type": "error", "message": "Invalid JSON"}))
                elif msg.type == WSMsgType.ERROR:
                    slog("websocket.error", sess.session_id, error=str(ws.exception()))
            slog("websocket.closed", sess.session_id)

        mcp_task = asyncio.create_task(mcp_to_ws())
        ws_task = asyncio.create_task(ws_to_mcp())
        done, pending = await asyncio.wait([mcp_task, ws_task], return_when=asyncio.FIRST_COMPLETED)
        for task in pending: task.cancel()
        conn_success = True

    except asyncio.TimeoutError:
        if not ws.closed: await ws.send_str(json.dumps({"type": "error", "message": "Timeout waiting for init"}))
        metrics.record_error("timeout")
        sess.transition("error")
    except Exception as e:
        slog("session.error", sess.session_id, error=f"{type(e).__name__}: {e}")
        metrics.record_error(f"{type(e).__name__}: {e}")
        sess.transition("error")
    finally:
        await sess.cleanup()
        session_mgr.remove(sess.session_id)
        if conn_success:
            metrics.record_connection(True)
        else:
            metrics.record_connection(False)

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
    slog("server.start", port=port, url=f"http://0.0.0.0:{port}")

    # Cleanup orphaned processes on startup
    await session_mgr.kill_orphaned()

    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        asyncio.run(session_mgr.cleanup_all())
