# Provisional Paper Accounts

**PAPER ONLY — no real transactions.**

Started: 2026-09-23T15:27:21.742+00:00
Updated: 2026-09-23T16:25:13.471+00:00

PROVISIONAL PAPER ACCOUNTING, not executable fills or realized profit. Exact quoted token quantities are retained. Entry cash adds 1% or 3% plus 0.05 USDC; exit cash subtracts the same scenario percentage plus 0.05 USDC. These are extra cost stresses, not measured slippage or additional AMM fees. No transaction, latency-fill, market-impact, full-route or token-extension execution validation. Alternatives share observations; never sum their P&L. Open positions have unknown liquidation value; book equity holds them at cost. Failed exits retain locked capital and position slots. Quality checks never retroactively remove trades. Model times are quote receipt times; bookkeeping may occur later. No earlier quote records are backfilled into this pilot.

Primary predeclared account: **E60_H900_C100** (60-second entry, 15-minute horizon, 1% extra cost per side).
Each row is a separate $500 account, not a slice of one portfolio. No profit-based model selection.

| Account | Cash USDC | Open | Unresolved | Closed | Closed modeled net P&L USDC |
|---|---:|---:|---:|---:|---:|
| E30_H300_C100 | 303.20 | 1 | 0 | 24 | -146.25 |
| E30_H300_C300 | 256.62 | 1 | 0 | 24 | -191.83 |
| E30_H900_C100 | 942.45 | 4 | 0 | 11 | +644.65 |
| E30_H900_C300 | 903.18 | 4 | 0 | 11 | +609.38 |
| E30_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E30_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E60_H300_C100 | 479.17 | 2 | 0 | 23 | +80.27 |
| E60_H300_C300 | 429.03 | 2 | 0 | 23 | +32.13 |
| E60_H900_C100 | 1040.01 | 4 | 0 | 11 | +742.21 |
| E60_H900_C300 | 998.77 | 4 | 0 | 11 | +704.97 |
| E60_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E60_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E120_H300_C100 | 231.12 | 4 | 0 | 21 | -66.68 |
| E120_H300_C300 | 186.00 | 4 | 0 | 21 | -107.80 |
| E120_H900_C100 | 532.12 | 4 | 0 | 11 | +234.32 |
| E120_H900_C300 | 501.14 | 4 | 0 | 11 | +207.34 |
| E120_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E120_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |
| E300_H300_C100 | 380.44 | 5 | 0 | 19 | +133.19 |
| E300_H300_C300 | 334.33 | 5 | 0 | 19 | +92.08 |
| E300_H900_C100 | 273.64 | 5 | 0 | 10 | +26.39 |
| E300_H900_C300 | 247.88 | 5 | 0 | 10 | +5.63 |
| E300_H3600_C100 | 247.25 | 5 | 0 | 0 | +0.00 |
| E300_H3600_C300 | 242.25 | 5 | 0 | 0 | +0.00 |

Open holdings are not marked as profits. Liquidation equity and market drawdown remain unknown while unmeasured.
Missing exits are not deleted from the denominator: see open and unresolved counts alongside closed-only statistics.
The authoritative ledger is accounts.sqlite3. ledger.csv is a rebuildable export with source quote hashes.
Collector research observations are never rewritten by this paper layer.
