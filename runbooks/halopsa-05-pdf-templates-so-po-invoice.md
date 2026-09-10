---
title: "HaloPSA 05: PDF templates for sales orders, purchase orders, invoices"
type: runbook
updated: 2026-07-20
tags: [halopsa, pdf-templates, branding]
related: [runbooks/halopsa-01-overview, projects/halopsa/STATUS]
source: "HaloPSA Claude Project: claude/HaloPSA-Runbook-05-PDF-Templates-SO-PO-Invoice.md"
migrated: 2026-09-09
---
> Migrated 2026-09-09 from the HaloPSA Claude Project (`HaloPSA-Runbook-05-PDF-Templates-SO-PO-Invoice.md`). This file is now the canonical copy; the project doc is frozen. The verbatim original is in `projects/halopsa/archive/project-export-2026-09-09/`. Em and en dashes in prose were replaced per CLAUDE.md; code blocks are untouched. Cross-references were rewritten to brain paths.

# Simvay HaloPSA - Runbook 05: PDF Templates for Sales Orders, Purchase Orders & Invoices

> **Purpose:** How the Simvay-branded PDF templates for Sales Orders, Purchase Orders and
> Invoices were built (2026-07-20) by cloning the "Simvay Proposal" quote template design,
> including the **pdftemplate API technique** that avoids the fragile config-UI save flow
> entirely. Companion to Runbook 01 §6 (the original proposal-template techniques).
>
> **Instance:** `https://simvay.halopsa.com`
> **Last updated:** 2026-07-20 (invoice Description-column fix: quote-era fixed column
> widths vs 5-column invoice tables; overrides must live in the LAST page's stylesheet)

---

## 1. Template registry (as of 2026-07-20)

PDF templates live at **Config → Reporting → PDF Templates** (`/config/reports/pdftemplates?type=NN`).
The `type` query param / API field selects the template family:

| type | Family | Templates (id:name) |
|---|---|---|
| 50 | Quotations | 10 Quick Quote, 11 Proposal (Alt), 19 Proposal PDF, 23 Formal Proposal, 28 Formal Basic, **29 Simvay Proposal** |
| 52 | Sales Orders | 4 Default Order Print Template, **30 Simvay Sales Order** |
| 14 | Purchase Orders | 2 Default PO Print Template, **31 Simvay Purchase Order** |
| 54 | Invoices | 6 Basic Invoice Pdf, 13 Invoice with Time Breakdown (rebranded), **32 Simvay Invoice** |
| 53 | Tickets | 12 Default Ticket Print, 27 Profitability Analysis |
| 55 | Contracts | 7 Agreement Overview |

Sentinels: `SIMVAY-SO-V2`, `SIMVAY-PO-V4`, `SIMVAY-INV-V4`, `SIMVAY-TB-V7` (template 13) -
quote template is `SIMVAY-V37`. Template 13's page 1 is kept a byte-copy of template 32's
page (sentinel aside) - when editing one, apply the identical change to the other and
re-verify parity.

## 2. Defaults wiring (all set 2026-07-20)

- **Sales Orders:** Config → Sales Orders → "Default PDF Template for Sales Orders" =
  **Simvay Sales Order** (`/config/salesorders`).
- **Purchase Orders:** Config → Purchase Orders → PDF Templates → "Default PDF Template for
  POs" = **Simvay Purchase Order** (`/config/purchaseorders`).
- **Invoices:** Config → Billing → PDF Templates (`/config/billing/invoicepdf`) has FIVE
  slots: **Invoices = Simvay Invoice**, **Sales Order Invoices = Simvay Invoice**,
  **Recurring Invoices = Simvay Invoice**, *Ticket Invoices = Invoice with Time Breakdown*
  (kept - it renders per-ticket time entries; now rebranded, see §6), *Credit Notes =
  Basic Invoice Pdf* (left as-is).
- **These config pages AUTO-SAVE on change - there is no Save button** (unlike the
  Quotations config page, which has a toolbar Save).
- **Gotcha (stale dropdown):** a template created mid-session does not appear in the
  default-template dropdowns until a full page reload of the config page.

### Per-record template override (same trap as quotes)

- **Invoices bake `pdftemplate_id` into the record at creation** - changing the global
  default does NOT restyle existing invoices; only new invoices pick it up. Per-invoice
  override: invoice → Edit → right sidebar **Print Options → PDF Template** → Save.
- POs also have a per-record **Print Options → PDF Template** (default "*Default
  Template*" resolves to the config default at print time). Sales orders resolve the
  default at print time too. Check Print Options first when the wrong template renders.

## 3. The pdftemplate API technique (STRONGLY PREFERRED over the config UI)

The config-UI modal flow (Pages tab → pencil → three textareas → triple-save + save
interceptor, Runbook 01 §6) is slow and fragile. The **Halo REST API does it in one call**
from the browser's page context, reusing the logged-in agent's bearer token:

1. **Capture the app's Authorization header** (the SPA keeps its token in memory, not
   localStorage). Install wrappers, then wait - the app POSTs `/api/OnlineStatus` roughly
   every 30s and the wrapper catches the header from that poll:
   ```js
   window.__cap = {auth:null};
   const of = window.fetch;
   window.fetch = function(u, opt){ try{ const h=(opt&&opt.headers)||{};
     const a=h.Authorization||h.authorization||(h.get?h.get('Authorization'):null);
     if(a) window.__cap.auth=a; }catch(e){} return of.apply(this,arguments); };
   const oo=XMLHttpRequest.prototype.open, os=XMLHttpRequest.prototype.setRequestHeader;
   XMLHttpRequest.prototype.open=function(m,u){this.__url=u;return oo.apply(this,arguments);};
   XMLHttpRequest.prototype.setRequestHeader=function(k,v){
     if(/^authorization$/i.test(k)) window.__cap.auth=v; return os.apply(this,arguments); };
   ```
   Then wait ~30-35s and check `!!window.__cap.auth`. **Full page navigations wipe the
   wrapper AND the captured token - capture again after any `navigate`.** (SPA route
   changes via in-app clicks preserve it.)
2. **Read:** `GET /api/pdftemplate?type=52` (list), `GET /api/pdftemplate/30` (full record
   incl. `pages[]` - each page has `mainhtml/subhtml/subhtml2` - and `detailcolumns`).
3. **Create:** `POST /api/pdftemplate` with body `[templateObject]` (array!), object cloned
   from an existing template, `id` deleted, `name`/`type`/`description`/`pages` replaced.
   Returns 201 + the created record. **Update:** same POST with `id` present.
4. Verify by GET and checking the sentinel comment.

Caveats: the `javascript_tool` return filter still blocks raw-HTML returns - return only
booleans/lengths/short flags. Keep all HTML in `window.__*` variables and assemble in-page.
The quote MCP connector cannot see any of this (no pdftemplate endpoint on its allowlist).
Bonus: `GET /api/report/157?includedetails=true&loadreport=true` returns a report's emitted
`report.table_html` - useful for inspecting what `$REPORTxxDATA` will inject.

### ⚠ Edit template HTML with STRING SURGERY, not DOM round-trips

**DOMParser round-trips corrupt Halo templates.** Two verified failure modes:

1. **Conditional blocks vanish:** `<!--[NONRECURRING]…[NONRECURRING]-->` sections are one
   big HTML comment - DOMParser keeps them as comment nodes only if you re-serialize the
   whole document, but slicing via `element.innerHTML` on containers drops them.
2. **Foster parenting moves variables out of tables:** a bare `$XXXLINES`/`$DETAILSTABLE`
   text node sitting directly inside a `<table>` element (valid in Halo templates - the
   variable expands to `<tr>` rows at render time) is HOISTED OUT of the table by the HTML
   parser. This silently broke template 13: `<table>$DETAILSTABLE</table>` became
   `$DETAILSTABLE<table></table>` after a DOM edit, and the invoice line items rendered as
   run-together text. Fix was string surgery to move the variable back inside:
   `replace(/\$DETAILSTABLE\s*(<table\b[^>]*>)\s*<\/table>/, '$1$DETAILSTABLE</table>')`.

Prefer `indexOf`/`slice`/`replace` on the raw `mainhtml` string. If DOM inspection is
needed (finding which element holds some text), parse a COPY for analysis only and apply
the actual change to the string.

### ⚠ Multi-page templates: ONE global stylesheet, and Preview Print lies

A template can have multiple `pages[]` (e.g. template 13: "Main Page" + "Time Breakdown",
each authored as a full `<html>` document, each rendering as its own PDF page).

1. **In the final PDF, ALL pages' `<style>` blocks apply to ALL pages** (the engine merges
   the page documents; CSS is global). Consequences, all hit on 2026-07-20:
   - A `body *{text-align:left !important}` added to page 2 broke page 1's right-aligned
     totals. Never use broad selectors in one page's CSS - scope with a page-specific
     class instead.
   - Conflicts between pages' `!important` rules resolve by normal cascade: **higher
     specificity wins; on a tie, the LATER page's rule wins.** The Simvay stylesheet's
     `.styled-table tbody td:nth-child(4/5/6){text-align:right !important}` (0,2,1 -
     written to beat detailcolumns' inline aligns for price columns) was silently
     right-aligning the report table's Note column; low-specificity overrides
     (`.styled-table td`, `td *`, even `html body table tbody tr td` - all !important)
     ALL LOSE to it. Fix: give page-2's tables their own class
     (`class="styled-table report-table"`) and override with ≥(0,2,x) selectors:
     `.report-table tbody tr td:nth-child(5){text-align:left !important}` etc.
   - **Equal-specificity overrides MUST live in the LAST page's `<style>`.** The
     `.invoice-table` width fix (§6 round 4) was correctly added to page 1 but had no
     effect: page 2's copy of the shared stylesheet still carried the old width rules
     and, being later in the merged document, won the tie. Rule of thumb: append fix
     blocks to EVERY page's stylesheet (keeps pages self-consistent) - the copy in the
     last page is the one that actually decides ties.
2. **The on-screen Preview Print mangles multi-page templates** - page 1 renders as
   unstyled plain text. The actual **Generate PDF output is correct**. Always verify
   multi-page templates via Generate PDF; don't chase "broken CSS" that only appears in
   the preview. Single-page templates preview accurately.
3. **Ground-truth markup inspection:** the on-screen preview renders in an IFRAME - from
   `javascript_tool`, walk `document.querySelector('iframe').contentDocument` to count
   real columns / read inline styles the engine emitted (return tag-skeletons and counts,
   never raw HTML). This settled the "is there a phantom 6th column?" question (no - the
   invoice table is a clean 5 columns with inline non-!important text-aligns from
   `detailcolumns`).

## 4. How the SO/PO/Invoice templates are composed

All three reuse the Simvay Proposal (id 29) building blocks, extracted by slicing its
`mainhtml` in-page: the `<html>`+`<style>` head, the hero band (retitled via
`.replace('>Proposal<', '>Sales Order<')` etc.), the one-time-costs section skeleton
(`h3.proposal-table-title` + `table.styled-table` + subtotal table), the gradient
grand-total bar, and the confidential tail (reworded per document). Custom middles: a
`meta-strip` with 3-4 `meta-cell`s, then section + totals + optional blocks. `subhtml` /
`subhtml2` (line/group row markup) are copied from template 29 verbatim.

**Column alignment/widths in `.styled-table` assume the QUOTE's 6-column layout** (SKU
first: `th:first-child{width:92px;max-width:92px}`, nth-child(3-6) fixed 34-72px, price
columns right-aligned by position). Any table with a different column set inherits the
wrong geometry - invoice tables are 5 columns with **Description first**, so Description
was crushed into the 92px SKU slot ("all squished", Ryan 2026-07-20). Scope exceptions
with an extra class:
- `report-table` - page-2 breakdown wrapper tables (alignment overrides, §6 round 3).
- `invoice-table` - the invoice items table (`class="styled-table invoice-table"`), with
  the `/* invoice column layout */` block: Description `width:52%` left, Quantity 60px
  center, Unit Price 70px right, Tax 60px right, Price 80px right, header
  `white-space:nowrap`, and nth-child(6) collapsed to 1px as belt-and-braces. Lives in
  template 32 AND both pages of template 13 (last-page copy decides ties, §3).

### Variables that WORK per family (verified by render)

- **Sales Order:** `$ORDERID` (order number), `$ORDERDATE`, `$ORDERPO` (customer PO number),
  `$ORDERLINES` (row markup via subhtml - use inside `table.styled-table` with
  `$DETAILSTABLEHEADER` in `<thead>`), `$ORDERSUBTOTAL`, `$ORDERTAXTOTAL`, `$ORDERTOTAL`,
  `$ORDERNOTE`, `$USERNAME`, `$AREA`, `$INVOICEADDRESS1/2`, `$INVOICEPOSTCODE`, `$ORNAME`,
  `$ORPHONE`. **Do NOT use:** `$ORDERREF`, `$ORDERNUMBER`, `$ORDERAGENT`,
  `$ORDERDELIVERYADDRESS`, `$SITENAME` (all print literally; `$SITENAME` half-resolves as
  `$SITE`+"NAME" → "MainName").
- **Purchase Order:** `$POREF` (e.g. R50086-1), `$PODATE`, `$SUPPLIER_NAME`, `$PODELIVERTO`
  (multi-line delivery address), `$POLINES` (works like $ORDERLINES), `$POSUBTOTAL`,
  `$POTAXTOTAL`, `$POTOTAL`, `$PONOTE`, and **custom fields: `$CFPOTerms` resolves** (CF
  variables work on PO templates).
- **Invoice:** `$INVOICEID`, `$invoiceDate`, `$dueDate`, `$area` (client name),
  `$invoiceAddress1`, `$INVOICEADDRESS2`, `$INVOICEPOSTCODE`, `$INVOICELINES`,
  `$DETAILSTABLEHEADER`, `$INVOICESUBTOTAL`, `$INVOICETAXTOTAL`, `$INVOICETOTAL`,
  `$INVOICENOTE`, `$REPORT157DATA`/`$REPORT158DATA` (embedded saved-report tables - time
  breakdown / device breakdown; they emit `<thead>/<tbody>` rows with `data-colname` attrs
  and NO inline styles - style them via the wrapper table's CSS).
  (Case-insensitive engine - stock templates mix cases.)
- `$DETAILSTABLE` (whole auto-built table) exists for SO/PO/Invoice but emits **rows only**
  (no `<table>` wrapper of its own) - bare in a div it renders as run-together text.
  Either wrap it in a `<table>` element, or (preferred for branding) use
  `<table class="styled-table"><thead>$DETAILSTABLEHEADER</thead>$xxxLINES</table>`.
- The **`detailcolumns`** field on the template record defines which columns
  `$DETAILSTABLEHEADER`/`$DETAILSLINE` emit (systemuse: PRODUCTCODE/DESCRIPTION/QUANTITY/
  PRICE/SUM_NETAMOUNT/TAX…). The three new templates inherited the quote template's set,
  but **on invoices the header/lines actually emit 5 columns** (DESCRIPTION, QUANTITY,
  PRICE, TAX, SUM_NETAMOUNT - no SKU), with inline non-!important `text-align`s.

### Template content decisions (Ryan-approved)

- New templates created alongside the stock ones (stock kept as fallback), then set as
  defaults.
- **PO template has NO Notes & Terms block** (Ryan 2026-07-20 - `$PONOTE` often carries
  internal notes). Instead it has a **Terms meta-cell**: "Net **$CFPOTerms** days" (see §7),
  hidden via `.terms-cell:has(.terms-val:empty){display:none}` when the field is blank
  (`:has()` works - the render engine is modern Chromium). PO closing line: "Please
  reference PO #$POREF on all invoices, packing slips and correspondence relating to this
  order."
- SO keeps a Notes & Terms block ($ORDERNOTE, hidden when empty via `:empty` CSS) + the
  legally-binding-order closing paragraph from the stock template.
- Invoice has a **Payment Details** box (checks payable to Simvay LLC / ACH) + Notes &
  Terms ($INVOICENOTE, hide-when-empty) + Amount Due gradient bar.
- **Time-breakdown Note column is LEFT-aligned, headers centered** (Ryan 2026-07-20).
- **Invoice Description column gets ~half the table width** (Ryan 2026-07-20 "all
  squished" fix).

## 5. Verification workflow (no records harmed)

- **Preview Print** on an SO/PO/invoice renders the current template server-side without
  saving an attachment or sending anything (Generate PDF *does* save an attachment). BUT
  see §3 - Preview Print misrenders multi-page templates; use Generate PDF for those.
- The invoice preview endpoint (`POST /api/Invoice/View`) takes only
  `[{id, current_action_type, current_action_name}]` - no template param (it's actually a
  presence/viewers call) - so to test an invoice template you must temporarily flip one
  invoice's Print Options → PDF Template, preview, and flip it back (done on unpaid
  invoice 20155/display 20137, reverted).
- **Chrome PDF viewer + synthetic input:** the viewer often ignores scroll/#page fragments;
  click ON the document first, then send `Down` arrow key repeats - or click the page
  thumbnail in the left sidebar, which also works.
- Verified renders: SO 4087 (Avon Lake VEEAM renewal), PO 2102/R50086-1 (TD SYNNEX, incl.
  Terms cell "Net 30 days"), invoice 20155 (Cleveland Yachting Club) - Simvay Invoice and
  the rebranded Invoice with Time Breakdown (Generate PDF, both pages, incl. the
  Description-width fix).

## 6. "Invoice with Time Breakdown" (id 13) - cleaned up AND rebranded (2026-07-20)

Four rounds, current sentinel `SIMVAY-TB-V7` (page 1 stays a byte-copy of template 32,
current sentinel `SIMVAY-INV-V4`):

1. **Placeholder cleanup (V3):** removed client-facing junk "Tax Number: TAXNUMBERHERE";
   replaced "Bank Details: BANK DETAILS GO HERE…" with "**Payment:** Make checks payable to
   **Simvay LLC**. / Contact us to pay via ACH."
2. **Full restyle (V4):** page 1 ("Main Page") is now a byte-copy of the Simvay Invoice
   (32) layout - hero band, meta-strip (From / Bill To / Dates), styled `$INVOICELINES`
   table, Amount Due bar, Payment Details box. Page 2 ("Time Breakdown") keeps its
   structure (h3 + intro + wrapper table around `$REPORT157DATA`/`$REPORT158DATA`)
   with the Simvay stylesheet swapped in, teal uppercase h3s, and a min-width on the Note
   column. Appearance updated to match (colour #00627b, margin 13).
3. **Alignment fix (V4/V5):** page-2 wrapper tables now carry
   `class="styled-table report-table"`; scoped rules left-align ALL body cells (incl. Note,
   which the shared stylesheet was right-aligning as "column 5 = price") and center the
   headers:
   `.report-table tbody tr td, …td:nth-child(3..6){text-align:left !important}` /
   `.report-table thead tr th, …th:nth-child(3..6){text-align:center !important}` -
   specificity ≥ the shared rules, and page 2 comes later in the merged document. See §3
   for why lower-specificity overrides silently failed.
4. **Description-width fix (V5→V7, and 32 V2→V4):** the items table was rendering
   Description in the quote stylesheet's 92px SKU slot. Tagged the table
   `styled-table invoice-table` and added the `/* invoice column layout */` block
   (Description 52% left / Qty 60px center / Unit Price 70px right / Tax 60px right /
   Price 80px right / `thead th{white-space:nowrap}`). **First attempt (block only in
   page 1) rendered unchanged** - page 2's stylesheet copy won the specificity tie by
   document order; the fix works once the block is ALSO appended to page 2's `<style>`
   (§3). `width:auto` for Description also under-delivered (auto table layout gave the
   leftover to the Price column) - the explicit 52% is what produced the wide column.
   Verified via Generate PDF on invoice 20155: page 1 two-line descriptions, single-line
   headers; page 2 breakdown tables untouched (they're `.report-table`, not
   `.invoice-table`).

## 7. PO Terms custom field (CFPOTerms, id 269) - added 2026-07-20

Some vendors require payment terms on the PO. Implementation:

- **Custom field:** Config → Custom Objects → Custom Fields (`/config/custom/fields`) →
  **Entity dropdown (top-left) → Purchase Orders** (URL `?typeid=998`) → New. The entity
  is set by the LIST filter before clicking New - the form itself has no entity picker
  (a form opened under Entity=Ticket creates a ticket field; it also demands a Tab).
- Field: name `POTerms` → **`CFPOTerms`** (id **269**), label "PO Terms (Net Days)", type
  Text/Anything, **Default Value = 30** (Default Value is a stock feature of the field
  form), Tab = "Purchase Order Details" (shows in the PO edit right sidebar, above Print
  Options). Stored in `SupplierOrderHeader`.
- **Template:** PO template (31, `SIMVAY-PO-V4`) has a 4th meta-cell "Terms" rendering
  "Net **$CFPOTerms** days", auto-hidden when blank via `:has(.terms-val:empty)`.
- **Default applies to NEW POs only** - existing POs have no value (cell hides). PO 2102
  was set to 30 manually as the verification example.
- Usage: agents just type the number (e.g. 45) in the PO's "PO Terms (Net Days)" field to
  override per-vendor.

## 8. Remaining loose ends

- Credit Notes still use Basic Invoice Pdf (old look).
- "Default PDF Template for Bills" is unset (stock behavior).
- Existing (pre-2026-07-20) invoices keep their baked-in old template ids.
- Test invoice 20155 accumulated several regenerated PDF attachments during verification
  (harmless; latest is current).
