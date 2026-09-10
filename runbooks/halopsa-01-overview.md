---
title: "HaloPSA 01: Overview and core workflows"
type: runbook
updated: 2026-08-12
tags: [halopsa, quotes, pdf-templates, mcp-connector]
related: [projects/halopsa/STATUS]
source: "HaloPSA Claude Project: HaloPSA-Runbook-01-Overview.md"
migrated: 2026-09-09
---
> Migrated 2026-09-09 from the HaloPSA Claude Project (`HaloPSA-Runbook-01-Overview.md`). This file is now the canonical copy; the project doc is frozen. The verbatim original is in `projects/halopsa/archive/project-export-2026-09-09/`. Em and en dashes in prose were replaced per CLAUDE.md; code blocks are untouched. Cross-references were rewritten to brain paths.

# Simvay HaloPSA - Master Runbook (01: Overview & Core Workflows)

> **Purpose:** A reference guide to Simvay's HaloPSA environment for future Claude
> sessions. Covers what can be done through the **read-only HaloPSA MCP connector**
> versus the **Chrome browser UI**, plus the concrete workflows, URLs, gotchas, and
> techniques discovered while building the branded quotation proposal template.
>
> **How to use this:** This file lives in the brain repo (`C:\Dev\Brain`, `runbooks/`).
> Since 2026-09-09 the brain is canonical; the "HaloPSA" Claude Project copy is frozen.
> This is runbook **#01 (overview)** - add more focused runbooks to `runbooks/` as
> new workflows are learned (see "Adding more runbooks" at the end), and update
> `projects/halopsa/STATUS.md`, `DECISIONS.md` and `LOG.md` per `CLAUDE.md`.
>
> **Instance:** `https://simvay.halopsa.com`
> **Last updated:** 2026-08-12 (§2 - worker v1.2.0 DEPLOYED & smoke-tested: 22 tools
> covering invoices, sales orders, quotations, purchase orders, contracts, attachments,
> workflows. v1.2.1 patch on disk pending paste. All endpoints verified live - see §2.2)

---

## ⚙️ Standing instruction: keep this knowledge alive

**This is a living knowledge base. Every future Claude session working in HaloPSA must feed
what it learns back in - this is part of the job, not an optional extra.**

Whenever you discover something new about HaloPSA (a new URL, a variable, a gotcha, a
working technique, a config location, an API quirk), **before ending the task**:

1. **Small addition** → write it back into the relevant section of the appropriate runbook
   in `runbooks/` (and bump that file's "Last updated" date and frontmatter `updated`).
2. **New area/workflow** → create a **new focused runbook** (`runbooks/halopsa-NN-<slug>.md`,
   same frontmatter) and add it to the index in §9 and to `projects/halopsa/BRIEF.md`.
3. If you corrected something that turned out to be wrong here, **fix it in place** so the
   record stays trustworthy.

The goal is that the environment gets *easier* to work in over time and no discovery is ever
re-learned from scratch. Treat "update the runbook" as a required closing step of any
HaloPSA task, the same way you'd verify your work.

> **A caution learned 2026-08-04:** a single observation was written up here as a general rule
> ("*Default Template* = the navy built-in"), and that wrong rule then propagated into a second
> runbook and shaped how three quotes were built. **Record what you observed and the conditions
> you observed it under.** If you infer a general rule, say so and say how you'd disprove it.

---

## 1. Environment at a glance

Simvay is an MSP/MSSP running **HaloPSA** as its PSA platform. HaloPSA holds tickets,
clients, sites, assets, agents, contracts, invoices, quotations, and the reporting layer.
Simvay uses it (among other things) for:

- **Sales pipeline** - Opportunities (Sales area 13) stepped through the *Opportunity
  Management* workflow, with quotes raised **from** the opportunity. Creating an opportunity
  and raising its quote is **Runbook 11**.
- **Quotations / proposals** - customer-facing quotes with a branded PDF template
  ("Simvay Proposal"). Building quote content (lines, groups, recurring items) is
  **Runbook 02**.
- **Financials / reporting** - revenue by category (Cybersecurity vs Managed Technology),
  recurring vs one-time, gross profit. (See the `simvay-monthly-sales-report` skill, which
  pulls these from HaloPSA.) Building/editing saved reports is **Runbook 10**.
- **Tickets / SOC operations**, assets, contracts, etc.

There are **two ways to interact with HaloPSA**, with very different capabilities:

| Method | Access | Good for | Cannot do |
|---|---|---|---|
| **HaloPSA MCP connector** | Read-only (GET only) | Fast structured reads of tickets, clients, assets, agents, items, contracts, reports, invoices, sales orders, quotations, POs, attachments, workflows (v1.2.0+) | Any write; anything outside the allowlisted endpoints (e.g. config, PDF templates) |
| **Chrome browser UI** | Full (whatever the logged-in agent can do) | Config, PDF templates, creating opportunities, editing quotes, custom fields, generating PDFs, anything the connector can't reach | Nothing inherently - but writes are slower and more fragile; respect the safety rules |

**Rule of thumb:** Reach for the **connector first** for read-only lookups (it's fast and
clean). Fall back to **Chrome** for configuration, edits, opportunities, quotations, and PDF
work. **For PDF-template read/create/update specifically, use the in-page Halo REST API
technique (Runbook 05 §3) - it replaces the fragile config-UI modal flow entirely.**

---

## 2. HaloPSA MCP connector (read-only)

The connector is **strictly read-only - every operation is a GET**. Nothing can be
modified through it. Server description (v1.2.0): *"Read-only access to Simvay's HaloPSA
instance (tickets, clients, assets, agents, invoices, sales orders, quotations, purchase
orders, contracts, attachments, workflows, saved reports). All operations are GET-only;
nothing can be modified through this connector."*

### 2.1 Dedicated tools

- `mcp__HaloPSA__get_agents`
- `mcp__HaloPSA__get_assets`
- `mcp__HaloPSA__get_clients`
- `mcp__HaloPSA__get_ticket`
- `mcp__HaloPSA__get_ticket_actions`
- `mcp__HaloPSA__get_tickets`
- `mcp__HaloPSA__list_reports`
- `mcp__HaloPSA__run_report`
- `mcp__HaloPSA__get_invoices` - **new in v1.1.0** - list/search invoices; filters
  `client_id`, `ticket_id`, `search` (all verified live 2026-08-12); headers only.
- `mcp__HaloPSA__get_invoice` - **new in v1.1.0** - one invoice by internal `id` (NOT the
  invoice number) with `includedetails=true` (line items).
- `mcp__HaloPSA__get_sales_orders` - **new in v1.1.0** - list/search sales orders; filters
  `client_id` (verified), `search`. **No server-side open/closed filter exists** - Halo
  silently ignores `open_only` (removed in v1.2.1); filter on `status` client-side.
- `mcp__HaloPSA__get_sales_order` - **new in v1.1.0** - one sales order by `id` with lines
  (verified on 4102 - ~60k chars, overflows to a file, see §2.5).
- `mcp__HaloPSA__get_quotes` / `get_quote` - **new in v1.2.0** - quotations at last (was the
  connector's known blind spot). List filters all verified live: `client_id`, `ticket_id`
  (exact - 51414 → quote 10204 only), `search` (matches client name - "Thogus" → both Thogus
  quotes). **The quote reference (51414-1) lives in the `po_ref` field**; `get_quote` takes
  the INTERNAL `id` (10204). Headers include `cost`/`profit`/`revenue`/`pdftemplate_id`.
  Details include `lines` (12 on 10204; ~75k chars → file).
- `mcp__HaloPSA__get_purchase_orders` / `get_purchase_order` - **new in v1.2.0** - completes
  the SO→PO→Invoice chain (verified: 113 POs; headers carry `supplier_name`,
  `salesorder_id`, `po_ref` like `R50086-1`). Detail payload is HUGE - embeds the full
  supplier record AND the parent sales order with its lines; always overflows to a file.
  Like SOs, no server-side open/closed filter.
- `mcp__HaloPSA__get_contracts` / `get_contract` - **new in v1.2.0** - dedicated contract
  tools (`pageinate` + `client_id` verified live 2026-08-12); `include_inactive` /
  `include_expired` flags, page_size up to 500.
- `mcp__HaloPSA__get_attachments` / `get_attachment` - **new in v1.2.0** - list a ticket's
  attachments / fetch one. **`get_attachment` returns a time-limited CDN link (~4-min
  expiry), NOT base64** - fetch promptly, re-call for a fresh link. List metadata includes
  `type` (54=invoice PDF, 50=quote PDF, 58=signature image, 0=manual upload) and
  `unique_id` = the source entity id (e.g. invoice 20194, quote 10228). Verified on ticket
  51606 (6 attachments).
- `mcp__HaloPSA__get_workflows` - **new in v1.2.0** - workflow config reads; no args = list
  (bare array - Simvay has 8 active: 3 Change Mgmt, 5 Problem Mgmt, 6 Quick Quote,
  11 MT-Legacy, 12 Lead Mgmt, 14 Opportunity Mgmt, **18 Cybersecurity Operations**,
  19 MT-Active); `{id: N}` = one workflow with steps, actions, and flow-chart JSON
  (verified on 18). Endpoint is `Workflow` (singular).
- `mcp__HaloPSA__halo_get` - generic escape hatch (see below)

> **Deploy status (2026-08-12): v1.2.0 LIVE and smoke-tested** - all new endpoints verified
> against production (see per-tool notes above and §2.2). A **v1.2.1 patch** is on disk at
> `E:\Projects\MCP\HaloPSA\` awaiting one more dashboard paste: removes the `open_only`
> param Halo silently ignores (SO + PO) and corrects the attachment-tool description.
> Remember `git add/commit/push` after pasting - repo is source of truth.
>
> **Connector tool-cache gotcha (2026-08-12):** after a worker deploy, the Claude
> connector can keep serving the OLD tools/list - RefreshMcpTools showed 9 tools while
> tools/call was already running v1.2.0 code. `halo_get` reaches everything regardless;
> the dedicated tools appear after the connector reconnects (toggle it in Claude →
> Settings → Connectors if a session needs them immediately).
>
> Follow-up: `halopsa-oauth/src/mcp.js` documents "tool parity with admin worker" and now
> lags by 13 tools (Runbook 09). Remaining declined/low candidates in
> `projects/halopsa/archive/HaloPSA-MCP-Capability-Review-2026-08-12.md`.

### 2.2 `halo_get` escape hatch

Performs a read-only GET against any **allowlisted** HaloPSA API endpoint.

- `path` is relative to `/api`, e.g. `Tickets`, `Client/12`, `Asset/42`.
- `query` is an object of query parameters.

**Allowlisted endpoints only:** `tickets`, `actions`, `client`, `site`, `users`, `asset`,
`agent`, `team`, `report`, `invoice`, `clientcontract`, `kbarticle`, `status`, `priority`,
`sla`, `tickettype`, `appointment`, `projects`, `item`, `salesorder` (v1.1.0),
`quotation`, `purchaseorder`, `attachment`, `workflow`, `workflows` (v1.2.0).

**Useful reads verified 2026-07-17:** `Team` (departments + team ids), `TicketType`
(default team/agent/SLA/priority per type), `Status` (incl. stale-status automation
fields), `SLA` + `Priority` (response/fix targets), `Agent` with
`{"includeenabled":true,"includedisabled":true}` returns **disabled agents too**
(plain `get_agents` omits them - e.g. Brooke Fogarty, Vivan Rayborn).

**Also verified 2026-07-23:** `TicketType/N` with `{"includedetails":true}` returns the
full type config incl. the `fields` list (portal form fields), `workflow_id`,
`initial_status`, `statusafteruserupdate`, etc. Large payload - may persist to a file.
SLA ids: 1 Request SLA, 2 24 Hour, 3 4 Hour, 5 NO SLA.

**Also verified 2026-08-04:**
- `Item` with `{"search":"SIM-VULN","count":50}` returns full catalog records - `id`, `name`,
  `supplier_part_code` (the SKU), `baseprice`, `costprice`, `markupperc`, `isrecurringitem`,
  `item_default_billing_period`, `assetgroup_name`. **This is the fastest way to confirm SKUs
  and prices before building a quote**, and it cross-checks the QUOTER.xlsx sheet.
- `Users` with `{"client_id":N,"count":30}` returns a client's contacts (with `other2` =
  job title) - use it to pick the right end-user for a new opportunity.
- `ClientContract` with `{"count":500,"includeinactive":true,"includeexpired":true}` is the
  canonical source for contract **ref naming conventions** (e.g. `A1-MMDDYY-MMDDYY`).
- `Client/N` with `{"includedetails":true}` exposes the **PDF-template and tax overrides**:
  `overridepdftemplatequote` / `overridepdftemplateinvoice` (`-1` = no override) and
  `item_tax_code_name` / `service_tax_code_name` / `contract_tax_code_name` /
  `prepay_tax_code_name`. **Check these before diagnosing a "wrong template" or "wrong tax"
  problem** - e.g. City of Parma Heights (id 29) carries EXEMPT on all four tax codes and no
  template override.

**Also verified 2026-08-12 (while building v1.1.0):**
- `Invoice` list accepts `pageinate/page_size/page_no`, `client_id`, `ticket_id`, and
  `search` (search matches client name / reference). Returns `{record_count, invoices:[…]}`
  with rich headers: `invoicenumber`, `salesorder_id`, `ticket_id`, `contract_id`,
  `paymentstatus` (`-1` unpaid / `2` paid seen), `amountpaid`, `amountdue`, `total`,
  `duedate`, `datepaid`, `posted`, `voided`, `internal_note`, `status`. 162 invoices total
  at time of check. Invoice **internal `id` ≠ `typeid`**; `invoice_display` shows both.

**Also verified 2026-08-12 (v1.2.0 smoke tests against production):**
- `Quotation` list: `pageinate`, `client_id`, `ticket_id` (exact match), `search` (client
  name) all work; 208 quotes total. **Quote reference is the `po_ref` field** (10204 →
  `po_ref: "51414-1"`) - the id↔reference mapping that used to require Chrome (§4.1) is now
  a one-call connector lookup.
- `SalesOrder` list: `pageinate` + `client_id` work; 95 SOs total. **`open_only` is
  SILENTLY IGNORED** - same record_count either way. No open/closed server-side filter on
  `SalesOrder` or `PurchaseOrder`; filter on `status` client-side.
- `PurchaseOrder` list: 113 POs; headers carry `supplier_name`, `salesorder_id`, `po_ref`.
- `Attachment` with `{"ticket_id":N}` lists metadata (`type`, `unique_id`, `filesize`,
  `desc`, sometimes `s3url`). `Attachment/N` with `{"includedetails":true}` returns
  **`{link: <CDN URL>}` with ~4-minute expiry** - not base64 content.
- `Workflow` (singular) lists workflow defs as a bare array; `Workflow/N` +
  `includedetails` returns steps/actions/flow-chart/access_control. Workflow 18
  (Cybersecurity Operations) steps: NEW → Operations/SRM → Resolved.

### 2.3 What the connector CANNOT reach (use Chrome)

- ~~Quotations~~ / ~~Purchase orders~~ - **covered from v1.2.0 onward** (`get_quotes`,
  `get_purchase_orders`; see §2.1). Historical note: pre-v1.2.0, quote lookups required the
  Chrome UI, which is why old runbook entries (e.g. finding quote 51414-1's internal id)
  describe browser navigation.
- **Config** (PDF templates, email templates, custom-field definitions, quotation settings,
  notification rules) - Chrome only.
- Any **write / edit / generate** action - Chrome only. **This includes creating
  opportunities** (Runbook 11).
- **Quirks seen 2026-07-16:** `get_clients`/`get_tickets` `search` params and `Tickets`
  filters (`client_id`, `tickettype_id`) returned 0 rows for Thogus; **prospects** don't
  appear in client lists. Find opportunities via the browser Sales Pipeline View instead.

### 2.4 Reporting

`list_reports` enumerates saved reports; `run_report` executes one. `halo_get` path
`Report/N` with `{"includedetails": true}` returns the full definition **including the
SQL** - the cheapest way to learn Halo's schema - and with `{"loadreport": true}` returns
the rows at `report.rows`. `$QUOTEID` can be used in report SQL for the Quotation ID.
The `simvay-monthly-sales-report` skill is the canonical example of driving HaloPSA
reporting for financials.

**Creating or editing a report is Chrome-only.** The report builder, the custom-SQL data
source, the verified table/column schema, the `reportingperiod` enum and the derived-table
`order by` trap are all in **Runbook 10**.

### 2.5 Large results always overflow - parse the file

Contracts, opp pages, full ticket details, item lists, **quote/SO/PO detail payloads**
(`get_quote` ~75k chars, `get_sales_order` ~60k, `get_purchase_order` even bigger - it
embeds the full supplier record and parent SO) and **Action1 `list_endpoints`** all
routinely exceed the inline token limit and get written to a file. **Never re-request them
inline.** Read the saved path from the tool result and parse it with Bash + `python3`
(`json.load`). This is the single most common time-waster in this environment.

---

## 3. Chrome browser UI - navigation & essentials

### 3.1 Login / instance

All UI lives under `https://simvay.halopsa.com`. Start a browser task by getting tab
context, then navigate. (See the `claude-in-chrome` tooling; batch clicks with
`browser_batch` for speed.) A window size of **1680×1100** avoids the collapsed-table
problem on quote line grids (Runbook 02 §8).

### 3.2 Left-sidebar navigation map

The far-left icon rail (top → bottom): **Technology Mgmt, Blended View, Cybersecurity,
Action1, Customers, Sales, Quotes & Orders, Contracts, Items, Invoices, Orders, Reporting,
Assets, Calendar, Knowledge Base**. The most-used for quoting work are **Sales** and
**Quotes & Orders**.

**Quotes & Orders** opens a secondary panel with:
- *Quotations:* Open Quotes, Closed Quotes, Requires Processing, Processed
- *Sales Orders:* Open/Closed Orders, Requires Ordering/Invoicing/Consigning/Action, Requires Recurring Invoice
- *Purchase Orders:* Open/Closed Orders, Ready For Purchasing

**Sales** (area 13) is where **Opportunities** live - Pipeline View kanban
(Qualification / Quoting / Deal Registration / Sent-Decision Pending / Won). Direct URL to an
opportunity: `/tickets?area=13&id=NNNNN`. **Creating one: Runbook 11 §4.**

### 3.3 Key URLs (bookmarks)

| Thing | URL |
|---|---|
| **Sales Pipeline View (opportunities kanban)** | `https://simvay.halopsa.com/tickets?area=13&mainview=myviews&viewid=4&selid=15&sellevel=1` |
| **New Opportunity form** | same URL + `&id=-1` (or toolbar **+ New → New Opportunity**) |
| **Quotation General Settings (incl. the global default PDF template)** | `https://simvay.halopsa.com/config/quotes/settings` - ⚠ **`/config/quotations` 404s**; the config-menu item is "Quotations" but the path is `/config/quotes` |
| PDF Templates config (Simvay Proposal, id=29) | `https://simvay.halopsa.com/config/reports/pdftemplates?type=50&id=29` |
| PDF Templates per family (Runbook 05): quotes `type=50`, SO `type=52`, PO `type=14`, invoices `type=54`, tickets `type=53` | `https://simvay.halopsa.com/config/reports/pdftemplates?type=NN` |
| **Reporting - report list / builder (Runbook 10)** | `https://simvay.halopsa.com/reports` (a group: `?mainview=reportgroup&selid=N&sellevel=1`; a report: `&id=N`). **`/reporting` 404s.** |
| Sales Orders config (default SO PDF template - auto-saves, no Save button) | `https://simvay.halopsa.com/config/salesorders` |
| Purchase Orders config (default PO PDF template - auto-saves) | `https://simvay.halopsa.com/config/purchaseorders` |
| Invoice PDF defaults (5 slots: Invoices / Ticket / Sales Order / Recurring / Credit Notes) | `https://simvay.halopsa.com/config/billing/invoicepdf` |
| Email Templates config (Runbook 03) | `https://simvay.halopsa.com/config/email/templates` (a specific template: `?id=N`; custom templates: `?mg=-2`, negative ids) |
| **Self Service Portal config (Runbook 06)** | `https://simvay.halopsa.com/config/selfservice` (portal branding, theme, color, menu tiles). Portal **Custom CSS** = `/config/email/templates?portalcss=true` (record id 707) |
| Notifications config (Runbook 04) | `https://simvay.halopsa.com/config/notifications/notifications` (`?id=N` per rule); General Settings: `/config/notifications/settings` (**`/general` 404s**) |
| Quotations list (Open Quotes) | `https://simvay.halopsa.com/orders?mainview=quotes&selid=1&sellevel=1` |
| A specific quote (example: Thogus 51414-1) | `https://simvay.halopsa.com/orders?mainview=quotes&selid=1&sellevel=1&quoteid=10204` |
| A sales order (example) | `https://simvay.halopsa.com/orders?mainview=salesorders&selid=1&sellevel=1&salesorderid=4087` |
| A purchase order (example) | `https://simvay.halopsa.com/orders?mainview=purchaseorders&selid=1&sellevel=1&purchaseorderid=2102` |
| An invoice (example) | `https://simvay.halopsa.com/invoices?mainview=invoices&selid=-1&sellevel=1&invoiceid=20155` |
| An opportunity (example: Thogus backup 51420) | `https://simvay.halopsa.com/tickets?area=13&id=51420` |
| An item (example: BaaS C2 add-on) | `https://simvay.halopsa.com/items?itemid=455` |

> Note: `/quotations` alone 404s - use the `/orders?mainview=quotes...` pattern or the
> Quotes & Orders nav. Similarly `/config/email/emailtemplates` 404s - it's
> `/config/email/templates`. And `/config/branding` 404s - portal branding is under
> `/config/selfservice` (Runbook 06).

### 3.4 The `javascript_tool` content filter (important gotcha)

The Chrome `javascript_tool` **blocks tool RETURN values** that contain raw HTML, base64,
or hex (you'll see `[BLOCKED: Cookie/query string data]` or `[BLOCKED: Base64 encoded
data]`). Workarounds:

- Return only **small JSON** (booleans, numbers, short strings/snippets) from
  `javascript_tool` - e.g. `{found:true, len:11780, hasV37:true}`.
- To *view* large HTML, render it into an on-screen `<pre>` overlay and **screenshot** it
  (images bypass the filter).
- To *inspect* large HTML without viewing it, strip it in-page: regex out tags and return
  text-only summaries, or DOMParser it and return a tag/class skeleton (Runbook 05 §4).

Separately, the Claude Chrome **safety classifier** blocks wrapping `fetch` /
`XMLHttpRequest.setRequestHeader` to capture the app's Authorization token. Where a
runbook describes that technique (Runbook 05 §3), expect it to be refused and fall back
to the supported UI flow.

---

## 4. Workflow: Quotations

> Creating the **Opportunity** and raising its quote is **Runbook 11**.
> Building quote CONTENT (lines, pricing, groups, recurring items, tax, leasing) is covered in
> depth in **Runbook 02**.
>
> **Standing sales-process rule (Ryan, 2026-08-04):** new deals must be **Opportunities
> stepped through the workflow**, with the quote **raised from the opportunity** - not
> standalone quotes created from the Quotes & Orders module.

### 4.1 Finding & opening a quote

Quotes & Orders → **Open Quotes** (or Closed/etc.). The list columns: Date, Reference, ID,
Status, Title, Expiry, amounts, Client/Site/User, Agent. Click a row to open it.

- **Reference** is the human quote number (e.g. `51414-1`).
- **ID** is the internal quote id used in the URL as `quoteid=` (e.g. reference 51414-1 →
  ID `10204`).
- **Ticket ID** (shown in the quote's right sidebar) is separate (e.g. `51414`).

Quotes attached to an **opportunity** also appear in the opportunity's right sidebar under
"Quotes, Orders & Invoices" as `Quotation NNNNN-1 (Draft)` - clicking that link is the
quickest way back into a quote you just raised.

**Worked example:** Quote **51414-1** = quoteid **10204**, client **Thogus**, site Main,
agent Ryan Patrick, status **Draft**.

**Search:** the search box above the Quotations nav finds quotes by client name (e.g.
"brooklyn") - type and press Return (verified 2026-07-27; found Kris's City of Brooklyn
"Rec Renovation" quote 50476-1 (1) (1) = quoteid 10222).

### 4.2 Quote screen anatomy

Top toolbar (view mode): **Edit, Preview Print, Generate PDF, Create Sales Order, Clone,
Revise, Edit Columns, Bundle View, Add Note, Delete**. Tabs: **Quotation, Change History,
Internal Notes, Custom Fields, Attachments**. Right sidebar: End-User details, Client, Site,
Address, Quotation details (Reference, Ticket ID, Status, Date, Expiry Date), Print Options,
Billing Account details, **Leasing**.

### 4.3 Generating / previewing the PDF

- **Generate PDF** builds a fresh PDF from the *current* template + quote data, saves it as
  an attachment, and opens it in a new browser tab. The URL is a time-limited
  `https://us-cdn.haloservicedesk.com/simvay/_s/Attachments/<hash>.pdf?...` link.
- **Preview Print** (quotes, SOs, POs, invoices) renders the document on screen WITHOUT
  saving an attachment - **prefer it for template verification**, and it is safe to run on
  another agent's quote because it changes nothing (Runbook 05 §5).

### 4.4 The per-quote PDF template field - how it actually works

**⚠ CORRECTED 2026-08-04. The previous text here was wrong and had propagated into Runbook 11.**

Each quote has its own PDF-template setting in **Edit → Print Options** (scroll the right
sidebar down in Edit mode). Options seen: **`*Default Template*`**, Formal Proposal, Formal
Proposal - Basic, Proposal - PDF Format, Proposal (Alternate Style), Quick Quote,
**Simvay Proposal**.

- **`*Default Template*` is an INHERIT POINTER to the org default** (same asterisk convention
  as `*Default (Sales Order Site)*` on a line's Delivery Site). **It is NOT the Halo navy
  built-in.** Since the org default is **Simvay Proposal** (§4.5), a quote left on
  `*Default Template*` renders fully branded.
- **Verified 2026-08-04:** quote **51625-1** (Staffco) sits on `*Default Template*` and its
  **Preview Print renders the Simvay Proposal** - teal hero band, SIMVAY wordmark, ONE-TIME
  COSTS table, gradient total bar. Quotes 51598-1 and 51514-1 are likewise on the inherit
  value. No client-level override exists (`Client/29 → overridepdftemplatequote: -1`).
- **New quotes raised from an opportunity come in on `*Default Template*` - that is normal and
  requires no fix.**
- **When to pin explicitly to *Simvay Proposal* anyway:** a quote on inherit will
  **retroactively change** if the org default is ever changed. Pin quotes that have been sent
  to a client so the document they received stays reproducible. Pinning is otherwise harmless.
- **Where the original wrong note came from:** a quote *did* once output the navy built-in
  (2026-07-16) - but that was **before** the org default had been configured. The observation
  was real; the general rule inferred from it was not.
- **Invoices are genuinely different** - `pdftemplate_id` is baked in at invoice creation, so
  changing the default only affects NEW invoices. Fix per-invoice via Edit → Print Options
  (Runbook 05 §2).

### 4.5 Global default quote template - already set

**Config → Quotations → General Settings**, URL **`https://simvay.halopsa.com/config/quotes/settings`**
(**`/config/quotations` 404s**). Scroll to the **PDF Templates** block →
**"Default PDF Template for Quotations"**.

**Current value (verified 2026-08-04): `Simvay Proposal`.** This is what makes every
`*Default Template*` quote render branded, and it applies to **all future quotes**
automatically. Nothing further is needed to "make it the default".

This page needs a **toolbar Save** if you change anything (it is not one of the auto-saving
config pages - see gotcha 12); reload to verify persistence.

### 4.6 SAFETY: never send quotes

**Leave quotes in Draft - never click Send.** Editing fields and regenerating PDFs is fine;
sending to the client is not. (Same rule for sending SOs/POs/invoices - preview freely,
never click Send.)

---

## 5. Workflow: Custom fields on quotations

### 5.1 Creating a custom field

**Config → Custom Objects → Custom Fields.** Filter **Entity = Quotation**, click **New**.

- Field Name is auto-prefixed **`CF`**.
- Type **"Memo"** = multiline text box.
- A **Tab** field is required (only option: "Custom Fields"); the field then appears on the
  quote under a new **"Custom Fields"** tab.
- Quotation custom fields are stored in **`QuotationHeader`**.

### 5.2 The "Deal Notes" field (live example)

- Label **Deal Notes**, variable **`$CFDealNotes`**, Type Memo, Entity Quotation,
  **id = 268**.
- Purpose: general deal terms (deposit, Net 30, S&H, RMA) that should **not** roll under the
  product/service line-item description. Rendered in the proposal PDF as a "Notes & Terms"
  block (see §6.7).
- On a quote, it's edited on the **Custom Fields** tab; the edit textarea DOM id is
  **`input-field-for-customfield_268`**.

### 5.3 Editing / clearing a custom-field value (framework-model gotcha)

Halo's quote form keeps its **own model separate from the DOM textarea**. Setting
`textarea.value` via JS (even with input/change events) may **not** persist through Save -
the framework can write its own model's old value back.

Reliable approaches:
1. **Real keyboard on a real selection:** focus the field, `setSelectionRange(0, len)` via
   JS, then send a **real Backspace** key event (not JS). This deletes through the input
   pipeline.
2. **Save-interceptor** (most robust - see §6.5): wrap `fetch`/`XHR.send`, parse the
   outgoing save body, walk it, and set the target field's value (e.g. any object with
   `id===268` → `value:''`, or any string containing a known signature substring).

After saving, **reload and re-open** to confirm the persisted value (the view can show a
stale value immediately post-save). An empty Memo field renders as **"Not set"** and the
Custom Fields tab dims.

---

## 6. Workflow: PDF proposal template ("Simvay Proposal", id=29)

This is the branded quotation proposal template. It is the most intricate workflow and has
its own hard-won techniques.

> **2026-07-20 update:** for template read/create/update, the in-page **pdftemplate API
> technique (Runbook 05 §3)** supersedes the UI modal + save-interceptor flow below. The
> UI flow is kept documented here because it's still how a human edits templates, and the
> save-interceptor pattern is still needed for OTHER Halo forms.

### 6.1 Where it lives

**Config → Reporting → PDF Templates**, URL
`.../config/reports/pdftemplates?type=50&id=29`.
Tabs: **Details / Appearance / Details Table / Pages**.

### 6.2 Editing the template HTML

1. Click **Edit** (toolbar).
2. Go to the **Pages** tab → there is one row, **"Proposal Details"** (sequence 1).
3. Hover the row to reveal the **pencil (edit) icon** on the right, click it. (The pencil
   only appears on hover - a batch click that fires before the hover state will miss it.)
4. The modal has three HTML textareas:

| Section (label) | Textarea DOM id | Holds |
|---|---|---|
| Core Template HTML | `input-field-for-mainhtml` | The whole document: `<html>`, `<style>`, hero band, tables, totals, signatures, notes, confidential line |
| Quotation Item Table Row HTML | `input-field-for-subhtml` | Per-line row markup (`<tr>…$DETAILSLINE…</tr>`) |
| Quotation Group Table Row HTML | `input-field-for-subhtml2` | Group/subheader row markup |

### 6.3 Save flow (order matters)

**Modal Save → Pages-panel Save → toolbar Save.** Skipping any of the three loses the edit.

### 6.4 The Halo PDF engine is Chromium-based

The renderer supports modern CSS/HTML: **linear-gradients, box-shadow, border-radius,
flexbox, `display:table`/`table-cell`, data-URI images, and pseudo-selectors/elements
including `:empty` and `::before`.** This is what makes the branded design (and the
hide-when-empty notes block) possible.

### 6.5 The save-interceptor technique (CRITICAL)

**Problem:** Setting a textarea's value via the native setter + input/change/blur events
does **not** persist through Halo's Save - the framework reads its own model, not the DOM.

**Solution:** Before saving, install wrappers on `window.fetch` and
`XMLHttpRequest.prototype.send` that `JSON.parse` the outgoing save body, deep-walk it, and
**replace the old template HTML string with the new one**. Then click through the save flow.

Skeleton (adapt the match condition & payload per task):

```js
(function(){
  window.__saveInfo = {fetch:0, xhr:0, mainrepl:0};
  var NEW = window.__newHtml;                       // the full new HTML you want saved
  function shouldReplace(s){
    return typeof s === 'string'
      && s.indexOf('brand-band') >= 0               // a stable marker in the template
      && (s.indexOf('<html') >= 0 || s.indexOf('notes-block') >= 0)
      && s.indexOf('SIMVAY-V37') < 0;               // sentinel: only the OLD payload matches
  }
  function walk(o){
    if (Array.isArray(o)) { for (var i=0;i<o.length;i++){
      if (shouldReplace(o[i])){o[i]=NEW; window.__saveInfo.mainrepl++;}
      else if (o[i] && typeof o[i]==='object') walk(o[i]); } }
    else if (o && typeof o==='object') { for (var k in o){
      if (shouldReplace(o[k])){o[k]=NEW; window.__saveInfo.mainrepl++;}
      else if (o[k] && typeof o[k]==='object') walk(o[k]); } }
  }
  function mutate(b){ try{ var j=JSON.parse(b); walk(j); return JSON.stringify(j);}catch(e){ return b; } }
  var of=window.fetch;
  window.fetch=function(u,opt){
    if(opt&&opt.body&&typeof opt.body==='string'&&opt.body.indexOf('brand-band')>=0){
      window.__saveInfo.fetch++; opt.body=mutate(opt.body); }
    return of.apply(this,arguments);
  };
  var os=window.XMLHttpRequest.prototype.send;
  window.XMLHttpRequest.prototype.send=function(body){
    if(body&&typeof body==='string'&&body.indexOf('brand-band')>=0){
      window.__saveInfo.xhr++; arguments[0]=mutate(body); return os.apply(this,arguments); }
    return os.apply(this,arguments);
  };
  return {installed:true};
})()
```

**Verification:** after the save, read `window.__saveInfo`. `mainrepl: 2` (two copies
replaced) indicates success - Halo sends the template HTML twice in the save body.

**Version sentinels:** embed a comment like `<!--SIMVAY-V39-->` in the HTML and bump it each
revision (`V31 … V39 …`). The interceptor keys on the **absence** of the new sentinel so it
only rewrites the *old* payload, never the already-updated one. To confirm a save truly
persisted, **reload the config page, reopen the modal, and check the sentinel** in the
textarea.

> **Caveat (Runbook 06, 2026-07-20):** the fetch/XHR save-interceptor is right for the
> textarea-based PDF/quote forms, but on the **Monaco**-based portal Custom CSS editor it is
> unnecessary (Monaco `setValue` already reaches the save payload) and a wrapped `fetch`
> there left the save stuck on a "Please wait…" spinner that never committed. Pick the method
> per form type - see Runbook 06 §2.1. The report builder's SQL editor is also Monaco -
> Runbook 10 §2.1.

**Save-scope gotcha:** bundling broken Appearance / HTML-footer changes into the same save
caused Halo to **reject/rollback the ENTIRE payload** (a whole version was lost this way).
Keep template-HTML saves isolated; don't combine them with the "Use HTML Footer" toggle
(which itself would not persist - see §6.8).

### 6.6 Halo `$`-variables (proposal template)

| Variable | Meaning |
|---|---|
| `$ORLOGOSRC` | Org logo source |
| `$ORNAME`, `$ORPHONE` | Org name / phone |
| `$QUOTEREF` | Quote reference (e.g. 51414-1) |
| `$QUOTEDATE`, `$QUOTEEXPIRY` | Quote date / expiry |
| `$QuoteTitle` | Quote title |
| `$QUOTEAGENT`, `$AGENTJOBTITLE` | Selling agent name / job title |
| `$USERNAME` | End-user (recipient) name |
| `$AREA`, `$INVOICEADDRESS1`, `$INVOICEADDRESS2`, `$INVOICEPOSTCODE` | Recipient address parts |
| `$DETAILSTABLEHEADER` | Line-items table header |
| `$QUOTELINESNONRECURRING` / `MONTHLY` / `QUARTERLY` / `ANNUAL` / `WEEKLY` / `TWOYEARLY` / `THREEYEARLY` | Line rows per billing period |
| `$QUOTESUBTOTAL*`, `$QUOTETAXTOTAL*` | Subtotal / tax (per period variants) |
| `$QUOTETOTAL*` | Grand total (incl. tax) |
| `$DETAILSLINE` | Single line row (used inside the row-template textareas) |
| `$NOTE` | Line-item note |
| `$QUOTENOTE` | Quote note from the sidebar Notes |
| `$CFDealNotes` | Custom "Deal Notes" field (see §5.2) |
| `$AGENTQUOTESIGNATURE`, `$QUOTESIGNATURE` | Signature graphics |
| `$QUOTEAPPROVALDATE`, `$USEROTHER2` | Approval date / misc user field |
| `$QUOTEID` | Quotation ID (usable in report SQL) |

**THREEYEARLY variants verified rendering 2026-07-27** (on City of Brooklyn quote 50476-1,
quoteid 10222): `$QUOTELINESTHREEYEARLY`, `$QUOTESUBTOTALTHREEYEARLY`,
`$QUOTETAXTOTALTHREEYEARLY`, `$QUOTETOTALTHREEYEARLY` all resolve with real values for
lines whose billing period is **3-Yearly**. The overall `$QUOTETOTAL` banner includes the
full 3-yearly amount once (verified: $15,039.61 one-time + $3,085.20 3-yearly =
$18,124.81 banner). TWOYEARLY variants added same day (V39) by the same pattern; their
conditional correctly hides the section on quotes with no 2-Yearly lines, but a live
render with actual 2-Yearly lines hasn't come up yet - spot-check the first quote that
uses one.

**ANNUAL variants verified rendering 2026-08-04** on the A1 renewal quotes (Yearly lines) -
"ANNUAL RECURRING COSTS" section with Subtotal / Tax / **Total per year**.

(Email templates share this `$`-variable engine - see Runbook 03 §5. Sales Order /
Purchase Order / Invoice variables are catalogued in **Runbook 05 §4**, including which
plausible-looking variables do NOT exist. Report SQL variables - `@startdate`, `@enddate`,
`$filters`, `$agentid` - are in **Runbook 10 §3.1**.)

### 6.7 Conditional billing-period blocks (and the custom-field limitation)

Parts of the template can be shown only for a given billing period:

```
<!--[MONTHLY]-->
  ...content shown only when the quote has Monthly lines...
[MONTHLY]-->
```

Other tokens: `[RECURRING]`, `[NONRECURRING]`, `[ANNUAL]`, `[MONTHLY]`, `[WEEKLY]`,
`[QUARTERLY]`, `[SIXMONTHLY]`, `[TWOYEARLY]`, `[THREEYEARLY]`, `[FOURYEARLY]`,
`[FIVEYEARLY]`. (`[THREEYEARLY]` verified rendering-when-present 2026-07-27;
`[TWOYEARLY]` verified hiding-when-absent same day.)

**Hard limitation:** these conditionals **only work for built-in billing-period fields, NOT
custom fields.** Wrapping a custom field (e.g. `$CFDealNotes`) in `<!--[X]-->…[X]-->` prints
the literal `[X]-->` marker as stray text in the PDF. **Use CSS instead** for custom fields
(see next).

**Parser note (2026-07-20):** the whole `<!--[X] … [X]-->` block is one HTML comment as far
as DOMParser is concerned - when slicing template HTML programmatically, extract these
sections with string indexOf, not DOM traversal (DOMParser silently drops them).

### 6.8 Hide-a-block-when-empty via pure CSS (the `$CFDealNotes` pattern)

To show a "Notes & Terms" box only when Deal Notes has content - without Halo conditionals:

- Put the field value **directly** in the box with **no whitespace** between tags so it's
  truly empty when the field is blank:
  `<div class="notes-block">$CFDealNotes</div>`
- Draw the heading with `::before` and hide the empty box with `:empty`:

```css
.notes-block{ /* box styles */ font-size:9px; line-height:14px; color:#2B3440; white-space:pre-wrap; }
.notes-block:empty{ display:none; }
.notes-block::before{ content:"Notes & Terms"; display:block; /* heading styles */ white-space:normal; }
```

Verified: with the field empty, Halo renders `<div class="notes-block"></div>`, `:empty`
matches, and the whole block (heading included - generated content doesn't affect `:empty`)
is hidden. With content, the heading + text render. `&` inside a CSS `content` string is
literal (it's inside `<style>`, which is raw text), so `content:"Notes & Terms"` is fine.

### 6.9 Appearance tab settings (as saved)

- Color `#00627b` (Simvay teal), **Portrait**, **Margin = 13** (mm ≈ 0.5").
- **Include Header = No**, **Include Footer = Yes**, **Use HTML Footer = No.**
- Footer Text (Centre) = `{page} of {total-pages}`; Footer Text (Right) = empty.
- **Gotcha:** the plain footer font isn't adjustable, and the **"Use HTML Footer" toggle
  would not persist** (body root was an array; the key wasn't found by the interceptor). So
  the confidential line was moved **into the template body** (a small `.confidential` line
  before `</body>`) rather than the Halo footer.

### 6.10 Current template state

The "Simvay Proposal" template is at **v3.9** (sentinel `<!--SIMVAY-V39-->`, saved
2026-07-27). It has: a teal
gradient hero band with a transparent-white "S" logo (data-URI) + "SIMVAY" wordmark +
address tagline; gradient table headers; rounded, zebra-striped tables; a gradient
grand-total bar (`$QUOTETOTAL`); table-based signature row (aligned via
`display:table`/`table-cell`); an in-body confidential line; and the hide-when-empty
Notes & Terms block (§6.8). The Quotation Group row is styled teal
(`background-color:#F0F7FA;color:#00627B;font-weight:600`).

Billing-period sections in document order: **One-Time (NONRECURRING) → Monthly →
Quarterly → Annual → 2-Year (TWOYEARLY, added V39) → 3-Year (THREEYEARLY, added V38) →
Weekly**, each a conditional block with its own styled table + Subtotal/Tax/Total. The
2-/3-Year sections are clones of the Annual block with `ANNUAL`→`TWOYEARLY`/`THREEYEARLY`
token/variable swaps, headings "2-Year Recurring Costs" / "3-Year Recurring Costs", and
total rows "Total per 2-year term" / "Total per 3-year term". They were added because
**lines with those billing periods previously rendered NOWHERE on the PDF** (Kris's City
of Brooklyn Rec Renovation quote surfaced the 3-Yearly case, 2026-07-27; 2-Year added for
completeness per Ryan). Remaining periods with no section (6-Monthly, 4/5-Yearly,
2-Monthly) - clone the same pattern if one ever shows up on a quote.

**Derived templates (2026-07-20, Runbook 05):** Simvay Sales Order (id 30, type 52),
Simvay Purchase Order (id 31, type 14), Simvay Invoice (id 32, type 54) - all cloned from
this design and set as defaults for their families. (They are quote-V37-era clones - the
2-/3-Year sections exist only in the quote template.)

---

## 7. Consolidated gotchas / lessons

1. **Connector is read-only** - GET only, limited allowlist; quotations & config aren't on
   it. Use Chrome for anything the connector can't reach.
2. **`javascript_tool` return filter** blocks HTML/base64/hex - return small JSON; screenshot
   overlays to view big HTML.
3. **JS-set form values don't persist** through Halo saves (framework model ≠ DOM). Use the
   save-interceptor, or a real keyboard selection+Backspace, then **reload to verify**.
   (Monaco editors are the exception - `setValue` reaches the payload; see Runbook 06 §2.1
   and Runbook 10 §2.1.)
4. **Save flow is multi-step** (modal → panel → toolbar) and **all-or-nothing** - a broken
   sub-change can roll back the whole payload. Keep saves isolated and use version sentinels.
5. **Hover-only icons** (the Pages-row edit pencil, quote-line pencils) - don't click before
   the hover state renders; take a screenshot first. On the quote lines grid the pencil sits
   just right of the Profit % column, ~x+20px from the row's right edge.
6. **`*Default Template*` on a quote means "inherit the org default" - it is NOT the navy
   built-in, and it is NOT a bug.** The org default is Simvay Proposal, so inherit renders
   branded (verified on quote 51625-1, 2026-08-04). Pin a quote to *Simvay Proposal*
   explicitly only when you want it insulated from a future change to the org default -
   e.g. quotes already sent to a client. **Invoices are the real trap** - they bake
   `pdftemplate_id` in at creation, so a default change only affects NEW invoices
   (Runbook 05 §2). Full evidence: §4.4 and Runbook 11 §10.
7. **Halo conditionals don't work for custom fields** - use CSS `:empty`/`::before` instead.
8. **Never send draft quotes** (safety) - regenerate/preview freely, but don't click Send.
   **Preview Print is safe on anyone's quote** - it saves nothing.
9. **PDF attachment URLs are time-limited** (`us-cdn.haloservicedesk.com/...?Expires=...`) -
   regenerate rather than relying on an old link.
10. **NEVER press Escape while a quote is in edit mode** - it closes the modal and silently
    discards every unsaved line edit. **Save first, always** (standing instruction from
    Ryan; full quote-edit lifecycle in Runbook 02 §1).
11. **SPA row tables (ReactTable) have no anchors** - to open a row via JS, dispatch
    `mousedown+mouseup+click` on a CELL (a bare `click()` on the row does nothing). See
    Runbook 04 §5 for the full row-walk recipe.
12. **Some config pages auto-save with NO Save button** (`/config/salesorders`,
    `/config/purchaseorders`, `/config/billing/invoicepdf`, `/config/selfservice`) while
    others (`/config/quotes/settings`) need a toolbar Save - verify persistence by reload
    either way. Template dropdowns on these pages cache their options: a just-created template
    only appears after a full page reload.
13. **The in-page Halo REST API beats the config UI for PDF templates** - capture the
    app's Authorization header (it re-sends on the ~30s `/api/OnlineStatus` poll), then
    GET/POST `/api/pdftemplate`. POST body is an ARRAY; omit `id` to create, include it to
    update. Full recipe: Runbook 05 §3. Full page navigations wipe the captured token.
    **⚠ 2026-08-02: the Claude Chrome safety classifier now BLOCKS wrapping
    `fetch`/`XHR.setRequestHeader` to capture that token.** Expect a refusal and use the
    supported UI flow instead - don't try to route around it.
14. **The first "Edit" click after navigating to a config record is swallowed** - click Edit,
    screenshot, and click again if not yet in edit mode (seen on the portal CSS record,
    Runbook 06 §2.1).
15. **Quote lines with a billing period that has no template section silently VANISH from
    the PDF** - no error, no box, totals for that period simply absent (though the grand
    `$QUOTETOTAL` banner still includes them). Seen 2026-07-27 with 3-Yearly Cisco lines on
    the City of Brooklyn quote; fixed by adding `[THREEYEARLY]` (V38) and `[TWOYEARLY]`
    (V39) sections (§6.10). If a client reports "items missing from the quote PDF", check
    the lines' billing period against the template's conditional blocks first.
16. **Custom report SQL cannot end in a bare `order by`** - Halo wraps it in a derived
    table, so you need `top 100 percent` on the outer select. This is why reports 203/233
    read `select distinct top 100 percent`. Runbook 10 §2.2.
17. **Long Halo config/report forms scroll under you as you type** - a value typed after a
    layout shift can land in a completely different field (a `10000` meant for Max Page
    Size ended up in *AI Prompt Override*, 2026-08-02). Screenshot and re-verify every
    field before saving.
18. **New Opportunity form defaults Ticket Type to `Lead`** - it must be switched to
    *Opportunity*, and **Existing Client** must be selected (Prospect is the default radio).
    The contact box searches **users, not clients** - type a surname. **Expected Close Date
    is mandatory.** Runbook 11 §4.
19. **Leasing is a QUOTE-level setting, not per-line** - the catalog-item line dialog has no
    "Is a Finance/Leased Item" field. Use right sidebar → **Leasing → Is Leased?**, which
    reveals *Term Limit (In Months)*. Runbook 02 §2/§7, Runbook 11 §6.3.
20. **Only ~one browser-driving subagent can run at a time.** Two concurrent Chrome subagents
    were dispatched 2026-08-04; the second could not hold a tab - it created 9+ tabs and each
    was pruned within 1-2 round trips, the group always collapsing back to the first agent's
    tabs. Run browser subagents **sequentially**, or do the work in the main session. Always
    instruct them to report a blocker rather than improvise, and never to touch a tab they
    did not create.
21. **Tax code `Default` on a quote line is NOT "no tax"** - it resolves to the *client's*
    configured tax code. Check `halo_get Client/<id>` → `item_tax_code_name` /
    `service_tax_code_name` before assuming. Parma Heights (29) is EXEMPT on all four;
    Conveyer & Caster resolves to 8% (Cuyahoga). Runbook 02 §5.

---

## 8. Related Simvay skills that touch HaloPSA

These packaged skills already automate HaloPSA-adjacent work - check them before rebuilding:

- **`simvay-monthly-sales-report`** - branded monthly exec sales/financial PDF from HaloPSA
  (revenue by Cybersecurity vs Managed Technology, recurring vs one-time, gross profit).
  Reads saved reports 288 (line revenue), 168 (cost) and **290 (delivery hours by team -
  Runbook 10 §5)**.
- **`simvay-anvil-determinations`** / **`simvay-blacksmith-staging`** - compliance evidence
  → determinations → BlacksmithInfoSec staging (adjacent systems, not HaloPSA itself).
- **`simvay-qbr-decks`** - per-client SOC QBR decks from PagerDuty.
- **`simvay-brand-styling`** - the document brand system used by the weekly renewals report
  and any client-facing deliverable.

---

## 9. Runbook index / adding more runbooks

This is runbook **#01 (overview + core workflows)**. Per the **Standing instruction** at the
top of this file, updating these runbooks is a required closing step of every HaloPSA task -
write small discoveries back into the right section, and spin up a new focused runbook for a
new area.

**Existing runbooks:**

- **01 (this file)** - overview, connector vs Chrome, quotations basics, custom fields,
  PDF template techniques.
- **02 - `runbooks/halopsa-02-quotations-lines-groups.md`** - building quote content:
  ad-hoc lines & margin-driven pricing, recurring items (monthly/annual), groups/bundles,
  billing-term PDF sections, per-line tax codes (incl. the EXEMPT/public-sector rule),
  quote-level Leasing, the quote-edit save lifecycle (and the Escape trap). Worked examples:
  Thogus 51420-1, the A1 renewals.
- **03 - `runbooks/halopsa-03-email-templates.md`** - email templates: config URLs
  (`/config/email/templates?id=N`, custom via `?mg=-2`), full 95-template inventory
  (2026-07-16), quality assessment, email `$`-variables, and the client-facing redesign
  project state (teal identity, mockups v1, apply-with-sign-off pending).
- **04 - `runbooks/halopsa-04-notifications.md`** - agent notification rules: config
  URLs (`/config/notifications/notifications?id=N`, General Settings at
  `/config/notifications/settings`), the 25-rule inventory + id map (2026-07-17), Agent vs
  Team notification anatomy, ticket-type intake defaults that drive alerting (Support →
  Primary Agent!), the ReactTable row-walk technique, and audit limitations. Full findings
  in `projects/halopsa/archive/HaloPSA-Notifications-Audit-2026-07-17.md`.
- **05 - `runbooks/halopsa-05-pdf-templates-so-po-invoice.md`** - the Simvay-branded
  Sales Order (id 30), Purchase Order (id 31) and Invoice (id 32) PDF templates: template
  type numbers, defaults wiring (incl. the five invoice slots), the **pdftemplate API
  technique** (auth capture + GET/POST - now classifier-blocked, see gotcha 13), verified
  per-family `$`-variables (and the fakes that print literally), `$xxxLINES` styled-table
  pattern vs unstyled `$DETAILSTABLE`, per-invoice baked-in template ids, and the Preview
  Print verification workflow.
- **06 - `runbooks/halopsa-06-client-portal.md`** - the client-facing self-service
  portal (`/portal`): config at `/config/selfservice` (title, welcome message, theme, Portal
  Color, menu tiles incl. hiding/icon-color, home backgrounds), the portal **Custom CSS**
  record (id 707, Monaco editor at `/config/email/templates?portalcss=true`), the full DOM
  selector map, the reliable Monaco save recipe (no fetch-interceptor + the swallowed-Edit
  quirk), and the applied dark **glass** rebrand (teal + sky-blue, white logo via CSS filter,
  smaller tiles, dark footer). Portal color is #00627B; theme = Halo PSA Dark.
- **07 - `runbooks/halopsa-07-travel-notifications.md`** - the **User Travel**
  workflow (design approved 2026-07-23; Halo build pending): portal + email intake under the
  User Lifecycle tile, the new **Traveling** hold status (off-hold at return date = revert
  trigger), NO-SLA/Low defaults, minimal 3-field portal form, and the fully-managed-client
  Conditional Access branch - country-scoped travel exception group with **PIM auto-expiry**,
  laptop-full / phone-Outlook-MAM posture, per-tenant pre-stage checklist, and the SOC
  alert-triage "is this user traveling?" check.
- **08 - `runbooks/halopsa-08-action1-ticket-type-routing.md`** - Action1 RMM →
  HaloPSA ticket-type routing: the `Action1` ticket type, ticket rules R1-R4, the MT-support
  client routing list (rule 13) and its refresh procedure, the email-suppression checklist,
  and the prospect-not-in-picker gotcha.
- **09 - `runbooks/halopsa-09-claude-access-architecture.md`** - decision record +
  build tracker for employee Claude access: per-user OAuth passthrough MCP now (Halo
  Authorisation Code login type - availability verified 2026-07-30), SARA agent-in-the-middle
  later on the same data plane. Code: `github.com/rpatrick-simvay/mcp-workers`
  (`E:\Projects\MCP`); work tracked as GitHub Issues/Milestones M1-M4.
- **10 - `runbooks/halopsa-10-reporting-sql.md`** - reporting & custom SQL reports:
  the Chrome report builder (`/reports`, **not** `/reporting`), the
  `*Write a custom SQL Query*` data source + Monaco `setValue` recipe, the derived-table
  `order by` trap, the **verified schema** of `actions`/`faults`/`area`/`uname`/invoice
  tables (incl. `area.aarea = faults.areaint` and `uname.usection` = agent team), SQL
  variables, the `reportingperiod` enum, and the worked example **report 290 "Billed Hours
  by Team"** with its first-run figures and data-quality flags.
- **11 - `runbooks/halopsa-11-action1-renewal-quotes.md`** - **Action1 (A1)
  Vulnerability & Patch Management renewal quotes**, and the general
  **opportunity-first sales process**: sizing from the Action1 connector (endpoint pull,
  server/workstation split, +5% growth allowance, T1-T4 tier table), the `SIM-VULN` SKU set
  and its QUOTER.xlsx↔Halo discrepancies, the `A1-MMDDYY-MMDDYY` naming convention, the full
  New-Opportunity click path and its auto-advancing pipeline stages, raising the quote from
  the opportunity, the multi-row item picker, the EXEMPT/public-sector tax rule, quote-level
  leasing, a reusable browser-subagent brief, and **§10 the PDF-template inheritance
  investigation**. Worked examples: Parma Heights 51641-1, Conveyer & Caster 51642-1,
  Olmsted Township 51643-1 (2026-08-04).

- **12 - `runbooks/halopsa-12-scheduled-tasks-connector-binding.md`** - why custom
  MCP connectors (the Cloudflare Workers) were absent from scheduled sessions (root-caused
  2026-08-12: a task's connector set is captured at creation; the UI scheduling flow cannot
  capture custom connectors - create every scheduled task via `create_trigger` from a live
  session instead), the STEP ZERO not-bound-vs-cold-start check now in every recurring
  prompt, and the 2026-08-12 task-inventory rebuild (v3.4 / v2.2 / v4.1 / v3.1 trigger ids).

**Other project docs:** `runbooks/halopsa-weekly-renewals-deep-dive.md` (the weekly "Weekly | Renewals" report
spec and its standing ops context), `runbooks/halopsa-weekly-ops-retrospective.md`,
`projects/halopsa/archive/HaloPSA-MCP-Capability-Review-2026-08-12.md` (worker v1.1.0 gap review - ranked
next-update candidates + survey of public HaloPSA MCP servers).

**Future candidates:** Tickets/SOC (statuses, SLAs, teams), Contracts & Invoices
(recurring billing).

Keep each file focused, date-stamped, and cross-referenced. Update this overview's
"Environment at a glance" table when a new method or major workflow is added.
