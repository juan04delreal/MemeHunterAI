# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:17:16.557+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 385.48 | 3 | 0 | 18 | +37.13 |
| E30_H300_C300 | 345.33 | 3 | 0 | 18 | -0.02 |
| E30_H900_C100 | 747.49 | 4 | 0 | 8 | +449.69 |
| E30_H900_C300 | 718.23 | 4 | 0 | 8 | +424.43 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 612.70 | 3 | 0 | 18 | +264.35 |
| E60_H300_C300 | 567.96 | 3 | 0 | 18 | +222.61 |
| E60_H900_C100 | 796.87 | 5 | 0 | 7 | +549.62 |
| E60_H900_C300 | 766.61 | 5 | 0 | 7 | +524.36 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 496.92 | 2 | 0 | 17 | +98.02 |
| E120_H300_C300 | 458.56 | 2 | 0 | 17 | +61.66 |
| E120_H900_C100 | 323.85 | 5 | 0 | 7 | +76.60 |
| E120_H900_C300 | 303.15 | 5 | 0 | 7 | +60.90 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 356.56 | 3 | 0 | 15 | +8.21 |
| E300_H300_C300 | 323.06 | 3 | 0 | 15 | -22.29 |
| E300_H900_C100 | 341.34 | 5 | 0 | 7 | +94.09 |
| E300_H900_C300 | 320.28 | 5 | 0 | 7 | +78.03 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
