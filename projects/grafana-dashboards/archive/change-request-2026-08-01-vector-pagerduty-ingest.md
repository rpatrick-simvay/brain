# Change request — add a PagerDuty ingest path to TEMP-Vector

**To:** James
**From:** Ryan
**Date:** 2026-08-01
**Target:** Proxmox LXC 101 (`TEMP-Vector`) on node SIMSRV-PVE2, `/etc/vector/vector.yaml`
**Read, not changed:** the config was inspected read-only on 2026-08-01. Nothing was modified and Vector was not restarted.

## Why

The SOC Wallboard is being re-pointed off direct PagerDuty API calls and onto per-incident records in VictoriaLogs. The Simvay API route that serves them, `GET /pagerduty/incidents/raw`, is deployed and verified — it reconciles exactly against both the aggregate metrics route and PagerDuty's REST API across 30 days and 1,116 incidents. Nothing is currently carrying those records anywhere; VictoriaLogs holds zero PagerDuty data.

An n8n workflow (`PagerDuty Incidents Push/Pull`) will pull them every 15 minutes. It needs somewhere to POST. Routing it through Vector rather than straight at VictoriaLogs keeps all three collectors on one pattern and puts dedup where the other two already have it. The config already anticipates this — line 41 carries the comment `# PagerDuty incident ID is perfect for this`.

## The change

Three additions, mirroring the existing Duo path exactly. No existing source, transform or sink is touched.

```yaml
sources:
  pagerduty_ingest:
    type: http_server
    address: "0.0.0.0:9003"
    encoding: json

transforms:
  dedup_pagerduty:
    type: dedupe
    inputs:
      - pagerduty_ingest
    cache:
      num_events: 50000
    fields:
      match:
        - id
        - updated_at

sinks:
  vlogs_pagerduty:
    type: elasticsearch
    inputs:
      - dedup_pagerduty
    endpoints:
      - http://10.10.100.12:9428/insert/elasticsearch/
    api_version: v8
    compression: gzip
    healthcheck:
      enabled: false
    query:
      _msg_field: description
      _time_field: isotimestamp
      _stream_fields: query_type,service_name,urgency
```

## The one thing that must not change

**The dedup match list has to be `id` *and* `updated_at`, not `id` alone.**

PagerDuty incidents mutate after creation — an incident is written, then its ack and resolve timings settle over the following hours, and the record is re-fetched with corrected numbers. The model is append plus last-wins: panels reduce with `stats by (id) last(...)` ordered on `ingested_at`. Deduping on `id` alone would discard every corrected version as a duplicate of the first, freeze each incident at whatever its timings were on first sight, and produce MTTA and MTTR figures that are quietly wrong rather than obviously broken. Matching on the pair means a record is written only when PagerDuty actually changed it, which is both correct and cheap.

This is why the change is not simply `- id` despite the comment on line 41 suggesting the incident ID is the natural key. It is the natural *identity*; it is not the natural *dedup key*.

## Field notes

`isotimestamp` is set by the n8n workflow rather than coming from PagerDuty. The API returns naive timestamps — `2026-07-31T11:46:41`, no `Z` — so the workflow appends the offset and writes the result to `isotimestamp`, leaving the original `created_at` intact as a queryable field. VictoriaLogs consumes whatever `_time_field` names, which is why Duo's `isotimestamp` returns zero results when queried directly; the same will be true here, and `created_at` is the field panels should use for anything other than `_time`.

`description` is PagerDuty's incident title. The three stream fields are all low cardinality: `query_type` is a constant, `service_name` is SentinelOne or Auvik, `urgency` is high or low. Nothing per-incident belongs in the stream field list.

## Please also confirm

1. **Port 9003 reachable from n8n** (`10.10.99.13` → `10.10.100.13:9003`). Vector binds `0.0.0.0`, but the container or Proxmox firewall may need a rule — 9001 and 9002 presumably already have one.
2. **Whether the Duo n8n node posts to Vector on 9002 or straight to VictoriaLogs on 9428.** The 2026-07-31 identity review recorded the latter, but `vlogs_duo`'s `_stream_fields: factor,event_type,result` is an exact match for the live Duo streams, which suggests Vector owns that path. Not blocking, but the docs should say the right thing.
3. **The four-hour timestamp offset on the Simvay API**, which is separate from this change and covered in `claude/review-2026-07-31-pagerduty-victorialogs-cutover.md` section 4. It affects `window` on the metrics route and `rolling_hours` on the raw route, and it looks like one line of timezone handling. The ingest workflow works around it with a wide overlap window, but it should be fixed before dashboard panels are written against stored values.

## Expected volume

Roughly 112 records per 15-minute run against a 48-hour rolling window, so about 10,700 POSTs/day arriving at 9003, deduping down to something near 100 actual writes. For scale: the Microsoft branch currently pushes about 1.1M/day through 9001. This is noise by comparison.

## Verification after the restart

Run against VictoriaLogs once the n8n workflow has executed twice.

| # | Check | Expect |
| --- | --- | --- |
| 1 | `query_type:PagerDutyIncidents \| stats count() n` | > 0 |
| 2 | `query_type:PagerDutyIncidents \| stats by (service_name, urgency) count() n` | high/low × SentinelOne/Auvik |
| 3 | `query_type:PagerDutyIncidents \| stats max(_time) t` | within ~5h of now, not ~9h — proves the timezone handling held |
| 4 | second run 15 min later | near-zero new records — proves dedup |
| 5 | `stats avg(seconds_to_resolve)` | returns a number, no `convertFieldType` |
| 6 | one UTC day reconciled against the metrics route | exact match on count, high/low split, MTTA and MTTR |

Check 6 is the accuracy gate. It passed against the API; passing it again against VictoriaLogs is what makes the cutover safe.
