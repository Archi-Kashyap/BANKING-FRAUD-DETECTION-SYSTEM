#!/usr/bin/env python3
"""
Playwright End-to-End Verification for run.py Orchestrator.
Launches run.py and uses Playwright to verify that the Streamlit frontend connects
to the live FastAPI backend without local fallback degradation.
"""

import asyncio
import os
import socket
import subprocess
import sys
import time
import requests
from playwright.async_api import async_playwright


def is_port_bound(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def wait_for_service(url: str, timeout: float = 25.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


async def verify_browser():
    print("[Playwright] Launching Chromium to inspect Streamlit UI at http://localhost:8503...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.goto("http://localhost:8503", wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # 1. Locate sidebar status box
        status_box = page.locator(".status-box")
        await status_box.wait_for(state="visible", timeout=15000)

        box_text = await status_box.inner_text()
        print("[Playwright] Status Box Text:\n", repr(box_text))

        assert "API online" in box_text, f"Expected 'API online' in status box, got: {box_text}"
        assert "rows loaded" in box_text, f"Expected 'rows loaded' in status box, got: {box_text}"
        assert "Local engine active" not in box_text, f"Degraded fallback detected! Status box: {box_text}"

        classes = await status_box.get_attribute("class")
        print("[Playwright] Status Box Classes:", classes)
        assert "local" not in classes.split(), f"Status box should not have 'local' class: {classes}"

        # 2. Locate telemetry in sidebar
        telemetry = page.locator(".sidebar-telemetry")
        telemetry_text = await telemetry.inner_text()
        print("[Playwright] Telemetry Text:\n", repr(telemetry_text))
        assert "Hybrid (Rules + RF)" in telemetry_text or "Random Forest" in telemetry_text, f"Expected model in telemetry, got: {telemetry_text}"

        # 3. Take screenshot
        sidebar = page.locator('section[data-testid="stSidebar"]')
        await sidebar.screenshot(path="run_py_orchestration_verified.png")
        print("[Playwright] Screenshot captured to run_py_orchestration_verified.png")

        await browser.close()
        print("[Playwright] UI Verification SUCCESSFUL! Streamlit and FastAPI communicating properly.")


def main():
    print("=" * 60)
    print("Playwright E2E Test: Validating run.py Unified Orchestration")
    print("=" * 60)

    # Pre-check ports
    assert not is_port_bound(8001), "Port 8001 is already in use!"
    assert not is_port_bound(8503), "Port 8503 is already in use!"

    # Start run.py
    print("[Orchestrator] Starting run.py --headless...")
    proc = subprocess.Popen(
        [sys.executable, "run.py", "--headless"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        # Wait for FastAPI
        print("[Orchestrator] Waiting for FastAPI backend (8001)...")
        assert wait_for_service("http://127.0.0.1:8001/health", timeout=25.0), "FastAPI failed to start"
        print("[Orchestrator] FastAPI online!")

        # Wait for Streamlit
        print("[Orchestrator] Waiting for Streamlit frontend (8503)...")
        assert wait_for_service("http://localhost:8503", timeout=25.0), "Streamlit failed to start"
        print("[Orchestrator] Streamlit online!")

        # Run Playwright
        asyncio.run(verify_browser())

    finally:
        print("[Orchestrator] Terminating run.py...")
        proc.terminate()
        try:
            proc.wait(timeout=6.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

        time.sleep(2.0)
        assert not is_port_bound(8001), "Port 8001 not released!"
        assert not is_port_bound(8503), "Port 8503 not released!"
        print("[Orchestrator] Ports released cleanly. Shutdown verified.")

    print("=" * 60)
    print("ALL PLAYWRIGHT ORCHESTRATION VERIFICATIONS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
