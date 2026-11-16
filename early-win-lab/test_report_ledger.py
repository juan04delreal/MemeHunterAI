import tempfile
import unittest
from pathlib import Path

import bot
import report_ledger
import wallet_copy


class LedgerReportTests(unittest.TestCase):
    def test_reports_separate_accounts_and_reconciles_closed_trade(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.sqlite3"
            old_bot, old_wallet = bot.DB_PATH, wallet_copy.DB_PATH
            try:
                bot.DB_PATH = path
                db = bot.connect()
                db.execute("UPDATE account SET cash=99.0 WHERE id=1")
                db.execute(
                    """INSERT INTO trades(token_address,symbol,opened_at,closed_at,entry_price,exit_price,cost,proceeds,pnl,roi,reason,entry_score)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    ("Mint111", "TEST", "2026-01-01T00:00:00+00:00", "2026-01-01T00:05:00+00:00",
                     1.0, 0.8, 5.0, 4.0, -1.0, -0.2, "stop_loss", 42.0)
                )
                db.commit()
                db.close()

                wallet_copy.DB_PATH = path
                db = wallet_copy.db_connect()
                db.close()

                report = report_ledger.build_report(path)
                discovery = report["discovery_engine"]
                wallet = report["pump_fun_wallet_consensus_engine"]
                self.assertEqual(discovery["starting_cash"], 100.0)
                self.assertEqual(discovery["cash"], 99.0)
                self.assertEqual(discovery["realized_closed_pnl"], -1.0)
                self.assertEqual(discovery["total_modeled_pnl_at_last_stored_price"], -1.0)
                self.assertEqual(discovery["reconciliation_delta"], 0.0)
                self.assertEqual(discovery["trades"][0]["mint"] if "mint" in discovery["trades"][0] else discovery["trades"][0]["token_address"], "Mint111")
                self.assertEqual(wallet["starting_cash"], 100.0)
                self.assertEqual(wallet["cash"], 100.0)
                self.assertEqual(wallet["closed_trade_count"], 0)
            finally:
                bot.DB_PATH, wallet_copy.DB_PATH = old_bot, old_wallet


if __name__ == "__main__":
    unittest.main()
