# Review — PagerDuty → VictoriaLogs cutover readiness

**Verified:** 2026-07-31, ~22:00–22:30 UTC, against live VictoriaLogs, VictoriaMetrics, the Simvay API and the PagerDuty REST API.
**Subject:** James's handoff *"SOC Wallboard v2 — PagerDuty data via Simvay API"* (draft, 2026-07-27), and whether the SOC Wallboard can be re-pointed at VictoriaLogs now.

## Verdict

The cutover cannot proceed. VictoriaLogs contains no PagerDuty incident data of any kind, and the ingestion path that would put it there has never run. Separately, the handoff document is accurate on most points but wrong on one that would have silently mislabelled every time-bucketed panel on the board.

The endpoint James built is good work. Tested directly against the live API, `/pagerduty/incidents/raw` returns 24 of the 26 fields the gap spec asked for, paginates without loss, filters and sorts correctly, forwards upstream errors honestly, and reconciles to the record against both the aggregate route and PagerDuty's own REST API across 30 days and 1,116 incidents. It has one defect — a four-hour timestamp offset it shares with the metrics route — and it cannot show anything that has not yet resolved and settled upstream, which is a PagerDuty constraint rather than an API one.

The blocker is transport, not correctness. The data is right; nothing is carrying it.

## 1. What is actually in VictoriaLogs

Nothing PagerDuty-related. Queried across an unbounded time range on datasource `Simvay-Logs` (`bfd1yqs9tvlkwf`):

| Query | Result |
| --- | --- |
| `query_type:PagerDutyIncidents \| stats count()` | 0 |
| `incident_number:*` | 0 |
| `seconds_to_first_ack:*` | 0 |
| `urgency:*` | 0 |
| stream label values for `query_type` | `SentinelOneIntegration`, `SentinelOneAccounts` only |
| full-text `i("pagerduty")` | 31 records, all in the `simvayAPI.service` journald stream |

Those 31 journald lines are the API's own access log, and they are informative. Extracting the route from each shows that `/pagerduty/metrics/incidents/teams` has been called 30 times between 2026-07-22 and 2026-07-31T10:00:02Z, `/pagerduty/teams` once, and **`/pagerduty/incidents/raw` zero times, ever**. The n8n workflow described in the handoff has not been built, so the state is exactly as the handoff itself admits under "The per-incident path": not built, waiting on the VictoriaLogs insert URL. Nothing has changed since the 2026-07-27 status note.

The call pattern also confirms what *did* ship: one call per day through 2026-07-27, then three calls per day from 2026-07-28 onward. That is the G1 urgency triple-scrape going live.

## 2. What is live and working

The metrics path is in good shape. VictoriaMetrics now carries `pagerduty_collector_last_success_timestamp_seconds` alongside the 29 gauges, and the new series carry `urgency`, `window_minutes` and `service_scope` labels as promised:

```
pagerduty_total_incident_count{team_id="P66WLWF", team_name="Security Operations Center",
  service_scope="sentinelone", urgency="all|high|low", window_minutes="1440"}
```

The last scrape landed 2026-07-31T10:00:01Z and the three urgency variants are internally consistent (high 26 + low 57 = all 83). The older unlabelled series for `P0KYTKC` Technology Management still exist and still receive no urgency labels, which is what makes handoff Panel rule 4 correct — history will not join.

The `/pagerduty/incidents/raw` route *is* deployed. It appears in `openapi.json` with all eleven documented parameters plus an undocumented `time_zone`. Calling it works and returns rich per-incident records. So the API side is genuinely done; only the n8n hop is missing.

## 3. Accuracy: the raw feed reconciles exactly

This is the part worth trusting. For the UTC day 2026-07-30, values computed from 112 raw per-incident records were compared against the aggregate route called with an explicit, unsnapped range over the identical window:

| Measure | From per-incident records | From metrics route |
| --- | --- | --- |
| Incident count | 82 | 82 |
| High urgency | 29 | 29 |
| Low urgency | 53 | 53 |
| Acknowledged | 38 | 38 |
| Mean seconds to first ack (all) | 776.9 | 777 |
| Mean seconds to first ack (high) | 94.6 | 95 |
| Mean seconds to first ack (low) | 2975.6 | 2976 |
| Mean seconds to resolve | 2634.4 | 2634 |
| Business / off / sleep hour interruptions | 64 / 5 / 0 | 64 / 5 / 0 |

A second check against PagerDuty's REST API for 2026-07-31T00:00–12:00Z returned incidents 22102 through 22113, and the analytics feed contained all twelve, with no extras and no gaps. Two independent sources, exact agreement. The per-incident feed is the right foundation for the board.

Two structural facts fall out of this comparison and both matter for panel authoring. First, `mean_seconds_to_first_ack` is computed over acknowledged incidents only — 38 of 82, not 82 — which is why the aggregate and per-incident means agree only when nulls are excluded. Second, the `id` and `incident_id` fields are identical on every record and unique across the pull, so either works as the dedup key.

## 4. Where the handoff document is wrong

### Both routes compute "now" four hours in the past

This is the one real defect, and it is a single root cause with two visible symptoms.

The handoff states that with `window=1440` the end boundary snaps to midnight UTC and "the response always describes the previous full UTC day." It does not. Called at 2026-07-31T22:10Z, the metrics route echoed back its own filters:

```
filters.created_at_start = 2026-07-29T20:00:00Z
filters.created_at_end   = 2026-07-30T20:00:00Z
```

The boundary is **20:00 UTC**, not midnight, and it is consistent across every observation available: the same 20:00 boundary explains the 2026-07-27 measurement recorded in the original gap spec, and reconstructing the stored 2026-07-31T10:00Z sample (83 / 26 / 57) against the raw records identifies its window as ending 2026-07-30T20:00Z rather than 2026-07-31T00:00Z. Across all three data points the boundary is exactly *most recent UTC midnight minus four hours*.

The handoff also states that the per-incident route has "deliberately no boundary snapping." That is true as far as it goes — but `rolling_hours` inherits the same four-hour shift. Called at 2026-07-31T22:35:55Z, `rolling_hours=8` returned exactly one record: incident 22113, created at 11:46:41Z. That incident is 10.8 hours old, well outside a true eight-hour window, but sits inside a window starting at 10:35Z — precisely `now − 4h − 8h`. The same offset explains the earlier `rolling_hours=48` pull, whose oldest record was 51.8 hours old.

So the diagnosis is not two separate quirks. `now` is being resolved four hours behind UTC — the shape of an America/New_York offset applied to a naive timestamp — and the metrics route then additionally floors that already-wrong value to a day boundary. Fixing the timestamp handling fixes both routes at once.

The practical consequences on the metrics route are worse than four hours suggests. The scrape's "day" runs 20:00→20:00 UTC, which is 16:00→16:00 Eastern — it straddles two calendar days in both UTC and local time, so no panel can honestly be titled "yesterday" or bucketed by date. Because the boundary lands a further day back than midnight snapping would, the daily sample describes a period that ended 14 hours before the scrape and began 38 hours before it. A tile reading "last 24h" is describing roughly two days ago through yesterday afternoon.

On the raw route the impact is milder but still real: an n8n workflow polling `rolling_hours=48` will actually cover `now−52h` to `now−4h`, so it never sees the most recent four hours on any given pass. With a 48-hour overlap window and a 15-minute cadence those records get picked up on a later poll, so nothing is permanently lost — but the backfill and any window arithmetic in the workflow need to account for it.

Until this is fixed, any panel needing a defensible period must pass explicit `created_at_start` / `created_at_end`, which the document correctly states are honoured verbatim, and which the reconciliations in sections 3 and 8 confirm to the record.

### The heartbeat carries more labels than documented

The handoff says the heartbeat is "labelled with `urgency` only (no team labels)." In practice it carries `urgency`, `service_scope` and `window_minutes`, so three series exist. The document's Panel rule 3 expression returns three results rather than one and will render as a multi-value panel. It needs an aggregator:

```promql
time() - max(last_over_time(pagerduty_collector_last_success_timestamp_seconds[25h])) > 93600
```

### Fields the spec asked for arrive permanently null

Across all 112 records, `seconds_to_engage`, `seconds_to_mobilize`, `user_defined_effort_seconds` and `incident_type_id` are null on every single one. Two of those — `seconds_to_engage` and `seconds_to_mobilize` — were requested in §4.1 of the original gap spec as secondary timing for QBRs. They are present in the payload and empty, which is the worst combination: a panel built on them will show "No data" rather than fail loudly. Either PagerDuty does not populate them for this account's incident type, or they require a PD Advance feature. Worth one question to James before anyone builds against them.

### The document is silent on null acknowledgements, and that is the biggest accuracy trap

62% of records (69 of 112) have `seconds_to_first_ack` set to null and an empty `acknowledged_user_names` array. On 2026-07-30 the split is stark: all 29 high-urgency incidents were acknowledged, while only 9 of 53 low-urgency ones were. That is consistent with the operating model recorded in the project handoff — the SOC acknowledges low-urgency incidents only when actively working them, and the rest auto-resolve.

Three panels break in different ways if this is not decided explicitly:

The **SLA Breaches** tile is the sharpest. Treating a null ack as a breach yields 44 low-urgency breaches for 2026-07-30 against a 12-hour SLA; treating nulls as out of scope yields zero. High urgency is unaffected either way, with exactly one genuine breach past the five-minute SLA. A wallboard that reports 44 breaches on a day the SOC did nothing wrong will be ignored within a week, so the definition needs to be written down before the panel is.

**Incidents by Responder** covers only the 43 acknowledged incidents, and on 2026-07-30 resolves to Stevie Kantor 35, Gabe Lister 2, Shane Goodsite 1. The tile needs a title that says "acknowledged incidents", or it reads as a claim about all 82.

**Total Triage Time** is where the per-incident feed earns its keep. Computed exactly as Σ(`seconds_to_resolve` − `seconds_to_first_ack`) over acknowledged incidents, 2026-07-30 comes to 16,185 seconds — 4.5 hours. The means-based approximation the original spec floated as a fallback, (mean_resolve − mean_ack) × count, gives 42.3 hours. That is a **9.4× overstatement**, because the two means run over different denominators. This number must not be approximated.

### Timestamps arrive without a timezone marker

`created_at`, `resolved_at` and `updated_at` come back as naive strings — `2026-07-31T11:46:41`, no `Z`, no offset. The values are UTC (they line up exactly with the `Z`-suffixed timestamps PagerDuty's REST API returns for the same incidents), but nothing in the payload says so. Whatever writes these into VictoriaLogs as `_time` must append the offset explicitly. If n8n or VictoriaLogs interprets them in the host timezone, every record silently shifts by four or five hours and the day buckets will be wrong in a way that looks plausible.

### One minor contradiction to watch

On 2026-07-30, `auto_resolved` is true for all 82 records, yet `resolved_by_user_name` is populated on one of them (Stevie Kantor). Any "human vs auto resolve" tile needs to pick one field and stick to it. `auto_resolved` looks like the safer choice, but it is worth asking which one PagerDuty considers authoritative.

## 5. What is correct in the handoff

Worth stating plainly so it does not get relitigated. The `engaged_seconds` versus `total_engaged_seconds` correction is right — the per-incident payload carries `engaged_seconds` and no `total_engaged_seconds` at all, and the two would have been easy to conflate. Numeric fields do arrive as JSON numbers, so no `convertFieldType` gymnastics are needed. Explicit `created_at_start` / `created_at_end` are honoured verbatim and unsnapped. Records are idempotent by `id`, making overlapping pulls safe. The urgency, service-scope and window-minutes labels are live exactly as described, and Panel rule 4's warning about pre-2026-07-22 history not joining is correct. Panel rules 1, 2 and 5 all hold.

## 6. One correction to the current volume assumptions

The original spec sized the ingestion around ~110 incidents/day. Observed volume is lower: 59 on 2026-07-29, 82 on 2026-07-30, and 13 so far on 2026-07-31. Quota headroom is better than planned, which strengthens the case for the 15-minute cadence in the open decision.

## 7. Live tiles are not possible from this feed, at any cadence

PagerDuty Analytics only exposes incidents after they resolve *and* settle, and the settle lag is hours. Incident 22114 resolved at 16:53Z and was still absent from the analytics feed at 22:05Z — over five hours later. Incident 22115, triggered at 22:04Z and still open, is absent entirely, as is every unresolved incident: all 112 records in the 48-hour pull carry `status: resolved`.

So no amount of polling makes this feed current. The 15-minute cadence in the open decision improves the heartbeat and makes rolling figures summable, both real wins, but it will not make the board show what is happening now. Anything on the wallboard that needs to be live — open incidents, in-triage counts, time since last alert — has to stay on the SentinelOne VictoriaMetrics series or move to PagerDuty's REST API, which does return open incidents immediately. That distinction should be stated on the board itself, otherwise a quiet-looking panel will be read as "nothing is happening" when it means "nothing has settled yet."

## 8. Does the endpoint itself pull the right information?

Yes. `/pagerduty/incidents/raw` was exercised directly against the live API across seven dimensions, including the three checks James listed as unproven in his own verification status. Six pass cleanly; the seventh is the timestamp defect in section 4.

**Field coverage.** Of the 26 fields the original gap spec asked for in §4.1, 24 arrive fully populated. One is a rename James already documented — `total_engaged_seconds` does not exist on the per-incident route, `engaged_seconds` does, and `total_engaged_seconds` is confirmed present on the aggregate route (188,984 seconds across July), so the two really are different fields on different endpoints. The remaining two, `seconds_to_engage` and `seconds_to_mobilize`, are present in the payload but null on every record, as covered above. The endpoint also returns 26 fields nobody asked for, including `escalation_policy_name`, `priority_order`, `joined_user_names`, `reassignment_count`, `timeout_escalation_count`, `active_user_count` and `status` — useful headroom for QBRs.

**Pagination integrity** (James's check 1). The same window pulled at `limit=1000` and at `limit=2` returns byte-identical incident-number sets — 12 records, no duplicates, no drops, ordering preserved across page boundaries. At scale, a 30-day pull returned 1,116 records with 1,116 unique ids across two pages. Cursor pagination is sound.

**Error forwarding** (James's check 2). A deliberately invalid `service_ids` value surfaces as an upstream **400 Bad Request**, not a proxy 500. Separately, a burst of test calls tripped PagerDuty's rate limiter and the proxy forwarded a genuine **429 Too Many Requests** rather than swallowing it into an empty 200. Both behave as the handoff claims.

**Backfill accuracy** (James's check 3, effectively). The doc proposed checking a 90-day backfill against PagerDuty Insights. A stronger internal check is available: pulling 2026-07-01 through 2026-07-31 through both routes over an identical explicit window gives

| Measure | Per-incident route | Aggregate route |
| --- | --- | --- |
| Incident count | 1,116 (1,116 unique ids) | 1,116 |
| High urgency | 287 | 287 |
| Acknowledged | 467 | 467 |
| Mean seconds to first ack | 403.79 | 404 |
| Mean seconds to resolve | 1,063.46 | 1,063 |
| Business hour interruptions | 913 | 913 |

Zero drift across 30 days and 1,116 records. The backfill will be accurate.

**Filters.** `urgency=high` and `urgency=low` return 29 and 53 records for 2026-07-30, every record correctly labelled, summing exactly to the 82 returned unfiltered. `service_ids` and `team_ids` both apply. Worth noting for the G2 concern: querying team `P66WLWF` for 2026-07-30 *without* a service filter still returns 82 records, all SentinelOne — Auvik sits on a different team, so the service-scope contamination the gap spec worried about does not appear in this team's numbers today. It is still right to filter by service, since that stops being true the moment another service is attached to the SOC team.

**Ordering.** `order_by=seconds_to_resolve` with `order=desc` returns a correctly sorted descending series. The non-default sort key works as documented.

One operational note: exercising these tests consumed roughly 25–30 PagerDuty Analytics calls and tripped the per-minute limiter once. That is a useful data point in itself — the limiter is easy to hit during development, which is exactly why the wallboard must not query PagerDuty live.

## 9. Ask list for James

Ranked, with the blocking item first.

1. **Build the n8n workflow** — it is the only thing standing between the current state and the cutover. It needs the VictoriaLogs insert URL, which was James's to provide. Nothing else in this review blocks it.
2. **Fix the four-hour timestamp offset.** It affects `window` on the metrics route and `rolling_hours` on the raw route, and it is almost certainly one line of timezone handling. Fixing it changes stored values, so it should land before panels are written against them.
3. **Decide the null-ack contract** for SLA Breaches: is a never-acknowledged low-urgency incident a breach, or out of scope? The wallboard cannot ship without an answer.
4. **Confirm the timestamp timezone** and have the ingestion append an explicit offset before writing `_time`.
5. **Confirm whether `seconds_to_engage` / `seconds_to_mobilize` will ever populate**, or drop them from the spec.

Once the workflow lands, the first verification should be re-running the section 3 reconciliation against VictoriaLogs rather than against the API — same day, same window, same seven numbers. If they match, the cutover is safe.
