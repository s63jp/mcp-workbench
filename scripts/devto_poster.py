#!/usr/bin/env python3
"""
Dev.to Poster for MCP Workbench - Script-based (no agent).
Picks a topic based on current hour and posts to Dev.to API.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

API_KEY = "z7oC3Psnc5TeduTRZPET1t3U"
BASE_URL = "https://dev.to/api"
PROJECT_DIR = "/home/kali/mcp-workbench"
CONTENT_DIR = f"{PROJECT_DIR}/content"

# Topic rotation by hour (0-23)
TOPICS = {
    0: ("MCP ecosystem overview", ["mcp", "ai", "devtools"]),
    4: ("Verification engine deep dive", ["mcp", "ai", "testing"]),
    8: ("Building with MCP servers", ["mcp", "ai", "development"]),
    12: ("Hermes Verification Engine philosophy", ["mcp", "hermes", "ai"]),
    16: ("Beta recruitment + feature showcase", ["mcp", "beta", "devtools"]),
    20: ("MCP server testing tutorial", ["mcp", "testing", "tutorial"]),
}

DEMO_URL = "https://mcp-workbench.uk"
BETA_URL = "https://mcp-workbench.uk/beta.html"

def load_content(filename):
    path = f"{CONTENT_DIR}/{filename}"
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return None

def get_topic_for_hour(hour):
    """Get topic info for the current hour."""
    # Round down to nearest 4-hour slot
    slot = (hour // 4) * 4
    topic_key = slot if slot in TOPICS else 0
    return TOPICS[topic_key]

def post_article(title, body, tags, published=True):
    """Post article to Dev.to API."""
    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
        "User-Agent": "MCP-Workbench/1.0"
    }
    payload = {
        "article": {
            "title": title,
            "body_markdown": body,
            "tags": tags,
            "published": published
        }
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/articles",
        data=data,
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return True, result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else str(e)
        return False, f"HTTP {e.code}: {body}"
    except Exception as e:
        return False, str(e)

def main():
    now = datetime.now()
    hour = now.hour
    topic_name, tags = get_topic_for_hour(hour)
    
    print(f"=== Dev.to Poster — {now.isoformat()} ===")
    print(f"Topic slot: {hour}h → {topic_name}")
    print(f"Tags: {', '.join(tags)}")
    
    # Load content files
    article1 = load_content("article-1-verification.md")
    article5 = load_content("article-5-beta-announcement.md")
    
    # Select article based on topic
    if "verification" in topic_name.lower() or "tutorial" in topic_name.lower():
        body = article1
        title_prefix = "Why MCP Servers Need Verification Before Production"
    elif "beta" in topic_name.lower() or "recruitment" in topic_name.lower():
        body = article5
        title_prefix = "MCP Workbench Beta Is Live"
    elif "ecosystem" in topic_name.lower():
        body = article1[:2000] if article1 else None  # Truncated overview
        title_prefix = "The MCP Ecosystem in 2026"
    elif "philosophy" in topic_name.lower():
        body = article1[1000:3500] if article1 and len(article1) > 1000 else article1
        title_prefix = "The Case for MCP Server Verification"
    else:
        body = article1 if article1 else article5
        title_prefix = f"MCP Workbench: {topic_name}"
    
    if not body:
        print("ERROR: No content found")
        sys.exit(1)
    
    # Add canonical links to body
    footer = f"\n\n---\n\n🔗 [Try MCP Workbench live]({DEMO_URL})\n🔗 [Join the beta]({BETA_URL})\n"
    body = body + footer
    
    # Truncate if too long (Dev.to limit ~30000 chars)
    if len(body) > 28000:
        body = body[:28000] + "\n\n*(truncated)...*"
    
    title = f"{title_prefix} | MCP Workbench"
    
    print(f"Title: {title}")
    print(f"Body length: {len(body)} chars")
    print(f"Posting to Dev.to...")
    
    success, result = post_article(title, body, tags, published=True)
    
    if success and isinstance(result, dict):
        url = result.get("url", "unknown")
        article_id = result.get("id", "unknown")
        print(f"✅ Published! Article ID: {article_id}")
        print(f"   URL: {url}")
        
        # Save last post info
        state_file = f"{PROJECT_DIR}/logs/devto_last_post.json"
        os.makedirs(f"{PROJECT_DIR}/logs", exist_ok=True)
        with open(state_file, "w") as f:
            json.dump({
                "timestamp": now.isoformat(),
                "article_id": article_id,
                "url": url,
                "topic": topic_name
            }, f, indent=2)
    else:
        print(f"❌ Failed: {result}")
        sys.exit(1)

if __name__ == "__main__":
    main()
