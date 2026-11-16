"""Read-only JSON report for both isolated Early-Win Lab paper ledgers."""
from __future__ import annotations
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("EARLY_WIN_DB", ROOT / "state.sqlite3"))


def _has_table(db, name):
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _dict_rows(rows):
    return [dict(row) for row in rows]


def _open_marks(positions, qty_key="qty", price_key="last_price"):
    rows = _dict_rows(positions)
    for row in rows:
        row["stored_mark_value"] = round(float(row.get(qty_key) or 0) * float(row.get(price_key) or 0), 8)
        row["unrealized_pnl_at_stored_mark"] = round(row["stored_mark_value"] - float(row.get("cost") or 0), 8)
    return rows


def _account_summary(db, account_table, trade_table, position_table, trade_mint_key):
    if not all(_has_table(db, name) for name in (account_table, trade_table, position_table)):
        return {"status": "not_initialized"}
    account = db.execute(f"SELECT * FROM {account_table} WHERE id=1").fetchone()
    if account is None:
        return {"status": "missing_account_row"}
    trades = _dict_rows(db.execute(f"SELECT * FROM {trade_table} ORDER BY id").fetchall())
    positions = _open_marks(db.execute(f"SELECT * FROM {position_table} ORDER BY opened_at").fetchall())
    realized = sum(float(t.get("pnl") or 0) for t in trades)
    open_cost = sum(float(p.get("cost") or 0) for p in positions)
    marked_value = sum(float(p.get("stored_mark_value") or 0) for p in positions)
    unrealized = marked_value - open_cost
    cash = float(account["cash"])
    starting = float(account["starting_cash"])
    equity = cash + marked_value
    net = equity - starting
    for trade in trades:
        trade["roi_pct"] = round(float(trade.get("roi") or 0) * 100, 4)
        trade["coin_name"] = None
        trade["coin_name_note"] = "Closed-trade schema stores symbol and mint, not token name"
        if "source_wallets" in trade:
            try:
                trade["source_wallets"] = json.loads(trade["source_wallets"])
            except (TypeError, json.JSONDecodeError):
                pass
    return {
        "status": "available",
        "starting_cash": round(starting, 8),
        "cash": round(cash, 8),
        "closed_trade_count": len(trades),
        "realized_closed_pnl": round(realized, 8),
        "open_position_count": len(positions),
        "open_cost_basis": round(open_cost, 8),
        "open_marked_value_at_last_stored_price": round(marked_value, 8),
        "open_unrealized_pnl_at_last_stored_price": round(unrealized, 8),
        "equity_estimate_at_last_stored_price": round(equity, 8),
        "total_modeled_pnl_at_last_stored_price": round(net, 8),
        "reconciliation_delta": round(net - (realized + unrealized), 8),
        "open_positions": positions,
        "trades": trades,
    }


def build_report(db_path=DB_PATH):
    path = Path(db_path)
    if not path.exists():
        return {"status": "ledger_missing", "database_path": str(path)}
    uri = "file:" + path.resolve().as_posix() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True)
    db.row_factory = sqlite3.Row
    try:
        discovery = _account_summary(db, "account", "trades", "positions", "token_address")
        wallet = _account_summary(db, "wallet_account", "wallet_trades", "wallet_positions", "mint")
        scans = _dict_rows(db.execute("SELECT * FROM scans ORDER BY id DESC LIMIT 20").fetchall()) if _has_table(db, "scans") else []
        wallet_runs = _dict_rows(db.execute("SELECT * FROM wallet_runs ORDER BY id DESC LIMIT 20").fetchall()) if _has_table(db, "wallet_runs") else []
        signal_count = db.execute("SELECT COUNT(*) AS n FROM wallet_signals").fetchone()["n"] if _has_table(db, "wallet_signals") else None
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "database_path": str(path),
            "discovery_engine": discovery,
            "pump_fun_wallet_consensus_engine": wallet,
            "scan_history_latest_20": scans,
            "wallet_run_history_latest_20": wallet_runs,
            "wallet_signal_count": signal_count,
            "important_notes": [
                "Two separate virtual accounts are reported independently; do not add them together as one portfolio.",
                "Open-position marks use the last price stored by a scan, not a guaranteed executable quote.",
                "Closed-trade rows store symbols and mints, not token names; no name is inferred.",
                "All results are simulated paper-account values, not real funds or realized on-chain profit."
            ]
        }
    finally:
        db.close()


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, sort_keys=True))
