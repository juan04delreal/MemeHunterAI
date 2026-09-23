# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:32:00.554+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 3.71 | 4 | 0 | 27 | -294.09 |
| E30_H300_C300 | 2.60 | 3 | 0 | 27 | -342.75 |
| E30_H900_C100 | 842.13 | 5 | 0 | 12 | +594.88 |
| E30_H900_C300 | 800.84 | 5 | 0 | 12 | +558.59 |
| E30_H3600_C100 | 100.86 | 4 | 0 | 4 | -196.94 |
| E30_H3600_C300 | 92.75 | 4 | 0 | 4 | -201.05 |
| E60_H300_C100 | 178.48 | 5 | 0 | 27 | -68.77 |
| E60_H300_C300 | 120.27 | 5 | 0 | 27 | -121.98 |
| E60_H900_C100 | 939.70 | 5 | 0 | 12 | +692.45 |
| E60_H900_C300 | 896.44 | 5 | 0 | 12 | +654.19 |
| E60_H3600_C100 | 100.82 | 4 | 0 | 4 | -196.98 |
| E60_H3600_C300 | 92.71 | 4 | 0 | 4 | -201.09 |
| E120_H300_C100 | 60.45 | 3 | 0 | 27 | -287.90 |
| E120_H300_C300 | 60.21 | 2 | 0 | 27 | -336.69 |
| E120_H900_C100 | 431.73 | 5 | 0 | 12 | +184.48 |
| E120_H900_C300 | 398.73 | 5 | 0 | 12 | +156.48 |
| E120_H3600_C100 | 149.03 | 4 | 0 | 3 | -148.77 |
| E120_H3600_C300 | 141.97 | 4 | 0 | 3 | -151.83 |
| E300_H300_C100 | 294.65 | 3 | 0 | 25 | -53.70 |
| E300_H300_C300 | 242.18 | 3 | 0 | 25 | -103.17 |
| E300_H900_C100 | 348.21 | 5 | 0 | 12 | +100.96 |
| E300_H900_C300 | 316.90 | 5 | 0 | 12 | +74.65 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
