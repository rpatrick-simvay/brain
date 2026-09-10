# HaloPSA — Ticket Status ID Map (verified against the live API)

**Verified:** 2026-08-18 via `halo_get "Status"` (read-only).
**Re-verified:** 2026-08-21, **2026-08-26**, **2026-09-01**, **2026-09-04** and again **2026-09-07** —
the API still returns exactly the values below. See "Drift watch" at the bottom: the skill-side copy
has now reverted **five times** and is still wrong as of 7 September.
**Why this doc exists:** the status map carried in the morning-brief skill reference had
**32 labelled "Ready to Invoice"**. That is wrong, and it is wrong in a way that quietly
corrupts two different reads — the sales pipeline and the SLA breach count. Recorded here so
the correct values survive outside any one skill folder.

## The correction

| ID | Correct name | What the old table said |
|---|---|---|
| 32 | **Stale** | ~~Ready to Invoice~~ |
| 34 | **Ready to Invoice** | *(absent)* |
| 20 | **Completed** | *(absent)* |

Status **1 New** auto-flips to **32 Stale** after 4 working hours with no change
(`statuschangeto: 32`, `statusnochangehours: 4`, `useworkinghours_statusnochangehours: 2`).
So a NEW ORDER communication ticket raised in the morning is routinely sitting in Stale by
the afternoon — that is the intake timer working, not a neglected order.

## Full map as returned by the API

| ID | Name | SLA action |
|---|---|---|
| 1 | New | removehold |
| 2 | In Progress | removehold |
| 3 | Action Required | none |
| 4 | With User | **hold** |
| 5 | With Distributor | **hold** |
| 9 | Closed | none |
| 10 | With CAB | none |
| 12 / 13 | Open Order / Closed Order | none |
| 14 / 15 | Open Item / Closed Item | none |
| 16 | Invoiced | none |
| 17 / 18 / 19 | Awaiting Approval / Approved / Rejected | none / removehold / removehold |
| 20 | **Completed** | none |
| 21 | On Hold | none |
| 22 | Updated | removehold |
| 23 | Scheduled | **hold** |
| 24 | Qualified | none |
| 25 | Awaiting Change Review | none |
| 26 / 27 | Quote Raised / Quote Sent | none |
| 28 | Scoped | none |
| 29 / 30 | With Halo / With Halo Development | none / **hold** |
| 31 | Draft | none |
| 32 | **Stale** | none |
| 33 | With 3rd Party | **hold** |
| 34 | **Ready to Invoice** | none |
| 35 | Traveling | **hold** |
| 36 | A1 Investigating | none |
| 37 | A1 Remediated — Awaiting Auto-Close | **hold** |
| 38 | A1 Suppressed — Decommissioned | **hold** |

**Watch out for 21 "On Hold".** Despite the name its `slaaction` is **none**, so the clock keeps
running. A ticket in 21 past its fix-by *is* a live breach. Only the eight statuses marked
**hold** above stop the clock.

## Two traps this fixes

**Completed tickets come back in the open set.** Status 20 means the work is finished and only
the close is pending. Counting 20 as open inflates every "past fix-by" figure with work that is
already done. In the 18 Aug brief this was the difference between 9 and 7 genuinely open Cyber
Ops breaches, and between 51 and 21 live breaches org-wide once SLA holds were also excluded.

**Hold statuses are not breaches.** The SLA clock stops on 4, 5, 23, 30, 33, 35, 37, 38. A past
`fixbydate` on a ticket in one of those is expected, not a miss. Separate them before reporting
or the number reads as a crisis that is mostly Scheduled work.

## A third trap — `agent_id` is not an assignment filter

**Found 2026-09-01.** `get_tickets agent_id=14` does **not** return only tickets assigned to
agent 14. It returns Ryan's *visible working queue* — tickets on his teams and in his sections
as well as his own. On 1 September it returned 30 records; of the 10 non-Action1 tickets, only
**4** actually carried `agent_id: 14` (#51031, #50822, #51759, #51828). The other six belonged
to Gabe Lister (19), James Hering (20), Shane Goodsite (18), Stevie Kantor (28) and Unassigned (1).

**Consequence:** a brief that says "your queue" over this result is fine, but one that says
"assigned to you" or attributes ownership per ticket is wrong unless `agent_id` is re-checked
per record. The first send of the 1 Sep brief attributed #50849 (Gabe's) to Ryan for exactly
this reason, and had to be corrected.

**Do this:** after pulling `get_tickets agent_id=N`, re-read `agent_id` on every ticket before
naming an owner, and say "working queue" rather than "assigned to you" for the aggregate count.

## A fourth trap — the firm-wide sweep silently truncates at 500 KB

**Found 2026-09-04. Recurred 2026-09-07.** `halo_get "Tickets"` with `open_only=true` and a large
`count` returns a tool-results file capped at exactly **500,000 characters** with the JSON cut
mid-record. The call reports no error; only `json.JSONDecodeError: Invalid control character
at ... (char 500000)` reveals it.

On 7 September, `count=500` against 178 open tickets produced a 500,097-character file that
parsed to only **139 of 178** records after truncation repair — the missing 39 were the *oldest*
tickets, which is exactly where the long-running breaches live. A second call with
`paginate=true, page_size=60, page_no=3` returned the remaining 58 and the two sets merged to a
complete 178.

**Consequence:** a run that catches the exception and proceeds on "whatever parsed" reports a
breach count over a partial set, biased toward recent tickets, with no indication it is partial.

**Do this:** page the firm-wide sweep with `paginate=true, page_size=60..90, page_no=1..N`, and
**always assert the assembled record count against the `record_count` field in the response
header before computing anything.** On 7 Sep that assertion is what caught the gap.

## Worked example — 21 Aug 2026 Cyber Ops queue

A complete 58-of-58 pull of team 17 (Cyber Ops Analysts), for anyone wanting to sanity-check
the split against real numbers:

| Slice | Count |
|---|---|
| Open tickets on the team | 58 |
| Action1 pipeline (36 / 37 / 38) | 32 |
| Real tickets | 26 |
| Real tickets past `fixbydate` | 20 |
| — of those, **live breaches** | **8** |
| — of those, **Completed (20)** awaiting close | 10 |
| — of those, **on SLA hold** (4 / 23 / 33 / 35) | 2 |

Reporting the raw 20 overstates the miss by 2.5×. The ten in Completed that morning were
almost all Cyber Hygiene Report and KnowBe4 tickets from 15–17 August — worked, never closed
out. That is a closure-workflow observation worth making on its own, but it is not a breach.

## Worked example — 26 Aug 2026 Ryan's queue (`get_tickets agent_id=14`)

Smaller, and it shows both traps firing at once on a ten-ticket queue:

| Slice | Count |
|---|---|
| Open tickets returned | 30 |
| Action1 pipeline (36 / 37 / 38) | 20 |
| Real tickets | 10 |
| Real tickets past `fixbydate` | 6 |
| — of those, **live breaches** | **5** |
| — of those, **on SLA hold** (#51828, status 4 With User) | 1 |
| Plus **Completed (20)** with a fix-by later today (#51905) | 1 |

**The first send of the 26 Aug brief reported 6 breaches and had to be corrected to 5** — exactly
the failure this doc exists to prevent, on a queue small enough that the error was one ticket.
#51828 (Polaris, *Fw: TP Roboguide connection*) went back to the client on 18 August; its clock
stopped there, so its 19 August fix-by is not a miss. The correction was applied to the page and
the filed OneDrive copy, and disclosed in the follow-up notification.

**Lesson worth keeping:** the hold-status check is cheap and it is easy to skip when the queue is
small and the mapping "past fix-by = breach" feels obvious. Run it every time, not just on
firm-wide sweeps.

## Worked example — 1 Sep 2026 firm-wide sweep

The largest sample so far, and the clearest illustration of how far the raw number drifts:

| Slice | Count |
|---|---|
| Open tickets, whole instance | 183 |
| Action1 pipeline (36 / 37 / 38) | 50 |
| Raw "past `fixbydate`" sweep | 55 |
| — of those, **on SLA hold** (4 / 5 / 23 / 30 / 33 / 35 / 37 / 38) | 25 |
| — of those, **Completed (20)** awaiting close | 2 |
| — **live breaches** | **28** |
| Live breaches in Cyber Ops (team 17) | 9 |
| Live breaches in Ryan's working queue | 6 |
| Live breaches actually assigned to `agent_id 14` | 3 |

**The raw 55 overstates the real position by roughly 2×.** The first send of the 1 Sep brief
published 55 / 11 / 7 and had to be corrected to 28 / 9 / 6 after this doc was read. #50976
(Brooklyn SRM Compliance Tracking, status 4 With User) and #51825 (BMF Pen Test, status 20
Completed) were the two rows demoted to context-only.

**Note #50822 and #51828 both sit in status 21 On Hold and still count** — 21 does not stop the
clock. That is the trap inside the trap: "On Hold" reads like a hold status and is not one.

## Worked example — 4 Sep 2026 firm-wide sweep

**The first run to publish a correct breach count on the first send.** The filter was applied
before the page was written rather than after, which is the whole point of the standing
instruction below.

| Slice | Count |
|---|---|
| Open tickets, whole instance | 186 |
| Action1 pipeline (36 / 37 / 38) | 57 |
| Real tickets | 129 |
| Raw "past `fixbydate`" sweep | 54 |
| — of those, **on SLA hold** | 26 |
| — of those, **Completed (20)** awaiting close | 6 |
| — **live breaches** | **22** |
| Live breaches in Cyber Ops (team 17) | 5 |
| Live breaches actually assigned to `agent_id 14` | 2 (#50822, #51759) |

Raw 54 → live 22, again a ~2.5× overstatement if unfiltered. #50822 (*Review | Device Code
Flow*, 87 days past) and #51419 (*Monroeville Client Offboarding*, 48 days past) are both in
status 21 **On Hold** and both count — the same pair of names keeps appearing in this row, which
is itself a signal that status 21 is being used as though it stopped the clock.

Ryan's own queue that morning: 29 records → 20 Action1 (North Royalton 10, Bober Markey
Fedorovich 10), 9 real.

## Worked example — 7 Sep 2026 firm-wide sweep

| Slice | Count |
|---|---|
| Open tickets, whole instance | 178 |
| Action1 pipeline (36 / 37 / 38) | 57 |
| Real tickets | 121 |
| Raw "past `fixbydate`" sweep | 54 |
| — of those, **on SLA hold** (4 / 5 / 23 / 30 / 33 / 35) | 28 |
| — of those, **Completed (20)** awaiting close | 3 (52001, 52004, 52027) |
| — **live breaches** | **23** |
| Live breaches in Cyber Ops (team 17) | 4 (51419, 51759, 51920, 51996) |
| Live breaches actually assigned to `agent_id 14` | 1 (#51759) |

**#51419 Monroeville Client Offboarding is in the list again, in status 21 On Hold, now 51 days
past.** That is the third consecutive firm-wide sweep in which the same ticket appears in the
"On Hold but still breaching" row. It has been sitting there since at least 1 September and is
either genuinely stalled or is being parked in 21 deliberately by someone who believes that
stops the clock. **Worth asking Ryan directly rather than re-reporting it a fourth time.**

### The failure this run actually made

**The 7 Sep brief published 25 live breaches on first send and was corrected to 23.** The cause
was not the status map — the map was read correctly and 32/34/20 were all labelled right. The
cause was the *hold set itself being wrong in the filter code*:

- **21 On Hold was wrongly included** in the hold set, excluding #51419 from the count.
- **20 Completed was wrongly excluded** from the hold set, so 52001/52004/52027 were counted
  as live breaches.
- **5 With Distributor and 30 With Halo Development were both omitted** from the hold set.

Those errors partly cancelled (−1 and +3, net +2), which is the dangerous part: a wrong filter
produced a plausible-looking number. The page, the OneDrive copy and the notification all had to
be corrected.

**Root cause: this doc was read *after* the page was drafted, not before.** The run consulted it
during the post-build project-update step, which is when the discrepancy surfaced. Had it been
read at the point the sweep was computed, the filter would have been right the first time.

**Do this:** on any run that reports SLA numbers, `project_read` this doc **before** writing the
breach filter, and copy the hold set from the table verbatim rather than reconstructing it from
memory. The correct set is exactly:

```python
HOLD = {4, 5, 23, 30, 33, 35, 37, 38}   # SLA clock stops
EXCLUDE_ALSO = {20}                      # Completed — work done, awaiting close
# 21 On Hold is NOT in either set: the clock runs, it counts as a live breach.
```

## How to re-verify

```
halo_get path="Status" query={}
```

Returns every status with `name`, `slaaction`, `statuschangeto` and `statusnochangehours`.
Cheap call, no pagination. Run it before trusting any hard-coded status table — status records
are editable in Halo config, so this map is a snapshot, not a constant.

## Drift watch

**The skill-side copy has reverted, five times.** On 2026-08-21 the synced
`simvay-morning-brief/references/halopsa-queries.md` was found still carrying the old table
with **32 = Ready to Invoice** and no entry for 20 or 34, despite the in-place correction
recorded on 2026-08-18. **Re-checked 2026-08-26: still wrong. 2026-09-01: still wrong.
2026-09-04: still wrong. 2026-09-07: still wrong — identical old table, still no mention of
hold statuses, still no entry for 20, 21, 34.** The synced skill directory is replaced from an
upstream source, so edits made inside it do not survive.

**Consequence:** any run that trusts the skill reference instead of this doc will mislabel the
sales pipeline and inflate the breach count. The 21 Aug brief hit exactly this and had to be
corrected after the fact. The 26 Aug brief hit it again — 6 instead of 5. **The 1 Sep brief hit
it a third time and shipped 55 / 11 / 7 before correction to 28 / 9 / 6. The 7 Sep brief shipped
25 before correction to 23** — a different mechanism (bad hold set rather than bad status label)
but the same root condition: the authoritative table was not in front of the run when the filter
was written.

**Six occurrences in twenty-one days on the same file. Stop trying to fix it in place.** The fix
has to happen upstream of the sync, or the skill reference has to be replaced with a pointer to
this doc rather than a copy of the table. **Worth raising with Ryan alongside Runbook 12 §13.2 —
this is now the longest-running known-wrong artefact in the stack, and it has now caused a
first-send error in four of the last six briefs.**

**Standing instruction for future runs:** treat *this* project doc as authoritative for status
IDs, not the skill's reference file. **Read it at the start of the run, before computing any
pipeline or SLA figure** — not at the end during the project-update step, which is when the
7 Sep run found its error. Re-run `halo_get "Status"` as well. Do not assume a fix inside the
synced skill folder persists. **Before publishing any breach count, filter out the hold statuses
(4, 5, 23, 30, 33, 35, 37, 38) and status 20 explicitly, and confirm 21 is NOT filtered** — do
not rely on remembering to. Reading the live status map is not sufficient on its own; the 1 Sep
run *did* re-read the map, correctly identified 32 as Stale, and still shipped an inflated count
because the hold filter was not applied, and the 7 Sep run read the map correctly and still
shipped an inflated count because the hold set was wrong. **Verify the map, then apply the filter
from the code block above verbatim — they are two separate steps and the second is the one that
gets skipped or improvised.** The 4 Sep run applied both before writing the page and published 22
correctly on the first send; that is the sequence to copy.

## Related

- Morning-brief skill reference `references/halopsa-queries.md` — corrected 2026-08-18,
  **found reverted 2026-08-21, 2026-08-26, 2026-09-01, 2026-09-04 and 2026-09-07**. See Drift
  watch above.
- Runbook 12 §9.2 — carries the same correction alongside the other Halo API gotchas, plus the
  full live status set as read on 2026-08-26.
- Runbook 12 Appendix — *Brief export base64 truncation* (2026-09-04): the OneDrive upload can
  silently truncate a large embedded logo; verify the returned byte count against the local file.
  **7 Sep note:** resampling the white S-mark to 124px tall (2× its 62px display height) cuts the
  embedded base64 from 11,348 to 4,300 characters with no visible change, which both shrinks the
  inline upload payload and reduces truncation exposure. Byte count still verified against the
  local file on every upload.
- Runbook 07 (Travel Notifications) — covers status-change timers and the workflow-step
  constraint on which statuses are selectable on a given ticket.
