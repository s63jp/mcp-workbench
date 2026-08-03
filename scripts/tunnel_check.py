#!/usr/bin/env python3
"""
External health check - calls the tunnel from outside perspective.
If tunnel is down, sends notification but cannot restart (gateway blocks).
"""
import urllib.request
import urllib.error
import sys

TUNNEL_URL = "https://mcp-workbench.uk"

def check_health():
    try:
        resp = urllib.request.urlopen(f"{TUNNEL_URL}/api/health", timeout=10)
        data = resp.read().decode()
        print(f"✅ Tunnel healthy: {TUNNEL_URL}")
        print(f"Response: {data}")
        return 0
    except urllib.error.HTTPError as e:
        print(f"⚠️ HTTP {e.code}: Tunnel may be rate-limited")
        return 1
    except Exception as e:
        print(f"❌ Tunnel DOWN: {e}")
        print(f"URL: {TUNNEL_URL}")
        print("\nACTION NEEDED: Restart cloudflared manually or run:")
        print("  pkill cloudflared; cloudflared tunnel --url http://localhost:3460")
        return 2

if __name__ == "__main__":
    exit(check_health())
