# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:15:01.358+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 405.25 | 3 | 0 | 16 | +56.90 |
| E30_H300_C300 | 368.75 | 3 | 0 | 16 | +23.40 |
| E30_H900_C100 | 745.39 | 5 | 0 | 7 | +498.14 |
| E30_H900_C300 | 716.17 | 5 | 0 | 7 | +473.92 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 624.48 | 3 | 0 | 16 | +276.13 |
| E60_H300_C300 | 583.54 | 3 | 0 | 16 | +238.19 |
| E60_H900_C100 | 796.87 | 5 | 0 | 7 | +549.62 |
| E60_H900_C300 | 766.61 | 5 | 0 | 7 | +524.36 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 341.40 | 2 | 0 | 16 | -57.50 |
| E120_H300_C300 | 308.21 | 2 | 0 | 16 | -88.69 |
| E120_H900_C100 | 323.85 | 5 | 0 | 7 | +76.60 |
| E120_H900_C300 | 303.15 | 5 | 0 | 7 | +60.90 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 397.90 | 3 | 0 | 14 | +49.55 |
| E300_H300_C300 | 365.59 | 3 | 0 | 14 | +20.24 |
| E300_H900_C100 | 376.96 | 5 | 0 | 6 | +129.71 |
| E300_H900_C300 | 357.21 | 5 | 0 | 6 | +114.96 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
