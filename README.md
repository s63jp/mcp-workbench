# MCP Workbench

> The Postman for Model Context Protocol servers.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Overview

MCP Workbench is a web-based platform for testing, validating, and debugging [Model Context Protocol](https://modelcontextprotocol.io) (MCP) servers. Stop wrestling with config files and start shipping.

## Features

- **Instant Validation** — Connect to any MCP server and validate tools/schemas in seconds
- **Compatibility Reports** — See which clients support your server (Claude, Cursor, VS Code, etc.)
- **Saved Configurations** — Store, version, and share MCP server configs
- **CI/CD Integration** — Webhook-based regression testing
- **Raw JSON-RPC** — Inspect every message for complete transparency

## Tech Stack

- **Frontend:** Next.js 16 + React 19 + TypeScript + Tailwind CSS v4
- **Backend:** Cloudflare Worker (Hono) + Durable Objects — WebSocket-to-stdio MCP proxy
- **Deployment:** Static export (Vercel / GitHub Pages / Cloudflare Pages) for frontend; Cloudflare Workers for backend
- **Icons:** Lucide React

## Getting Started

### Frontend

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### MCP Proxy (Cloudflare Worker)

```bash
cd apps/mcp-proxy
npm install
npx wrangler dev
```

The proxy exposes:

- `POST /connect` — start an MCP server session (returns `sessionId` and `wsUrl`)
- `GET /rpc` — upgrade to WebSocket and bridge JSON-RPC messages
- `POST /disconnect` — kill the session and its child process

## Architecture

```
┌──────────────┐        POST /connect        ┌─────────────────────────┐
│              │ ──────────────────────────▶ │                         │
│  Next.js     │        WS /rpc              │  Cloudflare Worker      │
│  (static)    │ ◀─────── WebSocket ───────▶ │  (Hono + Durable Obj)   │
│              │        POST /disconnect     │                         │
└──────────────┘ ──────────────────────────▶ │                         │
                                              └───────────┬─────────────┘
                                                          │ spawn()
                                                          ▼
                                              ┌─────────────────────────┐
                                              │  MCP Server (stdio)     │
                                              │  e.g. npx @mcp/server-… │
                                              └─────────────────────────┘
```

## Build

```bash
npm run build
# Output in ./dist
```

## Deploy

### Frontend

#### Vercel (recommended)
```bash
npx vercel --prod
```

#### GitHub Pages
```bash
npm run build
# Push dist/ to gh-pages branch
```

### Backend (MCP Proxy)
```bash
cd apps/mcp-proxy
npx wrangler deploy
```

## License

MIT © MCP Workbench
