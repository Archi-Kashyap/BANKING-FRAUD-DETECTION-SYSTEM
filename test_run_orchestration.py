#!/usr/bin/env python3
"""
Automated Verification Suite for DEF-08: Unified Process Orchestrator (run.py, start.bat, start.sh).
"""

import os
import socket
import subprocess
import sys
import time
import requests


def is_port_bound(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def wait_for_url(url: str, timeout: float = 25.0) -> requests.Response:
    start = time.time()
    last_err = None
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code == 200:
                return r
        except Exception as e:
            last_err = e
        time.sleep(0.5)
    raise RuntimeError(f"Timeout waiting for {url}. Last error: {last_err}")


def main():
    print("=" * 60, flush=True)
    print("Starting DEF-08 Unified Process Orchestration Tests", flush=True)
    print("=" * 60, flush=True)

    # 1. Test CLI Help on run.py
    print("\n[Test 1] Testing 'python run.py --help'...", flush=True)
    res = subprocess.run([sys.executable, "run.py", "--help"], capture_output=True, text=True)
    assert res.returncode == 0, f"run.py --help failed: {res.stderr}"
    assert "--api-port" in res.stdout
    assert "--streamlit-port" in res.stdout or "--port" in res.stdout
    assert "--headless" in res.stdout
    print("PASS: Argument parser verified.", flush=True)

    # 2. Test start.bat on Windows
    if sys.platform == "win32":
        print("\n[Test 2] Testing 'start.bat --help'...", flush=True)
        res_bat = subprocess.run(["cmd.exe", "/c", "start.bat", "--help"], capture_output=True, text=True)
        assert res_bat.returncode == 0, f"start.bat --help failed: {res_bat.stderr}"
        assert "--api-port" in res_bat.stdout
        print("PASS: Windows start.bat batch script verified.", flush=True)

    # Ensure ports 8001 and 8503 are free before starting
    assert not is_port_bound(8001), "Port 8001 is already bound before test start!"
    assert not is_port_bound(8503), "Port 8503 is already bound before test start!"

    # 3. Launch run.py with --headless
    print("\n[Test 3] Launching 'python run.py --headless'...", flush=True)
    proc = subprocess.Popen(
        [sys.executable, "run.py", "--headless"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        # 4. Wait for FastAPI backend to be live and healthy
        print("\n[Test 4] Verifying FastAPI backend (http://127.0.0.1:8001/health)...", flush=True)
        api_resp = wait_for_url("http://127.0.0.1:8001/health", timeout=25.0)
        api_data = api_resp.json()
        print(f"FastAPI Health: {api_data}", flush=True)
        assert api_data["status"] == "ok", f"Expected status 'ok', got {api_data['status']}"
        assert api_data["transactions_loaded"] > 0, "No transactions loaded in context"
        print("PASS: FastAPI backend is healthy and responding.", flush=True)

        # 5. Wait for Streamlit frontend
        print("\n[Test 5] Verifying Streamlit frontend (http://localhost:8503)...", flush=True)
        st_resp = wait_for_url("http://localhost:8503", timeout=25.0)
        assert st_resp.status_code == 200, f"Streamlit returned {st_resp.status_code}"
        assert "Streamlit" in st_resp.text or "stApp" in st_resp.text or len(st_resp.text) > 500
        print("PASS: Streamlit frontend is responding with HTTP 200.", flush=True)

        # 6. Verify API prediction endpoint directly
        print("\n[Test 6] Testing prediction through orchestrated FastAPI...", flush=True)
        pred_resp = requests.get("http://127.0.0.1:8001/predict/T7", timeout=10.0)
        assert pred_resp.status_code == 200, f"Predict failed: {pred_resp.text}"
        pred_data = pred_resp.json()
        print(f"Prediction result for T7: Decision={pred_data['result']['decision']}, Score={pred_data['result']['fraud_score']}", flush=True)
        assert "decision" in pred_data["result"]
        assert "agent1_behavior" in pred_data
        assert "agent2_risk" in pred_data
        assert "agent3_validation" in pred_data
        print("PASS: Prediction endpoint functioning properly.", flush=True)

        # 7. Test POST /predict
        print("\n[Test 7] Testing POST /predict with sample manual transaction...", flush=True)
        payload = {
            "user_id": "U999",
            "transaction_amount": 5000.0,
            "transaction_type": "Payment",
            "payment_mode": "Card",
            "device_type": "Web",
            "device_location": "Bangalore",
            "account_age_days": 180,
            "transaction_hour": 14,
            "previous_failed_attempts": 0,
            "avg_transaction_amount": 500.0,
            "is_international": 0,
            "ip_risk_score": 0.1,
            "login_attempts_last_24h": 1,
            "transaction_id": "TEST_TX_001",
        }
        post_resp = requests.post("http://127.0.0.1:8001/predict", json=payload, timeout=10.0)
        assert post_resp.status_code == 200, f"POST /predict failed: {post_resp.text}"
        post_data = post_resp.json()
        print(f"POST /predict result: Decision={post_data['result']['decision']}", flush=True)
        assert "decision" in post_data["result"]
        print("PASS: POST /predict transaction analysis verified.", flush=True)

    finally:
        # 8. Test Graceful Shutdown
        print("\n[Test 8] Testing graceful termination of run.py...", flush=True)
        proc.terminate()
        try:
            proc.wait(timeout=6.0)
        except subprocess.TimeoutExpired:
            print("WARNING: run.py did not terminate within 6s, killing...", flush=True)
            proc.kill()
            proc.wait()

        # Wait a moment to verify ports are freed
        time.sleep(2.0)
        port_8001_bound = is_port_bound(8001)
        port_8503_bound = is_port_bound(8503)

        print(f"Port 8001 bound after shutdown: {port_8001_bound}", flush=True)
        print(f"Port 8503 bound after shutdown: {port_8503_bound}", flush=True)

        assert not port_8001_bound, "CRITICAL ERROR: Port 8001 remained bound (orphaned process)!"
        assert not port_8503_bound, "CRITICAL ERROR: Port 8503 remained bound (orphaned process)!"
        print("PASS: Clean shutdown verified! No orphaned processes left behind.", flush=True)

    print("\n" + "=" * 60, flush=True)
    print("ALL DEF-08 ORCHESTRATION TESTS PASSED SUCCESSFULLY!", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
