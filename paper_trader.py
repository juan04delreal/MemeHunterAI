from config import BUY_AMOUNT, STOP_LOSS, TAKE_PROFIT, TRAILING_STOP

class PaperTrader:
    def __init__(self, start_balance: float):
        self.balance = start_balance
        self.equity = start_balance
        self.position = None
        self.trades = []

    def buy(self, coin: dict):
        if self.position is not None or self.balance < BUY_AMOUNT:
            return None

        tokens = BUY_AMOUNT / coin["price"]
        self.balance -= BUY_AMOUNT
        self.position = {
            "address": coin["address"],
            "name": coin["name"],
            "symbol": coin["symbol"],
            "entry": coin["price"],
            "tokens": tokens,
            "highest": coin["price"],
            "score": coin["score"],
        }
        return self.position

    def update_position(self, coin: dict):
        if not self.position:
            self.equity = self.balance
            return None

        price = coin["price"]
        p = self.position

        if price > p["highest"]:
            p["highest"] = price

        pnl = (price - p["entry"]) / p["entry"]
        trail = (price - p["highest"]) / p["highest"]
        self.equity = self.balance + (p["tokens"] * price)

        if pnl <= STOP_LOSS:
            return self.sell(price, "Stop loss")
        if pnl >= TAKE_PROFIT:
            return self.sell(price, "Take profit")
        if trail <= -TRAILING_STOP:
            return self.sell(price, "Trailing stop")

        return None

    def sell(self, price: float, reason: str):
        p = self.position
        if not p:
            return None

        value = p["tokens"] * price
        pnl = value - BUY_AMOUNT
        pnl_pct = ((price - p["entry"]) / p["entry"]) * 100

        trade = {
            "coin": p["symbol"],
            "name": p["name"],
            "reason": reason,
            "entry": p["entry"],
            "exit": price,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
        }

        self.balance += value
        self.equity = self.balance
        self.trades.insert(0, trade)
        self.position = None
        return trade

    def stats(self):
        wins = len([t for t in self.trades if t["pnl"] > 0])
        losses = len([t for t in self.trades if t["pnl"] <= 0])
        total = wins + losses
        win_rate = (wins / total * 100) if total else 0
        total_pnl = sum(t["pnl"] for t in self.trades)
        return {
            "wins": wins,
            "losses": losses,
            "total": total,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
        }
