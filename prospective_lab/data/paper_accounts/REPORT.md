# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:51:21.102+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 33.94 | 0 | 0 | 32 | -466.06 |
| E30_H300_C300 | 13.61 | 0 | 0 | 31 | -486.39 |
| E30_H900_C100 | 660.29 | 4 | 0 | 19 | +362.49 |
| E30_H900_C300 | 610.54 | 4 | 0 | 19 | +316.74 |
| E30_H3600_C100 | 50.46 | 4 | 0 | 5 | -247.34 |
| E30_H3600_C300 | 41.35 | 4 | 0 | 5 | -252.45 |
| E60_H300_C100 | 116.91 | 1 | 0 | 44 | -332.54 |
| E60_H300_C300 | 131.80 | 1 | 0 | 42 | -316.65 |
| E60_H900_C100 | 807.59 | 3 | 0 | 19 | +459.24 |
| E60_H900_C300 | 756.89 | 3 | 0 | 19 | +411.54 |
| E60_H3600_C100 | 50.49 | 4 | 0 | 5 | -247.31 |
| E60_H3600_C300 | 41.37 | 4 | 0 | 5 | -252.43 |
| E120_H300_C100 | 34.99 | 0 | 0 | 33 | -465.01 |
| E120_H300_C300 | 15.05 | 0 | 0 | 32 | -484.95 |
| E120_H900_C100 | 285.52 | 5 | 0 | 18 | +38.27 |
| E120_H900_C300 | 243.35 | 5 | 0 | 18 | +1.10 |
| E120_H3600_C100 | 50.14 | 4 | 0 | 5 | -247.66 |
| E120_H3600_C300 | 41.04 | 4 | 0 | 5 | -252.76 |
| E300_H300_C100 | 33.19 | 2 | 0 | 39 | -365.71 |
| E300_H300_C300 | 27.27 | 2 | 0 | 35 | -369.63 |
| E300_H900_C100 | 177.83 | 5 | 0 | 17 | -69.42 |
| E300_H900_C300 | 139.85 | 5 | 0 | 17 | -102.40 |
| E300_H3600_C100 | 49.29 | 4 | 0 | 5 | -248.51 |
| E300_H3600_C300 | 40.20 | 4 | 0 | 5 | -253.60 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
