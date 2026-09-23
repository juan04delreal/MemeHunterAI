# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T15:40:23.269+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 413.44 | 1 | 0 | 5 | -36.01 |
| E30_H300_C300 | 403.05 | 1 | 0 | 5 | -45.40 |
| E30_H900_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H900_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 407.21 | 1 | 0 | 5 | -42.24 |
| E60_H300_C300 | 396.96 | 1 | 0 | 5 | -51.49 |
| E60_H900_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H900_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 319.49 | 1 | 0 | 5 | -129.96 |
| E120_H300_C300 | 311.01 | 1 | 0 | 5 | -137.44 |
| E120_H900_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H900_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 321.61 | 2 | 0 | 3 | -77.29 |
| E300_H300_C300 | 315.10 | 2 | 0 | 3 | -81.80 |
| E300_H900_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H900_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
