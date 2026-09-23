# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:35:24.626+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 28.30 | 2 | 0 | 30 | -370.60 |
| E30_H300_C300 | 8.08 | 2 | 0 | 29 | -388.82 |
| E30_H900_C100 | 800.15 | 4 | 0 | 15 | +502.35 |
| E30_H900_C300 | 755.67 | 4 | 0 | 15 | +461.87 |
| E30_H3600_C100 | 50.46 | 4 | 0 | 5 | -247.34 |
| E30_H3600_C300 | 41.35 | 4 | 0 | 5 | -252.45 |
| E60_H300_C100 | 97.80 | 5 | 0 | 30 | -149.45 |
| E60_H300_C300 | 35.15 | 5 | 0 | 30 | -207.10 |
| E60_H900_C100 | 843.76 | 5 | 0 | 14 | +596.51 |
| E60_H900_C300 | 798.40 | 5 | 0 | 14 | +556.15 |
| E60_H3600_C100 | 50.49 | 4 | 0 | 5 | -247.31 |
| E60_H3600_C300 | 41.37 | 4 | 0 | 5 | -252.43 |
| E120_H300_C100 | 19.72 | 3 | 0 | 29 | -328.63 |
| E120_H300_C300 | 16.26 | 2 | 0 | 29 | -380.64 |
| E120_H900_C100 | 431.73 | 5 | 0 | 12 | +184.48 |
| E120_H900_C300 | 398.73 | 5 | 0 | 12 | +156.48 |
| E120_H3600_C100 | 50.14 | 4 | 0 | 5 | -247.66 |
| E120_H3600_C300 | 41.04 | 4 | 0 | 5 | -252.76 |
| E300_H300_C100 | 100.78 | 5 | 0 | 27 | -146.47 |
| E300_H300_C300 | 44.14 | 5 | 0 | 27 | -198.11 |
| E300_H900_C100 | 348.21 | 5 | 0 | 12 | +100.96 |
| E300_H900_C300 | 316.90 | 5 | 0 | 12 | +74.65 |
| E300_H3600_C100 | 97.99 | 5 | 0 | 3 | -149.26 |
| E300_H3600_C300 | 89.94 | 5 | 0 | 3 | -152.31 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
