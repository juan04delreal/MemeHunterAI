# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:36:31.930+00:00

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
| E60_H300_C100 | 148.12 | 3 | 0 | 32 | -200.23 |
| E60_H300_C300 | 84.45 | 3 | 0 | 32 | -260.90 |
| E60_H900_C100 | 913.25 | 4 | 0 | 15 | +615.45 |
| E60_H900_C300 | 866.49 | 4 | 0 | 15 | +572.69 |
| E60_H3600_C100 | 50.49 | 4 | 0 | 5 | -247.31 |
| E60_H3600_C300 | 41.37 | 4 | 0 | 5 | -252.43 |
| E120_H300_C100 | 34.16 | 2 | 0 | 30 | -364.74 |
| E120_H300_C300 | 16.26 | 2 | 0 | 29 | -380.64 |
| E120_H900_C100 | 340.21 | 5 | 0 | 14 | +92.96 |
| E120_H900_C300 | 305.02 | 5 | 0 | 14 | +62.77 |
| E120_H3600_C100 | 50.14 | 4 | 0 | 5 | -247.66 |
| E120_H3600_C300 | 41.04 | 4 | 0 | 5 | -252.76 |
| E300_H300_C100 | 100.78 | 5 | 0 | 27 | -146.47 |
| E300_H300_C300 | 44.14 | 5 | 0 | 27 | -198.11 |
| E300_H900_C100 | 348.21 | 5 | 0 | 12 | +100.96 |
| E300_H900_C300 | 316.90 | 5 | 0 | 12 | +74.65 |
| E300_H3600_C100 | 99.60 | 4 | 0 | 4 | -198.20 |
| E300_H3600_C300 | 91.52 | 4 | 0 | 4 | -202.28 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
