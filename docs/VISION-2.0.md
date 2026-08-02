# MCP Workbench — Vision Document 2.0

> From "Postman for MCP" to "AI Operating System for MCP"

## The Elevator Pitch

MCP Workbench isn't just a testing tool. It's becoming the **definitive place where developers build, test, secure, benchmark and publish MCP servers**.

Think: **VS Code for MCP** × **Docker Desktop for AI agents** × **Postman for MCP servers**

## Core Identity (What We ARE)

The AI Operating System for MCP servers. Not a dashboard. Not a registry. The runtime environment where MCP servers live, breathe, and prove themselves.

---

## Feature Architecture

### Layer 1: Discovery & Catalog 🔍
- Public MCP server directory with ratings
- Search by capability, protocol version, framework
- Author profiles and reputation
- Community reviews and trust scores

### Layer 2: Testing & Validation 🧪
- Visual tool discovery and parameter inspection
- Live tool call testing with form inputs
- Raw JSON-RPC console
- **Hermes Verification Engine (HVE) Integration**

### Layer 3: Verification & Trust 🔒
Every MCP server gets a verification badge:

| Status | Meaning |
|--------|---------|
| 🟢 **Verified** | Passed full HVE test suite |
| 🟡 **Untested** | Submitted but not verified |
| 🔴 **Failed** | Failed verification — see logs |

**Clicking a verification badge shows:**
- Startup logs
- Benchmark speed (tools/second)
- Memory usage profile
- Tool coverage analysis
- Hallucination rate (false positives)
- Runtime evidence (last 10 executions)
- Last successful execution timestamp

### Layer 4: Performance Metrics 📊
- Execution latency per tool
- Memory footprint over time
- Connection stability score
- Error rate tracking
- Resource usage graphs

### Layer 5: Security Scanning 🔐
- Static analysis of server code
- Permission audit (what files/system access)
- Network activity monitoring
- Data exfiltration detection
- Sandbox execution reports

### Layer 6: Version History 📜
- Git-like versioning for MCP servers
- Changelog generation
- Breaking change detection
- Migration guides between versions
- Dependency graph

### Layer 7: AI Documentation 🤖
- Auto-generated tool descriptions
- Usage examples from real executions
- Parameter explanations
- Best practices suggestions
- Troubleshooting guides

### Layer 8: Shared Memory 💾
- Context persistence across tool calls
- Session state management
- Multi-turn conversation support
- Tool call chain visualization

### Layer 9: Multi-Agent Orchestration 🧠
- Compose multiple MCP servers
- Agent workflow designer
- Parallel execution planning
- Result aggregation strategies
- Conflict resolution

### Layer 10: Live Execution Graphs 📈
- Real-time tool call visualization
- Execution flow diagrams
- Decision tree rendering
- Performance heatmaps
- Bottleneck identification

---

## Hermes Verification Engine (HVE) Integration

### Philosophy: Runtime Evidence Over Assumptions

Every MCP server claim must be backed by evidence.

**Verification Test Suite:**

```
HVE-MCP-v1 Test Protocol
├── 1. Startup Verification
│   ├── Clean startup (< 5s)
│   ├── No stderr errors
│   └── Protocol version match
│
├── 2. Tool Discovery Verification
│   ├── tools/list returns within 2s
│   ├── All advertised tools present
│   └── Schema validation (Zod/TypedDict)
│
├── 3. Tool Call Verification
│   ├── Basic call with required params
│   ├── Optional params handled
│   ├── Error cases return proper errors
│   └── Edge cases (empty, null, large)
│
├── 4. Performance Benchmarks
│   ├── Cold start time
│   ├── Warm tool call latency (p50, p95, p99)
│   ├── Memory at idle vs under load
│   └── Max concurrent requests
│
├── 5. Security Audit
│   ├── File system access scope
│   ├── Network requests (if any)
│   ├── Environment variable access
│   └── Child process spawning
│
├── 6. Stability Test
│   ├── 24h soak test (if applicable)
│   ├── Connection/disconnection cycles
│   └── Memory leak detection
│
└── 7. Evidence Capture
    ├── Screenshot of successful run
    ├── Performance metrics JSON
    └── Video/gif of interaction (optional)
```

**Verification Status Display:**
```
┌─────────────────────────────────────────────┐
│ 🟢 Verified — 7/7 tests passed              │
│                                             │
│ Startup:     ✅ 1.2s                        │
│ Discovery:   ✅ 0.4s                        │
│ Tool Calls:  ✅ 12/12 passed               │
│ Performance: ✅ p50=45ms, p95=120ms         │
│ Security:    ✅ No fs access beyond scope   │
│ Stability:   ✅ 24h soak passed             │
│                                             │
│ Last run:    2026-08-02 18:32:48 UTC       │
│ Evidence:    [View Logs] [Benchmarks]       │
└─────────────────────────────────────────────┘
```

---

## Competitive Differentiation

| Competitor | What They Do | What MCP Workbench Does |
|---|---|---|
| **Smithery** | Registry + installer | We RUN and VERIFY servers, not just list them |
| **MCP-get** | Package manager | We TEST before you install |
| **Toolbase** | Config manager | We VALIDATE configs work |
| **Turbo MCP** | Enterprise platform | We BENCHMARK and provide evidence |
| **Claude Desktop** | Client | We BUILD the servers it consumes |

**Our moat:** Nobody else provides runtime verification with evidence.

---

## Revenue Model (Updated)

### Free Tier
- Test public MCP servers
- Basic verification (startup + discovery)
- Community support

### Pro ($9/mo)
- Private server testing
- Full HVE verification suite
- Saved configurations
- Performance history
- Export reports (PDF/JSON)

### Team ($29/mo/seat)
- Shared verification dashboards
- CI/CD webhook integration
- Custom verification pipelines
- Slack notifications
- Audit logs

### Enterprise (Custom)
- On-premise deployment
- Custom security policies
- SSO (SAML, OIDC)
- Dedicated support

---

## Technical Architecture v2

### Current Stack
- Frontend: Next.js 16 + React 19 + Tailwind v4
- Backend: Python aiohttp (MCP proxy)
- Storage: Local JSON files

### Future Stack
- Frontend: Next.js + shadcn/ui + Recharts (graphs)
- Backend: Python FastAPI + Celery (background verification)
- Database: PostgreSQL (Supabase) + Redis (job queue)
- Verification: HVE engine (async workers)
- Analytics: InfluxDB + Grafana
- Security: gVisor sandboxes

---

## Milestones

### Phase 1: Foundation (DONE)
- ✅ Basic MCP testing UI
- ✅ WebSocket proxy
- ✅ Beta signup
- ✅ GitHub repo

### Phase 2: Verification Engine (Month 1-2)
- [ ] HVE integration
- [ ] Automated test suite
- [ ] Verification badges
- [ ] Evidence capture

### Phase 3: Performance (Month 2-3)
- [ ] Benchmarking system
- [ ] Metrics dashboard
- [ ] Historical comparison
- [ ] Performance regression alerts

### Phase 4: Security (Month 3-4)
- [ ] Static analysis
- [ ] Sandbox execution
- [ ] Permission audit
- [ ] Vulnerability scanning

### Phase 5: Community (Month 4-6)
- [ ] Public server directory
- [ ] Ratings and reviews
- [ ] Version history
- [ ] AI-generated docs

### Phase 6: Enterprise (Month 6-12)
- [ ] Team workspaces
- [ ] CI/CD integration
- [ ] On-premise option
- [ ] Custom policies

---

## Hermes Ecosystem Integration

This isn't competing with Hermes. It's **complementing** it.

| Hermes Component | MCP Workbench Role |
|---|---|
| HVE (Verification) | We run HVE on every MCP server |
| Agent Runtime | We provide the tools agents consume |
| Business Automation | We attract the developers who build those businesses |
| Cron Jobs | We schedule verification runs |
| Session Memory | We store server test histories |

**The flywheel:**
1. Developers use MCP Workbench to build servers
2. Those servers power Hermes agents
3. Agents validate demand for more servers
4. More developers join MCP Workbench
5. Better servers = better agents = more adoption

---

## Closing Thought

> "Runtime evidence over assumptions"

This isn't just a feature. It's the philosophy that separates MCP Workbench from every other tool in the ecosystem.

When a developer sees 🟢 Verified, they don't just see a badge. They see **proof** that this MCP server works, performs, and is safe to use.

That's the definitive place.

---

*Document version: 2.0*
*Author: Strategic feedback + Hermes agent synthesis*
*Last updated: 2026-08-03*
