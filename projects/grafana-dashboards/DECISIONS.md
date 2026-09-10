---
title: Grafana Dashboards decisions
type: decisions
updated: 2026-09-09
related: [projects/grafana-dashboards/BRIEF, projects/grafana-dashboards/STATUS]
---

# Decisions (append-only, one dated line each)

Migrated 2026-09-09 from the Claude Project "Grafana Dashboards"; sources in archive/.

- 2026-07-17 (Ryan): Single PagerDuty incident worked to resolution; ack is work start; alert manager auto-resolves about one minute after SentinelOne resolution. MTTR truthful only after this date.
- 2026-07-17 (Ryan): SLAs are MTTA-based: high urgency 5 minutes, low urgency 12 hours. priority_name is authoritative over titles.
- 2026-07-20 (Ryan): Writes go to draft dashboards in the Testing folder only; production and shared library panels need explicit OK. Security News Feeds datasource is the one disclosed exception.
- 2026-07-21 (Ryan): One shared PagerDuty analytics query per dashboard, tiles consume it via the Dashboard datasource; keep total PagerDuty calls under about 300 per day. Refresh 12h until a caching layer exists.
- 2026-07-22 (Ryan): Trend chart is high urgency only; low-urgency acks skew the means.
- 2026-07-27 (Ryan): SOC Wallboard v2 parked until James ships urgency and service dimensions, 15-minute cadence, heartbeat, and a per-incident feed into VictoriaLogs.
- 2026-07-27 (Ryan): Country rule: every client domain is US-only except gzgreatlakes.com (China, Philippines, Japan, Singapore, Vietnam). Exclude Microsoft Corporation / Microsoft Limited ISP and org from country signals.
- 2026-07-27 (Ryan): Travel-line arcs on the map TV wait for proper access_device geo enrichment; no city-lookup stopgap; new panel, not a replacement of the geomap.
- 2026-07-27 (Ryan): Anomalous Logins board uses tiered rules (fraud, MFA denial, unexpected country, infra/VPN IP, device geo mismatch); mobile geo mismatches and no_response are excluded as noise.
- 2026-07-31 (Ryan): Detection and dashboard work parked pending James's identity pipeline changes (acceptance checks 1 to 5 in the handoff).
- 2026-08-01 (Ryan): New PagerDuty ingest routes through Vector (port 9003), the house pattern, not direct n8n to VictoriaLogs.
- 2026-08-01 (Ryan, during build): Dedup key is (id, payload_hash) because PagerDuty does not reliably bump updated_at; Vector owns dedup exclusively; n8n removeDuplicates withdrawn because it commits keys on node run, not workflow success.
- 2026-08-01 (Ryan): Null numerics are deleted at ingest, never written as null; records batched 200 per POST; disk buffers added to all three Vector sinks.
- 2026-08-01 (Ryan): SLA thresholds for v2: high 5 min MTTA and 1 h MTTR; low 12 h MTTA and 24 h MTTR. Unacked high-urgency incidents breach only if resolution took over 5 minutes.
- 2026-08-01 (Ryan): SOC Wallboard v2 PagerDuty tiles query VictoriaLogs directly; SentinelOne tiles stay on VictoriaMetrics.
- 2026-08-11 (Ryan): The full identity pipeline (dedup, Duo routing, batching, watermark, wide Entra columns, failed-login branch) is our work, not James's; API-side enrichment asks stay with James.
- 2026-08-11 (Ryan): Identity dedup keys are identity-only (Duo txid, Entra metadata.uid), not content hashes; identity events are immutable.
- 2026-08-11 (Ryan): Consolidate all identity ingestion into one n8n workflow modeled on the PagerDuty standard; approved with IP enrichment added. The "parser drops metadata.original_time/type_name" ask to James is withdrawn.
- 2026-08-12 (Ryan): Duo email resolution happens on our side (daily GET /duo/users joined in an n8n Data Table), not via an API ask.
- 2026-08-12 (Ryan): n8n[DEV] at 10.10.99.13 is the deployment target; Duo Push/Pull, the Action1 login branch and the Entra branch of SentinelOne Push/Pull are retired in favor of Identity Push/Pull.
- 2026-08-12 (Ryan): Identity liveness is measured on ingest time (ingested_at_unix), not event time; Microsoft Graph lags 2 to 4 hours normally.
- 2026-08-12 (Ryan): 16 identity detection rules approved with severity adjustments; Rule 4 (Duo fraud push) withdrawn because SentinelOne already covers it; all legacy "New Identity Alert" rules are EOL (disabled, not deleted).
- 2026-08-12 (Ryan): Identity rules notify 24/7 with no mute window; noDataState=OK and execErrState=KeepLast.
- 2026-08-14 (Ryan): Consumer VPN demotion list (both axes): iCloud Private Relay, NordVPN, ExpressVPN, Surfshark, Proton VPN, Private Internet Access. Cloudflare WARP and Mullvad keep paging. Mobilitie/SWITCH venue Wi-Fi keeps paging.
- 2026-08-14 (Ryan): Rules 3, 13, 16 and the exclusions in 6, 7, 11 are one matched provider-list set; edit all six queries in the same change.
- 2026-09-09 (Ryan): Project knowledge from the Claude Project "Grafana Dashboards" migrated into the brain repo; this folder is now the canonical record.
