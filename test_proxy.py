#!/usr/bin/env python3
"""Quick test of MCP proxy with sequentialthinking server."""
import asyncio, websockets, json

async def test():
    uri = "ws://localhost:8765"
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as ws:
        # Send init message
        init = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]}
        await ws.send(json.dumps(init))
        print("Sent init, waiting for initialize response...")

        # Read messages until we see initialize response
        messages = []
        for _ in range(10):
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
            messages.append(msg)
            print(f"  -> {json.dumps(msg, indent=2)[:200]}")
            if msg.get("id") == 0:
                print("Got initialize response!")
                break

        # Send initialized notification
        await ws.send(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}))

        # List tools
        await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}))
        for _ in range(5):
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
            messages.append(msg)
            print(f"  -> {json.dumps(msg, indent=2)[:200]}")
            if msg.get("id") == 1:
                print("Got tools list!")
                break

        print(f"\nTotal messages: {len(messages)}")
        return True

if __name__ == "__main__":
    ok = asyncio.run(test())
    sys.exit(0 if ok else 1)
