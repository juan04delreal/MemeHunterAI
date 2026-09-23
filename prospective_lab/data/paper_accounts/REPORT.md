# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:37:41.500+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 29.09 | 1 | 0 | 31 | -420.36 |
| E30_H300_C300 | 8.85 | 1 | 0 | 30 | -439.60 |
| E30_H900_C100 | 749.60 | 5 | 0 | 15 | +502.35 |
| E30_H900_C300 | 704.12 | 5 | 0 | 15 | +461.87 |
| E30_H3600_C100 | 50.46 | 4 | 0 | 5 | -247.34 |
| E30_H3600_C300 | 41.35 | 4 | 0 | 5 | -252.45 |
| E60_H300_C100 | 97.57 | 4 | 0 | 32 | -200.23 |
| E60_H300_C300 | 32.90 | 4 | 0 | 32 | -260.90 |
| E60_H900_C100 | 862.70 | 5 | 0 | 15 | +615.45 |
| E60_H900_C300 | 814.94 | 5 | 0 | 15 | +572.69 |
| E60_H3600_C100 | 50.49 | 4 | 0 | 5 | -247.31 |
| E60_H3600_C300 | 41.37 | 4 | 0 | 5 | -252.43 |
| E120_H300_C100 | 34.86 | 1 | 0 | 31 | -414.59 |
| E120_H300_C300 | 16.95 | 1 | 0 | 30 | -431.50 |
| E120_H900_C100 | 421.85 | 4 | 0 | 15 | +124.05 |
| E120_H900_C300 | 385.01 | 4 | 0 | 15 | +91.21 |
| E120_H3600_C100 | 50.14 | 4 | 0 | 5 | -247.66 |
| E120_H3600_C300 | 41.04 | 4 | 0 | 5 | -252.76 |
| E300_H300_C100 | 101.65 | 4 | 0 | 28 | -196.15 |
| E300_H300_C300 | 45.00 | 4 | 0 | 28 | -248.80 |
| E300_H900_C100 | 348.21 | 5 | 0 | 12 | +100.96 |
| E300_H900_C300 | 316.90 | 5 | 0 | 12 | +74.65 |
| E300_H3600_C100 | 49.29 | 4 | 0 | 5 | -248.51 |
| E300_H3600_C300 | 40.20 | 4 | 0 | 5 | -253.60 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
