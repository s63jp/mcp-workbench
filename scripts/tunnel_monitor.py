#!/usr/bin/env python3
"""
Tunnel Monitor + Auto-Restarter for MCP Workbench.
Runs every 30 minutes via cron to ensure tunnel stays alive.
"""
import subprocess
import time
import re
import os
import glob
import json
from datetime import datetime

PROJECT_DIR = "/home/kali/mcp-workbench"
URL_FILE = f"{PROJECT_DIR}/.current_tunnel_url"
LOG_FILE = f"{PROJECT_DIR}/logs/tunnel-monitor.log"

def log(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.now().isoformat()
    with open(LOG_FILE, 'a') as f:
        f.write(f"{ts} | {msg}\n")
    print(msg)

def test_url(url):
    """Test if tunnel URL is responding."""
    try:
        import urllib.request
        urllib.request.urlopen(f"{url}/api/health", timeout=8)
        return True
    except:
        return False

def restart_tunnel():
    """Kill old tunnel and start new one."""
    log("Restarting Cloudflare tunnel...")
    
    # Kill old tunnels
    subprocess.run(["pkill", "-f", "cloudflared"], capture_output=True)
    time.sleep(3)
    
    # Clean old log
    if os.path.exists("/tmp/tunnel.log"):
        os.remove("/tmp/tunnel.log")
    
    # Start new tunnel
    with open("/tmp/tunnel.log", "w") as logf:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", "http://localhost:3460"],
            stdout=logf, stderr=subprocess.STDOUT
        )
    
    # Wait for URL
    url = None
    for _ in range(30):
        time.sleep(1)
        if os.path.exists("/tmp/tunnel.log"):
            with open("/tmp/tunnel.log") as f:
                content = f.read()
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', content)
                if match:
                    url = match.group(0)
                    break
    
    if url:
        with open(URL_FILE, 'w') as f:
            f.write(url)
        log(f"New tunnel URL: {url}")
        update_all_urls(url)
        return url
    else:
        log("ERROR: Failed to get new tunnel URL")
        return None

def update_all_urls(new_url):
    """Update all documentation with new tunnel URL."""
    old_url = None
    if os.path.exists(URL_FILE):
        with open(URL_FILE) as f:
            old_url = f.read().strip()
    
    if not old_url or old_url == new_url:
        return
    
    old_domain = old_url.replace("https://", "")
    new_domain = new_url.replace("https://", "")
    
    files_to_update = []
    for ext in ["*.md", "*.py", "*.html", "*.json", "*.sh", "*.txt"]:
        files_to_update.extend(glob.glob(f"{PROJECT_DIR}/**/{ext}", recursive=True))
    
    updated = 0
    for filepath in files_to_update:
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            if old_domain in content:
                new_content = content.replace(old_domain, new_domain)
                with open(filepath, 'w') as f:
                    f.write(new_content)
                updated += 1
        except:
            pass
    
    log(f"Updated {updated} files with new URL")
    
    try:
        subprocess.run(["git", "add", "-A"], cwd=PROJECT_DIR, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"auto: tunnel URL update to {new_domain}"],
            cwd=PROJECT_DIR, capture_output=True
        )
        log("Git commit complete")
    except:
        pass

def main():
    log("=== Tunnel Health Check ===")
    
    current_url = None
    if os.path.exists(URL_FILE):
        with open(URL_FILE) as f:
            current_url = f.read().strip()
    
    if current_url and test_url(current_url):
        log(f"Healthy: {current_url}")
        return 0
    
    log(f"Unhealthy/expired: {current_url}")
    new_url = restart_tunnel()
    
    if new_url:
        log(f"Restored: {new_url}")
        return 0
    else:
        log("FAILED to restore tunnel")
        return 1

if __name__ == "__main__":
    exit(main())
