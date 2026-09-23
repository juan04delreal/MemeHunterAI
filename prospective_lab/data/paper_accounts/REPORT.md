# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:19:32.345+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 287.46 | 4 | 0 | 19 | -10.34 |
| E30_H300_C300 | 245.25 | 4 | 0 | 19 | -48.55 |
| E30_H900_C100 | 778.86 | 4 | 0 | 10 | +481.06 |
| E30_H900_C300 | 744.92 | 4 | 0 | 10 | +451.12 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 615.72 | 2 | 0 | 19 | +216.82 |
| E60_H300_C300 | 570.92 | 2 | 0 | 19 | +174.02 |
| E60_H900_C100 | 984.22 | 2 | 0 | 10 | +585.32 |
| E60_H900_C300 | 950.18 | 2 | 0 | 10 | +553.28 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 396.52 | 3 | 0 | 18 | +48.17 |
| E120_H300_C300 | 356.15 | 3 | 0 | 18 | +10.80 |
| E120_H900_C100 | 364.74 | 3 | 0 | 9 | +16.39 |
| E120_H900_C300 | 343.21 | 3 | 0 | 9 | -2.14 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 537.58 | 3 | 0 | 16 | +189.23 |
| E300_H300_C300 | 498.40 | 3 | 0 | 16 | +153.05 |
| E300_H900_C100 | 341.34 | 5 | 0 | 7 | +94.09 |
| E300_H900_C300 | 320.28 | 5 | 0 | 7 | +78.03 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
