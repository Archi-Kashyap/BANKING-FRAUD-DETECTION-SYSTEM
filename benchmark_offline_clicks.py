import asyncio
import subprocess
import sys
import time
import requests
from playwright.async_api import async_playwright

import os

STREAMLIT_PORT = 8521
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"

def start_streamlit():
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", str(STREAMLIT_PORT),
        "--server.headless", "true"
    ]
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    start = time.time()
    while time.time() - start < 25:
        try:
            r = requests.get(STREAMLIT_URL)
            if r.status_code == 200:
                print("Streamlit server is ready!")
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("Streamlit failed to start within 25s")

async def test_latencies():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        page.on("console", lambda msg: print(f"[{time.time():.4f}] BROWSER: {msg.text.encode('ascii', 'replace').decode('ascii')}"))

        await page.goto(STREAMLIT_URL, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # Confirm offline badge
        status_box = page.locator(".status-box")
        await status_box.wait_for()
        text = await status_box.inner_text()
        assert "Local engine active" in text, f"Expected Local engine active, got: {text}"
        print("Confirmed: Local engine active badge is visible.")

        # Ensure initial Streamlit page render and lazy JS bundles are completely settled
        empty_box = page.locator(".empty-state-box")
        await empty_box.wait_for(timeout=15000)
        running_widget = page.locator('[data-testid="stStatusWidget"]')
        if await running_widget.count() > 0:
            await running_widget.wait_for(state="detached", timeout=10000)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2500)

        test_txs = ["T5", "T145", "T200"]
        expected_users = {"T5": "U9049", "T145": "U1247", "T200": "U1446"}
        latencies = []
        for tx in test_txs:
            print(f"\n--- Starting {tx} at {time.time()} ---")
            # Fill the transaction input
            input_elem = page.locator('input[aria-label="Transaction ID"]')
            await input_elem.fill(tx)
            await page.keyboard.press("Enter")
            await input_elem.blur()
            print(f"[{time.time():.4f}] Filled {tx}")

            # Wait for preview chip to reflect this transaction's user
            user_chip = page.locator(".preview-chip .chip-value").first
            await user_chip.filter(has_text=expected_users[tx]).wait_for(timeout=5000)
            print(f"[{time.time():.4f}] Preview chip updated to {expected_users[tx]}")
            if await running_widget.count() > 0:
                await running_widget.wait_for(state="detached", timeout=5000)
            await page.wait_for_timeout(600)

            # Click analyze
            btn = page.locator('button:has-text("Analyze transaction")').first
            t0 = time.time()
            print(f"[{t0:.4f}] Clicking analyze button for {tx}")
            await btn.click()
            t_clicked = time.time()
            print(f"[{t_clicked:.4f}] Button clicked, waiting for verdict subtitle...")

            # Wait for verdict subtitle containing this specific tx
            tx_subtitle = page.locator(".verdict-subtitle")
            await tx_subtitle.filter(has_text=f"Transaction {tx}").wait_for(timeout=5000)
            t1 = time.time()
            print(f"[{t1:.4f}] Verdict subtitle appeared!")
            click_elapsed = t_clicked - t0
            render_elapsed = t1 - t_clicked
            total_elapsed = t1 - t0

            verdict_badge = page.locator(".verdict-title")
            verdict_text = await verdict_badge.inner_text()
            tx_title = await tx_subtitle.inner_text()
            safe_title = tx_title.encode("ascii", "replace").decode("ascii")
            print(f"Transaction {tx}: click took {click_elapsed*1000:.1f}ms, verdict wait took {render_elapsed*1000:.1f}ms, total: {total_elapsed*1000:.1f}ms -> {verdict_text} ({safe_title})")
            latencies.append((tx, total_elapsed))

        # Test manual mode
        print("\nTesting Manual Entry mode...")
        # Select Manual entry radio
        manual_radio = page.locator('label:has-text("Manual entry")')
        await manual_radio.click()
        await page.wait_for_timeout(1000)

        # Click analyze manual transaction
        manual_btn = page.locator('button:has-text("Analyze transaction")').first
        t0 = time.time()
        await manual_btn.click()
        verdict_badge = page.locator(".verdict-title")
        await verdict_badge.wait_for(timeout=5000)
        t1 = time.time()
        manual_elapsed = t1 - t0
        verdict_text = await verdict_badge.inner_text()
        print(f"Manual transaction analysis completed in: {manual_elapsed:.4f}s ({manual_elapsed*1000:.1f}ms) -> Verdict: {verdict_text}")

        await browser.close()
        
        for name, el in latencies:
            assert el < 0.5, f"Transaction {name} took longer than 500ms: {el}s"
        assert manual_elapsed < 0.5, f"Manual transaction took longer than 500ms: {manual_elapsed}s"
        print("\nAll latency assertions passed!")

def main():
    proc = start_streamlit()
    try:
        asyncio.run(test_latencies())
    finally:
        proc.terminate()
        try:
            out, err = proc.communicate(timeout=5)
            print("\n=== STREAMLIT STDOUT ===")
            print(out)
            print("\n=== STREAMLIT STDERR ===")
            print(err)
        except Exception:
            proc.kill()
        print("Streamlit process terminated.")

if __name__ == "__main__":
    main()
