# Simvay HaloPSA — Runbook 04: Notifications (Agent Alerting)

> **Scope:** Config → Notifications — rule inventory, per-rule anatomy, general settings, and the
> browser techniques for auditing them. Companion to the full audit report
> (`claude/HaloPSA-Notifications-Audit-2026-07-17.md`) and Runbook 03 §6.
>
> **Last updated:** 2026-08-17 (**§7 NEW — the popup layer is a SEPARATE template family**;
> Sales Order Created popup cleaned up)

## 0. Change record

### 2026-08-17 — NEW SALES ORDER popup template cleaned up (Ryan / Kris)

**Driver:** Kris flagged the in-Halo popup for new sales orders — it printed `$PRIMARYAGENT`
and `$SECONDARYAGENT` literally (dead variables), and the money labels were too verbose.

**Key discovery (see §7):** the popup text does **NOT** come from the email template
(−115 "NEW SALES ORDER (Internal)") and there is **no popup-template field on the
notification rule**. It comes from **Config → Notifications → Notification Templates →
"Sales Order Created"** (`/config/notifications/templates?id=65`), which Halo selects
**by event name**, automatically.

**Applied to template 65** (verified after reload):

```
NEW SALES ORDER - $AREA

Sales Order ID: $ORDERID
Sales Order Title: $ORDERTITLE
Sales Order Date: $ORDERDATE

Purchase Order: $ORDERPO

T: $ORDERTOTAL
C: $ORDERCOST
M: $ORDERPROFIT

Order Notes: $ORDERNOTES
```

Removed: `Primary Agent: $PRIMARYAGENT` and `Secondary Agent: $SECONDARYAGENT` lines.
Renamed: `Order Total/Cost/Profit` → `T/C/M` (Ryan's explicit choice, 2026-08-17).

**Variables that do NOT resolve on Sales Order popups:** `$PRIMARYAGENT`, `$SECONDARYAGENT`.
Both print literally. Do not reintroduce them. Working ones (confirmed by Kris's live popup):
`$AREA`, `$ORDERID`, `$ORDERTITLE`, `$ORDERDATE`, `$ORDERPO`, `$ORDERTOTAL`, `$ORDERCOST`,
`$ORDERPROFIT`, `$ORDERNOTES`.

### 2026-08-04 — Cyber Ops notification rebuild (Ryan)

**Driver:** Ryan was being auto-assigned Cybersecurity tickets, and workflow-step-started emails
were noise. Decision: cyber tickets arrive **unassigned** on Cyber Ops (Analysts), and the team
gets email on exactly three events — **new ticket, client update, ticket closed**.

**Deleted:**

| Rule | Why |
|---|---|
| **27 "NEW TICKET \| Cyber"** | Fired on **Workflow Step Started** — the noisy trigger Ryan asked to kill. Its config for reference: Team Notification → Cyber Ops (Analysts), Send an Email, custom popup colour `#fda1ff`, template −103 "NEW TICKET", criteria `Team = Cyber Ops (Analysts)` + `Ticket Type ≠ Project Task` + `Ticket Type ≠ Action1`. **No "Workflow Step Started" notification exists anywhere in the instance now.** |

**Created — three Team Notifications, all to Cyber Ops (Analysts), all Send an Email, all with
the same three criteria (`Team = Cyber Ops (Analysts)` AND `Ticket Type ≠ Action1` AND
`Ticket Type ≠ Project Task`):**

| ID | Name | Event | Template |
|---|---|---|---|
| **57** | `NEW TICKET \| Cyber Ops` | **New Ticket Logged – All** | NEW TICKET |
| **58** | `CLIENT UPDATE \| Cyber Ops` | **Ticket Updated by User – All** | Technician Update |
| **59** | `TICKET CLOSED \| Cyber Ops` | **Closed – All** | Technician Update |

Team Notification = "notify all members of the specified Team", so all of Gabe Lister, James
Hering, Shane Goodsite, Stevie Kantor **and Ryan Patrick** (team manager, member of team 17)
receive these. There is no per-recipient exclusion on a Team Notification — to drop Ryan he
would have to leave team 17, or these would have to be rebuilt as Agent Notifications with an
explicit subscriber list.

**Still open / worth noting:**

- Rule **30 "Ticket Update by User | Cybersecurity"** (Agent Notification, 6 subscribers, event
  *Ticket Updated by User – Assigned to Recipient*) is now largely redundant and, with cyber
  tickets arriving unassigned, will rarely fire. Rule 58 supersedes it. Consider deleting.
- Action1 tickets remain deliberately silent (excluded from all three rules), per Runbook 08 §7.
  **But see §4.1 — the `Ticket Type ≠ Action1` exclusion leaks badly and rules 57/58/59 are
  emailing the team roughly 18 Action1 endpoint-offline tickets a week regardless.**

### 2026-08-04 — Client-level auto-assign turned off for Ryan's 8 cyber clients

**Root cause of "I keep getting assigned Cybersecurity tickets":** it was **not** the ticket
type. Every cyber ticket type (Event 34, Alert 21, Action1 41, User Travel 40, New Starter 17,
Business Review 29, Cyber Ops Daily Activity Report 36) already has `default_agent = 1`
(Unassigned). The assignment came from the **client record**:

> Client → Edit → **Assigning and Account Manager** → *Primary Agent* + checkbox
> **"Assign new Tickets to the Primary Agent"** (API field `priassign`, agent in `pritech`).

Ryan was Primary Agent with that box ticked on 8 clients. **Unticked on all 8 on 2026-08-04:**

| Client | id | Contracts (all security-only — no EMTS/MSA) |
|---|---|---|
| Avon Local Schools | 36 | ISM, S1, Umbrella, C2, SRM |
| Bober Markey Fedorovich | 39 | A1, S1 |
| Hinkley Lighting | 42 | S1 |
| Monroeville Local Schools | 43 | S1, A1 |
| North Royalton City Schools | 44 | A1, S1 |
| Western Reserve Local Schools | 54 | — |
| Huron City Schools | 57 | — |
| Polaris Career Center | 59 | Umbrella, MDR |

**Managed Technology's auto-assign is untouched** — no EMTS/MSA client was modified, and the
MT primary techs (Chajon 23, Mazzaro 29, Goetz 17, Karenke 21) keep their flags.

**Important interaction:** the **Support** ticket type (id 1) has `default_agent = -92` =
*Primary Agent*, which is a **separate** mechanism from the client `priassign` flag. Support
tickets for these clients still route to the Primary Agent regardless of the client checkbox.
Ryan intends to hand off Primary Technician on these clients to his analysts separately — that
is what will move Support-type work off him.

**Why Fairview Park behaved differently:** Fairview (19) has `priassign = true` with `pritech = 23`
(Chajon), yet its connector-created Action1 tickets came in Unassigned. Working theory: Halo only
applies the primary-agent auto-assign when that agent is a member of the ticket's team — Chajon is
in Support (Sys Admins), not Cyber Ops (Analysts), so the assign is skipped; Ryan **is** in team 17,
so his fired. Not formally proven; re-test if it matters.

## 1. Where things live (URLs)

| Thing | URL |
|---|---|
| Notification rules list + detail | `/config/notifications/notifications` (detail: `?id=N`; **`?id=-1` opens a blank New Notification form**) |
| Notification General Settings | `/config/notifications/settings` — **`/config/notifications/general` 404s**; reach it via the left submenu or this exact path |
| Notification (popup) Templates | `/config/notifications/templates` (detail: **`?id=N`** — see §7) |
| Ticket Types list (shows default Team/Agent/Workflow columns) | `/config/tickets/tickettype` (detail `?id=N`; Support = id 1) |
| **Client record** (auto-assign lives here) | `/customers?mainview=client&clientid=N` → Edit → *Assigning and Account Manager* |

## 2. Rule inventory (2026-08-04): 27 rules

ID map for `?id=N`: 1 MENTION · 21 APPROVED QUOTE · 22 NEW SALES ORDER · ~~27 NEW TICKET | Cyber~~ **(deleted 2026-08-04)** · 29 PURCHASE ORDER ISSUED · 30 Ticket Update by User | Cybersecurity · 32 INVOICE PAID · 37/38 UNASSIGNED New/Updated Support · 41 TICKET FEEDBACK · 42/43 OSWALD Updated/New · 44/45 UNASSIGNED New Opportunity/Lead · 46–49 MAZZARO/CHAJON/GOETZ/KARENKE NEW · 50–53 KARENKE/CHAJON/GOETZ/MAZZARO UPDATED · 54/55 UNASSIGNED Updated Opportunity/Lead · 56 ORDER to INVOICE · **57 NEW TICKET | Cyber Ops · 58 CLIENT UPDATE | Cyber Ops · 59 TICKET CLOSED | Cyber Ops**.

Key facts (full detail in the audit doc):
- **Agent Notification** detail shows: Description, Type, Access Restriction, Default Delivery Method, popup/browser-push/mobile-push Y/N, Trigger Event, conditions table, Template for Email/SMS. Tabs: **Setup / Agents / Roles** — the Agents tab lists subscribers as alternating `Name / Inherited-from-Role` lines.
- **Team Notification** has a different layout: Team field instead of subscribers, single "Delivery Method", no popup/push rows, no Agents tab.
- 17 of 25 (pre-change) rules are email + popup + browser push + mobile push. 13 use template **#32 Technician Update** (body still stock).
- Known defects found (do not re-discover): rule **54** pairs event "Updated by User – Assigned to Recipient" with condition Agent=Unassigned (can never fire); disabled agents **Brooke Fogarty** and **Vivan Rayborn** still subscribed (MENTION; 30); Chris Tjotjos duplicated on MENTION; **no rules exist for**: reassignment, SLA warnings/breach, Change Requests, Contract Renewals, MT team-wide new ticket.

## 3. General Settings state (2026-07-17)

ON: multiple-notifications-per-event-per-recipient, Owner notifications, exclude-API-agents, allow-outside-team-permissions, ticket-type bcc emails, mentions (action+CRM+teams). OFF: follower emails/notifications, include-additional-agents-in-assigned-to-recipient, completion status, **agent DND toggle**, **Event Log tab**, **notification logging**. Popup delivery = Heartbeat.

## 4. Ticket intake defaults that drive alerting

- **Support (1)** → Support (Sys Admins), default agent **Primary Agent** (`-92`), workflow "Managed Technology – Active", 4 Hour SLA/P3. The Primary-Agent default is why "New Ticket Logged – Unassigned" rules often don't fire for Support tickets, and it is **independent of the client `priassign` checkbox**.
- **Event (34)** → Cyber Ops (Analysts), Unassigned, workflow "Cybersecurity Operations".
- **Alert (21)** → Cyber Ops (Analysts), Unassigned, **no workflow**, Request SLA, default priority Low(4). Under the old rule 27 (workflow-step trigger) Alerts sent **nothing**; rule 57 now covers them.
- **Action1 (41)** → Cyber Ops (Analysts), Unassigned, NO SLA, no workflow — deliberately excluded from all Cyber notifications. **The exclusion does not work as intended — see §4.1.**
- **Change Request (2)** → Support (Sys Admins), Unassigned, workflow "Change Management" — still no notification rule matches it.

### 4.1 What ticket type 34 "Event" actually contains (measured 2026-08-04)

**Do not assume "Event = SOC incident". It is mostly not.** Measured over Jul 1 – Aug 4 2026
(`halo_get Tickets`, `requesttype=34`, `includeclosed`, 139 unique tickets — 5 weeks, so
**~28 Event tickets/week**, not the ~10/week the alert→ticket→incident funnel implies):

| What it really is | Count | Share |
|---|---:|---:|
| `[Action1] <host> - Endpoint offline` — **carrying `tickettype_id = 34`, not 41** | 88 | 63% |
| CISA "Cyber Hygiene Report" / "WAS Results" recurring scan emails (5-per-Monday batch) | 28 | 20% |
| Genuine security signal (anomalous login, credential leak, DLL sideloading, info-stealer) | 11 | 8% |
| Access / mail-release service requests | 4 | 3% |
| **SentinelOne vendor marketing email** ("You're Invited! … Purple AI Webinar") | 3 | 2% |
| Offboarding notices | 3 | 2% |
| Travel (filed as Event, not type 40) | 2 | 1% |

**Consequences — this is the important part:**

1. **`Ticket Type ≠ Action1` (rules 57/58/59, and any future webhook) does NOT exclude the
   Action1 signal stream.** 88 of 88 Action1 endpoint-offline tickets in the sample carried
   `tickettype_id = 34`. Only tickets that arrive on type **41** are caught by that criterion
   (26 in the same window). So the Cyber Ops team is currently being emailed ~18 Action1
   offline tickets a week that everyone believes are suppressed. Excluding Action1 reliably
   requires a **summary/subject prefix** condition (`Summary starts with "[Action1]"`) or a
   category condition, **not** a ticket-type condition.
2. **Roughly 92% of new Event tickets are not something a human needs to be interrupted for.**
   Any "alert on every new Cyber ticket" design inherits that ratio.
3. **Cyber Event tickets are a business-hours artefact.** Only 7 of 139 (5%) were created
   outside Mon–Fri 08:00–18:00 ET, and only **one** of those was a genuine security signal
   (51358 Anomalous Login, Sun 21:39 ET). Out-of-hours coverage is not what Halo ticket
   creation gives you — the SentinelOne PagerDuty stream already does that (399 incidents in
   the week Jul 28 – Aug 3, 67% of them out-of-hours).
4. **The ticket is frequently the *output* of triage, not the input.** Worked example: 51400
   "Credential Leak – asimanella139719@polaris.edu" was created by Stevie Kantor at 14:10:36
   and resolved by the same analyst at 14:13:48 — 3 minutes — with the note *"This is not new
   information, just creating a ticket for record keeping."*
5. **`responsedate` is unreliable as a first-touch measure** on Cyber tickets. 51400's
   `responsedate` implies 51.5 h; its first action was 36 seconds after creation. Several
   tickets share a suspicious ~50–52 h cluster. Measure first touch from
   `get_ticket_actions` (earliest action `datetime`), not from `responsedate` or
   `lastactiondate`.

**Where the real risk is: post-creation staleness, not creation-time blindness.** Of 51 open
Cyber Ops tickets on 2026-08-04, **12 had no action for >7 days and 7 for >14 days**, including
`50555` MDR Onboarding – Polaris (70 d), four `SRM | Compliance Tracking` tickets (40–59 d),
`50822` Review | Device Code Flow (31 d), and `51419` Offboarding Notice (19 d). No
creation-time alert catches any of these. Halo exposes **Ticket Unassigned for X Hours**,
**No Actions for X Hours/Days**, **SLA Breached** and **Re-assign** on the same criteria engine
(§5) — those are the triggers that match this failure mode.

## 5. Browser techniques (proven, Windows browser)

- The rules list is a ReactTable; the standard row scrape works (`.rt-tbody .rt-tr` → `.rt-td` innerText).
- **`innerText` on config list rows can come back EMPTY** (blocked-read redaction, Runbook 03 §2.8). **`textContent` passes fine** — use `r.textContent` for row scrapes and build your own summary strings in-page. Confirmed 2026-08-17 on the Notification Templates list.
- **Rows have no anchors.** To open a row via JS you must dispatch the full `mousedown+mouseup+click` sequence **on a cell** (e.g. `.rt-td:nth-child(2)`), not just `click()` on the row. After ~2s the URL updates to `?id=N` and the right-hand detail panel swaps in-place.
- The detail panel is plain text in `document.body.innerText` after the marker `Show Guide Links`; `get_page_text` also captures it.
- General Settings toggle states are NOT in innerText — **screenshot** to read the checkboxes.
- Chunk row-walks to ≤7 rows per `javascript_tool` call.
- **The toolbar `Edit` button often needs TWO clicks** (first click focuses/steals, second activates). Screenshot after the first; if still in view mode, click again at ~(325,49).
- **Halo config pages 404 on guessed URLs.** `/config/quotations`, `/config/quotes/general`, `/quotes`, `/config/tickets/actions?id=N` all 404. Navigate via the left submenu instead; the real paths are e.g. `/config/quotes`, `/config/quotes/approvals`, `/config/salesorders`, `/orders?mainview=quotes`.

### Notification-authoring gotchas (learned 2026-08-04)

- **Notification Type, Team and Event are immutable once a notification is saved.** Opening an
  existing rule in Edit renders them as static text. To change a trigger you must **create a new
  notification and delete the old one** — there is no in-place edit and no enable/disable toggle.
- **Clone does not help**: it prompts only for a new name and copies the (locked) event.
- **`?id=-1` opens the New Notification form directly** — faster than list → New.
- **Criteria are a two-modal flow**: modal 1 (Add criteria) picks the Field Name → its `Save`
  opens modal 2 (Edit criteria: Rule Type + value) → modal 2's `Save` commits the row. Both
  modals can be driven in a single `browser_batch`, but screenshot after each value pick — the
  modal's vertical position **shifts** depending on whether a dropdown list is open.
- **Event picker is a searchable tree.** Type e.g. `New Ticket Logged` and it filters to a parent
  (red, non-selectable) with children `– Assigned to Recipient / – Assigned to Recipients Teams /
  – Unassigned / – All`. **Pick a child, not the parent.** For a Team Notification the correct
  child is almost always **– All**, with the team scoped by an explicit `Team Is equal to` criterion.
- **Useful ticket events confirmed present:** New Ticket Logged, New PI/OOH/Qualified variants,
  Ticket Updated by User (+PI/OOH/Qualified), Ticket Changed, Re-assign, **Closed**, Ticket Status
  Changed, Ticket Unassigned for X Hours, No Actions for X Hours/Days, Priority Escalated, Ticket
  Updated by Agent, Ticket Budget threshold met, Document uploaded, Pre-Pay threshold met, Ticket
  Deleted, Action added by Agent, SLA Breached, Service Status Changed, Consignment Created,
  Appointment Mention.
- **Template for Email/SMS is mandatory** and defaults to *Technician Update*.

### Client-record editing gotchas

- The **Assigning and Account Manager** section is **collapsed by default** in both read and edit
  mode — click its header to expand before looking for the auto-assign checkbox.
- The Halo client URL is `/customers?mainview=client&clientid=N`. `/client?id=N` and
  `/customer?id=N` both fail.
- `/api/Client/N` returns **401 from in-page `fetch`** (cookie auth is not enough; the API needs
  the bearer token). Verify `priassign` visually from the expanded panel, or via the MCP connector.

## 6. Audit limitations to remember

Per-agent personal notification preferences (each agent's own mute/delivery overrides) are not visible anywhere in admin config — poll the humans. Notification logging is off, so historical "did it fire?" questions are unanswerable until it's enabled. Read-only sessions cannot test-fire events.

---

## 7. The POPUP layer is a separate template family (discovered 2026-08-17)

**This is the single most confusing thing about Halo notifications and it cost a full
investigation to establish. Read this before anyone touches a popup again.**

A single Halo notification rule fans out to up to four channels — **email, in-Halo popup,
browser push, mobile push** — and **email and popup use DIFFERENT templates from DIFFERENT
config screens**:

| Channel | Template source | Selected how | Example (NEW SALES ORDER, rule 22) |
|---|---|---|---|
| **Email / SMS** | Config → **Email** → templates (`?mg=-2` custom list) — Runbook 03 | Explicit dropdown on the rule: *Additional Details → Template for Email/SMS* | **−115 "NEW SALES ORDER (Internal)"** |
| **In-Halo popup** (+ the notification pane) | Config → **Notifications → Notification Templates** (`/config/notifications/templates`) | **Implicit — Halo matches the template NAME to the trigger EVENT.** There is no field for it anywhere on the rule. | **"Sales Order Created"** (id 65) |

**Consequences:**

1. **Editing the email template does nothing to the popup, and vice versa.** The
   2026-07-18 work that removed cost/margin from #74 and built −115 never touched the popup —
   which is why the popup was still showing dead `$PRIMARYAGENT` a month later.
2. **You cannot rewire which popup template a rule uses.** The binding is by event name. To
   change popup wording you edit the template whose name matches the event
   (`Sales Order created` → `Sales Order Created`).
3. **The 2026-07-17 audit §4.3 claim that popup templates are "not wired to any rule" is
   wrong** for the ones whose names match live events. Correct reading: the *SLA / deadline /
   reassignment* popup templates are unused **because no rule fires those events**, not
   because popup templates are unwired in general.

### 7.1 Notification Template inventory (106 total, 3 pages of 50)

Reach a template directly at `/config/notifications/templates?id=N`. The list has **no ID
column** — find a template by name, then open it and read the id off the URL.

Event-matched templates that matter to Simvay today:

| Template | Bound to (event) | Live rule |
|---|---|---|
| **Sales Order Created** (id 65) | Sales Order created | 22 NEW SALES ORDER |
| Quote approved by user | Quote approved by User | 21 APPROVED QUOTE |
| Purchase Order Created | Purchase Order created | 29 PURCHASE ORDER ISSUED |
| Invoice paid | Invoice paid | 32 INVOICE PAID |
| Feedback Added | Feedback Added | 41 TICKET FEEDBACK |
| New Request Logged / Request Updated by User / Request Closed | the ticket events | 37/38, 44/45, 57/58/59 etc. |

Page 1 is the classic ticket family (New Request Logged ×4, Request Updated by User ×4, Request
Updated, Re-assigned, Closed, 1st/2nd SLA Warning, Escalated, Time Taken Exceeded Estimate,
Software Usage Alarm, Contract Expiry Alarm, Stock Reorder Alarm, Approval Required, Approval
Outcome, Appointment Notification, Task Notification, Ticket Deadline Warning …). Page 2 is the
commercial + CRM family (Purchase Order Created/Updated/Deleted, **Sales Order
Created/Updated/Deleted**, Quotation Created/Updated/Deleted, Quote Status Changed, Quote
rejected, Quote approved by user, Invoice viewed/paid, Recurring Invoice ×3, Stock
Received/Removed, CRM Note ×3, Site Note ×3, Workflow Step Started, No Actions for X Hours/Days,
Ticket Type ×3, Service Status Changed, 1st OLA Warning …).

### 7.2 Editing a popup template (proven recipe, 2026-08-17)

1. Navigate `/config/notifications/templates?id=N`, wait ~5 s.
2. Click toolbar **Edit** at ~(325, 49). **Screenshot — the first click frequently doesn't
   register.** Click again if still in view mode. In edit mode the toolbar button becomes
   **Save** and a `Name` input + `Message` **`<textarea>`** appear.
3. Set the body with the React native-setter trick (a plain `.value =` is silently reverted):

```js
const ta = document.querySelector('textarea');
const setter = Object.getOwnPropertyDescriptor(
  window.HTMLTextAreaElement.prototype, 'value').set;
ta.focus();
setter.call(ta, newText);
ta.dispatchEvent(new Event('input',  {bubbles:true}));
ta.dispatchEvent(new Event('change', {bubbles:true}));
```

4. Click the **bottom** `Save` at ~(812, 387) (there is also a toolbar Save; the bottom one is
   the reliable target).
5. **Re-navigate to `?id=N` and re-read** — the view can show a stale value immediately
   post-save. Verified persisted for template 65 this way.

Popup templates are **plain text** — no Froala, no HTML, no image-upload dance. This makes them
far easier to edit than the email templates in Runbook 03.
