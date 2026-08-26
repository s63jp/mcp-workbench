#!/usr/bin/env python3
"""Verify the latest tweet on the Gizmo50009 profile."""
import asyncio
import shutil
import sqlite3
import sys
import os

FIREFOX_PROFILES = [
    "/home/kali/.mozilla/firefox/teveem2z.default-esr/cookies.sqlite",
    "/home/kali/.mozilla/firefox/q4tlbhyt.default/cookies.sqlite",
]


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
    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        await context.add_cookies(cookies)
        page = await context.new_page()
        await page.goto("https://x.com/Gizmo50009", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(6000)
        text = await page.evaluate("document.body.innerText.slice(0, 3000)")
        print("=== PROFILE TEXT ===")
        print(text)
        await browser.close()
    finally:
        await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
