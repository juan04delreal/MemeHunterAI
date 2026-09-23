# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T15:35:54.319+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 398.07 | 2 | 0 | 3 | -0.83 |
| E30_H300_C300 | 390.02 | 2 | 0 | 3 | -6.88 |
| E30_H900_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H900_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 395.94 | 2 | 0 | 3 | -2.96 |
| E60_H300_C300 | 387.94 | 2 | 0 | 3 | -8.96 |
| E60_H900_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H900_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 272.88 | 3 | 0 | 2 | -75.47 |
| E120_H300_C300 | 267.36 | 3 | 0 | 2 | -77.99 |
| E120_H900_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H900_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 297.80 | 4 | 0 | 0 | +0.00 |
| E300_H300_C300 | 293.80 | 4 | 0 | 0 | +0.00 |
| E300_H900_C100 | 297.80 | 4 | 0 | 0 | +0.00 |
| E300_H900_C300 | 293.80 | 4 | 0 | 0 | +0.00 |
| E300_H3600_C100 | 297.80 | 4 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 293.80 | 4 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
