# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:29:45.529+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 51.46 | 5 | 0 | 25 | -195.79 |
| E30_H300_C300 | 51.41 | 4 | 0 | 25 | -242.39 |
| E30_H900_C100 | 842.13 | 5 | 0 | 12 | +594.88 |
| E30_H900_C300 | 800.84 | 5 | 0 | 12 | +558.59 |
| E30_H3600_C100 | 148.56 | 5 | 0 | 2 | -98.69 |
| E30_H3600_C300 | 141.51 | 5 | 0 | 2 | -100.74 |
| E60_H300_C100 | 270.85 | 5 | 0 | 25 | +23.60 |
| E60_H300_C300 | 214.82 | 5 | 0 | 25 | -27.43 |
| E60_H900_C100 | 939.70 | 5 | 0 | 12 | +692.45 |
| E60_H900_C300 | 896.44 | 5 | 0 | 12 | +654.19 |
| E60_H3600_C100 | 148.71 | 5 | 0 | 2 | -98.54 |
| E60_H3600_C300 | 141.65 | 5 | 0 | 2 | -100.60 |
| E120_H300_C100 | 151.19 | 3 | 0 | 25 | -197.16 |
| E120_H300_C300 | 101.61 | 3 | 0 | 25 | -243.74 |
| E120_H900_C100 | 431.73 | 5 | 0 | 12 | +184.48 |
| E120_H900_C300 | 398.73 | 5 | 0 | 12 | +156.48 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 445.23 | 1 | 0 | 24 | -4.22 |
| E300_H300_C300 | 395.78 | 1 | 0 | 24 | -52.67 |
| E300_H900_C100 | 448.49 | 4 | 0 | 11 | +150.69 |
| E300_H900_C300 | 419.21 | 4 | 0 | 11 | +125.41 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
