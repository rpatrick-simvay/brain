# Spec — PagerDuty incidents into VictoriaLogs via n8n

**Date:** 2026-07-31
**Companion to:** `claude/review-2026-07-31-pagerduty-victorialogs-cutover.md`
**Artifact:** `pagerduty-incidents-push-pull.json` — importable n8n workflow, five nodes.

## The short answer

Yes. Copy `Duo Push/Pull`, not `SentinelOne Push/Pull` — the Duo workflow is already the shape this needs: a schedule trigger, one GET against the Simvay API, one POST downstream. Three nodes, no credentials, because the Simvay API holds the PagerDuty key.

**Revised 2026-08-01 after reading TEMP-VECTOR.** The original version of this doc said to post straight from n8n to VictoriaLogs and to avoid the "temporary parser" hop. Having now read the actual Vector config, that advice was half wrong — see the next section. The node shape below still stands; where the POST goes is now an open decision.

## The blocker in the handoff is already solved

James's handoff says the per-incident path "needs the VictoriaLogs insert URL from James." That URL is not unknown. It is `http://10.10.100.12:9428`, and two collectors have been writing to it for months. The work is not blocked on information.

## TEMP-VECTOR — what it actually is (read 2026-08-01)

Proxmox LXC 101 on node SIMSRV-PVE2, hostname `TEMP-Vector`, running Vector 0.55.0 from `/etc/vector/vector.yaml`. It is not a parser and it is not Microsoft-only. It is the ingestion front door for **both** identity streams, and its whole job is deduplication.

```yaml
sources:
  microsoft_ingest:   { type: http_server, address: "0.0.0.0:9001", encoding: json }
  duo_ingest:         { type: http_server, address: "0.0.0.0:9002", encoding: json }

transforms:
  dedup_microsoft:
    type: dedupe
    inputs: [microsoft_ingest]
    cache: { num_events: 5000 }
    fields:
      match:
        - metadata.original_time
        - device.ip.query
        - actor.user.email_addr        # PagerDuty incident ID is perfect for this
  dedup_duo:
    type: dedupe
    inputs: [duo_ingest]
    cache: { num_events: 50000 }
    fields:
      match: [txid]

sinks:
  vlogs:                               # inputs: [dedup_microsoft]
    type: elasticsearch
    endpoints: ["http://10.10.100.12:9428/insert/elasticsearch/"]
    api_version: v8
    compression: gzip
    healthcheck: { enabled: false }
    query:
      _msg_field: type_name
      _time_field: metadata.original_time
      _stream_fields: metadata.product.vendor_name
  vlogs_duo:                           # inputs: [dedup_duo]
    type: elasticsearch
    endpoints: ["http://10.10.100.12:9428/insert/elasticsearch/"]
    api_version: v8
    compression: gzip
    healthcheck: { enabled: false }
    query:
      _msg_field: event_type
      _time_field: isotimestamp
      _stream_fields: factor,event_type,result
```

Four things follow from this.

**Duo goes through Vector too, on port 9002.** The 2026-07-31 identity review recorded the Duo n8n node as posting directly to `10.10.100.12:9428/insert/jsonline`. The `vlogs_duo` sink's `_stream_fields: factor,event_type,result` is an exact match for the live Duo streams in VictoriaLogs, and its `_time_field: isotimestamp` explains why `isotimestamp:*` returns zero records — VictoriaLogs consumes that field into `_time`. Worth confirming the node's URL directly when n8n is reachable, but the evidence says Vector owns both paths, which means "post straight to VictoriaLogs" is not actually the house pattern. It is a pattern with zero current users.

**The dedup mystery is solved.** 1.1M Microsoft pushes/day collapse to ~1,650 rows because `dedup_microsoft` matches on the triple (`metadata.original_time`, `device.ip.query`, `actor.user.email_addr`) against a 5,000-event LRU cache. Duo dedupes on `txid` against a 50,000-event cache. Both caches are in-memory and reset on restart, which is fine for an overlap-window collector and worth knowing before anyone treats Vector as a durable dedup store.

**Someone already planned for this.** Line 41 of the config carries the comment `# PagerDuty incident ID is perfect for this`, sitting in the `dedup_microsoft` match list. The intent to route PagerDuty through Vector predates this work.

**The naming is misleading in both directions.** It is called TEMP-Vector and the container is "temporary", but it is load-bearing for every identity record that reaches VictoriaLogs. It is also not the villain the earlier review implied: it does not mangle `device_attributes`, it simply passes through what the Simvay API sends, which is already a JSON string.

## Where should the PagerDuty POST go?

Two viable targets, and this is a real decision rather than a formality.

**Through Vector**, as a new `pagerduty_ingest` source on `0.0.0.0:9003`, a `dedup_pagerduty` transform and a `vlogs_pagerduty` sink. This matches what both existing collectors do, moves dedup out of n8n's database and into the same component that already owns it, and gets Vector's buffering and retry on the VictoriaLogs hop for free. The costs are that it requires editing `vector.yaml` and restarting a load-bearing service, which is James's call, and that Vector's `dedupe` transform is exact-match only — so the match list must be `id` **and** `updated_at`, never `id` alone, or every late-settling ack and resolve correction gets silently dropped and the last-wins model breaks.

**Direct from n8n to `http://10.10.100.12:9428/insert/jsonline`**, with the `removeDuplicates` node doing the dedup, exactly as the attached workflow JSON is currently written. Nothing shared changes, Ryan can land it without waiting on anyone, and the `id`-plus-`updated_at` keying is already correct in the node. The cost is a third ingestion pattern in an environment that currently has one.

Recommendation: Vector, if James is available to make a ten-line config change this week. Direct from n8n if he is not — it is genuinely fine, and it can be moved behind Vector later without touching the dashboard, because the records land identically either way.

## What changes from the Duo template

Five nodes rather than three. Two of the additions are not optional.

**1. Schedule Trigger — 15 minutes rather than hourly.** The Duo flow's hourly schedule with a 60-minute lookback and no overlap is exactly why it has been losing events; do not copy that pattern. A 15-minute cadence against a 48-hour rolling window gives 192× overlap, which costs nothing because records are idempotent by `id`.

**2. Pull PagerDuty Incidents — `GET /pagerduty/incidents/raw`.** Repeat `service_ids` for both SentinelOne (`PG0FTPW`) and Auvik (`PEVYNFV`). Note that `rolling_hours=48` actually resolves to `now−52h` through `now−4h` because of the four-hour timestamp offset documented in section 4 of the review. That is harmless here — the overlap absorbs it — but it is why the window is 48 hours rather than something tighter.

**3. Normalise + Stamp — new, and mandatory.** The API returns naive timestamps: `2026-07-31T11:46:41`, no `Z`. Written as-is, VictoriaLogs interprets them in the host timezone and every record silently shifts four or five hours, which produces day buckets that look plausible and are wrong. This node appends the offset, and while it is there it also stamps `ingested_at` for the last-wins reduction, sets `query_type`, promotes the first acknowledger out of its array, and computes `triage_seconds` per incident — the last one because deriving triage time from means overstates it by 9.4×, so it is worth computing once at ingest rather than trusting every future panel to get it right.

**4. Only Changed Records — new.** `removeDuplicates` v2 is available on this instance (2.6.4, verified during the identity review). Keying on `id` alone would break the last-wins model, because a record whose ack or resolve timing later settles would be discarded as a duplicate. Keying on `{{ $json.id }}-{{ $json.updated_at }}` writes a record only when PagerDuty actually changed it. That takes roughly 10,700 pushes/day down to something closer to 100, while preserving every correction.

**5. Push to Log DB — same endpoint, different headers.**

| Header | Value | Why |
| --- | --- | --- |
| `VL-Msg-Field` | `description` | the incident title, the human-readable line in the log view |
| `VL-Time-Field` | `isotimestamp` | set by node 3; same field name the Duo collector uses |
| `VL-Stream-Fields` | `query_type,service_name,urgency` | exactly the three the gap spec called for, all low-cardinality |

Do not add `team_name`, `priority_name` or anything per-incident to the stream fields. They belong as regular fields; promoting them multiplies stream cardinality for no query benefit.

## Backfill

No second workflow needed. Swap the pull node's `rolling_hours` for explicit `created_at_start` / `created_at_end` — which are honoured verbatim, unaffected by the four-hour offset — and hit Execute three times for 30-day chunks. July alone is 1,116 records, so 90 days is roughly 3,300: small enough that chunking is about payload comfort rather than necessity.

## Acceptance checks

Run these against VictoriaLogs after the first execution.

| # | Check | Query | Want |
| --- | --- | --- | --- |
| 1 | Records landing | `query_type:PagerDutyIncidents \| stats count() n` | > 0 |
| 2 | Stream labels correct | `query_type:PagerDutyIncidents \| stats by (service_name, urgency) count() n` | high/low × SentinelOne/Auvik |
| 3 | Timestamps not shifted | `query_type:PagerDutyIncidents \| stats max(_time) t` | within ~5h of now, not ~9h |
| 4 | Dedup working | second execution 15 min later | near-zero new records |
| 5 | Numbers are numbers | `query_type:PagerDutyIncidents \| stats avg(seconds_to_resolve) x` | returns a number, no `convertFieldType` |
| 6 | Reconciles to the API | one UTC day, `count()` and `avg(seconds_to_first_ack)` where `acknowledged:true` | matches the metrics route exactly |

Check 6 is the one that matters. It is the same reconciliation that passed against the API in section 3 of the review; passing it again against VictoriaLogs is what makes the cutover safe.

## Pre-build confirmation (2026-08-01T15:18Z)

Re-verified immediately before this revision, unbounded time range, against `Simvay-Logs`. Nothing is writing PagerDuty data into VictoriaLogs:

| Query | Result |
| --- | --- |
| `query_type:PagerDutyIncidents \| stats count()` | 0 |
| `incident_number:*` | 0 |
| `seconds_to_first_ack:*` | 0 |
| `seconds_to_resolve:*` | 0 |
| `urgency:*` | 0 |
| `ingested_at:*` | 0 |
| all `query_type` stream values | `SentinelOneIntegration` (511,832), `SentinelOneAccounts` (1,621) — nothing else |

Confirmed independently on the Vector side: `grep -i pagerduty /etc/vector/vector.yaml` returns exactly one line, and it is the comment on line 41. There is no PagerDuty source, transform or sink. The field is clear.

## What this still does not fix

The feed carries only resolved, settled incidents, and settling takes hours. No cadence changes that. Open-incident and time-since-last-alert tiles stay on the SentinelOne VictoriaMetrics series or move to PagerDuty's REST API. That is a PagerDuty constraint, not something the workflow can route around.
