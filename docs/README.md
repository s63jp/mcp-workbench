# MCP Workbench Documentation

**GitHub:** https://github.com/s63jp/mcp-workbench


## Overview

MCP Workbench is a web-based MCP server testing, validation, and development platform. Think "Postman for MCP Servers."

## Architecture

```
Browser (Next.js Frontend)
    ↕ WebSocket (wss://host/ws)
MCP Workbench Server (aiohttp)
    ├── HTTP Static File Server (dist/)
    ├── WebSocket MCP Proxy (/ws)
    ├── API Endpoints (/api/*)
    └── Session Recording (sessions/)
    ↕ stdio
MCP Server (npx @modelcontextprotocol/*)
```

## Supported Servers

| Server | Package | Status | Notes |
|--------|---------|--------|-------|
| Filesystem | `@modelcontextprotocol/server-filesystem` | ✅ Supported | Requires directory path arg |
| GitHub | `@modelcontextprotocol/server-github` | ✅ Supported | Deprecated but functional |
| Memory | `@modelcontextprotocol/server-memory` | ✅ Supported | Knowledge graph server |
| Time | `@modelcontextprotocol/server-time` | ⚠️ Unsupported | Fails to start; config issue |
| SQLite | `@modelcontextprotocol/server-sqlite` | ⚠️ Unsupported | Requires DB file arg |
| Sequential Thinking | `@modelcontextprotocol/server-sequentialthinking` | ⚠️ Unsupported | Package not found |
| Fetch | `@modelcontextprotocol/server-fetch` | ⚠️ Unsupported | Connection closes early |

## Security Model

The proxy enforces a **command allowlist**:

- Allowed commands: `npx`, `node`, `python3`
- Allowed packages: `@modelcontextprotocol/*`
- Attempts to run `bash`, `sh`, `curl`, etc. are rejected with a clear error message.

Session recordings are saved locally in `sessions/` and never transmitted externally.

## Session Recording Format

Each session produces a JSON file:

```json
{
  "session_id": "a1b2c3d4",
  "started_at": "2026-08-02T18:42:00Z",
  "command": "npx -y @modelcontextprotocol/server-filesystem /tmp",
  "entries": [
    {"ts": 1785692510.0, "direction": "client->server", "payload": {"jsonrpc": "2.0", "id": 0, "method": "initialize"}},
    {"ts": 1785692511.0, "direction": "server->client", "payload": {"jsonrpc": "2.0", "id": 0, "result": {"protocolVersion": "2024-11-05"}}}
  ]
}
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Server health check |
| `/api/metrics` | GET | Connection metrics summary |
| `/api/sessions` | GET | List recent recorded sessions |
| `/ws` | WebSocket | MCP proxy endpoint |

## Metrics

`/api/metrics` returns:

```json
{
  "connections": {
    "total": 10,
    "success": 8,
    "failed": 2,
    "success_rate_pct": 80.0
  },
  "init_latency_ms": {
    "count": 8,
    "avg": 1200.0,
    "min": 900.0,
    "max": 1500.0
  },
  "tool_discovery": {
    "count": 8,
    "avg": 15.0,
    "max": 26
  },
  "errors_last_10": [...]
}
```

## Troubleshooting

### "Command 'bash' not allowed"
The proxy rejected your command. Only `@modelcontextprotocol/*` packages via `npx` are permitted.

### "Connection failed. Ensure the MCP Workbench server is running."
The frontend can't reach the WebSocket endpoint. Check that `python3 server.py` is running.

### "Timeout waiting for init"
The MCP server took too long to respond. Try a different server or check network connectivity.

### Orphaned Processes
If MCP processes remain after disconnect, restart the server. The proxy attempts to kill processes on disconnect, but some edge cases (browser tab close) may leave zombies.

## Adding a Server Preset

Edit `PRESETS` in `src/app/page.tsx`:

```typescript
const PRESETS = [
  { label: "My Server (npx)", command: "npx", args: "-y @myscope/my-mcp-server" },
];
```

## Running Locally

```bash
# 1. Install dependencies
npm install

# 2. Build frontend
npm run build

# 3. Start server
python3 server.py 3460

# 4. Open browser
open http://localhost:3460
```

## Running Tests

```bash
python3 tests/integration_test.py
```

## Stack

- Frontend: Next.js 16, Tailwind CSS, Radix UI
- Server: Python 3.13, aiohttp, websockets
- Deployment: Static export + Cloudflare Tunnel
