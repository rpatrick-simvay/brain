# Identity ingestion consolidation — review findings + design (2026-08-11)

Ryan's direction: condense all identity ingestion into ONE n8n workflow built on the PagerDuty Incidents Push/Pull standard, pull every decision-relevant field, normalize across platforms. **Ryan reviewed the plan 8/11 and approved it ("plan looks solid") with one addition: IP enrichment (§ below).** Review vehicle: `identity-consolidation-field-review.xlsx` v2 (7 sheets, delivered in session). This doc records the durable findings; the spreadsheet has the full field-by-field detail.

## New findings from the live n8n review (beyond phase 0)

1. **James staged the Entra column widening as an UNPUBLISHED draft.** SentinelOne Push/Pull version history: published version 1.52 (James, Jun 15) = the 9-column pull that is live; unpublished draft (James, Jul 31 16:19:29) widens `columns` to 29 fields — essentially the 7/31 spec §2 Stream A+B list (adds actor.user.uid, actor.session.uid, src_endpoint.ip, device.is_compliant, device.os.type_id, status_id, status_detail, metadata.correlation_uid, dst_endpoint.uid, ExtendedProperties, Operation, RecordType, cloud.org.uid, http_request.user_agent, BrowserName, BrowserVersion, AuthenticationType, GeoLocation, AppAccessContext.ClientAppName, ApplicationDisplayName). This is why VL still shows src_endpoint.ip/is_compliant at 0 — the draft-vs-published gotcha (#8 in the 8/11 spec), live for 11 days. Filter unchanged (`event.type='Logon'`, 12h lookback, no Stream C, no watermark).
2. **The Entra push is one-POST-per-record** (`Push Logs to temporary Parser`, POST :9001/, raw `JSON.stringify($json)`), same shape as Duo — confirms the 8/1 crash-shape concern on both branches.
3. **SentinelOne Push/Pull carries two non-identity branches** (S1 integrations + accounts inventory) that POST **directly to VL :9428**, bypassing Vector (no dedup, no disk buffer). They stay behind in the consolidation; flagged as future cleanup.
4. **PagerDuty workflow re-confirmed as the standard**: dual-cadence triggers (15-min rolling + daily deep sweep) → pull with retry → Normalise + Stamp (truncation guard ≥5000, UTC coercion, null-numeric deletion, payload_hash, ingested_at_unix, throw on missing keys) → Batch (arrays of 200) → single POST per batch → Vector dedupe → disk-buffered sink.

## IP enrichment (Ryan's addition, verified against the OpenAPI spec 8/11)

The Simvay API has an ip-api **pro** enrichment function: geo (lat/lon/city/region/country/continent/timezone/zip), network (isp/org/as/asname) and the **mobile / proxy / hosting flags** — high detection value (proxy'd MFA approvals, VPS logins).

- **Duo `/duo/authlogs`: already enriches BOTH device axes by default.** Params `enrich` (default true) + `enrich_fields` (closed enum `DuoIpField`: `access_device`, `auth_device`, defaulting to all). Docstring caveat: **only routable addresses are sent to ip-api** — 0.0.0.0 (device invisible to Duo) and RFC1918 (on-prem) are skipped. This most likely *explains* the measured coverage (auth_device geo 9%, access_device 0%) as the routable fraction, not a defect — verify by measuring the routable fraction in step-2 QA. Consolidated pull passes `enrich=true&enrich_fields=access_device&enrich_fields=auth_device` explicitly.
- **Entra `/sentinelone/datalake/queryall`: `enrich` (default true) but NO field selector — hardcoded to `device.ip`.** The concrete James ask: extend the datalake route's enrich set to `src_endpoint.ip` (+ `unmapped.ActorIpAddress` for stream C), ideally coalesce-then-enrich. His own DuoIpField closed-enum pattern is the template ("add a member here — that is the only change needed"). This retires the Canada-FP 5-panel workaround.
- Envelope: two axes — `client_geo_*` (workstation/client) and `approver_geo_*` (Duo phone) — full block on each; booleans real; lat/lon numeric (strings today — James ask stands); **absent geo = on-prem/invisible signal, never missing data**.
- Detection rules unblocked: proxy'd MFA approval, hosting/VPS interactive login, impossible travel on numeric lat/lon, cellular-vs-wifi approver baseline, RFC1918-as-on-prem baseline.

## Consolidated design (spreadsheet sheet 3)

One workflow **"Identity Push/Pull"**: three triggers (Entra 60s, Duo 5-min, daily 24h deep sweep), watermark Data Table read (per record_type: entra_success / entra_signin / entra_failed / duo_auth), three pulls (Entra A+B wide-column Logon query, enrich=true; Entra C UserLoginFailed query with NO device.ip term; Duo authlogs limit=1000 with explicit enrich_fields), per-branch Normalise + Stamp emitting a **normalized envelope** (top-level underscore fields: event_uid, event_time(_unix), record_type, vendor, tenant_uid, user_email/name/uid, client_ip coalesced, auth_result, result_detail, error_code, auth_method, application, device_managed/compliant (real booleans), device_os/hostname/uid, browser, user_agent, client_geo_*, approver_geo_*, ingested_at_unix, payload_hash-diagnostic) **alongside preserved nested source fields** (wire must stay nested — Vector dedupe match paths depend on it, proven by the 8/11 probe), batch 200, one POST per batch (Entra :9001, Duo :9002), watermark write strictly downstream of POST success, error trigger → PagerDuty/Alerting.

Replaces: Duo Push/Pull (whole) + the Entra branch of SentinelOne Push/Pull. Supersedes James's draft (absorbs its columns). Identity Alert Hook untouched.

Deliberate divergence from PagerDuty: **no content hash in dedup keys** (identity events are immutable; payload_hash carried as diagnostic only, excluded from match) and **no per-panel id-reduction needed** (one row per event; count_uniq discipline still mandatory for restart windows).

## Rollout mapping (absorbs approved-pending phases 2–5)

1. Vector phase 1 unchanged: dedup_microsoft → match [metadata.uid], cache 50k, SIGHUP; 24h gate.
2. New workflow with Duo branch only; unpublish Duo Push/Pull. Gate: volume holds, ≤2 POSTs/run. QA adds: measure routable fraction of access_device/auth_device IPs (settles enrichment-coverage question).
3. Add Entra A+B (30-col); unpublish SentinelOne Entra branch. Gate: checks 3/4/6/7/8.
4. Watermarks. Gate: force-fail run → watermark must not advance.
5. Entra C branch (hard-blocked on step 1). Gate: ~300 failed logins/day; no cross-stream uid collision.
6. Duo cadence/limit review, alone.

## Open decisions (sheet 7, top ones)

- Duo email 13% → correlation key decision (ask James: user.key→email resolution).
- James asks, consolidated: (a) extend datalake enrich set to src_endpoint.ip + ActorIpAddress (coalesce-then-enrich), (b) lat/lon numeric, (c) user.key→email, (d) quantify 4h offset. Items formerly "enrich access_device" and "explain auth_device 9%" are RESOLVED/reframed — enrichment exists; coverage is the routable fraction (verify in step 2).
- Coordinate with James BEFORE build: his draft is superseded, and his "temporary dedup mechanism" framing needs to become permanent (else risk of revert mid-rollout).
- Disk-buffer headroom re-check before step 3 (wide columns triple Entra record size).

Status: **plan approved by Ryan 8/11 (incl. enrichment addition). Ready to build** — next session starts at rollout step 1 (Vector phase 1), then step 2. Nothing changed in n8n or Vector this session beyond the phase-0 read-only probe (cleaned up).
