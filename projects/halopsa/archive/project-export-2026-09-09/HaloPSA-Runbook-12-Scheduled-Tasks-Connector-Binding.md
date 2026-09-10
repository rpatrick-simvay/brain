# Simvay — Runbook 12: Scheduled Tasks × MCP Connector Binding

> **Purpose:** Root-cause record and standing rules for why custom MCP connectors
> (the self-hosted Cloudflare Workers: HaloPSA, Action1, SentinelOne) went missing from
> scheduled Claude sessions, and how every scheduled task must be created from now on.
>
> **Diagnosed:** 2026-08-12 (Ryan Patrick + Claude) · **Last updated:** 2026-09-02
> · **STATUS: THE ATTENDANCE MODEL IS FALSIFIED (§13.1). On 2026-08-24 the three Workers were
> absent through a full 30-minute rebind ladder, a halt notification was sent, and they then bound
> ~4 minutes later — in an unattended session, with no human engagement, no task edit and no new
> schedule boundary. Binding is neither a per-task property (killed 08-14) nor a time-of-day
> property (killed 08-17) nor gated on attendance (killed 08-24). Best surviving model: a slow,
> session-independent attach that sometimes completes late. See §2 and §13.1.**
>
> **2026-08-31: THE LADDER FINALLY CAUGHT ONE.** The Morning Brief's second retry (~T+30) returned
> the Workers BOUND, in an unattended session, with no halt notification sent and no human
> involved. See §13.1 and §13.2.
>
> **2026-09-01: AND MISSED THE NEXT ONE.** Same trigger, same ladder, one day later — absent at
> T+0, T+15 and T+30, all three ToolSearch-confirmed. Halt sent 10:47Z. Bound instantly on Ryan's
> "try now". See §13.1.
>
> **2026-09-02: BOUND AT T+0 — THE FIRST CLEAN ZERO-WAIT UNATTENDED BIND ON THIS TRIGGER.** The
> Morning Brief's very first `RefreshMcpTools` returned all nine servers with the full 68 Worker
> tools. No ladder, no sleep, no halt, no human. **This is a new low end for the distribution —
> the observed unattended bind latency is now 0 to >30 minutes, not 30–37 — and it removes the
> last reason to think the delay has a floor.** See §13.1 and §2.
>
> **REPORT FILING CHANGED 2026-08-24 (evening).** Ryan's decision: reports are exported by joining
> a local folder to the session. The SharePoint upload path is retired for the three binary jobs and
> demoted to a fallback for the Morning Brief. All four prompts were rewritten the same evening.
> See §14 (rewritten) and §14.3 (corrected — the earlier "structurally impossible" write-up was
> too strong and is now fixed).
>
> **§5.1's UNTESTED RISK IS RESOLVED (2026-08-24):** `update_trigger` patches the message event in
> place and does NOT rebuild the events array. Auto-approve survived four consecutive prompt edits.

## 1. Symptom

Scheduled runs on 2026-08-06 and 2026-08-12 (~06:23 ET) were missing ALL tools from the
three custom connectors — not failing, entirely absent from the MCP server table — while
PagerDuty, Microsoft 365, Canva, Plaud and Cloudflare bound normally in the same runs.
Interactive sessions always had all 8. The daily Morning Brief silently lost its entire
HaloPSA half.

**Recurred 2026-08-13 morning on the rebuilt task.** See §7. **Did NOT recur on the
2026-08-13 afternoon run of the second rebuild.** See §9. **Recurred again 2026-08-14
morning on that same unchanged task.** See §10. **Recurred again 2026-08-17 morning —
then self-corrected mid-session when Ryan engaged.** See §11. **Recurred again 2026-08-24
on BOTH morning jobs.** See §13.1. **Recurred again 2026-08-25 — halted at T+30, no recovery.**
**Recurred again 2026-08-26 — halted at T+30, then bound 5/5 on Ryan's reply.**
**2026-08-31: absent at T+0 and T+15, then PRESENT at the T+30 retry — inside the ladder,
unattended, no halt.** **2026-08-31, Weekly Ops Reports (fired 10:10Z): absent through all three
rungs, halted, bound on Ryan's reply.** **2026-09-01: Morning Brief absent at all three rungs,
halted 10:47Z, bound instantly on Ryan's "try now".** **2026-09-02: DID NOT RECUR — bound at the
first probe, unattended.** See §13.1.

## 2. Root cause — current best model (rewritten 2026-08-24, extended 08-26, 08-31, 09-01, 09-02)

**Binding is a slow, unreliable attach that is evaluated per firing and can complete
immediately, minutes into the session, or not at all. Nothing the task or the operator controls
appears to gate it.** Three successive models have each been killed by a single observation:

| Model | Fitted | Killed by |
|---|---|---|
| Per-task capture at creation time (08-12) | the UI-created v3.3 job, GitHub #63233 | §9→§10: same unchanged trigger bound 5/5 then 2/5 |
| Time of day / morning contention (08-14) | seven consecutive firings | §11.4: recovery at 10:35Z, inside the "always fails" window |
| **Session attendance (08-17)** | **five unattended failures, three attended successes** | **§13.1: bound at ~10:50Z on 08-24 in an unattended session, no engagement** |

What survives all of it:

- The three Workers behave as a unit. They are absent together and they arrive together,
  in every observation on file. Directory connectors (PagerDuty, M365, Canva, Plaud,
  Cloudflare, claude-code-remote) have bound on **every single run without exception.**
- The attach is **re-evaluated over the life of a session**, not fixed at session start.
  A table read at T+0 is a snapshot, not a verdict, and §13's ladder is right to keep re-checking.
- Elapsed time alone does not guarantee it. 08-24 waited thirty minutes for nothing and bound at
  ~34; 08-25 and 08-26 waited the same thirty and were still absent; 09-01 waited the same
  thirty and was still absent, then bound the moment a human typed.
- **CORRECTED 09-02 — the bind time has no floor.** The previous claim that it "clusters around
  T+30–T+37 unattended" is now falsified at the low end: **09-02 bound at T+0, unattended, first
  probe.** Six unattended data points on the Brief's trigger now read: 08-24 bound ~T+34, 08-25
  unknown (stopped looking at T+30), 08-26 not bound by T+30, 08-31 bound at T+30 exactly, 09-01
  not bound by T+30, **09-02 bound at T+0**. The distribution is bimodal-looking — either it is
  there at once or it is not there for half an hour — and there is no safe latency to design
  around. **This does not weaken §13.2; it strengthens it**, because a run that has not bound by
  T+0 is now known to be in the slow mode, where the tail runs well past where the ladder stops.
- **The window looks account-wide, not per-session** (08-31 Ops/Brief pair: one session absent at
  10:41Z, the other bound at ~10:46Z).
- Human engagement is **correlated with** binding (6/6 attended successes) but is **not necessary**
  for it (08-24, 08-31, **09-02**). It may shorten the wait; it is not the gate.
- **An attended bind can be instantaneous** (08-26, 08-31 Ops, 09-01). Attended bind latency spans
  0–13 minutes. **Unattended latency now spans 0 to >30.**

**Explicitly ruled out throughout:** connector *type* as an absolute blocker; per-user
OAuth records; Worker cold start; expired credentials; Worker outage. **Note 08-31:** the
GitHub fine-grained PAT named "Claude Cowork - MCP repo" expired 2026-08-29, i.e. two days
before a firing that bound perfectly well. Whatever the PAT gates, it is not Worker binding.

**Fingerprint that identified the split:** `ListConnectors` shows
`directoryUuid == installedServerId` for custom connectors, different UUIDs for directory
connectors — useful for telling custom from directory, but not the binding gate.

## 3. The standing rule

**Create every scheduled task with `mcp__claude-code-remote__create_trigger` from a live
Cowork session in which the needed connectors are bound. Never create or re-create jobs
through the UI scheduling flow if they need HaloPSA, Action1 or SentinelOne.**

Necessary but not sufficient — no creation-time choice controls the attach (§2).

**NO UI EDITS, EVER (added 2026-08-13) — with ONE sanctioned exception (2026-08-20):** do
not change a scheduled task through the claude.ai/Cowork UI — not the model, not the
schedule, nothing. Every change goes through `update_trigger` from a Cowork session.
The exception is **approval mode**, which exists nowhere else (§5.1).

**Model policy (Ryan, 2026-08-13):** Daily Morning Brief runs **claude-opus-5**; Weekly
Renewals, Weekly Ops Reports and Monthly Sales Report run **claude-fable-5**.

When a job's prompt or schedule needs changing, use `update_trigger` — it is now proven
safe for auto-approve (§5.1). If a job must be re-created, do it from a session with all
connectors attached, verify the new trigger, then pause (don't delete) the old one.

## 4. Detection — never let this be silent again

Every recurring prompt opens with a STEP ZERO binding check. **The full current procedure
is §13; the numbered detection facts below are its inputs.**

1. `RefreshMcpTools` with no argument → read the server table.
2. **Server ABSENT from the table = not bound at this moment** — *at this moment* is the
   load-bearing part. Absence is not a terminal state (§13.1). Never advise recreating the
   task; recreation was tried twice (08-12, 08-13) and did not hold.
3. **Server PRESENT but erroring = possible Worker cold start.** Refresh that server by
   name, re-probe, sleep 20s, re-probe — 3 attempts max — before declaring it down.
   **08-31 variant worth knowing:** Microsoft 365 came back `status:"not_connected"` with
   `error: server connection state is "pending"` at T+0 and was fully `refreshed` (41 tools)
   by T+15 with no intervention. A *directory* connector reported as pending is a transient
   the ladder absorbs for free — do not treat it as a degraded source.
4. **§9.1: a server listed with `status:"error" / "Not connected"` is NOT evidence of
   anything.** Always fire the real probe tool and let the probe decide.
5. **§10.1: re-run `RefreshMcpTools` after any mid-run MCP disconnect/reconnect churn
   before concluding absence.** One table read is not a finding.
6. **§11.1: `ToolSearch` is a cheap second opinion on absence.** A keyword search returning
   "No matching deferred tools found" independently confirms the server was never attached.
   **It is equally good at confirming arrival** — the deferred-tool notice naming the Worker
   tools has been the first sign of the bind on 08-24, 08-26, 08-31 and 09-01 alike. On 08-31
   that notice arrived *inside a `sleep 450` Bash call*; on 09-01 it arrived inside Ryan's reply
   turn itself. **09-02 note: on a T+0 bind the notice arrives attached to the very first
   `RefreshMcpTools` result, so the deferred-tool listing and the server table agree from the
   start — nothing special to do, but it is what a clean run looks like.**
   **The `select:` form is the sharpest version** —
   `ToolSearch "select:mcp__HaloPSA__get_agents,mcp__Action1__get_me,mcp__SentinelOne__list_clients"`
   confirms or denies all three Workers in one call.
7. **§11.4 — the notification is a callback, not a eulogy.** A halted run's notification
   must tell Ryan that opening the session and typing anything may bind the Workers and
   that a one-word reply is enough. Vindicated 08-26, 08-31 (Ops) and 09-01. **Also report
   a bind that RECOVERED inside the ladder, or one that never needed the ladder at all
   (§13 step 6) — 09-02 reported "all five bound on the first check, no retries" and that is
   the correct behaviour.**

## 5. Task inventory (current as of 2026-08-24 evening)

| Job | Trigger (ENABLED) | Model | Schedule | Export |
|---|---|---|---|---|
| Daily Morning Brief **v3.6** | `trig_01PsbrBqfBMNtg2gkNPeJequ` | claude-opus-5 | weekdays 10:15Z | local folder → OneDrive fallback |
| Weekly Renewals **v2.4** | `trig_017dsq6X7wS6s9BLvdpFargE` | claude-fable-5 | Mon 10:10Z | local folder only |
| Weekly Ops Reports **v4.3** | `trig_014nHSw3WiL4yLEobbtpNJYd` | claude-fable-5 | Mon 10:10Z | local folder only |
| Monthly Sales Report **v3.3** | `trig_0143X2LEwHMUYFVFYGn25XUT` | claude-fable-5 | 1st 11:00Z | local folder only |
| Weekly SOC Tuning Report **v2.0** | `trig_013sabPbC9cvjV3ziixGDNTP` | (as created) | Mon 08:00Z | **its own flow — DO NOT TOUCH** |

**The SOC Tuning task was migrated to a new flow on 2026-08-24 (Ryan).** v1.0
(`trig_0155GRyZhLcmBPjEmZoHWvYv`) is now PAUSED; v2.0 is a new trigger with a single event
(no `set_permission_mode`, so no auto-approve) and a 5,051-character prompt of its own. It is
**excluded from every change made to the other four**. Do not edit it, do not fold §13.2 into it,
and do not "fix" its filing.

Note: the version number in a task's NAME is the scheduled-task generation. It is
independent of the SPEC version inside the referenced runbook. Do not renumber output filenames
when bumping a task name.

The four report prompts carry the §13 STEP ZERO and, since 2026-08-24, the export block in §14.
Notifications push+email on all four.

### 5.1 Auto-approve — how it is stored, and the risk now RESOLVED

Ryan asked for auto-approve on all jobs. **It cannot be set from the MCP surface** — neither
`create_trigger` nor `update_trigger` exposes an approval/permission-mode parameter. Ryan turned
it on in the Cowork UI on 2026-08-20 ~19:04–19:05Z.

**How it is stored.** Enabling auto-approve PREPENDS a second event to `job_config.ccr.events`,
ahead of the prompt event:

```json
{"data": {"type": "control_request",
          "request": {"subtype": "set_permission_mode", "mode": "auto"},
          "request_id": "set-perm-mode-<hex>",
          "uuid": "<uuid>"}}
```

So an auto-approve task has `events` of length 2, and **the prompt is not `events[0]`** — see §6.

**RESOLVED 2026-08-24 — `update_trigger` is safe.** It **patches in place**. Four consecutive
`update_trigger` prompt rewrites each returned `events` of length 2 with the
`set_permission_mode` control_request still at index 0, and `derived_state:
{"permission_mode": "auto"}`.

**Keep the verification step anyway** — it costs one field in the response. After any
`update_trigger`, confirm `derived_state.permission_mode` is still `auto` and the control_request
is still present. If it ever is not, Ryan has to re-toggle it in the UI.

## 6. Techniques learned (for future scheduled-task debugging)

- `list_triggers` returns each trigger's full `job_config` incl. the stored prompt.
  **Do NOT hard-code `events[0]`** — the prompt sits at `events[1]` on auto-approve tasks.
  Always search: `[e['data']['message']['content'] for e in ccr['events'] if 'message' in e['data']]`.
  Output is ~120 KB and exceeds the tool-result ceiling — it is written to a tool-results file.
  Parse it with `json.load` in python (`d['data']` is a list of triggers), never inline, and never
  with Read's offset/limit (the file is one long line).
- **`update_trigger` echoes the full stored trigger back**, including the rewritten prompt and
  `derived_state`. That response is the cheapest possible verification.
- **Verify prompt edits by diffing flags, not by eye.**
- A scheduled probe can report back through **M365 email** (`outlook_send_mail`) since directory
  connectors bind headless — then the interactive session reads the mailbox.
- GitHub refs: #63233 (UI cannot attach custom connectors), #43397 (connector init delays in
  autonomous tasks), #40835 (creating a task disabling connectors in other tasks). **#43397 remains
  the leading candidate** — "connector init delays in autonomous tasks" is precisely what an
  intermittent 0-to-35-minute unattended attach looks like.

## 7. 2026-08-13 morning — the FIRST rebuild did NOT fix it (regression record)

**FAILED.** `Daily | Morning Brief v3.4` fired (`last_fired_at 2026-08-13T10:23:11Z`) and
STEP ZERO found **HaloPSA, Action1 and SentinelOne absent**. Only PagerDuty and Microsoft
365 bound; both answered on the first probe. The brief shipped partial.

v3.4 was `created_via: meta_mcp`, created `2026-08-12T21:28:57Z` from an interactive
session that had all connectors bound — precisely what §3 prescribes.

### 7.1 The 08-12/08-13 config strip

Diffing `list_triggers` snapshots from 2026-08-12 21:05Z against 2026-08-13 13:38Z:
`job_config.ccr` lost `environment_id`, `session_context` and `tags`, retaining only
`events` — across **every** fresh-session trigger on the account. `send_later` self-bind
triggers were spared. Ryan had made a **UI edit** to the daily job on the evening of 08-12,
matching GitHub #40835's pattern.

**Reconfirmed 08-14, 08-17, 08-20, 08-24, 08-31, 09-01 and 09-02:** the missing `session_context`
is a *response-shape* change, not a functional one. Absence of `session_context` is **not** a
usable predictor of whether a task will bind. Only a live probe is. **09-02 is the cleanest
demonstration: same stripped config as every failing run, bound instantly.**

**Note 08-20:** a second UI edit (approval mode, §5.1) did NOT repeat the strip.

## 8. Discrimination probes (created 2026-08-13 13:39Z)

| Probe | Fires | Tests | Trigger |
|---|---|---|---|
| P1 | 08-13 13:55Z | Do short-horizon one-shots still bind post-migration? | `trig_01Kv5EBVHckto33ZP12UEjtx` |
| P2 | 08-13 14:25Z | Same, with one subsequent creation (P3) after it | `trig_012riVuUJCGHJbeKvsrimuPm` |
| P3 | 08-14 10:23Z | Morning window, long horizon, nothing created after | `trig_01Vj3JYcimncLhn3uuEM3v5k` |

**RESULTS:**
- **P2 (fired 14:34Z): ALL THREE BOUND, 9/9 servers, HaloPSA live-call ok.**
- **P1 (13:55Z): fired per the API (`run_once_fired`) but never emailed and left no visible run.**
- **P3 (08-14 10:23Z): never collected.**

**Fallback architectures — the case is now weaker than it was on 09-01 but not gone:**
1. **Data-push:** a Cloudflare Worker cron assembles the HaloPSA / Action1 / SentinelOne digest and
   emails it (or writes to SharePoint); the scheduled Claude session reads it via Microsoft 365,
   which has bound on every run without exception. **Recommended path.**
2. **Local schedule:** run the jobs as local scheduled tasks via the desktop app. Loses cloud
   unattended execution but gains the local filesystem.

**Escalation package for Anthropic support:** the §7.1 diff; the 08-12 9/9 probe; the 08-13 5/8
v3.4 result; the §9 5/5 result; the §10 and §11 2/5 results on the *same unchanged trigger*; the
send_later-spared observation; the §11.4 within-session flip on human engagement; the §13.1
within-session flip with NO human engagement; the 08-31 clean unattended ladder save; **and now
09-02, the same trigger binding at T+0 unattended.** **Lead with the 08-31 / 09-01 / 09-02 triple
on consecutive firings of one unchanged trigger — bound at T+30, not bound by T+30, bound at T+0 —
which shows the delay is a wide per-firing distribution rather than any property of the task.
That is the strongest possible statement of GitHub #43397's shape.**

## 9. 2026-08-13 afternoon — the SECOND rebuild appeared to hold (5/5 bound)

A scheduled Morning Brief run fired **2026-08-13 ~16:36Z** and probed all five connectors. Every
one answered live on the first attempt. Read at the time as confirmation that §3 was the fix;
§10 falsified that; §13.1 removes the attendance reading too. It is simply a run where the attach
completed before the first probe — **as 09-02 also did.**

### 9.1 GOTCHA — the `RefreshMcpTools` status column lied

In that run, `RefreshMcpTools` returned **`status:"error", error:"Not connected"` for all nine
servers**, and every connector then probed answered live on the first call.

- The distinction that matters is **absent from the table vs present in the table**.
- Prompt wording in all recurring jobs: *"a server ABSENT from the table was never attached — skip
  the retry ladder."* **That first half is wrong and should be amended when prompts are next
  edited: absence means not-attached-yet, not never-attached.** The ladder text itself already
  behaves correctly.
- **Note 08-17, reconfirmed on every run since:** the table reports no `status` field beyond
  `"refreshed"` — just `{server, status, toolCount, added, removed}`. Only membership is
  load-bearing. 09-01's unbound table was five servers `{memory: 6, Plaud_ai: 5, PagerDuty: 64,
  Microsoft_365: 41, claude-code-remote: 6}`; the bound table was nine — the same five plus
  `{Action1: 19, HaloPSA: 22, SentinelOne: 27}` (68 Worker tools). **09-02's table was those eight
  from the first call, every one reporting `status: "refreshed"` with empty `added`/`removed`
  arrays. Canva, Cloudflare and `visualize` were absent throughout — their absence is normal and
  is not a degraded source.**

### 9.2 Operational notes — Halo, SOC, Teams, brand assets

- **Halo `get_tickets` / `halo_get "Tickets"` responses exceed the tool-results ceiling.**
  **AMENDED 08-26, reconfirmed 08-31, 09-01 and 09-02: truncation is not the default.** Most large
  Halo payloads are written as complete, well-formed JSON and parse with a plain `json.load`.
  **Try `json.load` first; `raw_decode` is a repair tool, not the default path.**
- **The tool-results file hard-truncates at 500,000 characters.** 09-01: a firm-wide
  `halo_get "Tickets" {open_only: true, count: 400}` produced a 500,097-character file.
  **09-02 reproduced it exactly** with `{open_only: true, count: 300}` — 500,097 characters,
  `json.load` raising `Expecting property name enclosed in double quotes: line 14491 column 1
  (char 500002)`. **Repair, verified twice:** `i = raw.rfind('\n    },\n')`, then
  `json.loads(raw[:i+6] + '\n  ]\n}')`. On 09-02 that recovered **139 of 173** tickets cleanly.
  **Fetch the remainder with `pageinate: true, page_size: 60, page_no: 3` and merge on `id`** —
  that single extra call returned the missing 34 and completed the set. **Always check
  `record_count` against `len(tickets)`; they disagree exactly when this bites.**
- **The tool-results payload is a DICT, not a list.** `json.load` returns
  `{page_no, page_size, record_count, tickets, include_children}`. Always unwrap `raw["tickets"]`.
- **`halo_get "Tickets"` date sweeps WORK and page honestly.** With
  `{"open_only": false, "includedetails": false, "datesearch": "<field>", "startdate": ..., "enddate": ...}`.
  ET→UTC during EDT is `T04:00:00Z` to next-day `T04:00:00Z`. **09-02 (reporting Tuesday 09-01):
  dateoccurred 24, dateclosed 28 — both returned complete and every record fell inside the window,
  so no client-side date filtering was needed.**
- **`includedetails: false` is not honoured** — the sweeps still return full `details` bodies with
  Mimecast disclaimers. Budget for the size; do not expect the flag to shrink the payload.
- **`get_tickets agent_id=14` returns Ryan's whole VISIBLE queue, not tickets assigned to him.**
  Stable at 30 records on 08-24, 08-26, 08-31 and 09-01; **28 on 09-02** (20 Action1, 8 real).
  **09-02 breakdown by true `agent_id`: 14 → 7, 28 (Stevie Kantor) → 19, 19 (Gabe Lister) → 1,
  1 (Unassigned) → 1. Only 5 of the 8 real tickets are actually Ryan's.**
  **THIS TRAP BIT AGAIN ON 09-02 AND WAS PUBLISHED**: the first send attributed **#51920 Umbrella
  Fixes** to Ryan; it is Gabe Lister's. Same class of error as 09-01's #50849. **Re-read `agent_id`
  on every record before naming an owner, and call the aggregate his "visible queue", never
  "assigned to you" or "his tickets".**
- **THE STATUS-ID MAP IN THE MORNING-BRIEF SKILL IS STILL WRONG — re-verified 09-02, FOURTH
  consecutive run, STILL NOT FIXED.** The skill's `references/halopsa-queries.md` lists
  **32 = "Ready to Invoice"**. Live: **32 = "Stale"**, **34 = "Ready to Invoice"**,
  **20 = "Completed"** (which the skill omits).
  **Cross-check `claude/HaloPSA-Ticket-Status-ID-Map-Verified-2026-08-18.md` — it is authoritative.**
  **09-02 published the wrong mapping**, describing the ten status-32 orders as "Ready to Invoice"
  when they are Stale; corrected on the page, in the OneDrive copy and by follow-up notification.
  **Two consecutive runs have now shipped an error from this one stale file. Fixing the skill file
  is a smaller job than the corrections it keeps causing — do it.**
- **Reading the status map is NOT sufficient; you must also apply the hold filter, and that is the
  step that gets skipped.** 09-01 skipped it; **09-02 skipped it too and published 47 raw breaches
  where the live figure is 23.** Filter statuses **4, 5, 20, 23, 30, 33, 35, 37, 38**.
  **09-02 true figures: 173 open firm-wide, 56 Action1, 117 real; 47 raw past fix-by → 24
  clock-stopped (13 With User, 8 Scheduled, 3 With 3rd Party) → 23 LIVE, of which 5 on Cyber Ops
  and 3 actually Ryan's.** The raw number overstates by roughly 2× — consistently, on every run
  measured. **Verify the map, then apply the filter — two separate steps, and the second one is
  the one that keeps getting missed.**
- **Watch status 21 "On Hold": its `slaaction` is `none`, so it does NOT stop the clock.** Two of
  09-01's live breaches (#50822, #51828) sit in 21; **on 09-02 the same two plus #51419 did.** The
  name is a trap and it is worth saying so on the page.
- **`get_ticket` responses are huge** (186 KB for one ticket). **`get_ticket_actions` is far
  cheaper and usually the better call.**
- **`get_sales_orders` returns oldest-first with no sort parameter**, and its `record_count` is
  per-page. Faster route: filter the firm-wide open pull client-side on
  `"NEW ORDER" in summary or "QUOTE" in summary or team in ("Sales Team","Contract Renewals")` —
  returned **41** open order/quote tickets on 09-01 and **40** on 09-02 (10 Stale, 8 Ready to
  Invoice).
- **A cheap, high-value negative check:** `get_tickets(search=..., open_only=false)` returning
  `record_count: 0` is solid evidence that something seen elsewhere has no ticket. **09-02 used it
  twice to turn observations into findings** — no HaloPSA ticket exists for the Great Lakes Brewing
  consent cluster, and none for the BMF SentinelOne renewal. **"PagerDuty/mail says X, Halo has no
  ticket for X" is the single most useful shape of finding this brief produces.** Two such searches
  cost nothing and both landed in Priority Actions.
- **`scripts/soc_stats.py` reports `high 0 / low N` unless `--high` is passed, and reports
  `high N / low 0` when it IS passed** — it treats the `--high` file as the full set rather than
  intersecting it. **Reconfirmed 09-02: it printed `TOTAL 24 high 24 low 0`. Take the urgency split
  from the record counts of the two queries directly** (09-02: 24 total, 14 high → 10 low).
  Everything else it emits is trustworthy and it accepts hand-built input happily. **Its
  client/alert-type parser splits on the pipe in the incident title, so Auvik titles do not parse —
  aggregate Auvik by hand.** Its `REPEAT_FIRE_THRESHOLD` of 5 caught the Polaris storm (08-24), the
  Avon ScreenConnect storms (08-26, 08-31) and the Suspicious RMM pair (09-01). **NEW 09-02 — it
  can also MISS a real storm.** Six Registry RunOnce alerts on SIMVAY in twenty minutes did not
  trip the threshold because the exact titles differ (`Spillman Full.exe`, `rundll32.exe (CLI f6c5)`,
  `(CLI c08f)`, `(CLI 5040)`) — the script counts exact titles, not alert families.
  **Read the by-alert-type list yourself for a shared suffix (here "- Registry RunOnce Persistence
  detected") before trusting a clean repeat-fire report.**
- **PagerDuty `list_incidents` returns inline** at 24–95 records — no tool-results file. At weekly
  volume (250–350) it spills to a file; the schema has **no `service_ids` parameter** — pull the
  window and split by `service.id` in Python. **The `statuses: ["triggered","acknowledged"]` query
  is the cheapest and most valuable single call in the SOC section** — on 09-02 it returned an
  empty array, which is the "0 still open" KPI directly.
- **Teams `chat_message_search` is unreliable, and its failure mode keeps changing.** 08-31 no
  output; 09-01 rate-limited on both attempts. **09-02 it WORKED on the first call at a 48-hour
  window and returned 2 messages — both Otter.ai notetaker bot posts in one meeting chat, no human
  traffic.** No fallback was needed. **When it works, say what it found rather than reaching for
  `teams_list_chats`; when it rate-limits, run the list-level fallback and report coverage as
  UNKNOWN, not zero** — `lastUpdatedDateTime` is rename/membership time, not last-message time.
- **Action1 needs an explicit `org_id`.** `list_vulnerabilities` fails with `org_id is required`.
  Call `list_organizations` first, or skip Action1 vulnerability enrichment and say so. Action1's
  contribution to the Brief arrives via Halo's `[Action1]` tickets anyway.
- **`outlook_email_search` with no `folderName` and no `order`, paging by `offset`, is correct and
  it works.** 09-02 pulled 50 messages across two calls at `offset` 0 and 25 over a 48-hour window
  and got full cross-folder coverage. **Setting `order` silently scopes to Inbox — do not.**
- **Check for Ryan's own reply before flagging any mail.** 09-02 found three threads already
  answered late the previous evening (the Fairview Park handbook review at 21:29 ET, the FortiOS
  forward at 18:35 ET, the CISO event at 18:02 ET) and moved them to "Cleared" rather than
  Priority Actions. **A brief that tells him to answer something he handled at 10pm reads as
  broken.** Note the second-order finding, though: **his FortiOS reply was "No, thanks for
  forwarding this over" — the thread is closed but the exposure is not, and no ticket exists.**
- **The white S-mark is not where `build_page.py` looks.** It lives at
  `/root/.claude/skills/synced/<uuid>/simvay-brand-styling/assets/simvay-mark-white.png`. The
  script's `MARK_CANDIDATES` is missing the `synced/` path segment and will always miss. **Fix in
  one line:** `cp` that file into the morning-brief skill's own `assets/` dir, which IS the first
  candidate. Verified working 08-26, 08-31, 09-01 and 09-02. Locate it with
  `ls /root/.claude/skills/synced/*/simvay-brand-styling/assets/simvay-mark-white.png`.
- **Resize the mark before the first build, every run.** PIL resize 206×256 → 100×124 with
  `optimize=True` gives a **3,224-byte PNG** (~4,300-character data URI) versus 8,509 bytes
  (~11,300 characters) unresized. **09-02 built once unresized (44,331 bytes), resized, and rebuilt
  at 37,283 — a 7 KB saving, and the resized mark is visually identical in the hero at its 62px
  render height.** Do it first and the correction re-upload costs 7 KB less too.

## 10. 2026-08-14 morning — regression on the unchanged §9 trigger (2/5 bound)

**FAILED, 2 of 5,** fired **2026-08-14 ~10:27Z** on `trig_01PsbrBqfBMNtg2gkNPeJequ` — the same
trigger that bound 5/5 the previous afternoon, with no edits between.

### 10.1 GOTCHA — mid-run MCP disconnect/reconnect churn

All six bound servers dropped and reconnected mid-session. **Do not report absence off a single
table read during churn.**

### 10.2 What this falsified

Binding is not a stable per-task property. Whatever selects the connector set is evaluated
**per firing**. UI contamination cannot be the whole mechanism.

## 11. 2026-08-17 Monday — failed unattended, then bound mid-session on engagement

**Phase 1 — FAILED, 2 of 5** at ~10:22Z. **Phase 2 — 5 of 5.** Ryan typed *"Try now"* at ~10:35Z;
all three Workers answered on the first probe.

### 11.1 Detection note

`ToolSearch` returned **"No matching deferred tools found"** during phase 1, independently
confirming absence. Now step 6 of §4.

### 11.2 The record, re-read after 09-02

| Run | Time (ET) | Attended? | Bound | Bind latency |
|---|---|---|---|---|
| 08-06 / 08-12 / 08-13am / 08-14 / 08-17 ph1 | ~06:2x | no | **FAILED** | never, in-session |
| 08-12 diagnostic probe | 17:21 | Ryan at desk | 9/9 | immediate |
| 08-13 afternoon Brief | 12:36 | Ryan at desk | 5/5 | immediate |
| 08-17 same session, after Ryan typed | 06:35 | yes | 5/5 | ~13 min |
| 08-24 Morning Brief, NOBODY THERE | 06:50 | no | 5/5 | ~34 min |
| 08-24 Weekly Renewals, after Ryan typed "Go" | ~06:50 | yes | 9/9 | ~37 min |
| 08-25 Morning Brief | 06:16–06:46 | no | **FAILED, 2 of 5** | not bound by T+30 |
| 08-26 Morning Brief, ladder | 06:16–06:46 | no | **FAILED, 2 of 5** | not bound by T+30 |
| 08-26 same session, after Ryan replied "Continue" | ~10:10 | yes | 9/9 | INSTANT |
| 08-31 Morning Brief, ladder retry 2 | 06:16–06:46 | no | 5/5 — BOUND IN LADDER | ~30 min, no halt |
| 08-31 Weekly Ops Reports, ladder | 06:10–06:41 | no | **FAILED at T+30** | halt sent 5 min before Brief's bind |
| 08-31 same Ops session, after "Try now" | ~06:5x | yes | 8/8 | INSTANT |
| 09-01 Morning Brief, ladder | 06:16–06:46 | no | **FAILED, 3 rungs** | not bound by T+30; halt 10:47Z |
| 09-01 same session, after "try now" | ~10:1x | yes | 9/9 | INSTANT |
| **09-02 Morning Brief, first probe** | **06:17** | **no** | **8/8 — NO LADDER NEEDED** | **T+0, INSTANT** |

Attendance correlates with a *fast* bind, not with binding as such. **The Morning Brief's own
unattended record is now 2 clean runs in 6 (08-24 late-bind-after-halt, 08-25 no, 08-26 no,
08-31 YES in-ladder, 09-01 no, 09-02 YES at T+0).** Attended recovery is **6 for 6** and has been
instantaneous on the last three. **The Weekly Ops job is 0 for 4 unattended and 4 for 4 on a human
reply.**

### 11.3 What is still unknown

Why the attach is slow, and whether anything about the session influences it. **09-02 removes the
"it always takes about half an hour" reading** — six data points now span T+0 to >T+30 on one
unchanged trigger at one fixed time of day, which points at contention or a race rather than a
fixed initialisation cost. A scheduled one-shot that does nothing but probe every 5 minutes for an
hour and mail the timeline would still be the clean way to pin the distribution. **08-31's
Ops/Brief pair remains the closest thing to a concurrent probe.**

### 11.4 The operational win

**A failed run is recoverable.** Opening the session and replying with anything is correlated with
a fast bind (**6/6**) and costs Ryan two minutes. Keep saying so in degraded notifications.
**And a run that binds at T+0 should say so too** — 09-02's notification closed with "all five
bound on the first check, no retries needed, nothing degraded", which is what §13 step 6 asks for
and is worth the one sentence.

### 11.5 Recommendation

**09-02 does not change the recommendation, it sharpens the argument.** The bind is a coin-flip
per firing with a wide latency spread. §13.2 (cheap, one prompt edit per job) covers the slow half;
fallback architecture 1 (§8) covers what is left.

## 12. Findings that only appear with all five connectors bound

- **Ryan's visible queue: 30 open on 08-24, 08-26, 08-31 and 09-01; 28 on 09-02** — 20 Action1,
  8 real, **5 actually his**. Live breaches among them after the hold filter, 09-02: **3**
  (#50822 at 85 days, #51759 at 15, #51828 at 13).
- Firm-wide, 08-24: **175 open, 45 Action1, 57 past fix-by.** 08-31: **167 open, 49 Action1,
  53 past fix-by.** 09-01: **183 open, 50 Action1, 55 raw → 28 LIVE.**
  **09-02: 173 open, 56 Action1, 117 real, 47 raw past fix-by → 23 LIVE breaches, 40 open
  order/quote tickets (10 Stale, 8 Ready to Invoice).**
- **THE SRM | COMPLIANCE TRACKING CLUSTER WAS CLEARED ON 2026-09-01 — the standing finding of
  record is closed.** All four Gabe Lister trackers closed on Tuesday: Avon Local **#50849** (last
  measured at 90 days), Brooklyn **#50976**, Fairview Park **#51089**, Olmsted Township **#51120**.
  A fresh **Q3-2026 tracker #51996** opened for City of Avon Lake the same day. The series that had
  run **08-17: 76/66/54/52 → 08-24: 82/72/60/58 → 08-31: 89/79/67/65 → 09-01: 90/80/68/66** ends
  here. **#51419 Monroeville Offboarding (46 days, status 21) is the one Lister ticket still
  running — keep watching that one alone.** Do not re-report the cluster as an active backlog.
- **The Cyber Ops closure block did NOT recur on 09-01.** Where 08-31 saw Cyber Ops close zero and
  move seven to status 20 Completed, **09-01 saw Cyber Ops genuinely CLOSE 14 tickets against 4
  opened** — five Cyber Hygiene reports, the four SRM trackers, two risky sign-ins, the BMF pen
  test and an info-stealer detection. Firm-wide 24 new / 28 closed, net −4. **Only one ticket sat
  in status 20 on 09-02 (#51997).** Cross-reference Runbook 16 (Todo Closure Block) and note the
  improvement rather than restating the old pattern.
- **The client-storm SOC pattern, six consecutive reviews:** Polaris 22 of 43 (51%, 08-21) →
  Polaris again (08-24) → Avon Local 36 of 94 (38%, 08-26) → Avon Local 34 of 40 (85%, 08-28) →
  Suspicious RMM 12 of 35 across three clients (34%, 08-31) → **09-02: two storms at once on a
  small board. Six "Registry RunOnce Persistence" alerts on SIMVAY's OWN estate in 20 minutes
  (#23504–#23509, one Spillman install) and four Auvik alerts for ONE Olmsted Falls switch stack
  (#23515–#23518, FL_708_R1_2960_STACK plus its three members, self-cleared in 4 minutes).
  Together 10 of 24 incidents — 42% of the day's volume from two rules.** The internal one matters
  for a second reason: **Simvay's own tenant is generating a quarter of the SOC board.**
- **NEW 09-02 — a tenant-consent cluster on a CLIENT tenant, unassigned and unticketed.** Great
  Lakes Brewing fired six incidents 21:11–23:17 ET: **#23519/#23520** Entra ID Admin Consent
  Granted for All Principals, **#23521/#23524** Office 365 Admin Consent Granted for All
  Principals, **#23522** Service Principal Addition, **#23523** Application Role Assigned to
  Service Principal. All six had **empty assignment lists** and were **bulk-resolved together at
  03:12 ET**; `get_tickets(search="Great Lakes Brewing consent")` returns **0**. They also occupy
  all five slowest slots (235–361 min) and are the entire median-vs-mean MTTR gap (10.8 vs 84.8).
  **This is the exact promote-it shape in `references/pagerduty-metrics.md` — consent-for-all-
  principals plus a service principal handed an app role — and it is the second consecutive run
  where a privileged-change cluster auto-resolved with no confirmation recorded** (09-01 was the
  Avon Lake Duo bypass/MFA quartet). Flagged P1.
- **Auvik and Cyber Infra coverage:** 09-01 Auvik produced 13 incidents at Avon Lake; **09-02 it
  produced 4 and Cyber Infra again produced 0.** Report Cyber Infra's silence as coverage, not calm.
- **Notification mail lies, as designed.** Query Halo and PagerDuty directly.

## 13. STEP ZERO procedure v2 — the 15-minute rebind ladder (Ryan, 2026-08-20)

**This is the authoritative missing-connector procedure.** Binding is re-evaluated over time, so
waiting is not futile and a partial report has less value than a complete one delivered late.
**As of 09-02 the Brief has had two clean unattended runs in six — one saved by the ladder (08-31),
one that never needed it (09-02). The halt-and-callback half works reliably (6/6).**

1. Call `RefreshMcpTools` with no server argument and read the server table. Only MEMBERSHIP is
   load-bearing (§9.1). Confirm a suspected absence with `ToolSearch` (§11.1). Re-read after any
   disconnect/reconnect churn (§10.1).
2. PRESENT but erroring → possible Worker cold start: refresh by name, re-probe, `sleep 20`,
   re-probe. 3 attempts max. (A *directory* connector reported "pending" usually clears itself
   inside the first rung — §4 step 3.)
3. ABSENT → **15-minute rebind ladder.** Wait 15 minutes (`sleep 450` twice — a single Bash call is
   capped at 600s), re-check. If still absent, wait another 15 and re-check. **Two retries total,
   at roughly T+15 and T+30.** Ship nothing in the meantime.
4. Still absent after retry 2 → **HALT AND WAIT FOR RYAN.** One PushNotification whose FIRST
   sentence names the absent connectors and cites this runbook, then asks Ryan to open the session
   and type anything (§11.4). **§13.2 proposes amending this step; it is NOT yet in the prompts.**
5. When Ryan replies, re-run STEP ZERO from step 1 and, if bound, run the whole job from the start.
6. Report the binding outcome in the final notification either way — **a recovery inside the
   ladder, a halt, OR a clean T+0 bind. All three are worth one sentence.**

**Not applied to** the Weekly SOC Tuning Report (§5) by Ryan's explicit instruction.

### 13.1 Ladder run log

| Firing | Outcome |
|---|---|
| Fri 2026-08-21 10:15Z (Morning Brief v3.6) | **Not recorded.** The intended first live test; no session wrote the result back. |
| Mon 2026-08-24 10:15Z (Morning Brief v3.6) | **Halted at T+31, then bound at ~T+34 with nobody in the session, and completed.** |
| Mon 2026-08-24 10:10Z (Weekly Renewals v2.4) | **Halted at T+33, then bound the moment Ryan typed "Go" (~T+37) and ran to completion.** |
| Mon 2026-08-24 10:10Z (Weekly Ops Reports v4.3) | **Halted at T+30; bound on Ryan's one-word reply; full run completed in-session.** |
| Tue 2026-08-25 10:15Z (Morning Brief v3.6) | **HALTED at T+30. No recovery observed.** Halt sent 10:47Z. Nothing produced. |
| Wed 2026-08-26 10:15Z (Morning Brief v3.6) | **HALTED at T+30, then FULLY RECOVERED on "Continue".** 9/9, zero wait. Filed to OneDrive (45,607 bytes). |
| Mon 2026-08-31 10:15Z (Morning Brief v3.6) | **BOUND INSIDE THE LADDER AT RETRY 2 — NO HALT, NO HUMAN, COMPLETE REPORT.** |
| Mon 2026-08-31 10:10Z (Weekly Ops Reports v4.3) | **HALTED at T+30 (10:41Z) — five minutes before the Brief's bind — then bound instantly on "Try now".** |
| Tue 2026-09-01 10:15Z (Morning Brief v3.6) | **HALTED at T+30 (10:47Z) after three clean ToolSearch-confirmed rungs, then bound INSTANTLY on Ryan's "try now"; full job ran in-session.** |
| **Wed 2026-09-02 10:15Z (Morning Brief v3.6)** | **BOUND AT T+0. No ladder entered, no sleep, no halt, no human. All five probes answered on the first call. Full job ran straight through.** |

**The 09-02 Morning Brief timeline — what a clean run looks like:**

| Time (UTC) | Event |
|---|---|
| 10:17 | `RefreshMcpTools`, first call → **8 servers**: memory 6, Action1 19, HaloPSA 22, Plaud_ai 5, PagerDuty 64, SentinelOne 27, Microsoft_365 41, claude-code-remote 6. Every one `status: "refreshed"`. The deferred-tool notice listing all 68 Worker tools arrived with it. |
| 10:17 | `ToolSearch "select:"` for the five probe tools → all five schemas returned. |
| 10:18 | All five probes fired in one block; all five answered live first time (HaloPSA 16 agents, PagerDuty 4 services, M365 profile, Action1 API user, SentinelOne 15 clients). |
| 10:18–10:35 | Full job: 24 SOC incidents, 173-ticket firm-wide sweep (truncation repair + page 3 merge), previous-business-day movement, 50 mail messages, Teams, calendar. |
| 10:35–10:50 | Dashboard built, render-checked, mark resized and rebuilt, delivered, uploaded to OneDrive. |
| 10:50–11:05 | **Runbook cross-check caught two published errors** (status map, hold filter) → corrected page, re-delivered, re-uploaded in place, correction notification sent. |

**What 09-02 establishes.** (a) The unattended bind has **no floor** — it can be there at T+0.
(b) The Brief's unattended record is 2 in 6. (c) There is nothing about the task, its config strip,
its model, or the 10:15Z slot that determines the outcome; consecutive firings of one unchanged
trigger have now produced bind-at-T+30, no-bind-by-T+30, and bind-at-T+0 on three successive days.
(d) **A clean binding run is not a run without errors** — 09-02 bound perfectly and still shipped
two wrong figures from a stale skill file. Binding is one failure mode; the §9.2 data traps are
another, and they are currently the more frequent one.

**The 08-31 Morning Brief timeline — the one clean unattended ladder save:**

| Time (UTC) | Event |
|---|---|
| 10:16 | Probe 1. Five servers; Workers **absent**, ToolSearch confirms. |
| 10:31 | Retry 1. Workers **still absent**. |
| ~10:46 | **Deferred-tool notice arrives mid-`sleep`, listing all 68 Worker tools.** No human had engaged; no halt had been sent. |
| 10:47 | `RefreshMcpTools` → **8 of 8**. All five probes answered first call. |
| 10:47–11:15 | Full job ran and filed to OneDrive (33,117 bytes, byte-exact). |

**The 09-01 Morning Brief timeline — a textbook halt-and-callback:**

| Time (UTC) | Event |
|---|---|
| 10:16 | Probe 1. Five servers. Workers **absent**; `select:` ToolSearch → "No matching deferred tools found." |
| 10:31 | Retry 1. **Absent**, confirmed again. |
| 10:46 | Retry 2. **Absent**, confirmed a third time. |
| 10:47 | **Halt PushNotification sent** per step 4. Turn ended. Nothing produced or uploaded. |
| — | Ryan replies **"try now"**; the reply turn carries the deferred-tool notice for all 68 Worker tools. |
| next call | `RefreshMcpTools` → **9 servers**. Full job ran, delivered, filed, then corrected for the hold-filter miss. |

**The 08-24 Morning Brief timeline (kept for comparison):**

| Time (UTC) | Event |
|---|---|
| 10:16 | Probe 1. Six servers; Workers **absent**. |
| 10:31 / 10:46 | Retries 1 and 2. Still absent. |
| 10:47 | **Halt PushNotification sent.** |
| ~10:50 | Deferred-tool notice arrived listing **all 68 Worker tools**. **No human had engaged.** |
| 10:50–11:15 | Full job re-run, delivered, filed, corrected notification sent retracting the halt. |

### 13.2 PROPOSED amendment to step 4 — halt, then keep listening

**Send the halt notification, then continue probing before ending the turn.** After the halt
notice, run `RefreshMcpTools` at roughly T+35, T+40, T+50 and T+60 (`sleep 300` between). If the
connectors appear, run the whole job from the beginning and send a corrected notification that
**explicitly retracts the halt in its first sentence**. Only after T+60 should the turn end.

Cost: about half an hour of cheap polling on a morning that has already failed. Benefit, on the
08-24 evidence: the entire report.

A second, softer option: delay the halt notification to T+60 so a late bind never produces a
retracted alarm. Trades a false alarm against a later real one.

**STATUS: NOT IMPLEMENTED.** Deliberately still absent from all four prompts, because it changes
when Ryan gets paged, which is his call. Raised in the 08-25 halt notification and the 08-26,
08-31, 09-01 and 09-02 completion notifications.

**09-02 refines the case rather than repeating it.** The argument is no longer "the bind usually
lands at 30–37 minutes so extend to 60" — 09-02 shows it can land at zero. The sharper argument is
that **the outcome is decided per firing and the ladder currently truncates the slow half of the
distribution at exactly the point where it starts paying off.** Extending to T+60 costs nothing on
a run like 09-02 (it never enters the ladder at all) and only ever spends polling time on mornings
that have already failed. **This remains the single highest-value outstanding change in this
runbook.**

### 13.3 Standing recommendation

§13.2 first — cheap, one prompt edit per job, evidence both positive (08-31) and negative (08-24,
08-25, 08-26, 09-01). Fallback architecture 1 (§8, §11.5) after that. **Separately, and now
arguably ahead of both: fix the morning-brief skill's status-ID map (§9.2). It has caused a
published error on two consecutive runs, including one where every connector bound perfectly.**

## 14. Report export — LOCAL FOLDER (Ryan's decision, 2026-08-24)

**Reports are exported by joining a local folder to the session.** It replaces the SharePoint
upload block that had been in the prompts since 08-20.

**How it works.** `mcp__remote-devices__device_commit_files` writes a staged file to a connected
folder. It takes a file, not inline base64, so the payload-size wall in §14.3 disappears entirely.
If the folder Ryan joins is OneDrive/SharePoint-synced, sync performs the SharePoint filing with no
upload tool involved.

**The limitation, and it matters.** A scheduled firing runs in the cloud with **no desktop bridge** —
local folders are never connected to an unattended run. **Reconfirmed 08-25, 08-26, 08-31, 09-01
and 09-02: no folder was connected, as expected. On 08-31, 09-01 and 09-02, `ToolSearch` for
`mcp__remote-devices__get_device_info` returned "No matching deferred tools found" — that is the
correct, cheap way to establish "no bridge" in one call, and it is the NORMAL case, not a failure.**
Note that a human reply from a phone (08-26) or from the app without a folder joined (08-31 Ops,
09-01) binds the Workers but does NOT bring a desktop bridge with it.

**What the four prompts now say** (rewritten 2026-08-24 evening, verified post-edit):

| Job | Export block | Files |
|---|---|---|
| Weekly Renewals v2.4 | local folder only; SharePoint retired | `Simvay_Weekly_Renewals_v2.1_<date>.pdf` + `.xlsx` |
| Weekly Ops Reports v4.3 | local folder only; SharePoint retired | `Simvay_Weekly_Ops_Retrospective_<Monday>.pdf`, `Simvay_Weekly_Team_Report_<Monday>.pdf` |
| Monthly Sales Report v3.3 | local folder only; SharePoint retired | `Simvay_Sales_Report_<Month>_<YYYY>.pdf` |
| Daily Morning Brief v3.6 | local folder PREFERRED, **OneDrive upload kept as fallback** | `Simvay_Morning_Brief_<YYYY-MM-DD>.html` |

Every block states the same three rules: no folder connected is the NORMAL unattended case and must
not read as a failure or trigger a retry; a genuine commit failure (folder connected, write refused)
must be reported plainly; and the filename carries the SPEC version from the runbook.

**The Morning Brief keeps its OneDrive upload** because the brief is TEXT and goes up through the
`content` parameter, which is not whitespace-validated. See §14.2.

**Historic destinations, kept for reference only** — no longer in any prompt except the Brief's
fallback. LeadershipHub > Reports > Operations: driveId
`b!D5XIx3WdCkWZBzPuPszcjQaOiomtqIJIl9cSSj20-Vlpu2nkBEpoTbAEYKOgeiKK`, parentItemId
`01V5EVCZBR4J6QRCBIMRF3CBLWQU2NFKYO`, archive `01V5EVCZFMHH5A3LNUUFC3V6WRW3UPPY2M`; Sales folder
`01V5EVCZAW5EV62EY4PZAJP7QEUINBJHT4`; Ryan's OneDrive Daily Reports driveId
`b!ydrpSUdwrUK6_E_7vSnLVzJ8NbSi501Mhbw_V-Q8_V4dWvYOLivAQoAhFWuj0kCN`, parentItemId
`01TUGF7ZQ74AMJMLYTGZEKQCUYKGEYOKBJ`. Ryan's OneDrive is under `ryan@simvay.com`, not `rpatrick@`.

**The archive move is retired with the upload.** It must never be performed without a successful
replacement write.

### 14.1 The 1 MB upload cap — real, but not the constraint that bit

`sharepoint_upload_file` refuses payloads over **1,048,576 bytes** and there is no chunked upload.
Observed report sizes are far under it (Renewals PDF 193 KB, XLSX 23 KB, Ops 244/143 KB, Sales
492 KB, Morning Brief 33–46 KB). **The cap was never what blocked filing — see §14.3.**

### 14.2 Uploading TEXT (the Morning Brief) — this path works

The brief goes up as `content`, not `contentBase64`. **Line breaks are harmless.** Do not spend
effort producing an unbroken line.

**Track record on opus — seven for seven:**

| Run | Local bytes | Uploaded | Delta | itemId |
|---|---|---|---|---|
| 08-24 | 39,977 | 39,978 | +1 | — |
| 08-26 | 45,605 | 45,607 | +2 | `01TUGF7ZQMIUXGUGOBOBBICD4GRTUEMR67` |
| 08-31 | 33,117 | 33,117 | 0 | `01TUGF7ZRUNPSFABQAEZF27BI32ZQK5LVL` |
| 09-01 (first send) | 44,202 | 44,202 | 0 | `01TUGF7ZRLZIAGTO7CWRE3DPSOVYRF34TJ` |
| 09-01 (corrected, `replace`) | 44,873 | 44,873 | 0 | same itemId — replaced in place |
| **09-02 (first send)** | **37,437** | **37,437** | **0** | `01TUGF7ZTCRKKBLNE7NFDIP7BC3BEB5OTR` |
| **09-02 (corrected, `replace`)** | **38,166** | **38,160** | **−6** | same itemId — replaced in place |

**A delta of 0–2 bytes is normal.** **NEW 09-02: a −6 delta also turned out to be benign.** When it
appeared, the file was read back in full with `read_resource` on the `file:///{driveId}/{itemId}`
URI and compared — **every corrected figure and every section was present and identical**. The
lesson is the verification, not the number: **a byte delta in the single digits does not by itself
mean a bad upload, and `read_resource` on the returned itemId settles it in one call.** A genuine
transcription error shows as a large discrepancy or visibly missing content.

**`conflictBehavior: "replace"` overwrites in place and returns the SAME itemId** — confirmed twice
on 09-01 and twice on 09-02 — so a correction does not orphan the original or create a duplicate.
Re-uploading a corrected brief is safe and cheap to verify.

**Keep the brief small.** The embedded S-mark dominates the payload; see the resize note in §9.2.
**09-02 resized before the first upload and shipped 37.4 KB**, versus 44.3 KB unresized — which
also made the correction re-upload 7 KB cheaper.

### 14.3 Why BINARY filing failed — corrected 2026-08-24 (evening)

**An earlier version of this section called binary filing "structurally impossible". That was too
strong and is wrong.** `Simvay_Weekly_Renewals_v2.1_2026-08-17.pdf`, **211,241 bytes, is in the
Operations folder**. The correct statement is that it is **size-dependent and unreliable, and it
regressed on 08-24.**

**What was measured on 08-24:**

| Payload | base64 chars | Result |
|---|---|---|
| 193-byte test PDF | 260 | **Uploaded byte-exact**, then deleted |
| deliberately malformed probe | 1,034 | Rejected `bad_length` — **not** `whitespace` |
| Renewals XLSX (23,252 bytes) | 31,004 | Rejected `whitespace` **twice**, ~410 injected line breaks |
| Renewals PDF (193,529 bytes) | ~258,000 | Never attempted end-to-end |

So: the mechanism works, short payloads emit cleanly, and somewhere between ~1K and ~31K characters
the output starts acquiring line breaks that `contentBase64` rejects outright.

**Things that do NOT fix it, all tried:** ghostscript/qpdf compression; pre-scaling the embedded
S-mark; dropping the unused Poppins 500 weight; splitting and reassembling the base64.

**Likely why 08-17 worked and 08-24 did not:** the Renewals task normally runs **claude-fable-5**;
the 08-24 run completed in-session on **claude-opus-5**. Different model, different emission
behaviour. Hypothesis, not measurement. **None of 08-26, 08-31, 09-01 or 09-02 bears on it**: all
emitted plain UTF-8 through `content`. **The `contentBase64` hypothesis remains untested since
08-24 — though four clean 37–45 KB `content` emissions on opus across 09-01 and 09-02 show the
emission path itself is sound at that size, which further weakens the model-emission explanation.**

**Consequence.** The Renewals XLSX has probably never filed. **Check whether the Ops and Sales PDFs
are actually in SharePoint** rather than assuming.

## Standing instruction

Any future run that learns something new about connector binding, scheduled-task mechanics, or
report export updates THIS runbook in the same session, with the date and the evidence.
