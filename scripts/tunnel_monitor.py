#!/usr/bin/env python3
"""
Tunnel Health Monitor - EXTERNAL check only.
Cannot restart tunnel from inside gateway (SIGTERM blocked).
Will alert when tunnel is down so user can restart manually.
"""
import urllib.request
import urllib.error
import os
import json
from datetime import datetime

TUNNEL_URL = "https://blocked-skill-conviction-console.trycloudflare.com"
LOG_FILE = "/home/kali/mcp-workbench/logs/tunnel-monitor.log"

def log(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.now().isoformat()
    line = f"{ts} | {msg}"
    with open(LOG_FILE, 'a') as f:
        f.write(line + "\n")
    print(line)

def check_tunnel():
    try:
        resp = urllib.request.urlopen(f"{TUNNEL_URL}/api/health", timeout=10)
        data = json.loads(resp.read().decode())
        log(f"✅ Healthy: {TUNNEL_URL}")
        return 0
    except Exception as e:
        log(f"❌ DOWN: {e}")
        log("ACTION: Run 'pkill cloudflared' then restart tunnel from outside gateway")
        return 1

if __name__ == "__main__":
    exit(check_tunnel())
