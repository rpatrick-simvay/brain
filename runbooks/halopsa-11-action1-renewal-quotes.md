---
title: "HaloPSA 11: Action1 renewal quotes and the opportunity-first sales process"
type: runbook
updated: 2026-08-31
tags: [halopsa, action1, quotes, opportunities]
related: [runbooks/halopsa-01-overview, projects/halopsa/STATUS]
source: "HaloPSA Claude Project: claude/HaloPSA-Runbook-11-Action1-Renewal-Quotes.md"
migrated: 2026-09-09
---
> Migrated 2026-09-09 from the HaloPSA Claude Project (`HaloPSA-Runbook-11-Action1-Renewal-Quotes.md`). This file is now the canonical copy; the project doc is frozen. The verbatim original is in `projects/halopsa/archive/project-export-2026-09-09/`. Em and en dashes in prose were replaced per CLAUDE.md; code blocks are untouched. Cross-references were rewritten to brain paths.

# Simvay HaloPSA - Runbook 11: Action1 (A1) Vulnerability & Patch Management Renewal Quotes

> **Purpose:** End-to-end procedure for sizing and building an **Action1 Host Vulnerability
> and Patch Management** renewal - pull endpoint counts from Action1, apply the growth
> allowance and tier rules, create a sales **Opportunity**, step it through the workflow, and
> **raise the quote from the opportunity**.
>
> **Learned:** 2026-08-04 building three renewals in one session - City of Parma Heights
> (opp 51641 / quote 51641-1), Conveyer & Caster (51642 / 51642-1), Olmsted Township
> (51643 / 51643-1). Extended 2026-08-21 with Bober Markey Fedorovich (51880 / 51880-1).
>
> **Instance:** `https://simvay.halopsa.com`
> **Companion runbooks:** 01 (overview), 02 (quote lines/groups/tax), 08 (Action1 ticket routing),
> 14 (M365 CSP - §0 client-visible Details rule, §7 opportunity/quote UI gotchas),
> 15 (KnowBe4 quotes).
> **Last updated:** 2026-08-31 (**§1.1 opportunity Details field is CLIENT-VISIBLE - keep it
> short; audit trail goes in an Internal Note.** §3 and §4 step 6 amended accordingly; §1
> extended for quotes triggered by a service ticket.)
> Earlier: 2026-08-21 (§2.1 rewritten - **`list_endpoints` silently under-reports; use the
> Managed Endpoints report instead**. New §8 gotchas 11-14, new §11 worked example.
> §6.2 - **BMF lines are pinned to `CUYAHOGA`, not left on `Default`**.
> 2026-08-24 - **cost raised to $21.50 on all SIM-VULN items; new tiered item `SIM-VULN-EP`
> replaces T1-T4 (§2.5); BMF converted to monthly billing (§6.4)**. New gotchas 15-17.
> 2026-08-24 (later) - **catalog cleanup: T4 removed, tier breakpoints raised, legacy A1 SKUs
> set to Obsolete (§2.6); new §6.5 renewal rate-parity rule**. New gotchas 19-21.)

---

## 1. Standing sales-process rule (Ryan, 2026-08-04)

> **These must be new Opportunities that are stepped through the workflow, and the quote is
> raised FROM the opportunity.** Do not create a standalone quote from the Quotes & Orders
> module. The opportunity is the record of the deal; the quote hangs off it.

**Applies even when the request originates in a SERVICE ticket** (confirmed by Ryan
2026-08-31 for ticket 50822 → opportunity 51947 / quote 51947-1, Runbook 14 §6): create the
opportunity for the same client/contact, raise the quote from it, and reference the service
ticket number in the (short) Details line. Do not use *Raise Quote* on the service ticket itself.

### 1.1 ⚠️ The opportunity Summary and Details are CLIENT-VISIBLE (Ryan, 2026-08-31)

> *"The opportunity ticket description is visible to the client. Being so verbose in that field
> is not a wise idea."*

- **Details = one short client-safe sentence.** What is being quoted, quantity, term, and the
  originating ticket number if any. Nothing about cost, margin, list-price basis, the reference
  quote used for pricing, tax status, sizing method, or the client's security posture.
- **Audit trail (counts, pull date, growth allowance, predecessor contract ref, pricing basis)
  goes in an Internal Note** on the opportunity (toolbar *Internal Note* - hidden from user) or
  on the quote's *Internal Notes* tab. **Not** in Details.
- **Summary** is also visible - keep the `<ITEM>-MMDDYY-MMDDYY` reference or a plain product
  name; no internal annotations.
- **To fix Details after Submit:** the header has no edit control. Hover the **Opened** action
  card → **⋯ → View/Edit Action → Edit → Note → Save**. Verified: `Tickets/<id>` `details`
  updates and the card shows *Edited*. Full click path in Runbook 14 §0 / §7.

---

## 2. Sizing: Action1 → quantities

### 2.1 ⚠️ Pull the endpoint counts - use the REPORT, not `list_endpoints`

**This section was rewritten 2026-08-21 after `list_endpoints` under-reported BMF by 47%.**

**What goes wrong.** `mcp__Action1__list_endpoints` returns ~4.5 KB of JSON per endpoint (30
custom-attribute objects each). For any org over ~110 endpoints the response exceeds the inline
token limit, gets written to a file - **and that file is hard-truncated at 500,000 characters**.
The truncation cuts the tail of the JSON, which is exactly where `total_items` lives. So:

- `json.load()` fails with `Invalid control character at ... char 500000`.
- A `grep -c` of the endpoint records returns **only the records that fit**, and that number
  looks like a perfectly plausible total.
- On BMF this produced **112**, when the org actually has **210**. The error was caught only
  because Ryan said "BMF shows 207 for me - double check that number."

**Pagination does not rescue it.** `next_page` was passed four times as the cursor URL
(`…?limit=50&from=50/100/150/200`) and **every call returned the same first 50 endpoints**
(verified by comparing the first endpoint name across all five saved files - identical).
Treat `list_endpoints` pagination as **non-functional** through this connector.

**Do this instead - the Managed Endpoints report:**

```
mcp__Action1__list_reports  {org_id}                     → categories
mcp__Action1__list_reports  {org_id, category_id:"cat_iam"} → finds the report
mcp__Action1__get_report_data {org_id,
    report_id: "managed_endpoints_1635942317188", limit: 500}
```

The report id **`managed_endpoints_1635942317188`** is a built-in and is the same across orgs.
It returns one compact row per endpoint - **210 rows in 153 KB**, well inside the 500 KB file
cap, so the JSON parses cleanly and `total_items` is trustworthy.

Row shape (`items[].fields`): `Endpoint Name`, `Operating System`, `Status`,
`Last Seen`, `_Last Seen_sortby` (unix seconds), `Endpoint Groups`, `agent_id`.

```python
import json, collections, math
d = json.load(open('<saved report file>'))
rows = [i['fields'] for i in d['items']]
assert len(rows) == int(d['total_items'])          # <-- the check that would have caught it
print(collections.Counter(r['Status'] for r in rows))
srv = [r for r in rows if 'server' in r['Operating System'].lower()]
ws  = [r for r in rows if 'server' not in r['Operating System'].lower()]
print(len(ws), len(srv), math.ceil(len(ws)*1.05), math.ceil(len(srv)*1.05))
```

**Always assert `len(rows) == total_items` before quoting off the number.** And if the figure
disagrees with what the account owner sees in the Action1 console, believe the console and
re-derive - a small delta (BMF: 210 API vs 207 console) is normal agent churn; a 2× delta is a
truncation bug.

- **`total_items` is the licensed count.** Count **all** endpoints regardless of
  `Status` (Connected/Disconnected) - Action1 bills on the subscription, not the connection.
  Disconnected ≠ unlicensed. (On BMF, 69 of 210 were Disconnected and all were licensed.)
- Split **servers vs workstations** on the `Operating System` string containing `server`.
  This drives the SKU split (§2.3).
- Bucket `_Last Seen_sortby` by age. Heavy `>90d` counts are worth flagging to the account owner
  as decommission candidates, but do **not** silently drop them from the quote.

### 2.2 Apply the growth allowance

Standard practice: **add 5% and round UP to a whole endpoint**, applied **separately** to the
workstation count and the server count.

### 2.3 SKU selection - the server split

`QUOTER.xlsx` → **Cyber SKUS** sheet → *Risk Based Managed Patching A1* block.
SharePoint: `https://simvay.sharepoint.com/sites/ClientHub/Shared Documents/INTERNAL/QUOTER.xlsx`

| SKU | Description | Halo item id | List price | Cost | GM |
|---|---|---|---|---|---|
| **`SIM-VULN-EP`** | Per Endpoint - 12 Months - **TIERED, use this** | **484** | tier table (§2.5) | $21.50 | 57 / 46.25 / 38.57 |
| **`SIM-VULN-S`** | Per **Windows Server** - 12 Months - **use this** | **72** | **$150.00** | $21.50 | 85.67% |
| `SIM-VULN-T1` | Per Endpoint - 🚫 **Obsolete 2026-08-24** | 73 | $50.00 | $21.50 | - |
| `SIM-VULN-T2` | Per Endpoint - ⏳ **live only until BMF rolls 2026-12-01** | 74 | $40.00 | $21.50 | 46.25% |
| `SIM-VULN-T3` | Per Endpoint - 🚫 **Obsolete 2026-08-24** | 75 | $35.00 | $21.50 | - |
| `SIM-VULN-T4` | Per Endpoint - 🚫 **Obsolete 2026-08-24, band deleted** | 76 | $25.00 | $21.50 | - |
| `SIM-SOC-VULN-S` | Server, monthly $12.50 - ⏳ **live only until BMF rolls 2026-12-01** | 177 | $12.50/mo | $0 | - |

**Only two SKUs may be used on a NEW A1 quote: `SIM-VULN-EP` (484) and `SIM-VULN-S` (72).**
Everything else in the *Simvay - A1* group is either Obsolete or held open purely for BMF's
in-flight recurring invoice (§2.6).

**Cost is $21.50/endpoint/year for BOTH endpoints and servers** (Ryan, 2026-08-24 - "It's the
same for us for endpoints and servers"). Set on all five items that day; the old $20.00 figure
is dead. QUOTER's $21.50 was right all along.

**Rule (confirmed by Ryan 2026-08-04):** servers go on `SIM-VULN-S`; workstations go on the
tier SKU. **The tier is chosen from the TOTAL endpoint count (servers + workstations, after
the +5%)**, not the workstation count alone.

**Tiering for S1 and A1** (QUOTER, *Tiering* block) - A1 uses the **Number of Endpoints** column:

| Tier | Endpoints |
|---|---|
| T1 | 10 - 99 |
| T2 | 100 - 249 |
| T3 | 250 - 499 |
| T4 | 500 - 799 |

**⚠ Known QUOTER↔Halo discrepancies (still unreconciled as of 2026-08-21):**
- **T4 price:** QUOTER says $30.00, Halo item 76 says $25.00.
- **Cost:** QUOTER says $21.50/endpoint, Halo items all carry `costprice: 20`.
- The **DISCOUNT − EDU / − GOV ($30.00)** rows in QUOTER are worded *"Security Operations
  Center - Per Endpoint"* - they are **SOC/S1 discounts, NOT A1**. Do not apply them to
  SIM-VULN lines.
- Ignore the older `SIMSEC-VULN*` / `SIM-SOC-VULN-S` items (ids 177, 202-204) - zero-priced
  legacy records.

### 2.5 ⚠️ Tiered pricing - `SIM-VULN-EP` replaces T1-T4 (2026-08-24)

**Halo has native tiered pricing on items, and it does exactly what the Simvay tier table does.**
Item → **Costing & Pricing** → **Use Tiered Pricing** ✓ → **Tiered Pricing Method**:

| Method | Behaviour |
|---|---|
| **Volume based pricing** ← **use this** | All units take the price of the tier containing the selected quantity. |
| Tiered based pricing | Units are split into their respective tiers (graduated). Not the Simvay model. |

**Item 484 `SIM-VULN-EP`** is configured volume-based with:

| Price | Min Qty | Incl Min | Max Qty | Incl Max |
|---|---|---|---|---|
| $50.00 | 0 | Yes | **150** | **No** |
| $40.00 | **150** | Yes | **500** | **No** |
| $35.00 | **500** | Yes | *(blank)* Unlimited | No |

**Breakpoints raised and T4 deleted 2026-08-24 (Ryan).** The old table was
0-100 $50 / 100-250 $40 / 250-500 $35 / 500+ $25. Every band moved **up**, none down:

| Endpoints | Old $/yr | New $/yr |
|---|---|---|
| 0-99 | $50 | $50 |
| 100-149 | $40 | **$50** |
| 150-249 | $40 | $40 |
| 250-499 | $35 | **$40** |
| 500+ | $25 | **$35** |

**The 14%-GM hole is gone.** Worst-case margin is now **38.57%** ($35 against the $21.50 cost).
There is no longer any A1 endpoint price below $35, so the QUOTER-vs-Halo T4 discrepancy
($30 vs $25) is moot - neither figure survives.

Add the item to a quote at the endpoint quantity and **Halo prices the line automatically** -
verified 2026-08-24: qty 185 → $40.00 without touching the price field.

> **⚠ Tier basis changed (Ryan, 2026-08-24).** The old rule picked the tier from
> **workstations + servers combined**. Halo's tiering keys off **that line's own quantity**, so
> the rule is now: **the tier is chosen from the ENDPOINT LINE quantity alone.** Servers stay on
> `SIM-VULN-S` at a flat $150 and no longer influence the tier. On BMF both methods gave T2; they
> diverge on server-heavy clients (95 WS + 15 srv = 110 total → old rule T2 $40, new rule T1 $50).

- **Boundaries must be contiguous, not adjacent-integer.** Halo validates against *continuous*
  quantities: tiers of 0-99 and 100-249 are rejected with
  *"Gap detected at quantity 99. Tiered prices must be completely defined for all values greater
  than 0."* Overlap the boundary and un-tick **Include Maximum** instead.
- First tier must start at 0; last tier must be open-ended (blank Maximum).
- **"Only takes effect on addition of a new line"** - changing the tier table does **not**
  reprice existing quote lines.
- Tier prices are **annual** (matching QUOTER). For a monthly quote, divide by 12 per §6.4.
- ~~**T4 is $25.00 in Halo vs $30.00 in QUOTER, still unresolved.**~~ **RESOLVED 2026-08-24 -
  T4 deleted from the tier table and item 76 set to Obsolete.** (Historical note: at the
  $21.50 cost, $25 leaves **14% GM** on 500+ endpoint deals ($30 gives 28.3%). Flagged to Ryan
  2026-08-24; the tier table carries $25 to preserve current behaviour. **Change both the tier
  table and item 76 if he rules for $30.**
- ~~T1-T4 (items 73-76) are left live and cost-corrected.~~ **Retired 2026-08-24 - see §2.6.**
  (Superseded: retire them once nothing recurring
  references them - confirm with Ryan before deactivating.

### 2.4 Worked sizing

| Client | Date | A1 org endpoints | WS | Srv | WS +5%↑ | Srv +5%↑ | Tier | Annual |
|---|---|---|---|---|---|---|---|---|
| City of Parma Heights | 08-04 | 118 | 113 | 5 | **119** | **6** | T2 @ $40 (124) | **$5,660.00** |
| Conveyer & Caster | 08-04 | 74 | 65 | 9 | **69** | **10** | T1 @ $50 (78) | **$4,950.00** |
| Olmsted Township | 08-04 | 69 | 63 | 6 | **67** | **7** | T1 @ $50 (73) | **$4,400.00** |
| Bober Markey Fedorovich | 08-21 | **210** | 176 | 34 | **185** | **36** | T2 @ $40 (221) | **$12,800.00** |

---

### 2.6 Catalog retirement - the *Simvay - A1* item group (2026-08-24)

Ryan: *"remove any SKUs for A1 that aren't the new ones."* Halo items are **not deleted** - the
retirement control is **Details → Status**, which offers exactly two values: **Active** and
**Obsolete**. (API: `status: 14` = Active, `status: 15` = Obsolete.) Obsolete items vanish from
the group list and from the item picker on new quotes; the group went from **11 items to 8**
the moment the first three flipped.

| Item | SKU | Action | Why |
|---|---|---|---|
| 73 | `SIM-VULN-T1` | 🚫 Obsolete | superseded by the EP tier table |
| 75 | `SIM-VULN-T3` | 🚫 Obsolete | superseded by the EP tier table |
| 76 | `SIM-VULN-T4` | 🚫 Obsolete | band deleted entirely |
| 202 | `SIMSEC-VULN` | 🚫 Obsolete | legacy, zero-priced |
| 203 | `SIMSEC-VULN-S` | 🚫 Obsolete | legacy, zero-priced |
| 204 | `SIMSEC-VULN-T3` | 🚫 Obsolete | legacy, zero-priced |
| 269 | `ACTION1-1YR` | 🚫 Obsolete | mislabeled *"Managed SentinelOne Agent"*, zero-priced |
| **74** | `SIM-VULN-T2` | ⏳ **left Active** | on BMF's **live** recurring invoice (line 955, inv 20120) |
| **177** | `SIM-SOC-VULN-S` | ⏳ **left Active** | on BMF's **live** recurring invoice (line 954, inv 20120) |
| **72** | `SIM-VULN-S` | ✅ Active | current server SKU |
| **484** | `SIM-VULN-EP` | ✅ Active | current tiered endpoint SKU |

**Retire 74 and 177 after 2026-12-01**, when BMF's contract 49 rolls onto the new quote and the
old recurring invoice lines stop generating. Nothing else in the estate references them -
the other eight live A1 contracts (Fairview Park 66, Monroeville 68, Olmsted Falls 70,
Brooklyn 101, Avon Lake 65, North Royalton 195, Conveyer & Caster 215, Parma Heights 218)
were quoted on the tier SKUs, not on 74/177.

> **Safety note.** Setting an item Obsolete does **not** disturb existing recurring-invoice
> lines - the line stores its own `unit_price`, `item_price` and description, and carries its
> own `isinactive` flag independent of the item record. The 74/177 hold is Ryan's belt-and-braces
> call, not a technical requirement.

---

## 3. Naming & term conventions

- **Opportunity Summary** follows the standard renewal pattern `<ITEM>-MMDDYY-MMDDYY`.
  Action1's item code is **`A1`** → e.g. **`A1-090126-083127`** for a 09/01/2026-08/31/2027 term.
  (Verified against live A1 contract refs: `A1-070725-070628` Olmsted Falls c70,
  `A1-020126-013127` Brooklyn c101, `A1-072326-072227` North Royalton c195,
  `A1-120125-113026` BMF c39.)
- **Derive the renewal term from the expiring contract**, don't guess:
  `get_contracts {client_id, include_expired:true}` → take `end_date`, start the day after.
  BMF's A1 ran 12/01/2025-11/30/2026 → renewal `A1-120126-113027`.
- **Quote Title:** `Vulnerability and Patch Management Renewal (MM/DD/YYYY - MM/DD/YYYY)`.
  (Use "and", not "&" - see §8 gotcha 13.)
- **Expected Close Date:** a few days before term start (8/28/2026 for a 9/1 start;
  11/25/2026 for a 12/1 start).
- ~~Put the Action1 pull date, the raw counts, the WS/server split, the growth allowance and the
  predecessor contract ref in the opportunity **Details** body - it's the audit trail for the
  number. Keep it to one short paragraph (Runbook 13 §4).~~ **SUPERSEDED 2026-08-31 (§1.1):
  Details is client-visible.** Details gets one client-safe sentence (e.g. *"Action1
  Vulnerability and Patch Management renewal, 09/01/2026 - 08/31/2027."*). The pull date,
  counts, split, growth allowance and predecessor ref go in an **Internal Note** on the
  opportunity right after Submit.

> **Note:** Parma Heights, Conveyer & Caster and Olmsted Township had **no prior A1 contract
> record in Halo** (see Renewal Deep-Dive §11, "EMTS clients missing Action1"). These are
> therefore first-time A1 contracts sold as renewals alongside the EMTS book. **BMF is
> different** - it has a real predecessor (`A1-120125-113026`, contract id 49), so 51880-1 is a
> true successor renewal.

---

## 4. Procedure - create the Opportunity

Direct URL for the pipeline: `/tickets?area=13&mainview=myviews&viewid=4&selid=15&sellevel=1`

1. Toolbar **+ New → "New Opportunity"** → URL becomes `...&id=-1`.
2. **Ticket Type defaults to `Lead` - you MUST change it to `Opportunity`.** (Options: Lead,
   Opportunity, Quick Quote.) Leaving it as Lead produces a Lead with a *Register Lead* button
   instead of *Submit*. The dropdown does **not** respond to `form_input` - click the field,
   then click the option row.
3. **Contact details** → click the **Existing Client** radio (the right one; Prospect is default).
4. The **"Search by name or info"** box searches **users, not clients**. A surname works, but
   **the contact's email address is more precise** and returns exactly one row
   (`bsmith@bmf.cpa` → Bryan Smith / Bober Markey Fedorovich / Main). Client + Site + full
   contact block populate from the user. The right-hand "Opportunity details" panel only appears
   after this.
   - Contacts used: Parma Heights → **Michelle Kolesar**; Conveyer & Caster →
     **Clint Svancara**; Olmsted Township → **Gary Yelenosky**; BMF → **Bryan Smith**;
     Olmsted Falls City Schools → **Jeff Hollan** (`jhollan@ofcs.net`, 2026-08-31).
5. **Summary** (top of the right panel) → the `A1-…` reference.
6. **Details** rich-text body → **ONE short client-safe sentence** (§1.1). The sizing
   narrative goes in an **Internal Note** after Submit, not here.
7. **Potential Value** → the annual figure. **Use `find` → ref click on the field before
   typing** - Halo re-zooms once the contact block populates and a coordinate click aimed here
   missed on 51947 (the typed value went to global shortcuts; Runbook 14 §3.5).
8. **Expected Close Date** - **required** (red asterisk). Opens a calendar on the current month.
   For a date months out, use `find` on the month `<select>` and set it with `form_input`
   (it *is* a real select, unlike the Ticket Type combobox), then `find` the day button
   (`"Tuesday, September 15, 2026"`) and click its ref.
9. **Submit**, then wait - the tab title changes to the new ticket id when it lands.

**Auto-advance behaviour (no manual stage clicks needed):**

| Event | Status | Pipeline Stage | Workflow ribbon |
|---|---|---|---|
| After Submit | **Qualified** | **Quoting** | Negotiation |
| After Raise Quote | **Quote Raised** | **Deal Registration** | Negotiation |

---

## 5. Procedure - raise the Quote from the Opportunity

10. On the opportunity, toolbar → **Raise Quote**. Opens *New Quotation* with **Ticket ID
    pre-filled** - this is the link that makes it a proper opportunity-borne quote.
    **Screenshot and confirm the form actually rendered before typing anything** (§8 gotcha 13).
11. **Title** → the quote title.
12. **Set Site = Main** in the right sidebar. It comes in empty, and tax does not compute until
    it is set and the quote is saved (Runbook 15 §5).
13. **Add Item** → picker modal. Type `SIM-VULN` in the **Search…** box and **press Return**
    (it does not search-as-you-type). Five rows return. **Wait for the modal - screenshot first.**
14. **Set Quantity inline on BOTH rows before clicking Select** - the picker adds every row that
    has a quantity in one action. The modal footer echoes the pending selection
    (`…Per Endpoint - 12 Months x 185, …Per Windows Server - 12 Months x 36`) - **read it to
    verify before committing.**
15. **Select** → lines land with correct price/cost/margin. Verify the
    **Recurring Annual equivalent → Total Price** matches the computed annual figure.
16. **Per line (pencil → Edit Line):** **Number of Periods = 1**, **Start date = term start**.
    Billing Period arrives **Yearly** - confirm, don't change.
17. **PDF Template - no action required.** `*Default Template*` is an **inherit pointer to the
    org default**, which is **Simvay Proposal**. See §10.
18. **Save** in the **TOP** toolbar (the bottom Save is the line-table save). You return to the
    opportunity with a `Quotation NNNNN-1 (Draft)` link in the right sidebar.

**Never click Send / Send Quote - leave at Draft** (Runbook 01 §4.6).

**Re-opening the quote later:** `/quotes?quoteid=NNNN` **404s**. Go back to the opportunity
and click the `Quotation NNNNN-1 (Draft)` link in the right sidebar (`find` → `scroll_to` →
click). The opportunity's *Quote* **tab** is not the quote (Runbook 14 §7).

---

## 6. Post-build line settings (Ryan, 2026-08-04)

### 6.1 Billing period = Yearly - already correct, but verify

All five `SIM-VULN` catalog items are `isrecurringitem: true` with
`item_default_billing_period: 3` = **Yearly**, so lines arrive with a ♻ **Year…** badge in the
leftmost **Billing** column. **No edit needed - but confirm it**, because a non-recurring or
unmapped period silently vanishes from the proposal PDF (Runbook 01 gotcha 15).

`Number of Periods` defaults to **0** (= ongoing). The three 2026-08-04 quotes were left at 0;
**51880-1 was set to 1** on both lines to make the single-year term explicit on the record, along
with a Start date. Prefer **1 + Start date** going forward.

### 6.2 Tax code - EXEMPT for public sector, client default for private

**Rule: public-sector clients get tax code `EXEMPT`; private-sector clients keep the
client-default rate.**

- Set **per line**: quote → **Edit** → hover the row → **pencil** → **Tax code** dropdown
  (just below "Item Is Taxable") → **EXEMPT** → dialog **Save**. Repeat per line, then
  **top-toolbar Save**. There is no bulk tax setter.
- Options: Default, No Tax, Sales Tax 20%, CUYAHOGA, **EXEMPT**, LORAIN, OHIO.
- Applied 2026-08-04: **City of Parma Heights** (municipality) and **Olmsted Township**
  (township) → EXEMPT, Total Tax $0.00.
- **Private sector - client default:** Conveyer & Caster resolved to **8%**
  (Westlake / Cuyahoga), Total Tax **$396.00**. **BMF likewise resolves to 8%.**
- **⚠ Standing rule for BMF (Ryan, 2026-08-21): pin `CUYAHOGA` explicitly on EVERY line.**
  Do not leave BMF lines on `Default`. Applied to all four lines across 51879-1 and 51880-1
  on 2026-08-21; verified in the API as `item_tax_name: "CUYAHOGA"`, `override_tax_code: 3`,
  `tax_rate: 8` on each line.
- **`Default` and `CUYAHOGA` produce identical numbers for BMF** - the client record already
  carries `item_tax_code_name` / `service_tax_code_name` / `contract_tax_code_name` /
  `prepay_tax_code_name` = **CUYAHOGA** (`halo_get Client/39`). Pinning changes nothing
  financially; it makes the intent explicit on the line and insulates the quote from a future
  change to the client default. 51880-1 stayed at Total Tax **$1,024.00** through the change,
  51879-1 at **$630.71**.
- Check `halo_get Client/<id>` `item_tax_code` / `*_tax_code_name` before assuming a default.
  **And note the tax column reads $0.00 on an unsaved quote regardless** - save first
  (Runbook 15 §5).

### 6.4 Monthly billing - divide the annual price by 12

**Ryan, 2026-08-24: convert the A1 quote to monthly and split the cost across the months.**
The catalog stays **annual** (QUOTER lists A1 annually); the conversion happens per quote line:

1. Line dialog → **Billing Period → Monthly**
2. **Number of Periods → 12** (12 monthly periods = the 12-month term)
3. **Start date** = term start
4. **Base price = annual ÷ 12**, **Cost = $21.50 ÷ 12 = $1.79**
5. Description → append *"- Billed Monthly (12-Month Term)"* so the PDF is unambiguous

**Rounding rule (Ryan's call 2026-08-24): round the monthly price UP to the cent.** Never
under-bill.

| Annual | ÷12 exact | **Quote at** | Annual after rounding |
|---|---|---|---|
| $50.00 | $4.1667 | **$4.17** | $50.04 |
| $40.00 | $3.3333 | **$3.34** | $40.08 |
| $35.00 | $2.9167 | **$2.92** | $35.04 |
| $25.00 | $2.0833 | **$2.09** | $25.08 |
| $150.00 (server) | $12.50 | **$12.50** | $150.00 exact |

The annual value therefore lands slightly **above** the annual list - BMF: $12,814.80 vs
$12,800.00, +$14.80. That is intended.

### 6.5 ⚠️ Renewal rate parity - check what they paid LAST year

**Standing rule (Ryan, 2026-08-24):** *"make sure their rate matches for endpoints. They are
adding endpoints, so that's where I want the price changes to come from."*

A renewal must not smuggle in a rate increase. Growth in the quote should come **only** from
the endpoint/server count. Before pricing any A1 renewal:

1. `get_contracts {client_id}` → find the expiring `A1-…` contract, note its `id`.
2. `get_invoices {client_id}` → find a recent invoice whose `contract_id` matches.
3. `get_invoice {id}` → read `lines[]`. For each line record `productcode`, `qty_order`,
   `unit_price`, and `_itemid`.
4. Annualize: a monthly line's `unit_price × 12` is the rate to match.

**BMF worked example (invoice 20120, period 7/1/2026-7/31/2026, contract 49):**

| Line | SKU (item) | Qty then | Rate then | Annualized |
|---|---|---|---|---|
| Per Endpoint | `SIM-VULN-T2` (74) | **175** | $3.333/mo | **$40.00/endpoint/yr** |
| Per Server | `SIM-SOC-VULN-S` (177) | **30** | $12.50/mo | **$150.00/server/yr** |

Renewal 51880-1 was built at **$3.34/mo** (the round-up rule from §6.4) - $0.007/mo high, which
is a **rate increase**, however small. Corrected to **$3.333/mo** to match exactly.

> **§6.4's round-up rule is subordinate to this one.** Round up only when there is no prior
> rate to match. On a renewal, **carry the prior line's `unit_price` across verbatim**, decimals
> and all - Halo stores 3 decimal places on quote and invoice lines.

**Resulting BMF delta - 100% volume, 0% rate:**

| | Endpoints | Servers | Monthly | Annual |
|---|---|---|---|---|
| Current (inv 20120) | 175 × $3.333 = $583.28 | 30 × $12.50 = $375.00 | **$958.28** | **$11,499.36** |
| Renewal (51880-1) | 185 × $3.333 = $616.61 | 36 × $12.50 = $450.00 | **$1,066.60** | **$12,799.26** |
| **Increase** | +10 endpoints | +6 servers | **+$108.32** | **+$1,299.90** |

Every dollar of the increase is attributable to +10 endpoints and +6 servers. Bryan Smith can be
told the unit rates did not move.

### 6.3 Leased items - it is a QUOTE-level flag, not per-line

Leasing lives on the **quote**, in the right sidebar **below Billing Account details**:

1. Quote → **Edit** → scroll the right sidebar to the bottom → **Leasing** → tick **Is Leased?**
   (the sidebar does not respond to mouse scroll - use `find` for the checkbox and `scroll_to`
   its ref, then click the ref).
2. Ticking it reveals **Term Limit (In Months)**. Set **12** for a 12-month term.
3. Top-toolbar **Save**. Verify via `halo_get Quotation {client_id}` → `is_leased: true`,
   `term_limit: 12`.

> **⚠ Correction (Runbook 13):** the catalog-item **Edit Line** dialog **does** expose
> `Is a Finance/Leased Item` on **non-recurring** lines. Recurring lines show
> Billing Period / Number of Periods / Start date / Auto Renew instead. Quote level is still the
> right place - one tick covers every line.

---

## 7. Final state

| Client | Date | Opp | Quote | Lines | Annual | Tax |
|---|---|---|---|---|---|---|
| City of Parma Heights | 08-04 | **51641** | **51641-1** | 119 × T2 @ $40 · 6 × S @ $150 | **$5,660.00** | EXEMPT ($0.00) |
| Conveyer & Caster | 08-04 | **51642** | **51642-1** | 69 × T1 @ $50 · 10 × S @ $150 | **$4,950.00** | Default 8% ($396.00) |
| Olmsted Township | 08-04 | **51643** | **51643-1** | 67 × T1 @ $50 · 7 × S @ $150 | **$4,400.00** | EXEMPT ($0.00) |
| Bober Markey Fedorovich | 08-24 | **51880** | **51880-1** | 185 × **EP** @ **$3.333**/mo · 36 × S @ $12.50/mo | **$12,799.26** ($1,066.60/mo) | CUYAHOGA 8% ($1,023.94) |

Cost basis **$21.50**/endpoint/year (was $20.00 through 2026-08-21).
BMF blended margin **62.96%** - monthly revenue $1,066.60, monthly cost $395.59, monthly tax $85.33.
Endpoint rate held at last year's **$3.333/mo = $40.00/yr** per §6.5 - the entire
**+$1,299.90/yr** increase is volume (+10 endpoints, +6 servers), not rate.

**Open items for Ryan:**
- ~~Reconcile the QUOTER↔Halo T4 price ($30 vs $25).~~ **Closed 2026-08-24 - T4 removed
  entirely; no A1 endpoint price below $35 now exists.** Cost reconciled to QUOTER's $21.50.
- **Retire items 74 and 177 after 2026-12-01** when BMF's contract 49 rolls (§2.6).
- Once accepted, enter the successor **contract records**. For BMF: **`A1-120126-113027`**
  succeeding contract id 49.
- ~~BMF stale endpoints / endpoint growth~~ - **closed by Ryan 2026-08-21: "I know he is
  expecting the inflation of endpoints so it's fine."** BMF's A1 book grew to 210 and 9 endpoints
  were last seen >90 days ago (oldest `JBowen2020.bobermarkey.com` at 245 days; also
  `AdminDymo2023`, `TaxDymo2023`, `KWilkinson2022S`, `KWilkinson2021`, `ZSchweda2019`,
  `SBoughton2021`, `CLEServerRoom24`, `CMcLean2025`). All kept in the count per §2.1; Bryan
  Smith is already expecting the increase, so no decommission conversation is needed before
  the quote goes out. **Useful precedent: raise growth with the account owner, but don't hold
  the quote for it - they often already know.**
- **Review the Details body on the four opportunities above** (51641/51642/51643/51880) - they
  were written before the §1.1 rule and carry sizing narrative the client can see. Trim to one
  sentence and move the narrative to an Internal Note.

---

## 8. Gotchas discovered / confirmed

1. **Ticket Type defaults to Lead** on the New Opportunity form - must be switched to
   *Opportunity*. The combobox ignores `form_input`; click the field then the option row.
2. **The contact picker searches users, not clients.** Use the contact's **email address** for
   an exact single hit.
3. **Expected Close Date is mandatory** on the opportunity form.
4. **Opportunity/Pipeline stages auto-advance** on Submit and on Raise Quote - don't hand-drag
   the kanban card.
5. **Item picker needs Return** to search, and **accepts quantities on several rows in one
   pass** - set them all, read the footer summary, then Select once.
6. **`*Default Template*` on a quote is NOT a bug** - it means "inherit the org default", which
   is Simvay Proposal. See §10.
7. **Leasing is quote-level** (§6.3). The right sidebar **does not respond to mouse scroll** -
   use `find` + `scroll_to` on the `Is Leased?` checkbox ref.
8. **Tax must be set line by line**; new lines default to `Default`, which resolves to the
   *client's* configured tax code (not "no tax"). **And it reads $0.00 until the quote is saved
   with a Site set.**
9. ~~`list_endpoints` always overflows the token limit - parse the saved file~~ →
   **superseded, see gotcha 11.**
10. **Chrome tab cap under parallel subagents.** Practical limit: **~1 browser-driving subagent
    at a time** (plus the main session). Run multi-client browser work sequentially.
11. **⚠ `list_endpoints` SILENTLY UNDER-REPORTS.** The saved file is truncated at 500 KB, taking
    `total_items` with it, and `next_page` is ignored (every page returns the first 50). A naive
    record count looks legitimate. **Use the Managed Endpoints report
    (`managed_endpoints_1635942317188`) and assert `len(rows) == total_items`.** See §2.1.
12. **The Halo ticket detail pane will not render from a direct `?area=13&id=NNNNN` URL** in a
    fresh tab - the main pane stays blank no matter how long you wait, and reloading does not
    help. **Click "Pipeline View" in the left nav to load the kanban, then click the card.**
    *(2026-08-31: the full pipeline URL **with** `mainview=myviews&viewid=4&selid=15&sellevel=1&id=51947`
    did render the ticket after ~5 s, so include the view parameters if you deep-link.)*
13. **NEVER type into a Halo form you have not just screenshotted.** If the field is not focused,
    keystrokes hit Halo's **global keyboard shortcuts** - `g`+`h` jumps to Home (losing the
    unsaved form), `?` opens the Keyboard Shortcuts overlay. This ate two attempts at building
    51880-1. The full shortcut map is at `?` - `Esc` closes screens (see Runbook 02 §1's warning),
    `m` focuses the nav, `g`+`<letter>` jumps modules. **Bit again 2026-08-31** inside the
    View/Edit Action dialog: a missed click + `ctrl+a` + typing sent the app to `/home` under the
    dialog. Ref-click the editor and check `document.activeElement.isContentEditable` first.
15. **⚠ Editing an item's Cost SILENTLY RECALCULATES its Price.** Halo holds **Gross Margin**
    fixed and moves Price to match the new Cost. Raising SIM-VULN-T1's cost $20 → $21.50 pushed
    its price $50 → **$53.75** on its own. **Re-enter the Price after every Cost change and
    verify through the API** (`halo_get Item/<id>` → `baseprice`, `costprice`, `markupperc`).
    This applies to quote lines too, not just catalog items.
16. **⚠ Cancel on a line dialog reverts line edits you already "saved" - if the QUOTE has not
    been saved since.** Line edits live in the client-side model until the top-toolbar Save.
    Sequence that bit on 51880-1: set price $3.34 → line Save → reopen to check → **Cancel** →
    price silently back to $40.00, and the quote saved at 185 × $40 × 12 = **$94,200/yr**.
    **Save the quote (top toolbar) after every line edit, before opening any other line dialog** -
    and always re-verify totals through the API after saving.
17. **Tier tables validate on continuous quantities.** 0-99 then 100-249 is a *gap* at 99.5.
    Overlap the boundary (0→100 exclusive, 100→250 exclusive) - see §2.5.
18. **"Raise Quote" clicked on a still-loading opportunity does nothing** and creates no record.
19. **Items are retired via Details → Status → Obsolete, not deleted.** There is no Inactive
    checkbox and no Delete-that-preserves-history. Two values only: Active (`status: 14`) and
    Obsolete (`status: 15`). Obsolete items disappear from the group list and the quote item
    picker but keep every existing quote/invoice/contract reference intact. Reversible - flip
    back to Active if you retire one too early. To *see* them again in the UI, use the **⋯**
    menu → **Show Inactive Items**; via API pass `includeinactive: true`.
20. **The Halo Items module is slow and the item detail pane loads lazily.** A direct
    `…/items?…&itemid=NNN` URL works but can take **20-30 s** to paint, and a click on **Edit**
    fired before it finishes is swallowed silently - you end up staring at the read view
    wondering why nothing happened, or worse, the second click lands on **Save** and reverts.
    **Always screenshot and confirm the Edit/Save button state before the next click.**
    `find` for the *Status combobox* is the reliable readiness probe: if it returns
    "no Status combobox", the edit form is not up yet. Budget ~1 minute per item.
21. **The tier table's row controls only appear on hover** and sit at the far right of the
    table, often off-screen. Hover the row first, then click the pencil - or skip the
    coordinates entirely and `find` the row's Edit button by reference.
22. **Editing tier bands transiently breaks the gap rule, and that is fine.** Halo validates
    only on the item **Save**, not on each row dialog. Safe order when raising breakpoints:
    delete the top band → fix the new top band's Max to blank (unlimited) → work downward.
    Confirm the whole table on screen before hitting the top-toolbar Save.
    Verify with `halo_get Quotation {"ticket_id": NNNNN}` - `record_count: 0` means nothing was
    half-built and it is safe to retry. Screenshot to confirm the New Quotation form appeared
    before proceeding.
23. **Opportunity Details/Summary are client-visible** (§1.1). One sentence, client-safe; audit
    trail in an Internal Note. Fix after Submit via the Opened action's View/Edit Action.

---

## 9. Reusable subagent brief

The prompt that worked supplied: safety rules (no Escape in edit mode, never Send, own tab only),
the ToolSearch one-liner for the Chrome tools, the full target data block (client, contact email,
summary, value, close date, quote title, SKU→quantity map, expected total, **one-sentence
client-safe Details line + separate Internal Note text**), then the
numbered click path of §4-§5, a 3-attempt stop rule, and a compact-JSON return schema. **Add
gotchas 12-14 and 23 to any future brief** - they are the ones that cost the most time.

---

## 10. Investigation - "why didn't the quote template apply?" (2026-08-04)

**Verdict: it did apply. There was no defect.** `*Default Template*` is an **inherit pointer**
(same asterisk convention as `*Default (Sales Order Site)*`), not a concrete navy template.
Because the org default is Simvay Proposal, **every quote already renders branded.**

| Check | Result |
|---|---|
| Org setting - `/config/quotes/settings` → *Default PDF Template for Quotations* | **Simvay Proposal** |
| Client-level override - `halo_get Client/29` → `overridepdftemplatequote` | `-1` (none) |
| Quote 51625-1 (`*Default Template*`) → Preview Print | Renders full Simvay Proposal branding |

- **Config URL:** `/config/quotes/settings`. `/config/quotations` **404s**.
- **Inherit vs pin:** a quote left on `*Default Template*` will **retroactively change** if the
  org default changes. Prefer pinning for quotes already sent to a client.

---

## 11. Worked example - Bober Markey Fedorovich 51880-1 (2026-08-21)

Opportunity **51880** `A1-120126-113027` (client **39**, contact **Bryan Smith**,
`bsmith@bmf.cpa`, site Main, close 11/25/2026, value $12,800.00).
Quote **51880-1**, Draft, expires 11/19/2026, **Is Leased? Yes / Term 12**, both lines
**Monthly / 12 periods / start 12/01/2026**, tax code **CUYAHOGA** pinned on both lines (8%).
Rebuilt 2026-08-24: the endpoint line was replaced with the tiered **`SIM-VULN-EP`** item and
both lines converted to monthly billing.

Sizing (Managed Endpoints report, pulled 2026-08-21):

| | Count | +5% ↑ |
|---|---|---|
| Workstations (Win 11 24H2 ×104, 25H2 ×68, 23H2 ×1, 22H2 ×1; Win 10 22H2 ×2) | 176 | **185** |
| Windows Servers (2022 ×18, 2019 ×14, 2016 ×2) | 34 | **36** |
| **Total** | **210** | **221** → Tier **T2** |

Status split: 141 Connected / 69 Disconnected - all licensed, all counted.

| SKU | Halo item | Qty | Cost/mo | Price/mo | Monthly | Annual |
|---|---|---|---|---|---|---|
| `SIM-VULN-EP` | **484** | 185 | $1.79 | $3.34 | $617.90 | $7,414.80 |
| `SIM-VULN-S` | 72 | 36 | $1.79 | $12.50 | $450.00 | $5,400.00 |

**Monthly $1,067.90 · Annual $12,814.80** · monthly cost $395.59 · **62.96%** · tax $85.43/mo.
Line 2281 auto-priced at $40.00/yr from the tier table on qty 185 before the monthly conversion -
the end-to-end proof that volume tiering works (§2.5).
Predecessor contract `A1-120125-113026` (id 49, 12/01/2025-11/30/2026, user Bryan Smith).

Built alongside the BMF KnowBe4 quote (opportunity 51879 / quote 51879-1) - see **Runbook 15**.
