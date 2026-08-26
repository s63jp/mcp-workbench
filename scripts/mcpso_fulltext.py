#!/usr/bin/env python3
"""Dump full mcp.so submit page text after filling, to find the free review path."""
import asyncio
import sys

async def main():
    from playwright.async_api import async_playwright

    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()
        await page.goto("https://mcp.so/submit?type=client", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)

        url_el = await page.wait_for_selector('input[type="url"]', timeout=10000)
        await url_el.fill("https://github.com/s63jp/mcp-workbench")
        name_el = await page.wait_for_selector('input[placeholder*="Project name"]', timeout=10000)
        await name_el.fill("MCP Workbench")
        await page.wait_for_timeout(3000)

        # Full text
        text = await page.evaluate("document.body.innerText")
        print(text[:5000])

        # All links
        links = await page.evaluate("""
            Array.from(document.querySelectorAll('a')).map(a => ({
                text: (a.innerText || '').slice(0, 60),
                href: a.href || '',
            })).filter(a => a.text)
        """)
        print("=== LINKS ===")
        for l in links:
            print(l)

        await browser.close()
    finally:
        await pw.stop()

asyncio.run(main())
