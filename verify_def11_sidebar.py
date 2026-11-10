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

async def verify_sidebar():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.goto("http://localhost:8503", wait_until="networkidle")

        print("--- Test 1: Verify Sidebar Telemetry ---")
        telemetry = page.locator(".sidebar-telemetry")
        await telemetry.wait_for(state="visible", timeout=15000)
        telemetry_text = await telemetry.inner_text()
        print("Telemetry text:\n", telemetry_text)

        assert "Model:" in telemetry_text, "Expected 'Model:' in telemetry"
        assert "Hybrid (Rules + RF)" in telemetry_text, f"Expected 'Hybrid (Rules + RF)' in telemetry, got: {telemetry_text}"
        assert "ML Signal:" in telemetry_text, "Expected 'ML Signal:' in telemetry"
        assert "Supporting (Weak Dataset Baseline)" in telemetry_text, f"Expected 'Supporting (Weak Dataset Baseline)' in telemetry, got: {telemetry_text}"
        print("PASS: Sidebar telemetry labels verified!")

        # Verify tooltip attribute
        model_div = telemetry.locator('div[title="ML Signal: Supporting (Weak Dataset Baseline)"]').first
        tooltip = await model_div.get_attribute("title")
        print(f"Model element tooltip: {tooltip}")
        assert tooltip == "ML Signal: Supporting (Weak Dataset Baseline)", f"Expected tooltip, got: {tooltip}"
        print("PASS: Tooltip verified!")

        # Save screenshot of closed expander showing telemetry
        sidebar = page.locator('section[data-testid="stSidebar"]')
        await sidebar.screenshot(path="sidebar_telemetry_def11.png")
        print("Saved screenshot: sidebar_telemetry_def11.png")

        print("\n--- Test 2: Verify How it works Expander Note ---")
        expander_summary = page.locator('div[data-testid="stExpander"] details summary')
        await expander_summary.click()
        expander_details = page.locator('div[data-testid="stExpanderDetails"]')
        await expander_details.wait_for(state="visible", timeout=10000)

        expander_text = await expander_details.inner_text()
        print("Expander snippet:\n", expander_text[:300])

        expected_note = "Uses expert behavioral rules as primary signal; Random Forest model provides secondary support due to low synthetic dataset feature correlation."
        assert expected_note in expander_text, f"Expected transparency note in expander text, got:\n{expander_text}"
        print("PASS: 'How it works' expander transparency note verified!")

        # Save screenshot of open expander showing the note
        await sidebar.screenshot(path="sidebar_expander_def11.png")
        print("Saved screenshot: sidebar_expander_def11.png")
        await expander_details.screenshot(path="expander_details_def11.png")
        print("Saved screenshot: expander_details_def11.png")

        await browser.close()
        print("\nALL DEF-11 PLAYWRIGHT CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    proc = ensure_streamlit()
    try:
        asyncio.run(verify_sidebar())
    finally:
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
