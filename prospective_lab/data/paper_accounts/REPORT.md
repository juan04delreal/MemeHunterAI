# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:34:16.255+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 28.30 | 2 | 0 | 30 | -370.60 |
| E30_H300_C300 | 8.08 | 2 | 0 | 29 | -388.82 |
| E30_H900_C100 | 795.63 | 5 | 0 | 13 | +548.38 |
| E30_H900_C300 | 753.26 | 5 | 0 | 13 | +511.01 |
| E30_H3600_C100 | 50.46 | 4 | 0 | 5 | -247.34 |
| E30_H3600_C300 | 41.35 | 4 | 0 | 5 | -252.45 |
| E60_H300_C100 | 232.52 | 3 | 0 | 29 | -115.83 |
| E60_H300_C300 | 173.21 | 3 | 0 | 29 | -172.14 |
| E60_H900_C100 | 939.70 | 5 | 0 | 12 | +692.45 |
| E60_H900_C300 | 896.44 | 5 | 0 | 12 | +654.19 |
| E60_H3600_C100 | 50.49 | 4 | 0 | 5 | -247.31 |
| E60_H3600_C300 | 41.37 | 4 | 0 | 5 | -252.43 |
| E120_H300_C100 | 24.99 | 3 | 0 | 28 | -323.36 |
| E120_H300_C300 | 23.45 | 2 | 0 | 28 | -373.45 |
| E120_H900_C100 | 431.73 | 5 | 0 | 12 | +184.48 |
| E120_H900_C300 | 398.73 | 5 | 0 | 12 | +156.48 |
| E120_H3600_C100 | 49.95 | 5 | 0 | 4 | -197.30 |
| E120_H3600_C300 | 40.84 | 5 | 0 | 4 | -201.41 |
| E300_H300_C100 | 193.55 | 5 | 0 | 25 | -53.70 |
| E300_H300_C300 | 139.08 | 5 | 0 | 25 | -103.17 |
| E300_H900_C100 | 348.21 | 5 | 0 | 12 | +100.96 |
| E300_H900_C300 | 316.90 | 5 | 0 | 12 | +74.65 |
| E300_H3600_C100 | 147.95 | 5 | 0 | 2 | -99.30 |
| E300_H3600_C300 | 140.91 | 5 | 0 | 2 | -101.34 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
