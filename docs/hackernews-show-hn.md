# Show HN: MCP Workbench — Test MCP servers in your browser with runtime verification

**TL;DR:** I built a web-based testing platform for MCP servers. Think "Postman for MCP" but with a verification engine that actually runs the tools and gives you 🟢 Verified / 🔴 Failed badges.

**Live demo:** https://blocked-skill-conviction-console.trycloudflare.com
**GitHub:** https://github.com/s63jp/mcp-workbench
**Beta signup:** https://blocked-skill-conviction-console.trycloudflare.com/beta.html

---

## The Problem

I've been building with MCP (Model Context Protocol) servers for a few months. The ecosystem is exploding — there are 1000+ servers on GitHub now. But there's a massive trust gap:

- **"This server looks cool"** → Install it → cryptic stdio error → uninstall
- **"Does it actually work?"** → No way to know without running it yourself
- **"What tools does it expose?"** → Read the source code (if you're lucky)
- **"How fast is it?"** → shrug emoji

The current workflow is: find on GitHub → npm install → configure Claude/Cursor → hope it works → debug in terminal → repeat.

---

## What I Built

**MCP Workbench** is three things in one:

### 1. Visual MCP Server Tester
Connect any MCP server in your browser. No terminal. No config files.

- Paste the command (e.g., `npx -y @modelcontextprotocol/server-filesystem /tmp`)
- Click "Connect"
- Browse tools in the sidebar
- Test each tool with a JSON payload editor
- See results in a live console

### 2. Hermes Verification Engine
Every server gets tested automatically:

| Test | What It Checks |
|------|---------------|
| Startup | Clean boot, no errors, protocol version match |
| Discovery | tools/list returns within timeout |
| Tool Calls | Each tool responds correctly |
| Performance | Latency p50/p95/p99 |
| Security | File system scope, network access |
| Stability | Process stays alive across calls |

Results: 🟢 **Verified** (7/7 passed) / 🟡 **Untested** / 🔴 **Failed**

### 3. Public Server Directory (In Progress)
Verified servers get a public page with:
- Performance metrics
- Tool coverage
- Startup logs
- Last successful execution
- Version history

---

## Tech Stack

- **Frontend:** Next.js 16 + React 19 + Tailwind CSS
- **Backend:** Python asyncio + WebSocket stdio transport
- **Verification:** Async test runner with evidence capture
- **Hosting:** Self-hosted on localhost + Cloudflare tunnel
- **Cost:** £0 (everything is free/open source)

---

## What I Learned

1. **Stdio is the real API.** Most MCP servers speak stdio, not HTTP. Building a stdio-to-WebSocket bridge was the hardest part.

2. **Verification beats documentation.** "Works on my machine" is useless. Runtime evidence is what matters.

3. **MCP servers crash a lot.** Out of 20 servers I tested, 3 failed to start, 7 had tool errors, and 10 passed. The verification engine caught all of it.

4. **The ecosystem needs curation.** 1000+ servers but no quality signal. Verification badges could be that signal.

---

## Looking For

- **Beta testers** who build or use MCP servers daily
- **MCP server authors** who want their server verified
- **Feedback** on what features matter most

Beta testers get free lifetime Pro access + name in credits.

---

**Questions? Ask me anything.** I've been deep in the MCP protocol for months and happy to share what I learned.
