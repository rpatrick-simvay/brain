# Status — identity pipeline revision drafted; build moves to an on-computer session (2026-08-11)

Cloud Cowork session. **Nothing was changed** — the lab (10.10.x.x) is unreachable from the cloud sandbox, so all measurement ran through the browser against VictoriaLogs. n8n could not be inspected (session expired; browser-JS REST calls are blocked by the extension). Ryan decided: restart the task on his computer for the build, full identity-pipeline scope, and we take over the Vector-side work formerly earmarked for James.

## What this session produced

`claude/spec-2026-08-11-identity-dedup-revision.md` — the revised strategy, superseding the dedup sections of the 7/31 spec and handoff. Headlines:

1. **n8n Remove Duplicates is withdrawn everywhere** (commit-on-run defect proven in the 8/1 PagerDuty work). Vector owns all dedup.
2. **Identity dedup keys are ID-only** (`txid`, `metadata.uid`) — identity events are immutable facts, deliberately NOT the PagerDuty content-hash pattern. Panels therefore need no `stats by (id)` reduction, but must use `count_uniq()` not `count()`.
3. **New defect found: `dedup_microsoft` keys on a content triple** `(original_time, device.ip.query, email)` — collapses legitimate same-second sign-ins, and degenerates on `UserLoginFailed` records (no `device.ip`), which would silently under-count spray bursts. Key change is hard-ordered before the failed-login branch.
4. Batching to arrays of 200 (Entra's ~790 single POSTs/min is the 8/1 crash shape as a steady drip), watermark advanced only after POST success, Duo re-routed through Vector :9002.
5. 6-phase build plan with gates; 14 verification/risk items; 16 acceptance checks with 8/11 baselines.

## Fresh baseline (VL, 24h, 2026-08-11)

- Duo: **7,284 events, zero dupes** — volume recovered from 3,098. **Nobody documented this fix** — confirm who changed limit/cadence (James?) before touching Duo.
- Entra: all 7/31 gaps still open — `src_endpoint.ip` 0, `is_compliant` 0, `LogonError` 0, booleans still 4 variants, 1,602 rows = 1,602 unique uids.
- Microsoft-ISP false positives ~62/day (was ~40).
- Duo email 13%, auth_device geo 9% — the limit fix did NOT fix geo coverage (recovered events were disproportionately un-enriched), so that's a real API-side question.
- Confirmed: `_msg`/`_time` consume `type_name`/`original_time` on the Microsoft stream — the "parser drops fields" ask to James is withdrawn.

## For the next (on-computer) session — start here

1. Read `claude/spec-2026-08-11-identity-dedup-revision.md` in full.
2. **Ryan has NOT yet approved the plan.** Present the phase table (§6) for approval before changing anything.
3. Run phase 0 (read-only verification, ~30 min): items #1–#4 in spec §8 — the Vector payload-shape probe on a scratch port (BLOCKER, catastrophic quiet failure if wrong), Duo POST target read from the n8n node, Duo limit/cadence change attribution via execution history, live `vector.yaml` read of current `dedup_microsoft`.
4. Then build phases 1–6 in order, honoring the gates. n8n gotcha: every REST edit needs an explicit publish (orange dot).
5. Environment refs: n8n `10.10.99.13:5678`, Simvay API `10.10.100.8:8000`, VL `10.10.100.12:9428`, Vector LXC 101 on SIMSRV-PVE2 `10.10.100.13` (:9001 MS, :9002 Duo, :9003 PD), config `/etc/vector/vector.yaml`, backups in `/root/`.
