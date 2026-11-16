# Solana Early-Win Lab

Isolated Solana paper-trading research project. It never signs, sends, or broadcasts a transaction and contains no private key. It does not access or modify the V11 bot or its database.

## Engines

### Discovery paper trader
\`bot.py\` scans DexScreener latest Solana token profiles and simulates discovery-based entries in its own ledger tables.

### Pump.fun smart-money paper trader
\`wallet_copy.py\` tracks five public Pump.fun leaderboard wallets using Solana JSON-RPC transaction history. It looks for token balance increases (buys), then only considers tokens bought by at least two monitored wallets within a rolling 30-minute window. It rechecks DexScreener price and market quality after a 60-second observation delay before simulating an entry.

Watchlist:
- megacrabtopaxio: gVDXhoGbePACvSqN7CZBtQXFW9eyJwsgudPEwSydAkx
- ephraimschindle: JDQKDrc1TQgBRvdFh56tkta5sYcDj1SoP52Eiu64rSrT
- throatycrab1008: 29yFzeBZgxf5zqrAkKXwgZtQehRf4pL8WbV2nRJikbw8
- PetalS0l: 4HXb7ivgvjbHC3TBesmmD9LovH8tmTv9DZsq12GMvEpU
- MOGorDIE: 8ZN71XTdVo8yRovnGLmNgW3Tgniw6A4J3JGLvPD686FP

Addresses are stored in \`wallets.json\`. The first run establishes a signature cursor for each wallet and intentionally skips historical transactions; later runs persist a catch-up queue and process signature pages incrementally, draining each queued page before fetching the next, so a busy wallet is not silently truncated when more than one page of activity arrives. Missing transactions remain queued, the cursor advances only after the queue is complete, transaction lookups accept Solana v1, and HTTP 429 responses receive bounded backoff. The workflow exposes the remaining catch-up queue in its run report. A public RPC is used by default. An optional higher-capacity endpoint can be supplied as the GitHub Actions secret \`SOLANA_RPC_URL\`.

## Discovery paper-trading settings

The discovery engine has its own separate $100 virtual account. Its current code uses $5 entries, up to 5 open positions, $20,000 minimum liquidity, $50,000–$3,000,000 market-cap band, $10,000 minimum 5-minute volume, at least 25 five-minute transactions, at least 20 five-minute buys, a 5-minute buys/sells ratio of 1.50, a 1-hour buys/sells ratio of 1.10, liquidity at least 8% of market cap, and a weighted entry score of at least 60. Missing 1-hour flow data fails closed. These are new forward-only experimental filters, not thresholds selected from historical backtest optimization. Exit rules in code are a -40% stop, +150% target, trailing exit armed after a +50% peak with a 25% drawdown, or a 12-hour time exit. A -$5 UTC-day realized-loss gate pauses new entries for the rest of that UTC day; it is not a lifetime account drawdown limit.

The wallet-consensus engine also has a separate $100 virtual account; it is not funded from the discovery account. Its $10 entries, 4-position/$40 exposure cap, two-wallet/30-minute consensus and exit rules are listed below. Do not combine the two ledgers when evaluating either strategy.

## Smart-money paper strategy

- Separate virtual account: $100 starting balance.
- Simulated entry: $10 per token; maximum 4 positions and $40 total cost exposure.
- Consensus: at least 2 tracked wallets buy the same mint within 30 minutes.
- Market quality: minimum $25,000 liquidity, $50,000–$3,000,000 market cap, at least $5,000 5-minute volume, at least 10 five-minute buys, 5-minute buys/sells ratio of at least 1.50, 1-hour buys/sells ratio of at least 1.10, and liquidity at least 8% of market cap. Both initial and post-delay refreshed quotes must pass every filter.
- Entry: wait 60 seconds once per run, refresh price, then apply 1.5% adverse slippage and a 1% total fee allowance.
- Exits: -30% stop; sell half at +50%; after +80% peak gain, trail by 25%; close remainder after 6 hours.
- At most 2 new positions per workflow run.

These stricter filters are a new forward-only trial, not a claim of maximum profit or a guarantee. The discovery account currently has less than its unchanged $5 minimum position size, so it will continue scanning and managing any existing positions but cannot open a new position unless existing paper proceeds replenish cash; do not reset or top up the ledger. The wallet-consensus account remains independently funded at its existing $100 paper balance. Do not compare the new trial with prior results as if the old trades had used these filters. The engine does not yet calculate independently verified rolling 30/90-day wallet win rates or remove related wallets. It uses a two-wallet consensus filter as a starting anti-noise rule, not proof of independent smart money.

## Runtime and persistence

GitHub Actions runs every 15 minutes and supports manual dispatch. Each run tests both engines, executes the scans, and commits \`state.sqlite3\` to preserve the isolated paper ledger. Smart-money tables are separate (\`wallet_account\`, \`wallet_signals\`, \`wallet_positions\`, \`wallet_trades\`, \`wallet_runs\`) from discovery tables. GitHub Actions is scheduled automation, not a continuously running server.

## Verification

From \`early-win-lab/\`:
\`python -m unittest -v\`
\`python bot.py\`
\`python wallet_copy.py\`

## Important limitations

- A wallet's leaderboard win rate can be calculated over different periods and trade definitions. Public leaderboard numbers are snapshots, not proof of persistent edge.
- The first run seeds cursors and does not replay old buys. Wait for new wallet activity before expecting entries.
- The public Solana RPC may throttle or omit transactions; set a dedicated RPC endpoint secret for more reliable monitoring.
- DexScreener pair data can lag or be unavailable for new mints. No missing price is fabricated.
- Token balance deltas can miss complex routed trades, and token account ownership metadata is not always complete.
- The bot does not cluster wallets, model copy-trade latency beyond the observation delay, or guarantee actual market fills.
- Review at least 50–100 closed paper trades before considering any strategy change. Paper results are not evidence of live profitability.
