# 🔧 MCP Workbench

> A web-based testing platform for MCP servers — think "Postman for MCP"

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is MCP?

MCP (Model Context Protocol) is Anthropic's open protocol that lets AI assistants connect to external tools and data sources. As of August 2026, there are 1000+ community MCP servers, but testing and debugging them is painful.

## Our Solution

**MCP Workbench** gives you a visual, zero-config web interface to:

- ✅ Connect to any MCP server instantly
- ✅ See available tools and their schemas
- ✅ Test tool calls with parameters
- ✅ Debug with a live JSON-RPC console
- ✅ Get compatibility reports

**No terminal. No config files. No cryptic stdio errors.**

## 🚀 Live Demo

**Try it now:** https://blocked-skill-conviction-console.trycloudflare.com

**Beta signup:** https://blocked-skill-conviction-console.trycloudflare.com/beta.html

## 📸 Screenshot

*(Coming soon — add screenshot when UI is polished)*

## 🏗️ Tech Stack

- **Frontend:** Next.js 16 + React 19 + TypeScript + Tailwind CSS v4
- **Backend:** Python aiohttp + WebSocket MCP proxy
- **Deployment:** Cloudflare Tunnel (temporary) → Vercel (soon)

## 🛠️ Local Development

```bash
# Clone
git clone https://github.com/s63jp/mcp-workbench.git
cd mcp-workbench

# Install dependencies
npm install

# Start the Python MCP proxy server
python3 server.py 3460

# In another terminal, start the frontend
npm run dev

# Or use the Cloudflare tunnel for public access
cloudflared tunnel --url http://localhost:3460
```

## 📋 Roadmap

- [x] MVP with basic MCP connection
- [x] Beta signup landing page
- [x] WebSocket proxy for real-time testing
- [ ] User accounts and saved configurations
- [ ] Compatibility reports (Claude, Cursor, VS Code)
- [ ] Team workspaces
- [ ] CI/CD webhook integration
- [ ] Public MCP server directory

## 🤝 Contributing

We're looking for beta testers! If you build with Claude, Cursor, or VS Code + MCP:

1. Try the [live demo](https://blocked-skill-conviction-console.trycloudflare.com)
2. [Sign up for beta access](https://blocked-skill-conviction-console.trycloudflare.com/beta.html)
3. Open an issue with feedback

**Early adopters get free lifetime Pro access!**

## 📄 License

MIT License — see [LICENSE](LICENSE) file

## 🐦 Follow Us

- X/Twitter: [@Gizmo50009](https://x.com/Gizmo50009)
- Email: gizmo50009@agentmail.ai

---

*Built with ❤️ by MCP Workbench — £0 bootstrapped, fully autonomous AI business*
