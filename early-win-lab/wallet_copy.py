"""Wallet-consensus paper copier. Uses public Solana RPC + DexScreener; never signs or sends transactions."""
from __future__ import annotations
import json, os, sqlite3, time, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("EARLY_WIN_DB", ROOT / "state.sqlite3"))
CONFIG_PATH = ROOT / "wallets.json"
START_CASH = 100.0
POSITION_SIZE = 10.0
MAX_OPEN = 4
MAX_EXPOSURE = 40.0
MAX_SIGNAL_AGE_MIN = 30
SIGNATURE_PAGE_SIZE = 100
MAX_PENDING_TX_PER_WALLET = 50
RPC_REQUEST_DELAY_SECONDS = 0.5
MIN_LIQUIDITY = 15000.0
MIN_MCAP = 40000.0
MAX_MCAP = 5000000.0
MIN_VOL5M = 2000.0
MIN_BUY_SELL_RATIO = 1.10
SLIPPAGE = 0.015
FEE_RATE = 0.01
STOP = -0.30
TAKE_PROFIT = 0.50
TRAIL_ARM = 0.80
TRAIL_DRAWDOWN = 0.25
MAX_HOLD_HOURS = 6
WSOL = "So11111111111111111111111111111111111111112"
USER_AGENT = "PumpSmartMoneyPaperLab/1.0"
RPC_URL = os.environ.get("SOLANA_RPC_URL") or "https://api.mainnet-beta.solana.com"

def utcnow():
    return datetime.now(timezone.utc)

def iso_now():
    return utcnow().isoformat(timespec="seconds")

def load_wallets():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["wallets"]

def request_json(url, payload=None, timeout=18):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": USER_AGENT, "Accept": "application/json",
        **({"Content-Type": "application/json"} if data else {})
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def rpc(method, params):
    # Public Solana RPC endpoints can return 429s. Retry with bounded exponential backoff.
    for attempt in range(4):
        try:
            result = request_json(RPC_URL, {"jsonrpc":"2.0","id":1,"method":method,"params":params})
            if result.get("error"):
                raise RuntimeError(str(result["error"]))
            return result.get("result")
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 3:
                raise
            time.sleep(min(2 ** (attempt + 1), 8))
    raise RuntimeError("Solana RPC retry budget exhausted")

def db_connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS wallet_account(
      id INTEGER PRIMARY KEY CHECK(id=1), cash REAL NOT NULL, starting_cash REAL NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS wallet_cursors(wallet TEXT PRIMARY KEY, signature TEXT, initialized_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS wallet_signals(
      signature TEXT NOT NULL, wallet TEXT NOT NULL, mint TEXT NOT NULL, side TEXT NOT NULL,
      token_delta REAL NOT NULL, block_time INTEGER, seen_at TEXT NOT NULL,
      PRIMARY KEY(signature,wallet,mint,side));
    CREATE TABLE IF NOT EXISTS wallet_positions(
      mint TEXT PRIMARY KEY, symbol TEXT, name TEXT, entry_price REAL NOT NULL, qty REAL NOT NULL,
      cost REAL NOT NULL, opened_at TEXT NOT NULL, peak_price REAL NOT NULL, last_price REAL NOT NULL,
      source_wallets TEXT NOT NULL, partial_taken INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS wallet_trades(
      id INTEGER PRIMARY KEY AUTOINCREMENT, mint TEXT NOT NULL, symbol TEXT, opened_at TEXT NOT NULL,
      closed_at TEXT NOT NULL, entry_price REAL NOT NULL, exit_price REAL NOT NULL, qty REAL NOT NULL,
      cost REAL NOT NULL, proceeds REAL NOT NULL, pnl REAL NOT NULL, roi REAL NOT NULL, reason TEXT NOT NULL,
      source_wallets TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS wallet_runs(
      id INTEGER PRIMARY KEY AUTOINCREMENT, ran_at TEXT NOT NULL, wallets_checked INTEGER NOT NULL,
      new_signals INTEGER NOT NULL, eligible_mints INTEGER NOT NULL, opened INTEGER NOT NULL,
      closed INTEGER NOT NULL, note TEXT);
    CREATE TABLE IF NOT EXISTS wallet_catchup(
      wallet TEXT PRIMARY KEY, head_signature TEXT NOT NULL, target_signature TEXT NOT NULL,
      before_signature TEXT, fetch_complete INTEGER NOT NULL DEFAULT 0, started_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS wallet_pending_signatures(
      wallet TEXT NOT NULL, signature TEXT NOT NULL, block_time INTEGER, failed INTEGER NOT NULL DEFAULT 0,
      queued_at TEXT NOT NULL, PRIMARY KEY(wallet,signature));
    """)
    db.execute("INSERT OR IGNORE INTO wallet_account VALUES(1,?,?,?)",(START_CASH,START_CASH,iso_now()))
    db.commit()
    return db

def token_deltas(tx, wallet):
    meta = ((tx or {}).get("meta") or {})
    before, after = {}, {}
    for side, rows in (("before", meta.get("preTokenBalances") or []), ("after", meta.get("postTokenBalances") or [])):
        target = before if side == "before" else after
        for row in rows:
            if row.get("owner") != wallet:
                continue
            mint = row.get("mint")
            if not mint or mint == WSOL:
                continue
            amt = row.get("uiTokenAmount") or {}
            amount = float(amt.get("uiAmount") if amt.get("uiAmount") is not None else (amt.get("uiAmountString") or 0))
            target[mint] = target.get(mint, 0.0) + amount
    return {mint: after.get(mint,0.0)-before.get(mint,0.0) for mint in set(before)|set(after)
            if abs(after.get(mint,0.0)-before.get(mint,0.0)) > 1e-10}

def collect_wallet_signals(db, wallet):
    cursor = db.execute("SELECT signature FROM wallet_cursors WHERE wallet=?",(wallet,)).fetchone()
    if not cursor:
        rows = rpc("getSignaturesForAddress",[wallet,{"limit":1,"commitment":"confirmed"}]) or []
        if not rows:
            return 0, "no signatures"
        db.execute("INSERT INTO wallet_cursors VALUES(?,?,?)",(wallet,rows[0]["signature"],iso_now()))
        db.commit()
        return 0, "baseline initialized; old history skipped"

    catchup = db.execute("SELECT * FROM wallet_catchup WHERE wallet=?",(wallet,)).fetchone()
    created_catchup = False
    note = ""

    if catchup is None:
        page = rpc("getSignaturesForAddress",[wallet,{"limit":SIGNATURE_PAGE_SIZE,"commitment":"confirmed"}]) or []
        if not page:
            return 0, "ok"
        old_sig = cursor["signature"]
        newer = []
        found_cursor = False
        for item in page:
            if item.get("signature") == old_sig:
                found_cursor = True
                break
            newer.append(item)
        if not newer and found_cursor:
            return 0, "ok"
        for item in newer:
            db.execute("INSERT OR IGNORE INTO wallet_pending_signatures VALUES(?,?,?,?,?)",
                       (wallet,item["signature"],item.get("blockTime"),int(item.get("err") is not None),iso_now()))
        db.execute("INSERT INTO wallet_catchup(wallet,head_signature,target_signature,before_signature,fetch_complete,started_at) VALUES(?,?,?,?,?,?)",
                   (wallet,page[0]["signature"],old_sig,None if found_cursor else page[-1]["signature"],int(found_cursor),iso_now()))
        db.commit()
        catchup = db.execute("SELECT * FROM wallet_catchup WHERE wallet=?",(wallet,)).fetchone()
        created_catchup = True

    # Fetch at most one older page per run. The catch-up checkpoint and pending
    # signatures are durable, so high-volume wallets are not silently truncated.
    if not created_catchup and not catchup["fetch_complete"]:
        page = rpc("getSignaturesForAddress",[wallet,{"limit":SIGNATURE_PAGE_SIZE,"before":catchup["before_signature"],"commitment":"confirmed"}]) or []
        if not page:
            note = "catch-up waiting: RPC returned no older signatures; cursor held"
        else:
            found_target = False
            for item in page:
                if item.get("signature") == catchup["target_signature"]:
                    found_target = True
                    break
                db.execute("INSERT OR IGNORE INTO wallet_pending_signatures VALUES(?,?,?,?,?)",
                           (wallet,item["signature"],item.get("blockTime"),int(item.get("err") is not None),iso_now()))
            if found_target:
                db.execute("UPDATE wallet_catchup SET fetch_complete=1,before_signature=NULL WHERE wallet=?",(wallet,))
            else:
                db.execute("UPDATE wallet_catchup SET before_signature=? WHERE wallet=?",(page[-1]["signature"],wallet))
                note = "catch-up paging: saved cursor not reached yet; cursor held"
            db.commit()
        catchup = db.execute("SELECT * FROM wallet_catchup WHERE wallet=?",(wallet,)).fetchone()

    pending = db.execute("""SELECT * FROM wallet_pending_signatures WHERE wallet=?
                             ORDER BY COALESCE(block_time,0) ASC, queued_at ASC LIMIT ?""",
                          (wallet,MAX_PENDING_TX_PER_WALLET)).fetchall()
    count = 0
    for item in pending:
        if item["failed"]:
            db.execute("DELETE FROM wallet_pending_signatures WHERE wallet=? AND signature=?",(wallet,item["signature"]))
            continue
        try:
            tx = rpc("getTransaction",[item["signature"],{"encoding":"jsonParsed","maxSupportedTransactionVersion":1,"commitment":"confirmed"}])
        except Exception as exc:
            note = "transaction fetch paused; pending signature retained: " + str(exc)[:120]
            break
        if tx is None:
            note = "transaction lookup missing; pending signature retained for retry"
            continue
        for mint, delta in token_deltas(tx,wallet).items():
            side = "BUY" if delta > 0 else "SELL"
            db.execute("INSERT OR IGNORE INTO wallet_signals VALUES(?,?,?,?,?,?,?)",
                       (item["signature"],wallet,mint,side,delta,item["block_time"],iso_now()))
            if db.execute("SELECT changes()").fetchone()[0]:
                count += 1
        db.execute("DELETE FROM wallet_pending_signatures WHERE wallet=? AND signature=?",(wallet,item["signature"]))
        time.sleep(RPC_REQUEST_DELAY_SECONDS)

    db.commit()
    catchup = db.execute("SELECT * FROM wallet_catchup WHERE wallet=?",(wallet,)).fetchone()
    pending_count = int(db.execute("SELECT COUNT(*) AS n FROM wallet_pending_signatures WHERE wallet=?",(wallet,)).fetchone()["n"])
    if catchup and catchup["fetch_complete"] and pending_count == 0:
        db.execute("UPDATE wallet_cursors SET signature=?,initialized_at=? WHERE wallet=?",
                   (catchup["head_signature"],iso_now(),wallet))
        db.execute("DELETE FROM wallet_catchup WHERE wallet=?",(wallet,))
        db.commit()
        return count, note or "ok"
    if catchup:
        phase = "catch-up paging" if not catchup["fetch_complete"] else "processing catch-up"
        return count, note or f"{phase}: {pending_count} pending signatures; cursor held"
    return count, note or "ok"

def dex_pair(mint):
    try:
        payload=request_json("https://api.dexscreener.com/latest/dex/tokens/"+mint)
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None
    pairs=[p for p in (payload.get("pairs") or []) if p.get("chainId")=="solana"]
    if not pairs:
        return None
    return max(pairs,key=lambda p:float(((p.get("liquidity") or {}).get("usd")) or 0))

def pair_metrics(pair):
    tx=(pair.get("txns") or {}).get("m5") or {}
    buys=float(tx.get("buys") or 0); sells=float(tx.get("sells") or 0)
    return {
      "price":float(pair.get("priceUsd") or 0),
      "liq":float(((pair.get("liquidity") or {}).get("usd")) or 0),
      "mcap":float(pair.get("marketCap") or pair.get("fdv") or 0),
      "vol":float(((pair.get("volume") or {}).get("m5")) or 0),
      "ratio":buys/max(sells,1.0),
      "buys":buys,"sells":sells
    }

def close_qty(db, pos, qty, price, reason):
    if qty <= 0 or price <= 0: return 0.0
    exit_px=price*(1-SLIPPAGE)
    proceeds=qty*exit_px*(1-FEE_RATE/2)
    cost=pos["cost"]*(qty/pos["qty"])
    pnl=proceeds-cost
    db.execute("UPDATE wallet_account SET cash=cash+? WHERE id=1",(proceeds,))
    db.execute("""INSERT INTO wallet_trades(mint,symbol,opened_at,closed_at,entry_price,exit_price,qty,cost,proceeds,pnl,roi,reason,source_wallets)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
       (pos["mint"],pos["symbol"],pos["opened_at"],iso_now(),pos["entry_price"],exit_px,qty,cost,proceeds,pnl,pnl/cost if cost else 0,reason,pos["source_wallets"]))
    return qty

def run_once():
    db=db_connect(); new_signals=opened=closed=0; notes=[]
    try:
        wallets=load_wallets()
        for w in wallets:
            try:
                n,note=collect_wallet_signals(db,w["address"])
                new_signals+=n
                if note!="ok": notes.append(w["name"]+": "+note)
            except Exception as exc:
                notes.append(w["name"]+": "+str(exc)[:180])
        cutoff=int((utcnow()-timedelta(minutes=MAX_SIGNAL_AGE_MIN)).timestamp())
        grouped=db.execute("""SELECT mint, COUNT(DISTINCT wallet) AS n,
            GROUP_CONCAT(DISTINCT wallet) AS wallets, SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) AS buys
            FROM wallet_signals WHERE side='BUY' AND block_time>=? GROUP BY mint HAVING buys>0 ORDER BY n DESC""",(cutoff,)).fetchall()
        # Evaluate open positions first, independent of current wallet signals.
        positions=db.execute("SELECT * FROM wallet_positions").fetchall()
        for pos in positions:
            pair=dex_pair(pos["mint"])
            if not pair: continue
            m=pair_metrics(pair); price=m["price"]
            if price<=0: continue
            peak=max(pos["peak_price"],price)
            roi=price/pos["entry_price"]-1
            peak_roi=peak/pos["entry_price"]-1
            age=(utcnow()-datetime.fromisoformat(pos["opened_at"])).total_seconds()/3600
            db.execute("UPDATE wallet_positions SET peak_price=?,last_price=? WHERE mint=?",(peak,price,pos["mint"]))
            if not pos["partial_taken"] and roi>=TAKE_PROFIT:
                sold=pos["qty"]*0.5
                close_qty(db,pos,sold,price,"take_profit_50pct")
                db.execute("UPDATE wallet_positions SET qty=qty-?,cost=cost*0.5,partial_taken=1 WHERE mint=?",(sold,pos["mint"]))
                closed+=1
            elif roi<=STOP or (peak_roi>=TRAIL_ARM and price<=peak*(1-TRAIL_DRAWDOWN)) or age>=MAX_HOLD_HOURS:
                reason="stop_loss" if roi<=STOP else "trailing_exit" if peak_roi>=TRAIL_ARM and price<=peak*(1-TRAIL_DRAWDOWN) else "time_exit"
                fresh=db.execute("SELECT * FROM wallet_positions WHERE mint=?",(pos["mint"],)).fetchone()
                if fresh:
                    close_qty(db,fresh,fresh["qty"],price,reason)
                    db.execute("DELETE FROM wallet_positions WHERE mint=?",(pos["mint"],))
                    closed+=1
        cash=float(db.execute("SELECT cash FROM wallet_account WHERE id=1").fetchone()["cash"])
        open_rows=db.execute("SELECT COALESCE(SUM(cost),0) exposure,COUNT(*) n FROM wallet_positions").fetchone()
        exposure=float(open_rows["exposure"]); count=int(open_rows["n"])
        eligible=0
        delayed=False
        processed=0
        for sig in grouped:
            if sig["n"] < 2: continue
            eligible+=1
            mint=sig["mint"]
            if db.execute("SELECT 1 FROM wallet_positions WHERE mint=?",(mint,)).fetchone(): continue
            if count>=MAX_OPEN or exposure+POSITION_SIZE>MAX_EXPOSURE or cash<POSITION_SIZE: break
            pair=dex_pair(mint)
            if not pair: continue
            m=pair_metrics(pair)
            if not (m["price"]>0 and m["liq"]>=MIN_LIQUIDITY and MIN_MCAP<=m["mcap"]<=MAX_MCAP and
                    m["vol"]>=MIN_VOL5M and m["ratio"]>=MIN_BUY_SELL_RATIO):
                continue
            # Delay once per run, then re-price; cap entries per run to protect the small paper account.
            if not delayed:
                time.sleep(60)
                delayed=True
            if processed>=2: break
            refreshed=dex_pair(mint)
            if not refreshed: continue
            m2=pair_metrics(refreshed)
            if m2["price"]<=0 or m2["liq"]<MIN_LIQUIDITY or m2["ratio"]<MIN_BUY_SELL_RATIO: continue
            entry=m2["price"]*(1+SLIPPAGE)
            qty=POSITION_SIZE*(1-FEE_RATE/2)/entry
            src=json.dumps([x for x in (sig["wallets"] or "").split(",") if x])
            db.execute("INSERT INTO wallet_positions VALUES(?,?,?,?,?,?,?,?,?,?,0)",
              (mint,(refreshed.get("baseToken") or {}).get("symbol","?"),(refreshed.get("baseToken") or {}).get("name","?"),
               entry,qty,POSITION_SIZE,iso_now(),entry,entry,src))
            db.execute("UPDATE wallet_account SET cash=cash-? WHERE id=1",(POSITION_SIZE,))
            cash-=POSITION_SIZE; exposure+=POSITION_SIZE; count+=1; opened+=1; processed+=1
        db.execute("INSERT INTO wallet_runs(ran_at,wallets_checked,new_signals,eligible_mints,opened,closed,note) VALUES(?,?,?,?,?,?,?)",
          (iso_now(),len(wallets),new_signals,eligible,opened,closed,"; ".join(notes)[:1000]))
        db.commit()
        acct=db.execute("SELECT cash FROM wallet_account WHERE id=1").fetchone()
        positions=db.execute("SELECT qty,last_price,cost FROM wallet_positions").fetchall()
        realized=float(db.execute("SELECT COALESCE(SUM(pnl),0) p FROM wallet_trades").fetchone()["p"])
        pending_count=int(db.execute("SELECT COUNT(*) AS n FROM wallet_pending_signatures").fetchone()["n"])
        catchup_count=int(db.execute("SELECT COUNT(*) AS n FROM wallet_catchup").fetchone()["n"])
        result={"mode":"PAPER_ONLY","wallets_monitored":len(wallets),"new_wallet_signals":new_signals,
          "eligible_consensus_tokens":eligible,"opened":opened,"closed_or_partial":closed,
          "cash":round(acct["cash"],2),"open_positions":len(positions),"realized_pnl":round(realized,4),
          "equity_estimate":round(acct["cash"]+sum(p["qty"]*p["last_price"] for p in positions),4),
          "pending_signatures":pending_count,"wallets_catching_up":catchup_count,
          "wallets":[{"name":w["name"],"address":w["address"]} for w in wallets],"notes":notes}
        print(json.dumps(result,indent=2)); return result
    finally:
        db.close()

if __name__=="__main__":
    run_once()
