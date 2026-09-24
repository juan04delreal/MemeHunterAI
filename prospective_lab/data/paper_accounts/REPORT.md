# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-24T16:53:27.942+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 33.94 | 0 | 0 | 32 | -466.06 |
| E30_H300_C300 | 13.61 | 0 | 0 | 31 | -486.39 |
| E30_H900_C100 | 42.06 | 0 | 0 | 78 | -457.94 |
| E30_H900_C300 | 39.19 | 0 | 0 | 69 | -460.81 |
| E30_H3600_C100 | 34.98 | 0 | 0 | 11 | -465.02 |
| E30_H3600_C300 | 41.68 | 0 | 0 | 10 | -458.32 |
| E60_H300_C100 | 16.79 | 0 | 0 | 51 | -483.21 |
| E60_H300_C300 | 21.57 | 0 | 0 | 49 | -478.43 |
| E60_H900_C100 | 49.70 | 0 | 0 | 67 | -450.30 |
| E60_H900_C300 | 40.62 | 0 | 0 | 60 | -459.38 |
| E60_H3600_C100 | 49.18 | 0 | 0 | 10 | -450.82 |
| E60_H3600_C300 | 38.07 | 0 | 0 | 10 | -461.93 |
| E120_H300_C100 | 34.99 | 0 | 0 | 33 | -465.01 |
| E120_H300_C300 | 15.05 | 0 | 0 | 32 | -484.95 |
| E120_H900_C100 | 1.97 | 0 | 0 | 41 | -498.03 |
| E120_H900_C300 | 42.55 | 0 | 0 | 37 | -457.45 |
| E120_H3600_C100 | 43.96 | 0 | 0 | 10 | -456.04 |
| E120_H3600_C300 | 32.95 | 0 | 0 | 10 | -467.05 |
| E300_H300_C100 | 35.47 | 0 | 0 | 41 | -464.53 |
| E300_H300_C300 | 29.50 | 0 | 0 | 37 | -470.50 |
| E300_H900_C100 | 6.75 | 0 | 0 | 29 | -493.25 |
| E300_H900_C300 | 9.57 | 0 | 0 | 28 | -490.43 |
| E300_H3600_C100 | 14.66 | 0 | 0 | 13 | -485.34 |
| E300_H3600_C300 | 48.37 | 0 | 0 | 12 | -451.63 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
