#!/usr/bin/env python3
"""
Reddit bot for MCP Workbench using PRAW (Reddit API)
Post to r/LocalLLaMA and other relevant subreddits.
"""
import praw
import json
import sys
import os
from datetime import datetime

# Reddit API credentials from environment
CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET', '')
USERNAME = os.environ.get('REDDIT_USERNAME', '')
PASSWORD = os.environ.get('REDDIT_PASSWORD', '')

SUBREDDIT = 'LocalLLaMA'
TITLE = "Show MCP: Built a testing platform that verifies MCP servers with runtime evidence"

BODY = """Hi r/LocalLLaMA 👋

I've been building with MCP servers for a few months and kept hitting the same problem:

**"This MCP server looks cool but does it actually work?"**

You install it, configure it, run it... and get cryptic stdio errors. No visibility. No debugging. Just trial and error.

So I built **MCP Workbench** — a web-based testing platform for MCP servers.

**What it does:**
• Connect MCP servers in your browser (no terminal)
• Test tools visually with a JSON console
• Debug with live logs
• Get a verification badge: 🟢 Verified / 🟡 Untested / 🔴 Failed

**The verification engine** tests:
✓ Startup time
✓ Tool discovery speed
✓ Call validation
✓ Memory usage
✓ Error handling

No more "it works on my machine." Just runtime evidence.

**Try it:** https://mcp-workbench.uk

**GitHub (open source):** https://github.com/s63jp/mcp-workbench

**Beta signup:** https://mcp-workbench.uk/beta.html

🎁 Beta testers get free lifetime Pro access + name in credits.

What MCP servers are you using? Let me know and I'll verify them!
"""

def post_to_reddit():
    """Post the prepared content to Reddit."""
    
    if not all([CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD]):
        print("Missing Reddit API credentials!")
        print("Set these env vars:")
        print("  REDDIT_CLIENT_ID")
        print("  REDDIT_CLIENT_SECRET")
        print("  REDDIT_USERNAME")
        print("  REDDIT_PASSWORD")
        return False
    
    try:
        reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            username=USERNAME,
            password=PASSWORD,
            user_agent='MCPWorkbench/1.0'
        )
        
        subreddit = reddit.subreddit(SUBREDDIT)
        
        # Check if we can post
        print(f"Logged in as: {reddit.user.me()}")
        print(f"Posting to: r/{SUBREDDIT}")
        
        # Submit post
        submission = subreddit.submit(TITLE, selftext=BODY)
        print(f"✅ Posted successfully!")
        print(f"   URL: {submission.url}")
        print(f"   ID: {submission.id}")
        
        # Save to log
        log_file = '/home/kali/mcp-workbench/docs/posted_reddit.json'
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
        except:
            logs = []
        
        logs.append({
            'date': datetime.now().isoformat(),
            'subreddit': SUBREDDIT,
            'title': TITLE,
            'url': submission.url,
            'id': submission.id
        })
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"❌ Error posting to Reddit: {e}")
        return False

if __name__ == '__main__':
    success = post_to_reddit()
    sys.exit(0 if success else 1)
