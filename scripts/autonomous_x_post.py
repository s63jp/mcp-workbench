#!/usr/bin/env python3
"""
Autonomous X/Twitter posting script for MCP Workbench.
Uses fresh Firefox session cookies to post promotional content.

Requires: Firefox logged into X with valid session
"""
import asyncio
import json
import os
import random
import sqlite3
import shutil
import subprocess
import sys
from datetime import datetime

PROJECT_DIR = "/home/kali/mcp-workbench"
COOKIES_FILE = f"{PROJECT_DIR}/scripts/.x_cookies.json"

def extract_fresh_cookies():
    """Extract current X auth cookies from Firefox."""
    firefox_db = "/home/kali/.mozilla/firefox/teveem2z.default-esr/cookies.sqlite"
    if not os.path.exists(firefox_db):
        print("ERROR: Firefox cookies not found")
        return None
    
    temp_db = "/tmp/cookies_auto.sqlite"
    try:
        shutil.copy2(firefox_db, temp_db)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT name, value FROM moz_cookies WHERE host LIKE '%x.com%' AND name IN ('auth_token','ct0','gt','twid')")
        cookies = {row[0]: row[1] for row in c.fetchall()}
        conn.close()
        
        if 'auth_token' not in cookies:
            return None
            
        with open(COOKIES_FILE, 'w') as f:
            json.dump(cookies, f)
        return cookies
    except Exception as e:
        print(f"ERROR extracting cookies: {e}")
        return None

def get_stored_cookies():
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE) as f:
            return json.load(f)
    return None

TWEETS = [
    {
        "text": "🔧 MCP Workbench beta is LIVE!\n\nTest MCP servers in your browser. Zero terminal needed.\n\n✅ Connect instantly\n✅ Test tools visually\n✅ Debug with JSON console\n\nBuilt for: Claude, Cursor, VS Code + MCP\n\nJoin beta → {url}/beta.html\n\nDM for feedback 💬",
        "hashtags": "#MCP #AI #DevTools #BuildInPublic"
    },
    {
        "text": "🤖 Building with MCP servers?\n\nStop debugging cryptic stdio errors. MCP Workbench gives you a visual testing environment.\n\n• Tool schema inspection\n• Live parameter testing\n• JSON-RPC console\n\nTry it: {url}\n\n#ClaudeAI #CursorAI #VSCode #AIAgents",
        "hashtags": "#MCP #OpenSource #DevTools"
    },
    {
        "text": "💡 MCP tip of the day:\n\nUse MCP Workbench to validate your server before deploying to Claude Desktop or Cursor.\n\nCatch errors early. Save hours of debugging.\n\n🔗 {url}/beta.html\n\nWhat's your biggest MCP pain point? 👇",
        "hashtags": "#MCP #AITools #DeveloperTools #BuildInPublic"
    },
    {
        "text": "🚀 The MCP ecosystem is exploding.\n\n1000+ community servers and counting. But testing them is still painful.\n\nMCP Workbench fixes that.\n\nVisual testing. Zero config. Browser-based.\n\nTry the beta → {url}\n\n#AI #LLM #MCP #Claude",
        "hashtags": "#DevTools #OpenAI #ArtificialIntelligence"
    },
    {
        "text": "🧪 Beta testers wanted!\n\nMCP Workbench — a web UI for testing MCP servers.\n\nLooking for:\n• Claude/Cursor/VS Code users\n• MCP server builders\n• AI tooling enthusiasts\n\nFree lifetime Pro for early feedback 🎁\n\nApply: {url}/beta.html\n\n#BetaTesting #MCP #AI",
        "hashtags": "#DevCommunity #BuildInPublic"
    }
]

async def post_tweet(tweet_text):
    """Post a tweet using browser automation with Playwright."""
    # This requires a browser automation script
    # For now, we'll write a JavaScript snippet that can be injected
    print(f"[TWEET] {tweet_text[:80]}...")
    # TODO: Implement actual browser posting via Playwright or similar
    return True

def main():
    print("=" * 60)
    print(f"Autonomous X Posting — {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Get fresh cookies
    cookies = extract_fresh_cookies()
    if not cookies:
        print("ERROR: Cannot extract X cookies. User may not be logged in.")
        sys.exit(1)
    
    print(f"✅ Cookies extracted (auth_token: {cookies.get('auth_token', 'N/A')[:10]}...)")
    
    # Select a tweet
    url = "https://beads-elsewhere-fighters-saskatchewan.trycloudflare.com"
    tweet_template = random.choice(TWEETS)
    tweet_text = tweet_template["text"].format(url=url)
    
    # Add hashtags if they fit
    if len(tweet_text) + len(tweet_template["hashtags"]) < 280:
        tweet_text += "\n\n" + tweet_template["hashtags"]
    
    print(f"\n[TWEET CONTENT]\n{tweet_text}\n")
    print(f"[LENGTH] {len(tweet_text)} chars")
    
    # Save tweet to queue for browser automation to pick up
    queue_file = f"{PROJECT_DIR}/scripts/.tweet_queue.json"
    queue = []
    if os.path.exists(queue_file):
        with open(queue_file) as f:
            queue = json.load(f)
    
    queue.append({
        "text": tweet_text,
        "timestamp": datetime.now().isoformat(),
        "status": "queued"
    })
    
    with open(queue_file, 'w') as f:
        json.dump(queue[-5:], f, indent=2)  # Keep last 5
    
    print(f"✅ Tweet queued. Use browser automation to post.")
    print(f"Queue file: {queue_file}")

if __name__ == "__main__":
    main()
