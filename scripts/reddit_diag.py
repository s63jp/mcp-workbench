#!/usr/bin/env python3
"""Diagnose the Reddit submit page structure."""
import asyncio
import shutil
import sqlite3
import sys
import os

FIREFOX_PROFILES = [
    "/home/kali/.mozilla/firefox/teveem2z.default-esr/cookies.sqlite",
    "/home/kali/.mozilla/firefox/q4tlbhyt.default/cookies.sqlite",
]


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
    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        await context.add_cookies(cookies)
        page = await context.new_page()
        await page.goto("https://www.reddit.com/r/LocalLLaMA/submit", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(6000)

        print("=== URL:", page.url)
        text = await page.evaluate("document.body.innerText.slice(0, 2500)")
        print("=== PAGE TEXT ===")
        print(text)
        print("=== INPUTS ===")
        inputs = await page.evaluate("""
            Array.from(document.querySelectorAll('textarea, input[type=text], [contenteditable=true]'))
                .slice(0, 15)
                .map(el => ({
                    tag: el.tagName,
                    placeholder: el.placeholder || '',
                    testid: el.getAttribute('data-testid') || '',
                    role: el.getAttribute('role') || '',
                    name: el.name || '',
                }))
        """)
        for i in inputs:
            print(i)
        await browser.close()
    finally:
        await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
