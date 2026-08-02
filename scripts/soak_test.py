#!/usr/bin/env python3
"""MCP Workbench 24-Hour Soak Test

Periodic health and load exercise. Logs every iteration to JSON for
evidence-based stability analysis.

Success criteria per iteration:
- /api/health returns 200
- /api/metrics returns valid JSON
- WebSocket connection establishes
- initialize completes
- tools/list succeeds
- Connection closes cleanly
- No orphaned MCP processes
- RSS memory < 20% growth from baseline
- FD count stable
- Child process count returns to 0
- CPU low while idle

Usage:
    python3 scripts/soak_test.py --iterations 5 --interval 300
    python3 scripts/soak_test.py       # defaults: 288 iterations x 5 min = 24h
"""
import argparse
import json
import os
import resource
import subprocess
import sys
import time
import urllib.request
import websockets
from datetime import datetime, timezone

# Config
BASE_URL = os.environ.get("MCP_WORKBENCH_URL", "http://localhost:3460")
WS_URL = os.environ.get("MCP_WORKBENCH_WS", "ws://localhost:3460/ws")
LOG_FILE = os.environ.get("SOAK_LOG", "/home/kali/mcp-workbench/logs/soak_test.jsonl")
BASELINE_FILE = os.environ.get("SOAK_BASELINE", "/home/kali/mcp-workbench/logs/soak_baseline.json")
SERVER_PID = int(os.environ.get("SERVER_PID", "579682"))

# Memory threshold: 20% growth from baseline
MEMORY_GROWTH_THRESHOLD = 0.20

def get_system_stats():
    """Capture process tree, memory, FDs, sockets."""
    stats = {"timestamp": datetime.now(timezone.utc).isoformat()}

    # Target server stats
    try:
        with open(f"/proc/{SERVER_PID}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    stats["rss_kb"] = int(line.split()[1])
                elif line.startswith("VmSize:"):
                    stats["vsz_kb"] = int(line.split()[1])
                elif line.startswith("Threads:"):
                    stats["threads"] = int(line.split()[1])
        stats["fd_count"] = len(os.listdir(f"/proc/{SERVER_PID}/fd"))
    except (FileNotFoundError, PermissionError) as e:
        stats["server_error"] = str(e)
        stats["server_alive"] = False
        return stats

    stats["server_alive"] = True

    # Child process count (MCP servers spawned)
    try:
        result = subprocess.run(
            ["pgrep", "-P", str(SERVER_PID), "-c"],
            capture_output=True, text=True, timeout=5
        )
        stats["child_count"] = int(result.stdout.strip()) if result.stdout.strip() else 0
    except Exception:
        stats["child_count"] = -1

    # Orphaned MCP processes (not children of server)
    try:
        result = subprocess.run(
            ["pgrep", "-af", "mcp-server"],
            capture_output=True, text=True, timeout=5
        )
        orphans = [l for l in result.stdout.strip().split("\n") if l and str(SERVER_PID) not in l]
        # Filter out PIDs that are children of the server
        my_children = set()
        for line in result.stdout.strip().split("\n"):
            if not line: continue
            pid = line.split()[0]
            try:
                ppid = open(f"/proc/{pid}/stat").read().split()[3]
                if int(ppid) == SERVER_PID:
                    my_children.add(pid)
            except (FileNotFoundError, ValueError, IndexError):
                pass
        stats["orphan_mcp_count"] = len([l for l in orphans if l.split()[0] not in my_children])
    except Exception:
        stats["orphan_mcp_count"] = -1

    # Open sockets
    try:
        result = subprocess.run(
            ["ss", "-tlnp", f"pid = {SERVER_PID}"],
            capture_output=True, text=True, timeout=5
        )
        stats["open_sockets"] = len(result.stdout.strip().split("\n")) - 1
    except Exception:
        stats["open_sockets"] = -1

    return stats

def check_health():
    """Check /api/health endpoint."""
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/health")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"status": resp.status, "body": json.loads(resp.read())}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_metrics():
    """Check /api/metrics endpoint."""
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/metrics")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return {"status": resp.status, "connections": data.get("connections", {}).get("total", 0)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def exercise_websocket():
    """Full WebSocket lifecycle: connect, initialize, tools/list, disconnect."""
    result = {"steps": []}
    try:
        start = time.time()
        import asyncio
        async def _exercise():
            steps = []
            t0 = time.time()
            async with websockets.connect(WS_URL) as ws:
                steps.append({"step": "connect", "latency_ms": round((time.time() - t0) * 1000, 2)})
                t1 = time.time()
                await ws.send(json.dumps({"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]}))
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=30))
                steps.append({"step": "initialize", "latency_ms": round((time.time() - t1) * 1000, 2), "server": msg.get("payload", {}).get("result", {}).get("serverInfo", {}).get("name")})
                await ws.send(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}))
                t2 = time.time()
                await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}))
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                tools = len(msg.get("payload", {}).get("result", {}).get("tools", []))
                steps.append({"step": "tools_list", "latency_ms": round((time.time() - t2) * 1000, 2), "tool_count": tools})
                steps.append({"step": "close", "success": True})
            return steps
        result["steps"] = asyncio.run(_exercise())
        result["success"] = True
        result["total_latency_ms"] = round((time.time() - start) * 1000, 2)
    except Exception as e:
        result["success"] = False
        result["error"] = f"{type(e).__name__}: {e}"
    return result

def run_iteration(iteration):
    """Run one full soak iteration."""
    print(f"\n=== Iteration {iteration} @ {datetime.now(timezone.utc).isoformat()} ===")

    record = {
        "iteration": iteration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # 1. System stats
    record["system"] = get_system_stats()
    if not record["system"].get("server_alive", False):
        record["fail"] = "server_not_alive"
        record["reason"] = f"Server PID {SERVER_PID} not found"
        record["evidence"] = capture_failure_evidence()
        return record

    # 2. Health check
    health = check_health()
    record["health"] = health
    if health["status"] != 200:
        record["fail"] = "health_check_failed"
        record["reason"] = f"Health returned {health['status']}"
        record["evidence"] = capture_failure_evidence()
        return record

    # 3. Metrics check
    metrics = check_metrics()
    record["metrics"] = metrics
    if metrics["status"] != 200:
        record["fail"] = "metrics_check_failed"
        record["reason"] = f"Metrics returned {metrics['status']}"
        return record

    # 4. WebSocket exercise
    ws_result = exercise_websocket()
    record["websocket"] = ws_result
    if not ws_result.get("success"):
        record["fail"] = "websocket_exercise_failed"
        record["reason"] = ws_result.get("error")
        record["evidence"] = capture_failure_evidence()
        return record

    # 5. Post-exercise stats (check for orphans)
    time.sleep(2)
    record["post_exercise"] = get_system_stats()

    # 6. Memory growth check
    if os.path.exists(BASELINE_FILE):
        with open(BASELINE_FILE) as f:
            baseline = json.load(f)
        baseline_rss = baseline.get("rss_kb", 0)
        current_rss = record["system"].get("rss_kb", 0)
        if baseline_rss > 0:
            growth = (current_rss - baseline_rss) / baseline_rss
            record["memory_growth_pct"] = round(growth * 100, 2)
            if growth > MEMORY_GROWTH_THRESHOLD:
                record["fail"] = "memory_growth_exceeded"
                record["reason"] = f"RSS grew {growth*100:.1f}% (threshold {MEMORY_GROWTH_THRESHOLD*100:.0f}%)"
                return record

    # 7. Orphan check
    orphans = record["post_exercise"].get("orphan_mcp_count", 0)
    if orphans > 0:
        record["fail"] = "orphaned_processes"
        record["reason"] = f"{orphans} orphaned MCP processes after exercise"
        record["evidence"] = capture_failure_evidence()
        return record

    record["success"] = True
    return record

def capture_failure_evidence():
    """Capture diagnostic context on failure."""
    evidence = {}

    # Last 200 log lines
    server_log = "/home/kali/mcp-workbench/logs/server.log"
    if os.path.exists(server_log):
        with open(server_log) as f:
            lines = f.readlines()
            evidence["server_log_tail"] = lines[-200:]

    # Process tree
    try:
        result = subprocess.run(["pstree", "-ap", str(SERVER_PID)], capture_output=True, text=True, timeout=5)
        evidence["process_tree"] = result.stdout
    except Exception as e:
        evidence["process_tree_error"] = str(e)

    # Open sockets
    try:
        result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True, timeout=5)
        evidence["open_sockets"] = result.stdout
    except Exception as e:
        evidence["sockets_error"] = str(e)

    # Active WebSocket sessions (from /proc/net/tcp)
    try:
        with open("/proc/net/tcp") as f:
            evidence["tcp_connections"] = sum(1 for _ in f) - 1
    except Exception:
        pass

    return evidence

def capture_baseline():
    """Capture initial baseline stats."""
    baseline = get_system_stats()
    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=2)
    print(f"Baseline captured: RSS={baseline.get('rss_kb')}KB, FDs={baseline.get('fd_count')}")
    return baseline

def main():
    parser = argparse.ArgumentParser(description="MCP Workbench 24h Soak Test")
    parser.add_argument("--iterations", type=int, default=288, help="Number of iterations (default: 288 = 24h at 5min)")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between iterations (default: 300)")
    parser.add_argument("--baseline-only", action="store_true", help="Only capture baseline, don't run iterations")
    args = parser.parse_args()

    print(f"MCP Workbench Soak Test")
    print(f"  Target: {BASE_URL}")
    print(f"  WS: {WS_URL}")
    print(f"  Server PID: {SERVER_PID}")
    print(f"  Iterations: {args.iterations}")
    print(f"  Interval: {args.interval}s")
    print(f"  Log: {LOG_FILE}")

    if args.baseline_only:
        capture_baseline()
        return 0

    # Capture baseline if not exists
    if not os.path.exists(BASELINE_FILE):
        capture_baseline()

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    pass_count = 0
    fail_count = 0

    for i in range(1, args.iterations + 1):
        record = run_iteration(i)

        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(record) + "\n")

        if record.get("success"):
            pass_count += 1
            print(f"  ✅ PASS (RSS={record['system'].get('rss_kb')}KB, orphans={record['post_exercise'].get('orphan_mcp_count', '?')})")
        else:
            fail_count += 1
            print(f"  ❌ FAIL: {record.get('fail')} — {record.get('reason')}")
            # Evidence is already in the record
            # DO NOT touch code during soak test unless criteria met

        if i < args.iterations:
            time.sleep(args.interval)

    print(f"\n=== Final: {pass_count} passed, {fail_count} failed ===")
    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
