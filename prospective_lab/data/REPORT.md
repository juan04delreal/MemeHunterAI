# Prospective Quote Lab

**WATCH ONLY — no trades.**

Updated: 2026-09-23T11:42:47.296+00:00
Collector: prospective-quote-lab-0.4
RPC connected: True
Evidence-confirmed unique migrations: 63
Observed entry quotes: 12
Observed exit quotes: 36
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
| 81n3gLm6AP2UrVTZfhiJjyKnS7JrnaK6bVp3MMYApump | 2026-09-23T11:42:28.327+00:00 | 13.327080011367798 | none |
| 72eaAsF9PjfhvtEKuGi8UZvx2XWs9WARaaf5jRyapump | 2026-09-23T06:04:13.740+00:00 | 4.7400062084198 | 30:quote_observed, 60:quote_observed, 120:quote_observed, 300:quote_observed |
| BczEAPL4GmQZe3fYN53bWBXf1bm3wxQGFcdqdyMQpump | 2026-09-23T05:39:51.982+00:00 | 1.9827744960784912 | 30:quote_observed, 60:quote_observed, 120:quote_observed, 300:quote_observed |
| 8N43KnV3kXsQfaRgkLS7regB4CxrdN67EF96nEE8pump | 2026-09-23T03:35:25.792+00:00 | 5.792809963226318 | 30:quote_observed, 60:quote_observed, 120:quote_observed, 300:quote_observed |
| 3XYdRZ1Y2iEaXspZqiWb4LxQwy1F9bMZPER7QStxpump | 2026-09-22T18:41:20+00:00 | 5.154616355895996 | 30:not_configured, 60:not_configured, 120:not_configured, 300:not_configured |
| 7HLmsdfVcQdCtK7pHK4iu4Gr2aqYTsBhcA3eiueipump | 2026-09-22T18:01:04+00:00 | 3.0555779933929443 | 30:not_configured, 60:not_configured, 120:not_configured, 300:not_configured |

## Evidence and coverage audit

Historical instruction matches and their raw quotes are retained, not automatically validated.
Completion events, pool-creation instructions, and zero-to-positive pool funding are required for new samples. Prefunded or missing-evidence cases remain unresolved.
Re-audits and initial historical catch-up never create backfilled quote experiments.
Migration classifications: {"confirmed_new_migration": 63, "unresolved_no_new_migration_evidence": 22}
Discovery source: migration_authority_index; pending transactions: 0; catch-up: False
Out-of-scope or unrecognized migrate_v2 transactions: 3
Pool snapshot checks: {}
Pool-state corroboration does not validate full route fees, execution, or hypothetical market impact.
Old quotes without simultaneous pool snapshots cannot be retroactively given that evidence.
