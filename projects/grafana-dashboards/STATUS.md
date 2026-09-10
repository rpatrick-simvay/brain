---
title: Grafana Dashboards status
type: status
updated: 2026-09-09
owner: Ryan
---

# Grafana Dashboards: status as of 2026-09-09

State below reflects the last project record (2026-08-14). Nothing in the source docs covers 2026-08-15 onward; confirm with Ryan before assuming any item is still open.

## Where it stands
- PagerDuty feed is live since 2026-08-01 (n8n PagerDuty Incidents Push/Pull, Vector 9003, VictoriaLogs). Heartbeat fixed 2026-08-07 by publishing the draft. July 2026 aggregates reconcile exactly with the API.
- SOC Wallboard v2 (soc-wallboard-v2, Testing folder) is built on the VictoriaLogs feed; the old soc-wallboard-draft (v33) is untouched. Neither has been promoted out of Testing or put on a TV kiosk URL.
- Identity Push/Pull v1.1 went live 2026-08-12 with six branches; legacy Duo, Action1 login and Entra branches retired. Duo and Entra enrichment now covers both IP axes (verified 2026-08-12).
- 15 SIM-ID detection rules in SOC/Identity (13 live; 012 and 014 paused pending baselines), routed to SentinelOne through the Identity Alert Hook. Anomalous Logins Wallboard realigned to the rules (v13); queue dropped from 595 rows/24h to about 13.
- Ingest heartbeat rules SIM-OPS-001/002 exist but are paused: the VictoriaLogs datasource does not expand $__from, and ingested_at_unix coverage is only about 7% Entra / 47% Duo.

## Next three actions
1. Ryan or James: apply build-alert-node-v2.js to the Identity Alert Hook and wire the E1 error workflow, so High/Critical rules stop landing in SentinelOne as severity Low. About 30 minutes on the n8n box.
2. Ryan: promote SOC Wallboard v2 and Anomalous Logins out of Testing, set kiosk URLs per TV, retire soc-wallboard-draft. About one hour.
3. Ryan: export all dashboards and alert rules as JSON into a git repo (dashboards-as-code), recommended since 2026-07-20 and never started. About one hour for the first export.

## Later
- Fix the n8n Stamp node so ingested_at_unix reaches every row, then arm SIM-OPS-001/002.
- Build the 7-day BYOD allowlist (Rule 012) and Query B plus 30-day baseline (Rule 014), then unpause.
- Normalize count() to count_uniq on the remaining rules; surface client_geo_mobile on the wallboard.
- Ask James: add unmapped.ActorIpAddress to the SentinelOneIpField enum; fix the 4-hour offset in the PagerDuty routes; align on the "temporary" Vector Duo routing being permanent.
- Fleet Health / Inventory: Action1 enterprise seat ceiling snapshot for a true utilization tile; collector heartbeat for sentinelone_alert_count.
- Update the QBR triage-time metric spec to the post-2026-07-17 single-incident definitions before the next quarterly run.

## Blocked
- Travel-line arcs on the map TV: were blocked on access_device geo; Duo dual-axis enrichment landed 2026-08-11, so this is now unblocked and unbuilt.
- Webhook header auth on the Identity Alert Hook needs a change on the n8n box.
