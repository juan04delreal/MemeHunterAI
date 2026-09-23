# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T17:31:22.837+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 33.94 | 0 | 0 | 32 | -466.06 |
| E30_H300_C300 | 13.61 | 0 | 0 | 31 | -486.39 |
| E30_H900_C100 | 643.90 | 4 | 0 | 31 | +346.10 |
| E30_H900_C300 | 570.22 | 4 | 0 | 31 | +276.42 |
| E30_H3600_C100 | 49.42 | 2 | 0 | 8 | -349.48 |
| E30_H3600_C300 | 38.30 | 2 | 0 | 8 | -358.60 |
| E60_H300_C100 | 16.79 | 0 | 0 | 51 | -483.21 |
| E60_H300_C300 | 21.57 | 0 | 0 | 49 | -478.43 |
| E60_H900_C100 | 700.31 | 5 | 0 | 29 | +453.06 |
| E60_H900_C300 | 627.51 | 5 | 0 | 29 | +385.26 |
| E60_H3600_C100 | 45.28 | 2 | 0 | 8 | -353.62 |
| E60_H3600_C300 | 34.24 | 2 | 0 | 8 | -362.66 |
| E120_H300_C100 | 34.99 | 0 | 0 | 33 | -465.01 |
| E120_H300_C300 | 15.05 | 0 | 0 | 32 | -484.95 |
| E120_H900_C100 | 162.66 | 4 | 0 | 30 | -135.14 |
| E120_H900_C300 | 100.73 | 4 | 0 | 30 | -193.07 |
| E120_H3600_C100 | 92.05 | 2 | 0 | 7 | -306.85 |
| E120_H3600_C300 | 82.10 | 2 | 0 | 7 | -314.80 |
| E300_H300_C100 | 35.47 | 0 | 0 | 41 | -464.53 |
| E300_H300_C300 | 29.50 | 0 | 0 | 37 | -470.50 |
| E300_H900_C100 | 15.11 | 1 | 0 | 27 | -434.34 |
| E300_H900_C300 | 19.79 | 1 | 0 | 26 | -428.66 |
| E300_H3600_C100 | 49.29 | 4 | 0 | 5 | -248.51 |
| E300_H3600_C300 | 40.20 | 4 | 0 | 5 | -253.60 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
