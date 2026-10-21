# Solana Early-Win Lab

Isolated paper-only Solana token research bot. It does not use a wallet, private key, signer, or live order endpoint. It does not modify V11 or its database.

## Runtime

GitHub Actions runs every 15 minutes and can be run manually. Each run fetches public latest Solana token profiles and DexScreener pair data, filters liquidity/market cap/5-minute volume/transaction count, scores short-term buyer flow, simulates trades, and persists a separate SQLite ledger.

Initial settings: $100 balance, $5 positions, maximum 5 open positions, 1% simulated entry/exit fee allowance, 1% slippage per side, -40% stop, +150% target, trailing exit after +50% peak return with 25% drawdown, 12-hour time exit, and $5 daily realized-loss circuit breaker.

## Important limitations

- Wallet realized-PnL attribution and coordinated-wallet clustering are not integrated yet. This version does not claim a buyer is a profitable trader based only on activity.
- Public feeds can omit tokens or delay updates. Missing prices are not fabricated.
- A +150% target is a test rule, not a forecast.
- Fill, liquidity impact and slippage assumptions are approximations. Review at least 30–50 closed trades before judging performance.
- GitHub Actions is scheduled automation, not a continuously running server.
- Ledger lives in state.sqlite3 and is committed by the workflow. Never store secrets or wallet keys here.

## Results

Open the Actions tab and choose Early-Win Lab Paper Trading. Logs print JSON containing cash, estimated equity, realized PnL, positions, and scan counts.

## Local test

Run python -m unittest -v, then python bot.py.
