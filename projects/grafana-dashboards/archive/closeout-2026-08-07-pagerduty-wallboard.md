# Closeout — PagerDuty → VictoriaLogs → SOC Wallboard v2 (2026-08-07)

Spot check run 2026-08-07 ~01:40 UTC, six days after the pipeline went live. One real defect found and fixed; two things that looked broken and were not.

## The heartbeat defect — fixed

The collector heartbeat recorded exactly one beat, on 2026-08-01T17:55:48, and never again, despite the workflow running successfully every fifteen minutes for six days.

Cause: **this n8n instance separates a workflow's draft from its published version, and scheduled runs execute the published one.** The heartbeat was added through a REST `PATCH` after the workflow had already been published, so it only ever existed in the draft. The manual run that "proved" it worked on 2026-08-01 executed the draft, which is exactly why it looked fine at the time. Inspecting execution 283855 confirmed it: the executing `Batch for Vector` node did not contain the heartbeat code at all.

Fixed by publishing the draft as "v2 - collector heartbeat". Verified on the 01:45 scheduled run, not a manual one: the heartbeat count went to 2 with `last_beat` 2026-08-07T01:45:48.933Z. That write also proves the whole chain — n8n through Vector into VictoriaLogs — is alive, which is a better health signal than any process check.

Worth carrying forward: any future edit made through the REST API needs an explicit publish, and the tell is the orange dot on the Publish button. Nothing else drifted — the rolling window, batching and normalisation were all in place before the first publish, and the executing version pulls 60 records and batches them correctly.

## Missing 2026-08-06 data — not a defect

VictoriaLogs holds nothing created on 2026-08-06; its newest incident is 2026-08-05T18:12. PagerDuty's REST API shows roughly 78 incidents on 08-06, numbers 22395 through 22471.

That gap is upstream and expected. Querying the Analytics route directly with an explicit `created_at_start=2026-08-06T00:00:00Z` range returns **zero records** — PagerDuty Analytics has not settled that day yet. The rolling 48-hour pull correctly returns 60 records ending 2026-08-05T18:12, which is everything Analytics currently exposes.

The settle lag is longer than the five hours measured on 2026-08-01; it is currently running somewhere between 12 and 36 hours. The daily 14-day deep sweep exists precisely for this and will recover 08-06 once Analytics catches up. This is also why the trend panel visibly stops short of "today" — that is the data being honest, not the panel being broken.

**Confirmed self-healed the same night.** By 04:25 UTC, 2026-08-06 held 77 incidents in VictoriaLogs against the ~78 counted from PagerDuty's REST API, and the newest record was 2026-08-06T23:42:41 — incident 22471, the newest one PagerDuty had. Analytics settled, the collector picked the day up on its own, and no intervention was needed. The heartbeat reached 12 beats by 04:15, firing on every fifteen-minute run.

## X-axis date format — fixed

The two time series disagreed on their x-axis format because each carried a different `byType: time` unit override. "Alert Volume Over Time" used `time:ddd HH`, which renders a weekday and an hour — that is the "Fri 00" that looked like a broken date. "MTTA / MTTR Trend" used `time:MM/DD`.

Both are now `time:ddd MM/DD`, rendering "Sat 08/01", "Sun 08/02" and so on. That keeps the weekday cue, which is genuinely useful for spotting weekend dips in alert volume, and adds the date that was missing.

One tradeoff worth knowing: an explicit format does not adapt to zoom the way Grafana's automatic formatting does. At the board's fixed seven-day window it is correct, but zooming into a few hours in the editor would show the same date on every tick. Removing the override entirely would restore adaptive behaviour at the cost of the weekday label.

## Deep sweep timing — not a defect

The sweep was configured for 04:20 and fires at 08:20 UTC. n8n schedule triggers use the instance timezone, which is America/New_York, so it runs at 04:20 Eastern. That is arguably what you would want anyway. It fired once in the last 24 hours, at 2026-08-06T08:20:13, and that run is what wrote the most recent records.

## Health at closeout

100 executions in the preceding 24 hours, every one successful. VictoriaLogs holds 4,152 unique incidents in 7,612 rows, the expected roughly 1.8 revisions per incident. Streams split SentinelOne 3,738, Auvik 397, Cyber Infra 17 — the last still leaking through the API's service filter at about 0.4%, unchanged and still handled by filtering on service in every panel.

Every tile returns sane values over the trailing seven days: 290 incidents, high MTTA 54.1 s, high MTTR 10.7 min, low MTTA 14.4 min, low MTTR 48.8 min, total triage 22.9 h, 1 SLA breach, interruptions 161 business / 39 off / 9 sleep, responders Stevie Kantor 57 and Shane Goodsite 46. Collector heartbeat reads "a minute ago".

## Known and accepted

The four-hour timestamp offset in the Simvay API is still unfixed and still needs James. The ingest works around it with a 48-hour window plus the daily sweep, so nothing is lost, but it remains the one outstanding upstream bug.

Nothing on this board can be live. Analytics only exposes resolved, settled incidents, so the most recent day or two will always be sparse. Open Alerts, In Triage and Time Since Last Alert stay on the SentinelOne VictoriaMetrics series for exactly this reason.

The heartbeat is emitted from inside the batching node, so a pull returning zero records would produce no beat. With a 48-hour window that has not happened and is unlikely to, but moving it to its own branch off the trigger would close the gap properly.

Two test artifacts remain in their own streams and will age out with retention: `PagerDutyIncidentsTEST` (47 rows) and `PagerDutyArrayTest` (2 rows). Neither can contaminate a `PagerDutyIncidents` query.

## Remaining work

Promotion: move v2 out of the Testing folder, set the kiosk URL on the TV, retire `soc-wallboard-draft`. And the dashboards-as-code export to git, still not started and now more valuable than ever, since the board's queries are where the SLA definitions actually live.
