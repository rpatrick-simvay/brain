# Status — SOC Wallboard v2 built and rendering (2026-08-01)

**Dashboard:** `soc-wallboard-v2` — "SOC Wallboard v2 (Draft)", Testing folder, version 4.
**Old board:** `soc-wallboard-draft` untouched at v33. Both can run side by side on the TV.
**Default window:** now-7d, refresh 5m. Seven days is entirely post-2026-07-17, so the MTTR semantics change at the cutover never enters the default view.

## What changed

All nine PagerDuty-derived tiles now query the VictoriaLogs per-incident feed directly. The shared-query architecture is gone: panel 1 used to hold the single Infinity call to PagerDuty and eight other panels consumed it through `-- Dashboard --` with filterByValue / groupBy / calculateField chains, purely to stay under the daily API quota. VictoriaLogs has no quota, so each tile owns its query and roughly twenty transforms were deleted.

The four SentinelOne tiles — Alert Volume, Open Alerts, In Triage, Time Since Last Alert — still read VictoriaMetrics and were not touched. They have to stay there: PagerDuty Analytics only exposes incidents after they resolve and settle, so nothing live can come from the incident feed.

The `pagerduty_*` VictoriaMetrics gauges are deliberately unused. They still carry the four-hour offset, so their "day" runs 20:00→20:00 UTC, and they cannot express urgency-split triage time. Everything they were meant to feed now comes from VictoriaLogs instead, which sidesteps that bug entirely rather than working around it.

## SLA rules as implemented

Hard thresholds, per Ryan: high urgency 5 min MTTA and 1 h MTTR; low urgency 12 h MTTA and 24 h MTTR.

The judgement call was what to do with an incident that was never acknowledged, which is 62% of them. The rule implemented: a high-urgency incident resolved without an ack is acceptable only if it resolved inside the 5-minute MTTA window — anything slower is a breach. Low-urgency non-ack is normal operating procedure and is not an MTTA breach, but low urgency is still assessed on MTTR.

Against 2026-07-17 → 08-01, 658 incidents:

| Condition | Breaches |
| --- | --- |
| High, acked, MTTA > 5 min | 2 |
| High, never acked, resolved > 5 min | 7 |
| High, MTTR > 1 h | 5 |
| Low, acked, MTTA > 12 h | 0 |
| Low, MTTR > 24 h | 0 |
| **Distinct incidents breaching any rule** | **14** |

Of the 21 unacknowledged high-urgency incidents in that window, 14 auto-resolved inside five minutes and were correctly excluded.

## TRIAGE priority is not a problem

Zero TRIAGE-priority incidents exist across the whole 90-day backfill. Priorities are CRIT 20, HIGH 381, MED 348, LOW 1283, INFO 1445. The pre-cutover design does not contaminate the data as ingested. The reason to keep the default window recent is the MTTR semantics change on 2026-07-17, not the priority.

## Collector heartbeat added

The freshness tile initially showed "39 minutes ago" while the workflow was running fine every 15 minutes. Both the 17:30 and 17:45 runs succeeded; they simply produced no new records because Vector deduplicated everything, so nothing was written. A tile reading last-write-time would have shown a healthy collector as dead during any quiet period — precisely the "absent must not be read as zero" trap in the original handoff.

The workflow now emits one heartbeat record per run into its own stream, `query_type="PagerDutyCollectorHeartbeat"`, with a per-run unique `payload_hash` so Vector never deduplicates it. It carries `records_pulled` and `batches_sent` for diagnostics. The tile reads that stream and is independent of whether any incident changed.

One caveat worth knowing: the heartbeat is appended inside the batching node, so it only fires when the pull returns at least one record. With a 48-hour window that is effectively always, but a true zero-record pull would produce no heartbeat. Moving it to its own branch off the trigger would close that gap.

## Panel query pattern

Unchanged from the implementation record and still the thing to get right: VictoriaLogs holds one row per revision, so every aggregate reduces by `id` first.

```logsql
query_type:PagerDutyIncidents service_name:SentinelOne acknowledged:=true
| stats by (id) max(seconds_to_first_ack) as a
| stats avg(a) as mtta
```

Two Grafana specifics learned building this. Instant queries return their result inside a `labels` object, so every stat tile needs `extractFields(source:"labels", replace:true)` followed by `convertFieldType` to number. And a `displayName` override in `fieldConfig.defaults` renames the field *before* `reduceOptions.fields` matches against it — that silently blanked the Total Triage tile until the selector was set to all-numeric-fields instead of a name regex.

The trend panel uses `statsRange` rather than `instant`. The instant form with explicit `_time:1d` buckets is strictly more accurate per calendar day, but Grafana would not coerce the resulting `_time` string into a time field; `statsRange` returns clean named MTTA and MTTR frames with no transforms at all. The panel was retitled from "Daily MTTA / MTTR Trend" to "MTTA / MTTR Trend" to stay honest about the bucketing.

## Verified on screen

Every tile renders with plausible values at a 7-day window: High MTTA 1.10 min, High MTTR 8.09 min, Low MTTA 22.7 min, Low MTTR 41.8 min, Total Triage 13.7 h, SLA Breaches 2, interruptions 132 business / 13 off / 0 sleep, responders Stevie 85 / Gabe 7 / Shane 2 / James 1, heartbeat "a minute ago".

## Next

Promotion is the remaining work: move v2 out of the Testing folder, set the kiosk URL on the TV, and retire `soc-wallboard-draft` once the numbers have been watched side by side for a few days. The dashboards-as-code export to git is still not started and is now more valuable than before, since this board's queries encode the SLA definitions.
