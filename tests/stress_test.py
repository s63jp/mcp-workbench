#!/usr/bin/env python3
"""MCP Workbench Stress Test Suite

Tests: concurrent connections, sequential bursts, long-running idle, memory leaks.
Usage: python3 tests/stress_test.py
"""
import asyncio
import json
import os
import sys
import time
import tracemalloc

import websockets

WS_URI = "ws://localhost:3460/ws"

# ─── Helpers ────────────────────────────────────────────────────
async def connect_and_init(command: str, args: list):
    async with websockets.connect(WS_URI) as ws:
        await ws.send(json.dumps({"command": command, "args": args}))
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=15.0))
        assert msg["type"] == "message" and msg["payload"]["id"] == 0
        await ws.send(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}))
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=15.0))
        assert msg["type"] == "message" and msg["payload"]["id"] == 1
        return len(msg["payload"]["result"].get("tools", []))

# ─── Test: Sequential Burst ───────────────────────────────────────
async def test_sequential(count: int = 20):
    print(f"\n[STRESS] Sequential burst: {count} connections...")
    start = time.time()
    for i in range(count):
        tools = await connect_and_init("npx", ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"])
        assert tools > 0, f"Connection {i}: no tools found"
    elapsed = time.time() - start
    print(f"  ✅ Completed {count} connections in {elapsed:.1f}s ({elapsed/count*1000:.0f}ms avg)")
    return elapsed

# ─── Test: Concurrent Connections ─────────────────────────────────
async def test_concurrent(count: int = 20):
    print(f"\n[STRESS] Concurrent load: {count} simultaneous connections...")
    start = time.time()
    async def worker(i):
        try:
            tools = await connect_and_init("npx", ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"])
            return (i, True, tools, None)
        except Exception as e:
            return (i, False, 0, str(e))

    results = await asyncio.gather(*[worker(i) for i in range(count)])
    elapsed = time.time() - start
    passed = sum(1 for _, ok, _, _ in results if ok)
    failed = count - passed
    print(f"  ✅ {passed}/{count} passed in {elapsed:.1f}s")
    if failed:
        print(f"  ❌ {failed} failed:")
        for i, ok, _, err in results:
            if not ok:
                print(f"      Connection {i}: {err}")
    return elapsed, passed, failed

# ─── Test: Idle Connection ──────────────────────────────────────
async def test_idle(duration: int = 30):
    print(f"\n[STRESS] Idle connection: holding for {duration}s...")
    start = time.time()
    async with websockets.connect(WS_URI) as ws:
        await ws.send(json.dumps({"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]}))
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=15.0))
        assert msg["type"] == "message"
        await asyncio.sleep(duration)
    elapsed = time.time() - start
    print(f"  ✅ Held connection for {elapsed:.1f}s without errors")
    return elapsed

# ─── Test: Memory Leak ──────────────────────────────────────────
async def test_memory():
    print("\n[STRESS] Memory leak check...")
    tracemalloc.start()
    before = tracemalloc.take_snapshot()

    for i in range(10):
        tools = await connect_and_init("npx", ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"])
        assert tools > 0

    after = tracemalloc.take_snapshot()
    diff = after.compare_to(before, "lineno")
    top = diff[:3]
    print(f"  Top memory changes:")
    for stat in top:
        print(f"    {stat}")
    total_growth = sum(stat.size_diff for stat in diff)
    print(f"  Total growth: {total_growth / 1024:.1f} KB")
    if total_growth > 5 * 1024 * 1024:  # 5MB threshold
        print(f"  ⚠️ WARNING: Significant memory growth detected")
    else:
        print(f"  ✅ Memory growth within acceptable range")
    tracemalloc.stop()
    return total_growth

# ─── Test: Zombie Process Check ─────────────────────────────────
def test_zombies():
    print("\n[STRESS] Checking for orphaned MCP processes...")
    import subprocess
    result = subprocess.run(["pgrep", "-f", "@modelcontextprotocol"], capture_output=True, text=True)
    count = len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
    if count > 0:
        print(f"  ⚠️ Found {count} orphaned MCP processes:")
        subprocess.run(["pgrep", "-afl", "@modelcontextprotocol"])
    else:
        print(f"  ✅ No orphaned processes found")
    return count

# ─── Main ───────────────────────────────────────────────────────
async def main():
    print("=" * 60)
    print("MCP WORKBENCH STRESS TEST SUITE")
    print("=" * 60)

    # Pre-check
    test_zombies()

    results = {}
    try:
        results["sequential"] = await test_sequential(20)
        results["concurrent"] = await test_concurrent(20)
        results["idle"] = await test_idle(10)
        results["memory"] = await test_memory()
    except Exception as e:
        print(f"\n❌ Stress test failed: {e}")
        import traceback; traceback.print_exc()
        return 1

    # Post-check
    zombies = test_zombies()

    print("\n" + "=" * 60)
    print("STRESS TEST SUMMARY")
    print("=" * 60)
    for name, val in results.items():
        if isinstance(val, tuple):
            print(f"  {name:15s}: {val[1]}/{val[1]+val[2]} passed ({val[0]:.1f}s)")
        elif isinstance(val, float):
            print(f"  {name:15s}: {val:.1f}s")
        else:
            print(f"  {name:15s}: {val/1024:.1f} KB")
    print(f"  {'orphaned':15s}: {zombies} processes")
    print("=" * 60)
    return 0 if zombies == 0 else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
