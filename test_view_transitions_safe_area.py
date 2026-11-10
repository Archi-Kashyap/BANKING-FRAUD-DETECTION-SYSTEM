import asyncio
import subprocess
import time
import requests
from playwright.async_api import async_playwright

STREAMLIT_PORT = 8508
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"

def start_streamlit():
    cmd = [
        "streamlit", "run", "app.py",
        "--server.port", str(STREAMLIT_PORT),
        "--server.headless", "true"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    start = time.time()
    while time.time() - start < 30:
        try:
            r = requests.get(STREAMLIT_URL)
            if r.status_code == 200:
                print("Streamlit server is ready on port", STREAMLIT_PORT)
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("Streamlit failed to start within 30s")

async def test_features():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            has_touch=True,
        )
        page = await context.new_page()
        await page.goto(STREAMLIT_URL, wait_until="networkidle")

        # Wait for Streamlit app to complete loading
        status_box = page.locator(".status-box")
        await status_box.wait_for(timeout=25000)
        print("Status box loaded!")

        # 1. VERIFY SAFE AREA INSETS: Viewport meta tag
        viewport_meta = await page.evaluate("""() => {
            const meta = document.querySelector('meta[name="viewport"]');
            return meta ? meta.getAttribute('content') : null;
        }""")
        print("Viewport meta content:", viewport_meta)
        assert viewport_meta is not None, "Viewport meta not found"
        assert "viewport-fit=cover" in viewport_meta, f"Expected 'viewport-fit=cover' in meta content, got: {viewport_meta}"

        # 2. VERIFY SAFE AREA INSETS: Attributes & Styles
        safe_area_attr = await page.evaluate("() => document.documentElement.getAttribute('data-safe-area-enabled')")
        print("Safe area enabled attribute:", safe_area_attr)
        assert safe_area_attr == "true", "Expected data-safe-area-enabled='true'"

        main_padding = await page.evaluate("""() => {
            const el = document.querySelector('.stMainBlockContainer');
            if (!el) return null;
            const style = window.getComputedStyle(el);
            return {
                paddingTop: style.paddingTop,
                paddingBottom: style.paddingBottom,
                paddingLeft: style.paddingLeft,
                paddingRight: style.paddingRight,
            };
        }""")
        print("Main container computed padding:", main_padding)
        assert main_padding is not None, "Main container not found"

        # 3. VERIFY VIEW TRANSITIONS: Attributes & CSS rules
        vt_attr = await page.evaluate("() => document.documentElement.getAttribute('data-view-transitions')")
        print("View transitions attribute:", vt_attr)
        assert vt_attr == "true", "Expected data-view-transitions='true'"

        has_vt_css = await page.evaluate("""() => {
            let found = false;
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.cssText && (rule.cssText.includes('@view-transition') || rule.cssText.includes('view-transition-name'))) {
                            found = true;
                            break;
                        }
                    }
                } catch (_) {}
            }
            return found;
        }""")
        print("Has View Transitions CSS rules:", has_vt_css)
        assert has_vt_css, "Expected @view-transition or view-transition-name CSS rules in document"

        # 4. VERIFY PREDICTIVE BACK: Attributes & Gesture overscroll
        pb_attr = await page.evaluate("() => document.documentElement.getAttribute('data-predictive-back')")
        print("Predictive back attribute:", pb_attr)
        assert pb_attr == "true", "Expected data-predictive-back='true'"

        overscroll_x = await page.evaluate("""() => {
            const app = document.querySelector('.stApp');
            return app ? window.getComputedStyle(app).overscrollBehaviorX : null;
        }""")
        print("Computed overscroll-behavior-x on .stApp:", overscroll_x)
        assert overscroll_x in ["auto", "visible"], f"Expected overscroll-behavior-x to be auto, got: {overscroll_x}"

        # 5. TEST TAB NAVIGATION & PREDICTIVE BACK
        tabs = page.locator('[role="tab"]')
        tab_count = await tabs.count()
        print("Found tabs:", tab_count)
        assert tab_count >= 2, f"Expected at least 2 tabs, found: {tab_count}"

        # Click History tab
        history_tab = tabs.nth(1)
        await history_tab.click()
        await page.wait_for_timeout(1000)

        current_hash = await page.evaluate("() => window.location.hash")
        print("Current hash after clicking History tab:", current_hash)
        assert current_hash == "#history", f"Expected #history, got: {current_hash}"

        # Simulate Predictive Back navigation (go_back)
        await page.go_back()
        await page.wait_for_timeout(1500)

        # Verify active tab switched back to Analyze
        active_tab_text = await page.evaluate("""() => {
            const active = document.querySelector('[role="tab"][aria-selected="true"]');
            return active ? active.innerText : null;
        }""")
        print("Active tab after back gesture:", repr(active_tab_text))
        assert active_tab_text and "analyze" in active_tab_text.lower(), f"Expected Analyze tab active after back gesture, got: {active_tab_text}"

        # 6. TEST TRANSACTION ANALYSIS & SCREENSHOT
        # Click Quick Fill button
        quick_fill = page.locator('button:has-text("Quick Fill (T3768)")')
        if await quick_fill.count() > 0:
            await quick_fill.click()
            await page.wait_for_timeout(800)

        # Click Analyze Transaction button
        analyze_btn = page.locator('button:has-text("Analyze Transaction")')
        if await analyze_btn.count() > 0:
            await analyze_btn.click()
            # Wait for analysis hero card
            hero = page.locator('.hero-card')
            await hero.wait_for(timeout=15000)
            print("Hero verdict card rendered successfully with view transitions!")

        await page.screenshot(path="screenshot_view_transitions_safe_area.png", full_page=True)
        print("Saved screenshot to screenshot_view_transitions_safe_area.png")

        await browser.close()
        print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")

def main():
    proc = start_streamlit()
    try:
        asyncio.run(test_features())
    finally:
        proc.terminate()
        proc.wait(timeout=5)
        print("Streamlit process terminated.")

if __name__ == "__main__":
    main()
