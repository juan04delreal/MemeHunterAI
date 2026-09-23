# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:07:11.411+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 286.51 | 4 | 0 | 11 | -11.29 |
| E30_H300_C300 | 260.49 | 4 | 0 | 11 | -33.31 |
| E30_H900_C100 | 831.67 | 4 | 0 | 6 | +533.87 |
| E30_H900_C300 | 804.75 | 4 | 0 | 6 | +510.95 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 493.45 | 5 | 0 | 10 | +246.20 |
| E60_H300_C300 | 463.26 | 5 | 0 | 10 | +221.01 |
| E60_H900_C100 | 46.28 | 5 | 0 | 5 | -200.97 |
| E60_H900_C300 | 35.23 | 5 | 0 | 5 | -207.02 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 241.18 | 4 | 0 | 10 | -56.62 |
| E120_H300_C300 | 218.10 | 4 | 0 | 10 | -75.70 |
| E120_H900_C100 | 49.90 | 5 | 0 | 5 | -197.35 |
| E120_H900_C300 | 38.78 | 5 | 0 | 5 | -203.47 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 568.73 | 1 | 0 | 10 | +119.28 |
| E300_H300_C300 | 545.10 | 1 | 0 | 10 | +96.65 |
| E300_H900_C100 | 176.10 | 3 | 0 | 5 | -172.25 |
| E300_H900_C300 | 166.47 | 3 | 0 | 5 | -178.88 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
