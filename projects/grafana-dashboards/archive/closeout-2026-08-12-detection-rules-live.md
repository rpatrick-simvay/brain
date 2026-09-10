# Closeout — Identity detection rules configured, enabled, legacy disabled (2026-08-12 ~23:40Z)

Built live in Grafana (10.10.99.11:3000, folder SOC/Identity `ffh405wysfls0a`, group "Identity Evaluation") from Ryan's Home Desktop browser via `/api/v1/provisioning/alert-rules`. Spec: `claude/spec-2026-08-12-identity-detection-rules-v1.md` rev.8.

## Final state

**ENABLED (12, firing 24/7 → receiver "N8N - Identity" → Build Alert → S1):**
SIM-ID-001 (High), 002 (Critical), 003 (Medium), 005 (Medium), 006 (High), 007 (High), 008 (High), 009 (High), 010 (Low), 011 (Critical), 013 (Info), 015 (High).

**PAUSED — baseline-gated per approved spec (2):** SIM-ID-012 (generic-hostname unmanaged — would flag ~14 known-BYOD until a 7-day allowlist), SIM-ID-014 (first-seen location — needs 30-day baseline settle + mobile Query B). Built and ready to arm.

**DISABLED — all 6 legacy "New Identity Alert" rules:** Duo/Entra/Action1 × {Medium-High, Low}. (isPaused=true, not deleted — recoverable.)

## Rule construction pattern (canonical)
`<detection LogsQL, returns rows only when triggered> | mv <envelope fields → hook label names> | stats by (email, ip, isp, org, ismobile, isproxy, ishosting, country, city, region, event, tenant [+ rule extras]) count() total` → B reduce count → C threshold `>0`. relativeTimeRange A = 30d (inner `_time:` filters do the real windowing; 30d covers the SIM-ID-001/002/014 subqueries). Each rule carries labels `{alert_class, rule_id, alert_id, severity, alert_status}` and annotations `{summary "[SIM-ID-XXX | Sev] …", description (templated on $labels), runbook_url}`. Every query validated against live VL before creation.

**Per-rule axis mapping (found during validation — not one-size-fits-all):**
- Client/access axis (006, 007, 011, 001, 010, 005, 012, 014): `mv client_geo_* → labels`.
- Approver/phone axis (003, 013): `mv approver_geo_* → labels` (the suspicious signal is the phone's network). Note: approver axis carries isp/org/country/city but NOT a clean `ip`/`region` field — acceptable (ISP+country tells the story).
- Aggregate-by-source (001, 010): synthetic static `email` ("password-spray-source" / "disabled-account-probe"); no domain → routes to default tenant, correct for multi-tenant spray. `accounts`/`attempts` kept as labels for the summary.
- Aggregate-by-user (008, 009): `email` = user_email; `denies`/`countries` as labels.
- Action1 (005): envelope uses `client_geo_region` (NOT regionName) and has both `client_geo_*` and `ipv4.*`.
- Rule 015: both axes — client geo as primary + `approver_geo_country` as extra label.

## Choices made (override if wrong)
1. **24/7 notification.** Legacy rules used an "Identiy Timings" mute window (10:00–23:00). Removed it for these — a 3am spray-to-success / AiTM must page. Revert by adding `active_time_intervals:["Identiy Timings"]` to notification_settings if off-hours muting is wanted for the low-tier rules.
2. **12 & 14 paused** (baseline-gated), consistent with rev.8 §4.
3. `noDataState=OK`, `execErrState=KeepLast` (matches working legacy rules; avoids paging on transient VL errors).

## KNOWN CAVEAT — apply Build Alert v2 to fix S1 severity_id
The current n8n Build Alert node maps severity from the alertname suffix and only knows Medium/Low → **High/Critical alerts currently land in S1 with severity_id = Low.** Mitigation in place: the alert **title/summary carries `[SIM-ID-XXX | Critical]`**, so analysts see the true severity in the S1 alert name and PagerDuty summary now. Applying `build-alert-node-v2.js` (delivered) reads the `severity` label and corrects severity_id **with zero rule changes** — the rules already emit the label. This is the top follow-up.

Other n8n follow-ups (unchanged from V5/V6 closeout): wire E1 error workflow; Action1(005)→NFR static map (until then 005 routes by user_email domain like the rest); webhook header auth.

## State
12 rules live, 2 paused, 6 legacy disabled. Expected volume ~5–10 alerts/week total (validated). Heartbeat parked per Ryan. Next: apply Build Alert v2 (severity), then build the 7-day allowlists to arm 012/014.
