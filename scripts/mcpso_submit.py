#!/usr/bin/env python3
"""Submit MCP Workbench to mcp.so as an MCP Client (free review)."""
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
        await page.goto("https://mcp.so/submit?type=client", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)

        # Dump all inputs with details
        inputs = await page.evaluate("""
            Array.from(document.querySelectorAll('input, textarea, select, button'))
                .slice(0, 40)
                .map(el => ({
                    tag: el.tagName,
                    type: el.type || '',
                    name: el.name || '',
                    placeholder: el.placeholder || '',
                    text: (el.innerText || '').slice(0, 60),
                    testid: el.getAttribute('data-testid') || '',
                    id: el.id || '',
                }))
        """)
        print("=== ELEMENTS ===")
        for i in inputs:
            print(i)

        # Fill Repository URL
        print("[>] Filling repository URL...")
        repo_filled = False
        for sel in [
            'input[type="url"]',
            'input[placeholder*="example.com"]',
        ]:
            try:
                el = await page.wait_for_selector(sel, timeout=4000)
                if el:
                    await el.fill("https://github.com/s63jp/mcp-workbench")
                    repo_filled = True
                    print(f"[>] Repo URL filled via {sel}")
                    break
            except Exception:
                continue
        if not repo_filled:
            print("[!] Could not find repository URL field")
            await page.screenshot(path="/tmp/mcpso_fail.png")
            sys.exit(1)

        # Fill Name
        print("[>] Filling name...")
        name_filled = False
        for sel in [
            'input[placeholder*="Project name"]',
            'input[type="text"]',
        ]:
            try:
                el = await page.wait_for_selector(sel, timeout=4000)
                if el:
                    await el.fill("MCP Workbench")
                    name_filled = True
                    print(f"[>] Name filled via {sel}")
                    break
            except Exception:
                continue
        if not name_filled:
            print("[!] Could not find name field")
            await page.screenshot(path="/tmp/mcpso_fail.png")
            sys.exit(1)

        await page.wait_for_timeout(1000)
        await page.screenshot(path="/tmp/mcpso_filled.png")

        # Find and click the FREE submit button — it's a floating action button
        # (fixed bottom-right, empty text). The "Pay and submit automatically"
        # one is the $39 paid option. The FAB renders late, so poll for it.
        print("[>] Looking for free submit FAB...")
        submit_clicked = False
        for attempt in range(10):
            clicked = await page.evaluate("""
                () => {
                    // Try submit buttons with empty text first
                    const btns = Array.from(document.querySelectorAll('button[type="submit"]'));
                    for (const b of btns) {
                        if ((b.innerText || '').trim() === '') {
                            b.click();
                            return 'submit-empty';
                        }
                    }
                    // Fallback: the FAB has class 'fixed right-3 bottom-3'
                    const fabs = Array.from(document.querySelectorAll('button.fixed'));
                    for (const b of fabs) {
                        if ((b.innerText || '').trim() === '') {
                            b.click();
                            return 'fab-fixed';
                        }
                    }
                    return false;
                }
            """)
            if clicked:
                submit_clicked = True
                print(f"[>] Clicked free submit FAB via JS ({clicked}, attempt {attempt + 1})")
                break
            await page.wait_for_timeout(1500)

        # Last resort: get the FAB's exact bounding box and click its center
        if not submit_clicked:
            print("[>] Getting FAB bounding box...")
            box = await page.evaluate("""
                () => {
                    const fabs = Array.from(document.querySelectorAll('button.fixed'));
                    for (const b of fabs) {
                        if ((b.innerText || '').trim() === '') {
                            const r = b.getBoundingClientRect();
                            return { x: r.x + r.width / 2, y: r.y + r.height / 2, w: r.width, h: r.height };
                        }
                    }
                    return null;
                }
            """)
            if box:
                print(f"[>] FAB at ({box['x']:.0f}, {box['y']:.0f}) size {box['w']:.0f}x{box['h']:.0f}")
                await page.mouse.click(box["x"], box["y"])
                await page.wait_for_timeout(5000)
                submit_clicked = True
                # Check what happened
                text = await page.evaluate("document.body.innerText.slice(0, 1200)")
                print("=== AFTER FAB CLICK ===")
                print(text)
            else:
                print("[!] FAB not found for coordinate click")

        if not submit_clicked:
            print("[!] No free submit button found — dumping ALL buttons post-fill")
            all_btns = await page.evaluate("""
                Array.from(document.querySelectorAll('button, a[role=button]')).map(b => ({
                    text: (b.innerText || '').slice(0, 60),
                    type: b.type || '',
                    disabled: b.disabled || false,
                    cls: (b.className || '').slice(0, 80),
                }))
            """)
            for b in all_btns:
                print("  ", b)
            await page.screenshot(path="/tmp/mcpso_fail.png")
            sys.exit(1)

        await page.wait_for_timeout(8000)
        print(f"[>] After submit URL: {page.url}")
        text = await page.evaluate("document.body.innerText.slice(0, 1500)")
        print("=== AFTER SUBMIT ===")
        print(text)
        await page.screenshot(path="/tmp/mcpso_after.png")

        await browser.close()
    finally:
        await pw.stop()

asyncio.run(main())
