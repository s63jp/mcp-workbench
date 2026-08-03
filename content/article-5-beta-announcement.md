# MCP Workbench Beta Is Live: The Postman for MCP Servers

Today we're opening the MCP Workbench beta — a browser-based testing platform for Model Context Protocol servers. If you build or use MCP servers, this is the tool we wish existed six months ago.

## What Is MCP Workbench?

MCP Workbench is a visual testing environment for MCP servers. Instead of debugging cryptic stdio errors inside Claude Desktop or Cursor, you open a browser tab, paste your server command, and get instant visibility into every tool, schema, and JSON-RPC message.

**Think Postman for REST APIs, but for MCP.**

## What's in the Beta

The beta includes everything you need to validate and debug MCP servers:

### ✅ Instant Server Connection

Paste any MCP server command (e.g., `npx -y @modelcontextprotocol/server-filesystem /tmp`) and connect within seconds. Workbench handles the stdio transport, initialization handshake, and tool discovery automatically.

### ✅ Visual Tool Catalog

See every tool your server exposes with its JSON Schema, descriptions, and required parameters. No more guessing what arguments a tool expects.

### ✅ Form-Based Tool Testing

Fill out tool parameters in auto-generated forms instead of hand-crafting JSON payloads. Workbench validates inputs against the schema before sending, catching errors client-side.

### ✅ Live JSON-RPC Console

Inspect every request and response in full. Debug protocol mismatches, malformed parameters, and transport issues with complete visibility.

### ✅ Multi-Client Compatibility Checks

Test how your server behaves across Claude Desktop, Cursor, VS Code, and Cline emulators. Catch client-specific compatibility issues before your users do.

### ✅ Saved Configurations

Save and share server configurations with your team. Export to JSON or share a direct link. Everyone tests the same setup.

### ✅ Hermes Verification Engine

Every connected server is automatically validated for protocol compliance, schema integrity, error handling, and cross-client compatibility. Get a pass/fail report in seconds.

## Who Is This For?

**MCP Server Authors**: Validate your server before publishing. Catch schema errors, handshake failures, and compatibility issues in minutes instead of waiting for bug reports.

**AI Agent Builders**: Evaluate community MCP servers before integrating them into your agent. See exactly what tools a server exposes and how it handles edge cases.

**Teams**: Share server configurations, document expected behavior, and run regression tests from CI/CD pipelines.

**Learners**: See the MCP protocol in action without wrestling with local environment setup. The visual tool catalog makes the abstract concrete.

## What's Coming Next

The beta is just the beginning. Our roadmap includes:

- **User accounts and saved history**: Persistent configurations and test results
- **CI/CD webhook integration**: Trigger validation runs from your build pipeline
- **Public MCP server directory**: Browse and test community servers without installing them
- **Team workspaces**: Collaborate on server validation with shared dashboards
- **Performance profiling**: Measure tool call latency and resource usage

## How to Join

The beta is free and open now. No credit card required.

1. Visit the live demo
2. Connect your first MCP server
3. Sign up for beta access to unlock advanced features

**Early beta testers get free lifetime Pro access** when we launch paid tiers.

🔗 [Launch MCP Workbench](https://mcp-workbench.uk)

🔗 [Sign up for beta](https://mcp-workbench.uk/beta.html)

## Built by AI, for AI Developers

MCP Workbench is a £0-bootstrapped project built entirely by autonomous AI agents using the Hermes framework. Every line of code, every blog post, every design decision was made by AI — with human oversight and refinement.

We're proving that small teams (even teams of one human + AI agents) can build real products that solve real problems for the developer community.

## Get in Touch

- X/Twitter: [@Gizmo50009](https://x.com/Gizmo50009)
- Email: gizmo50009@agentmail.ai
- GitHub: (coming soon)

We read every piece of feedback. If you hit a bug, want a feature, or just want to chat about MCP, reach out.

---

*Ready to stop debugging MCP servers in the dark? Try MCP Workbench today.*
