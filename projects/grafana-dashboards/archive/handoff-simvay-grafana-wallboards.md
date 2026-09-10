# Handoff — Simvay Grafana SOC Wallboard Project

**Purpose of next session:** migrating this work into a dedicated project. This doc gives a fresh agent everything needed to continue the Grafana wallboard build-out for Simvay (an MSP/SOC) without re-discovery.
**User:** Ryan (rpatrick@[REDACTED]), technical, direct, likes iterative visual passes. Timezone America/New_York.
**Handoff written:** 2026-07-20.

## 1. Environment & access

- **Grafana** (v13.0.1, HTML sanitization DISABLED — CSS/script text-panel injection works): `http://10.10.99.11:3000`. Access via **Claude in Chrome** using tabs Ryan provides; he is logged in with admin rights. All work is done through the browser: `javascript_tool` on a Grafana-origin tab, calling `fetch('/api/...')` with `credentials:'same-origin'` (dashboard POSTs via `/api/dashboards/db`, queries via `/api/ds/query`, datasource proxy via `/api/datasources/proxy/uid/<uid>/...`).
- **PagerDuty**: subdomain `simvay.pagerduty.com` — NEVER navigate to `app.pagerduty.com` (bounces through identity.pagerduty.com and logs Ryan out; extension lacks permission for that domain). Ask Ryan to open a tab and click-navigate from there.
- **Simvay API** (FastAPI proxy): `http://10.10.100.8:8000` (`/openapi.json`). Duo, SentinelOne, Action1 routes; NO PagerDuty routes (proposed, not built).
- **Chrome extension quirks**: tab groups reset between sessions (`tabs_context_mcp createIfEmpty`); multiple browsers may be connected (Ryan uses "Browser 2"); this Grafana loads panel plugins slowly — wait 20–40s after navigation before judging a screenshot; VictoriaMetrics host (10.10.100.9:8428) is NOT extension-allowlisted (query it via Grafana datasource proxy instead).

## 2. Datasource map (uids matter)

| Name | uid | Notes |
|---|---|---|
| Temp PagerDuty API (Infinity) | `ffqszs3lk9se8a` | base `api.pagerduty.com`, apiKey auth. Load-bearing. |
| simvay-metrics (VictoriaMetrics) | `ff54vn5tei2o0d` | `sentinelone_alert_count{account,severity,alert_status,detection_type,alert_name,tenant_id}` |
| Simvay-Logs (VictoriaLogs) | `bfd1yqs9tvlkwf` | auth logs, Action1/S1 inventory snapshots, `query_type:SentinelOneIntegration` |
| Simvay-API (Infinity) | `cewz5mr2fpf5sc` | base URL prepends — cannot fetch absolute URLs |
| Security News Feeds (Draft) (Infinity) | `cfrk2guuwz2m8c` | **created by Claude**; no base URL, no creds, allowlisted to bleepingcomputer.com, feeds.feedburner.com, krebsonsecurity.com, isc.sans.edu. RSS needs a browser User-Agent header (Cloudflare 403 otherwise) and `root_selector: rss.channel.item`. |

## 3. Deliverables state (all in Grafana **Testing** folder, uid `cfbra19dmoyrka`)

- **SOC Wallboard (Draft)** `soc-wallboard-draft` (~v20) — flagship. Urgency-grouped tiles (High pair orange #ff9830, Low pair blue #5794F2, Triage purple #ad46ff, SLA Breaches thresholds), raw alert-count chart, Interruptions Breakdown (business/off/sleep), Incidents by Responder, Open/In-Triage counters, pipeline lag, live alert ticker + branded header w/ clock.
- **Inventory Wallboard (Draft)** `inventory-wallboard-draft` (~v12) — S1 purple #B877D9 / Action1 blue #5794F2 (vendor brand colors), canonical client names via LogsQL `replace ... at name` chains, per-client bars, 30d trend vs S1 license line ("true-up ref" — S1 is client-owned licensing, NOT an ops alarm; Action1 licensing DOES matter; enterprise A1 seat ceiling not yet collected).
- **Fleet Health Wallboard (Draft)** `fleet-health-wallboard-draft` (~v12) — Client Integration Matrix (verbatim clone of Posture's table — independent copy, edits don't sync; renaming pivot columns in the query BREAKS the transform chain), muted S1 API health strip, Security Headlines RSS panel (7 items, 19px).
- **Identity Wallboard (Draft)** `identity-wallboard-draft` (~v3) — Auth Map + anomalous auth table (lib panels).
- Docs delivered to Ryan in-conversation (regenerate if needed, containers don't persist): SOC metrics assessment, TRIAGE rework proposal, engineer handoff, **QBR triage-time metric spec** (now PARTLY OUTDATED — see §4), Grafana fleet review + TV plan (65" live queue + 4×40").

## 4. Pipeline context — CRITICAL, changed 2026-07-17

Old model (pre-07-17): ack auto-resolved the PD incident; a TRIAGE-priority tracker incident followed the S1 alert. **New model: single PD incident worked to resolution.** Ack = work start; alert manager polls S1 every 30s and resolves the PD incident ~1 min after S1 resolution (adds ~90s mechanical overhead to MTTR). SOC acks low-urgency only when actively working → Total Triage Time = Σ(seconds_to_resolve − seconds_to_first_ack).
- **SLAs (MTTA-based): High urgency (CRIT/HIGH/MED priority) = 5 min; Low urgency (LOW/INFO) = 12 h.**
- MTTA history valid across cutover; MTTR only truthful post-07-17. Dashboard default window now-3d; widen to 7d after ~07-24. The QBR metric spec doc's TRIAGE-priority rules apply to pre-cutover history only.
- PD service: SentinelOne = `PG0FTPW` (team `P66WLWF`); Auvik = `PEVYNFV` (different team — always filter by service, not team). `priority_name` is authoritative; titles lie during client onboarding.

## 5. Hard-won technical facts (do not relearn)

1. **PagerDuty analytics API has a DAILY quota** — returns `DAILY_LIMIT_EXCEEDED` as an empty-looking 200. Six tiles × 5m refresh burned it. Architecture now: ONE shared `/analytics/raw/incidents` query on panel id 1 (root_selector `data`), five tiles consume it via `-- Dashboard --` datasource + transforms (filterByValue/groupBy/calculateField); SLA Breaches keeps one JSONata call (OR logic); refresh 15m. Keep total ≤ ~300 calls/day. Also: burst reloads during dev trip the per-minute limiter (tiles blank, self-heal).
2. **Infinity backend JSONata**: object/array-of-object construction SILENTLY returns empty. Scalars, ternaries, `$count/$average/$sum/$sort`, variable blocks all work. One scalar per query + panel `displayName`.
3. **Filter-list animation gotcha**: CSS keyframes animating `filter` must have IDENTICAL function lists at every keyframe or the browser snaps instead of interpolating.
4. **Bubble styling**: stat `colorMode: background` gradient divs are selectable via `div[style*="linear-gradient"]`. Uniform spacing/alignment = `border: 7px solid transparent + background-clip: padding-box` (px inset), NOT `transform: scale` (proportional → misaligned edges). Sheen sweep on `::before`, breathe keyframes `bubbleBreathe`, crit pulse keyed to `rgb(223, 20, 16)` in inline style.
5. **Theme CSS lives in a hidden text panel (id 20) per dashboard** — header strip + clock + (SOC) ticker included. Scripts in text panels: `<script>` tags are inert (innerHTML); bootstrap via `<img src="data:," onerror="...">` with a `window.__guard`. Feed/ticker fetches go through `/api/ds/query` or the datasource proxy (no CORS).
6. **VictoriaLogs recipes**: instant stats → fields arrive in the `labels` object → `extractFields(source:"labels", replace:true)` + convertFieldType; `statsRange` queries → `extractFields(source:"Line")`. Name normalization server-side: `| replace ("old", "new") at name`.
7. **Collector behavior**: `sentinelone_alert_count` emits ONLY while alerts exist — pipeline-lag panels use `time() - max(tlast_over_time(sentinelone_alert_count[24h]))`. Proper fix (open ask to engineer): a collector heartbeat metric.
8. Grafana grid: ~26 rows fits 1080p kiosk (`?kiosk`); table density via `options.cellHeight:"sm"` + fieldConfig `custom.width`; react-data-grid hooks `.rdg-cell` / `.rdg-row`; page gutter `[class*="body-wrapper"]`.
9. Known data gaps: Olmsted Township + Western Reserve missing from `sentinelone_alert_count` accounts (ingestion gap, unresolved); Grafana "Accounts Reporting" red at 9/14 as of last check.

## 6. Open items / next steps

1. **Verify v20 SOC tiles after quota reset** (midnight UTC): urgency-split MTTA/MTTR values, Interruptions sums (sanity-check vs `total_interruptions`), Incidents-by-Responder labels (array field — regex value-mapping added untested; brackets may show).
2. Promotion path: move drafts out of Testing, kiosk URLs per TV, playlist for rotation, Chrome zoom per TV.
3. Dashboards-as-code: export JSON to git + provisioning (repeatedly recommended, not started). A dedicated project is the natural home.
4. Engineer asks outstanding: collector heartbeat metric, `alert_id` label / `sentinelone_alerts_total` counter, tenant ingestion gap, `/pagerduty` routes on Simvay API (retire "Temp PagerDuty API" DS), Action1 enterprise subscription snapshot → true A1 utilization tile.
5. Fleet Health: consider extracting the Integration Matrix into a shared library panel (touches production Posture — needs Ryan's OK). Identity: anomalous table noValue text (shared lib panel — needs OK).
6. Rules of engagement: drafts-only writes; the one exception so far is the Security News Feeds datasource (disclosed). Ryan confirms scope-consciousness matters to him.

## 7. Suggested skills

- `claude-in-chrome` — invoke BEFORE any browser tool; all Grafana/PD work flows through it.
- `dataviz` — read before styling any new panel; the boards follow its color-by-job rules (single hue for magnitude, status colors reserved, fixed severity palette CRIT red/HIGH orange/MED yellow/LOW blue/INFO purple).
- `simvay-qbr-decks` — QBR metrics must match the new single-incident definitions; the QBR spec doc needs a post-cutover update before next quarter's run.
- `skill-creator` — strong candidate: package this dashboard workflow (API-via-browser patterns, theme CSS, quota rules) as a `simvay-grafana-wallboards` skill for the dedicated project.
- `mattpocock-skills:research` / `engineering:documentation` — if the project starts with formalizing the dashboards-as-code repo.
