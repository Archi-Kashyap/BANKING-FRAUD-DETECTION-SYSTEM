import asyncio
import subprocess
import sys
import time
import requests
from playwright.async_api import async_playwright

API_PORT = 8001
STREAMLIT_PORT = 8505
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"

def start_services():
    api_cmd = [
        sys.executable, "-m", "uvicorn", "api:api",
        "--host", "127.0.0.1",
        "--port", str(API_PORT)
    ]
    api_proc = subprocess.Popen(api_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Wait for API to be ready
    start = time.time()
    api_ready = False
    while time.time() - start < 15:
        try:
            r = requests.get(f"http://127.0.0.1:{API_PORT}/health")
            if r.status_code == 200:
                print("FastAPI is ready:", r.json())
                api_ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)

    if not api_ready:
        api_proc.terminate()
        out, err = api_proc.communicate()
        print("API stdout:", out)
        print("API stderr:", err)
        raise RuntimeError("FastAPI failed to start")

    st_cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", str(STREAMLIT_PORT),
        "--server.headless", "true"
    ]
    st_proc = subprocess.Popen(st_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    start = time.time()
    st_ready = False
    while time.time() - start < 20:
        try:
            r = requests.get(STREAMLIT_URL)
            if r.status_code == 200:
                print("Streamlit is ready!")
                st_ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)

    if not st_ready:
        api_proc.terminate()
        st_proc.terminate()
        out, err = st_proc.communicate()
        print("ST stdout:", out)
        print("ST stderr:", err)
        raise RuntimeError("Streamlit failed to start")

    return api_proc, st_proc

async def test_online_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.goto(STREAMLIT_URL, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # Find status box
        status_box = page.locator(".status-box")
        await status_box.wait_for()

        box_text = await status_box.inner_text()
        print("Online Status Box Inner Text:\n", repr(box_text))

        assert "API online" in box_text, f"Expected 'API online' in box text, got: {box_text}"
        assert "rows loaded" in box_text, f"Expected 'rows loaded' in box text, got: {box_text}"
        assert "Local engine active" not in box_text, f"Did not expect 'Local engine active' in box text, got: {box_text}"

        classes = await status_box.get_attribute("class")
        print("Online Status Box Classes:", classes)
        assert "local" not in classes.split(), f"Expected no 'local' class, got: {classes}"

        # Verify telemetry text
        telemetry = page.locator(".sidebar-telemetry")
        telemetry_text = await telemetry.inner_text()
        print("Online Telemetry Text:\n", repr(telemetry_text))
        assert "Hybrid (Rules + RF)" in telemetry_text or "Random Forest" in telemetry_text, f"Expected model in telemetry, got: {telemetry_text}"

        sidebar = page.locator('section[data-testid="stSidebar"]')
        await sidebar.screenshot(path="sidebar_api_online.png")
        print("Saved screenshot to sidebar_api_online.png")

        await browser.close()
        print("ALL ONLINE PLAYWRIGHT ASSERTIONS PASSED!")

def main():
    api_proc, st_proc = start_services()
    try:
        asyncio.run(test_online_ui())
    finally:
        st_proc.terminate()
        api_proc.terminate()
        st_proc.wait(timeout=5)
        api_proc.wait(timeout=5)
        print("Services cleanly terminated.")

if __name__ == "__main__":
    main()
