import ast
import html
import sys
import unittest
from unittest.mock import patch, MagicMock

import app

class TestDEF07Indicators(unittest.TestCase):
    def test_format_risk_indicator(self):
        # 1. Plain string
        self.assertEqual(
            app.format_risk_indicator("Different transaction location"),
            "Different transaction location"
        )
        # 2. Known snake_case mapping
        self.assertEqual(
            app.format_risk_indicator("high_ip_risk"),
            "High IP risk"
        )
        self.assertEqual(
            app.format_risk_indicator("repeated_failed_attempts"),
            "Repeated failed attempts"
        )
        self.assertEqual(
            app.format_risk_indicator("elevated_ml_probability"),
            "Elevated ML probability"
        )
        # 3. Arbitrary snake_case auto-humanization
        self.assertEqual(
            app.format_risk_indicator("device_mismatch_detected"),
            "Device mismatch detected"
        )
        # 4. Dict with description
        self.assertEqual(
            app.format_risk_indicator({"indicator": "Failed logins", "description": "3 failed attempts."}),
            "3 failed attempts."
        )
        # 5. Dict with only indicator title
        self.assertEqual(
            app.format_risk_indicator({"indicator": "International transaction"}),
            "International transaction"
        )
        # 6. Stringified dict representation (Python dict repr)
        self.assertEqual(
            app.format_risk_indicator("{'indicator': 'Failed transaction attempts', 'score': 0.3, 'description': '1 failed attempts.'}"),
            "1 failed attempts."
        )
        # 7. Valid JSON string with booleans and nulls
        self.assertEqual(
            app.format_risk_indicator('{"indicator": "Failed login", "active": true, "details": null}'),
            "Failed login"
        )
        # 8. Uppercase and mixed-case snake_case
        self.assertEqual(
            app.format_risk_indicator("HIGH_IP_RISK"),
            "High IP risk"
        )
        self.assertEqual(
            app.format_risk_indicator("Repeated_Failed_Attempts"),
            "Repeated failed attempts"
        )
        # 9. Kebab-case
        self.assertEqual(
            app.format_risk_indicator("device-mismatch-detected"),
            "Device mismatch detected"
        )
        # 10. Non-risk absence indicators filtered out
        self.assertEqual(
            app.format_risk_indicator("No major behavioral deviation detected"),
            ""
        )
        self.assertEqual(
            app.format_risk_indicator("no behavioral deviation detected"),
            ""
        )
        # 11. Empty and None
        self.assertEqual(app.format_risk_indicator(""), "")
        self.assertEqual(app.format_risk_indicator(None), "")
        self.assertEqual(app.format_risk_indicator({}), "")

    def test_analyze_dataset_tx_uses_graph_indicators(self):
        # Run analyze_dataset_tx on T3768
        res = app.analyze_dataset_tx("T3768")
        self.assertIsNotNone(res)
        indicators = res.get("indicators", [])
        self.assertTrue(len(indicators) > 0)
        # Check that agent-generated indicators are present, not just the 3-4 old heuristics
        # T3768 in graph has: 'Different transaction location', 'repeated_failed_attempts', etc.
        self.assertTrue(
            any("Different transaction location" in ind or "repeated_failed_attempts" in ind for ind in indicators),
            f"Expected graph indicators in {indicators}"
        )

    def test_analyze_dataset_tx_fallback_on_empty(self):
        # Mock call_api or get_local_engine to return empty risk_indicators
        fake_api_res = {
            "result": {
                "decision": "LEGIT",
                "fraud_score": 10.0,
                "confidence": 90.0,
                "high_score_agent_count": 0,
                "risk_indicators": [],
                "user_id": "U1001",
            }
        }
        with patch("app.call_api", return_value=fake_api_res):
            res = app.analyze_dataset_tx("T1")
            self.assertIsNotNone(res)
            # Heuristics fallback should run on row T1
            self.assertIsInstance(res["indicators"], list)

    def test_analyze_manual_tx_uses_graph_indicators(self):
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
        res = app.analyze_manual_tx(payload)
        self.assertIsNotNone(res)
        indicators = res.get("indicators", [])
        self.assertTrue(len(indicators) > 0)
        # Should contain graph indicators
        self.assertTrue(
            any("repeated_failed_attempts" in ind or "international_transaction" in ind or "failed attempts" in ind for ind in indicators),
            f"Expected graph indicators in {indicators}"
        )

    def test_analyze_manual_tx_fallback_on_empty(self):
        fake_api_res = {
            "result": {
                "decision": "FRAUD",
                "fraud_score": 95.0,
                "confidence": 95.0,
                "high_score_agent_count": 3,
                "risk_indicators": [],
            }
        }
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
        with patch("app.call_api", return_value=fake_api_res):
            res = app.analyze_manual_tx(payload)
            self.assertIsNotNone(res)
            # Heuristics fallback should run on payload
            self.assertIn("International transaction", res["indicators"])
            self.assertTrue(any("failed attempts before this one" in ind for ind in res["indicators"]))

    def test_hud_card_formatting_pipeline(self):
        # Simulate what the UI rendering section does
        analysis = {
            "indicators": [
                "high_ip_risk",
                "repeated_failed_attempts",
                "{'indicator': 'Failed transaction attempts', 'score': 0.3, 'description': '4 failed attempts.'}",
                "<script>alert('xss')</script>",
                "high_ip_risk",  # duplicate
            ]
        }
        raw_indicators = analysis.get("indicators", []) or []
        formatted_indicators = []
        for it in raw_indicators:
            fmt = app.format_risk_indicator(it)
            if fmt and fmt not in formatted_indicators:
                formatted_indicators.append(fmt)

        self.assertEqual(len(formatted_indicators), 4) # duplicates removed
        self.assertEqual(formatted_indicators[0], "High IP risk")
        self.assertEqual(formatted_indicators[1], "Repeated failed attempts")
        self.assertEqual(formatted_indicators[2], "4 failed attempts.")
        self.assertEqual(formatted_indicators[3], "<script>alert('xss')</script>")

        # HTML escape test
        escaped_lines = [
            f'<div class="risk-line"><span class="risk-tag">[!]</span> {html.escape(item)}</div>'
            for item in formatted_indicators
        ]
        self.assertIn("&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;", escaped_lines[3])
        self.assertNotIn("<script>", escaped_lines[3])

    def test_hud_card_safe_state_renders_clean_summary(self):
        # When only non-risk indicators exist, HUD should display clean safe state
        analysis = {
            "indicators": ["No major behavioral deviation detected"]
        }
        raw_indicators = analysis.get("indicators", []) or []
        formatted_indicators = []
        for it in raw_indicators:
            fmt = app.format_risk_indicator(it)
            if fmt and fmt not in formatted_indicators:
                formatted_indicators.append(fmt)

        self.assertEqual(len(formatted_indicators), 0)

    def test_analyze_dataset_tx_stringified_list_indicators(self):
        fake_api_res = {
            "result": {
                "decision": "FRAUD",
                "fraud_score": 85.0,
                "confidence": 90.0,
                "high_score_agent_count": 2,
                "risk_indicators": '["high_ip_risk", "repeated_failed_attempts"]',
                "user_id": "U1001",
            }
        }
        with patch("app.call_api", return_value=fake_api_res):
            res = app.analyze_dataset_tx("T1")
            self.assertIsNotNone(res)
            self.assertEqual(res["indicators"], ["high_ip_risk", "repeated_failed_attempts"])

    def test_analyze_manual_tx_stringified_list_indicators(self):
        fake_api_res = {
            "result": {
                "decision": "FRAUD",
                "fraud_score": 85.0,
                "confidence": 90.0,
                "high_score_agent_count": 2,
                "risk_indicators": '["high_ip_risk", "repeated_failed_attempts"]',
                "user_id": "U9999",
            }
        }
        payload = {
            "user_id": "U9999",
            "transaction_amount": 50000.0,
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
        with patch("app.call_api", return_value=fake_api_res):
            res = app.analyze_manual_tx(payload)
            self.assertIsNotNone(res)
            self.assertEqual(res["indicators"], ["high_ip_risk", "repeated_failed_attempts"])

if __name__ == "__main__":
    unittest.main()
