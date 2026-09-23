# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:03:50.543+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 380.46 | 3 | 0 | 10 | +32.11 |
| E30_H300_C300 | 356.59 | 3 | 0 | 10 | +11.24 |
| E30_H900_C100 | 38.42 | 5 | 0 | 5 | -208.83 |
| E30_H900_C300 | 27.53 | 5 | 0 | 5 | -214.72 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 594.55 | 3 | 0 | 10 | +246.20 |
| E60_H300_C300 | 566.36 | 3 | 0 | 10 | +221.01 |
| E60_H900_C100 | 46.28 | 5 | 0 | 5 | -200.97 |
| E60_H900_C300 | 35.23 | 5 | 0 | 5 | -207.02 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 392.83 | 1 | 0 | 10 | -56.62 |
| E120_H300_C300 | 372.75 | 1 | 0 | 10 | -75.70 |
| E120_H900_C100 | 151.00 | 3 | 0 | 5 | -197.35 |
| E120_H900_C300 | 141.88 | 3 | 0 | 5 | -203.47 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 604.46 | 1 | 0 | 9 | +155.01 |
| E300_H300_C300 | 582.13 | 1 | 0 | 9 | +133.68 |
| E300_H900_C100 | 226.65 | 2 | 0 | 5 | -172.25 |
| E300_H900_C300 | 218.02 | 2 | 0 | 5 | -178.88 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
