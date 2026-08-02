#!/usr/bin/env python3
"""Health check for MCP Workbench site."""
import urllib.request
import urllib.error
import sys
import json
import os
from datetime import datetime, timezone

# Site to check
SITE_URL = os.environ.get("MCP_WORKBENCH_URL", "https://mcp-workbench.vercel.app")
TIMEOUT_SECONDS = int(os.environ.get("MCP_WORKBENCH_TIMEOUT", "30"))
REPORT_PATH = os.environ.get("MCP_WORKBENCH_REPORT", "/home/kali/mcp-workbench/docs/daily_report.json")

def check_site(url: str, timeout: int = TIMEOUT_SECONDS) -> dict:
    """Return {ok: bool, status: int, latency_ms: float, error: str|null}."""
    result = {"ok": False, "status": None, "latency_ms": None, "error": None}
    start = datetime.now(timezone.utc)
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "MCP-Workbench-HealthBot/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency = (datetime.now(timezone.utc) - start).total_seconds() * 1000
            result["ok"] = 200 <= resp.status < 400
            result["status"] = resp.status
            result["latency_ms"] = round(latency, 2)
    except urllib.error.HTTPError as e:
        latency = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        result["status"] = e.code
        result["latency_ms"] = round(latency, 2)
        result["error"] = f"HTTPError {e.code}: {e.reason}"
        result["ok"] = 200 <= e.code < 400
    except urllib.error.URLError as e:
        result["error"] = f"URLError: {e.reason}"
    except Exception as e:
        result["error"] = f"Exception: {type(e).__name__}: {e}"
    return result

def fetch_github_trends() -> dict:
    """Check GitHub trending topics for MCP."""
    result = {"searched_at": datetime.now(timezone.utc).isoformat() + "Z", "topics": []}
    try:
        req = urllib.request.Request(
            "https://api.github.com/search/topics?q=mcp",
            headers={
                "Accept": "application/vnd.github.mercy-preview+json",
                "User-Agent": "MCP-Workbench-HealthBot/1.0",
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result["topics"] = [
                {"name": t.get("name"), "display_name": t.get("display_name")}
                for t in data.get("items", [])[:5]
            ]
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
    return result

def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}Z] Checking {SITE_URL}...")
    site = check_site(SITE_URL)
    print(f"  OK={site['ok']} Status={site['status']} Latency={site['latency_ms']}ms Error={site['error']}")
    print(f"  Fetching GitHub trends...")
    trends = fetch_github_trends()
    print(f"  Found {len(trends.get('topics', []))} trending MCP topics.")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "site": site,
        "github_trends": trends,
    }
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report written to {REPORT_PATH}")
    sys.exit(0 if site["ok"] else 1)

if __name__ == "__main__":
    main()
