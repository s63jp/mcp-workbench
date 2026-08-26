---
title: "Building an MCP Server Directory: A Technical Deep-Dive with Real API Examples"
published: false
description: >
  Learn how to build, test, and publish MCP servers using the MCP Workbench API.
  This guide covers the directory API, test mode simulation, and server verification
  with working code examples.
tags: mcp, ai, api, testing
canonical_url: https://mcp-workbench.uk
cover_image: null
---

# Building an MCP Server Directory: A Technical Deep-Dive

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) is rapidly becoming the standard for connecting AI agents to external tools. But as the ecosystem grows, developers need a way to discover, test, and verify MCP servers before production use. That's why we built the MCP Server Directory API in [MCP Workbench](https://mcp-workbench.uk).

In this post, I'll show you exactly how the directory API works — with real endpoints, real responses, and the test mode feature that simulates MCP connections without credentials.

## The MCP Server Directory API

The directory is a public REST API with no authentication required for reads. Here's the base URL:

```
Local:  http://localhost:3460
Prod:   https://mcp-workbench.uk
```

### Listing Servers

```bash
GET /api/mcp-servers
```

```bash
curl "http://localhost:3460/api/mcp-servers?limit=3"
```

**Response:**

```json
{
  "servers": [
    {
      "id": 18,
      "name": "Grafana",
      "slug": "grafana",
      "description": "Query and visualize metrics from Grafana datasources",
      "category": "observability",
      "verified": false,
      "test_mode_enabled": false,
      "rating": 0.0,
      "install_count": 0,
      "github_url": "https://github.com/grafana/grafana-mcp"
    },
    {
      "id": 17,
      "name": "OWASP ZAP",
      "slug": "owasp-zap",
      "description": "Web application security scanner and penetration testing",
      "category": "security",
      "verified": false,
      "test_mode_enabled": false,
      "rating": 0.0,
      "install_count": 0,
      "github_url": "https://github.com/zaproxy/zaproxy-mcp"
    }
  ],
  "count": 3
}
```

### Filtering by Category

```bash
curl "http://localhost:3460/api/mcp-servers?category=security"
```

Available categories: `ai-ml`, `browser-automation`, `database`, `development`, `filesystem`, `http`, `integration`, `observability`, `search`, `security`

### Getting Server Details

```bash
GET /api/mcp-servers/{slug}
```

```bash
curl "http://localhost:3460/api/mcp-servers/playwright-mcp"
```

**Response:**

```json
{
  "id": 1,
  "name": "Playwright MCP",
  "slug": "playwright-mcp",
  "description": "Official Microsoft MCP server for browser automation",
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

## Test Mode: Simulate Connections Without Credentials

This is the feature developers ask for most: how do you verify an MCP server works before spending time on credentials and configuration?

The `/test-mode` endpoint simulates a full MCP connection handshake:

```bash
GET /api/mcp-servers/{slug}/test-mode
```

```bash
curl "http://localhost:3460/api/mcp-servers/playwright-mcp/test-mode"
```

**Response:**

```json
{
  "server_id": "playwright-mcp",
  "test_mode": true,
  "status": "connected",
  "connection_time_ms": 245,
  "tests": {
    "startup": {
      "passed": true,
      "duration_ms": 45,
      "details": "Server process launched successfully"
    },
    "initialization": {
      "passed": true,
      "duration_ms": 120,
      "details": "JSON-RPC initialize handshake successful"
    },
    "tool_discovery": {
      "passed": true,
      "duration_ms": 80,
      "details": "3 tools discovered"
    },
    "schema_validation": {
      "passed": true,
      "duration_ms": 0,
      "details": "All tool schemas valid"
    }
  },
  "verification_summary": {
    "total_tests": 4,
    "passed": 4,
    "failed": 0,
    "overall_status": "verified"
  }
}
```

Test mode validates four critical dimensions:

1. **Startup** — Can the server process launch?
2. **Initialization** — Does the JSON-RPC handshake succeed?
3. **Tool Discovery** — Are tools properly advertised?
4. **Schema Validation** — Are tool schemas well-formed?

## Adding a Server to the Directory

Authenticated users can add servers via `POST /api/mcp-servers`:

```bash
curl -X POST "http://localhost:3460/api/mcp-servers" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Custom MCP Server",
    "slug": "my-custom-mcp",
    "description": "A custom MCP server for my use case",
    "github_url": "https://github.com/user/my-mcp-server",
    "npm_package": "@user/my-mcp",
    "category": "development",
    "test_mode_enabled": true
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Display name |
| `slug` | string | Yes | URL-safe identifier (unique) |
| `description` | string | Yes | What the server does |
| `github_url` | string | No | GitHub repository |
| `npm_package` | string | No | npm package name |
| `category` | string | Yes | One of the available categories |
| `test_mode_enabled` | boolean | No | Enable test mode simulation |

## The CCS Verification Badge

Servers that pass the [Correctover Conformity Check (CCS)](https://correctover.com) get a verification badge:

```html
<img src="/api/integrations/ccs/badge/mw-ccs-a1b2c3d4e5f6" alt="CCS Protocol Compliant"/>
```

The badge is color-coded:
- **Green** (≥90%) — Compliant
- **Yellow** (≥70%) — Conditional
- **Red** (<70%) — Review Needed

## Rate Limits

- **Public:** 100 requests per 60-second window per IP
- **Authenticated:** No limits

## What's Next?

The MCP Workbench directory is designed for the growing ecosystem of MCP servers. Whether you're:

- Building a new MCP server and want early feedback
- Maintaining an existing server and want verification
- Looking for servers in a specific category

...the directory API gives you programmatic access to the ecosystem.

**Live at:** [https://mcp-workbench.uk](https://mcp-workbench.uk)  
**API Docs:** [https://mcp-workbench.uk/api-docs](https://mcp-workbench.uk/api-docs)  
**GitHub:** [https://github.com/mcp-workbench/mcp-workbench](https://github.com/mcp-workbench/mcp-workbench)
