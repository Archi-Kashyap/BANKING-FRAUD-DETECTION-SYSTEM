import asyncio
import socket
import subprocess
import sys
import time
from playwright.async_api import async_playwright

def is_port_open(port=8503):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex(('127.0.0.1', port)) == 0

def ensure_streamlit():
    if not is_port_open(8503):
        print("Starting Streamlit on port 8503...")
        proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8503", "--server.headless", "true"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        for _ in range(30):
            if is_port_open(8503):
                time.sleep(2)
                print("Streamlit is ready.")
                return proc
            time.sleep(1)
        raise RuntimeError("Streamlit failed to start within 30 seconds.")
    return None

async def run_e2e_tests():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.goto("http://localhost:8503", wait_until="networkidle")
        
        # Wait for the radio group to be attached (eliminates cold start race)
        opt0 = page.locator('div[data-testid="stRadioGroup"] > div').nth(0)
        await opt0.wait_for(state="attached", timeout=15000)
        
        print("--- Test 1: Verify Initial Sidebar State ---")
        # Radio Option 0 should have data-selected="true"
        is_selected_0 = await opt0.get_attribute("data-selected")
        print(f"Option 0 selected: {is_selected_0}")
        assert is_selected_0 == "true", "Option 0 should be initially selected"
        
        # Wait for Main content to render 'Pick a transaction'
        main_content = page.locator('div[data-testid="stMainBlockContainer"]')
        await page.locator('text="Pick a transaction"').wait_for(state="visible", timeout=20000)
        main_text = await main_content.inner_text()
        assert "Pick a transaction" in main_text, "Dataset mode should show Pick a transaction"
        print("PASS: Initial Dataset transaction mode verified")

        print("\n--- Test 2: Click 'Manual entry' ---")
        opt1 = page.locator('[data-testid="stRadioOption"]').nth(1)
        await opt1.click()
        await page.locator('text="User ID"').wait_for(state="visible", timeout=15000)
        
        # Verify Option 1 is now selected
        opt1_container = page.locator('div[data-testid="stRadioGroup"] > div').nth(1)
        is_selected_1 = await opt1_container.get_attribute("data-selected")
        print(f"Option 1 selected: {is_selected_1}")
        assert is_selected_1 == "true", "Option 1 should be selected after click"
        
        # Verify Main content switched to Manual entry form
        main_text_manual = await main_content.inner_text()
        assert "Manual entry" in main_text_manual or "User ID" in main_text_manual or "Amount" in main_text_manual, "Manual entry form should be visible"
        print("PASS: Manual entry mode switch verified")
        
        # Capture screenshot of Manual entry mode
        sidebar = page.locator('section[data-testid="stSidebar"]')
        await sidebar.screenshot(path="sidebar_manual_mode.png")
        print("Screenshot saved: sidebar_manual_mode.png")

        print("\n--- Test 3: Click 'How it works' Expander ---")
        expander_summary = page.locator('div[data-testid="stExpander"] details summary')
        await expander_summary.click()
        expander_details = page.locator('div[data-testid="stExpanderDetails"]')
        await expander_details.wait_for(state="visible", timeout=10000)
        
        details_el = page.locator('div[data-testid="stExpander"] details')
        is_open = await details_el.get_attribute("open")
        print(f"Expander open attribute: {is_open}")
        assert is_open is not None, "Expander should have open attribute when clicked"
        
        expander_text = await expander_details.inner_text()
        assert "Agent 1: Behavior Analyzer" in expander_text, "Expander content should contain Agent 1 info"
        print("PASS: Expander opened and content verified")
        await sidebar.screenshot(path="sidebar_expander_open.png")
        print("Screenshot saved: sidebar_expander_open.png")

        # Close expander again
        await expander_summary.click()
        await expander_details.wait_for(state="hidden", timeout=10000)
        is_open_closed = await details_el.get_attribute("open")
        print(f"Expander open attribute after second click: {is_open_closed}")
        assert is_open_closed is None, "Expander should close after second click"
        print("PASS: Expander closed verified")

        print("\n--- Test 4: Switch back to 'Dataset transaction' ---")
        opt0_label = page.locator('[data-testid="stRadioOption"]').nth(0)
        await opt0_label.click()
        await page.locator('text="Pick a transaction"').wait_for(state="visible", timeout=15000)
        is_selected_0_again = await opt0.get_attribute("data-selected")
        print(f"Option 0 selected again: {is_selected_0_again}")
        assert is_selected_0_again == "true", "Option 0 should be selected again"
        main_text_back = await page.locator('div[data-testid="stMainBlockContainer"]').inner_text()
        print(f"Main text snippet: {main_text_back[:100]}...")
        assert "Pick a transaction" in main_text_back, "Dataset mode should be restored"
        print("PASS: Switch back to Dataset transaction verified")

        print("\n--- Test 5: Click 'Switch theme' Button ---")
        theme_btn = page.locator('div.st-key-theme_toggle_btn button')
        await theme_btn.click()
        toast = page.locator('div[data-testid="stToast"]')
        await toast.wait_for(state="visible", timeout=10000)
        toast_text = await toast.inner_text()
        print(f"Toast text: {toast_text}")
        assert "Cyber Dark HUD" in toast_text, "Theme toggle toast should display"
        print("PASS: Theme toggle button verified")

        print("\n--- Test 6: Click 'Analyze transaction' and verify agent indicators in HUD ---")
        analyze_btn = page.locator('div.st-key-btn_ds_analyze button')
        await analyze_btn.click()
        hud_box = page.locator('.hud-box')
        await hud_box.wait_for(state="visible", timeout=25000)
        hud_text = await hud_box.inner_text()
        print(f"HUD Box text snippet:\n{hud_text[:200]}")
        assert "Why this verdict" in hud_text, "HUD Box should have title 'Why this verdict'"

        risk_lines = page.locator('.risk-line')
        risk_count = await risk_lines.count()
        print(f"Found {risk_count} risk indicator lines in HUD card")
        assert risk_count > 0, "Expected at least one risk indicator line in HUD card"
        all_indicators_text = [await risk_lines.nth(i).inner_text() for i in range(risk_count)]
        print(f"Rendered indicators in UI: {all_indicators_text}")
        # Verify that indicators are cleanly formatted and contain agent findings
        assert any("Different" in text or "attempts" in text or "risk" in text.lower() for text in all_indicators_text), "Expected agent findings in indicators"
        # Confirm no raw python dict braces
        assert not any("{" in text or "}" in text for text in all_indicators_text), "No raw python dicts should appear in UI"

        await hud_box.screenshot(path="hud_indicators_verified.png")
        print("Screenshot saved: hud_indicators_verified.png")
        print("PASS: Agent indicators verified in UI")

        print("\n--- Test 7: Switch to 'Manual entry', click 'Analyze transaction' and verify HUD ---")
        await opt1.click()
        await page.locator('text="User ID"').wait_for(state="visible", timeout=15000)
        manual_analyze_btn = page.locator('div.st-key-btn_manual_analyze button')
        await manual_analyze_btn.click()
        manual_hud = page.locator('.hud-box')
        await manual_hud.wait_for(state="visible", timeout=25000)
        manual_hud_text = await manual_hud.inner_text()
        assert "Why this verdict" in manual_hud_text, "Manual mode HUD should contain 'Why this verdict'"

        manual_risk_lines = page.locator('.risk-line')
        m_count = await manual_risk_lines.count()
        print(f"Found {m_count} risk indicator lines in manual mode HUD")
        assert m_count > 0, "Expected at least one risk indicator line in manual mode HUD"
        manual_all_text = [await manual_risk_lines.nth(i).inner_text() for i in range(m_count)]
        print(f"Manual mode rendered indicators: {manual_all_text}")
        assert not any("{" in text or "}" in text for text in manual_all_text), "No raw dicts in manual mode HUD"
        await manual_hud.screenshot(path="hud_manual_indicators_verified.png")
        print("Screenshot saved: hud_manual_indicators_verified.png")
        print("PASS: Manual entry mode agent indicators verified in UI")

        print("\n================ ALL E2E VERIFICATIONS PASSED ================")
        await browser.close()

if __name__ == "__main__":
    server_proc = ensure_streamlit()
    try:
        asyncio.run(run_e2e_tests())
    finally:
        if server_proc:
            try:
                server_proc.terminate()
                server_proc.wait(timeout=5)
            except Exception:
                server_proc.kill()
