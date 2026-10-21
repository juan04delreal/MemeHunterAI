import tempfile, unittest
from pathlib import Path
import bot

class EarlyWinLabTests(unittest.TestCase):
    def test_filters_reject_low_liquidity(self):
        pair={"priceUsd":"0.01","liquidity":{"usd":1000},"marketCap":200000,"volume":{"m5":9000},
              "txns":{"m5":{"buys":20,"sells":5},"h1":{"buys":100,"sells":50}}}
        score,_,reasons=bot.score_pair(pair)
        self.assertEqual(score,0)
        self.assertIn("insufficient price/liquidity",reasons)

    def test_quality_pair_scores_positive(self):
        pair={"priceUsd":"0.01","liquidity":{"usd":80000},"marketCap":400000,"volume":{"m5":25000},
              "txns":{"m5":{"buys":80,"sells":20},"h1":{"buys":400,"sells":180}}}
        score,metrics,_=bot.score_pair(pair)
        self.assertGreater(score,35)
        self.assertEqual(metrics["price"],0.01)

    def test_account_starts_at_100(self):
        with tempfile.TemporaryDirectory() as tmp:
            old=bot.DB_PATH
            try:
                bot.DB_PATH=Path(tmp)/"test.sqlite3"
                db=bot.connect()
                row=db.execute("SELECT cash,starting_cash FROM account WHERE id=1").fetchone()
                self.assertEqual(row["cash"],100.0)
                self.assertEqual(row["starting_cash"],100.0)
                db.close()
            finally: bot.DB_PATH=old

if __name__=="__main__": unittest.main()
