# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:30:53.043+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 3.71 | 4 | 0 | 27 | -294.09 |
| E30_H300_C300 | 2.60 | 3 | 0 | 27 | -342.75 |
| E30_H900_C100 | 842.13 | 5 | 0 | 12 | +594.88 |
| E30_H900_C300 | 800.84 | 5 | 0 | 12 | +558.59 |
| E30_H3600_C100 | 98.56 | 5 | 0 | 3 | -148.69 |
| E30_H3600_C300 | 90.49 | 5 | 0 | 3 | -151.76 |
| E60_H300_C100 | 270.85 | 5 | 0 | 25 | +23.60 |
| E60_H300_C300 | 214.82 | 5 | 0 | 25 | -27.43 |
| E60_H900_C100 | 939.70 | 5 | 0 | 12 | +692.45 |
| E60_H900_C300 | 896.44 | 5 | 0 | 12 | +654.19 |
| E60_H3600_C100 | 149.22 | 4 | 0 | 3 | -148.58 |
| E60_H3600_C300 | 142.15 | 4 | 0 | 3 | -151.65 |
| E120_H300_C100 | 50.09 | 5 | 0 | 25 | -197.16 |
| E120_H300_C300 | 50.06 | 4 | 0 | 25 | -243.74 |
| E120_H900_C100 | 431.73 | 5 | 0 | 12 | +184.48 |
| E120_H900_C300 | 398.73 | 5 | 0 | 12 | +156.48 |
| E120_H3600_C100 | 148.50 | 5 | 0 | 2 | -98.75 |
| E120_H3600_C300 | 141.45 | 5 | 0 | 2 | -100.80 |
| E300_H300_C100 | 344.13 | 3 | 0 | 24 | -4.22 |
| E300_H300_C300 | 292.68 | 3 | 0 | 24 | -52.67 |
| E300_H900_C100 | 398.76 | 4 | 0 | 12 | +100.96 |
| E300_H900_C300 | 368.45 | 4 | 0 | 12 | +74.65 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
