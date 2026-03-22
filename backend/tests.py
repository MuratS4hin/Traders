"""
Unit tests for the Traders backend.

Tests cover:
    - pivot point calculation (pivot.py)
    - demo transaction storage (transactions.py)
    - Flask API endpoints (app.py)
"""

import unittest
import json
import os
import tempfile

# Use a temporary DB so tests are isolated from production data
import transactions as txn_module

_original_db_path = txn_module.DB_PATH


class TestPivotCalculation(unittest.TestCase):

    def test_basic_pivot(self):
        from pivot import calculate_pivot_points
        levels = calculate_pivot_points(high=110.0, low=90.0, close=100.0)
        self.assertAlmostEqual(levels["pivot"], 100.0)
        self.assertAlmostEqual(levels["r1"],    110.0)
        self.assertAlmostEqual(levels["s1"],    90.0)
        self.assertAlmostEqual(levels["r2"],    120.0)
        self.assertAlmostEqual(levels["s2"],    80.0)

    def test_pivot_rounding(self):
        from pivot import calculate_pivot_points
        levels = calculate_pivot_points(high=150.33, low=140.11, close=145.22)
        self.assertIsInstance(levels["pivot"], float)
        # Ensure values are rounded to at most 4 decimal places
        for key in ("pivot", "s1", "s2", "r1", "r2"):
            self.assertEqual(round(levels[key], 4), levels[key])

    def test_trading_signal_buy(self):
        from pivot import calculate_pivot_points, trading_signal
        levels = calculate_pivot_points(high=110.0, low=90.0, close=100.0)
        # Price at or below S1 (90) → BUY
        self.assertEqual(trading_signal(88.0, levels), "BUY")
        self.assertEqual(trading_signal(90.0, levels), "BUY")

    def test_trading_signal_sell(self):
        from pivot import calculate_pivot_points, trading_signal
        levels = calculate_pivot_points(high=110.0, low=90.0, close=100.0)
        # Price at or above R1 (110) → SELL
        self.assertEqual(trading_signal(115.0, levels), "SELL")
        self.assertEqual(trading_signal(110.0, levels), "SELL")

    def test_trading_signal_hold(self):
        from pivot import calculate_pivot_points, trading_signal
        levels = calculate_pivot_points(high=110.0, low=90.0, close=100.0)
        self.assertEqual(trading_signal(100.0, levels), "HOLD")


class TestTransactions(unittest.TestCase):

    def setUp(self):
        # Redirect DB to a temp file for test isolation
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        txn_module.DB_PATH = self._tmp.name
        txn_module.init_db()

    def tearDown(self):
        txn_module.DB_PATH = _original_db_path
        os.unlink(self._tmp.name)

    def test_record_and_retrieve(self):
        txn = txn_module.record_transaction("AAPL", "BUY", 175.50, quantity=2)
        self.assertEqual(txn["ticker"], "AAPL")
        self.assertEqual(txn["action"], "BUY")
        self.assertAlmostEqual(txn["price"], 175.50)
        self.assertEqual(txn["quantity"], 2)
        self.assertIn("timestamp", txn)

    def test_get_all_transactions(self):
        txn_module.record_transaction("AAPL", "BUY", 175.0)
        txn_module.record_transaction("MSFT", "SELL", 320.0)
        all_txns = txn_module.get_all_transactions()
        self.assertEqual(len(all_txns), 2)

    def test_get_transactions_by_ticker(self):
        txn_module.record_transaction("AAPL", "BUY", 175.0)
        txn_module.record_transaction("MSFT", "SELL", 320.0)
        txn_module.record_transaction("AAPL", "HOLD", 176.0)
        aapl = txn_module.get_transactions_by_ticker("AAPL")
        self.assertEqual(len(aapl), 2)
        for t in aapl:
            self.assertEqual(t["ticker"], "AAPL")

    def test_invalid_action_raises(self):
        with self.assertRaises(ValueError):
            txn_module.record_transaction("AAPL", "INVALID", 175.0)


class TestFlaskAPI(unittest.TestCase):

    def setUp(self):
        # Redirect DB to a temp file for test isolation
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        txn_module.DB_PATH = self._tmp.name
        txn_module.init_db()

        import app as flask_app
        flask_app.app.config["TESTING"] = True
        self.client = flask_app.app.test_client()

    def tearDown(self):
        txn_module.DB_PATH = _original_db_path
        os.unlink(self._tmp.name)

    def test_transactions_empty(self):
        resp = self.client.get("/transactions")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("transactions", data)
        self.assertIsInstance(data["transactions"], list)

    def test_trade_missing_ticker(self):
        resp = self.client.post(
            "/trade",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_trade_invalid_ticker(self):
        resp = self.client.post(
            "/trade",
            data=json.dumps({"ticker": "NOTREAL"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_trade_invalid_quantity(self):
        resp = self.client.post(
            "/trade",
            data=json.dumps({"ticker": "AAPL", "quantity": 0}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_unknown_stock_route(self):
        resp = self.client.get("/stocks/NOTREAL")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
