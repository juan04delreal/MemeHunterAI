# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T17:07:18.565+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 33.94 | 0 | 0 | 32 | -466.06 |
| E30_H300_C300 | 13.61 | 0 | 0 | 31 | -486.39 |
| E30_H900_C100 | 707.34 | 5 | 0 | 23 | +460.09 |
| E30_H900_C300 | 646.53 | 5 | 0 | 23 | +404.28 |
| E30_H3600_C100 | 50.46 | 4 | 0 | 5 | -247.34 |
| E30_H3600_C300 | 41.35 | 4 | 0 | 5 | -252.45 |
| E60_H300_C100 | 19.44 | 2 | 0 | 48 | -379.46 |
| E60_H300_C300 | 26.18 | 2 | 0 | 46 | -370.72 |
| E60_H900_C100 | 788.55 | 5 | 0 | 22 | +541.30 |
| E60_H900_C300 | 728.12 | 5 | 0 | 22 | +485.87 |
| E60_H3600_C100 | 50.49 | 4 | 0 | 5 | -247.31 |
| E60_H3600_C300 | 41.37 | 4 | 0 | 5 | -252.43 |
| E120_H300_C100 | 34.99 | 0 | 0 | 33 | -465.01 |
| E120_H300_C300 | 15.05 | 0 | 0 | 32 | -484.95 |
| E120_H900_C100 | 189.99 | 5 | 0 | 23 | -57.26 |
| E120_H900_C300 | 139.63 | 5 | 0 | 23 | -102.62 |
| E120_H3600_C100 | 50.14 | 4 | 0 | 5 | -247.66 |
| E120_H3600_C300 | 41.04 | 4 | 0 | 5 | -252.76 |
| E300_H300_C100 | 35.47 | 0 | 0 | 41 | -464.53 |
| E300_H300_C300 | 29.50 | 0 | 0 | 37 | -470.50 |
| E300_H900_C100 | 41.32 | 4 | 0 | 22 | -256.48 |
| E300_H900_C300 | 49.57 | 3 | 0 | 22 | -295.78 |
| E300_H3600_C100 | 49.29 | 4 | 0 | 5 | -248.51 |
| E300_H3600_C300 | 40.20 | 4 | 0 | 5 | -253.60 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
