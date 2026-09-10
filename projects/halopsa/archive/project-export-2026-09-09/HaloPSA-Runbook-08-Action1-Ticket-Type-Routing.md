# Runbook 08 — Action1 → HaloPSA: dedicated ticket type, statuses + contract-based routing

> **Status: BUILT & TESTED in Halo (2026-07-28).** Decisions D1–D6 approved by Ryan.
> Statuses, ticket type, notification exclusion, routing rule and area wiring are **live and
> verified**. Outstanding: optional workflow, and the **connector repoint** (Ryan's host).
> See **§0b As-built** for exact state.
> **Instance:** `https://simvay.halopsa.com`

---

## 0a. Addendum 2026-08-04 — routing re-verified, no change needed

Ryan reported "Fairview Park's Action1 tickets aren't being routed to Managed Technology."
**Investigated: rule 13 is correct and working.** City of Fairview Park (19) was already in the
rule's Client list (it has been since 2026-07-28 — it holds EMTS-020126-013129 + EMTS-EXP +
FISM). Evidence:

| Ticket | Date | Type | Team | Agent |
|---|---|---|---|---|
| 51624 `[Action1] FP-LT-4J43CH4.FPPD.local - Endpoint offline` | 2026-08-03 | **Action1 (41)** | **Support (Sys Admins)** ✅ | Unassigned |
| 51562 `[Action1] CFPK25-SPARE.CFPK.local - Endpoint offline` | 2026-07-28 | **Action1 (41)** | **Support (Sys Admins)** ✅ | Unassigned |

What Ryan was actually looking at were **pre-2026-07-28 tickets**, raised before the Action1
type and rule 13 existed. Those are on the legacy **Event (34)** type and sat with Cyber Ops:
51351, 51327, 51304, 51303, 51302, 51199, 51198 — **all already Closed (status 9)**, so there
is nothing to re-route. (A parallel set — 51492, 51474, 51305, 51202, 51201, 51200, 51197 — was
hand-moved to type **Support (1)** / Support (Sys Admins) at the time and is also closed.)

**Conclusion: no config change made for Fairview Park.** If the same complaint recurs, check the
ticket's **type** first — if it is Event (34) or Support (1) it predates the rule; only type
**Action1 (41)** is in scope for rule 13.

**Standing gap (unchanged, by design):** rule 13 matches `Summary Contains "Endpoint offline"`
only. Vulnerability / missing-update / automation-failure Action1 tickets still go to Cyber Ops
for **every** client, MSA/EMTS included. If MT should own those for managed clients too, that is
rules R3/R4 in §5 with the client list added — not yet built.

### Interaction with client-level auto-assign (found 2026-08-04)

Halo's client record has **"Assign new Tickets to the Primary Agent"** (`priassign`, agent in
`pritech`), and it **does apply to connector-created Action1 tickets** even though the Action1
ticket type's default agent is Unassigned. That is why Action1 tickets for North Royalton (44),
Bober Markey (39), Monroeville (43) etc. were arriving assigned to Ryan Patrick. It was turned
**off** on Ryan's 8 cyber clients on 2026-08-04 — see Runbook 04 §0 for the full list and the
Managed-Technology caveat.

Odd data point worth remembering: Fairview Park has `priassign = true` with `pritech = 23`
(Chajon), yet its Action1 tickets arrive Unassigned. Working theory — Halo only applies the
auto-assign when the primary agent is a member of the ticket's **team**, and Chajon is in
Support (Sys Admins), not Cyber Ops (Analysts). Unproven.

### Notification exclusion still holds

The old notification rule **27 "NEW TICKET | Cyber"** (which carried the `Ticket Type ≠ Action1`
exclusion) was **deleted** on 2026-08-04 and replaced by three Team Notifications — 57 NEW
TICKET | Cyber Ops, 58 CLIENT UPDATE | Cyber Ops, 59 TICKET CLOSED | Cyber Ops. **All three
carry the same `Ticket Type ≠ Action1` exclusion**, so Action1 tickets remain email-silent.
Any future Cyber notification must repeat that exclusion. See Runbook 04 §0.

---

## 0b. As-built record (2026-07-28)

### Built and live

| Object | ID | State |
|---|---|---|
| Status **A1 Investigating** | **36** | seq 141, `#f5a623`, SLA hold action *No Action* |
| Status **A1 Remediated – Awaiting Auto-Close** | **37** | seq 142, `#00627b`, SLA *Put on hold (if not on hold already)* |
| Status **A1 Suppressed – Decommissioned** | **38** | seq 143, `#9b9b9b`, SLA *Put on hold* |
| Ticket type **Action1** | **41** | seq 25, Incident, Use=Tickets, team **Cyber Ops (Analysts)**, agent Unassigned, **NO SLA (5)**, priority 1, initial status **New (1)**, **no workflow**, agents-can-select **Yes**, end-users/anonymous **No** |
| ↳ Allowed statuses (type 41) | — | New, A1 Investigating, A1 Remediated, A1 Suppressed, **Closed (9)** — `allowall_status = No` |
| ↳ Field List (type 41) | — | Summary, Details |
| ↳ Email settings (type 41) | — | Send Acknowledgement **Don't Send**; Send Action Emails **Don't Send Email**; Account Manager Emails **No**; Forward agent updates to end-users **No**; Always Bcc **empty**; hidden from Self Service Portal **Yes** |
| ~~Notification rule **27** "NEW TICKET \| Cyber"~~ | 27 | **DELETED 2026-08-04** — replaced by rules 57/58/59, all of which keep `Ticket Type ≠ Action1` |

**Design change vs the plan:** Halo has **no is-closed flag on a status** — verified on the
status form and via `/api/Status/9` vs `/api/Status/20` (structurally identical). Only the
built-in **Closed (9)** actually closes a ticket (sets `dateclosed` / `hasbeenclosed`).
A custom "A1 Auto-Closed" would have sat in the open queue forever. So the terminal status is
**Closed (9)**, the connector's Closed Ticket Statuses list is **just `[Closed (9)]`**, and
"A1 Closed – Manual" was dropped. Status 9 sends no email (`statusemailid: 0`,
`notifystatuschange: 0`, `nochangetemplate: -1`).

| **Ticket rule 13** `Action1 \| Offline -> MT Support` | **13** | Use **New Ticket**, precedence **200**, stop-matching **Yes**, display-notification **No**, enabled. Criteria: Ticket Type = Action1 **AND** Summary Contains `Endpoint offline` **AND** Client Includes the 10 clients in §6. Outcome: Team → **Support (Sys Admins)**; everything else *No Change*. **Re-verified 2026-08-04.** |
| **Area: Action1 (17)** — was "Alert" | **17** | **Renamed** Alert → **Action1** (entity names "Action1 Ticket"/"Action1 Tickets", sequence 100, Button Icon set to **`bug`** on 2026-07-28 — was `exclamation`). Ticket Type filter changed from *Alert* → **Action1**. **No team filter**, so both Cyber-Ops- and MT-routed Action1 tickets land here. This is the single home for Action1 tickets (Ryan, 2026-07-28). ⚠ Because there is no team filter, an MT-routed ticket showing in this area is **not** evidence of misrouting — check the ticket's Team column. |
| **Area: Cybersecurity (16)** | 16 | Ticket Type filter back to **Event, User Travel** |
| **Area: Technology Mgmt (1)** | 1 | **No change needed** — its filters are ITIL Type Includes *Incident/Problem/Service Request/Change Request* + Team Includes *Support (Sys Admins), Support (Mgmt)*. Action1 is ITIL **Incident** and rule 13 sets the team, so MT-routed tickets also appear there |

⚠ **The legacy `Alert` ticket type (id 21) no longer has an area.** It was the only type area 17
filtered on. If Alert tickets are still raised, give them an area or fold them into another one.

### Verification performed (2026-07-28)

Test ticket **51558** — `[Action1] TEST-01 - Endpoint offline`, client City of Brooklyn:

- Ticket Type **Action1**, Workflow ***None***, SLA **NO SLA**, Status **New**
- **Team = Support (Sys Admins)** → rule 13 fired correctly
- Status dropdown offered exactly: New, A1 Investigating, A1 Remediated, A1 Suppressed, Closed
- Ticket action log contained **one entry only** (the Open action) — **no acknowledgement,
  no action email, no bcc**
- Closed to **Closed (9)** cleanly; closure details populated, still no email

### Outstanding

1. **Legacy Action1 tickets were NOT migrated** (decision D4). The 14 that were open on
   2026-07-27 are still on the old **Event** type (34) with the 4 Hour SLA and workflow 18.
   (Rule 13 has `Use = New Ticket`, so re-typing an existing ticket will **not** re-route it —
   the team has to be set manually.) **Fairview Park's share of these is fully closed as of
   2026-08-04.**
2. **Workflow "Action1 Signals"** — not built. Purely cosmetic. **Now safe to add**: since rule 27
   was deleted, no notification fires on Workflow Step Started at all.
3. **Connector repoint** — done for at least North Royalton / Bober Markey / Fairview (tickets are
   landing on type 41). Values in §4 step 8.
4. **Optional:** exclude A1 Remediated / A1 Suppressed from the Cybersecurity area's default
   filter profile.

### Note on per-agent notification rules

Per-agent rules 43, 46, 47, 48, 49 fire on *New Ticket Logged – Assigned to Recipient*. They only
matter if an Action1 ticket gets **assigned**. With client-level auto-assign now off for Ryan's 8
cyber clients (Runbook 04 §0), connector-created Action1 tickets stay Unassigned and these rules
do not fire. If Action1 tickets ever start getting auto-assigned again, add
`Ticket Type ≠ Action1` to rules 43, 46, 47, 48 and 49.

---

## 0. Decisions needed before build (6)

| # | Decision | Recommendation |
|---|---|---|
| D1 | Which contracts count as "support included" for offline routing? Confirmed: **EMTS** (7 clients) + **MSA** (3). Undecided: **RETAINER / MTS-RETAINER** (Hinkley, North Royalton, S. Russell, PharmAgility) and **EMNS** (Olmsted Falls, Solon). | Treat RETAINER + EMNS as **security-only** (offline stays with Cyber Ops) until you say otherwise. **2026-08-04: Hinkley and North Royalton no longer hold an active RETAINER — they are S1/A1-only now.** |
| D2 | SLA on the new type | **NO SLA (id 5)**. ⚠ Halo quirk (Runbook 07): NO SLA only offers **Priority 1** |
| D3 | Dedicated workflow? | **Yes, 3 steps** ("Action1 Signals": Detected → Investigating → Resolved) |
| D4 | Migrate the 97 existing `[Action1]` Event tickets? | **No.** 83 of 97 are already closed |
| D5 | **Existing Open Ticket Behavior** in the connector (Update vs Skip) | **Skip existing open tickets** |
| D6 | Should analysts ever be able to force-close a still-offline endpoint? | **No — give them `A1 Suppressed` instead** |

---

## 1. Current state (verified read-only, 2026-07-27)

### 1.1 What the connector actually sends

Source: `Action1Corp/Integrations/action1-halo-connector` (cloned and read).

The connector has **one global `ticketDestination`** — a single `ticketTypeId`, `teamId`,
`category1Id`, `newStatusId`, `closedStatusIds`. There is **no per-signal and no per-client
routing in the connector.** The create payload is only:

```
summary, details, details_html, client_id, tickettype_id,
status_id?, team_id?, category_1?
```

**All routing intelligence therefore has to live in Halo.** The one thing Halo can key on is
the **summary string**, which the connector builds deterministically:

| Mode | Summary format | Signal |
|---|---|---|
| Per-endpoint | `[Action1] <endpoint> - Endpoint offline` | OFFLINE |
| Per-endpoint | `[Action1] <endpoint> - Reboot required` | REBOOT_REQUIRED |
| Per-endpoint | `[Action1] <endpoint> - Vulnerabilities detected` | VULNERABILITY |
| Per-endpoint | `[Action1] <endpoint> - Updates required` | UPDATE |
| Per-endpoint | `[Action1] <endpoint> - Automation failures detected` | AUTOMATION_FAILED |
| Grouped | `[Action1] <CVE/issue> - Vulnerability detected on N endpoints` | VULNERABILITY |
| Grouped | `[Action1] <update> - Missing update detected on N endpoints` | UPDATE |
| Grouped | `[Action1] <automation> - Automation failures detected on N endpoints` | AUTOMATION_FAILED |

> A rule matching `Vulnerabilit` (partial) catches both grouped and per-endpoint wording.
> `Endpoint offline` is unique to the offline signal and safe to match on.

### 1.2 What's in Halo today

- **Ticket type: Event (id 34)** — team Cyber Ops (Analysts) (17), agent Unassigned,
  workflow **18 "Cybersecurity Operations"**, initial status New (1), SLA **3 (4 Hour)**,
  priority 3 (Medium), `default_sendemail: true`, `allowall_status: false`.
- **Ticket volume:** 140 tickets match `[Action1]`.
- **Category** is auto-set to `Cybersecurity>Operations>Vuln Management` on every ticket.

### 1.3 The email problem (historic — resolved)

Notification rule 27 fired on event **1176 = Workflow Step Started** for `Team = Cyber Ops
(Analysts)`, which is why every Action1 *Event* ticket used to email. Suppressing the type's own
emails was not enough — rule 27 fired off the *team*, not the type. **Rule 27 was deleted on
2026-08-04**; its three replacements (57/58/59) all exclude Action1 explicitly.

Rule **37 "UNASSIGNED | New Support Ticket"** is conditioned `Agent = Unassigned` **AND**
`Ticket Type = Support` — so routing Action1 tickets into Support (Sys Admins) does **not**
trigger it. General Settings: "Send Ticket Type bcc emails" is **ON** globally — the type's bcc
field must stay empty.

### 1.4 The routing engine: Ticket Rules

`Config → Tickets → Rules` — 11 rules today, API `/api/TicketRules`, detail UI
`/config/tickets/rules?id=N`.

- Rules match on ticket (`faults`) fields with **partial match**, **precedence**,
  **stop-matching-when-matched**, optional **criteria groups** (OR), and a `Use` setting
  (New Ticket / New & Existing).
- Actions: new team, agent, priority, status, SLA, category 1–4, workflow, template.
- **Criteria fields confirmed:** Ticket Type, Summary, Client, Site, Team, Status, Priority, SLA,
  User, Category, Impact, Urgency, Contract, Contract Reference, Important Client, plus custom fields.
- Existing rules 1–9 (the impact/urgency priority matrix) all carry `requesttypenew IN (1,3)`,
  so they do not touch the Action1 type.

> **Contract vs Client as the routing key:** "Contract" means the contract *linked to the ticket*,
> which the connector never sets. The reliable discriminator is **Client** (explicit multi-select).

### 1.5 Contract landscape

| Prefix | Count | Clients |
|---|---|---|
| **EMTS** (+EXP/MC) | 7 | Aria Financial (23), Avon Lake (25), Brooklyn (24), Fairview Park (19), Parma Heights (29), Conveyer & Caster (28), Olmsted Township (34) |
| **MSA** (+EXP) | 3 | Great Lakes Brewing (22), Russell Township (45), Staffco (72) |
| ECRM / SRM / ISM / FISM / MDR / S1 / A1 / Umbrella / C2 / DUO | — | Security only → Cyber Ops |

All managed-service agreements share **contract subtype 6**.

### 1.6 Connector lifecycle — the exact rules

| Signal state | Linked ticket state | Connector action |
|---|---|---|
| qualifies | none / missing | **CREATE** |
| qualifies | **closed** | **CREATE a brand-new ticket** ← the duplicate source |
| qualifies | open, behavior = *Skip existing open* | SKIP |
| qualifies | open, payload unchanged | SKIP |
| qualifies | open, payload changed, behavior = *Update* | **UPDATE — forces `status_id` back to New** |
| **cleared** | open | **CLOSE** → `setTicketStatus(ticketId, firstClosedStatusId)` |
| cleared | closed / none | SKIP |

Consequences: the API closes tickets itself when the endpoint returns; any status the connector
considers closed on a still-offline endpoint produces a duplicate next run; "closed" is defined
purely by the connector's `closedStatusIds` list (Halo returns `hasbeenclosed`, not `is_closed`);
CLOSE is endpoint-mode only — grouped tickets always need a human close.

---

## 2. Design

```
Action1 connector ──► type "Action1" (no emails, NO SLA, Cyber Ops default, own statuses)
                              │
                              ▼  Halo Ticket Rules (on New Ticket)
      ┌───────────────────────┴───────────────────────┐
Summary ~ "Endpoint offline"                  Summary ~ "Vulnerabilit" / Update / Automation
      │                                               │
 ┌────┴────┐                                          ▼
Client in   Client not in                      Cyber Ops (Analysts)
EMTS/MSA    the list                           cat: Vuln Management
   │             │
   ▼             ▼
Support      Cyber Ops
(Sys Admins) (Analysts)
```

**Status lifecycle:** New → A1 Investigating → A1 Remediated (parks until Action1 confirms the
endpoint is back) → **Closed (9)**, written by the connector. A1 Suppressed is the dead-end for
wiped/retired machines: stays open forever so the connector keeps SKIPping and never duplicates.

---

## 5. Ticket rules spec (R2–R4 not yet built)

| # | Name | Prec | Stop | Criteria (ANDed) | Action |
|---|---|---|---|---|---|
| R1 = **rule 13, live** | `Action1 \| Offline → MT Support` | 200 | Yes | Ticket Type = **Action1**; Summary **contains** `Endpoint offline`; Client **Includes** §6 list | Team → **Support (Sys Admins)** (14) |
| R2 | `Action1 \| Offline → Sec Ops` | 210 | Yes | Ticket Type = Action1; Summary contains `Endpoint offline` | Team → Cyber Ops (Analysts) (17) |
| R3 | `Action1 \| Vuln → Sec Ops` | 220 | Yes | Ticket Type = Action1; Summary contains `Vulnerabilit` | Team → Cyber Ops; Category 1 → Vuln Management (281) |
| R4 | `Action1 \| Updates/Automation → Sec Ops` | 230 | Yes | Ticket Type = Action1; Summary contains `Updates required` **OR** `Missing update` **OR** `Automation failures` (needs **Use Criteria Groups**) | Team → Cyber Ops |

**Do not set a status in any rule** — the type's initial status and the connector own that.

---

## 6. Client routing list for rule 13 (maintain this)

**MT-support clients (offline → Support (Sys Admins)) — 10, confirmed present in rule 13 on 2026-08-04:**

| Client | id | Basis |
|---|---|---|
| Aria Financial Group | 23 | EMTS-090125-083126 |
| City of Avon Lake | 25 | EMTS-040126-033128 |
| City of Brooklyn | 24 | EMTS-031526-031428 |
| **City of Fairview Park** | **19** | **EMTS-020126-013129 — present and working** |
| City of Parma Heights | 29 | EMTS-090125-083126.2 |
| Conveyer & Caster | 28 | EMTS-100125-093028 |
| Olmsted Township | 34 | EMTS-010126-123127 |
| Great Lakes Brewing | 22 | MSA-040126-033127 |
| Russell Township | 45 | MSA-070126-063027 |
| Staffco Connecting Solutions | 72 | MSA-100126-093028 |

**If a future MSA/EMTS client is missing from the rule's client picker, check whether it is still
a prospect** — prospects do not appear (this is what happened to Staffco).

**Refresh procedure:** re-run `/api/ClientContract?count=500`, filter `active = true` and ref
prefix in {EMTS, MSA} (all are contract **subtype 6**), diff against this table.

---

## 7. Email-suppression checklist

1. Type `Action1`: **Send email by default = No**
2. Type `Action1`: **Send acknowledgement = Never**, template none, AI ack off
3. Type `Action1`: **bcc addresses empty** (global "Send Ticket Type bcc emails" is ON)
4. Type `Action1`: **end users + anonymous cannot select**
5. **Every Cyber Ops team notification carries `Ticket Type ≠ Action1`** — currently rules
   **57, 58, 59**. Any new one must repeat it.
6. Rule 37 needs no change (`Ticket Type = Support`)
7. Ticket rules: "Display a notification when matched" = **No**
8. **Status changes don't email** — no notification rule is bound to the A1 statuses, and the
   connector writes as an API agent with "Exclude API-only agents" ON

---

## 9. Other findings worth acting on

- **Max Open Tickets Per Organization = 30** (connector default). When the cap is hit the
  connector **silently skips creates** — raise it, especially once vuln ticketing is on.
- **Category is wrong for offline.** Everything is filed as `Cybersecurity>Operations>Vuln
  Management`. Rule 13 could fix this for MT-routed tickets if a `Managed Technology>Endpoint
  Health` category is created.
- **Grouped vuln tickets never auto-close** — they need a human close path.
- **The 90-day offline threshold** catches a lot of wiped/retired machines. Excluding them in
  Action1 is the cleanest fix; `A1 Suppressed` is the safety net.

---

## 10. Techniques / discoveries

- **Ticket Rules is the routing engine** — `/api/TicketRules` (GET) and `/config/tickets/rules?id=N`.
  Criteria live on the `faults` table with `partialmatch`, `matchseparatedvalues` and `type`
  (0 = equals, 1 = not equals, 23 = in-list). Actions are the `new_*` fields.
- **Rule detail is fully readable via `get_page_text`** on `/config/tickets/rules?id=N` — the
  Criteria table (including the full comma-separated Client list) renders in the detail panel
  without needing edit mode. Faster and safer than opening Edit.
- **Criteria field picker** is enumerated by opening a rule → Edit → Criteria **+ Add** → the
  Field Name dropdown (~300 entries). **Escape closes the modal without saving.**
- **Notification rule conditions** are readable at `/config/notifications/notifications?id=N`
  (scroll the Setup tab to the criteria table).
- **`/api/ClientContract?count=500`** returns all contracts with `ref`, `subtype`, `active`,
  `client_id` — the fastest way to audit which clients hold which agreements. Filter client-side
  with `jq`; the raw response is large.
- **`/api/Client/<id>`** (via the MCP connector) exposes `pritech`, `sectech`, `priassign`,
  `secassign` — the auto-assign settings. The **list** endpoint `/api/Client` does **not** return
  `priassign`, so per-client detail calls (or the UI panel) are required.

### Build-session gotchas

- **Halo statuses have no is-closed flag.** Only the built-in **Closed (9)** closes a ticket.
- **The first interaction after a `navigate` is swallowed** on config forms — do the navigate in
  one tool call, then type in a *separate* call.
- **Ticket-type Field List: commit chips with the picker's `Add` button, then the panel `Save`,
  then the toolbar `Save`.**
- **Ticket-rule / notification criteria are a two-modal flow**: modal 1 picks the Field Name →
  its `Save` opens modal 2 (Rule Type + value) → modal 2's `Save` commits the row. Screenshot
  between them; the modal shifts vertically when a dropdown is open.
- **Client criteria in ticket rules**: Rule Type `Is equal to` is single-client; **`Includes`** is
  the multi-select.
- **The Allowed Values tab renders its "Allow All Values" checkboxes late.**
- **The in-page API token expires within a session**, and plain cookie-auth `fetch('/api/...')`
  from the page returns **401**.
- **Ticket-type config URL is `/config/tickets/tickettype` (singular)**; statuses at
  `/config/tickets/status`; `?id=-1` opens a new record for statuses, rules and **notifications**,
  but **not** for ticket types (use the list's `+ New`).
- **Ticket-area "Button Icon" is a fixed picker** — 505 built-in Font Awesome 4 glyphs, no upload,
  no URL, no free text. Ticket **types** have no icon field at all. Area 17 uses **`bug`**.
