import unittest
from unittest.mock import patch, MagicMock
import requests
import app

class TestCheckHealth(unittest.TestCase):
    def test_check_health_offline(self):
        with patch("requests.get", side_effect=Exception("Connection refused")):
            res = app.check_health()
            self.assertFalse(res["online"])
            self.assertEqual(res["status"], "local")
            self.assertEqual(res["transactions_loaded"], 7500)
            self.assertEqual(res["model"], "Random Forest (Local Engine)")

    def test_check_health_timeout(self):
        with patch("requests.get", side_effect=requests.exceptions.Timeout("Request timed out")):
            res = app.check_health()
            self.assertFalse(res["online"])
            self.assertEqual(res["status"], "local")
            self.assertEqual(res["transactions_loaded"], 7500)
            self.assertEqual(res["model"], "Random Forest (Local Engine)")

    def test_check_health_connection_error(self):
        with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Connection refused")):
            res = app.check_health()
            self.assertFalse(res["online"])
            self.assertEqual(res["status"], "local")
            self.assertEqual(res["transactions_loaded"], 7500)
            self.assertEqual(res["model"], "Random Forest (Local Engine)")

    def test_check_health_online(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "transactions_loaded": 7500,
            "model": "Random Forest",
            "weak_signal": False
        }
        with patch("requests.get", return_value=mock_response):
            res = app.check_health()
            self.assertTrue(res["online"])
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["transactions_loaded"], 7500)
            self.assertEqual(res["model"], "Random Forest")

    def test_check_health_server_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        with patch("requests.get", return_value=mock_response):
            res = app.check_health()
            self.assertFalse(res["online"])
            self.assertEqual(res["status"], "local")
            self.assertEqual(res["transactions_loaded"], 7500)
            self.assertEqual(res["model"], "Random Forest (Local Engine)")

    def test_check_health_not_found_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("requests.get", return_value=mock_response):
            res = app.check_health()
            self.assertFalse(res["online"])
            self.assertEqual(res["status"], "local")

    def test_check_health_invalid_json(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        with patch("requests.get", return_value=mock_response):
            res = app.check_health()
            self.assertFalse(res["online"])
            self.assertEqual(res["status"], "local")

    def test_check_health_non_dict_json(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["not", "a", "dict"]
        with patch("requests.get", return_value=mock_response):
            res = app.check_health()
            self.assertFalse(res["online"])
            self.assertEqual(res["status"], "local")

    def test_check_health_partial_response(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        with patch("requests.get", return_value=mock_response):
            res = app.check_health()
            self.assertTrue(res["online"])
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["transactions_loaded"], 7500)
            self.assertEqual(res["model"], "Random Forest")

    def test_check_health_string_tx_count(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "transactions_loaded": "7500",
            "model": "Random Forest",
        }
        with patch("requests.get", return_value=mock_response):
            res = app.check_health()
            self.assertTrue(res["online"])
            self.assertEqual(res["transactions_loaded"], 7500)
            self.assertIsInstance(res["transactions_loaded"], int)

if __name__ == "__main__":
    unittest.main()
