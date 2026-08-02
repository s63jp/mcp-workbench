# MCP Workbench — A testing environment for MCP servers (like Postman, but for MCP)

**TL;DR:** Built a free browser-based tool to connect, test, and debug MCP servers without wrestling with config files or restarting your chat client. Would love feedback from anyone building or integrating MCP servers.

🔗 [https://depth-plenty-mia-similarly.trycloudflare.com](https://depth-plenty-mia-similarly.trycloudflare.com)

---

**What's the problem?**

I've been building and integrating MCP servers for a while, and the debugging experience is rough. You spin up a server, point Claude/Cursor at it, and when something breaks you have basically zero visibility. No request logs, no schema validation, no way to inspect the JSON-RPC traffic. You're just toggling things blindly and hoping the client picks up the changes.

**What I built**

MCP Workbench is a web-based testing environment that works a lot like Postman, but for MCP servers instead of REST APIs:

- **Connect** to any MCP server via stdio or HTTP
- **Discover** all exposed tools and inspect their JSON schemas
- **Invoke** tools with a form-based UI and see responses in real time
- **Inspect** raw JSON-RPC messages to debug transport or protocol issues
- **Validate** compatibility across clients (Claude, Cursor, VS Code, Cline, etc.)
- **Save** configurations and export to JSON/YAML for your team

**Why this matters**

The MCP ecosystem is growing fast — there are already servers for filesystem access, GitHub, Slack, databases, web search, and tons of custom internal tools. But as adoption scales, the pain point shifts from building servers to *knowing they work reliably* across different clients and environments. A dedicated testing tool feels like missing infrastructure.

**Pricing**

- **Free tier:** Test public MCP servers, basic validation reports, console output — no signup required
- **Pro (£9/mo):** Private testing, saved configs, compatibility reports, exports, email support
- **Team (£29/mo):** Shared workspaces, Slack notifications, CI/CD webhooks, audit logs

**Tech stack**

Frontend is Next.js + TypeScript + Tailwind. Backend handles stdio spawning, JSON-RPC proxying, and SSE streaming to the browser. It's been a fun exercise in making a protocol inspector that actually feels responsive.

**What I'd love from this community**

If you're building MCP servers locally, I'd genuinely appreciate you trying to break this. Specifically:

- Does it handle your custom server commands correctly?
- Are the schema validations accurate compared to what Claude/Cursor expect?
- Any edge cases in JSON-RPC handling that we should be aware of?
- What's missing that would make this actually useful for your workflow?

All feedback goes straight into the issue tracker. Thanks for reading — happy to answer questions in the comments.

---

*Disclaimer: This is an independent project built for the MCP community. Not affiliated with Anthropic, OpenAI, or any specific AI client.*
