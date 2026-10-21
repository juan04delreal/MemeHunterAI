"""Isolated Solana Early-Win Lab paper trader. Paper only; no wallet keys or live transactions."""
from __future__ import annotations
import json, os, sqlite3, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("EARLY_WIN_DB", ROOT / "state.sqlite3"))
STARTING_CASH, POSITION_SIZE, MAX_OPEN_POSITIONS = 100.0, 5.0, 5
MIN_LIQUIDITY_USD, MIN_MCAP_USD, MAX_MCAP_USD = 20_000.0, 50_000.0, 3_000_000.0
MIN_VOL5M_USD, MIN_TXNS5M, MAX_HOLD_HOURS = 5_000.0, 15, 12
STOP_LOSS_PCT, TAKE_PROFIT_PCT = -0.40, 1.50
TRAIL_ARM_PCT, TRAIL_DRAWDOWN_PCT = 0.50, 0.25
FEE_RATE, SLIPPAGE_RATE, DAILY_LOSS_LIMIT = 0.01, 0.01, 5.0
USER_AGENT = "EarlyWinLab/1.0 paper-trading research bot"

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS account(id INTEGER PRIMARY KEY CHECK(id=1),cash REAL NOT NULL,starting_cash REAL NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS positions(token_address TEXT PRIMARY KEY,symbol TEXT,name TEXT,entry_price REAL NOT NULL,qty REAL NOT NULL,cost REAL NOT NULL,opened_at TEXT NOT NULL,peak_price REAL NOT NULL,last_price REAL NOT NULL,source_url TEXT,entry_score REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY AUTOINCREMENT,token_address TEXT NOT NULL,symbol TEXT,opened_at TEXT NOT NULL,closed_at TEXT NOT NULL,entry_price REAL NOT NULL,exit_price REAL NOT NULL,cost REAL NOT NULL,proceeds REAL NOT NULL,pnl REAL NOT NULL,roi REAL NOT NULL,reason TEXT NOT NULL,entry_score REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS scans(id INTEGER PRIMARY KEY AUTOINCREMENT,scanned_at TEXT NOT NULL,profiles_seen INTEGER NOT NULL,pairs_seen INTEGER NOT NULL,candidates INTEGER NOT NULL,opened INTEGER NOT NULL,closed INTEGER NOT NULL,note TEXT);
    CREATE TABLE IF NOT EXISTS seen_tokens(token_address TEXT PRIMARY KEY,first_seen_at TEXT NOT NULL);
    """)
    db.execute("INSERT OR IGNORE INTO account VALUES(1,?,?,?)",(STARTING_CASH,STARTING_CASH,now_iso()))
    db.commit()
    return db

def fetch_json(url, timeout=15):
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def discover_profiles():
    found={}
    for url in ("https://api.dexscreener.com/token-profiles/latest/v1","https://api.dexscreener.com/token-boosts/latest/v1"):
        try: payload=fetch_json(url)
        except (urllib.error.URLError,TimeoutError,json.JSONDecodeError,OSError): continue
        if isinstance(payload,list):
            for item in payload:
                if item.get("chainId")=="solana" and item.get("tokenAddress"):
                    found[item["tokenAddress"]]=item
    return list(found.values())

def token_pairs(addresses):
    pairs=[]
    for offset in range(0,min(len(addresses),60),30):
        batch=addresses[offset:offset+30]
        if not batch: continue
        url="https://api.dexscreener.com/latest/dex/tokens/"+urllib.parse.quote(",".join(batch),safe=",")
        try:
            payload=fetch_json(url)
            pairs.extend(p for p in (payload.get("pairs") or []) if p.get("chainId")=="solana")
        except (urllib.error.URLError,TimeoutError,json.JSONDecodeError,OSError): pass
        time.sleep(0.15)
    return pairs

def num(value):
    try: return float(value or 0)
    except (TypeError,ValueError): return 0.0

def metrics(pair):
    txns=pair.get("txns") or {}; m5=txns.get("m5") or {}; h1=txns.get("h1") or {}
    vol=pair.get("volume") or {}; liq=pair.get("liquidity") or {}
    return {"price":num(pair.get("priceUsd")),"liquidity":num(liq.get("usd")),
            "mcap":num(pair.get("marketCap") or pair.get("fdv")),"vol5m":num(vol.get("m5")),
            "buys5m":num(m5.get("buys")),"sells5m":num(m5.get("sells")),
            "buys1h":num(h1.get("buys")),"sells1h":num(h1.get("sells"))}

def score_pair(pair):
    m=metrics(pair)
    if m["price"]<=0 or m["liquidity"]<MIN_LIQUIDITY_USD: return 0.0,m,["insufficient price/liquidity"]
    if not MIN_MCAP_USD<=m["mcap"]<=MAX_MCAP_USD: return 0.0,m,["market cap outside test band"]
    if m["vol5m"]<MIN_VOL5M_USD: return 0.0,m,["insufficient 5m volume"]
    if m["buys5m"]+m["sells5m"]<MIN_TXNS5M: return 0.0,m,["insufficient 5m transactions"]
    score=min(25.0,m["vol5m"]/max(m["liquidity"],1)*100.0)
    total=m["buys5m"]+m["sells5m"]
    score+=min(35.0,max(0.0,((m["buys5m"]/total if total else 0)-0.45)*100))
    total1=m["buys1h"]+m["sells1h"]
    if total1: score+=min(20.0,max(0.0,(m["buys1h"]/total1-0.45)*60))
    score+=min(20.0,m["liquidity"]/10_000.0)
    return round(min(score,100),2),m,["liquidity/market-cap filters passed","volume and buyer-flow score"]

def daily_realized_pnl(db):
    day=datetime.now(timezone.utc).date().isoformat()
    return float(db.execute("SELECT COALESCE(SUM(pnl),0) p FROM trades WHERE substr(closed_at,1,10)>=?",(day,)).fetchone()["p"])

def close_position(db,pos,price,reason):
    if price<=0:return
    exit_price=price*(1-SLIPPAGE_RATE)
    proceeds=pos["qty"]*exit_price*(1-FEE_RATE/2)
    pnl=proceeds-pos["cost"]; roi=pnl/pos["cost"] if pos["cost"] else 0
    db.execute("UPDATE account SET cash=cash+? WHERE id=1",(proceeds,))
    db.execute("""INSERT INTO trades(token_address,symbol,opened_at,closed_at,entry_price,exit_price,cost,proceeds,pnl,roi,reason,entry_score) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
       (pos["token_address"],pos["symbol"],pos["opened_at"],now_iso(),pos["entry_price"],exit_price,pos["cost"],proceeds,pnl,roi,reason,pos["entry_score"]))
    db.execute("DELETE FROM positions WHERE token_address=?",(pos["token_address"],))

def run_once():
    db=connect(); opened=closed=0; note="ok"
    try:
        profiles=discover_profiles()
        if not profiles: note="No fresh profiles returned; no prices fabricated."
        pairs=token_pairs([x["tokenAddress"] for x in profiles])
        best={}
        for pair in pairs:
            address=(pair.get("baseToken") or {}).get("address")
            if address and (address not in best or metrics(pair)["liquidity"]>metrics(best[address])["liquidity"]): best[address]=pair
        for pos in db.execute("SELECT * FROM positions").fetchall():
            pair=best.get(pos["token_address"])
            if not pair: continue
            m=metrics(pair); price=m["price"]
            if price<=0: continue
            peak=max(pos["peak_price"],price)
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(pos["opened_at"])).total_seconds()/3600
            roi=price/pos["entry_price"]-1; peak_roi=peak/pos["entry_price"]-1
            reason=("stop_loss" if roi<=STOP_LOSS_PCT else "target_150pct" if roi>=TAKE_PROFIT_PCT else
                    "trailing_exit" if peak_roi>=TRAIL_ARM_PCT and price<=peak*(1-TRAIL_DRAWDOWN_PCT) else
                    "time_exit" if age>=MAX_HOLD_HOURS else None)
            db.execute("UPDATE positions SET last_price=?,peak_price=? WHERE token_address=?",(price,peak,pos["token_address"]))
            if reason:
                close_position(db,db.execute("SELECT * FROM positions WHERE token_address=?",(pos["token_address"],)).fetchone(),price,reason); closed+=1
        if daily_realized_pnl(db)>-DAILY_LOSS_LIMIT:
            cash=float(db.execute("SELECT cash FROM account WHERE id=1").fetchone()["cash"])
            count=int(db.execute("SELECT COUNT(*) n FROM positions").fetchone()["n"])
            ranked=[]
            for address,pair in best.items():
                if db.execute("SELECT 1 FROM positions WHERE token_address=?",(address,)).fetchone(): continue
                if db.execute("SELECT 1 FROM seen_tokens WHERE token_address=?",(address,)).fetchone(): continue
                score,m,_=score_pair(pair)
                if score>=35: ranked.append((score,pair,m))
            ranked.sort(key=lambda x:x[0],reverse=True)
            for score,pair,m in ranked:
                if count>=MAX_OPEN_POSITIONS or cash<POSITION_SIZE: break
                address=(pair.get("baseToken") or {}).get("address")
                if not address: continue
                entry=m["price"]*(1+SLIPPAGE_RATE); cost=POSITION_SIZE
                qty=cost*(1-FEE_RATE/2)/entry
                db.execute("UPDATE account SET cash=cash-? WHERE id=1",(cost,)); cash-=cost
                db.execute("""INSERT INTO positions VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (address,(pair.get("baseToken") or {}).get("symbol","?"),(pair.get("baseToken") or {}).get("name","?"),
                     entry,qty,cost,now_iso(),entry,entry,pair.get("url"),score))
                db.execute("INSERT OR IGNORE INTO seen_tokens VALUES(?,?)",(address,now_iso()))
                count+=1; opened+=1
        db.execute("INSERT INTO scans(scanned_at,profiles_seen,pairs_seen,candidates,opened,closed,note) VALUES(?,?,?,?,?,?,?)",
                   (now_iso(),len(profiles),len(pairs),len(best),opened,closed,note)); db.commit()
        acct=db.execute("SELECT cash,starting_cash FROM account WHERE id=1").fetchone()
        positions=db.execute("SELECT qty,last_price FROM positions").fetchall()
        realized=db.execute("SELECT COALESCE(SUM(pnl),0) p FROM trades").fetchone()["p"]
        result={"status":"ok","mode":"PAPER_ONLY","timestamp":now_iso(),"starting_balance":round(acct["starting_cash"],2),
          "cash":round(acct["cash"],2),"open_positions":len(positions),
          "closed_trades":db.execute("SELECT COUNT(*) n FROM trades").fetchone()["n"],"realized_pnl":round(realized,4),
          "equity_estimate":round(acct["cash"]+sum(r["qty"]*r["last_price"] for r in positions),4),
          "profiles_seen":len(profiles),"pairs_seen":len(pairs),"tokens_ranked":len(best),
          "opened_this_run":opened,"closed_this_run":closed,"note":note}
        print(json.dumps(result,indent=2)); return result
    finally: db.close()

if __name__=="__main__": run_once()
