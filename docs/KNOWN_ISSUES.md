# Known Issues — MCP Workbench v0.1.0-beta

**Last updated:** 2026-08-02
**Status:** Closed beta

---

## Failing Integration Tests (3 of 7)

These are upstream package issues, not proxy bugs. The proxy correctly reports the failure.

| Server | Symptom | Root Cause | Workaround |
|--------|---------|------------|------------|
| `@modelcontextprotocol/server-time` | Process exits before `initialize` response | Server package requires specific runtime args; spins down on initialization | None — package bug |
| `@modelcontextprotocol/server-sqlite` | "Database file required" error | Server requires a SQLite file path argument | Pass a test DB path via args |
| `@modelcontextprotocol/server-sequentialthinking` | `npm ERR! 404 Not Found` | Package does not exist on npm | Use a different reasoning server |
| `@modelcontextprotocol/server-fetch` | Connection closes before init | Network/timeout issue in upstream package | None — package bug |

---

## Supported Servers

These packages connect successfully and return tools:

| Server | Tools Discovered | Notes |
|--------|------------------|-------|
| `@modelcontextprotocol/server-filesystem` | 14 | Requires directory path argument |
| `@modelcontextprotocol/server-github` | 26 | Deprecated upstream, still functional |
| `@modelcontextprotocol/server-memory` | 9 | Knowledge graph operations |
| `@modelcontextprotocol/server-security-scanner` | 3 | Security analysis |

---

## Experimental / Limited Support

| Server | Status | Issue |
|--------|--------|-------|
| `@modelcontextprotocol/server-sentry` | Untested | Not yet validated |
| `@modelcontextprotocol/server-postgres` | Untested | May require DB connection string |
| Custom Python MCP servers | Untested | Should work via `python3` command |

---

## Current Limitations

### Functional
- **No authentication** — Anyone with the URL can use the proxy
- **No saved configurations** — Users must re-enter server commands each session
- **No tool invocation UI** — Tools are listed but not yet callable from the frontend (backend handles calls correctly)
- **No compatibility matrix** — Can't show which clients support which servers
- **No session replay** — Session recordings are saved but not viewable in-browser

### Operational
- **Temporary URL** — Cloudflare Tunnel URL changes on restart
- **No persistent storage** — Session recordings live in `sessions/` and are not indexed
- **Single-region deployment** — Running on local server; no CDN beyond Cloudflare edge
- **Manual restart required** — If server crashes, no auto-recovery

### Security
- **No rate limiting** — Endpoint can be flooded
- **No audit logging** — Security events not centrally logged
- **No user isolation** — All sessions share the same process pool

---

## Planned Improvements (v0.2 - Demand Dependent)

These are candidates based on what's frequently requested. **Do not build until validated by beta feedback.**

- [ ] User authentication (Supabase Auth or Clerk)
- [ ] Saved server configurations (per-user)
- [ ] In-browser tool invocation UI
- [ ] Compatibility matrix (server × client)
- [ ] Session replay viewer
- [ ] Rate limiting (Cloudflare WAF)
- [ ] Persistent named tunnel (custom domain)
- [ ] Pro tier billing (Stripe Checkout)
- [ ] Team collaboration features

---

## Process Cleanup (Minor)

Under rapid connect/disconnect cycles (stress test scenarios), a small number of `mcp-server` processes may occasionally persist. The server uses `start_new_session=True` + `os.killpg()` to kill entire process groups, but `npx` wrapper chains (bash → node → server) can occasionally leak.

**Severity:** Low — only occurs under artificial stress (20 connections in <10s)
**Impact:** Normal interactive use does not trigger this
**Mitigation:** Server restart cleans up all orphans (`kill_orphaned()` runs on startup)

---

## Reporting New Issues

If you encounter a bug during beta testing, please report:

1. **Which MCP server** were you connecting to?
2. **What command** did you send? (e.g., `npx -y @modelcontextprotocol/server-filesystem /tmp`)
3. **What did you expect** to happen?
4. **What actually happened?** (screenshot, console log, error message)
5. **Can you reproduce it?** (steps to trigger)

Reports to: founder@mcp-workbench.dev (or GitHub issues when repo is public)
