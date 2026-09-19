# Early-wallet research collector

This is an isolated WATCH_ONLY experiment in `research/early-wallet-watchlist`.
It does not import or run MemeHunterAI's app, scanner, trader, or v11. Main is unchanged.
This branch and its public on-chain research data are PUBLIC, matching the existing repository.
There are no wallet keys, no order submission, no automatic buys, and no claimed profit.

## Included

All 13 mint addresses provided in the conversation (the latest 11 plus PAID and ELON), three unverified overlap leads, two historical leads, and one reported creator-associated risk reference. Prior profit claims and win rates are deliberately not imported as facts.

The collector targets a 60-second cycle and commits a phone-readable [report](data/REPORT.md), [latest status](data/latest.json), durable state, and dated JSONL evidence about every five minutes. The first checkpoint is immediate. New mints bought by watched wallets are added to market observation, up to 100 total; the limit is reported rather than silently dropping observations.

Each GitHub job is bounded to about 75 minutes. An explicitly scheduled hourly ChatGPT supervisor creates a new `pulse.json` commit when no replacement run is queued. A concurrency group prevents overlapping collectors. This is best-effort polling, not uninterrupted or subsecond infrastructure. If the supervisor stops, the current and queued bounded jobs eventually finish. Nothing here restarts itself forever without that scheduled supervisor.

## Evidence and coverage

Wallet monitoring follows address transaction signatures with persisted pagination and a bounded decode backlog. The first scan establishes a forward baseline, not a recovered historical entry. Transactions referring only to associated token accounts can be missed. Failed requests, unavailable transactions, queue limits, and missing historical cursors are logged.

Pool discovery is explicitly a sample: two rotating selected seed pools, three recent signatures each per cycle. This cannot establish all early buyers or launch rank. Pool creation is not token creation. Historical pool samples are labeled separately and excluded from the forward overlap count.

Only recognized Pump/PumpSwap buy/sell instruction discriminators, expected account roles, and matching owner balance direction produce a `buy_candidate` or `sell_candidate`. These still need transaction-level audit for complex transactions. Other inflows and outflows stay unclassified. Transfers, mint allocations, and liquidity deposits are not simply counted as buys. Shared addresses/holdings are not proof of common ownership or insider information.

Quotes, executable exits, independent demand, exact cost basis, realized profit, and profitable copying are NOT established by this collector. Do not use the resulting overlap table as a live trading recommendation.

## Providers and secrets

Market feed: public DEX Screener API. Read-only RPC: public PublicNode Solana endpoint by default. An existing repository secret named `SOLANA_RPC_URL` is used when present, without printing it or its URL. No paid provider is purchased and no new credential is required for the public-endpoint attempt. Provider blocking/rate limits can leave markets available but wallet coverage degraded; inspect `rpc_status`, not just the Actions green/running icon.

## Stop and review

On this branch, set `watchlist/control.json` to `{"enabled":false,"mode":"WATCH_ONLY"}`. The current job reads the remote switch each cycle; a queued job reads it before collecting. Disable the hourly supervisor too. Retain the recorded files. When the user asks for results, stop this experiment unless they explicitly ask to keep it running, then analyze the saved evidence and report gaps. Never modify v11 or main to do this.

The workflow uses standard Ubuntu public-repository runners, no artifact/cache uploads, and no billing-setting changes. It will not start for a private-repository event. GitHub/provider limits still apply; it is not an indefinite uptime guarantee.

## Local checks

`python3 -m unittest discover -s watchlist -p 'test_*.py' -v`

`python3 watchlist/collector.py --once` performs a bounded network observation and writes local data. It does not place trades.

## Primary references

- https://docs.dexscreener.com/api/reference
- https://solana.publicnode.com/
- https://solana.com/docs/rpc/http/getsignaturesforaddress
- https://solana.com/docs/rpc/http/gettransaction
- https://github.com/pump-fun/pump-public-docs/blob/main/docs/PUMP_PROGRAM_README.md
- https://github.com/pump-fun/pump-public-docs/blob/main/docs/PUMP_SWAP_README.md
- https://docs.github.com/en/actions/reference/limits
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
