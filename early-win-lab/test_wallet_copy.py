import tempfile
import unittest
from pathlib import Path
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

if __name__ == "__main__":
    unittest.main()
