# Early-wallet live research watchlist

**WATCH ONLY. No trading, no private keys, no verified profitable-copy list.**

Last observation (UTC): `2026-09-19T11:46:18+00:00`

Status: **DEGRADED** | Completed observation cycles: 1
Configured seed coins: 13 | Wallet leads: 6
RPC: unavailable_or_partial | Pending transaction decodes: 3

Refresh this page. Data is checkpointed about every 5 minutes; the collector targets 60-second cycles.
The hourly supervisor renews bounded GitHub jobs. Runner/provider delays and restarts can cause gaps.

## Market snapshots (not executable quotes)

| Mint | Symbol | Observed price | Pool liquidity |
|---|---|---:|---:|
| `AyYNfPtftg2zDP4ZbgcoQMggQtwLh4zpfVVmUJs2thto` | Tilcayo | $0.002017 | $172,871.42 |
| `91ryaCo5yGpYZM3bs6GUPs97VWJQj7RozBmqPULgpump` | TIGRINO | $0.002838 | $188,001.67 |
| `DDVUsN8sDFxbaX6gNBoD44kjZhFETWJnwAn4EX1dpump` | BABYCATE | $0.002583 | $170,804.25 |
| `DnJeAP7hWjVNTTk1NUaDJ5Aps9qDroSsEMcKBCpSTNK` | PSA10 | $0.000562 | $69,623.73 |
| `HgcxVs6kJhPAaGqnPNGaa7zYgNT49hJrLufiqcNMuYZT` | FEELSGOOD | $0.004306 | $77,142.20 |
| `4tkupXEGfbYPCVN37CagviJd3tgWnudT9avKZvouT3Dm` | HEV | $0.003885 | $284,080.20 |
| `DFQHUegJWE29Xu3BUxPezqi77uyHURRyxJpdtyvLpump` | PUMPCAT | $0.000118 | $29,517.85 |
| `JAzfwUUbThYJNpDhaezwZquKog4Q6CRFELJQrfLMpump` | Canary | unavailable | unavailable |
| `6AUURRdHb9TrfPHv9AMofa8NEVoZDXcsbWKcUBpFSRXs` | CYPHERCAT | $0.001465 | $122,672.60 |
| `fvHLJUwsynVHJrssbZ8MLNyku9jt2izUspbBD4Spump` | FLEX | $0.000556 | $68,501.98 |
| `GJSfEpiK9RnmRt9AnZi3FL1b2K6AApcW1SzTs2FeHGis` | BRRR | $0.002667 | $145,242.80 |
| `98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump` | PAID | $0.024100 | $803,399.61 |
| `GY9mZfyPpxXxBXBxS2hB2XjhP3kfUsywTvgveozxpump` | ELON | $0.002034 | $181,194.60 |

## Wallet leads (unverified)

| Wallet | Role | Last successful address scan (UTC) |
|---|---|---|
| `kEFiAX3jo5NmemysQov342TZ9mGh6yp92GDRjhA8XDf` | unverified-overlap-lead | 2026-09-19T11:46:14+00:00 |
| `ftH8JtoAvBp5cxpGtMaoBKZDiGLRWBAXEwz3XyvsrwE` | unverified-overlap-lead | 2026-09-19T11:46:14+00:00 |
| `6a7tbRtWETeGrzWmLTUFkRAMQ2p9HxN4xCaSinRYnFXZ` | unverified-overlap-lead | 2026-09-19T11:46:15+00:00 |
| `cGxeYN6F7T9aELwjLPeL3hnJNscGU7EHg5CEsP4B3Hz` | historical-research-lead | 2026-09-19T11:46:15+00:00 |
| `P5tb4T6SBVQaM3BAoGfpVudLtTdecqjsh4KV9ESAhKg` | historical-research-lead | 2026-09-19T11:46:15+00:00 |
| `EKHARkLX6afkEkZvY8MBaMBzUKEwk6NWrDsA8pxHQ6TU` | reported-ELON-creator-risk-reference | 2026-09-19T11:46:16+00:00 |

## Cross-token observations since this collector started

These are sampled, instruction-supported **buy candidates**, not verified early buys or independent wallets.

| Wallet | Distinct supplied mints with observed buy candidates |
|---|---:|
| None recorded yet | 0 |

## Data-quality limits

- Initial wallet scans establish a forward baseline; they do not reconstruct earlier buys.
- Wallet-address signatures are monitored; unsolicited SPL transfers can be missed when the owner is not referenced.
- Pool discovery samples two rotating selected pools per cycle; it is not a complete buyer list or launch-rank study.
- Unknown programs, transfers, allocations, and complex transactions are not promoted to verified buys.
- Pool creation time is NOT token creation time. Early-entry flags and profit are intentionally unset.
- A mark is not an exit quote. No simulated fills or P&L are invented.
- RPC errors and pagination gaps are retained in the event logs. A running job alone is not proof of a healthy wallet feed.

## Latest observed events

- `2026-09-19T11:46:18+00:00` sell_candidate `6R5ArXAGWvWME3aycD8vGehmqWhFEpDUaiY9xtMAnyCB` / `AyYNfPtftg2zDP4ZbgcoQMggQtwLh4zpfVVmUJs2thto` / tx `3HTEuyGyux2yJ7yGeUqAApr1JgrTzit5gPWAZSy1C6K3QZWZFjHcHW1aa3SkK1wbcADfMMkmEsAmvK7HnszfU3M4`

## Latest feed errors

- wallet RPC: RPC error -32015

## Stop and results

Set `watchlist/control.json` to `{"enabled": false}` on this branch. The current job checks the stop switch each cycle.
The hourly supervisor must also be disabled when stopping. Existing data is retained.
Read `watchlist/data/latest.json`, `state.json`, and the dated JSONL event files for analysis.
