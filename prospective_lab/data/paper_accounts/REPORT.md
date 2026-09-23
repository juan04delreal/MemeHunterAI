# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:10:32.719+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 390.36 | 3 | 0 | 14 | +42.01 |
| E30_H300_C300 | 358.20 | 3 | 0 | 14 | +12.85 |
| E30_H900_C100 | 795.94 | 4 | 0 | 7 | +498.14 |
| E30_H900_C300 | 767.72 | 4 | 0 | 7 | +473.92 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 660.34 | 2 | 0 | 14 | +261.44 |
| E60_H300_C300 | 624.75 | 2 | 0 | 14 | +227.85 |
| E60_H900_C100 | 833.13 | 5 | 0 | 6 | +585.88 |
| E60_H900_C300 | 804.17 | 5 | 0 | 6 | +561.92 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 272.11 | 3 | 0 | 13 | -76.24 |
| E120_H300_C300 | 244.36 | 3 | 0 | 13 | -100.99 |
| E120_H900_C100 | 360.86 | 5 | 0 | 6 | +113.61 |
| E120_H900_C300 | 341.43 | 5 | 0 | 6 | +99.18 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 417.08 | 4 | 0 | 10 | +119.28 |
| E300_H300_C300 | 390.45 | 4 | 0 | 10 | +96.65 |
| E300_H900_C100 | 75.00 | 5 | 0 | 5 | -172.25 |
| E300_H900_C300 | 63.37 | 5 | 0 | 5 | -178.88 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
