#!/usr/bin/env python3
"""MCP Workbench Integration Test Suite

Tests real MCP servers through the WebSocket proxy.
Usage: python3 tests/integration_test.py
"""
import asyncio
import json
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Optional

import websockets

WS_URI = "ws://localhost:3461"


@dataclass
class TestResult:
    name: str
    passed: bool
    duration_ms: float
    error: Optional[str] = None
    logs: list[str] = field(default_factory=list)


async def run_mcp_test(name: str, command: str, args: list, tool_to_call: Optional[tuple] = None):
    """Run a full MCP lifecycle test."""
    logs = []
    start = time.time()
    try:
        async with websockets.connect(WS_URI) as ws:
            # 1. Send init
            await ws.send(json.dumps({"command": command, "args": args}))
            logs.append("Sent init")

            # 2. Receive initialize response
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10.0))
            logs.append(f"Initialize response: {json.dumps(msg)[:120]}")
            assert msg.get("type") == "message", "Expected message type"
            payload = msg["payload"]
            assert payload.get("id") == 0, "Expected id=0"
            assert "result" in payload, "Expected result in initialize response"

            # 3. Send notifications/initialized
            await ws.send(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}))
            logs.append("Sent notifications/initialized")

            # 4. List tools
            await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}))
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10.0))
            logs.append(f"Tools list: {json.dumps(msg)[:120]}")
            payload = msg["payload"]
            tools = payload.get("result", {}).get("tools", [])
            assert len(tools) > 0, "Expected at least one tool"
            logs.append(f"Discovered {len(tools)} tools")

            # 5. Optionally call a tool
            if tool_to_call:
                tool_name, tool_args = tool_to_call
                call_msg = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": tool_args
                    }
                }
                await ws.send(json.dumps(call_msg))
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10.0))
                logs.append(f"Tool call result: {json.dumps(msg)[:120]}")
                # Tool call might error if args wrong — that's OK for this test
                # We just verify we got a response

            # 6. Disconnect cleanly
            logs.append("Disconnecting...")
            return TestResult(name=name, passed=True, duration_ms=(time.time()-start)*1000, logs=logs)

    except Exception as e:
        return TestResult(
            name=name, passed=False, duration_ms=(time.time()-start)*1000,
            error=f"{type(e).__name__}: {e}\n{traceback.format_exc()}",
            logs=logs
        )


async def test_filesystem():
    return await run_mcp_test(
        "Filesystem Server",
        "npx", ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        tool_to_call=("list_directory", {"path": "/tmp"})
    )


async def test_sqlite():
    return await run_mcp_test(
        "SQLite Server",
        "npx", ["-y", "@modelcontextprotocol/server-sqlite"],
    )


async def test_fetch():
    return await run_mcp_test(
        "Fetch Server",
        "npx", ["-y", "@modelcontextprotocol/server-fetch"],
    )


async def test_github():
    return await run_mcp_test(
        "GitHub Server",
        "npx", ["-y", "@modelcontextprotocol/server-github"],
    )


async def test_time():
    return await run_mcp_test(
        "Time Server",
        "npx", ["-y", "@modelcontextprotocol/server-time"],
        tool_to_call=("get_current_time", {"timezone": "UTC"})
    )


async def test_memory():
    return await run_mcp_test(
        "Memory Server",
        "npx", ["-y", "@modelcontextprotocol/server-memory"],
    )


async def test_security_rejection():
    """Verify the proxy rejects dangerous commands."""
    logs = []
    start = time.time()
    try:
        async with websockets.connect(WS_URI) as ws:
            await ws.send(json.dumps({"command": "bash", "args": ["-c", "rm -rf /"]}))
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
            logs.append(f"Response: {json.dumps(msg)[:120]}")
            assert msg.get("type") == "error", "Expected error for forbidden command"
            assert "not allowed" in msg.get("message", "").lower(), "Expected 'not allowed' message"
            return TestResult(name="Security: Reject Forbidden Command", passed=True, duration_ms=(time.time()-start)*1000, logs=logs)
    except Exception as e:
        return TestResult(name="Security: Reject Forbidden Command", passed=False, duration_ms=(time.time()-start)*1000, error=str(e), logs=logs)


async def main():
    print("=" * 60)
    print("MCP WORKBENCH INTEGRATION TEST SUITE")
    print("=" * 60)

    tests = [
        test_filesystem,
        test_time,
        test_sqlite,
        test_fetch,
        test_github,
        test_memory,
        test_security_rejection,
    ]

    results = []
    for test_fn in tests:
        result = await test_fn()
        results.append(result)
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"\n{status} | {result.name} ({result.duration_ms:.0f}ms)")
        for log in result.logs:
            print(f"    → {log}")
        if result.error:
            print(f"    ERROR: {result.error[:300]}")

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} passed")
    print("=" * 60)

    # Save report
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "tests": [
            {
                "name": r.name,
                "passed": r.passed,
                "duration_ms": round(r.duration_ms, 2),
                "error": r.error[:500] if r.error else None,
                "logs": r.logs,
            }
            for r in results
        ]
    }
    import os
    os.makedirs("tests", exist_ok=True)
    with open("tests/results.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to tests/results.json")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
