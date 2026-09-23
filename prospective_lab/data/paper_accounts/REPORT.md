# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:11:40.266+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 408.07 | 3 | 0 | 15 | +59.72 |
| E30_H300_C300 | 373.53 | 3 | 0 | 15 | +28.18 |
| E30_H900_C100 | 745.39 | 5 | 0 | 7 | +498.14 |
| E30_H900_C300 | 716.17 | 5 | 0 | 7 | +473.92 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 609.79 | 3 | 0 | 14 | +261.44 |
| E60_H300_C300 | 573.20 | 3 | 0 | 14 | +227.85 |
| E60_H900_C100 | 847.42 | 4 | 0 | 7 | +549.62 |
| E60_H900_C300 | 818.16 | 4 | 0 | 7 | +524.36 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 323.48 | 2 | 0 | 14 | -75.42 |
| E120_H300_C300 | 294.70 | 2 | 0 | 14 | -102.20 |
| E120_H900_C100 | 360.86 | 5 | 0 | 6 | +113.61 |
| E120_H900_C300 | 341.43 | 5 | 0 | 6 | +99.18 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 376.52 | 4 | 0 | 11 | +78.72 |
| E300_H300_C300 | 348.69 | 4 | 0 | 11 | +54.89 |
| E300_H900_C100 | 427.51 | 4 | 0 | 6 | +129.71 |
| E300_H900_C300 | 408.76 | 4 | 0 | 6 | +114.96 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
