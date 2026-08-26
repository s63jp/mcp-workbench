#!/usr/bin/env python3
"""
Reddit poster for MCP Workbench — Playwright + Firefox cookie injection.
Posts to r/LocalLLaMA (Show flair) using the live Firefox session.
"""
import asyncio
import shutil
import sqlite3
import sys
import os

FIREFOX_PROFILES = [
    "/home/kali/.mozilla/firefox/teveem2z.default-esr/cookies.sqlite",
    "/home/kali/.mozilla/firefox/q4tlbhyt.default/cookies.sqlite",
]

TITLE = "Show: MCP Workbench — test MCP servers in your browser (Postman for MCP)"

BODY = """I kept hitting the same wall building with MCP servers: install a server, configure it, run it... and get cryptic stdio errors with zero visibility into what went wrong.

So I built **MCP Workbench** — a web-based testing platform for MCP servers.

**What it does:**
- Connect any MCP server in your browser (no terminal, no config files)
- See every tool + its schema instantly
- Test tool calls with one click
- Watch the raw JSON-RPC traffic live (both directions)
- Free tier for public servers

**Try it:** https://mcp-workbench.uk

It's free to use — paste any `npx` MCP server command and hit Connect. The filesystem, GitHub, SQLite, fetch, and sequential-thinking servers are one-click presets.

Built with Next.js + a Python aiohttp WebSocket proxy. Happy to answer questions about the architecture or the MCP protocol details I learned along the way.

Feedback very welcome — what would make this genuinely useful for your workflow?"""


def extract_reddit_cookies():
    cookies = []
    for profile in FIREFOX_PROFILES:
        if not os.path.exists(profile):
            continue
        dst = "/tmp/reddit_cookies_extract.sqlite"
        shutil.copy2(profile, dst)
        db = sqlite3.connect(dst)
        cur = db.cursor()
        cur.execute("SELECT name, value, host, path, isSecure, isHttpOnly FROM moz_cookies WHERE host LIKE '%reddit.com%'")
        for row in cur.fetchall():
            domain = row[2]
            if domain.startswith("."):
                domain = domain[1:]
            cookies.append({
                "name": row[0], "value": row[1], "domain": domain,
                "path": row[3] or "/", "secure": bool(row[4]), "httpOnly": bool(row[5]),
            })
        db.close()
    return cookies


async def main():
    from playwright.async_api import async_playwright

    cookies = extract_reddit_cookies()
    if not cookies:
        print("ERROR: no Reddit cookies found")
        sys.exit(1)
    print(f"[>] Extracted {len(cookies)} Reddit cookies")

    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        await context.add_cookies(cookies)
        page = await context.new_page()

        # Check login state
        print("[>] Checking Reddit login state...")
        await page.goto("https://www.reddit.com/", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(4000)
        text = await page.evaluate("document.body.innerText.slice(0, 2000)")
        logged_in = "Log In" not in text.split("Get the Reddit app")[0][:500] and "Create post" in text or "avatar" in text.lower()
        print(f"[>] Login check: {'logged in' if logged_in else 'UNCERTAIN'}")

        # Go to submit page
        print("[>] Opening submit page for r/LocalLLaMA...")
        await page.goto("https://www.reddit.com/r/LocalLLaMA/submit", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)

        # Check if we hit a login wall
        text = await page.evaluate("document.body.innerText.slice(0, 1000)")
        if "Log in" in text and "Title" not in text:
            print("[!] Login wall detected — session may be expired")
            await page.screenshot(path="/tmp/reddit_login_wall.png")
            sys.exit(1)

        # Fill title
        print("[>] Filling title...")
        title_input = await page.wait_for_selector('textarea[placeholder*="Title"]', timeout=15000)
        await title_input.type(TITLE, delay=8)
        await page.wait_for_timeout(500)

        # Fill body (contenteditable or textarea)
        print("[>] Filling body...")
        body_filled = False
        for selector in [
            'div[contenteditable="true"][role="textbox"]',
            'textarea[placeholder*="Text"]',
            'div[data-testid="post-composer"] div[contenteditable="true"]',
        ]:
            try:
                body_input = await page.wait_for_selector(selector, timeout=5000)
                if body_input:
                    await body_input.click()
                    await body_input.type(BODY, delay=5)
                    body_filled = True
                    print(f"[>] Body filled via {selector}")
                    break
            except Exception:
                continue

        if not body_filled:
            print("[!] Could not find body input")
            await page.screenshot(path="/tmp/reddit_body_fail.png")
            sys.exit(1)

        await page.wait_for_timeout(1000)
        await page.screenshot(path="/tmp/reddit_filled.png")

        # Select "Show" flair if available
        print("[>] Looking for flair selector...")
        try:
            flair_btn = await page.wait_for_selector('button[aria-label*="flair"], [data-testid="flair"]', timeout=5000)
            if flair_btn:
                await flair_btn.click()
                await page.wait_for_timeout(1500)
                # Try to find "Show" option
                text = await page.evaluate("document.body.innerText")
                if "Show" in text:
                    show_opt = await page.query_selector('text="Show"')
                    if show_opt:
                        await show_opt.click()
                        await page.wait_for_timeout(1000)
                        print("[>] Selected Show flair")
        except Exception:
            print("[>] No flair selector found (optional)")

        # Click Post button
        print("[>] Clicking Post...")
        posted = False
        for selector in [
            'button[type="submit"]:has-text("Post")',
            'button:has-text("Post")',
        ]:
            try:
                btn = await page.wait_for_selector(selector, timeout=5000)
                if btn:
                    await btn.click()
                    posted = True
                    break
            except Exception:
                continue

        if not posted:
            print("[!] Could not find Post button")
            await page.screenshot(path="/tmp/reddit_post_fail.png")
            sys.exit(1)

        print("[>] Post submitted, waiting...")
        await page.wait_for_timeout(10000)

        # Check result: URL should change to the post
        print(f"[>] Current URL: {page.url}")
        if "/comments/" in page.url:
            print(f"[✓] POST SUCCESS: {page.url}")
        else:
            text = await page.evaluate("document.body.innerText.slice(0, 1500)")
            print("[?] Post status unclear — page text:")
            print(text)
            await page.screenshot(path="/tmp/reddit_post_check.png")

        await browser.close()
    finally:
        await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
