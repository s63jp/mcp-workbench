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
- **Deployment:** Static export (Vercel / GitHub Pages / Cloudflare Pages)
- **Icons:** Lucide React

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Build

```bash
npm run build
# Output in ./dist
```

## Deploy

### Vercel (recommended)
```bash
npx vercel --prod
```

### GitHub Pages
```bash
npm run build
# Push dist/ to gh-pages branch
```

## License

MIT © MCP Workbench
