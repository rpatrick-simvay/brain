# SOC Wallboard v2 — PagerDuty data via Simvay API

**For:** James (Simvay API / collectors)
**From:** Ryan
**Date:** 2026-07-27
**Purpose:** Move the Grafana SOC Wallboard off direct `api.pagerduty.com` calls and onto Simvay-API-fed data. This documents what the API provides today, what the wallboard needs, and exactly what is missing.

---

## 1. What exists today

### 1.1 API routes (verified against `10.10.100.8:8000/openapi.json`)

| Route | Purpose |
|---|---|
| `GET /pagerduty/teams` | List teams visible to the stored key (`query`, `limit`). Discovery only. |
| `GET /pagerduty/metrics/incidents/teams` | Aggregated incident metrics per team from PD Analytics. |

Parameters on the metrics route:

| Param | Type | Default | Notes |
|---|---|---|---|
| `team_ids` | array[str] | `[]` | PD team IDs |
| `window` | int | `60` | Minutes; used to derive `created_at_start`/`end` |
| `created_at_start` / `created_at_end` | str | null | Explicit range, overrides `window` |
| `urgency` | `high` \| `low` | null | Single value per call |
| `major` | bool | null | |
| `aggregate_unit` | `day` \| `week` \| `month` | null | Returns one row per bucket |
| `time_zone` | str | `Etc/UTC` | |
| `prom_format` | bool | `true` | `true` → gauge samples; `false` → raw PD Analytics response |

Verified working: `aggregate_unit=day` returns per-day rows with the full metric set. Example (team `P66WLWF`, 7-day window, bucket 2026-07-21): `total_incident_count 109`, `mean_seconds_to_first_ack 44`, `mean_seconds_to_resolve 354`, `total_business_hour_interruptions 112`, `total_off_hour_interruptions 10`, `total_sleep_hour_interruptions 25`, `total_incidents_acknowledged 60`, `total_incidents_auto_resolved 103`, `total_down_time_minutes 155`.

### 1.2 Collector / storage

- Scrape job `pagerduty_team_metrics`, instance `localhost:7979`, landing in **VictoriaMetrics** (`simvay-metrics`, uid `ff54vn5tei2o0d`) — not VictoriaLogs.
- Observed call in the API journal: `/pagerduty/metrics/incidents/teams?window=1440` at `10:00:01Z`.
- **Cadence: once per day at 10:00:00 UTC** (06:00 EDT). A 10-minute-interval burst exists on 2026-07-22 17:00–18:20 UTC (test run), then nothing until the daily pattern starts.
- 29 metric names, all `pagerduty_*`, 58 series total.
- **Labels present: `team_id`, `team_name`, `job`, `instance`. Nothing else.**
- Teams covered: `P66WLWF` Security Operations Center, `P0KYTKC` Technology Management.

Metric families in VM:

```
pagerduty_mean_assignment_count            pagerduty_total_incident_count
pagerduty_mean_engaged_seconds             pagerduty_total_incidents_acknowledged
pagerduty_mean_engaged_user_count          pagerduty_total_incidents_auto_resolved
pagerduty_mean_seconds_to_engage           pagerduty_total_incidents_escalated
pagerduty_mean_seconds_to_first_ack        pagerduty_total_incidents_manual_escalated
pagerduty_mean_seconds_to_mobilize         pagerduty_total_incidents_reassigned
pagerduty_mean_seconds_to_resolve          pagerduty_total_incidents_timeout_escalated
pagerduty_mean_user_defined_engaged_seconds pagerduty_total_interruptions
pagerduty_total_business_hour_interruptions pagerduty_total_low_urgency_incidents
pagerduty_total_down_time_minutes          pagerduty_total_major_incidents
pagerduty_total_engaged_seconds            pagerduty_total_notifications
pagerduty_total_escalation_count           pagerduty_total_off_hour_interruptions
pagerduty_total_high_urgency_incidents     pagerduty_total_sleep_hour_interruptions
pagerduty_total_snoozed_seconds            pagerduty_total_user_defined_engaged_seconds
```

### 1.3 Window semantics (needs confirming with James)

A call at 15:40 UTC with `window=1440` returned `created_at_start 2026-07-25T20:00:00Z`, `created_at_end 2026-07-26T20:00:00Z` — a 24h window ending **~19.6 hours in the past**, not at "now". Either the API floors the end boundary or it compensates for PD Analytics' settle lag. Dashboards need this documented, because tiles will otherwise be labelled with the wrong period.

---

## 2. What the wallboard needs, tile by tile

Current SOC Wallboard (`soc-wallboard-draft`, v33): one shared PD `/analytics/raw/incidents` query on panel 1 feeds 8 tiles; a second PD call is the quota probe. Everything else is already VictoriaMetrics.

| Tile | Fields it consumes today | Servable from current API? |
|---|---|---|
| High Urgency — MTTA | `urgency`, `seconds_to_first_ack` | Only via a live per-urgency API call (`urgency=high`). Not from VM — no urgency label. |
| High Urgency — MTTR | `urgency`, `seconds_to_first_ack`, `seconds_to_resolve` | Same. |
| Low Urgency — MTTA / MTTR | `urgency`, both seconds fields | Same (`urgency=low`). |
| Total Triage Time | Σ(`seconds_to_resolve` − `seconds_to_first_ack`) per incident | Approximable as `(mean_resolve − mean_ack) × incident_count`; not exact — means are over different denominators (only 60 of 109 incidents were acked). |
| SLA Breaches | per-incident `seconds_to_first_ack` vs urgency SLA | **No.** Needs per-incident rows. |
| Interruptions Breakdown | `business/off/sleep_hour_interruptions` | **Yes**, already in VM. |
| Incidents by Responder | `acknowledged_user_names[0]` | **No.** Needs per-incident rows. |
| Daily MTTA/MTTR Trend (high urgency) | `created_at` day-bucketed, urgency-filtered means | Via live call with `aggregate_unit=day&urgency=high`. Not from VM at current cadence. |
| Alert Volume, Open Alerts, In Triage, Time Since Last Alert | SentinelOne metrics | Already VM, unaffected. |

---

## 3. Gaps — ranked ask list for James

### G1. Urgency dimension on the scrape (blocks 4 tiles)
The wallboard's core layout is urgency-split (High pair / Low pair) because the SLAs are urgency-based: **High = 5 min MTTA, Low = 12 h MTTA.** The current scrape has no `urgency` label, so those four tiles cannot be built from VM.

**Ask:** run the scrape three times per interval — no filter, `urgency=high`, `urgency=low` — and emit `urgency="all"|"high"|"low"` as a label. Cost: 3× the API calls, still trivial.

### G2. Service dimension (correctness, not just nicety)
The SOC board is scoped to the **SentinelOne service `PG0FTPW`**, not to the whole SOC team. Auvik (`PEVYNFV`) and future services roll into team-level numbers and will quietly inflate MTTA/MTTR. PD Analytics supports `service_ids`; the route does not expose it.

**Ask:** add `service_ids` to `/pagerduty/metrics/incidents/teams` (or a `/pagerduty/metrics/incidents/services` route) and emit `service_id` / `service_name` labels.

### G3. Scrape cadence (blocks wallboard use entirely)
One sample per day at 10:00 UTC means a wall-mounted board shows numbers up to 24 hours old and flatlines all day. Two of the last four days also have **missing samples** for the SOC team (07-26 and 07-27 absent for `mean_seconds_to_first_ack`) — likely NaN when the metric has no incidents, but it currently reads as "collector dead" to a dashboard.

**Ask:**
1. Scrape every **15 minutes** with a rolling `window=1440`.
2. Emit an explicit `0` (or omit consistently and document it) when a mean has no incidents in the window — pick one and tell us which.
3. Emit a **collector heartbeat** metric (e.g. `pagerduty_collector_last_success_timestamp_seconds`) so panels can distinguish "quiet night" from "collector down". This is the same ask already outstanding for the SentinelOne collector.

### G4. Per-incident raw feed (blocks SLA Breaches + Responder tiles, and QBRs)
Aggregates cannot answer "which incidents breached", "who acked what", or an exact Σ triage time. Spec in §4.

### G5. Window semantics documented
See §1.3 — confirm whether the ~20h end-boundary lag is deliberate.

---

## 4. Spec: per-incident PagerDuty data into VictoriaLogs

This is the piece that gets the wallboard fully off the PagerDuty API and makes QBR generation reproducible.

**Source:** PD Analytics `POST /analytics/raw/incidents`, filtered by `service_ids` (start with `PG0FTPW` SentinelOne and `PEVYNFV` Auvik), paged at `limit: 1000`.

**Cadence:** every 15 minutes over a rolling 48-hour window (2× overlap so late-settling records get corrected), plus a one-time **90-day backfill** for trend and QBR history.

**Quota:** at ~110 incidents/day this is 1–2 PD calls per run, ~100–200/day from a single consumer — versus today's model where every dashboard load spends quota. Well inside the daily analytics limit that we exhausted on 2026-07-21.

### 4.1 Fields to persist (one log record per incident)

| Field | Why the dashboard needs it |
|---|---|
| `id`, `incident_number` | Dedupe key; drill-through link |
| `created_at` | `_time`; day bucketing for the trend chart |
| `resolved_at` | Resolution timeline |
| `seconds_to_first_ack` | MTTA, SLA breach test, triage-time term |
| `seconds_to_resolve` | MTTR, triage-time term |
| `seconds_to_engage`, `seconds_to_mobilize` | Secondary timing, QBR |
| `urgency` | High/Low tile split; SLA threshold selection |
| `priority_name` | Authoritative severity (titles lie during onboarding) |
| `service_id`, `service_name` | Scope the board to SentinelOne; split Auvik out |
| `team_id`, `team_name` | Team rollups |
| `acknowledged_user_names` | Incidents-by-Responder tile (first element = acker) |
| `assigned_user_names` | Coverage / escalation analysis |
| `escalation_count`, `assignment_count` | Escalation tiles |
| `business_hour_interruptions`, `off_hour_interruptions`, `sleep_hour_interruptions` | Interruptions Breakdown |
| `snoozed_seconds`, `total_engaged_seconds` | Effort accounting for QBR appendix |
| `auto_resolved` / `resolved_by_user_name` | Distinguishes alert-manager auto-resolve from human resolve |
| `major` | Major-incident flagging |

### 4.2 Stream labels and shape

- Stream labels (low cardinality only): `query_type="PagerDutyIncidents"`, `service_name`, `urgency`.
- `_time` = incident `created_at`.
- Everything else as regular fields, matching the existing `SentinelOneIntegration` ingestion style so the same LogsQL patterns apply.
- Numeric fields must be emitted as **numbers, not strings** — the existing S1 records need `convertFieldType` gymnastics in every panel; avoid repeating that.

### 4.3 Mutation handling (important)

Incidents change after creation: created → acked → resolved. Two workable options — James's call, but the dashboard needs to know which:

1. **Append + last-wins.** Re-ingest the record on every poll; add an `ingested_at` field. Panels reduce with `stats by (id) last(...)`. Simple to write, heavier to query.
2. **Terminal-only + open snapshot.** Write the record once when it resolves, and separately publish an "open incidents" gauge for the live counters. Cleaner queries, but open incidents lose their history.

Recommendation: option 1, with a documented `ingested_at`.

---

## 5. What we can build before James ships anything

- Interruptions Breakdown → straight PromQL on the VM series (no PD calls).
- Team-wide incident counts, ack counts, auto-resolve rate, down-time minutes → VM.
- Urgency-split MTTA/MTTR + daily trend → live Infinity queries against `/pagerduty/metrics/incidents/teams`. Removes the PD API key from Grafana, but still spends upstream quota per refresh unless the API caches responses — worth confirming whether it does.
- SLA Breaches and Incidents by Responder → stay on the existing shared PD raw query until §4 lands, or come off the board.

**Bottom line for James:** the metrics route is a good foundation and the interruptions/volume tiles can move onto it immediately. Three additions unblock the rest — `urgency` and `service_ids` dimensions, a 15-minute cadence with a heartbeat, and a per-incident raw feed into VictoriaLogs.
