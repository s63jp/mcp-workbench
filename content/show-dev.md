# Show Dev: MCP Workbench - Browser-Based MCP Server Testing

**Repo:** [GitHub s63jp/mcp-workbench](https://github.com/s63jp/mcp-workbench)

Hey everyone! Built a tool for the MCP ecosystem and wanted to share.

## The Problem

If you've built an MCP server, you know the testing workflow is rough:
- Configure Claude Desktop / Cursor
- Restart the client repeatedly
- Hope errors show up in chat
- No visibility into JSON-RPC traffic

It's basically debugging APIs by typing into a chat box.

## What I Built

**MCP Workbench** - a browser-based testing environment for MCP servers.

Features:
- Connect to any MCP server via URL or command
- See all tools, schemas, and capabilities instantly
- Invoke tools with a form UI (no hand-coding JSON)
- Inspect raw JSON-RPC request/response
- Generate compatibility reports across clients
- Share test configs with your team
- CI/CD webhook integration

## The Tech Stack

Frontend: Next.js 15 + TypeScript
Backend: Python FastAPI + SQLite
Auth: JWT + Stripe (for future tiers)

Currently in free beta at [mcp-workbench.uk](https://mcp-workbench.uk).

## Why I'm Building This

The MCP ecosystem is growing fast (1000+ servers on the registry). But there's no dedicated testing tool like Postman for REST APIs. I wanted to fill that gap.

## Questions for You

- Would a testing workbench be useful in your MCP workflow?
- What features would you want most?
- Any concerns about browser-based vs CLI testing?

Feedback welcome!
