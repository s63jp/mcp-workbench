# MCP Workbench API — Server Directory

## Overview

The MCP Server Directory provides a curated list of MCP servers with verification status, test mode, and CCS badge support.

## Base URL
- Local: `http://localhost:3460`
- Production: `https://mcp-workbench.uk`
- Tunnel: `https://while-workplace-rome-beautiful.trycloudflare.com`

---

## Endpoints

### List MCP Servers
```
GET /api/mcp-servers
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| category | string | Filter by category (e.g., `browser-automation`, `database`) |
| verified | boolean | Show only verified servers |
| limit | integer | Max results (default: 50) |
| offset | integer | Pagination offset (default: 0) |

**Response:**
```json
{
  "servers": [
    {
      "id": 1,
      "name": "Playwright MCP",
      "slug": "playwright-mcp",
      "description": "Official Microsoft MCP server for browser automation",
      "category": "browser-automation",
      "verified": true,
      "ccs_score": 0.92,
      "test_mode_enabled": true,
      "rating": 4.8,
      "install_count": 1243,
      "github_url": "https://github.com/microsoft/playwright-mcp",
      "npm_package": "@playwright/mcp"
    }
  ],
  "count": 8
}
```

---

### Get Server Details
```
GET /api/mcp-servers/{slug}
```

**Response:**
```json
{
  "id": 1,
  "name": "Playwright MCP",
  "slug": "playwright-mcp",
  "description": "Official Microsoft MCP server for browser automation",
  "url": null,
  "github_url": "https://github.com/microsoft/playwright-mcp",
  "npm_package": "@playwright/mcp",
  "category": "browser-automation",
  "verified": true,
  "ccs_verification_id": "mw-ccs-a1b2c3d4e5f6",
  "ccs_score": 0.92,
  "test_mode_enabled": true,
  "rating": 4.8,
  "install_count": 1243,
  "created_at": "2026-08-04T18:03:37Z",
  "badge_url": "/api/integrations/ccs/badge/mw-ccs-a1b2c3d4e5f6",
  "embed_code": "<img src='/api/integrations/ccs/badge/mw-ccs-a1b2c3d4e5f6' alt='CCS Protocol Compliant'/>"
}
```

---

### Test Mode
```
GET /api/mcp-servers/{slug}/test-mode
```

**Description:** Simulates a full MCP connection test without requiring credentials.

**Response:**
```json
{
  "server_id": "playwright-mcp",
  "test_mode": true,
  "status": "connected",
  "connection_time_ms": 245,
  "tests": {
    "startup": {"passed": true, "duration_ms": 45, "details": "Server process launched successfully"},
    "initialization": {"passed": true, "duration_ms": 120, "details": "JSON-RPC initialize handshake successful"},
    "tool_discovery": {"passed": true, "duration_ms": 80, "details": "3 tools discovered"},
    "schema_validation": {"passed": true, "duration_ms": 0, "details": "All tool schemas valid"}
  },
  "verification_summary": {
    "total_tests": 4,
    "passed": 4,
    "failed": 0,
    "overall_status": "verified"
  }
}
```

---

### Categories
```
GET /api/mcp-servers/categories
```

**Response:**
```json
{
  "categories": ["browser-automation", "database", "filesystem", "http", "integration", "search"]
}
```

---

### Add Server (Admin/Authenticated)
```
POST /api/mcp-servers
```

**Body:**
```json
{
  "name": "Playwright MCP",
  "slug": "playwright-mcp",
  "description": "Official Microsoft MCP server for browser automation",
  "github_url": "https://github.com/microsoft/playwright-mcp",
  "npm_package": "@playwright/mcp",
  "category": "browser-automation",
  "test_mode_enabled": true
}
```

---

## Authentication

- **Public endpoints:** No auth required
- **Protected endpoints:** Bearer token or API key

---

## Categories

| Category | Description |
|----------|-------------|
| browser-automation | Browser control via Playwright, Puppeteer |
| database | Database servers (SQLite, PostgreSQL) |
| filesystem | File system operations |
| http | HTTP request handling |
| integration | Third-party service integration (GitHub) |
| search | Search engines (Brave Search) |

---

## CCS Integration

Servers can be verified by CCS (Correctover Conformity Check Service):

1. **Verify:** `POST /api/integrations/ccs/verify` with 7-dimension report
2. **Badge:** `GET /api/integrations/ccs/badge/{verification_id}` (public SVG)
3. **Report:** `GET /api/integrations/ccs/report/{verification_id}` (auth required)

**Color coding:**
- Green ≥90% (Compliant)
- Yellow ≥70% (Conditional)
- Red <70% (Review Needed)

---

## Rate Limits

- 100 requests per 60-second window per IP
- No limits for authenticated users

---

*Generated: 2026-08-04 | MCP Workbench v3.0.0*
