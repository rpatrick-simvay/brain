# Closeout — Identity Push/Pull built, tested, and LIVE (2026-08-12 ~02:25Z; v1.1 published ~02:15 local Aug 11 EDT / see below)

Built autonomously per Ryan's authorization ("build and test without me"). Everything below is verified live, not assumed.

## What is running now

**Workflow `Identity Push/Pull`** (n8n id 2trEaeHEqTCkL4jhzBJ1d, published **"Version 1.1"** — 25 nodes, md5 54f01cbef57d88e52bc1c3b625cd68db, copy at /root/identity_flow.json on SIMSRV-PVE2), six branches:

| Branch | Cadence | Pull | Push |
|---|---|---|---|
| Entra success (A+B) | 60s | POST /sentinelone/datalake/queryall, 12h lookback, 29-col set, `enrich=true&enrich_fields=src_endpoint.ip&device.ip` (inline URL — n8n collapses duplicate queryParameters names; reviewer catch B1) | batches of 200 → :9001 |
| **Entra failed (stream C) — NEW v1.1** | 60s (same Entra Schedule, fanout) | POST queryall, `unmapped.Operation='UserLoginFailed'`, 12h, James's captured column set, `enrich_fields=unmapped.ActorIpAddress&unmapped.ClientIP` (James's enum additions, verified live) | batches → :9001 (same dedup_microsoft [metadata.uid]) |
| Duo | 5 min | GET /duo/authlogs, **2h window (widened in v1.1** — Duo can't 24h-sweep under limit=1000, so the rolling window is the catch-all**)**, limit=1000, both enrich_fields inline | batches → :9002 |
| Action1 logins | 10 min | GET /action1/audit/events/loginips, 24h window (already self-sweeping) | batch → :9004 |
| Duo directory | daily 03:15 | GET /duo/users → static-data duoDirectory (key→email; survived the re-import) | joined in Duo Normalise |
| **Deep Sweep — NEW v1.1** | daily 03:45 | 24h Entra success sweep + 24h Entra failed sweep (own Pull/Normalise/Push nodes, fanout from one cron) | :9001; dedup absorbs the overlap |

Envelope + guards unchanged from v1.0 (see below). v1.1 C-stream additions to the Entra normaliser: client_ip coalesce extended `src_endpoint.ip → device.ip → ActorIpAddress → ClientIP` (enriched objects handled via pickIp), auth_result fallback from `unmapped.ResultStatus`, result_detail from `LogonError`, error_code from `ErrorNumber`, user_uid fallback from `UserKey`. record_type mapping: UserLoggedIn→entra_login_success, UserLoginFailed→entra_login_failed, SignInEvent→entra_signin, else entra_other.

**Vector** (backup `/root/vector.yaml.bak-20260812-preidentity` on LXC 101): `dedup_microsoft` → match `[metadata.uid]`, cache 50,000; `action1_ingest :9004 → dedup_action1 [id] 10k → vlogs_action1` (VL sink `_msg=event, _time=event_time, _stream_fields=record_type`, 256MB disk buffer). No Vector changes needed for v1.1 (failed stream rides :9001).

**Retired:** Duo Push/Pull (unpublished), Action1 Push/Pull login branch (stats-only), SentinelOne Push/Pull Entra branch + James's draft failed-logins branch (inventory-only).

## Verification results (live)

### v1.1 (2026-08-12, this session)
- Behavioral suite: 39 original + 9 new C-stream assertions, all pass pre-transfer; md5 verified end-to-end through the browser-accumulator transfer (62924 b64 → 47191 bytes → 54f01cbef57d88e52bc1c3b625cd68db).
- Import gotcha: on n8n 2.6.x, **Import from URL APPENDS to the canvas** (nodes got "1" suffixes next to the v1.0 set) — fixed by Ctrl+A → Delete → re-import into the empty canvas. Static duoDirectory survived.
- Test executions green: Entra Schedule fanout → success 904 items→5 batches, failed 225 items→2 batches; Deep Sweep → success sweep 941→5, failed sweep ~344→2.
- VictoriaLogs after settle: `entra_login_failed` rows=215 uniq=215 (rows==uniq, sweep/pull overlap fully dedup'd), **client_geo on 215/215**; `entra_login_success` rows=809 uniq=809; duo_auth 265, action1_login 31, entra_signin 35.
- Sample failed row: amazzaro@simvay.com, 184.56.48.244 → United States / Charter Communications, error_code 50074, result_detail UserStrongAuthClientAuthNRequiredInterrupt.
- **Nuance:** MFA-interrupt failures (50074/50076) carry `ResultStatus=Succeeded` upstream, so `auth_result` can read `success` on entra_login_failed rows (first factor succeeded, MFA interrupted). Faithful to the raw data — detection rules should filter on `record_type:entra_login_failed` + `error_code`, not auth_result alone.

### v1.0 (retained for record)
- All 4 branches test-executed green before publish: Duo 275→2 batched POSTs w/ directory-joined emails (bare `bkrosse` → `bkrosse@avonlake.org`); Action1 31/31 rows+geo; Entra 935→5 POSTs with stored uids dedup-dropped.
- Post-cutover soak: duo_auth climbing per run; entra rows=uniq with 100% client_geo_isp; scheduled executions Success every 60s.
- 39-assertion QA suite + adversarial agent review (1 blocker + 4 serious, all fixed) before deploy.

## Incidents during the build (all resolved)

1. **DEV-N8N VM (qemu 946) frozen Aug 11 ~20:15 local** (metrics flatlined, scheduler dead, UI alive). Rebooted per Ryan → schedules resumed, Entra backfilled. Cause unknown — VM logs worth a look.
2. Container console transfer dropped keystrokes on >3KB pastes → browser-fetch upload via temp receiver on the PVE2 node (receiver killed after both transfers; /root/identity_flow.json retained as the deployed-JSON copy).

## James's stream-C query (captured, now absorbed into v1.1)

filter `dataSource.vendor='Microsoft' dataSource.category='security' unmapped.Operation='UserLoginFailed'`, columns: metadata.uid, metadata.original_time, type_name, actor.user.email_addr, actor.user.uid, unmapped.UserKey, unmapped.ActorIpAddress, unmapped.ClientIP, unmapped.LogonError, unmapped.ErrorNumber, unmapped.ResultStatus, unmapped.DeviceProperties, unmapped.ExtendedProperties, unmapped.ApplicationId, unmapped.Operation, unmapped.RecordType, cloud.org.uid. Deployed verbatim in v1.1 (12h rolling + 24h sweep variants), riding his SentinelOneIpField enum additions.

## Follow-ups (in order)

1. **24h gate (check 10):** `metadata.product.vendor_name:Microsoft _time:24h | stats count() rows, count_uniq("metadata.uid") uniq` — rows≈uniq and advancing → phase 1 holds. Now also confirms no uid collision between success and failed streams (both dedup on the same key at :9001; operations are disjoint so collisions shouldn't occur — a rows<uniq-sum anomaly would surface here).
2. First Deep Sweep fires 03:45 local — confirm one clean run (rows==uniq must hold after it).
3. Duo email coverage after a day: `record_type:duo_auth user_email:* | stats count()` vs total — expect ~97%.
4. Step 4: watermarks (cuts the Entra 12h re-pull to ~30/run; failed branch would benefit equally).
5. E1: n8n Error Workflow → PagerDuty/Alerting for Identity Push/Pull.
6. Confirm with James: no timestamp-frame surprises on Action1 event_time; tell him Vector path is permanent and his draft was absorbed (columns deployed verbatim in v1.1).
7. Verify no residual Duo feed (rows without ingested_at_unix at :9002 would indicate another feeder).
8. Detection rules on the new envelope — deferred per Ryan. Failed-login data now flowing: spray sources (e.g. 105.79.99.226 Morocco/Wana), hosting-IP logins, proxy'd MFA approvals, impossible travel all writeable.
