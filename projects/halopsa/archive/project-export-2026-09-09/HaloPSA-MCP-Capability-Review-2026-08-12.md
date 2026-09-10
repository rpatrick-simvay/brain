# HaloPSA MCP Connector — Capability Gap Review (2026-08-12)

> **DISPOSITION (same day):** Ryan approved gaps **1, 2, 3, 5, 9** — all shipped in
> **worker v1.2.0** (22 tools, 52/52 harness checks) together with the v1.1.0
> invoice/sales-order work. Still open: recurring invoices (#6), timesheets (#7),
> KB dedicated tool (#8) — all low priority. §3 statuses updated inline.
>
> **SMOKE TESTS PASSED (2026-08-12, post-deploy):** every new endpoint verified live —
> quotes (208, `po_ref` = reference, ticket_id/search filters work), SOs (95, client_id
> works), POs (113), contracts, attachments (returns ~4-min CDN link, not base64),
> workflows (8 active, id 18 = Cybersecurity Operations). One defect: Halo silently
> ignores `open_only` on SO/PO lists → **v1.2.1 patch** (param removed, attachment
> description corrected) is on disk awaiting one dashboard paste. Full verified facts:
> Runbook 01 §2.1–§2.2.

**Context:** The `halopsa` worker (SARA, non-OAuth admin connector) was written from scratch —
there is no upstream "original" repo it was forked from. The only GitHub reference on record is
our own `github.com/rpatrick-simvay/mcp-workers`. This review therefore compares v1.1.0 against
(a) the public HaloPSA MCP servers on GitHub and (b) the HaloPSA REST API surface itself, per
Ryan's direction to "review all sources and choose the best build options."

## 1. What shipped in v1.1.0 (today)

New tools: `get_invoices`, `get_invoice`, `get_sales_orders`, `get_sales_order`.
`salesorder` added to the `halo_get` allowlist (invoice was already allowlisted).
Also: retry on 429/5xx honoring `Retry-After` (README claimed this shared trait; the halopsa
worker never had it), and a new offline `test-harness.mjs` (README claimed one existed; it didn't).
35/35 checks pass. Instructions string now mentions invoices + sales orders.

Verified live before building: `Invoice` list accepts `pageinate/page_size/page_no`,
`client_id`, `ticket_id`, and `search`. `SalesOrder` could not be verified live (it was not
allowlisted pre-update) — **post-deploy smoke test required** (§4).

## 2. Public HaloPSA MCP servers surveyed

| Project | Tools | Verdict for us |
|---|---|---|
| [wyre-technology/halopsa-mcp](https://github.com/wyre-technology/halopsa-mcp) | Tickets (R/W), Clients (R/W), Assets (R), Agents+Teams (R), Invoices (R). Hierarchical/lazy tool loading, built-in throttling for Halo's 500-req/3-min limit. | Only feature we lacked was invoices — **closed today**. Its writes conflict with our read-only-by-design admin tier. Its rate-limit throttling idea is partially adopted (retry w/ Retry-After). |
| [ssmanji89/halopsa-workflows-mcp](https://github.com/ssmanji89/halopsa-workflows-mcp) | getWorkflows / getWorkflowSteps / getWorkflow / createWorkflows / deleteWorkflow / healthcheck | Workflow **config** CRUD. Low value for daily ops; workflow deletes are dangerous. Skip. |
| [adamhancock/mcp](https://github.com/adamhancock/mcp) | Multi-server collection | Nothing distinctive confirmed for HaloPSA. Skip. |
| [tim-impendingtech/halopsa-mcp-server](https://lobehub.com/mcp/tim-impendingtech-halopsa-mcp-server) | Listing page returned 403 — not reviewed | Revisit only if something specific is wanted. |

**Conclusion:** no public server offers a read capability we still lack. The remaining gaps are
against the **HaloPSA API itself**.

## 3. Gap list — review candidates for the next update

Read-only candidates, ranked. None are included in v1.1.0; Ryan picks.

| # | Capability | Halo endpoint | Value | Status / Notes |
|---|---|---|---|---|
| 1 | **Quotations** | `Quotation` | **High** | ✅ **SHIPPED v1.2.0** — `get_quotes` / `get_quote` + `quotation` allowlisted. List params unverified pre-deploy — smoke test. |
| 2 | **Purchase orders** | `PurchaseOrder` | Medium-high | ✅ **SHIPPED v1.2.0** — `get_purchase_orders` / `get_purchase_order` + allowlist. Smoke test post-deploy. |
| 3 | **Contracts dedicated tool** | `ClientContract` | Medium | ✅ **SHIPPED v1.2.0** — `get_contracts` / `get_contract`. `pageinate` + `client_id` verified live 2026-08-12. |
| 4 | **Users/contacts dedicated tool** | `Users` | Medium | Declined for now — already allowlisted; `halo_get` suffices. |
| 5 | **Attachments (read)** | `Attachment` | Medium | ✅ **SHIPPED v1.2.0** — `get_attachments` (ticket_id required) / `get_attachment`. Base64 content rides the 500k truncation cap. Unverified pre-deploy — smoke test. |
| 6 | **Recurring invoices** | `RecurringInvoice` | Low-medium | Open. Renewal/billing forecasting; `get_invoices` already shows generated instances. |
| 7 | **Timesheets/time entries** | `TimesheetEvent` | Low | Open. Billed-hours questions are already answered better by report 290 (Runbook 10). |
| 8 | **KB articles dedicated tool** | `KBArticle` | Low | Open. Allowlisted already; `halo_get` suffices. |
| 9 | Workflow config reads | `Workflows` | Low | ✅ **SHIPPED v1.2.0** — `get_workflows` (list, or one by id with steps); both `workflow` and `workflows` allowlisted to hedge the endpoint name. Unverified pre-deploy — smoke test. |
| — | Opportunities | — | n/a | Already covered — opportunities are tickets (Sales area 13) via `get_tickets`. |
| — | Any writes | — | Out of scope | Read-only is this worker's security posture. Writes belong to the halopsa-oauth M3 roadmap (Runbook 09). |

## 4. Follow-ups created by this update

1. **Deploy v1.2.0** (Ryan, dashboard-paste worker): run `node HaloPSA/test-harness.mjs`
   (52/52 expected), paste `worker.js` into Cloudflare dashboard → Deploy, then
   `git add/commit/push` (files are on disk at `E:\Projects\MCP\HaloPSA\`, not yet committed).
2. **Post-deploy smoke test** (endpoints that couldn't be verified pre-deploy):
   `get_sales_orders {client_id: 45}` → `get_sales_order {id: 4102}`;
   `get_quotes {ticket_id: 51414}` → `get_quote {id: 10204}` (Thogus);
   `get_purchase_orders {}` → `get_purchase_order {id: 2102}`;
   `get_attachments {ticket_id: <any ticket with files>}`; `get_workflows {}` and
   `get_workflows {id: 18}` (SOC Event workflow). Confirm filter params (`open_only`,
   `search`) are honored rather than silently ignored — trim tool descriptions if not.
3. **Parity drift:** `halopsa-oauth/src/mcp.js` documents "tool parity with admin worker + whoami"
   (Runbook 09). It now lags by 13 tools — port when convenient.
4. **README drift fixed/remaining:** harness now actually exists; README's "retries on 429/5xx"
   claim is now true for halopsa too. README table row for halopsa should add invoices + sales
   orders to its scope description.
