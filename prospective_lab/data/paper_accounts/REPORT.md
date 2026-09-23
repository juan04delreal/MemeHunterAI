# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:09:25.549+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 388.80 | 3 | 0 | 13 | +40.45 |
| E30_H300_C300 | 358.69 | 3 | 0 | 13 | +13.34 |
| E30_H900_C100 | 781.12 | 5 | 0 | 6 | +533.87 |
| E30_H900_C300 | 753.20 | 5 | 0 | 6 | +510.95 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 620.25 | 3 | 0 | 13 | +271.90 |
| E60_H300_C300 | 585.47 | 3 | 0 | 13 | +240.12 |
| E60_H900_C100 | 833.13 | 5 | 0 | 6 | +585.88 |
| E60_H900_C300 | 804.17 | 5 | 0 | 6 | +561.92 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 232.15 | 3 | 0 | 12 | -116.20 |
| E120_H300_C300 | 207.23 | 3 | 0 | 12 | -138.12 |
| E120_H900_C100 | 411.41 | 4 | 0 | 6 | +113.61 |
| E120_H900_C300 | 392.98 | 4 | 0 | 6 | +99.18 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 417.08 | 4 | 0 | 10 | +119.28 |
| E300_H300_C300 | 390.45 | 4 | 0 | 10 | +96.65 |
| E300_H900_C100 | 75.00 | 5 | 0 | 5 | -172.25 |
| E300_H900_C300 | 63.37 | 5 | 0 | 5 | -178.88 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
