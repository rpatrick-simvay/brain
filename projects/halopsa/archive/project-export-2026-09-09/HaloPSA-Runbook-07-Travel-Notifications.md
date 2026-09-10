# Simvay HaloPSA — Runbook 07: User Travel (Travel Notifications) & Travel Conditional Access

> **Status:** BUILT in Halo 2026-07-23 (see §5 as-built record). Custom reclassification action
> added 2026-08-10 (§5c). Auto-complete-at-return-date investigated and **closed out** 2026-08-10
> — native status timer ruled out, and Ryan decided not to automate at all; the SLA hold
> auto-release stands as the return-date mechanism (§5d). Entra per-tenant pre-stage (§3) not yet
> started — that is the remaining project phase.
> **Scope:** The end-to-end travel notification workflow: HaloPSA ticket type, statuses,
> workflow, and portal intake (all clients), plus the Entra ID / Intune conditional-access
> travel exception process (fully managed clients only).
> **Last updated:** 2026-08-10 (§5d — status-timer experiment + decision to not automate)

---

## 1. Purpose & decision log

Users at client organizations notify Simvay before traveling (domestic out-of-state or
international). Simvay records the trip, and for **international travel at fully managed
clients** temporarily adjusts Conditional Access so the traveler can work from the
destination country — with access auto-expiring at trip end. Travel tickets also give SOC
analysts situational awareness when geo/impossible-travel alerts fire.

**Decisions locked 2026-07-23 (grilling session with Ryan):**

| # | Decision |
|---|---|
| 1 | Design + approval first; build in Halo (Chrome) only after doc sign-off |
| 2 | Intake: dedicated portal form **and** email (agents reclassify emails to the type) |
| 3 | Scope: domestic out-of-state **and** international; only international triggers CA work |
| 4 | Form fields: travel type, destination(s), depart/return dates, devices, email-on-phone, callback contact |
| 5 | Owning team: **Cyber Ops (Analysts)** |
| 6 | Statuses: reuse New / In Progress / Closed; **one new status: Traveling** (SLA hold, distinct color) |
| 7 | Revert trigger: ticket placed on hold until **return date**; popping off hold = do/verify the revert |
| 8 | CA removal automated: **PIM for Groups** active assignment with expiration (Graph-sweep fallback documented for strict licensing) |
| 9 | CA geographic scope: **country-scoped** — shared "Active Travel Countries" named location, not a blanket geo-block exclusion |
| 10 | Device posture abroad: compliant corporate laptop = full access; phone = **Outlook only with App Protection Policy (MAM)**; unmanaged devices blocked |
| 11 | Entra/Intune plumbing **pre-staged in all fully managed tenants** up front; portal Travel Notification section under **User Lifecycle** finished as part of the build (wire-up + form) |
| 12 | Ticket type is named **"User Travel"**; agents can manually create it too (email intake reclassification + phone-in) |
| 13 | **Always lowest SLA:** default SLA = **NO SLA (id 5)**, priority **Low (4)** — precedent: Contract Renewal (type 38) also uses NO SLA. Travel tickets never generate SLA pressure |
| 14 | **Minimal mandatory portal fields** (match the Support type's lightweight intake): only **destination(s), depart date, return date** are required; everything else optional or agent-side |
| 15 | Domestic trips ALSO sit in **Traveling** until return (zero CA work) so the analyst "is this user traveling?" check covers domestic impossible-travel alerts; they auto-surface and close on return |
| 16 | *(2026-08-10)* Email-intake reclassification is done with a **one-click action**, not manual type + status edits — see §5c |
| 17 | *(2026-08-10)* **No auto-completion at the return date.** The SLA hold auto-release is the mechanism; the ticket surfaces in the Cyber Ops queue and an analyst closes it. Ryan explicitly declined both the native timer (which cannot do it — §5d) and a scheduled Worker sweep. **Do not re-propose this without being asked.** |

---

## 2. HaloPSA build specification

### 2.1 Ticket type: "User Travel"

Create at **Config → Tickets → Ticket Types → New** (Chrome only; connector is read-only).
**Model on Support (id 1)** — per Ryan, Support and Event are the only ticket types actively
used today, so User Travel should behave like Support's intake, not the legacy types.
Support's verified config (read-only, 2026-07-23): initial_status 1 (New),
statusafteruserupdate/reopenedstatus 22 (Updated), portalcanreopen true, workflow_id 19,
default_agent −92 (team load-balance pattern).

> **Build note:** Support flips to **Updated (22)** when a user replies. For User Travel
> that's desirable mid-trip (e.g. "extending my trip") — but verify at build that a user
> update while in **Traveling** surfaces the ticket without cancelling the off-hold date;
> the agent re-sets Traveling (with the new return date if changed) after handling it.

| Setting | Value | Rationale |
|---|---|---|
| Name | `User Travel` | decision #12 |
| Use | Tickets | |
| Sequence | ~20 (after Support/Event) | sits with the actively-used types |
| ITIL request type | Service Request (3) | it's a request, not an incident |
| Default team | **Cyber Ops (Analysts)** | decision #5 |
| Default agent | team load-balance, same pattern as Support (−92) | confirm at build |
| Default SLA | **NO SLA (id 5)** | decision #13 |
| Default priority | **Low (4)** | decision #13 |
| Agents can select | **Yes** | decision #12 |
| End users can select | **Yes** | portal intake |
| Anonymous can select | No | requester identity matters (CA changes) |
| Allow attachments | Yes | itinerary screenshots |

### 2.2 Custom fields (Entity: Ticket, shown on the type's field list + portal form)

All prefixed `CF` automatically. **Only three portal-mandatory fields** (✱) — decision #14.

| Field | Type | Portal | Notes |
|---|---|---|---|
| ✱ `CFTravelDestinations` | Text/Memo | **Required** | state(s) or country(-ies); multi-stop allowed |
| ✱ `CFTravelDepartDate` | Date | **Required** | |
| ✱ `CFTravelReturnDate` | Date | **Required** | becomes the on-hold/expiry date |
| `CFTravelDevices` | Multi-select | Optional | triage anomaly reference |
| `CFTravelEmailOnPhone` | Checkbox | Optional | do they need mobile mail abroad |
| `CFTravelContact` | Text | Optional | callback method while traveling |
| `CFTravelType` | Single select | **Agent-only** | set at triage from the destination |

> ⚠ **These fields are only populated on portal-submitted tickets.** Every real travel ticket
> so far arrived by **email**, so 272 (`CFTravelReturnDate`) is empty on all of them and the
> return date exists only as prose in the body. **Never key automation or reporting off field
> 272** — use the SLA hold release date the analyst sets in the Convert to Travel action
> (§5c, §5d).

### 2.3 New status: "Traveling" (the only status addition)

| Setting | Value |
|---|---|
| Name / short name | `Traveling` |
| SLA action | **Hold** |
| Color | `#e91e63` |
| Show on quick change | Yes |
| Change Status after N hours | **0 — leave alone. It is wall-clock and ignores hold; see §5d.** |

All other lifecycle states reuse the existing pool: **New (1), In Progress (2), Closed (9)**.

### 2.4 Workflow / lifecycle

```
                 ┌── domestic ──► Traveling (hold until return) ──► auto-surface ──► Closed
New ── triage ───┤
                 └── international (fully managed) ──► In Progress (CA/MAM prep)
                                                          │
                                                          ▼
                                    Traveling (hold until CFTravelReturnDate)
                                                          │  (PIM expiry fires during this window)
                                                          ▼
                                    off-hold on return ──► verify auto-removal, remove country ──► Closed
```

- **On-hold mechanics:** when the agent sets **Traveling**, use the action's *on hold until*
  date = the return date. When the date passes, Halo takes the ticket off hold and it
  reappears in the Cyber Ops queue — that reappearance IS the revert prompt, and closing it is
  a manual analyst step by design (decision #17). **As of 2026-08-10 the "Convert to Travel"
  action exposes the SLA Hold/Release control so the release date can be set at the moment of
  conversion (§5c).**
- **International at a NON-fully-managed client:** no CA work is possible/contracted.
  Acknowledge with the limited-support reply, still track in Traveling, close on return.

### 2.5 Portal: Travel Notification section (User Lifecycle)

Entry under User Lifecycle → `/portal/newticket?tickettype_id=40&btn=<btn id>`. The new-ticket
form inherits the V10 dark/glass styling automatically. ✱ fields marked required.

### 2.6 Notifications & templates

1. **New User Travel ticket** → notify Cyber Ops (Analysts).
2. **Off-hold (return date reached)** → notify assigned agent/team: "verify travel access removal."
3. **User acknowledgment template** (client-facing, on ticket creation).

---

## 3. Entra ID / Intune — travel conditional access (fully managed clients only)

### 3.1 Standing per-tenant infrastructure (pre-staged in ALL fully managed tenants)

One-time rollout, ~30–45 min/tenant (scriptable via Graph). Naming uses the `SVY-` prefix.

| # | Object | Configuration |
|---|---|---|
| 1 | Security group `SVY-Travel-CA-Exception` | Assigned (NOT dynamic — PIM requirement). **Onboard to PIM for Groups**; active assignments with expiration, no approval required for Simvay admins. |
| 2 | Named location `SVY-Active-Travel-Countries` | Countries location (IP-geolocation based; do NOT check "include unknown/unmapped"). Starts **empty**. |
| 3 | CA policy `SVY-CA-Travel-01 Geo scope` | (a) **exclude** the travel group from the tenant's baseline geo-block policy; (b) new policy: include ONLY the travel group; all locations EXCEPT home allowed location(s) and `SVY-Active-Travel-Countries`; **Block**. |
| 4 | CA policy `SVY-CA-Travel-02 Mobile = Outlook w/ APP` | Travel group only; iOS + Android; Office 365 Exchange Online; grant **Require app protection policy**. |
| 5 | CA policy `SVY-CA-Travel-03 Desktop = compliant device` | Travel group only; Windows/macOS; grant **Require compliant device**. Mark N/A if the tenant baseline already enforces it. |
| 6 | Intune App Protection Policy `SVY-Travel-APP-Outlook` (iOS + Android) | Target Outlook. PIN, encryption, block save-as, restrict cut/copy/paste to policy-managed apps, block backup, offline grace then selective wipe. |

Deploy new CA policies in **report-only** first, or rely on the empty include group. Keep a
**per-tenant rollout tracker**.

### 3.2 Licensing note (recorded honestly)

PIM features are lit via an Entra P2 license on the Simvay GA account; client users are
Business Premium (P1). Microsoft's licensing terms require P2/Governance for users
*benefiting* from PIM, so this is out-of-license (acknowledged by Ryan, working for now).
**Strict-compliance fallback:** skip PIM; a scheduled Graph PowerShell sweep (hourly) reads
an expiry timestamp stamped at add-time and removes members whose expiry passed.
[PIM for Groups concepts](https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/concept-pim-for-groups) ·
[extend/renew assignments](https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/groups-renew-extend)

### 3.3 Per-trip execution (international, fully managed) — target ≤10 min

1. **Verify** the requester (callback if anything is off — this grants foreign sign-in access).
2. **PIM**: active assignment to `SVY-Travel-CA-Exception`, start = depart date, **end = return date + 1 day**.
3. **Named location**: add destination country/countries to `SVY-Active-Travel-Countries`.
4. **Pre-flight check**: Outlook on the phone signed in with the APP applied.
5. **Reply** with the acknowledgment template and set **Traveling** with on-hold until the return date.

### 3.4 Return / revert (ticket pops off hold)

| Trip type | Steps |
|---|---|
| International (fully managed) | 1. Confirm PIM removed the user from the group; remove manually if not. 2. Remove the destination country from `SVY-Active-Travel-Countries` — **unless another open Traveling ticket declares the same country**. 3. Optional: skim sign-in logs. 4. Close. |
| International (not fully managed) | Close after a welcome-back note. |
| Domestic | Auto-surfaced; nothing to revert; close. |

### 3.5 Alert-triage addendum (SOC situational awareness)

On any **geo / impossible-travel / risky sign-in location** alert, **first check for an open
ticket in status `Traveling`** for that user/client.

- Match AND sign-in country/state matches the declared destination → note the travel ticket
  reference, resolve as expected-travel.
- No match, or location ≠ declared destination → treat as genuine; escalate normally.

---

## 4. Build checklist

**Halo (Chrome UI — Runbook 01 safety rules apply):**

- [x] Create `Traveling` status (§2.3) — done, id 35
- [x] Create ticket type `User Travel` (§2.1) — done, id 40
- [x] Create 7 custom fields; attach to field list; set portal-required flags — done, ids 270–276
- [x] Portal section under User Lifecycle — done, service 123
- [x] **"Convert to Travel" reclassification action — done 2026-08-10, action id 101 (§5c)**
- [x] **Auto-complete at return date — investigated and declined 2026-08-10 (§5d). Closed.**
- [ ] Notifications + acknowledgment template (§2.6)
- [x] Test: portal submission end-to-end — ticket 51512
- [x] Update this runbook with as-built ids

**Entra/Intune (per fully managed tenant — separate rollout project):**

- [ ] Build §3.1 items 1–6; record deviations in the rollout tracker
- [ ] Dry-run one full trip in a test/internal tenant
- [ ] Publish the tenant tracker location here

**Effort:** Halo build ~2–3 hours. Entra pre-stage ~30–45 min/tenant. Per-trip steady state:
≤10 min analyst time + ~5 min at return.

---

## 5. As-built record (Halo build session, 2026-07-23)

| Object | ID / value |
|---|---|
| Status **Traveling** | **id 35** — sequence 136, color `#e91e63`, SLA action "Put on hold (if not on hold already)", "User updates release from SLA hold" = Yes, `statuschangeto` = 0 (no timer — deliberate, §5d) |
| Ticket type **User Travel** | **id 40** — sequence 20, Service Request, team Cyber Ops (Analysts), agent Unassigned, **SLA NO SLA (5) + Priority 1** (⚠ Halo rejects SLA/priority mismatches — see §5c for how this bites a second time), initial status New, agents + end users can select |
| Custom fields | CFTravelDestinations **270**, CFTravelDepartDate **271**, CFTravelReturnDate **272**, CFTravelDevices **273** (lookup 154), CFTravelEmailOnPhone **274**, CFTravelContact **275**, CFTravelType **276** (lookup 155, agent-only) |
| Field list (type 40) | Summary, Details, Departure Date✱, Travel Destination(s)✱, Best contact, Return Date✱, Devices, Email-on-phone, Travel Type (agent-only) |
| Portal wire-up | Service **"User Travel" id 123** (display name "Travel Notification", category User Lifecycle id 10) |
| End-to-end test | Ticket **51512** — portal submission captured all fields; Traveling flipped SLA to "On Hold" automatically |

**Follow-up changes (Ryan, 2026-07-23 evening):**

- Field order finalized (reordered by delete+re-add; drag/drop unreliable).
- **Workflow attached:** type 40 starts the **Cybersecurity Operations** workflow (same as Event).
- **Cybersecurity area (id 16)** ticket-type filter now Includes **Event, User Travel**.
- **Filter profile "User Travel Tickets"** created for the Cybersecurity area.
- **Portal service image removed** (service 123); portal CSS record 707 gained **`SIMVAY-PORTAL-V13`**.

**Team SOP:** **SOP-TRV-01 "User Travel" v1.0** (branded .docx, 2026-07-23), generated from §3.

**Build gotchas:** Halo config forms save on Enter — never press Return in a field. The
ticket-type Field List "Add" button next to the picker opens a NEW-custom-field modal — commit
picker chips with the modal **Save**. Field-row drag/drop only registers on longer drags.

## 5b. Entra as-built — Simvay tenant validation (2026-07-22 late evening)

| Object | As built |
|---|---|
| Group **SVY-Travel-CA-Exception** | Object id `70cef36e-a174-4104-b0c7-6fb00c4d9bdd`, Security/Assigned. PIM Groups discovers it automatically; active assignments require justification, max 6 months |
| Named location **SVY-Active-Travel-Countries** | Countries (IP), not trusted |
| CA **SVY-CA-Travel-01** | Travel group only · All resources · exclude "Approved Locations" (US) + SVY-Active-Travel-Countries · **Block** · On |
| CA **SVY-CA-Travel-02** | Travel group · Exchange Online · Android + iOS · **Require app protection policy** · On. ⚠ Report-only offers to exclude platforms — do NOT accept |
| Intune APP **SVY-Travel-APP-Outlook-iOS / -Android** | Outlook; backup Block, send org data → Policy managed apps; assigned to the travel group |

**What If validation (all passed, 2026-07-22):** Germany → Block ✅ · France (declared) → will not
apply ✅ · iOS/Exchange from France → Require app protection ✅. What If needs **both** an IP and a
matching Country; the Country dropdown is not searchable.

**PIM auto-expiry check (2026-07-23): PASSED** — group Members showed 0 after expiry, no manual action.

**Cleanup + constraint:** ⚠ Entra will NOT save a Countries named location with zero countries.
Convention: keep **United States** as the permanent placeholder.

**Team guide:** **CFG-TRV-01 "Travel CA — Client Tenant Configuration Guide" v1.0** (2026-07-23).

## 5c. Custom action "Convert to Travel" (2026-08-10)

**Purpose (Ryan):** a one-click reclassification for the common case — a travel notification
arrives by email and lands as an **Event** ticket in the Cyber Ops queue. The action converts it
to **User Travel** and parks it in **Traveling**, replacing two manual field edits.

### As built

| Object | Value |
|---|---|
| **Action id** | **101** |
| Name (outcome, shows in reporting) | `Converted to User Travel` |
| Button Name | **`Convert to Travel`** |
| Sequence in lists | 50 (same family as *Move to Cybersecurity* / *Move to Managed Technology*) |
| Button Icon / Colour | None / Default |
| Action button is visible | Yes |
| Action is visible outside of Workflows | Yes *(Halo default; every Event and User Travel ticket runs workflow 18 anyway, so this changes nothing in practice — untick it to make the button strictly workflow-only)* |
| Action Configuration Access Type | **Generic Action** (can be added to any workflow) |
| **Status After Action** *(Details tab)* | **Traveling (35)** |
| Show the "SLA Hold/Release" option | **Yes** — exposes the hold + auto-release date on the action screen |
| SLA Hold Auto-Release date must be set | **No** — optional, per Ryan 2026-08-10 |
| Enable auto release prompts | Yes |
| **Default Ticket Type** *(Defaults tab)* | **User Travel (40)** |
| Default Team / Default Agent | ***No Change*** — deliberately, so converting does not unassign whoever is working it |
| **Priority (0 = No Change)** | **1** — see the SLA/priority trap below |

**Workflow attachment:** added to **Cybersecurity Operations (workflow 18)** → Details →
**"Agent Actions allowed at any Step"**, joining Email User, Internal Note, Re-Assign, Child
Ticket Created, Triage, Claim, Move to Managed Technology. Workflow 18's stages
(1 Triage · 2 In Progress · 3 Escalated · 4 Resolved) were **not** touched.

> ⚠ Editing workflow 18 raises **"This workflow is in use, editing may cause issues with current
> workflow steps… recommended that you copy this workflow using Clone."** The change here is
> purely additive (one entry in the any-step action list), so **Save** was used, not
> *Save as new*. Cloning would fork the workflow and require re-pointing types 34 and 40 — far
> more disruptive than the risk it avoids. Use *Save as new* only for step/stage surgery.

### The SLA/priority trap — round two

Converting a normal Event ticket (4 Hour SLA, priority 3 Medium) to User Travel (NO SLA) raised:

> *"SLA and Priority combination is invalid. The original SLA (NO SLA) and Priority level (3) is
> invalid. Priority has been adjusted to NO SLA."*

Halo self-corrects, so the conversion still succeeds — but the analyst gets a modal every single
time. **Fix: set the action's Priority default to 1** (the same value the User Travel type itself
carries). This is the identical quirk recorded in §5 for the ticket type; it resurfaces anywhere
a NO SLA object inherits a priority from elsewhere. Re-tested clean afterwards.

### Verification (2026-08-10)

| Ticket | What it proved |
|---|---|
| **51719** (Simvay / Halo House, type Event) | Button appears in the ticket header. Action → Ticket Type **User Travel**, Status **Traveling**, SLA **NO SLA / On Hold**, team + agent unchanged, action logged as "Converted to User Travel". Surfaced the priority modal. |
| **51720** (same setup, after Priority=1) | Identical result, **no modal**. |

Both test tickets were closed after the test. Note: each test ticket fires notification rule 57
("NEW TICKET | Cyber Ops"), so it emails the whole Cyber Ops team — expect that when testing
anything on the Event type, and label test summaries clearly.

### Discoveries (also relevant to Runbooks 01 and 04)

- **The Actions config page is `/config/tickets/outcomes`.** `/config/tickets/actions` and
  `/config/tickets/action` both **404**. Halo calls actions "outcomes" internally; the left-nav
  item is labelled "Actions". Workflows are at `/config/tickets/workflow` (singular);
  `/config/tickets/workflows` 404s. **Statuses are at `/config/tickets/status` (singular)** —
  `/config/tickets/statuses` 404s.
- **An action's two effects live on two different tabs.** *Status After Action* is on the
  **Details** tab; *Default Ticket Type* (and team/agent/priority/category) are on the
  **Defaults** tab. There is no single "outcome" screen.
- **Workflows have a global action list** — Details → *"Agent Actions allowed at any Step"* —
  separate from the per-step action lists on the Flow Chart. Actions added there are available
  regardless of stage and **do not advance the workflow**.
- **`*No Change*` is an explicit option** on Default Team and Default Agent, and it is the
  default for a new action. Setting a team here would silently reassign; leave it alone unless
  reassignment is the point.
- **Actions carry a per-action `Send To PagerDuty` toggle** (Defaults tab, default No). Worth
  remembering for the HaloPSA→PagerDuty work — it is a native per-action push that neither the
  webhook nor the Service Mapping route documents.
- The **swallowed-first-Edit-click** gotcha (Runbook 01 §7.14) recurred on the action config
  record — click Edit, screenshot, click again if the toolbar still shows *Edit*.

### Not done / open

- The action does **not** populate `CFTravelDepartDate` / `CFTravelReturnDate` / destinations —
  an email-sourced ticket has none of that, so the analyst still fills them in. Adding those
  fields to the action's **Field List** tab would prompt for them inline at conversion; not done
  because Ryan asked for type + status only.
- The auto-release date is **optional**, so an analyst can still park a ticket on an indefinite
  hold by skipping it. Flip *"SLA Hold Auto-Release date must be set"* to Yes if that starts
  happening.

---

## 5d. Auto-complete at return date — investigated, then DECLINED (2026-08-10)

**Ask (Ryan, morning):** *"Set the ticket to change status to Completed when the return date has
passed rather than just updating the SLA hold."*
**Outcome (Ryan, same day, after the experiment below):** *"Let's not worry about the automation
then for status change, the SLA hold thing is fine."* — **decision #17. Closed; do not rebuild.**

**Candidate mechanism:** the status-level setting **"Change Status after this many hours (does
not recur)"** (`statuschangeto` + `statuschangetofreq` on `/api/Status`). If that clock paused
while the ticket sat on SLA hold, then `Traveling → 1 hour → Completed` would have given exactly
the requested behaviour: hold auto-releases on the return date, an hour later the ticket completes.

### The experiment

Run in isolation so the three live client travel tickets (51636 Cancun, 51630, 51623) were never
at risk:

| Step | Detail |
|---|---|
| Scratch status | **id 39 `ZZ TEST Hold Timer`** — SLA action **Hold**, `statuschangeto` = **20 (Completed)**, `statuschangetofreq` = **1** hour, Normal Hours, sequence 1009 |
| Test vehicle | Ticket **51726**, ticket type **Alert (21)** — chosen because `workflow_id: 0` and `allowall_status: true`, and zero Alert tickets have ever existed in the instance |
| Enter status | 2026-08-10 **18:48:51 UTC**, confirmed `onhold: true` via `/api/Tickets/51726` |
| Observed | 2026-08-10 **19:50:44 UTC** → `status_id: 20` (**Completed**), `onhold:` **still true**, `slaholdtime: 1.19` |

### Result: the clock does NOT pause on SLA hold

The ticket completed **62 minutes** after entering the status, having spent every one of those
minutes on hold. The timer is plain wall-clock from status entry and is blind to hold state.

**Therefore the timer approach is unsafe for Traveling.** Enabling it on status 35 would have
completed the three live travel tickets N hours after conversion, with no relationship to any
return date. **Leave `Traveling.statuschangeto` at 0.**

### Two further findings from the same run — keep these

1. **A timer-driven status change does not release the hold.** 51726 ended up `Completed` **and**
   `onhold: true` simultaneously. Any status set by a timer inherits the *new* status's
   `slaaction`, and Completed's is `none` (= no change), so the hold survives. Watch for
   Completed-but-held tickets anywhere a timer is used.
2. **Statuses are constrained by the workflow step, not the ticket type.** The scratch status was
   invisible in both the quick-change dropdown and the Re-Open action's picker on ticket 51719
   (a workflow-18 ticket), returning "No results found" for "ZZ" — while being freely selectable
   on the workflow-less Alert type. When a status will not appear on a ticket, look at the
   workflow step's allowed-status list before suspecting the status record itself.

### Native alternatives assessed (all rejected — recorded so nobody re-walks this)

| Mechanism | Verdict |
|---|---|
| Status "Change Status after N hours" | ❌ Fixed hours, wall-clock, ignores hold (proven above) |
| Status `timeuntilloffhold` (auto off-hold after N hours) | ❌ Also fixed hours; releases hold but does not set status |
| SLA hold auto-release date | ✅ Fires on the right date, but only clears the hold — there is no native "status to set on hold release" field on the Status record. **This is what Simvay uses.** |
| Config → Tickets → **Automated Tickets** | ❌ Creates *new* tickets from criteria (the only existing rule is "Expiring Agreements \| 90 Days"); it does not update existing tickets |
| Config → Tickets → **Rules** | ❌ Event-driven field mapping at create/update, not scheduled |
| Scheduled sweep in the `halopsa` Cloudflare Worker | ⛔ Technically viable (~1–2 h: cron → `GET /api/Tickets?status_id=35&open_only=true` → for each `onhold == false`, `POST {id, status_id: 20}`) but **Ryan declined it.** Not built. |

### Cleanup — done

- [x] Scratch status **39 `ZZ TEST Hold Timer`** deleted (Halo warns status deletion is permanent
      and cannot be rolled back; confirmed clean via `/api/Status`).
- [x] Test ticket **51726** set to **Closed**.
- [x] Verified `Traveling` (35) is untouched: `statuschangeto: 0`, `statuschangetofreq: 0`,
      `slaaction: hold`.

---

## 6. References

- Runbook 01 (Chrome techniques, save gotchas), Runbook 03 (email templates), Runbook 04
  (notification rules + intake-default trap), Runbook 06 (portal tiles, V10 form styling)
- Microsoft: [PIM for Groups](https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/concept-pim-for-groups) ·
  [PIM assignment extend/renew](https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/groups-renew-extend) ·
  [CA: require approved app / app protection policy](https://learn.microsoft.com/en-us/entra/identity/conditional-access/policy-all-users-approved-app-or-app-protection) ·
  [CA: require APP for Windows](https://learn.microsoft.com/en-us/entra/identity/conditional-access/policy-all-users-windows-app-protection)
