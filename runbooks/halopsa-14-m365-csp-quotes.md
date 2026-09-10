---
title: "HaloPSA 14: Microsoft 365 CSP licensing quotes"
type: runbook
updated: 2026-08-31
tags: [halopsa, quotes, m365]
related: [runbooks/halopsa-01-overview, projects/halopsa/STATUS]
source: "HaloPSA Claude Project: claude/HaloPSA-Runbook-14-M365-CSP-Quotes.md"
migrated: 2026-09-09
---
> Migrated 2026-09-09 from the HaloPSA Claude Project (`HaloPSA-Runbook-14-M365-CSP-Quotes.md`). This file is now the canonical copy; the project doc is frozen. The verbatim original is in `projects/halopsa/archive/project-export-2026-09-09/`. Em and en dashes in prose were replaced per CLAUDE.md; code blocks are untouched. Cross-references were rewritten to brain paths.

# Simvay HaloPSA - Runbook 14: Microsoft 365 CSP Licensing Quotes

> **Purpose:** Building a **Microsoft 365 CSP** (NCE) licensing quote - item selection,
> pricing basis, and the browser mechanics that make a 6+ line quote survivable.
>
> **Learned:** 2026-08-13 building City of Fairview Park opportunity **51765** /
> quote **51765-1** (110 seats + Entra/Intune add-ons, 10/09/2026 - 10/08/2027, $10,896.00/yr).
> Extended 2026-08-31 with Olmsted Falls City Schools **51947 / 51947-1** (single Entra ID P2
> line raised to satisfy a Cyber Ops service ticket - §6).
>
> **Instance:** `https://simvay.halopsa.com`
> **Companion runbooks:** 11 (opportunity-first procedure §4-§5 applies verbatim),
> 13 (Mimecast - naming conventions in §4 there apply here too), 02 (quote lines).
> **Last updated:** 2026-08-31 (§0 **client-visible Details rule**, §6 worked example,
> §7 new gotchas - quote deep-link URL, editing Details after Submit, ticket-borne quotes)

---

## 0. ⚠️ STANDING RULE (Ryan, 2026-08-31): the opportunity Details field is CLIENT-VISIBLE

**The opportunity's Details body (and its Summary) show to the client on the portal / in
emails. Keep them short and client-safe.** No internal pricing basis, no cost/margin talk, no
"priced per quote NNNNN-1", no "public sector - tax exempt", no SOC narrative about their
tenant, no contact-name annotations.

- **Good Details:** `Quote for 1 x Microsoft Entra ID P2 license (annual subscription), per
  ticket 50822.`
- **Bad Details (what 51947 was first written with, then trimmed):** a paragraph covering the
  device-code-flow attack pattern, the license requirement, list-price basis, the reference
  quote used for pricing, tax status and contact name.

**Where the audit trail goes instead:** an **Internal Note** on the opportunity (toolbar
*Internal Note*, hidden from user), or the quote's **Internal Notes** tab. Runbook 11 §3/§4 step
6 ("sizing narrative in the Details body") is **superseded** for the client-facing part - put the
counts/pull-date/predecessor-ref in an Internal Note.

**Fixing Details after Submit:** there is no Edit button for ticket details on the opportunity
header. Path that works: hover the **Opened** action card → its **⋯ More options** →
**View/Edit Action** → dialog **Edit** (top-left) → replace the **Note** rich-text → dialog
**Save**. The ticket `details` field updates (verified via `Tickets/51947`), and the card shows
an *Edited* tag.

## 1. The catalog is CLEAN here - unlike Mimecast

**M365 is the easy case.** The `(NCE)` items carry Microsoft **list price** with cost already
loaded at the partner rate, giving a consistent **~12.8% gross margin** across the family. No
price or cost overrides are needed - add the item, set quantity, done.

| Halo item | Name | SKU | Price | Cost | GM |
|---|---|---|---|---|---|
| **52** | (NCE) Microsoft 365 Business Basic | `CFQ7TTC0LH18:0001:Commercial` | $72.00 | $62.76 | 12.83% |
| **48** | (NCE) Microsoft 365 Business Standard | `CFQ7TTC0LDPB:0001:Commercial` | $150.00 | $130.92 | 12.72% |
| 53 | (NCE) Microsoft 365 Business Premium | `CFQ7TTC0LCHC:0002` | $264.00 | $241.80 | 12.80% |
| **54** | (NCE) Microsoft Entra ID P1 | `CFQ7TTC0LFLS:0002:Commercial` | $72.00 | $62.76 | 12.83% |
| **55** | (NCE) Microsoft Entra ID P2 | `CFQ7TTC0LFK5:0001:Commercial` | $108.00 | $94.20 | 12.78% |
| **209** | (NCE) Microsoft Intune Plan 1 | `CFQ7TTC0LCH4:0009:Commercial` | $96.00 | $83.76 | 12.75% |
| **56** | (NCE) Microsoft Intune Plan 2 | `CFQ7TTC0RP76:0002` | $48.00 | $41.88 | 12.75% |

All are `isrecurringitem: true` with `item_default_billing_period: 3` (**Yearly**) - lines
arrive with the ♻ Year badge already correct.

**Pricing rule (Ryan, 2026-08-13): sell M365 CSP at Microsoft list** - i.e. take the Halo
catalog price unchanged. The 12.8% is the Microsoft partner margin. Do **not** apply the 40%
Mimecast rule (Runbook 13 §2) to M365. Re-confirmed 2026-08-31: item 55 still $108.00/$94.20,
identical to line 2210 on 51765-1 - "use a recent quote for the exact pricing" resolves to the
catalog price.

**⚠ Zero-priced decoys to avoid** - these return in the same searches and would silently quote
$0.00: items **230**, **254** (Business Standard), **214** (Business Basic), **226**, **228**,
**223**, **225** (Intune), **224** (M365 Apps), **216**, **256**. Rule of thumb: the correct
NCE items show a **red/orange item icon** and a `CFQ7TTC…` SKU; the zero-priced ones show a
grey box icon and an `M365-…`-style internal reference.

**⚠ Duplicate Intune Plan 2:** items **56** and **210** both carry SKU `CFQ7TTC0RP76:0002` at
$48.00/$41.88. Use **56** (named "Plan 2", matching "Plan 1" = 209). Worth de-duplicating.

**Legacy monthly items:** items 15/16 ("Microsoft 365 Business Basic/Standard", no `(NCE)`
prefix) are old monthly-priced records - item 15 is priced **below cost** ($3.50 vs $5.00).
Ignore them.

## 2. Item picker - three passes, not one

`Add Item` search is name-based, so one search can't reach every item:

| Pass | Search term | Rows to set |
|---|---|---|
| 1 | `(NCE) Microsoft 365 Business` | Basic × qty, Standard × qty |
| 2 | *(blank - full list)* | Entra ID P1 × 1, Entra ID P2 × 1 |
| 3 | `Intune Plan` | Plan 1 × 1, Plan 2 × 1 |

Set quantities on every row in a pass, **read the footer summary**, then click **Select** once.
Prices need no editing.

**Single-line shortcut (2026-08-31):** the unfiltered picker opens sorted by name with the
whole `(NCE)` family on page 1 of 471, so for one Entra/Intune line you don't need to search
at all - `find "Quantity input on the row for item 00000055"` → click ref → type `1` → footer
reads `(NCE) Microsoft Entra ID P2 ( Microsoft ) x 1` → Select.

## 3. ⚠️ Browser mechanics - the part that actually costs time

Six lines means six `Edit Line` dialogs. Three hazards, all hit on 51765-1:

### 3.1 The collapsed table viewport

After each dialog save the lines table often re-renders **one row tall** with its own inner
scrollbar, so the next row is invisible. Mouse-scrolling inside it jumps ~2 rows and silently
skips lines.

**Reliable pattern - use `find` + `scroll_to` per line, never blind scrolling:**

```
find "table row (NCE) Microsoft Entra ID P2"  → ref
scroll_to ref                                  → row lands at y≈389
hover (900, y) → click pencil at (1152, y)
```

A **taller browser window helps enormously**: after `resize_window 1680×1100` on a *fresh* tab
all six rows rendered at once (y = 399/438/477/516/555/593). Resizing an existing window did
not re-flow the table - open a new tab, size it, then load the quote.

**Even better (2026-08-31): skip coordinates entirely.** `hover` anywhere on the row, then
`find "edit (pencil) button on the <item> quote line row"` returns the pencil as a ref - click
the ref. Same for the Add Item quantity cell, Tax code combobox, EXEMPT option, Number of
Periods input, `Is Leased?` checkbox, Term Limit input and both Save buttons. Zero
coordinate clicks were needed to build 51947-1.

### 3.2 Prefer `form_input` over clicking date/number widgets

The date picker's forward arrow **swallows rapid successive clicks** (two clicks advanced one
month). The month `<select>` is a real dropdown - `find` it and use `form_input` with the month
name, then click the day. Same for `Number of Periods`: `form_input` sets it in one call.

### 3.3 ⚠️ CRITICAL: never keep a second Halo tab open

Clicks issued to the working tab **also landed in a second open tab** in the same group, which
drifted onto unrelated opportunities and got as far as opening a *New Quotation* form on
someone else's opportunity (50487). Nothing was saved, but it easily could have been.

**Rule: run browser work in exactly ONE tab.** If a second tab exists, close it *before*
starting line edits - and note that `tabs_close_mcp` on the other tab can **dissolve the whole
tab group**, killing your working tab too (it did here). Recovery: `tabs_context_mcp
{createIfEmpty:true}` → re-navigate → re-open the quote. Line edits already dialog-saved
persist; the in-flight dialog is lost.

### 3.4 Bulk "Update All Line Values" - looks useful, isn't

The toolbar's **Update All Line Values** opens an *Edit Line* dialog with a **Field** picker
that DOES include **Tax code** - tempting for setting EXEMPT on six lines at once, and it
contradicts Runbook 02 §5's "there's no bulk tax setter". **But the Field combobox reassigns
itself on a stray click** - one click landed on `Gross Margin (%)`, which applied to all lines
would have overwritten every price. **Cancelled and did it per line.** Only use this if you can
confirm the selected field immediately before saving.

### 3.5 Screenshot-to-click scale drift (Windows Chrome too, 2026-08-31)

Runbook 09 §11.15 documented ~1.1× drift on the Mac extension. **It happens on Windows as
well** once Halo re-zooms after a form loads: the screenshot came back 1495×822 while
`read_page` reported a 1664×915 viewport. A coordinate click aimed at *Potential Value* missed
and the typed `108` went to global shortcuts. **Use `find` → ref clicks for every input**;
reserve coordinate clicks for "click somewhere neutral to close a menu".

## 4. Per-line settings (same standing rules as Runbooks 11/13)

For each line: **Tax code EXEMPT** (public sector), **Number of Periods = 1**,
**Start date = term start** (or **blank** when the client hasn't committed to a start - Ryan's
call for 51947-1; the term is set when the order is processed). Billing Period arrives
**Yearly** - verify, don't change. Quote level: **Is Leased? ✓ / Term Limit 12**.

**Verify through the API, not the screen** - `get_quote {id}` then check per line:

```python
{'billingperiod': 3, 'line_periods': 1}   # 3 = Yearly, line_periods = Number of Periods
override_tax_code: 4                       # 4 = EXEMPT
startdate: '2026-10-09T00:00:00'           # or '1899-12-30T00:00:00' when left blank
is_leased: True, term_limit: 12            # quote level
```

Note the field names: **`line_periods`** (not `number_of_periods`) and
**`override_tax_code`** (not `tax_code`).

**Tax-code note for OFCS (client 37):** the client record already carries
`item_tax_code: 4` / `item_tax_code_name: EXEMPT` (likewise service/prepay/contract), so
`Default` would have resolved to EXEMPT anyway. Pin EXEMPT explicitly regardless - same
reasoning as the BMF CUYAHOGA rule in Runbook 11 §6.2.

## 5. Worked example - City of Fairview Park 51765-1 (2026-08-13)

Opportunity **51765** "M365 2026-2027" (client 19, contact **Henry Chaski**). Quote
**51765-1**, Draft, term **10/09/2026 - 10/08/2027**, all lines EXEMPT / Yearly / periods 1 /
start 10/09/2026, **Is Leased? Yes / Term 12**, expires 11/11/2026.

| SKU | Line | Qty | Cost | Price | Annual |
|---|---|---|---|---|---|
| `CFQ7TTC0LH18:0001` | (NCE) Microsoft 365 Business Basic | 76 | $62.76 | $72.00 | $5,472.00 |
| `CFQ7TTC0LDPB:0001` | (NCE) Microsoft 365 Business Standard | 34 | $130.92 | $150.00 | $5,100.00 |
| `CFQ7TTC0LFLS:0002` | (NCE) Microsoft Entra ID P1 | 1 | $62.76 | $72.00 | $72.00 |
| `CFQ7TTC0LFK5:0001` | (NCE) Microsoft Entra ID P2 | 1 | $94.20 | $108.00 | $108.00 |
| `CFQ7TTC0LCH4:0009` | (NCE) Microsoft Intune Plan 1 | 1 | $83.76 | $96.00 | $96.00 |
| `CFQ7TTC0RP76:0002` | (NCE) Microsoft Intune Plan 2 | 1 | $41.88 | $48.00 | $48.00 |

**Total $10,896.00/yr** · cost $9,503.64 · profit $1,392.36 · margin **12.78%** · Tax **$0.00**.
PDF verified: single **ANNUAL RECURRING COSTS** section, all six SKUs, gradient
`TOTAL · incl. tax $10,896.00` bar, signature row (Ryan Patrick / Henry Chaski).

**Follow-ups for Ryan:**
- De-duplicate Intune Plan 2 (items 56 vs 210) and retire the zero-priced NCE decoys in §1.
- On acceptance, create the contract record (existing M365 ref pattern:
  `M365-INTUNE-062226-062127`, so e.g. `M365-100926-100827`).
- Auto Renew is inconsistent across these lines (checked on some, unchecked on others) - the
  flag was not part of the brief; decide the house default.

## 6. Worked example - Olmsted Falls City Schools 51947-1 (2026-08-31): a quote to satisfy a SERVICE ticket

**Trigger:** Cyber Ops ticket **50822** "Review | Device Code Flow" (type Event, team Cyber Ops
(Analysts), client **37** Olmsted Falls City Schools, contact **Jeff Hollan**
`jhollan@ofcs.net`). Ryan had told Jeff on 06-17 that mitigating device-code-flow auth needs at
least one Entra ID P2 license; Jeff bumped the ticket on 08-06 still waiting on the quote.

**Ryan's decisions:** raise it from a **new Opportunity** (not directly off the service ticket -
the opportunity-first rule in Runbook 11 §1 holds even when the ask originates in a service
ticket); **leave the line Start date blank**; tax **EXEMPT** (public school district).

| Field | Value |
|---|---|
| Opportunity | **51947**, type Opportunity, Existing Client via `jhollan@ofcs.net`, client 37 / site Main |
| Summary | `Microsoft Entra ID P2 License (Qty 1) - Device Code Flow Mitigation` |
| Details | `Quote for 1 x Microsoft Entra ID P2 license (annual subscription), per ticket 50822.` (trimmed per §0) |
| Potential Value / Close | $108 / 09/15/2026 |
| Quote | **51947-1** (internal id **10280**), Draft, expires 11/29/2026, PDF template resolves to Simvay Proposal |
| Title | `QUOTE \| Microsoft Entra ID P2 License \| 1 Year` |
| Line 2308 | item **55** `CFQ7TTC0LFK5:0001:Commercial` × 1 · $108.00 / $94.20 · **EXEMPT** (`override_tax_code 4`) · Yearly (`billingperiod 3`) · `line_periods 1` · start blank · Auto Renew ✓ (item default) |
| Quote level | `is_leased: true`, `term_limit: 12`, Site Main, tax $0.00 |

**Total $108.00/yr** · profit $13.80 · margin 12.78%. Status auto-advanced Qualified → Quote
Raised on Save. **Not sent** - Draft, per Runbook 01 §4.6.

**Still to do (Ryan):** send 51947-1 to Jeff (or attach the PDF to ticket 50822 and reply
there), and relate opportunity 51947 to ticket 50822 (`⋯ → Relate to another Ticket`) so the
service ticket shows the quote link.

## 7. Gotchas (added 2026-08-31)

1. **`/quotes?quoteid=NNNN` 404s.** The connector's `quoteid=` hint is not a UI route. Open a
   quote through the opportunity: **right sidebar → Quotes, Orders & Invoices →
   `Quotation NNNNN-1 (Draft)`** (`find` it, `scroll_to`, click). The opportunity's **Quote
   tab** is *not* the quote - it shows project-task settings.
2. **The opportunity header has no Edit-details button.** The toolbar icons right of the logo
   are Previous / Open in new window / Next / Follow / Share / Agreements / ⋯, and ⋯ has no
   Edit either. Edit Details via the **Opened action → View/Edit Action → Edit** (§0).
3. **Global-shortcut trap, again (Runbook 11 §8 gotcha 13).** A coordinate click that missed
   the Froala editor left focus on the dialog body; `ctrl+a` selected the whole page and the
   typed sentence fired `g`+`h` → the app navigated to `/home` **underneath the still-open
   dialog**. The dialog survived: `find "Note rich text editor contenteditable"` → click ref →
   confirm `document.activeElement.isContentEditable` via `javascript_tool` → `ctrl+a` → type →
   Save worked and persisted. **Always ref-click the editor and verify focus before typing.**
4. **Site must be set on the New Quotation form** (comes in empty - Runbook 15 §5); it is a
   react-select: click the combobox ref, then `find` the `Main` option and click it.
5. **Halo re-zooms after the opportunity form loads** (screenshot 1338×896 → 1495×822 mid-form).
   See §3.5 - ref clicks only.
