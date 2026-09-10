---
title: "HaloPSA 02: Building quotes (lines, groups, recurring items, tax)"
type: runbook
updated: 2026-08-04
tags: [halopsa, quotes]
related: [runbooks/halopsa-01-overview, projects/halopsa/STATUS]
source: "HaloPSA Claude Project: claude/HaloPSA-Runbook-02-Quotations-Lines-Groups.md"
migrated: 2026-09-09
---
> Migrated 2026-09-09 from the HaloPSA Claude Project (`HaloPSA-Runbook-02-Quotations-Lines-Groups.md`). This file is now the canonical copy; the project doc is frozen. The verbatim original is in `projects/halopsa/archive/project-export-2026-09-09/`. Em and en dashes in prose were replaced per CLAUDE.md; code blocks are untouched. Cross-references were rewritten to brain paths.

# Simvay HaloPSA - Runbook 02: Building Quotes (Lines, Groups, Recurring Items, Tax)

> **Purpose:** How to build a full quotation in the HaloPSA web UI - ad-hoc lines, catalog
> items, recurring (monthly/annual) lines, grouped sections that render as separate
> ONE-TIME / MONTHLY / ANNUAL blocks on the Simvay Proposal PDF, and per-line tax codes.
>
> Learned building the Thogus "Backup Appliance and BaaS" dual quote (opportunity #51420,
> quote 51420-1) on 2026-07-16. Companion to Runbook 01 (overview, PDF template, custom fields).
>
> **Instance:** `https://simvay.halopsa.com`
> **Last updated:** 2026-08-04 (§2 leasing-field correction, §5 EXEMPT/public-sector rule, §7 Leasing detail - see Runbook 11)

---

## ⚠️ 1. CRITICAL: the quote-edit lifecycle (how edits are lost)

Quote line edits are held **client-side** until the quote's **toolbar Save** is clicked.
The modal flow is: quote → **Edit** (toolbar) → add/edit lines (each line dialog has its own
Save) → **toolbar Save** persists EVERYTHING.

1. **NEVER press Escape while in quote edit mode.** Escape closes the entire quote modal and
   silently **discards every unsaved line** - an entire 8-line quote was lost this way.
   (Standing instruction from Ryan: *do not use Escape when in edit mode. Save first.*)
2. A line dialog's Save only stages the line into the edit session; it is NOT persisted until
   the toolbar Save.
3. **Save early, save often**: click toolbar Save after every few lines, then click Edit again.
   Toolbar Save returns the quote to view mode.
4. Reload/reopen to verify persistence (same rule as Runbook 01 §7.3).
5. Clicking a table row (not its pencil) while in edit mode can also bounce back to view mode -
   harmless if everything was saved, another reason to save often.

## 2. Ad-hoc lines ("Add Ad-hoc Item")

Dialog fields (top→bottom): Description, Supplier, SKU, Quantity, Fixed Quantity, Cost,
Track cost only, **Gross Margin (%)**, **Base price**, Item Is Taxable, **Tax code**,
Discount (%), **Group**, Notes, Optional, (Billing Period/Periods on recurring lines),
Delivery Override/Site, Is a Finance/Leased Item, Client, Item, Advanced (price formula).

> **⚠️ Correction (2026-08-04):** the **catalog-item** line dialog (`Edit Line ID …`, reached
> via the row pencil on a line added through *Add Item*) has **NO "Is a Finance/Leased Item"
> field.** Verified on quotes 51641-1 / 51643-1. Its fields are: Sequence, Description,
> Supplier, SKU, Quantity, Fixed Quantity, Cost, Track cost only, Gross Margin (%), Base price,
> Item Is Taxable, **Tax code**, Discount (%), Group, Notes, Optional, **Billing Period**,
> Number of Periods, Start date, Auto Renew, Delivery Override, Delivery Site, Client, Item,
> Automatic Increase, Advanced.
>
> **Leasing is a QUOTE-level setting**, in the right sidebar under **Leasing** → *Is Leased?*
> → reveals *Term Limit (In Months)* and *Margin Per Annum (%)*. See §7 and Runbook 11 §6.3.
> The field list above may still be accurate for genuinely *ad-hoc* lines - unverified since.

**Margin-driven pricing gotcha:** Base price is **recalculated from Gross Margin** when you
tab out - typing a Base price directly then Tab gets overwritten (`price = cost / (1 − margin)`).
Two reliable approaches:

- **Cost > 0:** set Cost, then set **Gross Margin** to the value that yields the target price
  and Tab. E.g. cost+20% markup ⇒ margin 16.6667%; $1,579 → $1,979.99 ⇒ margin 20.2521%;
  $116.65 → $166.67 ⇒ margin 30.01.
- **Cost = 0 (flat-fee service):** leave Cost 0 and type Base price directly - with cost 0 the
  margin recalc can't fire; typing price then clicking the dialog Save directly worked.

Cents rounding: margin→price rounding can land a penny off (2860.32 @16.6667% → 3432.39,
not .38). Fix the base price by margin tweak or accept the penny.

## 3. Recurring lines (monthly / annual) need catalog Items

Ad-hoc lines have **no billing-period field** - a line is recurring only if it comes from an
**Item** flagged recurring. Flow:

1. **Create New Item** (button on quote edit, or Items module → New):
   - Details tab: Name, **Group** (item group, required - e.g. `VEEAM`, `C2`; full list incl.
     Duo, KnowBe4, Microsoft 365, Mimecast, SentinelOne, Umbrella, BITWARDEN, BrightSign,
     CloudFlare, Desktop Computers, …),
     **"Is a Recurring Item" checkbox → reveals Is a meter / Auto Renew / Default billing
     period** (Weekly, Monthly, 2-Monthly, Quarterly, 6-Monthly, Yearly, 2-Yearly, …).
   - Costing & Pricing tab: Price, Recurring Price, Cost, Recurring Cost, Gross Margin.
   - **Gotcha:** the recurring checkbox can silently revert if you immediately click another
     control (both items created this session saved as non-recurring the first time. Fix in
     Items module → item → Edit → re-check → set billing period → Save, then **verify the
     Details view shows "Is a Recurring Item: Yes"**).
   - **Gotcha:** the item's Price did not flow onto an already-added quote line, and for the
     Yearly item the line price came in as 0 - always check the line price after adding.
   - **Gotcha (price auto-conversion):** changing an item's Default billing period
     Yearly→Monthly **divides the item's Price by 12 on save** - including a price you typed
     in the same save (166.67 saved as 13.89). Change the billing period, save, THEN set the
     price in a second edit/save.
2. Add to quote via **Add Item** (catalog picker): search box (press Return), rows have
   **inline editable Price / Cost / Quantity** - set qty (and fix price) right in the picker,
   then click **Select**. Saving a "Create New Item" form while on a quote also auto-adds
   one line of that item to the quote.
   - **Multi-row selection (verified 2026-08-04):** set a Quantity on **several rows** and click
     **Select once** - all of them are added together. The modal footer echoes the pending
     selection (`…Per Endpoint - 12 Months x 119, …Per Windows Server - 12 Months x 6`);
     read it to verify before committing.
   - Items whose catalog `item_default_billing_period` is already correct come in with the right
     price and the ♻ badge with **no** post-add fixup needed (the SIM-VULN family, ids 72-76,
     landed clean at full price on all three 2026-08-04 quotes).
3. On the quote line (pencil → Edit Line), recurring items expose **Billing Period**
   (inherited from item default, overridable per line), **Number of Periods** (0 = ongoing;
   set **12 on a Monthly line to record a 1-year term**, or **1 on a Yearly line**), Start date,
   Auto Renew. The line list shows a ♻ Monthly/Yearly badge in the leftmost "Billing" column.
4. **Contract-term visibility:** Number of Periods alone isn't obvious on the PDF - also put
   the term in the **group description and/or line description** (e.g. group
   "Backup as a Service - BaaS (Monthly, 12-Month Term)").
5. **Client-facing vs internal descriptions:** the quote line description is editable
   independently of the catalog item name - use this to scrub internal detail from the PDF
   (e.g. item 454 is named `…Veeam Licensing + 4 Hours Monthly Management` internally, but the
   quote line reads "BaaS - Backup as a Service (Includes Veeam Licensing & Managed Backup
   Operations)" so the labor allotment isn't exposed; likewise hardware make/model can be
   genericized, e.g. "Dedicated Veeam Backup Server / Jumpbox (32GB RAM, 1TB SSD, Dual 25GbE)"
   instead of the Minisforum model name).

## 4. Grouped sections ("Add New Bundle" = Add Group)

- **"Add New Bundle"** on the quote edit toolbar opens an **"Add Group"** dialog:
  Sequence, Description (required), Notes, Accounts Code, Hide Items that are part of this
  group, Hide Item Price for items in group (PDF only), Optional, Advanced.
  This creates a **group header row** in the lines table. Edit it later via its own hover
  pencil ("Edit Group" dialog - e.g. to rename).
- Free-typing a group name in a line's Group combobox does **NOT** persist (shows "No options",
  reverts on blur). Groups must exist first as group rows.
- Assign each line: hover row → **pencil** → Edit Line → **Group** dropdown (now lists the
  group descriptions) → pick → dialog Save. The line indents under the group and the group row
  shows rolled-up Price/Cost/Profit. Set Group back to "No Grouping" to pull a line out.
- Group **Sequence** places the header among lines (use 5 for a top group, 65 for a mid group
  after lines sequenced 10-60, 200 for a bottom group).
- Hover a row in edit mode to reveal pencil (edit) and trash (delete) icons on the right.
- "Update Table Values" toggles an inline grid editor (description/qty/price/cost only - no
  Group or Tax column). Toggle it off before using pencils.
- **The PDF auto-groups by billing term anyway** (one-time vs monthly vs annual sections), so
  use quote groups for *sub*-structure within a term - e.g. a "Backup Hardware" group and a
  separate "Initial Configuration Service (One-Time)" group among the one-time lines - not to
  separate one-time from recurring (Ryan's guidance). A single-line group works fine as a way
  to visually break out a service on the PDF.
- A short 2-line quote (e.g. the A1 renewals, Runbook 11) needs no groups at all.

## 5. Per-line tax codes (Lorain County, EXEMPT, etc.)

Tax is set **per line**: hover row → pencil → Edit Line → **Tax code** dropdown (right below
Base price / "Item Is Taxable"). Options in this instance:
**Default, No Tax, Sales Tax 20%, CUYAHOGA, EXEMPT, LORAIN, OHIO.**

- **Public-sector rule (Ryan, 2026-08-04): public-sector clients get tax code `EXEMPT`.**
  Applied to City of Parma Heights (municipality) and Olmsted Township (township) on the A1
  renewals - Total Tax $0.00. Private-sector clients keep the client default.
- **`Default` resolves to the client's own rate**, it is not "no tax": on Conveyer & Caster
  (Westlake / Cuyahoga) Default computed **8%** - $4.00 on a $50 line, $12.00 on a $150 line,
  Total Tax $396.00 (verified 2026-08-04, quote 51642-1).
- **LORAIN = 6.5%** (verified: $125.93 → $8.19; $3,653.11 → $237.45). Use for Lorain County
  clients (e.g. Thogus, Avon Lake). Standing instruction from Ryan for the Thogus quote: *all
  items must have Lorain County tax.*
- The line-table Tax column shows **per-unit** tax; Net Total picks up qty × tax. The PDF
  shows per-line tax plus a Tax row in each section's subtotal block.
- There's no bulk tax setter visible - set it line by line (8 pencil edits for the Thogus quote).
- New lines default to tax code **Default** - remember to change it when a county code or
  EXEMPT is required.

## 6. How groups render on the Simvay Proposal PDF

Generate PDF (view mode) → groups render as teal sub-header rows inside the billing-period
sections: **ONE-TIME COSTS** (with Subtotal/Tax/Total), **MONTHLY RECURRING COSTS**
(Total per month), **ANNUAL RECURRING COSTS** (Total per year), and - since template
V38/V39, 2026-07-27 - **2-YEAR RECURRING COSTS** (Total per 2-year term) and
**3-YEAR RECURRING COSTS** (Total per 3-year term) for lines with billing period
**2-Yearly** / **3-Yearly**. Ungrouped lines print after
the grouped ones within their section. A group whose lines span periods appears in each
relevant section. The footer **TOTAL CONTRACT VALUE · incl. tax** banner = one-time total +
ONE month of recurring (not the full term), so state term value in conversation/cover text
if needed. (A 2-/3-Yearly line's FULL term amount is included once in the banner - verified
on Brooklyn 50476-1: $15,039.61 one-time + $3,085.20 3-year = $18,124.81 banner.)

**⚠️ Billing periods with no template section silently vanish from the PDF.** Before V38,
3-Yearly lines (e.g. Kris's City of Brooklyn "Rec Renovation" quote 50476-1, quoteid 10222 -
Cisco 3-year subscriptions/licenses) rendered nowhere on the proposal PDF. If a quote uses a
billing period other than one-time / Monthly / Quarterly / Annual / 2-Yearly / 3-Yearly /
Weekly, the template needs a matching `<!--[PERIOD]-->` section added (Runbook 01 §6.7,
§6.10 - clone the Annual block).

## 7. Per-quote settings (right sidebar in Edit mode, scroll down)

Status, Date, **Expiry Date** (auto ~30 days), Days to deliver, PO Number, Currency, Notes,
Assigned Agent, then **Print Options** → **PDF Template** (set to **Simvay Proposal** -
defaults to *Default Template*, the navy built-in; see Runbook 01 §4.4), "Include grouped items
quantity/price" checkboxes, canned text, PDFs to prepend/append, **Billing Account details**
(Billing Contact Name / Email / Phone), and **Leasing** at the very bottom.

**Leasing (detail added 2026-08-04):** the section holds a single **`Is Leased?`** checkbox.
Ticking it reveals **`Term Limit (In Months)`** and **`Margin Per Annum (%)`**. This is the
**only** leased/finance control on a catalog-item quote - there is no per-line equivalent
(see the §2 correction). One tick therefore covers every line on the quote. Used on the A1
renewals with Term Limit **12**, Margin Per Annum left *Not set*; view mode then reads
`Is Leased? Yes` / `Term Limit (In Months) 12`.

## 8. Misc discoveries

- An **Opportunity** (Sales area, tickettype 6) shows its quotes under "Quotes, Orders &
  Invoices" in the right sidebar; "Raise Quote"/quote actions create `NNNNN-1` references.
  **Creating the opportunity itself and stepping it through the workflow is Runbook 11 §4-§5**
  (Ryan's standing sales-process rule: quotes are raised FROM an opportunity, never standalone).
- Quote lines get internal Line IDs (Edit Line dialog title "Edit Line ID 1975").
- The connector's `get_tickets`/`Tickets` filters (`client_id`, `tickettype_id`) returned 0
  for Thogus - opportunity lookup is more reliable via the browser Pipeline View
  (`/tickets?area=13`). Direct URL to an opportunity: `/tickets?area=13&id=NNNNN`.
- Thogus is a **Prospect** (client_id 95) - prospects don't appear in `get_clients` results.
- Item catalog list: `/items`, filter by item group in left panel; search box only searches
  within the selected group - pick the right group (or All) first. Direct URL:
  `/items?itemid=NNN`.
- **The connector CAN read the item catalog:** `halo_get` path `Item` with
  `{"search":"SIM-VULN","count":50}` returns full item records (price, cost, SKU,
  `isrecurringitem`, `item_default_billing_period`). Much faster than the Items UI for
  confirming SKUs and prices before building a quote (verified 2026-08-04).
- **Collapsed table viewport:** the quote lines table sometimes renders only ~1 row tall with
  its own inner scrollbar (smaller browser windows). Workarounds: `resize_window` bigger
  (1680×1100 worked well; may take a couple of tries to apply), or use the Chrome `find` tool
  on a line's description → `scroll_to` the ref, then hover/pencil at the visible row.
- The quotes-list **search box** (left panel above the Quotations nav) finds quotes by client
  name (e.g. "brooklyn") - press Return after typing (verified 2026-07-27).

## 9. Worked example - Thogus dual quote 51420-1 (final state, 2026-07-16)

Opportunity #0051420 "Backup Appliance and BaaS" (Thogus, Mark Szuminski). Quote 51420-1,
Draft, PDF template Simvay Proposal, expiry 8/15/2026. Title "Backup Project and Management".
**All 8 lines tax code LORAIN (6.5%). Three groups.**

**ONE-TIME** - Subtotal **$14,608.70**, Tax **$949.57**, **Total $15,558.27**:

Group "Backup Hardware" ($12,508.70 sell / $10,352.92 cost):
| Line | Qty | Cost | Sell |
|---|---|---|---|
| Synology HAT5300-12T 12TB HDD | 4 | 691.10 | 829.32 |
| Synology RKS-02 Rail Kit | 1 | 104.94 | 125.93 |
| Synology RS2423RP+II 12-Bay RackStation | 1 | 3,044.26 | 3,653.11 |
| Synology Premium Support 3-Year (PSS3-E) | 1 | 2,860.32 | 3,432.39 |
| Dedicated Veeam Backup Server / Jumpbox (32GB RAM, 1TB SSD, Dual 25GbE) - genericized; actually Minisforum MS-02 Ultra | 1 | 1,579.00 | 1,979.99 |

Group "Initial Configuration Service (One-Time)" (sequence 65, single line - broken out per
Ryan to show the project service clearly):
| Line | Qty | Cost | Sell |
|---|---|---|---|
| Initial Configuration Service: Backup Infrastructure Deployment & Network Segmentation (ransomware-resilient isolation) - One-Time Flat Fee | 1 | 0 | 2,100.00 |

Synology costs from TD SYNNEX quote US2026071485337 (#163345235, expires 8/13/2026), priced
cost+20% (margin 16.6667%). Jumpbox = Amazon $1,579, sold at list $1,979.99.

**MONTHLY - group "Backup as a Service - BaaS (Monthly, 12-Month Term)"** - Subtotal
**$1,316.67/mo**, Tax **$85.58**, **Total per month $1,402.25**; both lines Monthly with
Number of Periods = 12 (1-year term):
- Item 454 (catalog name `BaaS - Backup as a Service (Veeam Licensing + 4 Hours Monthly
  Management)`, VEEAM group, recurring Monthly, $1,150/mo, cost 0). Quote line description
  scrubbed to "BaaS - Backup as a Service (Includes Veeam Licensing & Managed Backup
  Operations)" - labor allotment kept internal per Ryan.
- Item 455 `BaaS Add-On - Synology C2 Cloud Replication (20TB) - Billed Monthly, 12-Month Term`
  C2 group, recurring Monthly, $166.67/mo, cost $116.65/mo (margin 30.01; $2,000/yr
  equivalent vs $1,399.80/yr C2 cost).

PDF TOTAL CONTRACT VALUE banner shows $16,960.52 (= one-time total + one month, incl. tax).

## 10. Worked example - A1 renewals (2026-08-04)

Three single-group-free, 2-line annual recurring quotes built opportunity-first. Full procedure,
Action1 sizing method, SKU/tier tables and the leased/EXEMPT settings are in
**Runbook 11 - `runbooks/halopsa-11-action1-renewal-quotes.md`**.

| Client | Opp | Quote | Annual | Tax |
|---|---|---|---|---|
| City of Parma Heights | 51641 | 51641-1 | $5,660.00 | EXEMPT |
| Conveyer & Caster | 51642 | 51642-1 | $4,950.00 | Default 8% ($396.00) |
| Olmsted Township | 51643 | 51643-1 | $4,400.00 | EXEMPT |
