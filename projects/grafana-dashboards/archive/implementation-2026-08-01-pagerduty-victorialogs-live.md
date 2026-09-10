# PagerDuty → VictoriaLogs ingest: implementation and QA record

**Date:** 2026-08-01
**Status:** Live. Workflow `PagerDuty Incidents Push/Pull` (n8n id `pr51pfrwucOZta1X`) is published and running on a 15-minute schedule. 90-day backfill complete. All QA gates passed.
**Supersedes the "open decision" sections of** `claude/spec-2026-07-31-n8n-pagerduty-ingest.md` and `claude/change-request-2026-08-01-vector-pagerduty-ingest.md`.

## What is live

```
Simvay API /pagerduty/incidents/raw
  → n8n "PagerDuty Incidents Push/Pull"  (15 min rolling 48h + daily 14-day sweep)
      Normalise + Stamp  →  Batch for Vector  →  POST 10.10.100.13:9003
  → TEMP-Vector  pagerduty_ingest → dedup_pagerduty → vlogs_pagerduty
  → VictoriaLogs 10.10.100.12:9428, stream query_type="PagerDutyIncidents"
```

VictoriaLogs currently holds 3,871 unique incidents spanning 2026-05-03 to 2026-07-31, across services SentinelOne (3,460), Auvik (395) and Cyber Infra (16).

## The two infrastructure faults found during testing

Both were pre-existing and neither was specific to PagerDuty. Finding them is the single most valuable outcome of this work.

### TEMP-Vector had a 1,024 file-descriptor limit and no override

The first backfill attempt pushed one HTTP POST per record. 1,244 records in six seconds exhausted Vector's file descriptors and the process died with `hyper::Error(Accept, IncomingListener { source: Os { code: 24, message: "Too many open files" } })`, taking the whole topology down. systemd restarted it, and the same thing happened on each of the three backfill chunks — three crashes in three minutes.

`vector.service` carried no `LimitNOFILE`, so it inherited the 1,024 default while the hard limit was 524,288. **This was latent in the environment before any of this work.** Any burst against port 9001 or 9002 — a Microsoft branch catch-up after an outage, a Duo backfill — would have killed Duo and Microsoft ingestion the same way, and the only evidence would have been a gap in VictoriaLogs.

Fixed with `/etc/systemd/system/vector.service.d/override.conf`:

```ini
[Service]
LimitNOFILE=65535
```

Verified after restart: `Max open files 65535 / 65535`.

### The PagerDuty sink had no disk buffer

Vector's `http_server` returns 200 as soon as it parses the body, so n8n saw success for every one of the 1,244 records that were subsequently lost when the process died. With the default in-memory buffer, anything queued at crash time is gone silently. `vlogs_pagerduty` now has:

```yaml
    buffer:
      type: disk
      max_size: 268435488
      when_full: block
```

**Updated 2026-08-01 17:28Z — all three sinks now have disk buffers.** The same block was applied to `vlogs` and `vlogs_duo` at Ryan's request and the config reloaded via SIGHUP with no restart. Vector created `/var/lib/vector/buffer/v2/{vlogs,vlogs_duo,vlogs_pagerduty}` and all three sinks came up clean. Worst-case disk use is 768 MB across the three against 3.7 GB free on `/`, so the ceiling is comfortable but worth watching if retention or volume grows. Backup of the pre-buffer config is at `/root/vector.yaml.bak-20260801-prebuffers`.

The practical effect: if VictoriaLogs is unreachable, all three streams now queue to disk and block rather than silently discarding in memory, and a Vector restart no longer loses whatever was in flight. That is the failure mode that cost 234 records during the first backfill attempt.

## Design changes made after the adversarial review

An independent QA agent reviewed the workflow before any of it ran and found four issues that would have produced wrong-but-plausible numbers. All four are fixed, and one of them was the highest-value catch of the exercise.

**Reduction cannot order on `_time`.** The original design said panels would reduce with `stats by (id) last(...)` ordered on `ingested_at`. That does not work: LogsQL's `last()` orders by `_time`, and every revision of an incident carries the same `_time` because `_time` is the incident's `created_at`. The reduction would have been non-deterministic — the same panel returning different numbers on consecutive refreshes. Records now carry `ingested_at_unix` (epoch milliseconds, numeric) and the verified reduction pattern is in the section below.

**The n8n dedup node was removed entirely.** `removeItemsSeenInPreviousExecutions` commits its keys when the node runs, not when the workflow succeeds. A POST failing partway through a batch would have marked every remaining record as "seen", and because those incidents are already resolved and settled, PagerDuty would never bump `updated_at` again — they would have been permanently absent with no error anywhere. Vector now owns deduplication exclusively, which also matches what Duo and Microsoft do. A failed run is now self-healing: the next run re-pulls the same window and re-sends.

**Dedup keys on a content hash, not `updated_at`.** Nothing guarantees PagerDuty bumps `updated_at` when only a derived metric such as `seconds_to_first_ack` settles. Each record now carries `payload_hash`, an FNV-1a over the fields whose change should produce a new row, and `dedup_pagerduty` matches on `[id, payload_hash]`.

**Null numerics are deleted rather than emitted.** 62% of incidents are never acknowledged. If `seconds_to_first_ack: null` had been written and VictoriaLogs treated nulls as zero, July's mean ack would have read ~169 instead of 404 — entirely plausible on a wallboard, and wrong. The Code node deletes null numerics outright, so `avg()` only ever sees real values. Verified: `avg(seconds_to_first_ack)` with no filter returns 403.79 over a denominator of 38 for 2026-07-30, not 82.

Also fixed: `triage_seconds` now requires both terms to be finite numbers and the result to be non-negative, instead of letting JavaScript coerce a null to zero and emit a negative duration; `acknowledged` is a strict `typeof === 'number'` test; and the workflow throws rather than proceeding if a record arrives without `id` or `created_at`.

## The batching change

One POST per record is what killed Vector. Vector's `http_server` with `encoding: json` splits a JSON array into one event per element — verified live with a two-element probe that produced two rows with numeric types intact — so the workflow now groups records into arrays of 200. A 1,244-record backfill went from 1,244 connections to 7. Normal 15-minute runs are a single POST.

## How panels must query this data

**This is the most important section for the dashboard work.** VictoriaLogs holds one row per revision, not one row per incident. Aggregating raw rows weights each incident by how many times it happened to be re-ingested. Right now the store has 6,904 rows for 3,871 incidents because Vector's dedup cache is in-memory and was cleared by the restarts.

Every aggregate must reduce by `id` first. The verified pattern is two-stage:

```logsql
query_type:PagerDutyIncidents service_name:SentinelOne acknowledged:true
| stats by (id) max(seconds_to_first_ack) as ack
| stats avg(ack) as mtta
```

Counting is safe with `count_uniq(id)`; `count()` is not.

`max()` per incident is correct for these fields because they are write-once-then-stable — a null becomes a number as the metric settles and never reverts, and `seconds_to_resolve` does not change once the incident is resolved. For a field that can genuinely change value, such as `urgency`, `max()` is not "latest" and the reduction needs `ingested_at_unix`. `row_max()` returns an empty object on this VictoriaLogs version and cannot be used.

Two further notes. `description` and `isotimestamp` are consumed by the sink — query `_msg` and `_time` instead; `created_at` survives as a normal queryable field. And the `service_ids` filter is not airtight over long windows: 16 incidents from a third service (`P0RL2B5`, Cyber Infra) arrived despite only `PG0FTPW` and `PEVYNFV` being requested. Panels must filter on `service_id` or `service_name` explicitly rather than trusting the ingest scope.

## QA results

All four gates from the agreed plan, plus the adversarial review.

| Gate | Result |
| --- | --- |
| Dry run on a scratch stream | 47 records landed under `PagerDutyIncidentsTEST` with correct stream labels across SentinelOne and Auvik, high and low |
| Timestamps not shifted | `_time` range landed at incident time, not ingest time; `isotimestamp` correctly consumed (returns 0 rows) |
| Types preserved | `avg()` and `sum()` work directly; no `convertFieldType` needed anywhere |
| Nulls not coerced | `avg(seconds_to_first_ack)` unfiltered returns 403.79 over denominator 38, not a diluted 169 |
| Second-run dedup | 47 records re-pushed in full, VictoriaLogs still held exactly 47 rows and 47 ids |
| Adversarial config review | 14 findings; 4 blockers and 5 serious, all fixed or accepted with mitigation |

The accuracy gate, reconciled against API ground truth pulled independently:

| Measure | API | VictoriaLogs (reduced) |
| --- | --- | --- |
| July incidents | 1,116 | 1,116 |
| July high urgency | 287 | 287 |
| July acknowledged | 467 | 467 |
| July mean seconds to first ack | 403.79 | 403.7944325481799 |
| July mean seconds to resolve | 1,063.46 | 1,063.4596774193549 |
| July business hour interruptions | 913 | 913 |
| 2026-07-30 incidents | 82 | 82 |
| 2026-07-30 mean seconds to resolve | 2,634.37 | 2,634.3658536585367 |
| 2026-07-30 total triage seconds | 16,185 | 16,185 |

## What this still does not fix

The four-hour timestamp offset in the Simvay API is unchanged and still needs James. It affects `window` on the metrics route and `rolling_hours` on the raw route; the ingest works around it with a 48-hour window and a daily 14-day sweep, so nothing is lost, but any panel written against stored metrics-route values inherits it.

PagerDuty Analytics only exposes incidents after they resolve and settle, and settling takes hours. Nothing on the wallboard that needs to be live — open incidents, in-triage counts, time since last alert — can come from this feed. Those stay on the SentinelOne VictoriaMetrics series or move to PagerDuty's REST API.

Two test artifacts remain in VictoriaLogs and will age out with retention: `query_type:PagerDutyIncidentsTEST` (47 rows) and `query_type:PagerDutyArrayTest` (2 rows). Both are in their own streams and cannot contaminate `PagerDutyIncidents` queries.

## Post-change health check (2026-08-01 17:31Z)

All three collectors verified healthy after the buffer change.

| Stream | Evidence |
| --- | --- |
| PagerDuty | Five consecutive scheduled runs at 16:15, 16:30, 16:45, 17:00, 17:15 UTC, all success, 1.2–1.6 s each. 1,261 incidents in the rolling window, last ingest 17:15:50Z |
| Duo | Count climbing live (100,804 → 100,828 over two minutes), newest event 17:27:43Z |
| Microsoft | `SentinelOne Push/Pull` running every 60 s, all success; the 17:31:46Z execution pulled and pushed 313 records to Vector |

One thing that looks alarming and is not: the Microsoft record count in VictoriaLogs has been flat at 63,606 since 15:21Z. That is `dedup_microsoft` working correctly. The Entra branch re-fetches a 12-hour lookback every 60 seconds, so it pushes the same ~313 rows repeatedly and Vector drops them all as duplicates. The count only advances when a genuinely new Entra sign-in appears, and none has since 15:21Z on a Saturday afternoon. The taper that precedes it — 265 records in the 12:00 hour, 222 at 13:00, 38 at 14:00, 6 at 15:00 — began roughly two hours before the first Vector crash, so it is upstream quiet plus the S1 datalake's own ingestion lag, not fallout from this work. Worth a glance on Monday morning to confirm volume returns.

## Rollback

`cp /root/vector.yaml.bak-20260801 /etc/vector/vector.yaml && systemctl reload vector` reverts the Vector config to its pre-change state. Removing `/etc/systemd/system/vector.service.d/override.conf` reverts the FD limit, though there is no good reason to. Unpublishing the n8n workflow stops ingestion; nothing else depends on it yet.
