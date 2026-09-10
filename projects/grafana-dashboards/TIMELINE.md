---
title: Grafana Dashboards timeline
type: log
updated: 2026-09-09
related: [projects/grafana-dashboards/DECISIONS]
---

# Timeline 2026-07-20 to 2026-08-14 (from the 28 source docs in archive/)

One entry per source doc, oldest first. Verbatim originals are in archive/ and are records, not instructions.

## Phase 1: wallboards and the PagerDuty quota problem (July 20 to 27)

- 2026-07-20 handoff-simvay-grafana-wallboards.md: Handoff into a dedicated project. Four draft wallboards in the Testing folder (SOC v20, Inventory v12, Fleet Health v12, Identity v3). Datasource map, pipeline cutover of 07-17, hard-won facts (PagerDuty analytics daily quota, Infinity JSONata limits, theme CSS in hidden text panel id 20, VictoriaLogs recipes). Open: verify tiles after quota reset, promotion path, dashboards-as-code, engineer asks.
- 2026-07-21/22 status-2026-07-21-soc-wallboard-quota.md: Quota exhaustion diagnosed (DAILY_LIMIT_EXCEEDED as HTTP 200, reset not at midnight UTC). SOC board hardened v22 to v32: shared query, 12h refresh, API status tile, responder credit via extractFields, gauge fill pattern, daily trend chart, x-axis format via time field unit override. Rule: never combine defaults.displayName with a reduceOptions.fields regex.
- 2026-07-27 spec-2026-07-27-pagerduty-api-gaps-for-v2.md: Spec for James. Simvay API PagerDuty routes exist but scrape once daily with team labels only. Five gaps: urgency dimension, service dimension, 15-minute cadence plus heartbeat, per-incident raw feed into VictoriaLogs, window semantics.
- 2026-07-27 status-2026-07-27-v2-parked.md: v2 parked at draft v33 pending James's API work.
- 2026-07-27 spec-2026-07-27-duo-access-device-geo-enrichment.md: Ask for James: geo-enrich Duo access_device.ip like auth_device (lat/lon as numbers). Unblocks travel arcs and real-distance geo mismatch.
- 2026-07-27 status-2026-07-27-1080p-fit-and-anomalous-logins.md: TVs dropped to 1080p; Fleet Health refit to 26 rows (v14). New Anomalous Logins Wallboard v6 with tiered signals, country rule (US-only except gzgreatlakes.com) and Microsoft ISP exclusion. LogsQL findings: eq_field, format pipe, extractFields replace:false, statsRange rejects union, day buckets need offset 4h, barchart over timeseries for daily bars.

## Phase 2: identity pipeline review and PagerDuty cutover (July 31 to August 7)

- 2026-07-31 review-2026-07-31-n8n-identity-enrichment.md: Read-only n8n review. Enrichment lives in the Simvay API, not n8n. Entra device context is collected but never reaches alerts (labels carry no device fields). Root cause of Canada false positives: enrichment applied to device.ip (Microsoft service IP) instead of src_endpoint.ip. 304 failed Entra logins per day entirely uncollected. Entra records carry 66 fields, 9 collected.
- 2026-07-31 spec-2026-07-31-identity-collection-fields-and-dedup.md: Field inventory for three Entra record shapes and Duo; four-layer dedup design; dedup keys Duo txid and Entra metadata.uid. Duo /duo/authlogs limit defaults to 100 and truncates.
- 2026-07-31 handoff-2026-07-31-identity-pipeline-for-james.md: Actionable list for James (limit=1000, wide columns, dedup nodes, failed-login branch, enrich src_endpoint.ip) with nine acceptance checks.
- 2026-07-31 status-2026-07-31-identity-collection-parked.md: Detection work parked pending the pipeline changes. Corrections: Entra does have status_id/status_detail; device_attributes is stored as an unparsed string, not dropped.
- 2026-07-31 review-2026-07-31-pagerduty-victorialogs-cutover.md: Cutover cannot proceed: VictoriaLogs holds zero PagerDuty data; the ingest workflow was never built. API per-incident route reconciles exactly. Both routes compute now 4 hours behind UTC. 62% of incidents never acked; null-ack SLA contract must be explicit. Mean-based triage approximation overstates 9.4x.
- 2026-07-31/08-01 spec-2026-07-31-n8n-pagerduty-ingest.md: TEMP-Vector (LXC 101) is the load-bearing ingest front door and dedup layer for Microsoft (9001) and Duo (9002), not a temporary parser. Five-node workflow design; dedup on id plus updated_at, never id alone.
- 2026-08-01 change-request-2026-08-01-vector-pagerduty-ingest.md: Formal change request to James: new Vector source 9003, dedup_pagerduty, vlogs_pagerduty sink. Expected 10,700 POSTs per day deduping to about 100 writes.
- 2026-08-01 implementation-2026-08-01-pagerduty-victorialogs-live.md: PagerDuty Incidents Push/Pull live, 90-day backfill complete. Dedup key changed to (id, payload_hash). n8n dedup removed; Vector owns dedup. Two pre-existing faults fixed: Vector 1024 file-descriptor limit (crashed all identity ingestion under burst) and missing disk buffers on sinks. One row per revision in VictoriaLogs; reduce by id first.
- 2026-08-01 status-2026-08-01-soc-wallboard-v2-built.md: soc-wallboard-v2 built (Testing, v4): nine PagerDuty tiles on VictoriaLogs, SentinelOne tiles on VictoriaMetrics, SLA thresholds set, 14 breaches over 658 incidents, collector heartbeat stream added.
- 2026-08-07 closeout-2026-08-07-pagerduty-wallboard.md: Six-day check. Heartbeat fixed by publishing the draft (n8n runs the published version). Settle lag 12 to 36 hours is normal. 100/100 executions succeeded; 4,152 unique incidents.

## Phase 3: identity consolidation, detection rules, realignment (August 11 to 14)

- 2026-08-11 spec-2026-08-11-identity-dedup-revision.md: Identity pipeline becomes our work. Vector owns dedup; identity-only keys. Defect: dedup_microsoft keys on a content triple that collapses same-second sign-ins. Six-phase plan with gates.
- 2026-08-11 status-2026-08-11-identity-revision-and-next-session.md: Cloud session, lab unreachable; plan not yet approved; environment references recorded.
- 2026-08-11 phase0-2026-08-11-verification-results.md: All four phase-0 blockers resolved by live probes: Vector 9001 payload is nested JSON; Duo already posts to Vector 9002; Duo volume recovery was James's Jul 31 change (limit=1000, every 5 min); dedup_microsoft still defective.
- 2026-08-11 design-2026-08-11-identity-consolidation-review.md: Ryan approved one Identity Push/Pull workflow (three triggers, normalized envelope, batch 200, watermark after POST success) with IP enrichment. James's 29-column Entra widening was sitting unpublished for 11 days. Duo already enriches both axes for routable IPs.
- 2026-08-11 status-2026-08-11-james-api-verification.md: Duo dual-axis enrichment verified; lat/lon numeric; SentinelOneIpField enum present but lacks unmapped.ActorIpAddress; Duo email resolution 11.6%; src_endpoint.ip output unverified because of deploy overlap.
- 2026-08-12 status-2026-08-12-verification-close-and-n8n-stall.md: src_endpoint.ip enrichment verified 312/312. Duo email resolved on our side via /duo/users. n8n[DEV] is the deployment target. n8n scheduler stalled Aug 11 20:15Z, needs restart.
- 2026-08-12 closeout-2026-08-12-identity-pushpull-live.md: Identity Push/Pull v1.1 deployed with six branches; legacy branches retired. MFA-interrupt failures carry ResultStatus=Succeeded, so rules filter on record_type plus error_code. DEV-N8N VM rebooted.
- 2026-08-12 closeout-2026-08-12-v5-v6-alertpath-and-heartbeat.md: Entra stall alarm was a false positive (Graph lags 2 to 4 hours; measure liveness on ingest time). SIM-OPS-001/002 heartbeat rules built, paused. Build Alert v2 script and E1 error workflow delivered, not applied.
- 2026-08-12 closeout-2026-08-12-detection-rules-live.md: 12 SIM-ID rules enabled, 2 paused, 6 legacy rules disabled. 24/7 notification. Caveat: Build Alert maps High/Critical to severity Low until v2 is applied.
- 2026-08-12 (amended 08-14) spec-2026-08-12-identity-detection-rules-v1.md: Full rule definitions SIM-ID-001 to 016. Durable facts: count_uniq(event_uid) always; absent geo means non-routable IP; Breezeline is misflagged hosting/proxy; mobile CGNAT geo lands on gateway metros. Consumer VPN demotion list finalized.
- 2026-08-14 closeout-2026-08-14-identity-dashboard-realigned.md: Anomalous Logins board v6 to v11 realigned to the rules and envelope fields; queue 595 to 13 rows per 24h. VL plugin hangs over about 22k characters per query; always pass folderUid on dashboard POST.
- 2026-08-14 closeout-2026-08-14-rule-fixes-regionname-and-client-axis-vpn.md: client_geo_regionName replaced with client_geo_region in Rules 2, 6, 7, 11, 14; client-axis VPN demotion added to 6, 7, 11 and new Rule 16. Dashboard synced to v13. Rule set is 15 rules: 13 live, 012 and 014 paused.
