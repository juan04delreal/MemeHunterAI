# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:44:32.163+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 33.94 | 0 | 0 | 32 | -466.06 |
| E30_H300_C300 | 13.61 | 0 | 0 | 31 | -486.39 |
| E30_H900_C100 | 649.75 | 5 | 0 | 17 | +402.50 |
| E30_H900_C300 | 602.24 | 5 | 0 | 17 | +359.99 |
| E30_H3600_C100 | 50.46 | 4 | 0 | 5 | -247.34 |
| E30_H3600_C300 | 41.35 | 4 | 0 | 5 | -252.45 |
| E60_H300_C100 | 215.06 | 3 | 0 | 37 | -133.29 |
| E60_H300_C300 | 238.46 | 2 | 0 | 36 | -158.44 |
| E60_H900_C100 | 813.52 | 4 | 0 | 17 | +515.72 |
| E60_H900_C300 | 764.72 | 4 | 0 | 17 | +470.92 |
| E60_H3600_C100 | 50.49 | 4 | 0 | 5 | -247.31 |
| E60_H3600_C300 | 41.37 | 4 | 0 | 5 | -252.43 |
| E120_H300_C100 | 34.52 | 1 | 0 | 32 | -414.93 |
| E120_H300_C300 | 14.59 | 1 | 0 | 31 | -433.86 |
| E120_H900_C100 | 322.17 | 4 | 0 | 17 | +24.37 |
| E120_H900_C300 | 283.30 | 4 | 0 | 17 | -10.50 |
| E120_H3600_C100 | 50.14 | 4 | 0 | 5 | -247.66 |
| E120_H3600_C300 | 41.04 | 4 | 0 | 5 | -252.76 |
| E300_H300_C100 | 74.38 | 3 | 0 | 35 | -273.97 |
| E300_H300_C300 | 50.15 | 2 | 0 | 33 | -346.75 |
| E300_H900_C100 | 276.50 | 5 | 0 | 15 | +29.25 |
| E300_H900_C300 | 240.58 | 5 | 0 | 15 | -1.67 |
| E300_H3600_C100 | 49.29 | 4 | 0 | 5 | -248.51 |
| E300_H3600_C300 | 40.20 | 4 | 0 | 5 | -253.60 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
