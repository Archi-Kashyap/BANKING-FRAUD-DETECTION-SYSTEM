import subprocess
import sys
import time
import requests
import app

API_PORT = 8001

def main():
    print("Starting FastAPI service on port 8001...")
    api_cmd = [
        sys.executable, "-m", "uvicorn", "api:api",
        "--host", "127.0.0.1",
        "--port", str(API_PORT)
    ]
    proc = subprocess.Popen(api_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        # Wait for FastAPI
        ready = False
        for _ in range(30):
            try:
                r = requests.get(f"http://127.0.0.1:{API_PORT}/health", timeout=1.0)
                if r.status_code == 200:
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(0.5)

        if not ready:
            raise RuntimeError("FastAPI did not start in time.")
        print("FastAPI is online.")

        # Test dataset tx via online API
        print("Testing analyze_dataset_tx('T3768') with live FastAPI...")
        ds_res = app.analyze_dataset_tx("T3768")
        assert ds_res is not None, "Expected valid result from online API"
        assert len(ds_res["indicators"]) > 0, "Expected non-empty indicators"
        print(f"Online dataset indicators count: {len(ds_res['indicators'])}")
        assert any("Different transaction location" in ind or "repeated_failed_attempts" in ind for ind in ds_res["indicators"]), "Expected agent indicators from online API"

        # Test manual tx via online API
        print("Testing analyze_manual_tx() with live FastAPI...")
        payload = {
            "user_id": "U9999",
            "transaction_amount": 90000.0,
            "transaction_type": "Payment",
            "payment_mode": "Card",
            "device_type": "Android",
            "device_location": "Bangalore",
            "account_age_days": 30,
            "transaction_hour": 2,
            "previous_failed_attempts": 5,
            "avg_transaction_amount": 4000.0,
            "is_international": 1,
            "ip_risk_score": 0.95,
            "login_attempts_last_24h": 9,
            "transaction_id": "MANUAL",
        }
        man_res = app.analyze_manual_tx(payload)
        assert man_res is not None, "Expected valid result from online API"
        assert len(man_res["indicators"]) > 0, "Expected non-empty indicators"
        print(f"Online manual indicators count: {len(man_res['indicators'])}")
        assert any("repeated_failed_attempts" in ind or "international_transaction" in ind for ind in man_res["indicators"]), "Expected agent indicators from online API"

        print("ALL ONLINE INDICATOR VERIFICATIONS PASSED!")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        print("FastAPI stopped.")

if __name__ == "__main__":
    main()
