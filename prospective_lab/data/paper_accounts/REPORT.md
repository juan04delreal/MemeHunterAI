# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T15:57:07.467+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 517.38 | 1 | 0 | 9 | +67.93 |
| E30_H300_C300 | 496.81 | 1 | 0 | 9 | +48.36 |
| E30_H900_C100 | 190.07 | 2 | 0 | 5 | -208.83 |
| E30_H900_C300 | 182.18 | 2 | 0 | 5 | -214.72 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 518.97 | 2 | 0 | 8 | +120.07 |
| E60_H300_C300 | 498.37 | 2 | 0 | 8 | +101.47 |
| E60_H900_C100 | 197.93 | 2 | 0 | 5 | -200.97 |
| E60_H900_C300 | 189.88 | 2 | 0 | 5 | -207.02 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 246.66 | 2 | 0 | 8 | -152.24 |
| E120_H300_C300 | 231.56 | 2 | 0 | 8 | -165.34 |
| E120_H900_C100 | 201.55 | 2 | 0 | 5 | -197.35 |
| E120_H900_C300 | 193.43 | 2 | 0 | 5 | -203.47 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 247.30 | 1 | 0 | 8 | -202.15 |
| E300_H300_C300 | 234.20 | 1 | 0 | 8 | -214.25 |
| E300_H900_C100 | 277.20 | 1 | 0 | 5 | -172.25 |
| E300_H900_C300 | 269.57 | 1 | 0 | 5 | -178.88 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
