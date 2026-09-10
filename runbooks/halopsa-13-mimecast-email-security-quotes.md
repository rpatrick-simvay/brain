---
title: "HaloPSA 13: Mimecast email security quotes"
type: runbook
updated: 2026-08-13
tags: [halopsa, quotes, mimecast]
related: [runbooks/halopsa-01-overview, projects/halopsa/STATUS]
source: "HaloPSA Claude Project: claude/HaloPSA-Runbook-13-Mimecast-Email-Security-Quotes.md"
migrated: 2026-09-09
---
> Migrated 2026-09-09 from the HaloPSA Claude Project (`HaloPSA-Runbook-13-Mimecast-Email-Security-Quotes.md`). This file is now the canonical copy; the project doc is frozen. The verbatim original is in `projects/halopsa/archive/project-export-2026-09-09/`. Em and en dashes in prose were replaced per CLAUDE.md; code blocks are untouched. Cross-references were rewritten to brain paths.

# Simvay HaloPSA - Runbook 13: Mimecast Email Security Quotes

> **Purpose:** Sizing, SKU selection, pricing basis and build procedure for a **Mimecast
> Secure Email Gateway** quote (Advanced Protection + Archive add-on + deployment).
>
> **Learned:** 2026-08-13 building City of Fairview Park opportunity **51764** /
> quote **51764-1** (125 mailboxes, 09/01/2026 - 08/31/2027, $20,875.00).
>
> **Instance:** `https://simvay.halopsa.com`
> **Companion runbooks:** 01 (overview), 02 (quote lines/groups/tax), 11 (A1 renewals - the
> opportunity-first procedure in §4-§5 there applies here verbatim).
> **Last updated:** 2026-08-13

---

## 1. QUOTER - Mimecast Email Security block

`QUOTER.xlsx` → **Cyber SKUS** sheet → *Mimecast Email Security* block.
SharePoint: `https://simvay.sharepoint.com/sites/ClientHub/Shared Documents/INTERNAL/QUOTER.xlsx`
(read it with the M365 connector: `sharepoint_search` "QUOTER" → `read_resource` the
`file:///{driveId}/{itemId}` URI - it returns all four sheets as tab-separated text).

| SKU | Product Description | QUOTER Cost | Override Price | Source |
|---|---|---|---|---|
| `SIM-SEG-CP` | Mimecast Critical Protection (Per Mailbox) | $29.64 | - | Ingram Micro |
| `SIM-SEG-AP` | Mimecast Advanced Protection (Per Mailbox) | **$47.52** | - | Ingram Micro |
| `SIM-SEG-365P` | Mimecast 365 Protect (Per Mailbox) | $51.96 | - | Ingram Micro |
| `SIM-SEG-M3RA` | ***RENEWALS ONLY*** Mimecast SEG - M3RA (Per Mailbox) | $61.20 | - | Ingram Micro |
| `SIM-SEG-A1` | Add-On - Mimecast Archive (Per Mailbox) | **$33.48** | - | Ingram Micro |
| `SIM-SEG-AT1` | Add-On - Security Awareness Training / Simulated Phishing (Per Mailbox) | $13.32 | - | Ingram Micro |
| `SIM-SEG-DEPLOY` | Deployment and Configuration of Secure Email Gateway - One-Time | - | **$4,000.00** | Simvay |

**QUOTER footnotes (verbatim):** *"Choose either AP or 365P and add-ons"* and
***"All public sector clients require A1."*** - the archive add-on is not optional for a
municipality/township/school.

**`SIM-SEG-M3RA` is renewals-only.** Check for a prior Mimecast contract before reaching for it
(`halo_get ClientContract {client_id}` and look for a Mimecast/SEG ref). Fairview Park had
none → new business → AP + A1.

## 2. ⚠️ Pricing: QUOTER carries NO Override Price for Mimecast

Unlike the A1 `SIM-VULN` family (Runbook 11 §2.3), the Mimecast rows have a **Cost but no
Override Price**, so the sell price must be derived. **Halo's own Mimecast items disagree with
each other** - the margins baked into the catalog are 20.79%, 23.07%, 30.89%, 40.00% and
40.20% across six items. There is no safe default; **ask before quoting.**

**Rule set by Ryan 2026-08-13: price Mimecast at 40% gross margin** (`price = cost / 0.60`),
which matches `SIM-SEG-PP` (item 399, exactly 40%) and the Cloud Archiving item (item 126,
40.2%).

| SKU | Cost | @ 40% GM | 125 mailboxes |
|---|---|---|---|
| `SIM-SEG-AP` | $47.52 | **$79.20** | $9,900.00/yr |
| `SIM-SEG-A1` | $33.48 | **$55.80** | $6,975.00/yr |

Set **Cost** and **Gross Margin (%) = 40** in the item picker or line dialog and the base price
computes itself - no margin-back-solving needed (contrast Runbook 02 §2).

## 3. ⚠️ Halo catalog data quality - Mimecast items are wrong

Verified 2026-08-13 via `halo_get Item {"search":"SEG","count":60}`:

| Halo item | SKU | Halo price | Halo cost | Problem |
|---|---|---|---|---|
| **332** | `SIM-SEG-AP` | **$0.00** | **$0.00** | Zero-priced. Must override price AND cost on every line. |
| **442** | `SEC-SEG-AP` | $0.00 | $0.00 | Also zero. Duplicate of 332 under the Ingram group. |
| **398** | `SEC-SEG-PP` | $0.00 | $0.00 | Zero-priced duplicate of 399. |
| **126** | `SEC-SEG-A1` | $58.80 | $35.16 | **Only archive item in the catalog** - SKU is `SEC-`, not the QUOTER `SIM-SEG-A1`; cost is stale ($35.16 vs QUOTER $33.48). |
| **334** | `SIM-SEG-DEPLOY` | $0.00 | $0.00 | Zero-priced, and the item **name has `(Fire Department)` baked into it** - it leaks onto the quote line and the client PDF. |
| 131 | `SIM-SEG-CP` | $38.53 | $29.64 | Cost matches QUOTER; priced at cost × 1.30 (23.07% GM), not 40%. |
| 399 | `SIM-SEG-PP` | $98.00 | $58.80 | Clean, exactly 40% GM. |

**Workarounds used on 51764-1 (no catalog edits made):**
- Overrode price + cost inline in the **Add Item** picker before clicking Select.
- Added item 126 for archive, then **retyped the line SKU to `SIM-SEG-A1`** - the line-level
  SKU field is free text, so the QUOTER SKU can appear on the PDF without creating a new
  catalog item.
- Rewrote the deploy line description to strip `(Fire Department)`.

**Open item for Ryan:** correct items 332, 334, 126 (and retire the zero-priced duplicates 442,
398) in the Items module, or every future Mimecast quote repeats this fixup.

## 4. Naming conventions (Ryan, 2026-08-13) - corrects Runbook 11 §3 scope

- **The `<ITEM>-MMDDYY-MMDDYY` summary pattern is for RENEWALS only.** For new business the
  opportunity summary is simply **`<Product> <YYYY>-<YYYY>`** → **`Mimecast 2026-2027`**.
- **Keep the opportunity Details short** - a one-line description ("Mimecast quote for 125
  mailboxes - Advanced Protection plus Cloud Archiving, 12-month term 09/01/2026 - 08/31/2027,
  plus one-time deployment. Tax exempt."). Do **not** paste the full sizing/pricing audit trail
  into the ticket; Runbook 11 §3's "put the maths in the Details body" guidance was rejected
  here.
- Quote title still carries the detail: `QUOTE | Mimecast Email Security - Advanced Protection
  & Archiving (09/01/2026 - 08/31/2027)`.

**Editing these after the fact:** the **Summary** is inline-editable - click the summary text
under the ticket header, `cmd+a`, retype, Tab. The **Details** body becomes the ticket's
**"Opened" action** - hover the action → **`...`** → **View/Edit Action** → **Edit** → edit the
Note rich-text → **Save**.

## 5. Build procedure - deltas from Runbook 11 §4-§5

The opportunity-first flow is unchanged (New Opportunity → Ticket Type **Opportunity** →
Existing Client → surname search → Summary / Details / Potential Value / Expected Close Date →
Submit → **Raise Quote**). Mimecast-specific notes:

1. **Item picker search term: `SEG`** (returns all 11 Mimecast items in one page). `SIM-SEG`
   also works but misses the `SEC-` archive item you need.
2. **Set Price, Cost AND Quantity inline on all three rows, then click Select once** - verified
   again 2026-08-13; the footer echoed all three pending lines correctly.
3. **Per line (pencil → Edit Line):** tax code **EXEMPT**, description scrubbed and suffixed
   `- 12 Months`, **Number of Periods = 1** on each Yearly line, **Start date = 09/01/2026**.
   Recurring lines arrive **Billing Period: Yearly** already (`item_default_billing_period: 3`)
   confirm, don't change.
4. **Quote-level Leasing:** right sidebar bottom → **Is Leased?** ✓ → **Term Limit = 12**.
   Confirmed persisted via the API: `is_leased: true`, `term_limit: 12`.
5. **PDF template:** the org default is now Simvay Proposal (Ryan, 2026-08-13), so
   `*Default Template*` renders branded and **no action is needed** - pinning is optional
   belt-and-braces only (Runbook 11 §10).

### ⚠️ Correction to Runbook 02 §2 / Runbook 11 §6.3

The catalog-item **Edit Line** dialog **does expose `Is a Finance/Leased Item`** - seen on the
**non-recurring** deploy line (item 334) on quote 51764-1. The earlier claim that no
catalog-item line has this field was based only on *recurring* lines. Recurring lines show
Billing Period / Number of Periods / Start date / Auto Renew instead. **Leasing is still best
set at quote level** - one tick covers every line.

## 6. Worked example - City of Fairview Park 51764-1 (2026-08-13)

Opportunity **51764** "Mimecast 2026-2027" (client 19, contact **Henry Chaski**, Executive
Assistant / Mayor's Office). Quote **51764-1**, Draft, Simvay Proposal, expires 11/11/2026,
**Is Leased? Yes / Term 12**, all lines **EXEMPT**.

| SKU | Description | Qty | Cost | Price | Net |
|---|---|---|---|---|---|
| `SIM-SEG-DEPLOY` | Deployment and Configuration of Secure Email Gateway - One-Time | 1 | $0.00 | $4,000.00 | $4,000.00 one-time |
| `SIM-SEG-A1` | Mimecast Add-On - Cloud Archiving (Per Mailbox) - 12 Months | 125 | $33.48 | $55.80 | $6,975.00/yr |
| `SIM-SEG-AP` | Mimecast Advanced Protection (Per Mailbox) - 12 Months | 125 | $47.52 | $79.20 | $9,900.00/yr |

**Annual recurring $16,875.00** (cost $10,125.00, margin 40.00%) · **One-time $4,000.00** ·
**Tax $0.00** · **TOTAL incl. tax $20,875.00** · profit $10,750.00 / 51.50% year-one margin.
PDF verified: ONE-TIME COSTS and ANNUAL RECURRING COSTS sections both render, teal gradient
total bar shows $20,875.00.

**Tax:** client 19 already carries `item/service/contract/prepay_tax_code_name = EXEMPT`, so
`Default` would have resolved to exempt anyway - set explicitly per Runbook 11 §6.2.

**Follow-ups for Ryan:**
- Fix the Halo Mimecast catalog items listed in §3.
- On acceptance, create the contract record (suggested ref `MIM-090126-083127`) - Fairview Park
  currently has EMTS, EMTS-EXP, FISM, S1, A1, DUO, SRM and M365-INTUNE contracts but no
  Mimecast record.
- Decide whether 40% GM is the standing Mimecast rule or was a one-off for this deal.
