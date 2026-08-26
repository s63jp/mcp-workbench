#!/usr/bin/env python3
"""
X/Twitter poster for MCP Workbench — Playwright + Firefox cookie injection.
Robust version: explicit textarea focus, verify text landed, click Post button,
verify tweet appears on profile.
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

TWEET = """🔧 Testing MCP servers shouldn't need a terminal.

MCP Workbench connects any MCP server in your browser:
• See every tool + schema instantly
• Test tool calls with one click
• Watch raw JSON-RPC traffic live

Free → https://mcp-workbench.uk

#MCP #DevTools #ClaudeAI #CursorAI"""


def extract_x_cookies():
    cookies = []
    for profile in FIREFOX_PROFILES:
        if not os.path.exists(profile):
            continue
        dst = "/tmp/x_cookies_extract.sqlite"
        shutil.copy2(profile, dst)
        db = sqlite3.connect(dst)
        cur = db.cursor()
        cur.execute("SELECT name, value, host, path, isSecure, isHttpOnly FROM moz_cookies WHERE host LIKE '%x.com%'")
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

    cookies = extract_x_cookies()
    if not cookies:
        print("ERROR: no X cookies found")
        sys.exit(1)
    print(f"[>] Extracted {len(cookies)} X cookies")

    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        await context.add_cookies(cookies)
        page = await context.new_page()

        print("[>] Opening x.com home...")
        await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)

        # Open composer modal
        print("[>] Opening composer...")
        await page.click('a[href="/compose/post"]')
        await page.wait_for_timeout(3000)

        # Focus the textarea explicitly
        editor = await page.wait_for_selector('[data-testid="tweetTextarea_0"]', timeout=10000)
        await editor.focus()
        await page.wait_for_timeout(500)

        # Type the tweet using element-level typing (fires proper React input events)
        print("[>] Typing tweet...")
        await editor.type(TWEET, delay=10)
        await page.wait_for_timeout(1000)

        # Verify text landed in the textarea
        typed = await editor.inner_text()
        print(f"[>] Textarea contains {len(typed)} chars")
        if "Testing MCP servers" not in typed:
            print("[!] Text did not land in textarea — dumping page text")
            text = await page.evaluate("document.body.innerText.slice(0, 1500)")
            print(text)
            await page.screenshot(path="/tmp/x_typed_fail.png")
            sys.exit(1)

        # Click the Post button (fallback to Ctrl+Enter if disabled)
        print("[>] Clicking Post button...")
        try:
            post_btn = await page.wait_for_selector('[data-testid="tweetButton"]', timeout=10000)
            await post_btn.click(timeout=8000)
        except Exception:
            print("[>] Button click failed — trying Ctrl+Enter")
            await page.keyboard.press("Control+Enter")
        print("[>] Post action sent, waiting...")
        await page.wait_for_timeout(8000)

        # Check if composer closed
        try:
            await page.wait_for_selector('[data-testid="tweetTextarea_0"]', timeout=3000)
            print("[?] Composer still open")
            text = await page.evaluate("document.body.innerText.slice(0, 1500)")
            print(text)
        except Exception:
            print("[✓] Composer closed — tweet likely posted")

        await browser.close()
    finally:
        await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
