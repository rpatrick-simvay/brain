# Project Proposal (v2) — PagerDuty alerting for Cybersecurity tickets in HaloPSA

**Prepared for:** Ryan Patrick, Simvay
**Date:** 2026-08-04
**Status:** PROPOSAL — nothing has been created or changed in HaloPSA, PagerDuty or Cloudflare
**Review:** v1 was scrutinised by three independent reviewers (technical correctness, alerting
design, operational risk). Their findings changed the recommendation. §9 records what changed.

---

## 1. Executive summary

You asked for a new PagerDuty Service that alerts on new Cybersecurity tickets in HaloPSA. That is
buildable, and §5 specifies it. But the measured data says building exactly that would page the SOC
about **~10 tickets a week of which about 2 are real**, and would not catch the failure mode that is
actually hurting you.

**What the numbers say** (measured 2026-08-04, post-connector-cutover window Jul 28 – Aug 4):

| Type-34 "Event" tickets in 8 days | Count | Rate |
|---|---:|---:|
| CISA Cyber Hygiene / WAS scan report emails | 6 | 5.2/wk |
| SentinelOne **vendor marketing email** | 1 | 0.9/wk |
| Client requests (VPN region allow, Boomi bypass) | 2 | 1.7/wk |
| **Genuine security signal** (credential stealer, anomalous sign-in) | **2** | **1.7/wk** |
| **Total** | **11** | **9.6/wk** |

So an alert-on-creation design has a **~80% noise rate** before any filtering, and the noise arrives
in bursts — five CISA report tickets landed within two minutes on Aug 3.

Meanwhile the real gap is staleness: **12 of 51 open Cyber Ops tickets have had no action for over
7 days, and 7 for over 14 days** — including an MDR onboarding at 70 days and four compliance
tracking tickets at 40–59 days. Nothing alerts on those today.

And ticket creation is usually the *output* of triage, not the input. Ticket 51400 ("Credential
Leak") was created and resolved by the same analyst three minutes apart, with the opening note
*"This is not new information, just creating a ticket for record keeping."* Paging on that tells the
SOC about work that just finished.

**Recommendation: build the new Service, but point better triggers at it.**

- **Phase A (recommended, ~4 hrs):** a **Cyber Watchdog** — alert when a Cyber ticket goes
  *unattended*: unassigned for N hours, no action for N days, and any new Cyber ticket raised
  **out of hours**. Low-urgency to start.
- **Phase B (optional, +2 hrs):** add in-hours alert-on-creation, filtered hard, only if Phase A
  shows a gap it doesn't cover.

If you'd rather just have exactly what you asked for, §5.4 gives the alert-on-creation build with
the filters corrected — it's a subset of the same plumbing, so nothing is wasted either way.

---

## 2. What is already in place

### 2.1 PagerDuty (read 2026-08-04)

| Object | ID | Notes |
|---|---|---|
| Team **Security Operations Center** | `P66WLWF` | |
| Team **Technology Management** | `P0KYTKC` | |
| Service **SentinelOne** | `PG0FTPW` | EP `P334LDW`, team SOC |
| Service **Cyber Infra** | `P0RL2B5` | EP `PEASUHT`, team SOC |
| Service **Auvik** | `PEVYNFV` | EP `PSFD6HJ`, team Technology Management |
| Global Event Orchestration **SOC Alert Routing** | `c44b63cf-f3ac-4f13-a96a-37e09db74734` | Team SOC, 2 routes |

Orchestration router:

| Rule | Condition | Route to |
|---|---|---|
| `408f005c` | `event.custom_details.type matches 'New Sentinel One Alert'` | SentinelOne `PG0FTPW` |
| `d94f941b` | `event.custom_details.type matches regex '^HEALTH'` | Cyber Infra `P0RL2B5` |
| catch-all | — | `unrouted` (creates a *suppressed* alert — no incident, no page) |

**On-call, now verified.** `get_escalation_policy` fails on this account (the MCP cannot parse
`schedule_v3_reference`), but **`list_oncalls` works**. Escalation policy `P334LDW`:

| Level | Target | People |
|---|---|---|
| 1 | Schedule *SOC Alerts - Tier 1* `P8S01MI` | Shane Goodsite, Stevie Kantor |
| 2 | Schedule *SOC Alerts - Tier 2* `P4FC1NV` | James Hering, Gabe Lister |
| 3 | Direct user, **no schedule, unbounded** | **Ryan Patrick** |

Cyber Infra's `PEASUHT` escalates to **James Hering alone**, level 1, no schedule.

### 2.2 HaloPSA

**A native PagerDuty integration exists and is configured** (`/config/integrations/pagerduty`): API
key stored, one Service Mapping — Service *SentinelOne*, Default Ticket Type *Alert*, Default Agent
*Shane Goodsite*, User for New Tickets *Ben Castle*, **Don't sync User created Tickets = Yes**.

The dialog's own help text defines the semantics:

- *Default Ticket Type* — "Incidents synced **from PagerDuty** will be created in HaloPSA using this Ticket Type"
- *Default Agent* — "used to create an Incident in PagerDuty **when a User triggers this via the portal**"
- *User for New Tickets* — "Tickets raised from PagerDuty webhooks will be assigned to this User"

**Two consequences.** First, the outbound direction only fires for **portal-raised** tickets, so the
native integration cannot meet the objective. Second — and this needs resolving before anything is
built — **HaloPSA contains zero Alert (type 21) tickets, ever** (verified: `record_count = 0`, open
and closed). The inbound PD→Halo path has apparently never created a ticket. Whether that integration
is dormant, or scoped only to the mapped SentinelOne service, is unknown and is a gating question:
if it turns out to be account-wide, every incident on a *new* service would create a Halo Alert
ticket, and Alert tickets have `default_sendemail: true`, are **not** excluded by notification rules
57/58/59, and have had **no ticket area** since 2026-07-28 — invisible in the UI while generating
mail.

**Webhooks module** (`/config/integrations/webhooks`): **currently empty — zero webhooks
configured.** The New Webhook form provides:

- Payload URL, Method (Post), Content Type (`application/json`), **Authentication** (observed
  default "No authentication"; Halo's published guide documents **Basic Authentication** as the only
  alternative — no custom header)
- **Payload**: "Small object with key fields only" — Halo's guide documents four options including
  **"Use a custom payload"**
- **Batching**: one delivery per event occurrence
- **Events** table, each event with its own **Conditions** (Field / Rule Type / Value) — the same
  criteria engine as notification and ticket rules
- **Enabled** checkbox, **Day(s) to Retain Logs** = 30, and a **Deliveries** tab with request/response
  logs and a **Redeliver** button (a "Use lightweight logs" option disables bodies and breaks Redeliver)

Events personally observed in the webhook picker: `New Ticket Logged`, `New PI Ticket Logged`,
**`New OOH Ticket Logged`**, `New Ticket Logged (Qualified)`, `Ticket Updated by User`,
`PI Ticket Updated by User`, `OOH Ticket Updated by User`, `Ticket Updated by User (Qualified)`,
`Ticket Changed`, `Ticket Status Changed`. The notification engine additionally offers `Closed`,
`Ticket Unassigned for X Hours`, `No Actions for X Hours`, `No Actions for X Days`, `SLA Breached`,
`Priority Escalated` — the two engines share the same event tree in every respect observed, but the
watchdog events have **not been individually confirmed in the webhook picker**. That is Phase 0
item 1, and Phase A depends on it.

### 2.3 The Cyber ticket landscape

Cyber Ops (Analysts) is Halo team **17** — Gabe Lister (19), James Hering (20), Shane Goodsite (18),
Stevie Kantor (28), manager Ryan Patrick (14). Ticket types defaulting to that team: **Event (34)**,
Alert (21), **Action1 (41)**, User Travel (40), New Starter Request (17), Business Review (29),
Cyber Ops Daily Activity Report (36), Risk (26), HaloPSA Issue (32).

**Important correction to the noise model.** Before 2026-07-28 the Action1 connector wrote its
tickets as type **34 (Event)** — 67 of them between Jun 1 and Jul 27, 8.2/week. Since the cutover to
type **41** they are correctly typed: **zero Action1-summary tickets on type 34 since Jul 28.** So a
ticket-type exclusion does work going forward — but anyone baselining volume on historical data will
badly overestimate, and any reprocessing of old tickets would leak.

**The dominant go-forward noise is inbound email, not Action1**: CISA Cyber Hygiene / WAS reports
from `reports@cyber.dhs.gov` and `vulnerability@cisa.dhs.gov` at ~5/week, plus SentinelOne marketing
mail. v1's filter did not exclude either.

### 2.4 The Cloudflare stack

Production Workers already exist — `halopsa`, `action1`, `halopsa-oauth` — with KV, runtime secrets
in the Cloudflare dashboard, and CI deploys via GitHub Actions from
`github.com/rpatrick-simvay/mcp-workers`. The Cloudflare MCP can manage KV but **cannot deploy worker
code**. Per Runbook 09, **Ryan is the sole developer** and the only person who can deploy.

---

## 3. Options considered

| # | Option | Verdict |
|---|---|---|
| 1 | **Native Halo PagerDuty integration** — add a Service Mapping | **Rejected.** Outbound fires only for portal-raised tickets; mapping is per ticket type with no team filter; and the same mapping controls PD→Halo inbound, so editing it risks the SentinelOne path. |
| 2 | **Halo Webhook → Events API v2 directly**, using Halo's "Use a custom payload" option | **Viable, worth a look in Phase 0.** v1 wrongly claimed this was impossible. It is genuinely simpler. Against it: the PagerDuty routing key would live in Halo config, readable by six effective superadmins (Runbook 09 F1, incl. one unconfirmed Administrator account with no 2FA); no version control; severity mapping and the resolve/dedup logic would have to be expressible in a template. **Evaluate the custom-payload editor before committing.** |
| 3 | **Halo Custom Integration + Runbook step** | **Rejected.** Runbook steps hang off workflows; only Event has one (workflow 18), so coverage is uneven and adding a step edits the live SOC workflow — an environment with a documented history of all-or-nothing saves rolling back an entire payload. |
| 4 | **Halo Webhook → Cloudflare Worker → PagerDuty** | **Recommended.** Filtering, severity mapping and dedup live in reviewable code; the PagerDuty key never enters Halo; Halo's Deliveries log gives 30 days of audit and one-click Redeliver. |

**Change from v1: the Worker posts to a dedicated Events API v2 integration key on the new service,
not to the shared orchestration routing key.** Reasons:

- The orchestration router API is a **full replace** of the rule array. A malformed edit silently
  deletes the SentinelOne and Cyber Infra routes and sends every SOC alert to `unrouted` — no
  incident, no page, no error. Not worth the risk for a single source with a single destination.
- The orchestration routing key is **shared with SentinelOne and Cyber Infra**. Adding a fourth
  holder means a leak forces re-keying every SOC source at once. A per-service key is independently
  rotatable.
- The fan-out pattern exists to split one aggregated stream. Here there is one source and one
  destination, so the hop buys nothing.

---

## 4. Recommended design — Phase A: Cyber Watchdog

```
HaloPSA  ──webhook (JSON POST, Basic auth, per-event conditions)──▶  Cloudflare Worker
                                                                          │
                                        validate → re-filter → map severity → build v2 envelope
                                                    dedup_key = halo-<event>-<ticket id>
                                                                          ▼
                                    PagerDuty Service "HaloPSA — Cyber Watchdog"
                                    (dedicated Events API v2 integration key)
```

### 4.1 New PagerDuty service

| Setting | Value |
|---|---|
| Name | **HaloPSA — Cyber Watchdog** |
| Description | "Unattended or out-of-hours Cybersecurity tickets in HaloPSA. Not a detection source — see SentinelOne." |
| Team | Security Operations Center `P66WLWF` |
| Integration | **Events API v2**, dedicated key (not the orchestration key) |
| Escalation policy | **New, notify-only** — do **not** reuse `P334LDW` during the soak |
| **Incident urgency** | **Severity-based (Dynamic Notifications)** — otherwise the severity mapping is cosmetic and `info` pages exactly as hard as `critical` |
| Alert grouping | Off |
| Auto-resolve timeout | **24 hours** — a backstop so a dropped resolve cannot strand an incident forever |

### 4.2 Triggers

| # | Halo event | Conditions | Severity | Catches |
|---|---|---|---|---|
| A1 | `Ticket Unassigned for X Hours` (X = 2) | Type = Event · Team = Cyber Ops (Analysts) · exclusions below | `warning` | Nobody has picked it up — newly meaningful since client auto-assign was turned off on 2026-08-04 |
| A2 | `No Actions for X Days` (X = 5) | Type = Event · open · exclusions below | `info` (digest) | The 12 stale tickets — the failure mode that is actually happening |
| A3 | `New OOH Ticket Logged` | Type = Event · Team = Cyber Ops (Analysts) · exclusions below | `error` | The genuine after-hours ticket, at roughly **1/month** |
| A4 | `Closed` | same | resolve | Clears A1/A3 incidents |

**Filter is an allowlist, not a blocklist:** `Ticket Type Is equal to Event`. Any ticket type added to
Cyber Ops in future is then silent by default rather than paging by default — the opposite of the
maintenance debt Runbook 08 §7 already carries ("any new one must repeat it").

**Plus two exclusions** aimed at the real noise:

- `Summary Does not contain "Cyber Hygiene Report"`
- `Summary Does not contain "WAS Results"`

(and a Worker-side sender check on `reports@cyber.dhs.gov` / `vulnerability@cisa.dhs.gov` as a
belt-and-braces second gate, since the summary format is CISA's to change.)

**Estimated page volume: low single digits per week**, versus ~10 for alert-on-creation, with every
page corresponding to an unmet obligation rather than an arrival.

### 4.3 Worker behaviour — corrections from review

- **`custom_details` goes inside `payload`.** In Events API v2, `routing_key`, `event_action`,
  `dedup_key`, `client`, `client_url`, `links` and `images` are top-level; `summary`, `severity`,
  `source`, `component`, `group`, `class`, `custom_details` and `timestamp` live **inside `payload`**.
  Getting this wrong fails silently — PagerDuty still returns **202 Accepted**, Halo's Deliveries log
  is all green, and no incident is ever created. v1 had it wrong.
- **PagerDuty returns 202, not 200** — the success check must accept any 2xx.
- **Resolve events carry a full payload.** If the orchestration is ever reintroduced, a bare resolve
  (routing key + action + dedup key) matches no route; PagerDuty explicitly documents that *all*
  events including resolves are re-evaluated against routing rules. Posting direct to the service key
  makes this moot, but the Worker should send the full payload regardless.
- **Severity is required and enum-constrained** to `critical | error | warning | info`; an unmapped
  value returns 400. Default to `warning`.
- **Key on numeric `priority_id`, not the display name.** Verified against `/api/Priority`: 1 =
  Critical/Urgent, 2 = High, 3 = Medium, 4 = Low, with no priority 5. But display names are
  SLA-scoped — `priority_id: 1` renders as "Urgent" under SLA 2, "Critical" under SLAs 1/3, and
  **"NO SLA"** under SLA 5. Halo's webhook has an ID-vs-name toggle for single-select fields.
- **Return non-2xx to Halo on failure** so the delivery is flagged and can be Redelivered. Halo has
  no automatic retry.
- Handle **reopen, merge and double-close**: a merged ticket (`merged_into_id`) fires no close and
  would strand its incident; the 24-hour auto-resolve backstop covers it.

### 4.4 Secrets

| Secret | Where | Rotation |
|---|---|---|
| PagerDuty service integration key | Cloudflare Worker secret | Regenerate on the service; single-system blast radius |
| Halo → Worker Basic auth credential | Cloudflare Worker secret + Halo webhook auth | Worker accepts old+new for a window → flip Halo → drop old |

Note the Halo half is readable by any Halo superadmin. Runbook 09 F1 counts **six effective
superadmins**, and F4 flags one Administrator account (Lemanowicz) with unconfirmed email and no 2FA —
open question Q3 in that runbook. **Resolve Q3 before placing a shared secret in Halo.**

---

## 5. If you want exactly what you asked for

Alert-on-creation is the same plumbing with one trigger swapped. Use `New Ticket Logged` in place of
A1/A2/A3, with the identical allowlist and CISA exclusions. Expect ~4 alerts/week after filtering, of
which ~2 are genuinely actionable. Keep it **notify-only**; do not attach it to `P334LDW`.

This is a strict subset of Phase A, so starting with the watchdog costs nothing if you later decide
you want creation alerts too.

---

## 6. Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | **Alert fatigue contaminating a working stream.** SentinelOne's PD service took 399 incidents in the week Jul 28–Aug 3, 67% out-of-hours, **median resolve 26.5 min**. Feeding a known-noisy stream into the same people, same phone, same escalation policy teaches dismissal. | Separate, notify-only escalation policy. Never reuse `P334LDW` until the stream has earned it. |
| R2 | **Halo Alert-type ticket loop** if the inbound PD→Halo integration turns out to be account-wide. | Gating question in Phase 0. Independently, add `Ticket Type ≠ Alert` to notification rules 57/58/59 and either give type 21 an area or retire it. |
| R3 | **CISA burst noise** — 5 tickets in 2 minutes observed. | Summary exclusions plus a Worker-side sender check. |
| R4 | **Worker is a single point of failure with a single maintainer.** | Do **not** narrow email rules 57/58/59 — they are the no-code fallback. Second deployer + org-owned repo before go-live. Heartbeat monitoring (but note Cyber Infra pages James Hering alone). |
| R5 | **Silent failure via wrong payload nesting** — 202 Accepted, no incident. | Phase 4 verification asserts an *incident exists*, not that PagerDuty returned 2xx. |
| R6 | **Ticket-rule ordering.** Ticket rules rewrite Team after creation (rule 13 moves Action1 tickets to Support Sys Admins). Whether the webhook fires before or after rule evaluation is unknown. | Establish empirically in Phase 0; prefer conditions on Ticket Type (immutable) over Team. |
| R7 | **Test noise** — there is no HaloPSA sandbox. Every test ticket also triggers rules 57/58/59 and emails the whole Cyber Ops team. | Stage: capture endpoint → log-and-drop Worker route → service with a no-op escalation policy → announce the test window to Cyber Ops. |
| R8 | **Reporting blind spot.** The weekly retrospective filters on `service_ids: [PEVYNFV, PG0FTPW]` and the QBR skill filters `service_name == "SentinelOne"`, so both are safe — but the new stream would be invisible, and the headline "alert → ticket → incident" funnel becomes ambiguous. | Add the new service to the retrospective runbook §5.5 explicitly, as an inclusion or a documented exclusion. |

---

## 7. Plan and effort (revised upward — v1's 5–6 hrs was code time only)

| Phase | Work | Effort |
|---|---|---|
| 0 | Confirm watchdog events exist in the **webhook** picker; enumerate webhook auth options; evaluate "Use a custom payload"; capture one real payload; settle the inbound-integration scope question; test rule-vs-webhook ordering | **2–3 hrs** |
| 1 | Create PD service + dedicated integration key + notify-only escalation policy | 30 min |
| 2 | Write and deploy the Worker via the existing GitHub Actions pipeline | 2–3 hrs |
| 3 | Create the Halo webhook and its per-event conditions (two-modal criteria flow, ~300-entry field picker, swallowed first clicks, forms that scroll under you — screenshot-verify every field) | **2–3 hrs** |
| 4 | Verify: unassigned fires, stale fires, OOH fires, close resolves, CISA excluded, Action1 excluded, **incident actually created** | 2 hrs |
| 5 | Runbook 12 + updates to Runbooks 04/08 and the retrospective runbook; handover card | 1 hr |
| 6 | Two-week soak at notify-only, then decide on urgency | 2 wks elapsed |

**Total hands-on: 9–13 hours**, spread across about two and a half weeks.

**Rollback,** in order: (1) untick **Enabled** on the Halo webhook — the checkbox does exist, it was
observed on the form; (2) **bulk-resolve any open incidents on the new service** (the 24-hour
auto-resolve backstop limits this, but do it explicitly); (3) delete the service or park it on a
no-op escalation policy; (4) leave the Worker route returning 204. Because there is no orchestration
edit in this design, there is no router state to restore.

---

## 8. Decisions needed

1. **Watchdog (Phase A) or alert-on-creation (§5), or both?** *Recommendation: watchdog first.*
2. **Thresholds** — unassigned for 2 hours? no-action for 5 days? *Recommendation: 2h / 5d, tune after the soak.*
3. **Notify-only or page?** *Recommendation: notify-only for two weeks, then revisit with evidence.*
4. **Escalation policy** — new notify-only policy, or reuse `P334LDW`? *Recommendation: new.*
5. **Scope** — Event type only, or add User Travel / New Starter Request? *Recommendation: Event only.*
6. **Email rules 57/58/59** — keep as the redundant channel? *Recommendation: keep, unchanged.*
7. **Second deployer** — who besides you gets Cloudflare deploy rights before this goes live?

---

## 9. What changed after review

| v1 claim | Corrected |
|---|---|
| "~10 new Cyber Event tickets a week, comfortably inside noise tolerance" | ~10/week is right, but **~80% is noise** (CISA reports, vendor marketing). Genuine signal ≈ 2/week. v1 imported the retrospective's 9–11 funnel figure, which counts analyst-triaged events, not ticket creations. |
| Exclude Action1 by ticket type | Correct **going forward only**. Pre-2026-07-28 the connector wrote Action1 tickets as type 34; 67 of them Jun 1 – Jul 27. Zero since the cutover. |
| Halo Standard Webhook cannot build an Events API v2 envelope | **Wrong.** Halo documents a "Use a custom payload" option. Option 2 is viable and must be evaluated. |
| Authentication: shared secret header | **Wrong.** Halo documents Basic Auth as the only alternative to none. |
| Post via the shared orchestration routing key | **Changed.** Router edits are full-replace (SOC-blinding risk) and the key is shared across three sources. Use a dedicated service key. |
| `custom_details` at top level | **Wrong.** It belongs inside `payload`. Getting it wrong returns 202 with no incident — silent failure. |
| Severity mapping controls paging urgency | **Wrong** unless the service is set to severity-based Dynamic Notifications. |
| Auto-resolve timeout Off | **Changed to 24h.** A dropped or out-of-order resolve would otherwise strand an incident permanently. |
| Who is on call is unverifiable | **Wrong.** `list_oncalls` works: Tier 1 Goodsite/Kantor, Tier 2 Hering/Lister, L3 Ryan unbounded, 24/7 coverage. |
| Alert (21) tickets are created by the inbound integration | **Unproven.** Zero Alert tickets exist, ever. Inbound scope is now a gating question. |
| Blocklist of excluded ticket types | **Changed to an allowlist** — fail closed. |
| Effort 5–6 hrs; rollback leaves no residue | **9–13 hrs**; rollback strands open incidents unless they are explicitly resolved. |
| — | **New:** the strongest argument for a different trigger is that client auto-assign was turned off for 8 clients on 2026-08-04, so Cyber tickets now arrive **unassigned** — which makes "unassigned for N hours" both meaningful and measurable for the first time. |

---

## 10. Appendix — verification notes

All findings were read on **2026-08-04** via the read-only HaloPSA MCP connector, the PagerDuty MCP
connector, and read-only navigation of the HaloPSA configuration UI. **No configuration was created,
changed or saved.** The New Webhook and Service Mapping forms were opened to enumerate fields and
cancelled; the Webhooks list remains empty.

Still unverified, carried into Phase 0:

1. Whether `Ticket Unassigned for X Hours`, `No Actions for X Days` and `Closed` appear in the
   **webhook** event picker (confirmed in the notification picker; the trees have matched everywhere
   observed). **Phase A depends on this.**
2. The full list of Halo webhook Authentication options (only "No authentication" observed directly).
3. The capabilities of Halo's "Use a custom payload" editor.
4. The exact JSON of "Small object with key fields only".
5. Whether the Halo↔PagerDuty inbound sync is account-wide or scoped to the mapped service.
6. Whether webhooks fire before or after ticket-rule evaluation (affects Team-based conditions).
7. PagerDuty licensing — reviewers assert billing is per-user with unlimited services; confirm
   against your plan.
