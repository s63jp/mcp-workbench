#!/usr/bin/env python3
"""
Test Roblox MCP Server with MCP Workbench

This script tests if the Roblox MCP server can be connected to
via MCP Workbench's client infrastructure.
"""
import asyncio
import json
import sys
import os
import subprocess
import time
import signal

# Add MCP Workbench to path
sys.path.insert(0, '/home/kali/mcp-workbench')

from mcp_client import MCPClient


async def test_roblox_stdio():
    """Test Roblox MCP server via stdio transport."""
    print("🧪 Testing Roblox MCP Server via stdio...")
    print("=" * 60)
    
    # Roblox MCP server command
    command = "python3"
    args = ["-u", "-m", "app.main"]  # or direct script
    cwd = "/home/kali/roblox-mcp-server"
    
    # Actually, let's check if there's a simpler entry point
    # The server uses uvicorn.run() on port 8001
    # For stdio, it has a stdio_transport that reads from stdin
    
    print(f"📁 Working directory: {cwd}")
    print(f"🔧 Command: {command} {' '.join(args)}")
    print()
    
    # Check if roblox server has a CLI entry point
    main_path = os.path.join(cwd, "app", "main.py")
    if not os.path.exists(main_path):
        print(f"❌ Main file not found: {main_path}")
        return False
    
    # The Roblox server starts a WebSocket + HTTP server
    # It also starts stdio transport on startup
    # Let's start it and see what happens
    
    print("🚀 Starting Roblox MCP server...")
    env = os.environ.copy()
    env["PYTHONPATH"] = cwd
    
    try:
        proc = subprocess.Popen(
            ["python3", "-u", "app/main.py"],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1
        )
        
        print(f"✅ Server started with PID {proc.pid}")
        print()
        
        # Wait a moment for startup
        await asyncio.sleep(3)
        
        # Check if process is still running
        if proc.poll() is not None:
            stdout, stderr = proc.communicate(timeout=1)
            print(f"❌ Server exited early with code {proc.returncode}")
            print(f"STDOUT: {stdout[:500]}")
            print(f"STDERR: {stderr[:500]}")
            return False
        
        print("✅ Server is still running")
        print()
        
        # The Roblox server starts uvicorn on port 8001
        # AND starts stdio transport
        # Let's try to connect to the WebSocket endpoint
        
        print("🔗 Testing WebSocket connection on port 8001...")
        
        # Test HTTP health endpoint first
        import urllib.request
        try:
            req = urllib.request.urlopen("http://localhost:8001/health", timeout=5)
            response = req.read().decode()
            print(f"✅ Health check: {response}")
        except Exception as e:
            print(f"⚠️ Health check failed: {e}")
        
        # Give it time
        await asyncio.sleep(2)
        
        # Now try MCP Workbench connection to stdio
        print()
        print("📡 Attempting MCP stdio connection...")
        
        # For MCP Workbench, we need a process that speaks stdio
        # The Roblox server has stdio_transport but it requires an API key
        # Let's test what we can
        
        # Write a test message to stdin
        test_msg = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}}}
        
        msg_json = json.dumps(test_msg)
        msg_bytes = msg_json.encode('utf-8')
        header = f"Content-Length: {len(msg_bytes)}\r\n\r\n"
        
        try:
            proc.stdin.write(header + msg_json + "\n")
            proc.stdin.flush()
            print(f"📤 Sent: {msg_json[:100]}...")
            
            # Read response with timeout
            import select
            readable, _, _ = select.select([proc.stdout], [], [], 5.0)
            if readable:
                response = proc.stdout.readline()
                print(f"📥 Response: {response[:200]}")
            else:
                print("⏱️ No response within timeout")
        except Exception as e:
            print(f"❌ Communication error: {e}")
        
        # Clean up
        print()
        print("🧹 Stopping server...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
            print("✅ Server stopped cleanly")
        except:
            proc.kill()
            print("⚠️ Server killed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_roblox_http():
    """Test Roblox MCP server via HTTP/WebSocket."""
    print()
    print("🧪 Testing Roblox MCP Server via HTTP...")
    print("=" * 60)
    
    cwd = "/home/kali/roblox-mcp-server"
    env = os.environ.copy()
    env["PYTHONPATH"] = cwd
    
    try:
        # Start server in background
        proc = subprocess.Popen(
            ["python3", "-u", "app/main.py"],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )
        
        print(f"✅ Server started with PID {proc.pid}")
        
        # Wait for startup
        await asyncio.sleep(4)
        
        # Test HTTP endpoints
        import urllib.request
        import urllib.error
        
        # Health check
        try:
            req = urllib.request.urlopen("http://localhost:8001/health", timeout=5)
            response = json.loads(req.read().decode())
            print(f"✅ Health: {response}")
        except Exception as e:
            print(f"⚠️ Health: {e}")
        
        # Check if server is still running
        if proc.poll() is not None:
            stdout, stderr = proc.communicate(timeout=1)
            print(f"⚠️ Server exited with code {proc.returncode}")
            print(f"STDERR: {stderr[-500:]}")
        
        # Stop server
        proc.terminate()
        proc.wait(timeout=5)
        
        print("✅ HTTP test complete")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run tests."""
    print("🔧 MCP Workbench + Roblox MCP Server Test")
    print("=" * 60)
    print()
    
    # Test 1: HTTP mode
    result1 = asyncio.run(test_roblox_http())
    
    # Test 2: stdio mode (if needed)
    # result2 = asyncio.run(test_roblox_stdio())
    
    print()
    print("=" * 60)
    print("🏁 Tests complete!")


if __name__ == "__main__":
    main()
