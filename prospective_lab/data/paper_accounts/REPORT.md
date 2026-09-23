# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T15:45:58.550+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 375.62 | 2 | 0 | 6 | -23.28 |
| E30_H300_C300 | 361.95 | 2 | 0 | 6 | -34.95 |
| E30_H900_C100 | 288.33 | 2 | 0 | 3 | -110.57 |
| E30_H900_C300 | 282.50 | 2 | 0 | 3 | -114.40 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 370.99 | 2 | 0 | 6 | -27.91 |
| E60_H300_C300 | 357.42 | 2 | 0 | 6 | -39.48 |
| E60_H900_C100 | 296.19 | 2 | 0 | 3 | -102.71 |
| E60_H900_C300 | 290.20 | 2 | 0 | 3 | -106.70 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 285.31 | 2 | 0 | 6 | -113.59 |
| E120_H300_C300 | 273.47 | 2 | 0 | 6 | -123.43 |
| E120_H900_C100 | 249.60 | 3 | 0 | 2 | -98.75 |
| E120_H900_C300 | 244.55 | 3 | 0 | 2 | -100.80 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 345.01 | 0 | 0 | 6 | -154.99 |
| E300_H300_C300 | 336.01 | 0 | 0 | 6 | -163.99 |
| E300_H900_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H900_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
