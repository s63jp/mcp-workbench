#!/usr/bin/env python3
"""Submit MCP Workbench to mcp.so directory via Playwright."""
import asyncio
import sys

async def main():
    from playwright.async_api import async_playwright

    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()
        await page.goto("https://mcp.so/submit?type=server", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)

        # Dump form structure
        text = await page.evaluate("document.body.innerText.slice(0, 3000)")
        print("=== PAGE TEXT ===")
        print(text)

        inputs = await page.evaluate("""
            Array.from(document.querySelectorAll('input, textarea, select, button'))
                .slice(0, 30)
                .map(el => ({
                    tag: el.tagName,
                    type: el.type || '',
                    name: el.name || '',
                    placeholder: el.placeholder || '',
                    text: (el.innerText || '').slice(0, 60),
                    testid: el.getAttribute('data-testid') || '',
                }))
        """)
        print("=== ELEMENTS ===")
        for i in inputs:
            print(i)

        await page.screenshot(path="/tmp/mcpso_form.png")
        await browser.close()
    finally:
        await pw.stop()

asyncio.run(main())
