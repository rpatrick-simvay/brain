# Simvay HaloPSA Notification Audit & Assessment

**Date:** July 17, 2026
**Prepared by:** Claude (read-only audit, requested by Ryan Patrick)
**Scope:** All agent-facing notification rules, notification general settings, delivery channels (email, popup, browser push, mobile push), and the client-facing email layer they connect to. **No changes were made to any configuration.**

---

## 1. Executive Summary

Simvay's HaloPSA instance has **25 notification rules**, one **Team Notification** (Cyber only), and a nearly universal "all channels on" delivery posture (email + popup + browser push + mobile push). The system works, but it grew person-by-person rather than by design, and the two departments are on completely different architectures:

- **Cybersecurity** has a single, team-wide, workflow-driven new-ticket alert that covers every analyst automatically.
- **Managed Technology** has a patchwork: one "unassigned ticket" blast to 6 people plus **five hand-built pairs of per-person rules** — and the patchwork has holes. This is the direct root cause of the MT team's dissatisfaction with new-ticket alerts (detailed root-cause analysis in §6).

Headline findings:

1. **New Support tickets default-assign to the client's Primary Agent.** When that happens, the "UNASSIGNED | New Support Ticket" alert never fires and only the assignee's personal rule fires — and **Jonathan Gayda has no personal rules at all**, so a ticket logged straight to him alerts no one.
2. **When a ticket arrives unassigned, all 6 MT subscribers get it on all 4 channels (~24 alerts per ticket)** with no accountability for who picks it up — the classic alert-fatigue / bystander pattern.
3. **Reassignment is silent.** No rule fires when an existing ticket is moved to a tech — for either department. Triage handoffs rely on people watching boards.
4. **Change Requests, Project tickets, and Contract Renewal opportunities generate no notifications at all.**
5. **There are no SLA warning or breach notifications** anywhere in the instance, despite active 1h/4h SLA targets.
6. **The SOC "Alert" ticket type may be silent too**: the Cyber new-ticket rule triggers on *Workflow Step Started*, and the Alert type starts no workflow (needs a one-ticket live test to confirm).
7. Hygiene issues: two disabled agents still subscribed, one duplicate subscriber, one rule whose trigger/condition combination can never fire, and notification logging turned off.

The recommendations (§7) prioritize rebuilding MT's new-ticket alerting on the proven Cyber model, consolidating the per-person rules into role-based ones, filling the coverage gaps (reassignment, SLA, Change Requests, renewals), and adopting a deliberate channel policy so mobile push means "act now" instead of "FYI."

---

## 2. Scope & Method

**Reviewed (read-only):**
- Config → Notifications → **Notifications**: all 25 rules, including each rule's Setup tab (type, delivery methods, trigger event, conditions, email template) and Agents tab (subscriber list with role inheritance).
- Config → Notifications → **General Settings**: all toggles and the popup delivery method.
- Config → Notifications → **Notification Templates**: the stock popup-template list.
- Config → Tickets → **Ticket Types**: default team/agent/SLA/priority and workflow wiring per type (to trace how tickets actually enter teams).
- HaloPSA API (read-only connector): teams, agents (incl. disabled), ticket types, statuses, SLAs, priorities, and a snapshot of open-ticket distribution.
- Prior project knowledge: the complete 94-template client-facing email inventory (Runbooks 01/03 and the Email Templates status doc).

**Not visible to this audit (flagged in §8):** each agent's *personal* notification preferences (agents can individually mute or change delivery for a subscription — this lives in their own preference pane), and live-fire behavior (read-only means nothing could be test-triggered).

---

## 3. Observed Team Structure

**Departments and teams (active agents only):**

| Department | Team | Members (in section) | Managers |
|---|---|---|---|
| Simvay – Managed Technology (dept 3) | Support (Sys Admins), id 14 | Andrew Mazzaro, Brian Goetz, Darryl Chajon, Jonathan Gayda | Kristoffer Oswald, Mike Karenke |
| Simvay – Managed Technology | Support (Mgmt), id 16 | Kristoffer Oswald, Mike Karenke | (same) |
| Simvay – Managed Technology | Contract Renewals, id 20 | MegHan Soltis, Kristoffer Oswald, Mike Karenke, Ryan Patrick | — |
| Simvay – Cybersecurity (dept 10) | Cyber Ops (Analysts), id 17 | Gabe Lister, James Hering, Shane Goodsite, Stevie Kantor | Ryan Patrick |
| Simvay – Cybersecurity | Cyber Ops (Mgmt), id 18 | Ryan Patrick | Ryan Patrick |
| Simvay – Sales (dept 8) | Sales Team, id 19 | Mike Schilling, Kristoffer Oswald, Mike Karenke, Ryan Patrick | — |
| (no team) | — | Chris Tjotjos (Partner), Justine Lemanowicz | — |

**Disabled agents still present in notification subscriber lists:** Brooke Fogarty (Sales, disabled), Vivan Rayborn (Cyber analyst, disabled).

**Ticket intake by type (drives who gets alerted):**

| Ticket type | Default team | Default agent | Starts workflow | Default SLA / priority |
|---|---|---|---|---|
| Support | Support (Sys Admins) | **Primary Agent** (client's) | Managed Technology – Active | 4 Hour SLA / Medium |
| Event | Cyber Ops (Analysts) | Unassigned | Cybersecurity Operations | 4 Hour SLA / Medium |
| Alert | Cyber Ops (Analysts) | Unassigned | **No workflow** | Request SLA / **Low (4)** |
| Change Request | Support (Sys Admins) | Unassigned | Change Management | none |
| New Starter Request | Cyber Ops (Analysts) | Unassigned | No workflow | Request SLA / Medium |
| Project / Project Task | Support (Mgmt) | Unassigned | No | none |
| Lead / Opportunity / Quick Quote | Support (Mgmt) | Unassigned | No | none |
| Contract Renewal (opp) | Contract Renewals | Unassigned | No | SLA 5 / Urgent-1 |

**Volume snapshot (2026-07-17):** 129 open tickets — Support (Sys Admins) 39, Support (Mgmt) 26, Cyber Ops (Analysts) 32, Cyber Ops (Mgmt) 2, Sales 1. Of the 100 most recently logged open tickets, 75 were opened within the last 30 days; open Support-type tickets logged in the last 30 days: 28 (≈1–2 new Support tickets per business day surviving as open, more including same-day closures).

---

## 4. Notification Architecture — Current State

### 4.1 General Settings (Config → Notifications → General Settings)

| Setting | State | Assessment |
|---|---|---|
| Allow multiple notifications per event per recipient | **ON** | Amplifies duplicates when someone is subscribed twice (see F12) |
| Enable Owner Notification Functionality | ON | OK |
| Owner notification on link/unlink/merge | OFF | OK |
| Exclude API-only agents from Owner/Updated-by-Agent | ON | Good (keeps integration noise out) |
| Allow notifications outside team/department permissions | ON | Broad; acceptable at this size |
| Send Ticket Type bcc emails for notifications | ON | Worth confirming which mailboxes are bcc'd |
| Do Not Send Follower Emails / Follower agent notifications | OFF / OFF | Followers get nothing — intentional? |
| Mentions in action notes / CRM notes / include teams | ON / ON / ON | Good |
| Include additional agents in assigned-to-recipient | OFF | OK |
| Completion status for notifications | OFF | Optional workflow aid |
| Popup notification delivery method | Heartbeat | Default |
| Agent "Do not disturb" toggle | **OFF** | Agents cannot silence popups — invites invisible personal muting |
| "Event Log" tab (admins) | **OFF** | Blind spot |
| Notification logging | **OFF** | Blind spot — cannot troubleshoot "did it fire?" |

### 4.2 The 25 notification rules — full inventory

Channels key: **E** = email, **P** = in-app popup+sound, **B** = browser push, **M** = mobile push. "Halo-only" = no email, still popup/push as listed.

**Ticket alerts — Managed Technology (the patchwork):**

| ID | Name | Trigger | Conditions | Channels | Template | Subscribers |
|---|---|---|---|---|---|---|
| 37 | UNASSIGNED \| New Support Ticket | New Ticket Logged – Unassigned | Agent=Unassigned AND Type=Support | E+P+B+M | #32 Technician Update | Mazzaro, Goetz, Chajon, Gayda (MT Role); Oswald, Karenke (MT Mgmt Role) — 6 |
| 38 | UNASSIGNED \| Updated Support Ticket | Ticket Updated by User – Unassigned | Type=Support | E+P+B+M | #32 | Mazzaro, Goetz, Chajon, Gayda, Karenke — 5 |
| 43 | OSWALD \| NEW TICKET | New Ticket Logged – Assigned to Recipient | Agent=Oswald | E+P+B+M | −103 NEW TICKET | Oswald |
| 46 | MAZZARO \| NEW TICKET | (same) | Agent=Mazzaro | E+P+B+M | −103 | Mazzaro |
| 47 | CHAJON \| NEW TICKET | (same) | Agent=Chajon | E+P+B+M | −103 | Chajon |
| 48 | GOETZ \| NEW TICKET | (same) | Agent=Goetz | E+P+B+M | −103 | Goetz |
| 49 | KARENKE \| NEW TICKET | (same) | Agent=Karenke | E+P+B+M | −103 | Karenke |
| 42 | OSWALD \| UPDATED TICKET | Ticket Updated by User – Assigned to Recipient | Agent=Oswald | E+P+B+M | #32 | Oswald |
| 50 | KARENKE \| UPDATED TICKET | (same) | Agent=Karenke | E+P+B+M | #32 | Karenke |
| 51 | CHAJON \| UPDATED TICKET | (same) | Agent=Chajon | E+P+B+M | #32 | Chajon |
| 52 | GOETZ \| UPDATED TICKET | (same) | Agent=Goetz | E+P+B+M | #32 | Goetz |
| 53 | MAZZARO \| UPDATED TICKET | (same) | Agent=Mazzaro | E+P+B+M | #32 | Mazzaro |

> **Note:** there is no personal rule pair for **Jonathan Gayda**, and no team-wide MT new-ticket rule.

**Ticket alerts — Cybersecurity (the clean model):**

| ID | Name | Trigger | Conditions | Channels | Template | Recipients |
|---|---|---|---|---|---|---|
| 27 | NEW TICKET \| Cyber | **Team Notification** on Workflow Step Started | Team=Cyber Ops (Analysts) AND Type≠Project Task | E | −103 NEW TICKET | Entire Cyber Ops (Analysts) team, automatically |
| 30 | Ticket Update by User \| Cybersecurity | Ticket Updated by User – Assigned to Recipient | none | E+P+B+M | #32 | Lister, Hering, Goodsite, Kantor, Patrick (+ **Vivan Rayborn, disabled**) — 6 |

**Sales / leadership:**

| ID | Name | Trigger | Conditions | Channels | Template | Subscribers |
|---|---|---|---|---|---|---|
| 21 | APPROVED QUOTE | Quote approved by User | Approval Status=Approved | E+P+B+M | #246 Quote Approved | Oswald, Soltis, Karenke, Schilling, Patrick — 5 |
| 22 | NEW SALES ORDER | Sales Order created | Status=1 NEW ORDER | E+P+B+M | −115 (Internal) | Tjotjos, Oswald, Soltis, Karenke, Schilling, Patrick — 6 |
| 44 | UNASSIGNED \| New Opportunity Ticket | New Ticket Logged – Unassigned | Agent=Unassigned AND Type=Opportunity | E+P+B+M | −103 | same 6 as 22 |
| 45 | UNASSIGNED \| New Lead TICKET | New Ticket Logged – Unassigned | Agent=Unassigned AND Type=Lead | E+P+B+M | −103 | same 6 |
| 54 | UNASSIGNED \| Updated Opportunity Ticket | **Ticket Updated by User – Assigned to Recipient** | Agent=Unassigned AND Type=Opportunity | E+P+B+M | −103 | same 6 |
| 55 | UNASSIGNED \| Updated Lead Ticket | Ticket Updated by User – Unassigned | Agent=Unassigned AND Type=Lead | E+P+B+M | −103 | same 6 |

> **Rule 54 is internally contradictory** — see finding F10.

**Financial / operational:**

| ID | Name | Trigger | Conditions | Channels | Template | Subscribers |
|---|---|---|---|---|---|---|
| 29 | PURCHASE ORDER ISSUED | Purchase Order created | none | Halo-only, P+B+M | — | Tjotjos, Oswald, Soltis — 3 |
| 32 | INVOICE PAID | Invoice paid | none | E+P (no push) | −112 Invoice Paid | Oswald, Soltis — 2 |
| 41 | TICKET FEEDBACK | Feedback Added | none | Halo-only, P+M (no B) | — | Tjotjos, Oswald, Karenke, Patrick — 4 |
| 56 | ORDER to INVOICE | Ticket Status Changed – All | Status=Ready to Invoice | Halo-only, P+B+M | — | Oswald, Soltis — 2 |

**Cross-company:**

| ID | Name | Trigger | Channels | Template | Subscribers |
|---|---|---|---|---|---|
| 1 | MENTION | Mention | E+P+B+M | #32 | All 25 subscriber rows — every agent via roles, **including disabled Brooke Fogarty (twice) and duplicate Chris Tjotjos rows** |

### 4.3 Notification templates (popup layer)

The stock popup template list exists (New Request Logged, Request Re-assigned, 1st/2nd SLA Warning, Ticket Deadline Warning, Escalated, etc.) but these are only wording templates — **none of the SLA/deadline/reassignment ones are wired to any rule.** They are ready-made building blocks for the gaps in §5.

### 4.4 The client-facing email layer (context)

The outbound client email system (94 templates) was fully audited and largely rebranded in the July 16–18 sessions (Runbook 03): ticket lifecycle, quotes, billing, portal/security emails are Simvay-branded; internal pipe-format templates (−103 NEW TICKET, −112, −115, #32, #318) intentionally keep machine-readable subjects for Outlook rules. Outstanding from that work: **#32 Technician Update — the single highest-volume internal template, used by 13 of the 25 notification rules — still has a stock body** (Phase 3), and inbound reply-threading has not been live-verified.

---

## 5. Findings

**Coverage gaps**

- **F1 — No MT team-wide new-ticket alert.** Cyber has rule 27 (team notification, fires for every ticket entering the team). MT has nothing equivalent; coverage is stitched from rules 37 + 5 personal rules. The Support ticket type already starts a workflow ("Managed Technology – Active"), so the same mechanism Cyber uses is available but unused.
- **F2 — Gayda (and any future MT hire) has no assigned-ticket alerts.** A new ticket logged directly to Jonathan Gayda fires nothing. The per-person rule set was never extended past the original five agents. This architecture requires two new rules per hire — it will always drift.
- **F3 — Auto-assignment defeats the unassigned alert.** Support tickets default-assign to the client's **Primary Agent**. Whenever that resolves, rule 37 (unassigned) is skipped by design; only the assignee's personal rule fires. If the assignee is out that day, no one else learns of the ticket.
- **F4 — Reassignment is silent, both departments.** No rule uses a reassignment event; the personal "UPDATED" rules only fire on *end-user* updates. A ticket triaged and moved to a tech produces no alert (the stock "Request Re-assigned" popup template exists, unwired). This is almost certainly experienced as "new ticket alerts don't work" — from the tech's perspective the ticket is new to *them*.
- **F5 — Change Requests are silent.** They default to Support (Sys Admins) unassigned, but rule 37 filters Type=Support, so no alert fires. Same for New Starter Requests (Cyber), Project/Project Task (Support Mgmt), and Business Reviews.
- **F6 — No SLA warning or breach notifications.** SLAs are active (4 Hour SLA: 30-min response on Critical) and 1st/2nd SLA Warning popup templates exist, but no rule sends them. SLA performance currently depends on agents noticing on their own.
- **F7 — SOC "Alert" tickets may not trigger rule 27.** Rule 27 fires on *Workflow Step Started*, and the Alert ticket type starts **no workflow** (Event does). If true, the SOC's most time-sensitive ticket type is the least announced. Needs one live test ticket to confirm (read-only audit cannot fire events). Related: Alert's default priority is **Low (4)** on Request SLA — worth revisiting independently.
- **F8 — Contract Renewal opportunities generate no notification** to the Contract Renewals team (Soltis, Oswald, Karenke, Patrick).

**Noise and misconfiguration**

- **F9 — Unassigned MT tickets blast 6 people × 4 channels (~24 notifications per ticket)**, including partners' mobile phones, 24/7 — there are no working-hours conditions anywhere. High noise with no ownership signal is the textbook recipe for ignored alerts.
- **F10 — Rule 54 can never fire as configured.** Event "Ticket Updated by User – **Assigned to Recipient**" combined with condition "Agent = **Unassigned**" is contradictory (its sibling rule 55 uses the correct Unassigned event). Sales believes it has an updated-opportunity alert; it effectively doesn't.
- **F11 — Nearly everything is all-channels.** 17 of 25 rules send email + popup + browser push + mobile push. When a quote approval and a critical ticket produce the identical buzz, mobile push stops meaning anything.
- **F12 — Duplicates.** "Allow multiple notifications per event per recipient" is ON, and MENTION has duplicate subscriber rows (Chris Tjotjos twice, Brooke Fogarty twice via two roles). Managers are also double-covered by overlapping rules (e.g., Oswald/Karenke get rule 37 *and* their personal rules).
- **F13 — Disabled agents still subscribed.** Brooke Fogarty (MENTION) and Vivan Rayborn (MENTION, rule 30) are disabled but remain in subscriber lists.
- **F14 — Template inconsistency on the same event class.** New-ticket alerts use the branded −103 NEW TICKET card in 10 rules, but MT's highest-traffic new-ticket alert (37) uses generic #32 Technician Update — so MT's "new ticket" emails don't look like new-ticket emails, and #32's body is still stock.

**Observability**

- **F15 — Notification logging and the Event Log are OFF**, so "did the alert fire?" disputes are unresolvable. The agent DND toggle is also off, which pushes frustrated agents toward invisible personal unsubscribes (which admins cannot audit — see §8).

---

## 6. Root Cause: the Managed Technology New-Ticket Complaint

Tracing every path a new MT ticket can take makes the dissatisfaction predictable:

| Scenario | What fires today | Experience |
|---|---|---|
| Support ticket arrives, client has a Primary Agent (the default) | Only that agent's personal rule — if they're one of the 5 | Team is blind to the ticket; if the agent is out, nobody knows it exists |
| Support ticket arrives assigned to Gayda / a future hire | **Nothing** | Ticket sits until someone checks the board |
| Support ticket arrives unassigned | Rule 37: 6 people × 4 channels, template #32 (generic look) | Everyone is alerted, no one is responsible; alert fatigue |
| Ticket triaged and reassigned to a tech | **Nothing** (F4) | The tech never gets a "this is now yours" alert — feels exactly like a broken new-ticket alert |
| Change Request logged | **Nothing** (F5) | Silent |
| End user replies to an unassigned ticket | Rule 38: 5 people × 4 channels | More blast noise |

So MT simultaneously experiences **too much noise** (every unassigned ticket hits everyone's phone) and **missed tickets** (auto-assigned, reassigned, Gayda's, and Change Request tickets are quiet). Both are true at once, which is why "the new ticket alerts" feel broken no matter which failure any individual tech hit that week. Cyber doesn't feel this because rule 27 gives them exactly one predictable, team-wide, branded email per new ticket.

---

## 7. Recommendations

No changes have been made. These are proposed for internal review, ordered by impact. Effort ratings: S (< 30 min), M (1–2 h), L (half day+).

### Priority 1 — Fix MT new-ticket alerting (addresses the complaint directly)

- **R1 (S). Create "NEW TICKET | Managed Tech" as a Team Notification**, mirroring rule 27: trigger Workflow Step Started, conditions Team = Support (Sys Admins) and Type ≠ Project Task, template −103 NEW TICKET, email delivery. The Support type already starts the "Managed Technology – Active" workflow, so this is a clone-and-edit of rule 27. Every new Support ticket then produces exactly one consistent team email regardless of assignment — including for future hires.
- **R2 (M). Replace the five per-person rule pairs with two consolidated role-based rules:** "MT | Ticket assigned to you" (New Ticket Logged – Assigned to Recipient, no agent condition, subscribers = Managed Technology Role + Mgmt role) and "MT | Your ticket updated by user" (Ticket Updated by User – Assigned to Recipient, same subscribers). Assigned-to-recipient events are inherently per-recipient, so the agent conditions are redundant — one rule covers everyone, closes the Gayda gap (F2), and new hires inherit via role. Then retire rules 42–43 and 46–53.
- **R3 (S). Add a reassignment alert** for both departments using the ticket-reassignment event (the "Request Re-assigned" popup template already exists): recipient = new assignee, channels email + popup + mobile push. This kills the biggest silent failure (F4).
- **R4 (S). Decide the unassigned-blast policy.** Keep rule 37 but consider: narrow it to popup + email only (drop the double push), and/or subscribe only a designated dispatcher/triage rotation instead of all six. With R1 in place, rule 37's job shrinks to "somebody claim this," which does not need four channels to six people. Also drop its Type=Support-only condition or clone it for Change Requests (F5).

### Priority 2 — Coverage gaps that bite silently

- **R5 (S). Verify and fix SOC Alert-type coverage (F7).** Log one test Alert ticket and confirm whether rule 27 fires. If not, either attach a workflow to the Alert type or add a Team/New-Ticket rule with Team = Cyber Ops (Analysts). While there, revisit Alert's default priority (currently Low).
- **R6 (M). Add SLA warning/breach notifications (F6):** 1st SLA warning → assigned agent (popup + mobile push); breach → assigned agent + team manager (email + push). The stock popup templates are ready.
- **R7 (S). Add a Contract Renewal notification (F8):** New Ticket Logged, Type = Contract Renewal → Contract Renewals team (email is enough).
- **R8 (S). Fix rule 54's event** to "Ticket Updated by User – Unassigned" (match rule 55), or retire it if sales prefers.

### Priority 3 — Noise reduction & channel policy

- **R9 (M). Adopt a channel policy and re-tier every rule.** Suggested tiers: **mobile push + all channels** only for act-now events (ticket assigned to you, SLA warning/breach, unassigned support ticket if kept broad); **email + popup** for team awareness (new team ticket, user updates); **email or Halo-only** for business/financial FYIs (approved quote, sales order, PO, invoice paid, order-to-invoice, feedback). Today's all-channels default is the main fatigue driver (F11). Note quote/order events currently push to phones at any hour.
- **R10 (S). Hygiene sweep:** remove disabled agents (Brooke, Vivan) from subscriber lists, dedupe Chris Tjotjos on MENTION, and reconsider "Allow multiple notifications per event per recipient" (OFF makes double-subscription harmless).
- **R11 (S). Standardize new-ticket alerts on template −103** (rule 37 currently uses #32), and prioritize the Phase 3 restyle of **#32 Technician Update** — it is the body behind 13 of 25 rules and is still stock.

### Priority 4 — Operability

- **R12 (S). Turn ON notification logging and the admin Event Log tab** at least for the duration of the redesign, so "did it fire?" is answerable during rollout.
- **R13 (S). Consider enabling the agent "Do not disturb" toggle** once channels are re-tiered — a sanctioned mute beats invisible personal unsubscribes.
- **R14 (M). Subscribe roles, not individuals, everywhere** (the role machinery is already in use on MENTION/37/30). New hires and departures then self-maintain.
- **R15 (process). Pilot with MT for two weeks** (R1–R4 only), collect feedback, then apply the same pattern to Cyber and Sales. Re-run this audit's inventory afterward to confirm the end state.

### Suggested end-state (for discussion)

Per department, roughly **4 rules instead of 12+**: (1) team new-ticket alert, (2) assigned-to-you (new + reassigned), (3) your-ticket-updated-by-user, (4) unassigned/triage safety net — plus shared SLA warnings and the existing business/financial set at reduced channel intensity.

---

## 8. Open Items / Limitations

1. **Per-agent personal preferences are invisible to this audit.** Agents may have personally muted subscriptions (a likely partial explanation for "alerts don't work" reports). Recommend a quick poll of the MT team, or checking each agent's preference pane, before concluding any rule "doesn't fire."
2. **No live-fire verification** was possible (read-only). R5's Alert-type test and a Support-ticket end-to-end test (log → assign → reassign → user reply) are the two tests worth running before/after changes.
3. **"Send Ticket Type bcc emails" is ON** — worth confirming which mailbox(es) receive bcc copies and whether that's still wanted.
4. Follower notifications are fully off — confirm that's intentional.
5. Inbound reply-threading remains unverified from the email-template project (pre-existing item).

---

## Appendix A — Notification rule ID map

Rule IDs for direct access (`https://simvay.halopsa.com/config/notifications/notifications?id=N`):
1 MENTION · 21 APPROVED QUOTE · 22 NEW SALES ORDER · 27 NEW TICKET | Cyber · 29 PURCHASE ORDER ISSUED · 30 Ticket Update by User | Cybersecurity · 32 INVOICE PAID · 37 UNASSIGNED | New Support Ticket · 38 UNASSIGNED | Updated Support Ticket · 41 TICKET FEEDBACK · 42 OSWALD | UPDATED · 43 OSWALD | NEW · 44 UNASSIGNED | New Opportunity · 45 UNASSIGNED | New Lead · 46 MAZZARO | NEW · 47 CHAJON | NEW · 48 GOETZ | NEW · 49 KARENKE | NEW · 50 KARENKE | UPDATED · 51 CHAJON | UPDATED · 52 GOETZ | UPDATED · 53 MAZZARO | UPDATED · 54 UNASSIGNED | Updated Opportunity · 55 UNASSIGNED | Updated Lead · 56 ORDER to INVOICE

## Appendix B — Email templates referenced by rules

| Template | Used by rules | State |
|---|---|---|
| #32 Technician Update | 1, 30, 37, 38, 42, 50–53 (+status-stale emails) | **Stock body — Phase 3 pending** |
| −103 NEW TICKET (internal card) | 27, 43–49, 54, 55 | Restyled 2026-07-17 |
| #246 Quote Approved | 21 (+ client copy) | Kept (Outlook pipe rules) |
| −115 NEW SALES ORDER (Internal) | 22 | Created 2026-07-18 (with cost/margin) |
| −112 Invoice Paid | 32 | Restyled 2026-07-17 |
