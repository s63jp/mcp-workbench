#!/usr/bin/env python3
"""Check mcp.so submit page state after filling the form."""
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

        # Fill the form
        url_el = await page.wait_for_selector('input[type="url"]', timeout=10000)
        await url_el.fill("https://github.com/s63jp/mcp-workbench")
        name_el = await page.wait_for_selector('input[placeholder*="Project name"]', timeout=10000)
        await name_el.fill("MCP Workbench")
        await page.wait_for_timeout(3000)

        # Full page text
        text = await page.evaluate("document.body.innerText")
        print("=== FULL PAGE TEXT (first 3000) ===")
        print(text[:3000])

        # All buttons with positions
        btns = await page.evaluate("""
            Array.from(document.querySelectorAll('button')).map(b => {
                const r = b.getBoundingClientRect();
                return {
                    text: (b.innerText || '').slice(0, 50),
                    type: b.type,
                    x: Math.round(r.x + r.width/2),
                    y: Math.round(r.y + r.height/2),
                    w: Math.round(r.width),
                    h: Math.round(r.height),
                    visible: r.width > 0 && r.height > 0,
                };
            })
        """)
        print("=== BUTTONS WITH POSITIONS ===")
        for b in btns:
            print(b)

        await page.screenshot(path="/tmp/mcpso_state.png")
        await browser.close()
    finally:
        await pw.stop()

asyncio.run(main())
