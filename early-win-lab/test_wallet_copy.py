import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import wallet_copy as wc


class WalletCopyTests(unittest.TestCase):
    def test_token_delta_detects_buy_and_sell(self):
        wallet = "Wallet111"
        tx = {"meta": {
            "preTokenBalances": [{"owner": wallet, "mint": "Mint111", "uiTokenAmount": {"uiAmount": 0}}],
            "postTokenBalances": [{"owner": wallet, "mint": "Mint111", "uiTokenAmount": {"uiAmount": 12.5}}],
        }}
        self.assertEqual(wc.token_deltas(tx, wallet), {"Mint111": 12.5})

    def test_ignores_other_wallet_and_wsol(self):
        tx = {"meta": {"preTokenBalances": [], "postTokenBalances": [
            {"owner": "Other", "mint": "Mint111", "uiTokenAmount": {"uiAmount": 5}},
            {"owner": "Wallet111", "mint": wc.WSOL, "uiTokenAmount": {"uiAmount": 2}},
        ]}}
        self.assertEqual(wc.token_deltas(tx, "Wallet111"), {})

    def test_pair_metrics_and_buy_pressure(self):
        pair = {"priceUsd":"0.01","liquidity":{"usd":20000},"marketCap":100000,
                "volume":{"m5":5000},"txns":{"m5":{"buys":22,"sells":10}}}
        m = wc.pair_metrics(pair)
        self.assertEqual(m["price"], 0.01)
        self.assertGreaterEqual(m["ratio"], 2.0)

    def test_wallet_watchlist_has_five_unique_addresses(self):
        wallets = wc.load_wallets()
        addresses = [w["address"] for w in wallets]
        self.assertEqual(len(addresses), 5)
        self.assertEqual(len(set(addresses)), 5)

    def test_wallet_ledger_is_separate_and_starts_at_100(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = wc.DB_PATH
            try:
                wc.DB_PATH = Path(tmp) / "wallet_test.sqlite3"
                db = wc.db_connect()
                row = db.execute("SELECT cash,starting_cash FROM wallet_account WHERE id=1").fetchone()
                self.assertEqual(row["cash"], 100.0)
                self.assertEqual(row["starting_cash"], 100.0)
                self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='account'").fetchone())
                db.close()
            finally:
                wc.DB_PATH = old

    def test_persists_catchup_pages_and_advances_only_after_processing(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_path = wc.DB_PATH
            try:
                wc.DB_PATH = Path(tmp) / "wallet_test.sqlite3"
                db = wc.db_connect()
                db.execute("INSERT INTO wallet_cursors VALUES(?,?,?)", ("Wallet111", "old-cursor", "2026-01-01T00:00:00+00:00"))
                db.commit()
                page1 = [{"signature": f"new-{i:03d}", "blockTime": 2000-i} for i in range(100)]
                page2 = [{"signature": "old-cursor", "blockTime": 1000}]
                def fake_rpc(method, params):
                    if method == "getSignaturesForAddress":
                        if "before" not in params[1]:
                            return page1
                        return page2
                    if method == "getTransaction":
                        self.assertEqual(params[1]["maxSupportedTransactionVersion"], 1)
                        return {"meta": {}}
                    raise AssertionError(method)
                with mock.patch.object(wc, "rpc", side_effect=fake_rpc), mock.patch.object(wc.time, "sleep"):
                    count, note = wc.collect_wallet_signals(db, "Wallet111")
                self.assertEqual(count, 0)
                self.assertIn("cursor held", note)
                saved = db.execute("SELECT signature FROM wallet_cursors WHERE wallet='Wallet111'").fetchone()["signature"]
                self.assertEqual(saved, "old-cursor")
                pending = db.execute("SELECT COUNT(*) n FROM wallet_pending_signatures").fetchone()["n"]
                self.assertEqual(pending, 0)
                self.assertEqual(db.execute("SELECT COUNT(*) n FROM wallet_catchup").fetchone()["n"], 1)
                with mock.patch.object(wc, "rpc", side_effect=fake_rpc), mock.patch.object(wc.time, "sleep"):
                    count, note = wc.collect_wallet_signals(db, "Wallet111")
                saved = db.execute("SELECT signature FROM wallet_cursors WHERE wallet='Wallet111'").fetchone()["signature"]
                self.assertEqual(saved, "new-000")
                self.assertEqual(db.execute("SELECT COUNT(*) n FROM wallet_catchup").fetchone()["n"], 0)
                db.close()
            finally:
                wc.DB_PATH = old_path

    def test_missing_transaction_stays_pending_and_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_path = wc.DB_PATH
            try:
                wc.DB_PATH = Path(tmp) / "wallet_test.sqlite3"
                db = wc.db_connect()
                db.execute("INSERT INTO wallet_cursors VALUES(?,?,?)", ("Wallet111", "old-cursor", "2026-01-01T00:00:00+00:00"))
                db.commit()
                page = [{"signature":"new-signature","blockTime":2000},{"signature":"old-cursor","blockTime":1000}]
                state = {"missing": True}
                def fake_rpc(method, params):
                    if method == "getSignaturesForAddress":
                        return page
                    if method == "getTransaction":
                        self.assertEqual(params[1]["maxSupportedTransactionVersion"], 1)
                        return None if state["missing"] else {"meta": {}}
                    raise AssertionError(method)
                with mock.patch.object(wc, "rpc", side_effect=fake_rpc), mock.patch.object(wc.time, "sleep"):
                    _, note = wc.collect_wallet_signals(db, "Wallet111")
                self.assertIn("pending signature retained", note)
                self.assertEqual(db.execute("SELECT signature FROM wallet_cursors WHERE wallet='Wallet111'").fetchone()["signature"], "old-cursor")
                self.assertEqual(db.execute("SELECT COUNT(*) n FROM wallet_pending_signatures").fetchone()["n"], 1)
                state["missing"] = False
                with mock.patch.object(wc, "rpc", side_effect=fake_rpc), mock.patch.object(wc.time, "sleep"):
                    wc.collect_wallet_signals(db, "Wallet111")
                self.assertEqual(db.execute("SELECT signature FROM wallet_cursors WHERE wallet='Wallet111'").fetchone()["signature"], "new-signature")
                self.assertEqual(db.execute("SELECT COUNT(*) n FROM wallet_pending_signatures").fetchone()["n"], 0)
                db.close()
            finally:
                wc.DB_PATH = old_path

    def test_rpc_retries_rate_limit(self):
        response = {"result": "ok"}
        http_error = urllib.error.HTTPError("https://rpc.invalid", 429, "Too Many Requests", {}, None)
        with mock.patch.object(wc, "request_json", side_effect=[http_error, response]) as request, mock.patch.object(wc.time, "sleep"):
            self.assertEqual(wc.rpc("getSlot", []), "ok")
        self.assertEqual(request.call_count, 2)


if __name__ == "__main__":
    unittest.main()
