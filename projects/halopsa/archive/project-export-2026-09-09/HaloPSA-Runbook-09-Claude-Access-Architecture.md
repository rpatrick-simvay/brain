# Simvay HaloPSA — Runbook 09: Claude Access Architecture (Employee Rollout + SARA)

> **Purpose:** Decision record and build tracker for rolling Claude access to HaloPSA out
> beyond the two org admins. Companion to Runbook 01 §2 (current read-only MCP connector).
>
> **Decision owner:** Ryan Patrick · **Decided:** 2026-07-30
> **Last updated:** 2026-09-01 (§11.17 — post-go-live incident 4: Meghan "Ticket not found"
> sending an invoice whose linked Opportunity sat in the Cybersecurity department. Root cause:
> Operations role lacked that department row. Fixed on the role's Departments & Teams tab,
> API-verified. Prior: §11.16 closed-ticket edit fix 2026-08-31.)

## 1. Decision (2026-07-30)

The current broad read-only MCP connector (Runbook 01 §2) is **admin-tier only** — Ryan and
partner Chris (full org control). It is too permissive for general employees because it runs
as a single service account and ignores each agent's Halo permissions.

**Chosen architecture, in order:**

1. **Now — per-user OAuth passthrough MCP.** MCP OAuth 2.1 flow delegating auth to HaloPSA's
   **Authorisation Code** login type. Each employee signs into Halo as themselves (via Entra
   SSO) → every API call runs with *their* Halo agent permissions. Read-only scopes first.
2. **Later — SARA (agent-in-the-middle).** Curated task-level tools calling Halo **with the
   requesting user's passthrough token** — the passthrough server is SARA's data plane.

**Division of labor:** Ryan is the sole developer. Kris Oswald's involvement is using the
existing full-access read MCP, which **stays in place unchanged** as the admin tier.

## 2. Live deployment — WORKING (2026-07-30)

- **Worker URL:** `https://halopsa-oauth.simvay.workers.dev`
- **Claude connector URL:** `https://halopsa-oauth.simvay.workers.dev/mcp`
- **Halo redirect URI:** `https://halopsa-oauth.simvay.workers.dev/callback`
- **Halo API app Client ID:** `fb5725c1-fae9-43ba-b190-ffd5d60faf20` — Authorisation Code app
  **with a client secret** (this instance issues one and requires it). Worker secrets
  `HALO_CLIENT_ID` + `HALO_CLIENT_SECRET` set in the Cloudflare dashboard. Observability
  logs enabled (invocation logs on).
- **SMOKE TEST PASSED:** `whoami` returned Agent "Ryan Patrick", ryan@simvay.com, Halo user
  ID `b9f012fe-a781-4b51-98ce-66aaaf03327c`. Full chain proven: MCP OAuth ↔ Halo auth-code +
  PKCE ↔ Entra SSO ↔ per-agent API calls.
- **Gotchas learned:**
  - `invalid_client` (401) at the token endpoint = client secret typo/mismatch. Fix:
    regenerate the secret on the Halo app page, re-save the worker secret, redeploy.
  - Halo's OIDC `sub` is a **GUID**, NOT the integer agent id (Ryan = 14). Resolve via email
    against `/api/Agent` if an integer mapping is ever needed.

## 3. Verified facts

- **Entra ID SSO enforced for all Halo logins — confirmed working with the flow.** Keep
  "Username & Password" unused. Worker + OAuth flow run entirely on Cloudflare — **Ryan's
  machine is not part of the runtime**.
- **Cloudflare account:** workers `halopsa`, `action1`, `halopsa-oauth`; KV namespace
  `halopsa-oauth-OAUTH_KV` id `178aeb7b3d6e47db9dd9798ca87917f0`; no D1. The Cloudflare MCP
  connector can create KV namespaces but **cannot deploy worker code**.
- **Deploys via GitHub Actions** (`.github/workflows/deploy-halopsa-oauth.yml`, repo root):
  checkout@v5 + setup-node@v5 (Node 24) + `cloudflare/wrangler-action@v3`; runs the offline
  harness then deploys on push to main touching `halopsa-oauth/**`; repo secrets
  `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` set. Worker runtime secrets live in the
  Cloudflare dashboard and persist across CI deploys.
- **Device-bridge gotchas:** `.github/workflows/*` is a **protected path** — Claude's remote
  file tools cannot write it; stage in `halopsa-oauth\deploy-workflow\` and `move /Y`.
  Also, the remote-devices file tools disappear entirely when the desktop app closes —
  deliver files via chat and have Ryan save them if that happens mid-session.
- Architecture: `@cloudflare/workers-oauth-provider@0.0.11` + KV; stateless Streamable HTTP;
  no Durable Objects/D1; wrangler-built (npm dependency — deliberate exception to the repo's
  paste-into-dashboard convention).
- Halo auth methods also include JWT Assertion (BETA) and Halo Automation Identity (BETA) —
  possible future SARA service-side options.

## 4. Code — status

- **Repo:** `github.com/rpatrick-simvay/mcp-workers`, clone `E:\Projects\MCP` on ws-ludus.
  Project folder `E:\Projects\MCP\halopsa-oauth\` — self-contained; `Action1/` untouched.
  (`HaloPSA/` admin worker is now at v1.2.1 — see Runbook 01 §2.)
- **M1 code:** `src/index.js` (OAuthProvider wiring; /authorize → Halo with PKCE S256 +
  HttpOnly verifier cookie; /callback code exchange + OIDC/JWT identity;
  tokenExchangeCallback refreshes the upstream Halo token on MCP refresh, aligns TTLs,
  rotates refresh tokens), `src/halo-auth.js`, `src/mcp.js` (tool parity with admin worker +
  `whoami`; per-user token; 401/403 → reconnect/permission guidance), `test-harness.mjs`,
  README (live URLs + Client ID + pilot checklist).
- **2026-08-12 — `src/mcp.js` v0.2.0 written to the repo clone (NOT deployed):** restores
  tool parity with admin worker v1.2.1 — 22 tools (adds invoices, sales orders, quotations,
  purchase orders, contracts, attachments, workflows; allowlist 19 → 25 endpoints) plus the
  429/5xx retry. `test-harness.mjs` extended to 32/32 (was 20/20). Descriptions carry the
  live-verified facts from Runbook 01 §2 (quote ref = `po_ref`, no server-side open/closed
  filter on SO/PO, attachment = ~4-min CDN link).
  - **⚠ DEPLOY IS DELIBERATELY GATED on the §5/§6/§8 permissions audit** (Ryan,
    2026-08-12): the new tools expose exactly the data classes the audit is removing from
    line roles (financials, quotes, POs, contracts). Per-user Halo permissions are the
    enforcement layer, so the role redesign lands FIRST, then this ships.
    **2026-08-17: the gate lifts at Wave 5 step 5.5 of the §11 deployment plan.**
  - **⚠ CI TRAP: pushing these files to `main` AUTO-DEPLOYS the worker** (the workflow
    triggers on any `halopsa-oauth/**` change on main). To update GitHub without deploying,
    push to a **branch** (e.g. `oauth-v0.2`) and hold the merge until the audit is done —
    or keep the commit local. The live worker stays at v0.1.0 (10 tools) until merge.
- Milestones: **M1** ▣ code / ▣ Halo app / ▣ CI / ▣ deployed / ▣ smoke test /
  ☐ >1h refresh verified / ☐ non-admin pilot · **M1.5 tool parity v0.2.0** ▣ code ▣ tests
  ☐ merged-to-main ☐ deployed (gated on audit) · **M2** rollout ☐ · **M3** write scopes ☐ ·
  **M4** SARA ☐

## 5. Risk assessment & permission audit (2026-07-30)

**Deliverables** (in `E:\Projects\MCP\halopsa-oauth\docs\`):
- `Simvay_HaloPSA_AI_Access_Risk_Assessment_2026-07-30.pdf` — **the partner decision
  document.** 8 pages, Simvay-branded. Search-lift thesis, 8 scored behavioural scenarios,
  10 pitfalls + remediations, Relaxed vs Strict configurations, recommendation.
- `Simvay_HaloPSA_Permissions_AI_Risk_Audit_2026-07-30.html` — the original findings audit.

**Core thesis:** the connector grants no new access. It removes the *search lift* — the
effort barrier that made broad permissions safe in practice. Impact is unchanged; likelihood
moves sharply. Four mechanisms: bulk retrieval, aggregation, inference, externalisation.

**Findings (from the API audit):** F1 superadmin sprawl — 6/15 effective SAs: Oswald(3),
Patrick(14), Soltis(15), Tjotjos(24), Lemanowicz(30) via role, **Karenke(21) via a hidden
agent-level SA claim**. F2 zero client/site/tickettype/assettype scoping anywhere; all teams
allow unassigned + other-agent tickets. F3 the four staff roles carry **identical claims**
(verified pairwise). F4 Lemanowicz = Administrator, email+account unconfirmed, no 2FA.
F5 per-agent claim overrides (Karenke SA; Soltis 8 finance claims — the spec for a Finance
role). F6 no Halo 2FA on 24/30/25/26/28; Lister(19) has an **empty SSO claim**. F7 Gayda(26)
dormant since 2026-04-30. F8 invoice/campaign approval true for ALL agents. F9 claims are
opaque codes — one-time UI verification needed.

**Top scenarios (post-AI L×I):** peer comparison / self-benchmarking (20), departure
harvesting (20), client security-posture aggregation (20), margin & compensation inference
(16), confident false inference (16 — note Cyber Ops works outside Halo *by design*, so any
AI "productivity" comparison from Halo hours is wrong), cross-client pricing leak (15),
prompt injection (15), colleague surveillance (12).

**Key structural insight:** six of eight scenarios are resolved by removing **three data
classes** from line roles — financial records, cross-agent time/utilisation, and saved
reports covering either. Only security-posture aggregation genuinely needs client scoping.

**Two configurations:** Option A "Relaxed" (data-class restriction only, ~½ day) vs
Option B "Strict" (adds client scoping, ticket-type restrictions, ~1 day + maintenance).
**Recommendation was Option A+.**

**Open questions for the partners:** Q1 cross-agent time management-only? Q2 any client
contract/sector requiring tighter internal handling? Q3 what is the Lemanowicz account?
Q4 does Tjotjos need Administrator? Q5 do we disclose retrieval logging? Q6 Sales — all
clients or assigned accounts?

> **Q3 ANSWERED 2026-08-06: Justine Lemanowicz is Simvay's fractional CFO.** Not a service or
> shared account. She moves to the new **Finance** role — see §8. Note she is an **external
> contractor**, which makes the Finance role the widest financial reach held by a non-employee.
>
> **Q4 ANSWERED 2026-08-06:** No. Tjotjos moves to the new **Executive** role — see §8.
>
> **Q6 ANSWERED 2026-08-06:** All clients. *"Sales, operations, admin, and Mikes role can all
> view the whole sales pipeline."* — see §8.5.

**Reusable API technique:** role claims arrive in `Agent/<id>?includedetails=true` as
`roles[].claims[]`; role assignment rides on department AND team membership rows (`role_id`);
per-agent `claims` can carry direct grants; Halo API applications are not API-visible —
inventory in Config → Integrations manually.

---

## 6. Checkbox-level permission audit (2026-08-06)

**Trigger:** Ryan + Kris agreed to limit permissions **by business unit** to reduce AI-abuse
risk. That required §5's F9 to be closed — the opaque claim codes had to be resolved to real
UI checkbox labels before anything could be changed.

**Deliverables** (save to `E:\Projects\MCP\halopsa-oauth\docs\`):
- `Simvay_HaloPSA_Permission_Audit_AI_Risk_2026-08-06.xlsx` — the as-found matrix.
  6 tabs: Read Me · Full Matrix (904 rows) · Removals by Group (185) · Role Summary ·
  Agent Exposure (17 agents) · Top Findings (14).
- `Simvay_HaloPSA_Permission_Audit_AI_Risk_2026-08-06.pdf` — 7-page branded partner document.

**Scope:** all **8 roles × 113 permission settings = 904 assessed rows.** Every value read
from the Halo Roles UI in *view* mode (nothing edited), cross-checked against
`Agent/<id>?includedetails=true`.

### 6.1 The 8 roles (as-found)

| Role | GUID (8) | id_int | Claims | Agents |
|---|---|---|---|---|
| Administrator | `1402be5f` | 2 | 82 | Tjotjos(24), Patrick(14), Soltis(15), Oswald(3) |
| Cybersecurity Operations Role | `21b209aa` | 19 | 78 | Lister(19), Hering(20), Goodsite(18), Kantor(28), Rayborn(27✗) |
| Cybersecurity Operations Role (Management) | `f92ba463` | 21 | 78 | Patrick(14) |
| Managed Technology Role | `20f1b60d` | 18 | 78 | Mazzaro(29), Goetz(17), Chajon(23), Gayda(26) |
| Managed Technology Role (Management) | `18ebffb4` | 20 | 78 | Oswald(3), Karenke(21) |
| Project Manager | `a9ac27f6` | — | — | **none** |
| Sales Executive | `febac04c` | 8 | 70 | Fogarty(22✗), Schilling(25), Oswald(3) |
| Sales Rep | `09ce8c1f` | 16 | 69 | Fogarty(22✗), Schilling(25), Oswald(3) |

### 6.2 Findings

**⚠ F3 CORRECTED AND EXTENDED.** §5 F3 said "the four *staff* roles carry identical claims."
The real picture is worse: the four **operational** roles — Cyber Ops, Cyber Ops (Management),
Managed Technology, Managed Technology (Management) — are **byte-for-byte identical**. Verified
twice: **0 diffs across all 243 UI permission lines** for each of the three comparisons, and
identical 78-claim multisets via the API. The *management* variants are not elevated versions of
the line roles; they are the same role under a different name.

Numbered findings (full text in the PDF and the workbook's Top Findings tab):

1. **`Can Create SQL Data Sources = Yes` on ALL EIGHT roles** — CRITICAL. Arbitrary SQL is not
   constrained by feature-access levels, client restrictions or ticket-type scoping. It sits
   *upstream* of every other control. **Highest-value single removal.**
2. **`Can View Agent Costs = Yes` on ALL EIGHT roles** alongside `Timesheets = Read and Modify
   (All)` — compensation inference made trivial.
3. **`Allow use of all Clients = Yes` on every role**, scoping arrays empty on every agent.
4. The four-identical-roles finding above.
5. **Five accounts with no 2FA, two of them superusers** (24, 25 verified; 30, 26, 28 per F6).
6. **Karenke(21)'s agent-level `SA=true` does not render in the Roles UI.**
7. **The full financial data class is on every line role.**
8. `Can export tickets = Yes` on all 8.
9. **`Password Fields = Visible` on Administrator.**
10. **`Billing Details Access Level` renders as the raw value `3`** on the four operational
    roles — confirm in Edit mode. Possible product defect.
11. Gayda(26) dormant since 2026-04-30, still enabled.
12. Lemanowicz(30) Administrator, no job title, no team rows. **Q3 now ANSWERED — fractional CFO.**
13. **`Project Manager` assigned to nobody and the broadest non-admin role.**
14. `can_approve_invoice` + `can_approve_campaign` true for every agent incl. Unassigned.

### 6.3 Scoring model used

`criticality (0–10) = permission sensitivity (0–10) × grant strength`, where grant strength is
0 (not granted, or a `No - scope to ...` restriction) / 0.55 (read-only or own-only) / 0.7
(team-department scoped) / 1.0 (read+modify or Yes) / 1.1–1.15 (includes delete, or "Visible").
Result on the as-found state: **94 rows at 8.0+**, **185 flagged for removal**.

> **Scoring gotcha:** three values are *restrictions* that a naive scorer reads as grants —
> `Can review Expenses = None`, `Client Group Override = <a group>`, and any `No - scope to ...`
> value. `Client Group Override` is the **mechanism that enforces** scoping; setting it reduces
> risk. Score it 0.

### 6.4 Defect fixes that need no policy decision

1. Enable 2FA on all five accounts lacking it (24, 25, 26, 28, 30) — 20 min.
2. Remove `Can Create SQL Data Sources` from all line roles — 15 min.
3. Remove Karenke's agent-level `SA=true` override — 10 min.
4. `Can View Agent Costs = No` on line roles; Timesheets own-only for line staff — 30 min.

---

## 7. Halo Roles UI — read technique (learned 2026-08-06)

- **URL is `/config/agents/roles`** — **`/config/teams/roles` 404s**. A role: `?id=<role GUID>`.
- Tabs per role: Details · Preferences · Departments & Teams · **Permissions** · Access Control.
- **The Permissions tab renders every setting as label/value text in VIEW mode** — no Edit click
  needed, so the read is completely non-destructive. 243 text lines per role.
- **`get_page_text` returns the whole panel cleanly.** For a compact read, slice
  `document.body.innerText` from the index of `'General Permissions'` to the end and split on
  newlines — ~243 short strings, which passes the `javascript_tool` return filter.
- **Diffing trick:** store the first role's array as `window.__base`, then for later roles return
  only the differing indices. **Only works while navigating within the SPA** — a full page
  navigation wipes `window` state.
- **Gotcha 14 applies hard:** the first click on a tab after a record loads is swallowed. Click,
  wait, re-check for `'General Permissions'`, click again if absent. Do **not** blind-double-click
  in one batch — the second click lands before render and the panel never populates.
- **Do not build a JS "click the back arrow" helper by geometry** — a bounding-rect heuristic
  clicked a nav item and navigated the whole app away, destroying `window.__base`.
- **Project Manager GUID `a9ac27f6-f4e0-46df-b6a7-c7e13dc5ced0`** — not discoverable via agents
  because nobody holds it.
- **Halo's three ways of saying "not granted":** `Not set`, `No`, `No Access`. Treat them as
  equivalent when diffing, or a change plan fills with cosmetic edits (this collapsed a 597-row
  plan to 259 real changes).

### 7.1 Reading the EDIT form (learned 2026-08-06)

- **A new role (`?id=-1`) will not leave the Details tab until it is saved** — you cannot use a
  blank new role to inspect the Permissions dropdowns. Use an existing role you do not mind
  touching (the retired **Project Manager** is the safe choice) and **navigate away by URL** when
  done; that discards cleanly. Never click Save, never press Escape (gotcha 10).
- **The Permissions edit form is react-select, not native `<select>`** — 111 components with ids
  `react-select-N-input`. Option lists exist in the DOM **only while a dropdown is open**, so
  enumerating every option means opening every dropdown. This is why nine option strings in §8.6
  are still unconfirmed.
- **The restriction sections (Ticket Type / Client / Asset Type / Asset Field) render their
  description text but their controls load lazily** — scroll them fully into view before reading.
- **`CRM Access Level` is NOT prospect access.** Its in-form help text reads: *"Includes access to
  notes tab on Halo entities. Used in conjunction with the access level of the entity you are
  on."* It governs the notes tab. Do not use it to hide prospects.

---

## 8. Target role model v4 (decided by Ryan 2026-08-06)

**Deliverable:** `Simvay_HaloPSA_Role_Redesign_Change_Plan_2026-08-06.xlsx` — the approval
workbook. 9 tabs: Read Me · **Change Plan (301 rows, Approve/Decline/Defer/Discuss dropdown)** ·
Target Role Model · Role Migration · Full Matrix (1,017) · Decision Summary ·
**Ticket Type Write Matrix** · **Sales Pipeline Visibility** · **Open Items**.

> **2026-08-17: partner review is COMPLETE** — 279 Approve / 22 Decline / 0 Undecided, plus
> notes on approved rows that override targets. See §11 for the reconciliation rule, the
> **Services Leadership** rename, and the deployment plan.

### 8.1 The nine roles

| Role | Status | Holder(s) | Purpose |
|---|---|---|---|
| Administrator | KEPT, cut to 2 | Patrick(14), Oswald(3) | Full org control. Accepted admin tier per §1. |
| **Executive** | **NEW** | Tjotjos(24) | Reports, invoice receipt, full sales flow. No SA, no config, no SQL. |
| **Finance** | **NEW** | Lemanowicz(30) | Fractional CFO. Financial reporting, invoice/contract oversight, cost and margin. **External contractor.** |
| **Operations** | **NEW** | Soltis(15) | Order processing, POs, invoicing, contract creation, goods receipt. Full pipeline view. |
| Cybersecurity Operations Role | tightened | Lister, Hering, Goodsite, Kantor | SOC line role. No sales pipeline. |
| Managed Technology Role | tightened | Mazzaro, Goetz, Chajon, Gayda (kept per 2026-08-17 decline) | MT line role. No sales pipeline. |
| **Services Leadership** (renamed 2026-08-17 from Managed Technology Role (Management)) | now elevated | Oswald(3), Karenke(21) | Services management across BOTH units: modify on all service ticket types + projects, full pipeline view. |
| Sales Executive | differentiated | Schilling(25) | Full sales flow incl. orders, contracts, cost visibility. |
| Sales Rep | differentiated | (vacant) | Pipeline view + quoting. No cost, no orders, no invoices. |
| ~~Cyber Ops (Management)~~ | **RETIRED** | Patrick → Administrator | Byte-identical to the line role. |
| ~~Project Manager~~ | **RETIRED** | (none) | Broadest non-admin role, zero holders. |

**Effective superusers drop from 5 of 7 sampled agents to 2.** Karenke's hidden agent-level
`SA=true` is removed; Services Leadership becoming genuinely elevated is what makes that
survivable.

### 8.2 The v2 → v3 change: read stays open, WRITE gets scoped

v2 scoped Cyber and MT by client group, which blocked cross-boundary reading. **Ryan asked for
the opposite:** he is not concerned about MT and Cyber *viewing* tickets across the boundary; he
wants **write/action restricted by ticket type**.

Halo supports this natively — but **not on the role**. See §9. Consequently:

- `Allow use of all Clients` → **back to Yes** on Cyber Ops and Managed Technology.
- `Allow use of all Ticket Types` → **back to Yes** (read).
- Write control moves to the **Ticket Type Write Matrix** tab: 18 ticket types × which roles get
  **Modify** via each type's own Access Control list.

### 8.3 Change volume by role (v4)

| Role | Changes | Reductions | Grants |
|---|---|---|---|
| Administrator | 1 | 1 | 0 |
| Executive | 43 | 43 | 0 |
| Finance | 55 | 55 | 0 |
| Operations | 36 | 35 | 1 |
| Cybersecurity Operations Role | 37 | 35 | 0 |
| Managed Technology Role | 37 | 35 | 0 |
| Managed Technology Role (Management) | 30 | 18 | 11 |
| Sales Executive | 30 | 27 | 2 |
| Sales Rep | 32 | 31 | 0 |
| **TOTAL** | **301** | **280** | **14** |

Administrator's single change is `Password Fields: Visible → Hidden`. Executive, Finance and
Operations are compared against **Administrator**, because that is what Tjotjos, Lemanowicz and
Soltis hold today — so all of their reductions are real losses of access.

### 8.4 Deliberate high-risk grants (annotated in the workbook)

- **Finance · Reporting = Read and Modify, `Can View Agent Costs = Yes`, Item Costs, Contracts,
  Timesheets (All)** — all core CFO functions, and all held by an **external contractor**. This
  is the single largest concentration of financial reach outside the partner group.
- **Executive · Reporting = Read and Modify** — requested; saved reports are pre-built bulk
  extracts, so this is the highest residual risk in the Executive role.
- **Executive · Invoices = Read and Modify** — enough to mark invoices received, without
  Create or Delete.
- **Operations · Invoices = Read, Create, Modify and Delete** — she creates invoices. Prefer a
  Create-without-Delete level if Halo exposes one.
- **MT (Mgmt) · `Can Delete Tickets = Yes`** — scores 8.0. Decline if deletes should be admin-only.
  **APPROVED 2026-08-17** (survives into Services Leadership).
- **Administrator · `Can Create SQL Data Sources = Yes`** — accepted, 2 people.

### 8.5 Sales pipeline visibility (decided 2026-08-06)

Ryan, verbatim: *"Sales, operations, admin, and Mikes role can all view the whole sales pipeline."*

> **CONFIRMED 2026-08-17: "Mike's role" = Karenke.** Ryan's deployment-plan request names the
> renamed role explicitly: Services Leadership gets "more visibility to the whole sales
> pipeline". The Executive (FULL) and Finance (read-only partial) assumptions were also
> approved in the workbook. All three §8.5 confirmations are closed.

| Role | Pipeline view | In Ryan's list | CRM | Sales | Quotations |
|---|---|---|---|---|---|
| Administrator | FULL | yes | R+M | R+M | R+M |
| Sales Executive | FULL | yes | R+M | R+M | R+M |
| Sales Rep | FULL | yes | R+M | R+M | R+M |
| Operations | FULL | yes | R+M | R+M | R+M |
| Services Leadership | FULL | yes (as "Mike's role") | R+M | R+M | R+M |
| Executive | FULL | confirmed 2026-08-17 | R+M | R+M | R+M |
| Finance | PARTIAL — read only | confirmed 2026-08-17 | No Access | Read Only | Read Only |
| Cybersecurity Operations Role | **NONE** | yes | No Access | No Access | No Access |
| Managed Technology Role | **NONE** | yes | No Access | No Access | No Access |

**This decision also delivers the prospects/leads restriction.** Excluding Cyber Ops and Managed
Technology from CRM, Sales and Quotations keeps them out of the pipeline without needing a
"Customers only" client group — so §10's client-group item is probably now unnecessary.

**It also supersedes the "assigned-only quotes/opportunities" requirement** for the whole-pipeline
roles: they see everything by decision. **Still wanted long-term (2026-08-17 notes):** Sales Rep
and MT line should eventually see only quotes/opportunities they are attached to (MT: clients
where primary/secondary agent). No per-record mechanism found yet — tracked as OI-2 in §11.

### 8.6 Prerequisites that are NOT checkboxes

1. **Nine target option strings were never observed** in a rendered dropdown and are marked
   `CONFIRM` in the workbook: own-only timesheets (`Read and Modify (Own)`), own-only
   billing-time adjustment (`Own`), `Can review Expenses = None`, and the ticket-type /
   asset-type / client-group restriction values. See §7.1 for why.
2. **`Billing Details Access Level` still renders as the raw value `3`** on the operational
   roles — confirm what level 3 is in Edit mode (§6.2 finding 10).
3. **Reassign the default team on HaloPSA Implementation and HaloPSA Project Task** before
   retiring Cyber Ops (Management) — both currently point at it. *(2026-08-17: both types are
   marked Delete in the workbook — deletion supersedes reassignment if it lands first.)*

---

## 9. Halo's object-level Access Control model (discovered 2026-08-06)

**This is the mechanism behind Ryan's write-by-ticket-type requirement, and it is not on the
role.** It was found in the in-form help text on the role Permissions page:

> *"Allow creation of new Ticket Types and linked objects — This will allow access to Config to
> create new Ticket Types, Actions, Workflows and Approval Processes. **Access to edit specific
> Ticket Types and other objects can be assigned through the objects Access Control list.**"*

Confirmed at **Config → Tickets → Ticket Types → *[type]* → Access Control** (toolbar button).
The dialog states, verbatim:

> *"All Administrators will automatically have Owner access.*
> ***Read access to Ticket Types is determined by other permissions so cannot be set here***
> *(E.G Organization, Role and Agent).*
> ***Only permission to Modify can be granted here."***

**The model, therefore:**

| Layer | Governs | Where it is set |
|---|---|---|
| **Role** | Feature-level access (module read/modify), global ticket permissions, **and READ on ticket types** | Config → Teams & Agents → Roles → Permissions |
| **Object Access Control list** | **MODIFY on a specific object** — ticket type, column profile, list, filter profile, webhook, custom integration, Entra config | On the object itself |
| **Role → Access Control tab** | **Read-only summary** of grants made elsewhere: *"The below is read only. To edit individual entities please navigate to the specified section."* | — |

**Ticket type inventory read 2026-08-06 (18 of 18):** Event, Support, User Travel, Action1,
Alert, Change Request, New Starter Request, Business Review, New Order, Project, Project Task,
Risk (Projects), Pre-Sales, HaloPSA Implementation, HaloPSA Project Task, HaloPSA Issue,
Cyber Ops Daily Activity Report, Techology Mgmt Daily Activity Report *(sic — misspelled in Halo)*.
URL: `/config/tickets/tickettype` (**`/config/tickets/tickettypes` 404s** — singular).

> **2026-08-17: 9 of the 18 are marked DELETE in the approved workbook** — Change Request,
> New Starter Request, Business Review, Risk (Projects), Pre-Sales, HaloPSA Implementation,
> HaloPSA Project Task, HaloPSA Issue, Cyber Ops Daily Activity Report. The surviving 9 carry
> the final write matrix (workbook tab "Final Targets (Reconciled)").

**Not in that list:** Lead, Opportunity and Quick Quote. All 18 have Use = Tickets / Projects /
Contracts. The sales-pipeline types are managed in a config area this session did not open. The
*policy* for them is now settled (§8.5); the *mechanism* to enforce it is not.

**Untested behaviour:** Support's Access Control list is currently **empty**. Whether empty means
"anyone with role read can modify" (likely) or "nobody can" is unverified. **Add one grant on one
low-traffic type — Business Review — and test with a non-admin agent before touching Support.**

---

## 10. Open items (in order)

1. ~~Confirm "Mike's role" = Karenke~~ **ANSWERED 2026-08-17** — Karenke; role renames to
   **Services Leadership** (§8.5, §11).
2. ~~Confirm Executive and Finance pipeline access~~ **ANSWERED 2026-08-17** — both approved
   as proposed (Executive FULL, Finance partial read-only).
3. **Test empty-vs-populated Access Control semantics** on one low-traffic ticket type (§9).
   **Blocker** — now deployment-plan step 0.4.
4. **Find where Lead / Opportunity / Quick Quote are configured** — now step 0.6.
5. ~~Partner review of the Change Plan workbook~~ **DONE 2026-08-17** — 279 Approve /
   22 Decline / 0 Undecided. Decline notes = corrected targets (§11 reconciliation rule).
6. Execute §6.4 defect fixes 1–4 — folded into deployment waves (2FA = 0.5, SQL/costs =
   role edits, Karenke SA = 1.4).
7. Confirm the nine unverified option strings in Edit mode — now step 0.2.
8. Reassign the default team on the two internal HaloPSA project types — now step 0.7
   (deletion in 2.3 may supersede).
9. Build Executive, Finance and Operations; migrate; retire roles — now Waves 4–5.
10. Apply the Ticket Type Write Matrix — now steps 1.6 / 2.3 / 3.5.
11. Narrow the connector allowlist to match; deploy via push. **Note: `src/mcp.js` v0.2.0
    (already in the repo clone, §4) WIDENS the allowlist to admin-worker parity — when this
    item is executed, decide per role whether the financial endpoints (invoice, quotation,
    salesorder, purchaseorder, clientcontract) stay in, relying on per-user Halo permissions,
    or get trimmed from the oauth worker's allowlist.** Unblocks at step 5.5.
12. Pilot 2–3 agents across roles for two weeks; review retrieval logs.
13. Passive check: use the connector >1h after connecting to confirm silent token refresh.
14. Decide connector distribution (Claude Team/Enterprise managed vs manual add).
15. Answer remaining §5 questions: Q1, Q2, Q5.
16. Later: M3 write scopes (fix approval-flag defaults first — F8/finding 14), then SARA.

> ~~Create a "Customers only" client group~~ — **probably unnecessary now.** §8.5's CRM/Sales/
> Quotations exclusion achieves the same intent. Revisit only if prospect *client records* still
> surface for Cyber/MT staff.

---

## 11. Deployment plan (built 2026-08-17, from the completed partner review)

**Deliverable:** `Simvay_HaloPSA_Role_Redesign_Change_Plan_20260817.xlsx` — the v2 workbook
plus two new tabs: **Deployment Plan** (6 waves, 33 steps, status dropdown) and
**Final Targets (Reconciled)** (every row where Ryan's note overrides the v2 target, plus the
final 9-type write matrix). Delivered in chat 2026-08-17.

**Reconciliation rule:** Approve = execute the Change Plan target as written. Decline, or a
note contradicting the target, = **the note is the target**. 22 declines + several noted
approvals reconciled on the new tab.

### 11.1 Execution decisions (Ryan, 2026-08-17)

- **Executor: Claude via the Chrome extension**, Ryan watching, every edit announced first.
  HaloPSA MCP stays read-only; the browser is the write path. 2FA enrolment, smoke tests and
  account deletions stay human.
- **Cadence: 2–3 business days of soak per wave**; next wave only on a clean soak. ~3 weeks.
- **Wave order: 0 Prereqs → 1 MT + Services Leadership → 2 Cyber Ops → 3 Sales →
  4 Back Office (Exec/Ops/Finance) → 5 Admin cleanup.** MT first was Ryan's call — it also
  carries the rename and the first ticket-type ACL grants, so the write-scoping model is
  proven in wave 1.
- **Rollback:** view-mode snapshot of every affected role immediately before each wave; roles
  never deleted until Wave 5.

### 11.2 Headline changes vs the v2 workbook

1. **Managed Technology Role (Management) → "Services Leadership"** — modify on ALL 9
   surviving service ticket types + projects (both units), full pipeline view, Sales Orders
   R+M, POs Read Only, Items R+M, KB keeps delete, dashboards for self.
2. **Gayda(26) is NOT disabled** — Ryan declined; he keeps the tightened MT role, gated on
   2FA enrolment.
3. **Rayborn(27) + Fogarty(22): DELETE** the disabled accounts (check history attribution
   first; archive if deletion unlinks it).
4. **9 ticket types deleted**, 9 survive (list in §9 note). Action1 modify = Cyber + MT + SL
   (closes the Runbook 08 routing question); Project/Project Task/New Order get Cyber (and
   New Order gets MT) added — "MT and Cyber deliver on these project tickets".
5. **Contracts stay readable for both line roles** (Read Only, not No Access) — "teams need
   them to know service scopes".
6. **Operations keeps its ticket-handling muscles** — edit unassigned tickets, change ticket
   type, remove to-dos, edit/delete all appointments all stay Yes.
7. **Finance keeps report publishing + dashboards** ("probably won't but can").

### 11.3 Flags carried into execution

- **AMBIG-1:** Operations · Editing of Actions — Ryan's note "Should be no" vs proposed
  own-only. Confirm whether a cannot-edit option exists during step 0.2, then set.
- **OI-2:** per-record scoping (Sales Rep attached-only quotes/opportunities; MT line
  primary/secondary-agent quotations) — no mechanism found in the role UI. Interim: module
  No Access (MT) / approved scoping (Sales Rep). Revisit after step 0.6.
- **OI-3:** ticket-type deletions assume open tickets can be closed/re-typed first; any type
  that cannot be emptied defers deletion to Wave 5 with its ACL locked down instead.

### 11.4 Wave 1 execution log (2026-08-17, Claude via Chrome)

**DONE and verified (view-mode re-read after every save):**

1. **Pre-edit snapshots** of both MT roles saved (243 lines each; the two were still
   byte-identical, hash-verified). NOTE: several values had already been tightened since the
   08-06 audit read (Password Fields=Hidden, Editing of Actions=Own-only, Reporting=No Access,
   appointments own-only, Can Publish Reports=Not set) — someone partially applied changes
   between audit and execution.
2. **MT (Management) renamed "Services Leadership"** (GUID 18ebffb4 unchanged, id_int 20),
   holders Oswald(3)+Karenke(21) intact, all reconciled permission targets applied.
3. **Karenke's agent-level SA override removed** — `Agent/21?includedetails=true` now shows
   `SA=false` at both agent and role level; everything else inherits from Services Leadership.
   His `twofactor_enabled=true`. He was ALREADY `is_manager` on both MT teams (14+16), so
   Ryan's "add Mike as MT team leader" request was already satisfied — no team edit needed.
4. **Managed Technology (line) role**: all 36 reconciled changes applied and verified.
5. **Business Review ACL test grant placed** (step 0.4): Role=Cybersecurity Operations,
   level=Read and Modify. **Awaiting the human half of the test** — an MT agent tries to
   modify a Business Review ticket; result decides the empty-list semantics.

**Halo facts discovered while editing (extends §7.1):**

- **Editing dropdowns via UI clicks only** — synthetic mousedown/input events do NOT open
  react-select menus here. Pattern that works: real click on control → menu renders inline
  below (options at ~+30/+51/+71/+92px) → real click on option. Verify via
  `.Select__single-value` (walk up from `input[id^=react-select]`, query `[class*=ingleValue]`).
- **NEVER dispatch Escape** (gotcha 10 confirmed the hard way): it silently exits the edit
  form to the list and discards every pending change. Tab is also dangerous while a menu is
  open — react-select tab-selects the highlighted option.
- **§8.6 CONFIRM strings resolved:** `Read and Modify (own)` EXISTS (Timesheets);
  `Can review Expenses = None` EXISTS; `Cannot Edit Actions` EXISTS (resolves AMBIG-1 —
  Operations "Editing of Actions should be no" = Cannot Edit Actions);
  **billing-time adjust has NO "Own" option** — options are No / Managed Only / Managed and
  their Managed / All → MT line set to **No** (SL keeps All).
- **Billing Details Access Level raw "3" = Read and Modify** (dropdown is No Access/Read
  Only/Read and Modify; finding 10 closed — set Read Only on SL, No Access on MT line).
- **Suppliers Access Level + Supplier Contracts Access Level are NON-EDITABLE** in the role
  Permissions form (`div.noedit-value`) — both still Read and Modify on both MT-side roles
  despite a No Access target. Investigate what controls them (licence/module setting?).
- **Invoices has "Read and Create" and "Read, Create and Modify" levels** — the
  create-without-delete level §8.4 wanted for Operations EXISTS.
- **Ticket-type Access Control grant levels are None / Read and Modify / Owner** (not bare
  "Modify"); principal types Role/Agent/Team/Department. **CORRECTION 2026-08-18: the dialog's
  Save only STAGES the grants — the record then drops into edit mode and you MUST click the
  record's Save to commit. Clicking Cancel on the record form DISCARDS the staged ACL rows**
  (confirmed the hard way on Support: grants vanished after dialog-Save + record-Cancel).
  Always reopen Access Control afterwards to verify the rows persisted.
- **Two agents exist that were NOT in the audit:** id 31 "Action1" (**Administrator role** —
  service account, review this) and id 32 "Sara – Automated Analyst (Work in ...)".
  Fogarty(22)/Rayborn(27) no longer appear in the active agents list (already disabled).

**Remaining Wave 1 (gated):** 1.6 Support + Tech Mgmt DAR grants and Change Request deletion
(after the 0.4 human test); 1.7 Gayda 2FA (Ryan); 1.8 smoke tests (Mazzaro + Karenke).

> **2026-08-17 (Ryan): Halo-native 2FA flags are NOT relevant — all agent logins go through
> M365/Entra SSO (§3), where MFA is enforced at the IdP.** The audit's F6 "no 2FA" findings
> and §6.4 fix 1 are superseded; deployment-plan step 0.5 dropped, Gayda (1.7) unblocked, and
> the Wave 4 "2FA hard gate" for Lemanowicz/Tjotjos removed. Residual check (low priority):
> confirm "Username & Password" login stays disabled instance-wide so the SSO policy is the
> only door.

### 11.5 Ticket-type cleanup + Wave 1 step 1.6 completion (2026-08-18, Claude via Chrome)

**Ryan's instruction:** every ticket type flagged "unused" in the workbook comments gets
deleted. Verified ticket-ever counts first via the read-only API — the working filter is
`Tickets?requesttype=<id>&pageinate=true&page_size=1&ticketidonly=true&includeclosed=true`
(`tickettype_id` and `tickettype` are silently IGNORED and return everything).

**All 9 flagged types deleted:** Business Review, Change Request, New Starter Request,
Leaver Request, Incident (unused duplicate), Problem, HaloPSA Implementation, HaloPSA
Project Task, and the remaining flagged type. Post-delete list = exactly the 9 surviving
operational types (Support 1, Project 5, Project Task 20, Alert 21, Event 34, Techology
Mgmt DAR 35, New Order 39, User Travel 40, Action1 41) + 4 sales-side types (Opportunity 6,
Lead 27, Quick Quote 25, Contract Renewal 38).

**Blockers hit and cleared:**

1. **New Starter Request** deletion silently failed → retry surfaced "criteria in use by
   Rule: Azure Automation DB Lookup". Per Ryan: deleted the rule (its only criteria was NSR;
   all outcomes No Change), then the type deleted cleanly.
2. **Types with ticket history refuse deletion** ("move these tickets to another Ticket Type
   before deleting"). 32 historical tickets re-typed first (history preserved, per Ryan's
   "delete anyway" = re-type, don't purge): 30 HaloPSA Project Task tickets → Project Task,
   project 2852 → Project, ticket 50493 → Event. Bulk re-type path: ticket LIST with
   checkboxes (project's task tab, or search an ID then toolbar back-arrow for the results
   list) → select rows → "Edit (N)" → Change Ticket Type → Save.
3. Deleting the two HaloPSA-internal project types also **cleared the old 0.7 blocker**
   (their default team was the retiring Cyber Ops (Mgmt)).

**Step 1.6 DONE:** Support (id 1) and Techology Mgmt DAR (id 35) Access Control now each
carry Role=Managed Technology Role → Read and Modify + Role=Services Leadership → Read and
Modify (DAR also keeps Agent=Ryan Patrick → Owner). Both verified persisted by reopening the
Access Control dialog after the RECORD save (see corrected staging/commit note in §11.4).
The 0.4 empty-ACL semantics test is MOOT — every surviving type has explicit grants and
Business Review no longer exists.

**Wave 1 remaining:** 1.8 smoke tests (Mazzaro cross-boundary read + Support modify; a Cyber
analyst should now FAIL to modify Support/Tech DAR; Karenke services-wide write + pipeline
visibility), then the 2-3 day soak (1.9) before Wave 2 (Cyber Ops).

**Carry-forward flags:** Suppliers + Supplier Contracts access levels non-editable in the
role form (still Read and Modify vs a No Access target); agent 31 "Action1" holds
Administrator (review before Wave 2); OI-2 per-record quote/opportunity scoping has no
mechanism; confirm "Username & Password" login stays disabled instance-wide.

### 11.6 Wave 2 execution log — Cyber Ops (2026-08-18, Claude via Chrome, Windows browser)

Ryan confirmed MT-side soak clean and ordered Wave 2. All four config steps DONE:

1. **2.1 Snapshot:** `CyberOps_line_21b209aa_pre-wave2_2026-08-18.txt` (local + project doc).
   Role GUID **21b209aa-bb73-4b6e-b10d-45c501d2d453**. As with MT, several values were
   already tightened vs the 08-06 audit read (Password Fields, own-only actions/appointments,
   Reporting=No Access, Can change Ticket Type=No).
2. **2.2 Role edits: 35 applied, view-mode verified.** Financial/pipeline class to No Access
   (CRM, Sales, Quotations, Sales Orders, PO, Billing Details, Invoices, Item Costs, Item
   Prices, Agent Costs=No, Expenses=None); Client Contracts = **Read Only** (decline-note
   override); Items/Services/Software Licencing/Item SKU = Read Only; KB = Read and Modify;
   Timesheets = Read and Modify (own); 8 ticket-permission toggles to No (closed-ticket edit,
   billing-time adjust, billing recalc, cross-team assign, priority override, review override,
   action visibility, export); 6 Configuration creators to No + Can Use Data Sources cleared;
   active/inactive toggle = No. **Deviations:** Suppliers + Supplier Contracts NON-EDITABLE
   (still R+M — same noedit fields as MT, carry-forward); **Client Group Override has no
   "Customers only" mechanism — the field is a single-CLIENT picker, not a client-group
   picker** (typed search returns client names; "Customer" → no results). Left Not set,
   joins OI-2 as scoping-without-a-mechanism. Billing-time adjust has no "Own" → No.
   One mis-click self-caught: Software Licencing initially landed "Not set", fixed to
   Read Only in a second edit pass and re-verified.
3. **2.3 Ticket-type grants — all verified persisted** (reopened Access Control after each
   record Save): Event(34), User Travel(40), Alert(21) = Cyber + SL Read and Modify;
   Action1(41) = Cyber + MT + SL (Ryan's note: MT can also edit — closes the Runbook 08
   routing question); Project(5), Project Task(20) = MT + Cyber + SL.
4. **2.4 Agents:** Kantor(28) duplicate DIRECT Cyber Ops (Analysts) team row (id 1206,
   no role_id) deleted via Departments & Teams edit; API-verified — only the two
   role-inherited rows (1209/1210) remain. Lister(19) "empty SSO claim" (F6) is a
   NON-ISSUE: logs in fine via M365 SSO (last login 08-13); per-agent AD/Azure fields
   (useadlogin=0, adconnection=-1, azure_connectionid=0) are identical across working
   agents — SSO is enforced at the instance auth method, not per-agent. Documented.

**New Halo facts (extend §7.1):**

- **Access Control dialog: the Add button COMMITS a row.** A row whose principal+level are
  filled but not yet Add-committed is DISCARDED by the dialog Save (confirmed on User
  Travel — first attempt saved zero rows). Full sequence per grant: pick type → pick
  principal → pick level → **Add** → repeat → dialog Save → **record Save** → reopen to verify.
- **Client Group Override on a role is a client picker**, despite the name — it restricts
  agent visibility per-client, and there is no client-group scoping option in the role form.
- Halo UI window zoom flips between two scales after dialog saves — re-screenshot before
  clicking toolbar buttons; coordinates are NOT stable across saves.
- Teams renamed since audit: MT teams now "Support (Mgmt)" / "Support (Sys Admins)".

**Wave 2 remaining:** 2.5 smoke tests (Lister: modify Event/Alert works, read Support works,
modify Support FAILS, contract read-only works, no quotations/CRM/SQL; Runbook 07/08 flows
run end to end), then 2-3 day soak (2.6). Wave 3 (Sales) after soak.

**Carry-forward flags:** Suppliers + Supplier Contracts noedit (now on BOTH MT-side and
Cyber roles); Client Group Override scoping mechanism absent (joins OI-2); agent 31
"Action1" still holds Administrator (was flagged for review before Wave 2 — still open,
raise with Ryan); agent 32 "Sara – Automated Analyst" unaudited.

### 11.14 Post-go-live incident 1: "Ready to invoice" re-assign failure (fixed 2026-08-23)

**Symptom:** SO "Ready to invoice" popup: "Unable to re-assign. The Agent or Team was
not found or did not have access to the $#request Type or Client."

**Facts found:** ALL sales-order "NEW ORDER | <SO#>" tickets are ticket type 5
(**Project**) — type 39 "New Order" has NEVER been used (0 tickets ever, API-verified).
This is systemic config, not a Kris one-off. The re-assign target is MegHan Soltis
(agent 15, invoicing) on the **Operations** role. Project (5)'s Access Control listed
MT/Cyber/SL only — Operations was missing because **roles created during the waves have
new GUIDs that appear in NO ticket-type ACL rows added before their creation**. This
class of gap applies to every wave-created role (Operations, Executive, Finance,
recreated Sales roles) on every ACL-restricted type.

**Fix:** added Role=Operations, Read and Modify to Access Control on **Project (5)**
and **Project Task (20)** (Add commits row → dialog Save → record Save → reopened and
verified). Contract Renewal (38) has an EMPTY ACL = unrestricted — no change needed;
empty list means no restriction, rows-present means allow-list.

**Open decisions:** (a) whether order tickets should switch to type 39 New Order
(process change — never used to date); (b) audit whether Executive/Finance roles need
ACL rows on any restricted types their members get assigned.

### 11.15 Post-go-live incident 2: SL cannot select supplier on quotes (fix applied 2026-08-23, pending retest)

**Correction first:** the 2026-08-21 "live SL levels" line above is WRONG about POs —
live value was **Read Only** (the wave target, applied correctly; no drift ever
existed). The R+M reading came from innerText label/value adjacency, which is
UNRELIABLE on the role Permissions panel — always pair label→value via DOM
(label.closest(div).parentElement, value follows label). Ryan's ruling stands as
"R+M is fine for SL POs".

**Hypothesis + fix:** Mike (SL) lost quote-line supplier selection when Wave 1 dropped
SL Purchase Orders R+M → Read Only (supplier-on-line feeds PO creation). SL Suppliers
Access Level is Read and Modify (noedit) — not the cause. Fix applied: SL Purchase
Orders Access Level → **Read and Modify** (edit mode, react-select, saved, verified in
view mode). **Pending Mike's retest.** If confirmed, note Sales Executive also carries
PO=Read Only from Wave 3 — same symptom will hit Schilling when quoting; same fix if
Ryan approves.

**Mac Chrome browser gotchas (new 2026-08-23):** screenshot coordinates do NOT map 1:1
to click coordinates on the Mac extension (scale drift ~1.1x) — a raw coordinate click
landed on an AI-settings radio (staged only, discarded by navigation). Use find→ref
clicks exclusively on Mac. Role/config pages can render menu-only innerText (~860
chars) while the record loads in a nested container — find/read_page still sees the
loaded content; re-navigate if truly stuck.

### 11.16 Post-go-live incident 3: Operations blocked sending invoice email — closed Opportunity ticket (fixed 2026-08-31)

**Symptom (Meghan, 2026-08-31 ~8:58 AM ET):** sending an invoice email from a sales order
popped "Unable to save data. You do not have permission to update this Ticket."

**Trace:** invoice 20205 (Staffco, 50% milestone, $4,050) created by Meghan at 8:57 off
**SO 4076** "PROPROSAL | EMTS, FISM and MDR Onboarding/Installation Services". The invoice's
linked ticket is the originating **Opportunity 50402** (type 6), which is **CLOSED**
(status 9 since 2026-07-21 — closed-won opportunities stay closed while invoicing happens
later). "Send invoice" logs an **Invoice Emailed action on that linked ticket**, and the
Operations role had `Can edit closed Tickets = No` (a Wave 4 reduction), so the action —
and the send — was refused.

**Why it worked before:** her 08-20 invoice send (inv 20204, Fairview) logged its Invoice
Emailed action on Opportunity 50588 while that ticket was OPEN ("With Distributor" — a
"PO Received" step had reopened it). Product-only orders often reopen the opportunity via
goods-receipt steps; services-only orders like SO 4076 never do, so the closed-ticket wall
only shows up on those. NOT an ACL problem: Opportunity(6) modify was already proven for
Operations by the 08-20 send.

**Fix (approved by Ryan in advance):** Operations role → Tickets Permissions →
`Can edit closed Tickets: No → Yes`. Applied via Chrome, saved, **view-mode verified**.
Pre-change snapshot: `Operations_70222833_pre-closedticket-fix_2026-08-31.txt` (session
workspace). Operations role GUID `70222833-6e9f-4ebe-951a-c55f04d35fce`, id_int 22.

**Generalization:** any role that sends invoice/PO/quote emails needs closed-ticket edit,
because Halo writes those sends as actions on the linked (often closed) sales ticket.
Executive (Invoices R+M) and Finance may hit the same wall if they ever email invoices —
check `Can edit closed Tickets` on those roles if the symptom recurs there. Line roles
(Cyber/MT) keep No by design.

**Diagnostic shortcut for next time:** invoice → `salesorder_id`/`ticket_id` via
`/api/Invoice`; the linked ticket's `status_id`/`dateclosed` via `/api/Tickets/<id>`; the
role's ticket permissions in view mode at `/config/agents/roles?id=<GUID>`. The Invoice
Emailed action lands on the SO's originating ticket (`salesorder.ticket_id`), not the
"NEW ORDER |" communication ticket.

### 11.17 Post-go-live incident 4: Operations "Ticket not found" on invoice send — department visibility (fixed 2026-09-01)

**Symptom (Meghan, 2026-09-01 ~4 PM ET):** sending invoice 20236 (Cleveland Museum of
Natural History, S1 onboarding) from **SO 4107** popped "Unable to save data. Ticket not
found." Clicking the SO's "Ticket ID" link said she had no permission to view. Logout /
fresh window did not help. Different error text from 11.16 (that one said "no permission to
update"; this one says "not found").

**Trace:** SO 4107 `ticket_id` = **Opportunity 50889** (type 6, closed status 9) — but its
team is **Cyber Ops (Analysts)** (team 17) → department **Simvay - Cybersecurity** (dept 10).
Meghan's Operations role carried department membership for MT (3), Projects (9) and Sales (8)
only. Halo scopes ticket *visibility* by department/team membership, so a ticket in a
department the agent is not in is simply "not found" — the Invoice Emailed action write
then fails. Yesterday's 50402 was in Sales Team (dept 8), which is why the 11.16 fix worked
there and not here. Role Permissions, ticket-type ACL and Client restrictions were all
checked in view mode first and are NOT the cause.

**Fix (approved by Ryan):** Operations role → **Departments & Teams tab** → Departments →
Add → `Simvay - Cybersecurity`, membership **Modify All** (matches the other three rows) →
dialog Save → record Save. API-verified: `Agent/15?includedetails=true` now shows a 4th
`departments[]` row (id 274, dept 10, role Operations, membershiplevel 2). Halo notes agents
may need to log out/in for department changes to apply — tell Meghan to do that before retry.

**New Halo facts (extend §7.1):**

- **Department/team membership for a role-holder lives on the ROLE** (Roles → Departments &
  Teams), not the agent. The agent record's Departments & Teams tab shows them read-only with
  "Inherited from Role". Edit the role.
- **Department membership levels:** Basic Member / View All / Modify All / Department Manager.
  Department membership is the ticket-VISIBILITY layer; role Permissions + type ACL are the
  modify layers. "Ticket not found" = visibility (department/team); "no permission to update"
  = closed-ticket or ACL.
- **Agent record toolbar has an "Impersonate Agent" button** (Config → Teams & Agents →
  Agents → open agent). Not used this time; available for future permission repros.
- Agents config list URL `/config/agents/agents?id=<n>` loads the LIST, not the record — click
  the row (URL becomes `...&agentid=<n>`).

**Generalization:** any wave-created role (Operations, Executive, Finance) whose members
handle invoicing/POs across BOTH business units needs department rows for **all four**
departments (MT 3, Sales 8, Projects 9, Cybersecurity 10). Opportunities are routinely
assigned to Cyber Ops (Analysts) even though that team has `foropps=false`. Check Executive
and Finance role department rows before they hit the same wall.

**Diagnostic shortcut:** SO → `ticket_id` → `Tickets/<id>` → `team_id`/`department_id` →
compare with `Agent/<n>?includedetails=true` `departments[]`. Whole trace is API-only.
