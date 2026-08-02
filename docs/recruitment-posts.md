# Reddit Post Draft — r/LocalLLaMA

**Title:** [Showoff Sunday] MCP Workbench — A web UI to test MCP servers (no terminal needed)

**Body:**

Hey all,

I built MCP Workbench because I was tired of debugging MCP servers in the terminal.

**What it does:**
- Paste your MCP server command, click Connect
- Instantly see available tools and their schemas
- Test tool calls with parameters right in the browser
- Get raw JSON-RPC logs for debugging

**Try it:** https://beads-elsewhere-fighters-saskatchewan.trycloudflare.com

**Why I built it:** The #1 pain point I see on GitHub issues is MCP servers failing to install/connect. This removes the guesswork.

**Looking for beta testers:** If you actively use Claude, Cursor, or VS Code with MCP servers, DM me or comment. Free lifetime Pro access for early feedback.

Built with Next.js + TypeScript + Tailwind. £0 budget bootstrapped project.

---

# Hacker News Post Draft

**Title:** Show HN: MCP Workbench — Postman for MCP servers

**Body:**

MCP (Model Context Protocol) servers let AI assistants connect to external tools, but testing them is painful. You need to edit JSON configs, restart your AI client, and hope it works.

I built MCP Workbench to solve this. It's a zero-config web interface where you paste a server command and immediately see available tools, test them, and get compatibility reports.

**Live demo:** https://beads-elsewhere-fighters-saskatchewan.trycloudflare.com

**Features:**
- Visual tool discovery and parameter inspection
- Real-time JSON-RPC console
- Saved server configurations
- Compatibility reports for Claude, Cursor, VS Code

**Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS. Deployed on a temporary Cloudflare tunnel (moving to Vercel soon).

I'm looking for beta testers — especially developers building custom MCP servers. Free Pro access for early adopters.

---

# Discord/Slack Message (MCP, Cursor, Cline communities)

**Title:** 🧪 Beta Testers Wanted: MCP Workbench

**Body:**

Hey builders! I made MCP Workbench — a web UI to test MCP servers without touching the terminal.

🔗 Live: https://beads-elsewhere-fighters-saskatchewan.trycloudflare.com

What you get:
✅ Connect to any MCP server in seconds
✅ See tool schemas visually
✅ Test tool calls with form inputs
✅ JSON-RPC debug console

What I need:
🙏 Beta testers who use MCP daily (Claude, Cursor, VS Code)
🙏 Feedback on what's missing or broken
🙏 Feature requests from real use cases

Perks:
🎁 Free lifetime Pro access
🎁 Name in credits
🎁 Direct dev access (me!)

DM me or comment below. Building in public at @Gizmo50009 on X.
