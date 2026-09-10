# Closeout — V5/V6 alert-path + ingest heartbeat (2026-08-12 ~23:10Z)

Finishing the two build-time gates on the identity detection rules (spec: `claude/spec-2026-08-12-identity-detection-rules-v1.md`, rev.8). Work done live against Grafana (10.10.99.11:3000) from Ryan's Home Desktop browser.

## CORRECTION — no incident. My "Entra stall" alarm was a false positive.

Earlier in this session I flagged a live Entra ingest stall (freshest event `_time` = 20:47Z, "0 events in 2h"). **That was wrong.** Ryan pointed out Microsoft Graph normally surfaces events ~2–4h late, which he has lived with for over a year. Re-checked on the correct clock:

- **All four streams are actively ingesting**, by `ingested_at_unix` (the push-time stamp), max age at 23:03Z: entra_login_success **0 min**, entra_login_failed **6 min**, duo_auth **2 min**, action1_login **3 min**.
- A row landed ~2 min ago carrying an event with `_time` 18:48Z — i.e., a ~4h-old event just arrived. That is normal Graph latency, not a stall.
- Lesson: **event-time (`_time` = metadata.original_time) is NOT a liveness signal for Entra** — Graph delay makes recent-`_time` windows perpetually near-empty even when healthy. Liveness must be measured on **ingest time**.

## V6 — ingest heartbeat (Grafana) — DRAFTED, paused, FAIL-SAFE (needs redesign before arming)

Two rules exist in folder `HealthCheck` (ff5aw2cuz162oe), routed to the **PagerDuty** contact point (direct to Events API v2 — deliberately NOT the identity→S1 hook). **Both isPaused + noDataState=OK (fail-safe: cannot page while draft).**

| UID | Title | Status |
|---|---|---|
| dfv02j6tkmio0c | SIM-OPS-001 - Entra Identity Ingest Stalled | DRAFT — do not arm |
| efv02j6vijocgd | SIM-OPS-002 - Duo Identity Ingest Stalled | DRAFT — do not arm |

**They were first drafted on event-time and would false-fire constantly (see correction above).** Correct design keys on ingest time: count rows whose `ingested_at_unix` landed in the last window; stall = 0. Headroom is excellent — healthy Entra lands **168 rows/60m**, Duo **305/60m** (measured), so a real stall (→0) is unambiguous.

**Two blockers before this can be armed:**
1. **Time-macro expansion:** the VictoriaLogs Grafana datasource did not expand `$__from` correctly through any path testable from the cloud session (`${__from}` errors; `$__from` returned 0 where an explicit epoch returned 168). Needs finishing on the box with the real rule-test panel — or inject the `now−window` bound via n8n / a recording rule instead of a macro.
2. **Field coverage:** `ingested_at_unix` is only on ~7% of Entra rows and ~47% of Duo rows. Even the current count clears the threshold comfortably, but for a bulletproof heartbeat the n8n **Stamp node should write `ingested_at_unix` on every row** (James/n8n).

**Durable datasource gotchas found (still valid):**
- VL Grafana plugin does not honor `stats by (_time:1h)` bucket syntax (works via raw VL API only). Use `stats by (_time) count() n` → reduce **sum**. Bare `stats count()` errors "wide series … got type long".
- `${__from}` (braced) throws a VL parse error; time macros need verification on this datasource.

**Why two rules, not one:** independent failure — if only the Entra pull dies while Duo flows, a combined heartbeat misses it. Keep them separate.

## V5 — alert-path correctness — code produced, apply + synthetic test remain

**PagerDuty contract confirmed** (read live from the "PagerDuty" contact point): webhook → `https://events.pagerduty.com/v2/enqueue`, `summary ← CommonAnnotations.summary`, `custom_details` carries `alertname / severity / alert_id / alert_status` from CommonLabels, `dedup_key ← .GroupKey`. Identity rules must set `annotations.summary`, `annotations.description`, labels `severity`, `alert_id`(=rule_id), `alert_status`.

**S1 severity enum confirmed** (live NFR alert): UAM severities UPPERCASE `CRITICAL/HIGH/MEDIUM/LOW`; `INFORMATIONAL` for Info. detectionSource `SIMVAY / Simvay-Identity`, primaryIndicatorType `Authentication`.

**Build Alert node v2** (`build-alert-node-v2.js`, delivered) — drop-in replacement fixing the 3 review gaps: severity from the `severity` label (old code parsed the alertname suffix → Critical/High/Info silently became Low); `finding_info.uid` = dedup key; per-rule evidence labels as a `Rule Evidence` related_event. Keeps `resources[0].name = email` so domain→tenant routing still works. class_uid 99602001, extension s1/996 unchanged.

**E1 error workflow** (`identity-error-workflow-E1.json`, delivered) — n8n Error Trigger → PagerDuty Events v2. Catches node/API errors. Complements the heartbeat (a dead scheduler throws nothing → heartbeat covers that; E1 covers thrown errors).

**Remaining for Ryan/James (on the n8n box — browser bridge sanitizes n8n creds):**
1. Swap the Build Alert node for v2; publish.
2. Import + wire E1 as the Identity Push/Pull error workflow.
3. Action1 (Rule 5) → NFR: one static map in the hook (`record_type:action1_login` → NFR), not domain-routed.
4. Add header auth to the `Webhook - Medium/High` node (currently unauthenticated).
5. Raise `ingested_at_unix` coverage to ~100% (Stamp node) → then finish + arm the heartbeat.
6. Synthetic test per severity via Grafana contact-point "Test" button → confirm S1 casing + PagerDuty summary.

## State
Detection rules rev.8 = query-validated + approved. V5 + E1 = code delivered, n8n apply pending. V6 heartbeat = drafted but keyed on the wrong clock; corrected design (ingest-time) blocked on macro expansion + field coverage — rules left paused + fail-safe. **No live incident — Graph latency is normal.** Next: apply n8n artifacts, fix ingest-stamp coverage, finish heartbeat on the box, run synthetic tests, then arm rules (2, 11 first).
