import asyncio
import subprocess
import time
import requests
from playwright.async_api import async_playwright

STREAMLIT_PORT = 8504
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"

def start_streamlit():
    cmd = [
        "streamlit", "run", "app.py",
        "--server.port", str(STREAMLIT_PORT),
        "--server.headless", "true"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # Wait for server to become responsive
    start = time.time()
    while time.time() - start < 20:
        try:
            r = requests.get(STREAMLIT_URL)
            if r.status_code == 200:
                print("Streamlit server is ready!")
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("Streamlit failed to start within 20s")

async def test_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.goto(STREAMLIT_URL, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # Find status box
        status_box = page.locator(".status-box")
        await status_box.wait_for()

        box_text = await status_box.inner_text()
        print("Status Box Inner Text:\n", repr(box_text))

        # Check local engine active is present
        assert "Local engine active" in box_text, f"Expected 'Local engine active' in box text, got: {box_text}"
        assert "rows loaded" in box_text, f"Expected 'rows loaded' in box text, got: {box_text}"
        assert "API online" not in box_text, f"Did not expect 'API online' in box text, got: {box_text}"

        # Verify class and styling
        classes = await status_box.get_attribute("class")
        print("Status Box Classes:", classes)
        assert "local" in classes, f"Expected 'local' in class, got: {classes}"

        # Verify telemetry text
        telemetry = page.locator(".sidebar-telemetry")
        telemetry_text = await telemetry.inner_text()
        print("Telemetry Text:\n", repr(telemetry_text))
        assert "Hybrid (Rules + RF)" in telemetry_text or "Random Forest (Local Engine)" in telemetry_text, f"Expected model in telemetry, got: {telemetry_text}"

        # Take screenshot of sidebar
        sidebar = page.locator('section[data-testid="stSidebar"]')
        await sidebar.screenshot(path="sidebar_local_engine.png")
        print("Saved screenshot to sidebar_local_engine.png")

        await browser.close()
        print("ALL PLAYWRIGHT ASSERTIONS PASSED!")

def main():
    proc = start_streamlit()
    try:
        asyncio.run(test_ui())
    finally:
        proc.terminate()
        proc.wait(timeout=5)
        print("Streamlit process terminated.")

if __name__ == "__main__":
    main()
