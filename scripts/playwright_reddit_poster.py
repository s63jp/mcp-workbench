#!/usr/bin/env python3
"""
Playwright Reddit Poster with Firefox Cookie Injection
Posts to r/LocalLLaMA, r/MachineLearning, and r/programming
"""
import asyncio
import json
import shutil
import sqlite3
import sys
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def extract_reddit_cookies():
    """Extract Reddit cookies from Firefox profile."""
    firefox_profiles = [
        "/home/kali/.mozilla/firefox/teveem2z.default-esr/cookies.sqlite",
        "/home/kali/.mozilla/firefox/q4tlbhyt.default/cookies.sqlite",
    ]
    
    cookies = []
    for profile in firefox_profiles:
        if not os.path.exists(profile):
            continue
        
        dst = "/tmp/reddit_cookies_extract.sqlite"
        try:
            shutil.copy2(profile, dst)
        except Exception as e:
            print(f"  [!] Could not copy {profile}: {e}")
            continue
        
        db = sqlite3.connect(dst)
        cur = db.cursor()
        cur.execute("""
            SELECT name, value, host, path, isSecure, isHttpOnly 
            FROM moz_cookies 
            WHERE host LIKE '%reddit.com%'
        """)
        
        for row in cur.fetchall():
            domain = row[2]
            if domain.startswith('.'):
                domain = domain[1:]
            cookies.append({
                "name": row[0],
                "value": row[1],
                "domain": domain,
                "path": row[3] or "/",
                "secure": bool(row[4]),
                "httpOnly": bool(row[5])
            })
        
        db.close()
        
        if cookies:
            print(f"  [+] Found {len(cookies)} Reddit cookies in {profile}")
            return cookies, dst
    
    return cookies, None


def load_post_content():
    """Load the Reddit post content."""
    content_path = "/home/kali/mcp-workbench/content/reddit-post.md"
    with open(content_path) as f:
        content = f.read()
    
    # Extract title and body from the markdown content
    lines = content.strip().split('\n')
    
    # Title is the first line (without the H1 marker)
    title = lines[0].lstrip('#').strip()
    
    # Body is everything after the first H1 separator
    # Find the first --- separator
    body_lines = []
    in_body = False
    for i, line in enumerate(lines):
        if line.strip() == '---' and i > 0:
            in_body = True
            continue
        if in_body:
            body_lines.append(line)
    
    body = '\n'.join(body_lines).strip()
    return title, body


async def post_to_subreddit(browser, subreddit, title, body, link="https://mcp-workbench.uk"):
    """Post content to a specific subreddit."""
    print(f"\n[>] Posting to r/{subreddit}...")
    
    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Extract and add cookies
    cookies, db_path = await extract_reddit_cookies()
    if not cookies:
        print(f"  [!] No Reddit cookies found in Firefox")
        await context.close()
        return None
    
    for c in cookies:
        try:
            await context.add_cookies([c])
        except Exception as e:
            print(f"  [!] Could not add cookie {c['name']}: {e}")
    
    page = await context.new_page()
    
    try:
        # Navigate to Reddit login first to establish session
        print(f"  [>] Navigating to Reddit...")
        await page.goto("https://www.reddit.com", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        
        current_url = page.url
        print(f"  [>] Current URL: {current_url}")
        
        # Check if we hit a JS challenge
        if "js_challenge" in current_url or "challenge" in current_url:
            print(f"  [!] Hit JS challenge at {current_url}")
            await context.close()
            return None
        
        # Check if logged in
        page_content = await page.content()
        if " Log in" in page_content and "Sign Up" in page_content:
            print(f"  [!] Not logged in (session cookies may be expired or invalid)")
            await context.close()
            return None
        
        print(f"  [+] Logged in successfully")
        
        # Navigate to subreddit submit page
        submit_url = f"https://www.reddit.com/r/{subreddit}/submit"
        print(f"  [>] Navigating to {submit_url}...")
        await page.goto(submit_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        
        if "js_challenge" in page.url or "challenge" in page.url:
            print(f"  [!] Hit JS challenge at submit page")
            await context.close()
            return None
        
        # Take a snapshot to see form elements
        snapshot = await page.content()
        
        # Try to find and fill the title field
        print(f"  [>] Filling post form...")
        
        # Reddit's submit page has changed - try multiple approaches
        title_filled = False
        body_filled = False
        
        # Method 1: Look for title input
        title_selectors = [
            'input[name="title"]',
            'input[placeholder*="title" i]',
            'input[data-testid="title-input"]',
            'input[id="title"]',
            'input[autocomplete="off"]'
        ]
        
        for selector in title_selectors:
            if await page.locator(selector).count() > 0:
                await page.locator(selector).first.fill(title)
                title_filled = True
                print(f"  [+] Title filled using: {selector}")
                break
        
        if not title_filled:
            # Try using JavaScript
            try:
                await page.evaluate("""
                    const inputs = document.querySelectorAll('input');
                    for (const input of inputs) {
                        if (input.type === 'text' && input.closest('.submit')) {
                            input.value = arguments[0];
                            input.dispatchEvent(new Event('input', {bubbles: true}));
                            break;
                        }
                    }
                """, title)
                title_filled = True
                print(f"  [+] Title filled via JavaScript")
            except:
                print(f"  [!] Could not fill title")
        
        # Method 2: Look for body/description textarea
        body_selectors = [
            'textarea[name="text"]',
            'textarea[placeholder*="description" i]',
            'textarea[data-testid="description-input"]',
            'textarea[id="text"]',
            '.public-DraftEditor-content',
            '[data-testid="textarea"]'
        ]
        
        for selector in body_selectors:
            if await page.locator(selector).count() > 0:
                # Add the link to the body
                full_body = f"{body}\n\n🔗 {link}"
                await page.locator(selector).first.fill(full_body)
                body_filled = True
                print(f"  [+] Body filled using: {selector}")
                break
        
        if not body_filled:
            # Try rich text editor
            try:
                # Escape text for safe insertion
                safe_body = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                safe_link = link.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                await page.evaluate("""
                    const editor = document.querySelector('.public-DraftEditor-content') || 
                                   document.querySelector('[contenteditable="true"]');
                    if (editor) {
                        editor.textContent = arguments[0] + '\\n\\n🔗 ' + arguments[1];
                        editor.dispatchEvent(new Event('input', {bubbles: true}));
                    }
                """, safe_body, safe_link)
                body_filled = True
                print(f"  [+] Body filled via contenteditable")
            except Exception as e:
                print(f"  [!] Could not fill body: {e}")
        
        # Submit the post
        print(f"  [>] Looking for submit button...")
        submit_selectors = [
            'button[type="submit"]',
            'button:has-text("Post")',
            'button:has-text("Submit")',
            '[data-testid="submit-post-button"]'
        ]
        
        for selector in submit_selectors:
            if await page.locator(selector).count() > 0:
                btn = page.locator(selector).first
                btn_text = await btn.text_content()
                print(f"  [>] Clicking submit: {selector} -> '{btn_text}'")
                await btn.click()
                break
        
        # Wait for navigation
        await page.wait_for_timeout(5000)
        
        final_url = page.url
        print(f"  [>] Final URL: {final_url}")
        
        # Check if post was successful
        if "/comments/" in final_url or final_url.endswith(subreddit) or "submitted" in final_url:
            print(f"  [✅] POST SUCCESSFUL: {final_url}")
            await context.close()
            return final_url
        else:
            # Take a screenshot for debugging
            await page.screenshot(path=f"/tmp/reddit_post_{subreddit}_failure.png")
            print(f"  [!] Post may have failed. URL: {final_url}")
            print(f"      Screenshot saved to /tmp/reddit_post_{subreddit}_failure.png")
            await context.close()
            return final_url
            
    except Exception as e:
        print(f"  [!] Error posting to r/{subreddit}: {e}")
        await page.screenshot(path=f"/tmp/reddit_post_{subreddit}_error.png")
        print(f"      Error screenshot saved to /tmp/reddit_post_{subreddit}_error.png")
        await context.close()
        return None


async def main():
    """Main entry point."""
    print("=" * 60)
    print("MCP Workbench Reddit Poster — Playwright + Cookie Injection")
    print("=" * 60)
    
    # Load post content
    title, body = load_post_content()
    print(f"\n[>] Loaded post content")
    print(f"    Title: {title[:60]}...")
    
    # Subreddits to post to
    subreddits = ["LocalLLaMA", "MachineLearning", "programming"]
    
    # Launch browser
    print(f"\n[>] Launching Chromium...")
    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.launch(
            executable_path="/usr/bin/chromium",
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        results = {}
        for subreddit in subreddits:
            result = await post_to_subreddit(browser, subreddit, title, body)
            results[subreddit] = result
            await asyncio.sleep(2)  # Rate limiting
        
        await browser.close()
    finally:
        await pw.stop()
    
    # Save results
    output = {
        "status": "completed",
        "results": results
    }
    
    output_path = "/home/kali/mcp-workbench/docs/posted_reddit.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    for subreddit, url in results.items():
        status = "✅" if url and "/comments/" in str(url) else "❌"
        print(f"  {status} r/{subreddit}: {url}")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
