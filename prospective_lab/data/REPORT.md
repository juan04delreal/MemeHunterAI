# Prospective Quote Lab

**WATCH ONLY — no trades.**

Updated: 2026-09-23T11:52:18.450+00:00
Collector: prospective-quote-lab-0.4
RPC connected: True
Evidence-confirmed unique migrations: 68
Observed entry quotes: 29
Observed exit quotes: 39
Quote failures/unavailable: 8
Missed deadlines (no backfill): 0
Jupiter API key configured: False
Quote access mode: keyless
Provider connection test: healthy

Connection-test SOL/USDC quotes are separate from migration samples and never imply profit.
Existing failed observations are retained. Expired deadlines are never backfilled.
New exit horizons start when the entry quote was received; actual request/receipt times are retained.
Quotes are route snapshots, not fills. Network fees, execution slippage, and realized profit are not established.
Bounded migration-authority cursor and retry queue; SOL-paired migrate and migrate_v2 only; non-SOL pairs excluded. Independent total-market coverage is not established.

## Recent opportunities

| Mint | First observed | Lag from chain | Entry quote states |
|---|---|---:|---|
| 4UnHwE52BPboFQaqSzbNx8yJ4UeiubcQSgWZbtGFpump | 2026-09-23T11:51:18.943+00:00 | 2.943943977355957 | 30:quote_observed |
| D6FbvxB8PtC14ECK3tFUNtshSzEzivw3pcbuemKgpump | 2026-09-23T11:49:54.271+00:00 | 20.27192521095276 | 30:quote_observed, 60:quote_observed, 120:quote_observed |
| Dbw7VFWGdy1VAXsGkADePQfHiP8tpQ2KgtQM34iRpump | 2026-09-23T11:49:53.267+00:00 | 13.267284393310547 | 30:quote_observed, 60:quote_observed, 120:quote_observed |
| 6bpwdv8EbvW1C7rKvimsQr6omxTQYqQ8VqPsrTqmBJUL | 2026-09-23T11:48:28.398+00:00 | 17.39808988571167 | 30:quote_observed, 60:quote_observed, 120:quote_observed |
| dt7wprKecLM6u4cC3Wat1bLtd4H4KDrroMYiKpWpump | 2026-09-23T11:48:27.895+00:00 | 3.8956351280212402 | 30:quote_observed, 60:quote_observed, 120:quote_observed |
| 81n3gLm6AP2UrVTZfhiJjyKnS7JrnaK6bVp3MMYApump | 2026-09-23T11:42:28.327+00:00 | 13.327080011367798 | 30:quote_observed, 60:quote_observed, 120:quote_observed, 300:quote_observed |
| 72eaAsF9PjfhvtEKuGi8UZvx2XWs9WARaaf5jRyapump | 2026-09-23T06:04:13.740+00:00 | 4.7400062084198 | 30:quote_observed, 60:quote_observed, 120:quote_observed, 300:quote_observed |
| BczEAPL4GmQZe3fYN53bWBXf1bm3wxQGFcdqdyMQpump | 2026-09-23T05:39:51.982+00:00 | 1.9827744960784912 | 30:quote_observed, 60:quote_observed, 120:quote_observed, 300:quote_observed |
| 8N43KnV3kXsQfaRgkLS7regB4CxrdN67EF96nEE8pump | 2026-09-23T03:35:25.792+00:00 | 5.792809963226318 | 30:quote_observed, 60:quote_observed, 120:quote_observed, 300:quote_observed |
| 3XYdRZ1Y2iEaXspZqiWb4LxQwy1F9bMZPER7QStxpump | 2026-09-22T18:41:20+00:00 | 5.154616355895996 | 30:not_configured, 60:not_configured, 120:not_configured, 300:not_configured |
| 7HLmsdfVcQdCtK7pHK4iu4Gr2aqYTsBhcA3eiueipump | 2026-09-22T18:01:04+00:00 | 3.0555779933929443 | 30:not_configured, 60:not_configured, 120:not_configured, 300:not_configured |

## Evidence and coverage audit

Historical instruction matches and their raw quotes are retained, not automatically validated.
Completion events, pool-creation instructions, and zero-to-positive pool funding are required for new samples. Prefunded or missing-evidence cases remain unresolved.
Re-audits and initial historical catch-up never create backfilled quote experiments.
Migration classifications: {"confirmed_new_migration": 68, "unresolved_no_new_migration_evidence": 24}
Discovery source: migration_authority_index; pending transactions: 0; catch-up: False
Out-of-scope or unrecognized migrate_v2 transactions: 3
Pool snapshot checks: {"requires_review": 15, "unrecognized_or_inconsistent_pool_evidence": 5}
Pool-state corroboration does not validate full route fees, execution, or hypothetical market impact.
Old quotes without simultaneous pool snapshots cannot be retroactively given that evidence.
