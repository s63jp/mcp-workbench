# CCS Integration API Spec (Draft)
# For discussion with Correctover sync

POST /api/integrations/ccs/verify
Request:
{
  "server_id": "playwright-mcp",
  "ccs_report": {
    "report_id": "ccs-2026-08-04-001",
    "dimensions": {
      "structure": {"passed": true, "score": 0.95, "details": "..."},
      "schema": {"passed": true, "score": 0.98, "details": "..."},
      "latency": {"passed": true, "score": 0.87, "details": "..."},
      "cost": {"passed": true, "score": 1.0, "details": "..."},
      "identity": {"passed": false, "score": 0.72, "details": "..."},
      "integrity": {"passed": true, "score": 0.91, "details": "..."},
      "security": {"passed": true, "score": 0.89, "details": "..."}
    },
    "overall_score": 0.90,
    "verified_at": "2026-08-04T12:00:00Z",
    "report_url": "https://correctover.ccs/reports/ccs-2026-08-04-001"
  }
}

Response:
{
  "badge_url": "https://mcp-workbench.uk/badges/ccs-compliant.svg",
  "embed_code": "<img src='https://mcp-workbench.uk/badges/ccs-compliant.svg' alt='CCS Protocol Compliant'/>",
  "verification_id": "mw-ccs-2026-08-04-001",
  "directory_url": "https://mcp-workbench.uk/servers/playwright-mcp",
  "expires_at": "2026-11-04T12:00:00Z"
}

GET /api/integrations/ccs/badge/:verification_id
Returns: SVG badge with 7-dimension breakdown on hover

Webhook (optional):
POST /api/webhooks/ccs/verify
Called by CCS when new verification is complete
