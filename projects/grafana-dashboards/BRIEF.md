---
title: Grafana Dashboards brief
type: brief
updated: 2026-09-09
tags: [grafana, soc, wallboard, victorialogs, pagerduty, identity, n8n, vector]
related: [projects/grafana-dashboards/STATUS, projects/grafana-dashboards/DECISIONS, projects/grafana-dashboards/TIMELINE, projects/data-platform/STATUS]
---

# Grafana Dashboards (SOC wallboards and identity detection)

## What it is
Simvay's SOC wall displays and the data pipeline behind them, built in Grafana 13 on the lab stack. The project started as a set of TV wallboards (SOC, Inventory, Fleet Health, Identity) and grew into the ingestion and detection layer those boards depend on: PagerDuty incidents and identity sign-in events (Entra, Duo, Action1) landing in VictoriaLogs through n8n and Vector, with Grafana alert rules that route identity findings into the SentinelOne console.

## Components
- Wallboards (Grafana Testing folder, uid cfbra19dmoyrka): SOC Wallboard v2 (soc-wallboard-v2), Inventory Wallboard, Fleet Health Wallboard, Auth Map (identity-wallboard-draft), Anomalous Logins Wallboard (identity-anomalous-logins-draft). All sized for 1920x1080 kiosk (26 grid rows maximum).
- PagerDuty feed: n8n workflow "PagerDuty Incidents Push/Pull" (id pr51pfrwucOZta1X), 15-minute schedule, 48-hour rolling window plus daily deep sweep, posting to Vector port 9003, deduped on (id, payload_hash), stored one row per revision in VictoriaLogs. Collector heartbeat stream query_type=PagerDutyCollectorHeartbeat.
- Identity feed: n8n workflow "Identity Push/Pull" v1.1 (id 2trEaeHEqTCkL4jhzBJ1d), six branches (Entra success, Entra failed, Duo, Action1 logins, Duo directory, Deep Sweep), normalized envelope with underscore fields alongside nested source fields, batches of 200, Vector ports 9001 (Microsoft), 9002 (Duo), 9004 (Action1).
- Detection rules: SIM-ID-001 to SIM-ID-016 (004 withdrawn) in Grafana folder SOC/Identity, routed through the "N8N - Identity" receiver to the Identity Alert Hook and then to SentinelOne unified alerts. Ingest heartbeat rules SIM-OPS-001/002 in folder HealthCheck, paused.
- Ingestion front door: TEMP-Vector (Proxmox LXC 101 on SIMSRV-PVE2, 10.10.100.13), Vector 0.55.0, config /etc/vector/vector.yaml, disk buffers on every sink, LimitNOFILE raised to 65535.

## Environment
- Grafana http://10.10.99.11:3000 (HTML sanitization disabled; all edits via browser fetch to /api/dashboards/db, always pass folderUid).
- Simvay API (FastAPI) http://10.10.100.8:8000, owned by James; enrichment via ip-api pro defaults on.
- VictoriaLogs 10.10.100.12:9428; VictoriaMetrics 10.10.100.9:8428 (datasource uid ff54vn5tei2o0d, not extension-allowlisted, query through the Grafana proxy).
- n8n http://10.10.99.13:5678 (titled n8n[DEV] but is production; instance timezone America/New_York; REST edits need an explicit publish or scheduled runs keep the old version).
- PagerDuty: use simvay.pagerduty.com only, never app.pagerduty.com. SentinelOne service PG0FTPW, Auvik PEVYNFV, SOC team P66WLWF.

## Why
Give the SOC a live, quota-safe view of alert load, triage performance and identity risk on wall TVs; make QBR metrics reproducible from stored per-incident data instead of ad hoc PagerDuty API calls; turn identity telemetry into detections that reach the analysts in the SentinelOne console.

## Constraints
- PagerDuty Analytics has a daily quota and only exposes settled incidents (12 to 36 hours lag). Live counters stay on VictoriaMetrics/SentinelOne.
- VictoriaLogs holds one row per PagerDuty revision; every aggregate reduces by id first (stats by (id) max(x) | stats ...). Identity counts use count_uniq(event_uid), never count().
- The Grafana VictoriaLogs plugin hangs on panel queries over roughly 22k characters; keep queries under about 8k.
- Rules of engagement: writes to drafts only; production dashboards and shared library panels need Ryan's OK.
- The 4-hour timestamp offset in the Simvay API PagerDuty routes is worked around, not fixed.

## Documents
- Source records 2026-07-20 to 2026-08-14 (28 docs) in archive/ in this folder, listed in TIMELINE.md.
- Rule definitions: archive/spec-2026-08-12-identity-detection-rules-v1.md (amended 2026-08-14).
- Pipeline design: archive/design-2026-08-11-identity-consolidation-review.md and archive/implementation-2026-08-01-pagerduty-victorialogs-live.md.
