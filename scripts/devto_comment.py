#!/usr/bin/env python3
"""
Post comments on Dev.to articles using Firefox session.
Uses Playwright with Firefox cookies from your browser.
"""
import asyncio
import json
import os
import shutil
import sqlite3

FIREFOX_DB = "/home/kali/.mozilla/firefox/teveem2z.default-esr/cookies.sqlite"
COOKIES_FILE = "/tmp/devto_cookies.json"

def extract_devto_cookies():
    """Extract Dev.to cookies from Firefox."""
    if not os.path.exists(FIREFOX_DB):
        print("ERROR: Firefox cookies not found")
        return None
    
    temp_db = "/tmp/devto_comment.sqlite"
    try:
        shutil.copy2(FIREFOX_DB, temp_db)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("""
            SELECT name, value, host, path, isSecure, isHttpOnly 
            FROM moz_cookies 
            WHERE host LIKE '%dev.to%'
        """)
        cookies = []
        for row in c.fetchall():
            cookies.append({
                'name': row[0],
                'value': row[1],
                'domain': row[2],
                'path': row[3],
                'secure': bool(row[4]),
                'httpOnly': bool(row[5])
            })
        conn.close()
        os.remove(temp_db)
        
        with open(COOKIES_FILE, 'w') as f:
            json.dump(cookies, f, indent=2)
        return cookies
    except Exception as e:
        print(f"ERROR: {e}")
        return None

async def post_comment(page, article_slug, comment_text):
    """Post a comment on a Dev.to article."""
    url = f"https://dev.to/{article_slug}"
    print(f"Navigating to {url}")
    await page.goto(url, wait_until='networkidle')
    
    # Wait for comment box to appear
    await page.wait_for_selector('textarea', timeout=10000)
    
    # Fill comment
    await page.fill('textarea', comment_text)
    
    # Submit - try Ctrl+Enter or button
    await page.keyboard.press('Control+Enter')
    await asyncio.sleep(2)
    
    print(f"✅ Comment posted on {article_slug}")

async def main():
    # Extract cookies
    cookies = extract_devto_cookies()
    if not cookies:
        print("Failed to get cookies")
        return
    
    print(f"Extracted {len(cookies)} Dev.to cookies")
    
    # Get articles with comments
    articles_with_comments = [
        {
            'slug': 'jaypee_2de6db397980219fcd/how-to-debug-mcp-server-connection-issues-in-60-seconds-18bd',
            'comment': "Great points from both of you! Reid - you're right about the protocol state issue after the Jul 28 MCP draft. Bartek - the session id reuse problem is exactly what our compatibility reports aim to catch. MCP Workbench tests across multiple clients including forced reconnects to catch exactly these issues. We'd love to feature your servers in our directory at https://mcp-workbench.uk"
        }
    ]
    
    # Use Playwright with Firefox context
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        # Launch Firefox (persistent context)
        context = await p.firefox.launch_persistent_context(
            user_data_dir='/tmp/devto_browser',
            headless=True
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Go to Dev.to to set cookies
        await page.goto('https://dev.to', wait_until='networkidle')
        
        # Inject cookies
        for cookie in cookies:
            try:
                await context.add_cookies([{
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie['domain'],
                    'path': cookie['path'],
                    'secure': cookie['secure'],
                    'httpOnly': cookie['httpOnly']
                }])
            except:
                pass
        
        # Post comments
        for article in articles_with_comments:
            try:
                await post_comment(page, article['slug'], article['comment'])
            except Exception as e:
                print(f"Error posting comment: {e}")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
