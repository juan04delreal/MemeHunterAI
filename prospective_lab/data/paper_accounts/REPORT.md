# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T15:48:12.037+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 478.84 | 0 | 0 | 8 | -21.16 |
| E30_H300_C300 | 463.09 | 0 | 0 | 8 | -36.91 |
| E30_H900_C100 | 291.17 | 0 | 0 | 5 | -208.83 |
| E30_H900_C300 | 285.28 | 0 | 0 | 5 | -214.72 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 370.99 | 2 | 0 | 6 | -27.91 |
| E60_H300_C300 | 357.42 | 2 | 0 | 6 | -39.48 |
| E60_H900_C100 | 298.36 | 1 | 0 | 4 | -151.09 |
| E60_H900_C300 | 292.32 | 1 | 0 | 4 | -156.13 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 285.31 | 2 | 0 | 6 | -113.59 |
| E120_H300_C300 | 273.47 | 2 | 0 | 6 | -123.43 |
| E120_H900_C100 | 302.03 | 1 | 0 | 4 | -147.42 |
| E120_H900_C300 | 295.92 | 1 | 0 | 4 | -152.53 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 243.91 | 2 | 0 | 6 | -154.99 |
| E300_H300_C300 | 232.91 | 2 | 0 | 6 | -163.99 |
| E300_H900_C100 | 249.04 | 3 | 0 | 2 | -99.31 |
| E300_H900_C300 | 244.00 | 3 | 0 | 2 | -101.35 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
