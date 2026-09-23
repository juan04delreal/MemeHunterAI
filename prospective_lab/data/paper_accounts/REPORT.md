# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:21:46.469+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 291.76 | 3 | 0 | 21 | -56.59 |
| E30_H300_C300 | 247.44 | 3 | 0 | 21 | -97.91 |
| E30_H900_C100 | 728.31 | 5 | 0 | 10 | +481.06 |
| E30_H900_C300 | 693.37 | 5 | 0 | 10 | +451.12 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 464.93 | 4 | 0 | 20 | +167.13 |
| E60_H300_C300 | 417.11 | 4 | 0 | 20 | +123.31 |
| E60_H900_C100 | 832.57 | 5 | 0 | 10 | +585.32 |
| E60_H900_C300 | 795.53 | 5 | 0 | 10 | +553.28 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 247.89 | 5 | 0 | 19 | +0.64 |
| E120_H300_C300 | 204.46 | 5 | 0 | 19 | -37.79 |
| E120_H900_C100 | 320.28 | 5 | 0 | 10 | +73.03 |
| E120_H900_C300 | 293.58 | 5 | 0 | 10 | +51.33 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 529.49 | 3 | 0 | 18 | +181.14 |
| E300_H300_C300 | 486.44 | 3 | 0 | 18 | +141.09 |
| E300_H900_C100 | 351.30 | 4 | 0 | 8 | +53.50 |
| E300_H900_C300 | 330.04 | 4 | 0 | 8 | +36.24 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
