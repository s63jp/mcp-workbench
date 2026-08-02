#!/usr/bin/env python3
"""
Hermes Verification Engine (HVE) — MCP Adapter
Validates MCP servers with runtime evidence over assumptions.

Usage:
    python3 hve_mcp.py --command "npx -y @modelcontextprotocol/server-filesystem" --timeout 30
    python3 hve_mcp.py --command "node dist/index.js" --server-name "my-mcp-server"
"""
import asyncio
import json
import os
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class VerificationResult:
    server_name: str
    timestamp: str
    overall_status: str  # "verified", "untested", "failed"
    
    # Test results
    startup_passed: bool = False
    startup_duration_ms: float = 0.0
    startup_errors: list = field(default_factory=list)
    
    discovery_passed: bool = False
    discovery_duration_ms: float = 0.0
    tool_count: int = 0
    tools: list = field(default_factory=list)
    
    tool_call_results: list = field(default_factory=list)
    tool_calls_passed: int = 0
    tool_calls_failed: int = 0
    
    performance: dict = field(default_factory=dict)
    security: dict = field(default_factory=dict)
    stability: dict = field(default_factory=dict)
    
    evidence_path: str = ""
    logs: list = field(default_factory=list)

async def verify_mcp_server(
    command: str,
    args: list | None = None,
    env: dict | None = None,
    server_name: str = "unknown",
    timeout_seconds: int = 30
) -> VerificationResult:
    """Run full HVE verification on an MCP server."""
    
    result = VerificationResult(
        server_name=server_name,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        overall_status="untested"
    )
    
    start_time = time.time()
    proc = None
    
    try:
        # ─── 1. Startup Verification ──────────────────────────────
        print(f"[{server_name}] Phase 1: Startup verification...")
        startup_start = time.time()
        
        proc = await asyncio.create_subprocess_exec(
            command, *(args or []),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **(env or {})}
        )
        
        # Wait for process to be ready (check if it responds to initialize)
        init_req = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "hve-mcp", "version": "1.0.0"}
            }
        }
        
        init_json = json.dumps(init_req) + "\n"
        proc.stdin.write(init_json.encode())
        await proc.stdin.drain()
        
        # Read response with timeout
        response = await asyncio.wait_for(
            read_jsonrpc_response(proc.stdout),
            timeout=timeout_seconds
        )
        
        startup_duration = (time.time() - startup_start) * 1000
        result.startup_passed = True
        result.startup_duration_ms = round(startup_duration, 2)
        
        # Check for stderr errors
        stderr_data = await asyncio.wait_for(
            read_available_stderr(proc.stderr),
            timeout=1.0
        )
        if stderr_data:
            result.startup_errors.append(stderr_data[:500])
        
        print(f"  ✅ Startup: {result.startup_duration_ms}ms")
        
        # ─── 2. Tool Discovery ──────────────────────────────────
        print(f"[{server_name}] Phase 2: Tool discovery...")
        disc_start = time.time()
        
        tools_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        proc.stdin.write(json.dumps(tools_req).encode() + b"\n")
        await proc.stdin.drain()
        
        tools_response = await asyncio.wait_for(
            read_jsonrpc_response(proc.stdout),
            timeout=timeout_seconds
        )
        
        disc_duration = (time.time() - disc_start) * 1000
        result.discovery_duration_ms = round(disc_duration, 2)
        
        if "result" in tools_response and "tools" in tools_response["result"]:
            result.discovery_passed = True
            result.tool_count = len(tools_response["result"]["tools"])
            result.tools = [t.get("name", "unknown") for t in tools_response["result"]["tools"]]
            print(f"  ✅ Discovery: {result.tool_count} tools found ({result.discovery_duration_ms}ms)")
        else:
            result.discovery_passed = False
            print(f"  ❌ Discovery failed")
        
        # ─── 3. Tool Call Verification ─────────────────────────────
        print(f"[{server_name}] Phase 3: Tool call verification...")
        
        # Try calling each tool with minimal params
        for tool_info in tools_response.get("result", {}).get("tools", [])[:3]:  # Test first 3
            tool_name = tool_info.get("name", "unknown")
            tool_start = time.time()
            
            try:
                # Build minimal parameter set from schema
                params = build_minimal_params(tool_info.get("inputSchema", {}))
                
                call_req = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": params}
                }
                
                proc.stdin.write(json.dumps(call_req).encode() + b"\n")
                await proc.stdin.drain()
                
                call_response = await asyncio.wait_for(
                    read_jsonrpc_response(proc.stdout),
                    timeout=timeout_seconds
                )
                
                tool_duration = (time.time() - tool_start) * 1000
                
                call_result = {
                    "tool": tool_name,
                    "passed": "result" in call_response,
                    "duration_ms": round(tool_duration, 2),
                    "response_type": type(call_response.get("result", {})).__name__
                }
                
                result.tool_call_results.append(call_result)
                if call_result["passed"]:
                    result.tool_calls_passed += 1
                else:
                    result.tool_calls_failed += 1
                    
            except Exception as e:
                result.tool_call_results.append({
                    "tool": tool_name,
                    "passed": False,
                    "error": str(e)
                })
                result.tool_calls_failed += 1
        
        print(f"  ✅ Tool calls: {result.tool_calls_passed}/{result.tool_calls_passed + result.tool_calls_failed} passed")
        
        # ─── 4. Performance Metrics ────────────────────────────────
        print(f"[{server_name}] Phase 4: Performance metrics...")
        
        result.performance = {
            "startup_ms": result.startup_duration_ms,
            "discovery_ms": result.discovery_duration_ms,
            "tools_per_second": round(result.tool_count / (result.discovery_duration_ms / 1000), 2) if result.discovery_duration_ms > 0 else 0,
            "total_test_duration_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        # ─── 5. Security Audit (Basic) ─────────────────────────────
        print(f"[{server_name}] Phase 5: Security audit...")
        
        result.security = {
            "command_used": command,
            "args": args or [],
            "process_pid": proc.pid if proc else None,
            "notes": "Full sandbox audit requires gVisor integration (Phase 4)"
        }
        
        # ─── 6. Stability ─────────────────────────────────────────
        print(f"[{server_name}] Phase 6: Stability check...")
        
        result.stability = {
            "process_alive": proc.returncode is None if proc else False,
            "test_duration_ms": result.performance["total_test_duration_ms"]
        }
        
        # ─── Determine Overall Status ───────────────────────────────
        passed_tests = sum([
            result.startup_passed,
            result.discovery_passed,
            result.tool_calls_passed > 0
        ])
        
        if passed_tests == 3:
            result.overall_status = "verified"
        elif passed_tests >= 1:
            result.overall_status = "partial"
        else:
            result.overall_status = "failed"
        
    except asyncio.TimeoutError:
        result.overall_status = "failed"
        result.logs.append(f"TIMEOUT after {timeout_seconds}s")
    except Exception as e:
        result.overall_status = "failed"
        result.logs.append(f"ERROR: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
    finally:
        if proc and proc.returncode is None:
            try:
                proc.kill()
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except:
                pass
    
    return result

async def read_jsonrpc_response(stream) -> dict:
    """Read a single JSON-RPC response from stdout."""
    buffer = b""
    while True:
        chunk = await stream.read(4096)
        if not chunk:
            break
        buffer += chunk
        try:
            # Try to parse the first complete JSON object
            decoded = buffer.decode('utf-8', errors='replace')
            for line in decoded.split('\n'):
                line = line.strip()
                if line:
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
        except:
            pass
    
    return {}

async def read_available_stderr(stream) -> str:
    """Read any available stderr data (non-blocking)."""
    try:
        data = await asyncio.wait_for(stream.read(4096), timeout=1.0)
        return data.decode('utf-8', errors='replace') if data else ""
    except asyncio.TimeoutError:
        return ""

def build_minimal_params(schema: dict) -> dict:
    """Build minimal valid parameters from JSON schema."""
    params = {}
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    for prop_name, prop_schema in properties.items():
        if prop_name in required:
            prop_type = prop_schema.get("type", "string")
            
            if prop_type == "string":
                params[prop_name] = prop_schema.get("default", "")
            elif prop_type == "number":
                params[prop_name] = prop_schema.get("default", 0)
            elif prop_type == "boolean":
                params[prop_name] = prop_schema.get("default", False)
            elif prop_type == "array":
                params[prop_name] = prop_schema.get("default", [])
            elif prop_type == "object":
                params[prop_name] = prop_schema.get("default", {})
    
    return params

def print_verification_badge(result: VerificationResult):
    """Print a verification badge like the UI will show."""
    status_emoji = {
        "verified": "🟢",
        "partial": "🟡",
        "failed": "🔴",
        "untested": "⚪"
    }
    
    emoji = status_emoji.get(result.overall_status, "⚪")
    
    print(f"\n{'='*60}")
    print(f"{emoji} Verification Result: {result.overall_status.upper()}")
    print(f"{'='*60}")
    print(f"Server:     {result.server_name}")
    print(f"Timestamp:  {result.timestamp}")
    print(f"\nStartup:     {'✅' if result.startup_passed else '❌'} {result.startup_duration_ms}ms")
    print(f"Discovery:   {'✅' if result.discovery_passed else '❌'} {result.discovery_duration_ms}ms")
    print(f"Tools:       {result.tool_count} found")
    print(f"Tool Calls:  {result.tool_calls_passed}/{result.tool_calls_passed + result.tool_calls_failed} passed")
    print(f"Duration:    {result.performance.get('total_test_duration_ms', 'N/A')}ms")
    print(f"{'='*60}\n")

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="HVE MCP Verification Engine")
    parser.add_argument("--command", default="npx", help="Command to run (e.g., npx, node, python3)")
    parser.add_argument("--args", default="-y @modelcontextprotocol/server-filesystem", help="Arguments as single string (quoted)")
    parser.add_argument("--server-name", default="test-server", help="Server name")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds")
    parser.add_argument("--output", default="verification.json", help="Output file")
    args = parser.parse_args()
    
    # Parse args string into list
    arg_list = args.args.split() if args.args else []
    
    print(f"🔧 HVE-MCP Verification Engine v1.0")
    print(f"Testing: {args.command} {' '.join(arg_list)}\n")
    
    result = await verify_mcp_server(
        command=args.command,
        args=arg_list,
        server_name=args.server_name,
        timeout_seconds=args.timeout
    )
    
    print_verification_badge(result)
    
    # Save results
    os.makedirs("verifications", exist_ok=True)
    output_path = f"verifications/{args.server_name}_{int(time.time())}.json"
    with open(output_path, "w") as f:
        json.dump(asdict(result), f, indent=2)
    
    print(f"💾 Evidence saved: {output_path}")
    
    # Also save latest as symlink
    latest_path = f"verifications/{args.server_name}_latest.json"
    if os.path.exists(latest_path):
        os.remove(latest_path)
    os.symlink(os.path.basename(output_path), latest_path)

if __name__ == "__main__":
    asyncio.run(main())
