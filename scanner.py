import requests
from config import (
    MIN_LIQUIDITY, MAX_MARKET_CAP, MIN_VOLUME_5M,
    MIN_BUY_PRESSURE, MAX_CANDIDATES, WATCHLIST_SIZE
)

DEX_LATEST = "https://api.dexscreener.com/token-profiles/latest/v1"
DEX_TOKEN = "https://api.dexscreener.com/latest/dex/tokens/{address}"

def latest_pump_tokens():
    try:
        data = requests.get(DEX_LATEST, timeout=10).json()
        tokens = []
        for item in data:
            addr = item.get("tokenAddress", "")
            if item.get("chainId") == "solana" and addr.endswith("pump"):
                tokens.append(addr)
        return tokens[:MAX_CANDIDATES]
    except Exception:
        return []

def token_data(address: str):
    try:
        data = requests.get(DEX_TOKEN.format(address=address), timeout=10).json()
        pairs = data.get("pairs") or []
        if not pairs:
            return None

        pair = max(
            pairs,
            key=lambda p: float((p.get("liquidity") or {}).get("usd", 0) or 0)
        )

        base = pair.get("baseToken") or {}
        txns = pair.get("txns") or {}
        m5 = txns.get("m5") or {}

        buys = int(m5.get("buys", 0) or 0)
        sells = int(m5.get("sells", 0) or 0)
        pressure = buys / max(sells, 1)

        d = {
            "address": address,
            "name": base.get("name", "Unknown"),
            "symbol": base.get("symbol", "???"),
            "price": float(pair.get("priceUsd", 0) or 0),
            "liquidity": float((pair.get("liquidity") or {}).get("usd", 0) or 0),
            "market_cap": float(pair.get("marketCap", 0) or pair.get("fdv", 0) or 0),
            "volume_5m": float((pair.get("volume") or {}).get("m5", 0) or 0),
            "buys": buys,
            "sells": sells,
            "pressure": pressure,
            "score": 0,
            "url": pair.get("url", ""),
        }

        score = 0
        if d["liquidity"] >= MIN_LIQUIDITY:
            score += 25
        if 0 < d["market_cap"] <= MAX_MARKET_CAP:
            score += 20
        if d["volume_5m"] >= MIN_VOLUME_5M:
            score += 25
        if d["pressure"] >= MIN_BUY_PRESSURE:
            score += 20
        if buys > sells:
            score += 10

        d["score"] = score
        return d
    except Exception:
        return None

def scan_best_coin():
    coins = []
    for address in latest_pump_tokens():
        d = token_data(address)
        if not d:
            continue
        if d["liquidity"] < MIN_LIQUIDITY:
            continue
        if d["market_cap"] <= 0 or d["market_cap"] > MAX_MARKET_CAP:
            continue
        if d["volume_5m"] < MIN_VOLUME_5M:
            continue
        if d["pressure"] < MIN_BUY_PRESSURE:
            continue
        coins.append(d)

    coins.sort(key=lambda c: c["score"], reverse=True)
    return (coins[0] if coins else None), coins[:WATCHLIST_SIZE]
