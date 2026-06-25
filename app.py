import threading
import time
from flask import Flask, render_template

from config import START_BALANCE, SCAN_SECONDS, MIN_SCORE_TO_BUY
from scanner import scan_best_coin, token_data
from paper_trader import PaperTrader
from notifications import notify

app = Flask(__name__)
trader = PaperTrader(START_BALANCE)

state = {
    "status": "Starting",
    "reason": "Loading Meme Hunter AI",
    "best": None,
    "watchlist": [],
    "last_alert": "None yet",
    "last_scan": "Never",
}

def money(x):
    return f"${x:,.2f}"

def bot_loop():
    state["last_alert"] = notify("🤖 Meme Hunter AI Started", "Dashboard and paper scanner are running.")

    while True:
        try:
            if trader.position:
                coin = token_data(trader.position["address"])
                if coin:
                    trade = trader.update_position(coin)
                    if trade:
                        state["status"] = "Sold"
                        state["reason"] = trade["reason"]
                        state["last_alert"] = notify(
                            "🔴 SELL PAPER TRADE",
                            f"{trade['name']} ({trade['coin']})\n{trade['reason']}\nP/L: {money(trade['pnl'])} | {trade['pnl_pct']:.2f}%"
                        )
                    else:
                        pnl = ((coin["price"] - trader.position["entry"]) / trader.position["entry"]) * 100
                        state["status"] = "Holding"
                        state["reason"] = f"{trader.position['symbol']} P/L {pnl:.2f}%"
            else:
                state["status"] = "Scanning"
                state["reason"] = "Looking for strong newly listed Pump-style coins"

                best, watchlist = scan_best_coin()
                state["best"] = best
                state["watchlist"] = watchlist
                state["last_scan"] = time.strftime("%H:%M:%S")

                if best and best["score"] >= MIN_SCORE_TO_BUY:
                    trader.buy(best)
                    state["status"] = "Bought"
                    state["reason"] = "High-score paper entry"
                    state["last_alert"] = notify(
                        "🟢 BUY PAPER TRADE",
                        f"{best['name']} ({best['symbol']})\nScore: {best['score']}/100\nEntry: ${best['price']:.10f}"
                    )

        except Exception as e:
            state["status"] = "Error"
            state["reason"] = str(e)

        time.sleep(SCAN_SECONDS)

@app.route("/")
def dashboard():
    return render_template(
        "dashboard.html",
        state=state,
        trader=trader,
        stats=trader.stats(),
        money=money,
    )

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
