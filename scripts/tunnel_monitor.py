#!/usr/bin/env python3
"""
Cloudflare Tunnel Auto-Restarter for MCP Workbench.
Monitors the tunnel health and restarts with new URL if needed.
"""
import subprocess
import time
import re
import os
import json
from datetime import datetime

PROJECT_DIR = "/home/kali/mcp-workbench"
URL_FILE = f"{PROJECT_DIR}/.current_tunnel_url"
LOG_FILE = f"{PROJECT_DIR}/logs/tunnel-monitor.log"

def log(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f"{datetime.now().isoformat()} | {msg}\n")
    print(msg)

def get_current_tunnel_url():
    """Try to find existing tunnel process and extract URL."""
    try:
        result = subprocess.run(
            ["pgrep", "-a", "cloudflared"],
            capture_output=True, text=True
        )
        # URL is assigned on startup - we need to check the log file
        if os.path.exists("/tmp/tunnel.log"):
            with open("/tmp/tunnel.log") as f:
                content = f.read()
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', content)
                if match:
                    return match.group(0)
    except Exception as e:
        log(f"Error finding tunnel: {e}")
    return None

def test_url(url):
    """Test if tunnel URL is responding."""
    try:
        import urllib.request
        urllib.request.urlopen(f"{url}/api/health", timeout=5)
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
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:3460"],
        stdout=open("/tmp/tunnel.log", "w"),
        stderr=subprocess.STDOUT
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
        # Save URL
        with open(URL_FILE, 'w') as f:
            f.write(url)
        log(f"New tunnel URL: {url}")
        
        # Update all files with new URL
        update_all_urls(url)
        return url
    else:
        log("ERROR: Failed to get new tunnel URL")
        return None

def update_all_urls(new_url):
    """Update all documentation with the new tunnel URL."""
    import glob
    
    # Read current URL
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
    
    # Git commit
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=PROJECT_DIR, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", f"auto: update tunnel URL to {new_domain}"],
            cwd=PROJECT_DIR, capture_output=True
        )
        log("Git commit pushed")
    except:
        pass

def main():
    log("=== Tunnel Monitor Starting ===")
    
    # Check current URL
    current_url = None
    if os.path.exists(URL_FILE):
        with open(URL_FILE) as f:
            current_url = f.read().strip()
    
    if current_url and test_url(current_url):
        log(f"Tunnel healthy: {current_url}")
        return
    
    # URL expired or not responding
    log(f"Tunnel unhealthy or expired. Current: {current_url}")
    new_url = restart_tunnel()
    
    if new_url:
        log(f"Tunnel restored: {new_url}")
    else:
        log("FAILED to restore tunnel")

if __name__ == "__main__":
    main()
