import asyncio
import os
import socket
import subprocess
import sys
import time
from playwright.async_api import async_playwright

PORT = 8503

def is_port_open(port=PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex(('127.0.0.1', port)) == 0

def kill_port_owners(port=PORT):
    try:
        res = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
        for line in res.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 5 and "LISTENING" in line:
                pid = parts[-1]
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def ensure_fresh_streamlit():
    kill_port_owners(PORT)
    time.sleep(1)
    print(f"Starting Streamlit on port {PORT}...", flush=True)
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(PORT), "--server.headless", "true"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    for _ in range(40):
        if is_port_open(PORT):
            time.sleep(3)
            print("Streamlit is ready and accepting connections.", flush=True)
            return proc
        time.sleep(1)
    raise RuntimeError("Streamlit failed to start within 40 seconds.")

async def verify_sidebar_lifecycle():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.goto(f"http://localhost:{PORT}", wait_until="networkidle")

        print("--- Step 1: Wait for app initialization ---", flush=True)
        sidebar = page.locator('section[data-testid="stSidebar"]')
        await sidebar.wait_for(state="attached", timeout=30000)
        await page.locator('div[data-testid="stRadioGroup"]').wait_for(state="attached", timeout=30000)
        
        # Check computed styles of sidebar
        sidebar_debug = await sidebar.evaluate('''e => ({
            rect: e.getBoundingClientRect(),
            computedWidth: window.getComputedStyle(e).width,
            minWidth: window.getComputedStyle(e).minWidth,
            maxWidth: window.getComputedStyle(e).maxWidth,
            inlineStyle: e.getAttribute("style"),
            classList: Array.from(e.classList)
        })''')
        print(f"Sidebar debug info: {sidebar_debug}", flush=True)

        collapse_btn = page.locator('div[data-testid="stSidebarCollapseButton"] button, div[data-testid="stSidebarHeader"] button').first
        expand_btn = page.locator('button[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"]').first

        for cycle in range(1, 4):
            print(f"\n--- Cycle {cycle}: Closing Sidebar ---", flush=True)
            await collapse_btn.click(force=True)
            await page.wait_for_timeout(800)

            # Check sidebar is closed
            is_closed = await sidebar.get_attribute("aria-expanded")
            box_closed = await sidebar.bounding_box()
            print(f"After collapse: aria-expanded={is_closed}, width={box_closed['width']}", flush=True)
            assert is_closed == "false", f"Sidebar should have aria-expanded='false', got {is_closed}"
            assert box_closed["width"] == 0, f"Sidebar width should be 0 when collapsed, got {box_closed['width']}"

            # Check expand button is visible and active
            btn_visible = await expand_btn.is_visible()
            assert btn_visible, "Expand/open sidebar button must be visible when sidebar is closed"
            btn_box = await expand_btn.bounding_box()
            print(f"Expand button is visible at ({btn_box['x']}, {btn_box['y']}), size={btn_box['width']}x{btn_box['height']}", flush=True)

            if cycle == 1:
                await page.screenshot(path="sidebar_collapsed_fixed.png")
                print("Saved screenshot: sidebar_collapsed_fixed.png", flush=True)

            print(f"--- Cycle {cycle}: Opening Sidebar Again ---", flush=True)
            await expand_btn.click()
            await page.wait_for_timeout(800)

            # Check sidebar is open again
            is_open_again = await sidebar.get_attribute("aria-expanded")
            box_open_again = await sidebar.bounding_box()
            print(f"After re-opening: aria-expanded={is_open_again}, width={box_open_again['width']}", flush=True)
            assert is_open_again == "true", f"Sidebar should have aria-expanded='true', got {is_open_again}"
            assert box_open_again["width"] > 0, f"Sidebar width should be > 0 when re-opened, got {box_open_again['width']}"

            if cycle == 1:
                await page.screenshot(path="sidebar_reopened_fixed.png")
                print("Saved screenshot: sidebar_reopened_fixed.png", flush=True)

        print("\nSUCCESS: All sidebar close and re-open cycles passed perfectly!", flush=True)
        await browser.close()

if __name__ == "__main__":
    proc = ensure_fresh_streamlit()
    try:
        asyncio.run(verify_sidebar_lifecycle())
    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
