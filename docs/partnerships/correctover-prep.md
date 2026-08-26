# Correctover Sync Prep — August 5, 2026

## Lead Context
**Correctover** (wangguigui@correctover.com) — Security research company with CCS (Conformity Check Service) product. They did a static code analysis of Playwright MCP and want to integrate with MCP Workbench.

**GitHub Issue:** microsoft/playwright-mcp#1694 (Security Architecture Review)
**Our Reply:** https://github.com/microsoft/playwright-mcp/issues/1694#issuecomment-5182020776

---

## Their Security Findings (Know These Cold)

| Finding | Type | Our Angle |
|---------|------|-----------|
| WebSocket bypasses HTTP Host validation | Architectural inconsistency | We test this — forced reconnects across instances, Host header injection |
| Extension Token exposed in URL | Info exposure | Our traffic logs would catch this in verification reports |
| Environment variable config override | Shared-env concern | Part of multi-tenant testing in our verification suite |
| initScript/initPage injection | Config-level risk | We validate tool schemas including script injection vectors |

**Their 3-layer defense (what they got RIGHT):**
1. localhost binding default
2. HTTP Host header validation
3. UUID path obscurity

**Their suggested fix:** `verifyClient` handler in WebSocket upgrade

**CCS Standard:** DOI 10.5281/zenodo.21603250

---

## Integration Proposal (What We'll Pitch)

### Phase 1: Listing + Test Mode (This Week)
- [ ] Create Playwright MCP test entry in our directory
- [ ] Test mode: no credentials, localhost-only simulation
- [ ] Auto-generate JSON-RPC traffic log + schema validation report
- [ ] Badge: "Verified by MCP Workbench"

### Phase 2: CCS Badge Integration (Next 2 Weeks)
- [ ] API endpoint: `POST /api/integrations/ccs/verify`
- [ ] Accepts: `{server_id, ccs_report, dimensions_passed[]}`
- [ ] Returns: `{badge_url, embed_code, verification_id}`
- [ ] Badge: "CCS Protocol Compliant" + 7-dimension breakdown

### Phase 3: Joint Pipeline (Month 2)
- [ ] Pre-publish: MCP Workbench runtime tests → CCS protocol validation
- [ ] Shared JSON Schema for unified verification reports
- [ ] Co-marketing badge: "CCS + MCP Workbench Certified"

---

## Technical Questions to Ask

1. **CCS API format** — What does their verification report JSON look like?
2. **Test endpoint** — Do they have a public Playwright MCP demo server we can test?
3. **Badge embedding** — SVG or PNG? Dynamic or static?
4. **WebSocket testing** — Do they want us to add Host header injection tests?
5. **Authentication** — How do they verify server identity in CCS checks?

---

## Demo Script (If They Want a Live Demo)

```
1. Open https://mcp-workbench.uk
2. Navigate to "Server Directory"
3. Click "Playwright MCP" (test mode)
4. Show: JSON-RPC traffic log, schema validation, latency percentiles
5. Show: Verification report with 7-dimension breakdown
6. Show: How CCS badge would appear
```

---

## Their Persona
- Technical, security-focused
- Values evidence over claims
- Proposed concrete integration points
- Academic background (DOI reference)
- Responsive and engaged

## Our Value Prop
- 35K+ stars on Playwright MCP = huge audience
- We test what they analyze — complementary, not competitive
- Badge = trust signal = developer adoption
- Free for open source servers

---

## Prep Checklist
- [x] Read their full security review
- [x] Understand CCS 7 dimensions
- [x] Draft integration phases
- [x] Prepare demo flow
- [ ] Build test endpoint for Playwright MCP
- [ ] Create CCS badge mockup
- [ ] Draft API spec for `/api/integrations/ccs`
