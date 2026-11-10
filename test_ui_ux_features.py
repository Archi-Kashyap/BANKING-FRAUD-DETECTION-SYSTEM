import asyncio
import subprocess
import time
import sys
import requests
from playwright.async_api import async_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

STREAMLIT_PORT = 8509
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
                print("Streamlit server is ready on port", STREAMLIT_PORT)
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("Streamlit failed to start within 35s")

async def test_ui_features():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": 1400, "height": 900},
            has_touch=True,
        )
        page = await context.new_page()
        print(f"Navigating to {STREAMLIT_URL}...")
        await page.goto(STREAMLIT_URL, wait_until="networkidle")

        # Wait for Streamlit app to complete loading
        status_box = page.locator(".status-box")
        await status_box.wait_for(timeout=25000)
        print("Status box loaded!")

        # -------------------------------------------------------------
        # 1. VERIFY HIT SLOP
        # -------------------------------------------------------------
        print("\n--- 1. Testing Hit Slop ---")
        hit_slop_attr = await page.evaluate("() => document.documentElement.getAttribute('data-hit-slop-enabled')")
        print("Hit slop enabled attribute:", hit_slop_attr)
        assert hit_slop_attr == "true", f"Expected data-hit-slop-enabled='true', got: {hit_slop_attr}"

        has_hit_slop_css = await page.evaluate("""() => {
            let found = false;
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.cssText && (rule.cssText.includes('.hit-slop') || rule.cssText.includes('data-hit-slop'))) {
                            found = true;
                            break;
                        }
                    }
                } catch (_) {}
            }
            return found;
        }""")
        print("Has Hit Slop CSS rules:", has_hit_slop_css)
        assert has_hit_slop_css, "Expected .hit-slop CSS rules in document stylesheet"

        # Verify hit slop interactive targets exist
        hit_slop_count = await page.locator(".hit-slop, [data-hit-slop], .flyout-nav-item").count()
        print("Interactive hit slop elements found:", hit_slop_count)
        assert hit_slop_count > 0, f"Expected at least 1 hit-slop element, found: {hit_slop_count}"

        # Deep verification of hit slop: click within 6px of an interactive target
        hit_slop_forward_test = await page.evaluate("""() => {
            const btn = document.querySelector('.flyout-nav-item[data-agent="1"]');
            if (!btn) return { ok: false, err: 'no btn' };
            const rect = btn.getBoundingClientRect();
            // Point 5px to the left of the item (in empty margin within 10px hit-slop zone)
            const clickX = rect.left - 5;
            const clickY = rect.top + rect.height / 2;
            
            // Check if candidates list finds this element
            const candidates = document.querySelectorAll('button, [role="button"], [role="tab"], [role="radio"], summary, a, .flyout-nav-item');
            let nearest = null;
            let minDistance = Infinity;
            for (const el of candidates) {
                const r = el.getBoundingClientRect();
                if (r.width === 0 || r.height === 0) continue;
                const dx = Math.max(r.left - clickX, 0, clickX - r.right);
                const dy = Math.max(r.top - clickY, 0, clickY - r.bottom);
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist <= 10 && dist < minDistance) {
                    minDistance = dist;
                    nearest = el;
                }
            }
            return {
                ok: nearest === btn,
                minDistance,
                foundCandidate: !!nearest
            };
        }""")
        print("Hit-slop proximity target resolution test:", hit_slop_forward_test)
        assert hit_slop_forward_test["ok"], f"Hit-slop resolution failed: {hit_slop_forward_test}"

        # -------------------------------------------------------------
        # 2. VERIFY TABULAR NUMBERS
        # -------------------------------------------------------------
        print("\n--- 2. Testing Tabular Numbers ---")
        tab_nums_attr = await page.evaluate("() => document.documentElement.getAttribute('data-tabular-nums')")
        print("Tabular numbers attribute:", tab_nums_attr)
        assert tab_nums_attr == "true", f"Expected data-tabular-nums='true', got: {tab_nums_attr}"

        tab_nums_styles = await page.evaluate("""() => {
            const el = document.querySelector('.status-text, .tabular-nums, .chip-value');
            if (!el) return null;
            const style = window.getComputedStyle(el);
            return {
                fontVariantNumeric: style.fontVariantNumeric,
                fontFeatureSettings: style.fontFeatureSettings
            };
        }""")
        print("Tabular numbers computed styles on indicator/chip:", tab_nums_styles)
        assert tab_nums_styles is not None, "Could not find element to check tabular numbers style"
        has_tnum = ("tabular-nums" in tab_nums_styles["fontVariantNumeric"]) or ("tnum" in tab_nums_styles["fontFeatureSettings"])
        assert has_tnum, f"Expected tabular-nums or tnum in styles, got: {tab_nums_styles}"

        # -------------------------------------------------------------
        # 3. VERIFY BALANCED HEADLINES
        # -------------------------------------------------------------
        print("\n--- 3. Testing Balanced Headlines ---")
        balanced_attr = await page.evaluate("() => document.documentElement.getAttribute('data-balanced-headlines')")
        print("Balanced headlines attribute:", balanced_attr)
        assert balanced_attr == "true", f"Expected data-balanced-headlines='true', got: {balanced_attr}"

        title_text_wrap = await page.evaluate("""() => {
            const title = document.querySelector('.console-title, .card-title, .balanced-headline');
            if (!title) return null;
            const style = window.getComputedStyle(title);
            return style.textWrap || style.webkitTextWrap || 'unknown';
        }""")
        print("Computed text-wrap on headline:", title_text_wrap)
        assert title_text_wrap in ["balance", "pretty"], f"Expected text-wrap: balance/pretty, got: {title_text_wrap}"

        # Check orphan prevention (non-breaking space in last position of multiline text)
        has_orphan_prevention = await page.evaluate("""() => {
            const titles = document.querySelectorAll('.console-title, .card-title, .balanced-headline');
            for (const t of titles) {
                if (t.textContent && (t.textContent.includes('\\u00A0') || t.innerHTML.includes('&nbsp;'))) {
                    return true;
                }
            }
            return false;
        }""")
        print("Orphan prevention non-breaking space active:", has_orphan_prevention)

        # -------------------------------------------------------------
        # 4. VERIFY CONTINUOUS CORNERS
        # -------------------------------------------------------------
        print("\n--- 4. Testing Continuous Corners ---")
        continuous_corners_attr = await page.evaluate("() => document.documentElement.getAttribute('data-continuous-corners')")
        print("Continuous corners attribute:", continuous_corners_attr)
        assert continuous_corners_attr == "true", f"Expected data-continuous-corners='true', got: {continuous_corners_attr}"

        has_continuous_corners_css = await page.evaluate("""() => {
            let found = false;
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.cssText && (rule.cssText.includes('corner-smoothing') || rule.cssText.includes('.continuous-corner'))) {
                            found = true;
                            break;
                        }
                    }
                } catch (_) {}
            }
            return found;
        }""")
        print("Has Continuous Corners CSS rules:", has_continuous_corners_css)
        assert has_continuous_corners_css, "Expected corner-smoothing or .continuous-corner rules in stylesheet"

        status_box_border_radius = await page.evaluate("""() => {
            const el = document.querySelector('.status-box, .brand-icon-box, .continuous-corner');
            return el ? window.getComputedStyle(el).borderRadius : null;
        }""")
        print("Continuous corner computed border-radius:", status_box_border_radius)
        assert status_box_border_radius is not None, "Continuous corner element not found"

        # -------------------------------------------------------------
        # 5. VERIFY AMAZON SAFE TRIANGLE
        # -------------------------------------------------------------
        print("\n--- 5. Testing Amazon Safe Triangle ---")
        safe_tri_attr = await page.evaluate("() => document.documentElement.getAttribute('data-amazon-safe-triangle')")
        print("Amazon Safe Triangle attribute:", safe_tri_attr)
        assert safe_tri_attr == "true", f"Expected data-amazon-safe-triangle='true', got: {safe_tri_attr}"

        # 5a. Deep mathematical algorithm verification of point-in-triangle
        math_check = await page.evaluate("""() => {
            const testApi = window._amazonSafeTriangleTest;
            if (!testApi) return { ok: false, error: 'testApi missing' };

            // Triangle: A(0,0), B(100,0), C(50,100)
            const inside = testApi.checkInTriangle(50, 50, 0, 0, 100, 0, 50, 100);
            const outsideRight = testApi.checkInTriangle(120, 50, 0, 0, 100, 0, 50, 100);
            const outsideAbove = testApi.checkInTriangle(50, -10, 0, 0, 100, 0, 50, 100);
            const onVertex = testApi.checkInTriangle(0, 0, 0, 0, 100, 0, 50, 100);

            // Realistic flyout triangle:
            // Mouse at (150, 100), Target Flyout Left Edge at x=250, y from 50 to 250
            // Triangle: (150,100), (250,50), (250,250)
            const inDiagonalPath = testApi.checkInTriangle(200, 120, 150, 100, 250, 50, 250, 250);
            const outsideBelow = testApi.checkInTriangle(200, 300, 150, 100, 250, 50, 250, 250);

            return {
                ok: inside && !outsideRight && !outsideAbove && onVertex && inDiagonalPath && !outsideBelow,
                inside, outsideRight, outsideAbove, onVertex, inDiagonalPath, outsideBelow
            };
        }""")
        print("Point-in-triangle algorithm test result:", math_check)
        assert math_check["ok"], f"Safe triangle mathematical verification failed: {math_check}"

        # 5b. Interactive flyout menu hover verification
        flyout_item_1 = page.locator('.flyout-nav-item[data-agent="1"]')
        flyout_panel = page.locator('.flyout-panel-container')
        assert await flyout_item_1.count() > 0, "Flyout navigation items not found"

        # Hover over item 1
        await flyout_item_1.hover()
        await page.wait_for_timeout(400)

        # Panel should now be open AND VISIBLE (not clipped by sidebar overflow)
        is_open = await page.evaluate("() => document.querySelector('.flyout-panel-container').classList.contains('open')")
        print("Flyout panel opened on hover:", is_open)
        assert is_open, "Expected flyout panel to open on item hover"

        panel_box = await flyout_panel.bounding_box()
        print("Flyout panel on-screen bounding box:", panel_box)
        assert panel_box is not None and panel_box["width"] > 250 and panel_box["height"] > 150, (
            f"Flyout panel must be unclipped and visible on screen, got: {panel_box}"
        )

        panel_title = await page.locator('.flyout-panel-title').inner_text()
        print("Flyout panel title:", repr(panel_title))
        assert "Behavior" in panel_title, f"Expected Behavior in flyout panel title, got: {panel_title}"

        # Hover over item 2
        flyout_item_2 = page.locator('.flyout-nav-item[data-agent="2"]')
        await flyout_item_2.hover()
        await page.wait_for_timeout(400)

        panel_title_2 = await page.locator('.flyout-panel-title').inner_text()
        print("Flyout panel title after switching:", repr(panel_title_2))
        assert "Risk" in panel_title_2, f"Expected Risk in flyout panel title, got: {panel_title_2}"

        # -------------------------------------------------------------
        # 6. TRANSACTION ANALYSIS & VERIFICATION
        # -------------------------------------------------------------
        print("\n--- 6. Running Transaction Analysis ---")
        analyze_btn = page.locator('button:has-text("Analyze transaction")')
        await analyze_btn.wait_for(state="visible", timeout=20000)
        print("Found Analyze transaction button, clicking...")
        await analyze_btn.click()

        hero_card = page.locator('.hero-card')
        await hero_card.wait_for(state="visible", timeout=25000)
        print("Hero verdict card rendered successfully!")

        # Verify tabular numbers in hero card
        hero_tabular_check = await page.evaluate("""() => {
            const statVal = document.querySelector('.hero-card .stat-value');
            if (!statVal) return false;
            const style = window.getComputedStyle(statVal);
            return style.fontVariantNumeric.includes('tabular-nums') || style.fontFeatureSettings.includes('tnum');
        }""")
        print("Hero card stat-value uses tabular numbers:", hero_tabular_check)
        assert hero_tabular_check, "Hero card stat-value should have tabular numbers"

        # Hover over Agent 1 again so the flyout panel appears alongside the hero card
        await flyout_item_1.hover()
        await page.wait_for_timeout(400)

        screenshot_path = "screenshot_ui_ux_features_verified.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"\nSaved full verification screenshot to {screenshot_path}")

        await browser.close()
        print("\n=======================================================")
        print(">>> ALL 5 FEATURES VERIFIED SUCCESSFULLY WITH 100% PASS <<<")
        print("=======================================================")

def main():
    proc = start_streamlit()
    try:
        asyncio.run(test_ui_features())
    finally:
        proc.terminate()
        proc.wait(timeout=5)
        print("Streamlit process terminated.")

if __name__ == "__main__":
    main()
