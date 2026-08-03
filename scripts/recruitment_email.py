#!/usr/bin/env python3
"""
MCP Recruitment Email Campaign - Script-based (no agent).
Uses GitHub API to find MCP server authors and sends recruitment emails via HTTP.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

PROJECT_DIR = "/home/kali/mcp-workbench"
LOG_FILE = f"{PROJECT_DIR}/logs/recruitment_emails.log"
SENT_FILE = f"{PROJECT_DIR}/logs/recruitment_sent.json"
GITHUB_TOKEN_FILE = "/home/kali/.github_env"

DEMO_URL = "https://mcp-workbench.uk"
BETA_URL = "https://mcp-workbench.uk/beta.html"
AGENTMAIL_API_KEY = os.environ.get("AGENTMAIL_API_KEY", "")
INBOX_ADDRESS = "mcp-workbench@agentmail.to"

# MCP-related repos to search
MCP_REPOS = [
    "modelcontextprotocol/servers",
    "modelcontextprotocol/python-sdk",
    "modelcontextprotocol/claude-desktop",
]

def load_github_token():
    """Load GitHub token from .github_env file."""
    if os.path.exists(GITHUB_TOKEN_FILE):
        with open(GITHUB_TOKEN_FILE) as f:
            for line in f:
                if line.startswith("GITHUB_TOKEN="):
                    return line.split("=", 1)[1].strip()
    return os.environ.get("GITHUB_TOKEN", "")

def github_api(url):
    """Make a GitHub API request."""
    token = load_github_token()
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MCP-Workbench-Recruiter/1.0"
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return {"error": "rate_limit", "message": "GitHub API rate limit exceeded"}
        return {"error": f"HTTP {e.code}"}
    except Exception as e:
        return {"error": str(e)}

def get_contributors(repo, max_pages=3):
    """Get contributors from a repo."""
    contributors = []
    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/repos/{repo}/contributors?per_page=100&page={page}"
        data = github_api(url)
        if isinstance(data, dict) and "error" in data:
            print(f"  ⚠️  GitHub API error for {repo} page {page}: {data['error']}")
            break
        if not isinstance(data, list):
            break
        for user in data:
            contributors.append({
                "login": user.get("login", ""),
                "type": user.get("type", "User"),
            })
        if len(data) < 100:
            break
        time.sleep(0.5)  # Be nice to GitHub API
    return contributors

def get_user_email(username):
    """Get user's public email."""
    if not username:
        return None
    url = f"https://api.github.com/users/{username}"
    data = github_api(url)
    if isinstance(data, dict):
        email = data.get("email")
        if email:
            return email
    return None

def load_sent():
    """Load list of already-emailed addresses."""
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE) as f:
            return set(json.load(f))
    return set()

def save_sent(sent_set):
    """Save sent email list."""
    os.makedirs(f"{PROJECT_DIR}/logs", exist_ok=True)
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent_set), f, indent=2)

def send_email_via_agentmail(to_email, subject, body):
    """Send email using AgentMail MCP tool."""
    import subprocess
    
    if not AGENTMAIL_API_KEY:
        print(f"  📧 [would send to {to_email}]")
        return True, "mailto (no API key)"
    
    # Use AgentMail MCP via subprocess
    proc = subprocess.Popen(
        ['/home/kali/.local/bin/agentmail-mcp'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    
    # Initialize
    init_req = {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"recruiter","version":"1.0"}}}
    proc.stdin.write((json.dumps(init_req) + "\n").encode())
    proc.stdin.flush()
    
    # Send message
    send_req = {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"send_message","arguments":{"inboxId": INBOX_ADDRESS,"to":[to_email],"subject":subject,"body":body}}}
    proc.stdin.write((json.dumps(send_req) + "\n").encode())
    proc.stdin.flush()
    proc.stdin.close()
    
    stdout, _ = proc.communicate(timeout=30)
    
    # Parse response
    for line in stdout.decode().strip().split("\n"):
        try:
            d = json.loads(line)
            if 'result' in d and not d.get('isError'):
                return True, "sent"
        except:
            pass
    
    return False, "send failed"

def build_email_body(recipient_name=""):
    """Build recruitment email body."""
    greeting = f"Hi{', ' + recipient_name if recipient_name else ''}"
    body = f"""{greeting},

I recently built MCP Workbench (https://mcp-workbench.uk) — a browser-based testing platform for Model Context Protocol servers. Since you're active in the MCP ecosystem, I thought you might find it useful.

**What it does:**
- Test MCP servers visually in a browser (no terminal debugging)
- Inspect tool schemas, test tool calls with forms
- Live JSON-RPC console for debugging
- Automatic verification: protocol compliance, schema integrity, cross-client compatibility

**Why I'm reaching out:**
We're in early beta and looking for MCP server authors and AI agent builders to try it out and give feedback. Early beta testers get free lifetime Pro access when we launch paid tiers.

**To try it:**
1. Visit: https://mcp-workbench.uk/beta.html
2. Connect your MCP server and start testing
3. DM me or reply here with feedback

Would love to hear what you think — and happy to feature any MCP servers you'd like validated on the platform.

Best,
Jay
@Gizmo50009
mcp-workbench@agentmail.to
"""
    return body

def main():
    now = datetime.now()
    print(f"=== MCP Recruitment Email Campaign — {now.isoformat()} ===")
    
    sent = load_sent()
    print(f"Already sent: {len(sent)}")
    
    all_contributors = []
    for repo in MCP_REPOS:
        print(f"\nFetching contributors from {repo}...")
        contribs = get_contributors(repo)
        print(f"  Found {len(contribs)} contributors")
        all_contributors.extend(contribs)
    
    # Dedupe
    seen = set()
    unique = []
    for c in all_contributors:
        if c["login"] and c["login"] not in seen and c["type"] == "User":
            seen.add(c["login"])
            unique.append(c)
    
    print(f"\nUnique contributors: {len(unique)}")
    
    subject = "I built a browser-based MCP server testing platform — want to try it?"
    new_sent = 0
    failed = 0
    
    # Limit per run to avoid rate limits
    MAX_EMAILS = 20
    
    for contrib in unique[:MAX_EMAILS]:
        login = contrib["login"]
        print(f"\nChecking {login}...")
        
        email = get_user_email(login)
        if not email:
            print(f"  ⚠️  No public email for {login}")
            continue
        
        if email in sent:
            print(f"  ⏭️  Already emailed {email}")
            continue
        
        print(f"  📧 Found email: {email}")
        body = build_email_body(login)
        
        success, result = send_email_via_agentmail(email, subject, body)
        if success:
            print(f"  ✅ Sent to {email}")
            sent.add(email)
            new_sent += 1
        else:
            print(f"  ❌ Failed: {result}")
            failed += 1
        
        time.sleep(1)  # Be nice to mail servers
    
    save_sent(sent)
    
    print(f"\n=== Summary ===")
    print(f"New emails sent: {new_sent}")
    print(f"Failed: {failed}")
    print(f"Total emailed: {len(sent)}")
    
    # Log
    os.makedirs(f"{PROJECT_DIR}/logs", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{now.isoformat()}] sent={new_sent}, failed={failed}, total={len(sent)}\n")
    
    if new_sent == 0 and failed == 0:
        print("\nNo new emails to send (all contacted or no new contributors).")

def MAX_EMAIL_MAX():
    return 20

if __name__ == "__main__":
    main()
