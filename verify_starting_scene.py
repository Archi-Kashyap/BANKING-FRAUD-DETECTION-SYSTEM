"""
Automated Verification Script for FraudGuard Starting Scene.
Tests:
1. Fast startup without blocking
2. Total absence of 'Running get_local_engine().'
3. Visual and functional presence of Executive Starting Scene
4. 1-click test vector execution (T3768)
5. Seamless return to starting scene
"""

import asyncio
import subprocess
import time
import sys
import requests
from playwright.async_api import async_playwright

STREAMLIT_PORT = 8521
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"

def start_streamlit():
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", str(STREAMLIT_PORT),
        "--server.headless", "true"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    start = time.time()
    while time.time() - start < 25:
        try:
            r = requests.get(STREAMLIT_URL)
            if r.status_code == 200:
                print(f"[Verifier] Streamlit server is ready on port {STREAMLIT_PORT} in {time.time() - start:.2f}s")
                return proc
        except Exception:
            pass
        time.sleep(0.4)
    proc.terminate()
    raise RuntimeError("Streamlit failed to start within 25s")


async def verify():
    proc = start_streamlit()
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 1400, "height": 960})
            page = await context.new_page()

            t0 = time.time()
            print(f"[Verifier] Navigating to {STREAMLIT_URL}...")
            await page.goto(STREAMLIT_URL, wait_until="networkidle")
            load_time = time.time() - t0
            print(f"[Verifier] Initial page loaded in {load_time:.2f}s")

            # Wait for Streamlit WebSocket to finish connecting
            status_box = page.locator(".status-box")
            await status_box.wait_for(timeout=20000)
            print("[Verifier] Streamlit WebSocket ready and sidebar mounted!")

            # 1. VERIFY ABSENCE OF OLD UGLY SPINNER
            body_text = await page.content()
            assert "Running get_local_engine()." not in body_text, "CRITICAL ERROR: 'Running get_local_engine().' found in page content!"
            print("[Verifier] PASS: 'Running get_local_engine().' is completely absent!")

            # 2. VERIFY EXECUTIVE STARTING SCENE HERO & RADAR SVG
            count = await page.locator(".starting-hero").count()
            print("[Verifier] Hero element count right now:", count)
            hero = page.locator(".starting-hero")
            try:
                await page.wait_for_selector(".starting-hero", timeout=10000)
            except Exception as e:
                print("Failed to find .starting-hero:", e)
                print("Body content:")
                print(await page.locator("body").inner_text())
                raise e
            print("[Verifier] PASS: .starting-hero rendered successfully!")

            title_text = await page.locator(".starting-title").inner_text()
            print(f"[Verifier] Starting title: '{title_text}'")
            norm_title = title_text.replace('\u00a0', ' ')
            assert "FraudGuard Threat Analysis Center" in norm_title, f"Unexpected title: {title_text}"

            status_pill = await page.locator(".starting-status-pill").inner_text()
            norm_status = status_pill.replace('\u00a0', ' ')
            assert "DEFENSE MATRIX ACTIVE" in norm_status, f"Unexpected status pill: {status_pill}"

            # Verify Radar SVG inside hero
            radar_svg = page.locator(".starting-radar-box svg")
            assert await radar_svg.count() > 0, "Radar SVG was stripped or missing inside .starting-radar-box!"
            assert await radar_svg.is_visible(), "Radar SVG is not visible on screen!"
            sweep = page.locator(".radar-sweep-beam")
            assert await sweep.count() > 0, "Radar sweep beam is missing!"
            print("[Verifier] PASS: Radar SVG with rotating sweep beam rendered and visible!")

            # 3. VERIFY TELEMETRY COUNTER CARDS
            stat_cards = page.locator(".starting-stat-card")
            count = await stat_cards.count()
            assert count == 4, f"Expected 4 stat cards, found {count}"
            print("[Verifier] PASS: 4 telemetry counter cards rendered!")

            # 4. VERIFY QUICK-LAUNCH SCENARIO CARDS ARE REMOVED
            scenario_cards = page.locator(".starting-scenario-card")
            sc_count = await scenario_cards.count()
            assert sc_count == 0, f"Expected 0 scenario cards (removed as requested), found {sc_count}"
            print("[Verifier] PASS: Quick-launch scenario cards are cleanly removed as requested!")

            # 5. VERIFY MULTI-AGENT MESH DOSSIER IS REMOVED
            mesh_cards = page.locator(".mesh-agent-card")
            mesh_count = await mesh_cards.count()
            assert mesh_count == 0, f"Expected 0 mesh agent cards (removed as requested), found {mesh_count}"
            print("[Verifier] PASS: Multi-agent architecture dossier is cleanly removed as requested!")

            # 6. VERIFY NO TRUNCATION IN PRIMARY ACTION BUTTON
            btn_ds_analyze = page.locator("button[data-testid='stBaseButton-primary']:has-text('Analyze transaction')")
            assert await btn_ds_analyze.count() > 0, "Analyze transaction button not found!"
            btn_text = await btn_ds_analyze.inner_text()
            assert "Analyze transaction" in btn_text and not btn_text.endswith("..."), f"Button text truncated: '{btn_text}'"
            print(f"[Verifier] PASS: Primary button is fully rendered without truncation: '{btn_text}'")

            # 7. VERIFY NO REDUNDANT BLURHASH PLACEHOLDER AT BOTTOM
            blurhash = page.locator(".blurhash-dashboard-placeholder")
            assert await blurhash.count() == 0, "Redundant blurhash placeholder found on starting scene!"
            print("[Verifier] PASS: Redundant ghost blurhash placeholder cleanly eradicated!")

            # 8. VERIFY HERO IS LOCATED ABOVE TRANSACTION PICKER
            hero_box = await hero.bounding_box()
            tx_input = page.locator("[data-testid='stTextInput']")
            tx_box = await tx_input.bounding_box()
            assert hero_box['y'] < tx_box['y'], f"Hero y={hero_box['y']} should be strictly above transaction picker y={tx_box['y']}"
            print(f"[Verifier] PASS: Hero card (y={hero_box['y']:.1f}) is rendered strictly ABOVE transaction picker (y={tx_box['y']:.1f})!")

            # Capture Starting Scene Screenshot
            await page.screenshot(path="screenshot_starting_scene_verified.png", full_page=True)
            print("[Verifier] Saved screenshot: screenshot_starting_scene_verified.png")

            # 9. TEST EXECUTION VIA PRIMARY 'Analyze transaction' BUTTON
            print("\n[Verifier] Testing execution: Clicking 'Analyze transaction'...")
            await btn_ds_analyze.click()

            # Wait for analysis results (hero-card or gauge-svg)
            verdict_card = page.locator(".hero-card")
            await verdict_card.wait_for(timeout=20000)
            verdict_text = await page.locator(".verdict-title").inner_text()
            print(f"[Verifier] Analysis verdict: '{verdict_text}'")
            assert "FRAUD" in verdict_text or "CRITICAL" in verdict_text or "SUSPICIOUS" in verdict_text or "SAFE" in verdict_text

            # Verify return button exists
            btn_return = page.locator("button:has-text('Return to Starting Scene')")
            await btn_return.wait_for(timeout=5000)
            print("[Verifier] PASS: '← Return to Starting Scene' button is visible!")

            # Capture Analyzed Dossier Screenshot
            await page.screenshot(path="screenshot_starting_scene_analyzed.png", full_page=True)
            print("[Verifier] Saved screenshot: screenshot_starting_scene_analyzed.png")

            # 7. TEST RETURN TO STARTING SCENE
            print("\n[Verifier] Testing return: Clicking 'Return to Starting Scene'...")
            await btn_return.click()
            await hero.wait_for(timeout=10000)
            print("[Verifier] PASS: Successfully returned to Starting Scene!")

            await browser.close()
            print("\n[Verifier] ALL STARTING SCENE VERIFICATIONS PASSED PERFECTLY!")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(verify())
