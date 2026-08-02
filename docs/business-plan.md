# MCP Workbench — Business Plan

> **Version:** 1.0  
> **Date:** August 2026  
> **Status:** Pre-launch (MVP in development)  
> **Budget:** £0 (bootstrapped)

---

## 1. Executive Summary

**MCP Workbench** is a web-based testing, validation, and development platform for Model Context Protocol (MCP) servers. Positioned as “Postman for MCP servers,” it solves the #1 pain point in the MCP ecosystem: servers failing to install or configure correctly. Unlike existing registries (Smithery, MCP-get, Toolbase), MCP Workbench provides a **visual, interactive testing environment** where developers can verify server behavior before deployment.

Our freemium model captures individual developers with a free public-testing tier, then monetises through a Pro tier (£9/mo) for private-server workflows and a Team tier (£29/mo) for collaborative CI/CD and audit requirements. The product is built on a modern, low-cost stack (Next.js 14, Tailwind, Supabase, Cloudflare Workers, Stripe) and is being launched with zero external funding.

---

## 2. Market Opportunity

### 2.1 Problem Statement
MCP (Model Context Protocol) is rapidly becoming the standard for connecting AI models to external tools and data sources. However:
- **Installation friction** is the top reported pain point in community surveys and GitHub issues.
- **No visual debugging** exists; developers rely on terminal logs and trial-and-error.
- **Configuration drift** across environments (local, staging, production) causes silent failures.

### 2.2 Target Market
| Segment | Description | Est. Size (2026) |
|---------|-------------|------------------|
| **Primary** | Indie / freelance AI developers building MCP servers | ~45,000 |
| **Secondary** | AI startups & agencies shipping MCP integrations | ~8,000 |
| **Tertiary** | Enterprise platform teams standardising MCP internally | ~2,500 |

### 2.3 Market Trends
- MCP adoption is accelerating alongside agentic AI frameworks (e.g., Claude, Cursor, Cline).
- Developer-tool spend is shifting toward “pre-flight” validation to reduce production incidents.
- Visual, browser-based devtools (Postman, Insomnia, Bruno) command high engagement and retention.

---

## 3. Competitive Analysis

### 3.1 Direct Competitors

| Competitor | Type | Strength | Weakness vs. MCP Workbench |
|------------|------|----------|---------------------------|
| **Smithery** | Registry / catalogue | Large listing; community stars | No interactive testing; static READMEs only |
| **MCP-get** | CLI installer | Quick install scripts | No validation or visual feedback; breaks silently |
| **Toolbase** | Registry + discovery | Good SEO; categorisation | No runtime testing; no CI/CD integration |

### 3.2 Indirect Competitors
- **Postman / Insomnia / Bruno** — General HTTP/API testing tools. They do not understand MCP protocol semantics (tools, resources, prompts, sampling).
- **Custom Python scripts** — Ad-hoc testing by individual developers. Non-shareable, non-repeatable, high maintenance.

### 3.3 Competitive Advantage (Moat)
1. **Protocol-native UI** — Built specifically for MCP’s tool/resource/prompt model, not generic REST.
2. **Zero-config sandbox** — Cloud-hosted workers spin up isolated MCP environments in seconds.
3. **Compatibility reports** — Automated matrix testing across MCP protocol versions and host implementations.
4. **CI/CD webhooks** — Team tier integrates with GitHub Actions, GitLab CI, etc.

---

## 4. Revenue Model

### 4.1 Pricing Tiers

| Tier | Price | Audience | Features |
|------|-------|----------|----------|
| **Free** | £0/mo | Individual developers, OSS contributors | Public server testing, basic validation, community templates |
| **Pro** | £9/mo | Freelancers, small teams, indie hackers | Private servers, saved configurations, compatibility reports, exportable test suites |
| **Team** | £29/mo / seat | Startups, agencies, platform teams | Everything in Pro + shared configs, CI/CD webhooks, audit logs, SAML SSO (v1.2) |

### 4.2 Unit Economics (Target)
- **Free-to-Pro conversion:** 5–8 % (industry benchmark for devtools).
- **Pro-to-Team uplift:** 15 % of Pro accounts upgrade within 12 months.
- **Average Revenue Per User (ARPU):** ~£14/mo blended (year 1).
- **Gross margin:** 85 %+ (cloud infra amortised across free users).

### 4.3 Additional Revenue Streams (Future)
- **Certified MCP Server badges** — Paid verification programme for commercial server publishers.
- **On-premise / Enterprise licence** — £500+/mo for air-gapped environments (Year 2).

---

## 5. Marketing Strategy

### 5.1 Positioning
> “The only visual debugger and test harness built for MCP servers. Ship with confidence.”

### 5.2 Channels (Zero-Budget Priority)
| Channel | Tactic | KPI |
|---------|--------|-----|
| **GitHub** | Open-source starter templates; automated issues/PR replies | Stars, forks, referral traffic |
| **Reddit / Hacker News / X** | Launch posts, Show HN, MCP-themed threads | Upvotes, sign-ups, mentions |
| **Newsletter / Blog** | Weekly “MCP Compatibility Report” + deep-dive tutorials | Subscribers, organic traffic |
| **Community** | Discord server; office hours; AMAs with MCP core contributors | DAU, NPS |
| **SEO** | Long-tail guides: “How to test MCP servers,” “MCP server troubleshooting” | Organic SERP ranking |

### 5.3 Launch Sequence
1. **Week 0:** Private beta (50 hand-picked MCP authors).
2. **Week 2:** Public beta with “Free forever” messaging.
3. **Week 4:** Product Hunt + Hacker News launch.
4. **Week 6:** First paid-tier announcement with early-bird discount (50 % off first 3 months).

---

## 6. Customer Acquisition Plan

### 6.1 Acquisition Funnel
```
Awareness (Content, GitHub, Reddit)
    ↓
Sign-up (Free tier — email + GitHub OAuth)
    ↓
Activation (First successful test run within 24 h)
    ↓
Engagement (3+ test runs / week, 1 saved config)
    ↓
Conversion (Pro upgrade — private server or report export)
    ↓
Expansion (Team upgrade — invite colleague, enable CI webhook)
```

### 6.2 Tactics by Stage
| Stage | Tactic | Owner |
|-------|--------|-------|
| **Awareness** | GitHub README badges, MCP ecosystem roundup posts, X threads | Founder / Community |
| **Sign-up** | Frictionless OAuth (GitHub, Google); no credit card required | Product |
| **Activation** | Onboarding wizard pre-fills a popular MCP server (e.g., filesystem) | Product |
| **Engagement** | Weekly “Test Health” email digest; Discord #showcase channel | Growth / Community |
| **Conversion** | In-app paywall at private-server creation; limited-time discount banner | Product / Marketing |
| **Expansion** | Team invitation credits; “Add CI webhook” CTA after 10th test run | Product |

### 6.3 CAC Targets (Month 1–12)
- **Organic:** £0 (primary channel; founder-led content).
- **Paid (experimental):** < £20 / Pro customer (Google Ads, Reddit promoted posts — only after £1k MRR).

---

## 7. Financial Projections

### 7.1 Assumptions
- Launch: Month 1 (M).
- Free users grow via organic channels only.
- Conversion rates: 5 % free → Pro; 15 % Pro → Team (by Month 12).
- No salaries (bootstrapped; founder time only).
- Infra costs absorbed by generous free tiers of Supabase + Cloudflare (pay-as-you-go thereafter).

### 7.2 6-Month Projection (Months 1–6)

| Metric | Month 1 | Month 2 | Month 3 | Month 4 | Month 5 | Month 6 |
|--------|---------|---------|---------|---------|---------|---------|
| Free sign-ups | 200 | 400 | 700 | 1,000 | 1,300 | 1,600 |
| Total free users | 200 | 600 | 1,300 | 2,300 | 3,600 | 5,200 |
| Pro conversions | 0 | 10 | 25 | 45 | 70 | 100 |
| Team seats | 0 | 0 | 2 | 5 | 10 | 18 |
| **MRR** | **£0** | **£90** | **£283** | **£550** | **£1,070** | **£1,422** |
| Infra costs | £0 | £0 | £20 | £40 | £70 | £100 |
| Stripe fees (1.5 %) | £0 | £1 | £4 | £8 | £16 | £21 |
| **Net margin** | **£0** | **£89** | **£259** | **£502** | **£984** | **£1,301** |

### 7.3 12-Month Projection (Months 7–12)

| Metric | Month 7 | Month 8 | Month 9 | Month 10 | Month 11 | Month 12 |
|--------|---------|---------|---------|----------|----------|----------|
| Free sign-ups | 1,900 | 2,200 | 2,500 | 2,800 | 3,100 | 3,400 |
| Total free users | 7,100 | 9,300 | 11,800 | 14,600 | 17,700 | 21,100 |
| Pro conversions | 140 | 185 | 240 | 300 | 375 | 460 |
| Team seats | 28 | 42 | 58 | 78 | 102 | 132 |
| **MRR** | **£2,072** | **£2,883** | **£3,842** | **£4,962** | **£6,333** | **£7,908** |
| Infra costs | £140 | £190 | £250 | £320 | £410 | £520 |
| Stripe fees | £31 | £43 | £58 | £74 | £95 | £119 |
| **Net margin** | **£1,901** | **£2,650** | **£3,534** | **£4,568** | **£5,828** | **£7,269** |

### 7.4 Annual Summary (Year 1)
- **Total ARR at Month 12:** ~£94,900
- **Total net revenue (Year 1):** ~£28,000 (cumulative after costs)
- **Break-even:** Immediate (no paid staff or office)
- **Year 2 runway:** Self-funded from Year 1 profits; no external capital required unless accelerating to Enterprise tier.

---

## 8. Product Roadmap

### 8.1 MVP (Month 1–2)
**Goal:** Validate that developers will visually test MCP servers.

| Feature | Description |
|---------|-------------|
| Public MCP server tester | Paste a server URL or `npx` command; run in Cloudflare Worker sandbox |
| Tool/resource explorer | Visual tree of exposed tools, resources, and prompts |
| Basic validation | Protocol-version check; required-env-var detection |
| Shareable test links | Permalink to a test result for GitHub issues / Discord |
| GitHub OAuth login | Identity + public-profile read for community features |

**Success criteria:** 200 sign-ups; 50 % activate within 24 h; 10 % run 3+ tests.

### 8.2 v1 (Month 3–5)
**Goal:** Monetise power users and enable private-server workflows.

| Feature | Description |
|---------|-------------|
| **Pro tier paywall** | Private servers, unlimited saved configs, compatibility reports |
| Saved configurations | JSON/YAML export + import; version history |
| Compatibility matrix | Automated testing against MCP spec versions (2024-11-05, 2025-03-01, etc.) |
| Team collaboration | Shared workspaces (Team tier) |
| CI/CD webhooks | GitHub Actions trigger + status badge generation |
| Stripe billing portal | Self-serve upgrade/downgrade/invoicing |

**Success criteria:** 50 Pro customers; 3 Team accounts; £1,000 MRR.

### 8.3 v2 (Month 6–9)
**Goal:** Become the standard toolchain for MCP quality assurance.

| Feature | Description |
|---------|-------------|
| **Mock MCP host** | Simulate Claude, Cursor, Cline behaviours to test edge cases |
| Regression test suites | Scheduled nightly runs; diff reports between versions |
| Audit logs & compliance | SOC-2-aligned export (Team tier) |
| Marketplace / templates | Curated MCP server blueprints with one-click deploy |
| On-premise Enterprise pilot | Docker Compose package for air-gapped teams |
| Public API | Programmatic test execution for custom integrations |

**Success criteria:** 400 Pro customers; 20 Team accounts; £7,000 MRR.

---

## 9. Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| R01 | **MCP protocol changes** break our validation logic | High | High | Subscribe to MCP spec RFCs; maintain compatibility matrix; 48-hour patch SLA |
| R02 | **Competitor clones** our visual testing concept | Medium | Medium | Speed-to-market; community moat via GitHub stars & content; freemium network effects |
| R03 | **Low free-to-paid conversion** (< 3 %) | Medium | High | Tighten Pro feature gating; add usage-based alerts; introduce annual discount (2 months free) |
| R04 | **Cloudflare / Supabase free-tier limits** exceeded before revenue | Medium | Medium | Aggressive caching; rate-limit free tier; apply for startup credits; move to pay-as-you-go from Month-3 profits |
| R05 | **Security incident** in sandboxed worker (RCE, data exfil) | Low | Critical | Firecracker/mini-VM isolation; ephemeral 60-second workers; no persistent FS; bug-bounty programme |
| R06 | **Founder burnout / time constraints** (bootstrapped, £0 budget) | High | Medium | Ruthless MVP scope; defer non-core features; open-source community contributions; seek advisory (not investment) |
| R07 | **Market apathy** — MCP adoption stalls | Low | Critical | Diversify toward general “AI tool testing”; maintain API-agnostic layer; monitor Anthropic / OpenAI roadmap |
| R08 | **Stripe / payment regulatory issues** (EU VAT, SCA) | Medium | Low | Stripe Tax automatic compliance; price in GBP/USD; invoice generation for Team accounts |

---

## 10. Key Metrics Dashboard

Track weekly:
- **North Star:** Weekly Active Testers (WAT) — users who execute ≥1 test.
- **Acquisition:** Sign-up rate, organic traffic %, GitHub referral traffic.
- **Activation:** Time-to-first-test (target < 5 min).
- **Retention:** Week-4 retention rate (target > 30 %).
- **Revenue:** MRR, ARPU, Net Revenue Retention (NRR), churn rate.
- **Infrastructure:** Sandbox cold-start latency, error rate, cost per 1,000 tests.

---

*End of Business Plan — MCP Workbench*
