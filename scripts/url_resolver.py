#!/usr/bin/env python3
"""
Dynamic URL resolver for MCP Workbench.
Ensures all outbound content uses the CURRENT tunnel URL.
"""
import os
import subprocess
import time

URL_FILE = "/home/kali/mcp-workbench/.current_tunnel_url"

def get_current_url():
    """Get current tunnel URL from file or regenerate."""
    if os.path.exists(URL_FILE):
        with open(URL_FILE) as f:
            url = f.read().strip()
        # Test if still valid
        try:
            import urllib.request
            urllib.request.urlopen(f"{url}/api/health", timeout=5)
            return url
        except:
            pass
    
    # Need to get new URL
    return regenerate_tunnel()

def regenerate_tunnel():
    """Kill old tunnel, start new one, save URL."""
    # Kill old tunnels
    subprocess.run(["pkill", "-f", "cloudflared"], capture_output=True)
    time.sleep(2)
    
    # Start new tunnel
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:3460"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    
    # Wait for URL
    url = None
    for _ in range(30):  # 30 seconds max
        line = proc.stdout.readline()
        if "trycloudflare.com" in line:
            import re
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                url = match.group(0)
                break
        time.sleep(1)
    
    if url:
        with open(URL_FILE, 'w') as f:
            f.write(url)
        return url
    
    return None

def replace_url_in_text(text, old_url=None):
    """Replace any old tunnel URLs with current URL."""
    current = get_current_url()
    if not current:
        return text
    
    # Replace known old URLs
    known_urls = [
        "beads-elsewhere-fighters-saskatchewan.trycloudflare.com",
        "mexico-dan-cincinnati-alternatives.trycloudflare.com",
    ]
    
    for old in known_urls:
        text = text.replace(old, current.replace("https://", ""))
    
    return text

if __name__ == "__main__":
    print(get_current_url())
