import asyncio
import json
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
            time.sleep(2)
            print("Streamlit is ready.", flush=True)
            return proc
        time.sleep(1)
    raise RuntimeError("Streamlit failed to start within 40 seconds.")

async def test_sidebar_centering():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        # Test on standard wide screen (1600x900)
        page = await browser.new_page(viewport={"width": 1600, "height": 900})
        await page.goto(f"http://localhost:{PORT}", wait_until="load")
        
        sidebar = page.locator('section[data-testid="stSidebar"], [data-testid="stSidebar"]').first
        await sidebar.wait_for(state="attached", timeout=20000)
        await page.wait_for_selector('div[data-testid="stRadioGroup"]', timeout=20000)
        await page.wait_for_timeout(1000)
        
        print("=== STEP 1: VERIFY OPEN STATE ===")
        open_state = await page.evaluate('''() => {
            const sb = document.querySelector('[data-testid="stSidebar"]');
            const main = document.querySelector('section.main') || document.querySelector('[data-testid="stMain"]');
            const container = document.querySelector('.stMainBlockContainer');
            return {
                sidebarWidth: sb ? sb.getBoundingClientRect().width : null,
                containerRect: container ? container.getBoundingClientRect() : null,
                windowWidth: window.innerWidth
            };
        }''')
        print("Open state:", json.dumps(open_state, indent=2))
        assert open_state["sidebarWidth"] > 0, "Sidebar should be visible when open"
        await page.screenshot(path="verified_open_state.png")
        
        print("\n=== STEP 2: CLOSE SIDEBAR AND VERIFY MIDDLE ALIGNMENT ===")
        await sidebar.hover()
        collapse_btn = page.locator('div[data-testid="stSidebarCollapseButton"] button, div[data-testid="stSidebarHeader"] button').first
        await collapse_btn.click(force=True)
        await page.wait_for_timeout(1000)
        
        closed_state = await page.evaluate('''() => {
            const sb = document.querySelector('[data-testid="stSidebar"]');
            const container = document.querySelector('.stMainBlockContainer');
            const hero = document.querySelector('.starting-hero');
            const expandBtn = document.querySelector('button[data-testid="stExpandSidebarButton"]');
            const r = container ? container.getBoundingClientRect() : null;
            const leftMargin = r ? r.left : null;
            const rightMargin = r ? (window.innerWidth - r.right) : null;
            return {
                sidebarWidth: sb ? sb.getBoundingClientRect().width : null,
                sidebarDisplay: sb ? window.getComputedStyle(sb).display : null,
                containerRect: r,
                leftMargin: leftMargin,
                rightMargin: rightMargin,
                marginDifference: (leftMargin !== null && rightMargin !== null) ? Math.abs(leftMargin - rightMargin) : null,
                isMiddleAligned: (leftMargin !== null && rightMargin !== null) ? (Math.abs(leftMargin - rightMargin) < 5) : false,
                heroRect: hero ? hero.getBoundingClientRect() : null,
                expandBtnVisible: expandBtn ? (expandBtn.offsetParent !== null) : false,
                expandBtnRect: expandBtn ? expandBtn.getBoundingClientRect() : null,
                dataSidebarClosed: document.documentElement.getAttribute('data-sidebar-closed')
            };
        }''')
        print("Closed state:", json.dumps(closed_state, indent=2))
        
        # Assertions
        assert closed_state["sidebarWidth"] == 0, f"Expected sidebar width 0, got {closed_state['sidebarWidth']}"
        assert closed_state["isMiddleAligned"], f"Main container is NOT centered! Left margin: {closed_state['leftMargin']}, Right margin: {closed_state['rightMargin']}, Diff: {closed_state['marginDifference']}"
        assert closed_state["expandBtnVisible"], "Expand sidebar button should be visible"
        print(f"PASS: Container is precisely centered in the middle! Left margin: {closed_state['leftMargin']}px, Right margin: {closed_state['rightMargin']}px (Diff: {closed_state['marginDifference']}px)")
        
        await page.screenshot(path="verified_closed_middle_aligned.png")
        
        print("\n=== STEP 3: RE-OPEN SIDEBAR ===")
        expand_btn = page.locator('button[data-testid="stExpandSidebarButton"]').first
        await expand_btn.click()
        await page.wait_for_timeout(1000)
        
        reopened_state = await page.evaluate('''() => {
            const sb = document.querySelector('[data-testid="stSidebar"]');
            return {
                sidebarWidth: sb ? sb.getBoundingClientRect().width : null,
                sidebarDisplay: sb ? window.getComputedStyle(sb).display : null,
                dataSidebarClosed: document.documentElement.getAttribute('data-sidebar-closed')
            };
        }''')
        print("Reopened state:", json.dumps(reopened_state, indent=2))
        assert reopened_state["sidebarWidth"] > 0, "Sidebar should be open again"
        print("PASS: Sidebar successfully re-opened!")
        await page.screenshot(path="verified_reopened_state.png")
        
        await browser.close()

if __name__ == '__main__':
    proc = ensure_fresh_streamlit()
    try:
        asyncio.run(test_sidebar_centering())
    finally:
        if proc:
            proc.terminate()
            kill_port_owners(PORT)
