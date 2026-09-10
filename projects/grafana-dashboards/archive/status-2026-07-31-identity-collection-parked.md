# Status — identity collection reviewed, pipeline changes handed to James (2026-07-31)

Read-only investigation of the n8n identity pipeline. **Nothing was changed** — no workflow saved, activated, or executed; only read/query endpoints called. Detection and dashboard work is **parked pending James's pipeline changes**.

## What happened

Ryan reviewed the n8n instance (`10.10.99.13:5678`) to understand the identity enrichment path and find where Microsoft device context should plug in. The investigation widened once it became clear the data was being dropped rather than missing.

## Docs produced

| Doc | Purpose |
|---|---|
| `claude/review-2026-07-31-n8n-identity-enrichment.md` | Full pipeline review — inventory, node-by-node, all findings |
| `claude/spec-2026-07-31-identity-collection-fields-and-dedup.md` | Field inventory for both sources + dedup/cadence design |
| `claude/handoff-2026-07-31-identity-pipeline-for-james.md` | **The actionable list for James**, with acceptance checks |

## Findings that changed the picture

1. **ip-api enrichment is not in n8n.** It lives in the Simvay API (`10.10.100.8:8000`); `enrich` defaults to `true` on both `/duo/authlogs` and `/sentinelone/datalake/queryall`. n8n only moves already-enriched records.
2. **Microsoft device context is already collected** — `unmapped.DeviceProperties` (device GUID, DisplayName, OS, BrowserType, IsCompliant, TrustType, SessionId) — but it never reaches an alert. `Identity Alert Hook` builds its OCSF finding purely from Grafana labels, and those 13 labels contain no device fields. All 4 executions ever were Duo-sourced.
3. **Entra has no auth device.** One device per record, and it is the source device. Richer than Duo on every dimension (100% geo vs 0%, 96% browser, 97% compliance) but there is no second endpoint. Duo stays the only source for workstation-vs-2FA geo comparison.
4. **Duo is dropping ~50% of events** to an unset `limit` (defaults to 100). 118 events/hour returned by default vs 237 with `limit=1000`.
5. **We collect 9 of 66 available Entra fields**, and 303 failed logins/day are excluded entirely by two independent filter clauses.
6. **We enrich a Microsoft-owned IP instead of the client IP.** `src_endpoint.ip` carries the real client and is discarded. This is the root cause of the Canada false positives worked around on 2026-07-27 in panels 13, 15, 20, 30, 31.
7. **~1.1M records/day are pushed to store ~1,650.** The parser at `:9001` is silently absorbing a ~700× write amplification and is the only thing keeping VictoriaLogs clean. Duo does not pass through it.

## Corrections to earlier notes

- **Entra does have a success/failure field** — `status_id` / `status_detail`, 100%/97% coverage. This corrects finding #10 in `claude/status-2026-07-27-1080p-fit-and-anomalous-logins.md`.
- `device_attributes` is **not** dropped by the parser — it lands intact but as an unparsed JSON string, which is why nothing can query it.
- `trusted_endpoint_status` is 97% `unknown`, not 100% — 601 `trusted` and 62 `not trusted` exist over 7 days.

## Resume conditions

Detection work starts when acceptance checks 1-5 in the handoff doc pass:

1. Duo 24h volume ~5,700 (from 3,098)
2. Duo `txid` unique = total
3. `src_endpoint.ip` present on Entra records
4. `device.is_compliant` queryable
5. `unmapped.LogonError` landing, ~300/24h

Then, in order: password spray / lockout detections off `IdsLocked` (83/day) and `UserDisabled` (25/day); device-trust signals; delete the Microsoft exclusion from the five Grafana panels; extend `Build Alert` with device `related_events` once the Grafana rules emit device labels.

## Carried forward, unchanged

- `claude/spec-2026-07-27-duo-access-device-geo-enrichment.md` — enrich Duo `access_device.ip`, emit lat/lon as numbers. Still the blocker for travel-line arcs on the map TV.
- Duo `email` coverage is 20% in VL (7.6% in a fresh API sample); the rest carry only `user.name`. Caps any Duo↔Entra correlation at ~20% of the Duo side until resolved.
