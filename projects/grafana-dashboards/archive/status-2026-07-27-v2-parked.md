# Status — SOC Wallboard v2 parked pending API work (2026-07-27)

**State:** No dashboard changes made. `soc-wallboard-draft` untouched at v33. No v2 copy created yet.

**Decision:** James is implementing the missing PagerDuty endpoints/collector changes. v2 build resumes after that ships.

**Spec handed to James:** `claude/spec-2026-07-27-pagerduty-api-gaps-for-v2.md` — full inventory of what exists plus the gap list.

## What v2 is waiting on

1. `urgency` dimension on the scrape (label `urgency="all"|"high"|"low"`) — blocks the 4 urgency-split MTTA/MTTR tiles.
2. `service_ids` filter/label — board is scoped to SentinelOne service `PG0FTPW`; team-level numbers mix in Auvik.
3. 15-minute scrape cadence (currently once daily 10:00 UTC, `window=1440`) + collector heartbeat metric.
4. Per-incident raw feed into VictoriaLogs (§4 of the spec) — blocks SLA Breaches and Incidents by Responder.
5. Confirm window semantics: `window=1440` at 15:40 UTC returned a range ending 2026-07-26T20:00Z (~20h lag). Deliberate or bug?

## Facts to reload on pickup (verified 2026-07-27)

- API routes live: `GET /pagerduty/teams`, `GET /pagerduty/metrics/incidents/teams`.
- Metrics land in **VictoriaMetrics** (`ff54vn5tei2o0d`), not VictoriaLogs. 29 `pagerduty_*` gauges, 58 series, job `pagerduty_team_metrics`, instance `localhost:7979`.
- Labels available today: `team_id`, `team_name` only. Teams: `P66WLWF` SOC, `P0KYTKC` Technology Management.
- `aggregate_unit=day` and `urgency=high|low` both work on the live route (verified).
- No `pagerduty` records in VictoriaLogs — only the API's own journald logs match the string.

## First step when work resumes

Re-run the discovery queries in the spec (§1) to confirm what James shipped, then decide the v2 data path (VM-only vs live Infinity vs hybrid) before copying the dashboard.
