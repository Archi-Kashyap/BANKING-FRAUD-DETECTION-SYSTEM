import asyncio
import subprocess
import time
import requests
from playwright.async_api import async_playwright

STREAMLIT_PORT = 8511
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"

def start_streamlit():
    cmd = [
        "streamlit", "run", "app.py",
        "--server.port", str(STREAMLIT_PORT),
        "--server.headless", "true"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    start = time.time()
    while time.time() - start < 35:
        try:
            r = requests.get(STREAMLIT_URL)
            if r.status_code == 200:
                print("Streamlit server ready on port", STREAMLIT_PORT)
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("Failed to start Streamlit")

async def test_deep_threat_inspector():
    async with async_playwright() as p:
        # 1. Test normal viewport
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        await page.goto(STREAMLIT_URL, wait_until="networkidle")

        status_box = page.locator(".status-box")
        await status_box.wait_for(timeout=25000)

        print("\n--- 1. Testing Threat Inspector Accessibility Attributes ---")
        items = page.locator(".flyout-nav-item")
        count = await items.count()
        assert count == 5, f"Expected 5 nav items, got {count}"
        for i in range(count):
            item = items.nth(i)
            role = await item.get_attribute("role")
            tabindex = await item.get_attribute("tabindex")
            aria_label = await item.get_attribute("aria-label")
            assert role == "button", f"Item {i} must have role='button', got {role}"
            assert tabindex == "0", f"Item {i} must have tabindex='0', got {tabindex}"
            assert aria_label and len(aria_label) > 0, f"Item {i} must have aria-label"
        print("PASS: All 5 nav items have role='button', tabindex='0', and aria-labels")

        print("\n--- 2. Testing Threat Presets Hover (Verified Scenarios) ---")
        preset_item = page.locator('.flyout-nav-item[data-agent="5"]')
        await preset_item.hover()
        await page.wait_for_timeout(400)

        flyout_panel = page.locator('.flyout-panel-container')
        assert await flyout_panel.is_visible()
        panel_text = (await flyout_panel.inner_text()).upper()
        print("Preset panel snippet:\n", panel_text[:250])
        assert "THREAT PRESETS" in panel_text
        assert "SAMPLE T3768" in panel_text
        assert "SAMPLE T7" in panel_text
        assert "MANUAL U9999" in panel_text
        assert "MANUAL U1757" in panel_text
        assert "MULTI-AGENT PIPELINE" in panel_text
        assert "⚡" not in panel_text, "Emoji must not be present in dossier footer"
        print("PASS: Verified test vector presets correctly rendered without emoji slop")

        print("\n--- 3. Testing Interactive Click Action ---")
        # Click Agent 1 item -> should trigger scroll and target highlight
        agent1_item = page.locator('.flyout-nav-item[data-agent="1"]')
        await agent1_item.click()
        await page.wait_for_timeout(300)

        # Check if an expander was opened/found
        expander = page.locator('[data-testid="stExpander"]').first
        assert await expander.count() > 0
        print("PASS: Click action executed successfully")

        # 4. Test Extreme Small Viewport Height (< 350px) to verify boundary clamping and no cut-off
        print("\n--- 4. Testing Small Viewport Height (320px) Clamping ---")
        await page.set_viewport_size({"width": 1200, "height": 320})
        await page.wait_for_timeout(300)

        await preset_item.hover()
        await page.wait_for_timeout(400)

        box_small = await flyout_panel.bounding_box()
        print("Flyout box at 320px viewport height:", box_small)
        assert box_small is not None
        assert box_small["y"] >= 10, f"Panel top must be within viewport (>= 10), got: {box_small['y']}"
        assert box_small["y"] + box_small["height"] <= 330, (
            f"Panel bottom must be clamped within viewport bounds, got: {box_small['y'] + box_small['height']}"
        )
        print("PASS: Flyout properly clamped within 320px height viewport without overflowing screen fold")

        await browser.close()
        print("\n>>> ALL DEEP THREAT INSPECTOR TESTS PASSED <<<")

def main():
    proc = start_streamlit()
    try:
        asyncio.run(test_deep_threat_inspector())
    finally:
        proc.terminate()
        proc.wait(timeout=5)

if __name__ == "__main__":
    main()
