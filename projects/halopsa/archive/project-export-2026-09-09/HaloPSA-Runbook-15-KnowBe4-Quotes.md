# Simvay HaloPSA — Runbook 15: KnowBe4 Security Awareness Training Quotes

> **Purpose:** How to turn a KnowBe4 partner quote into a Simvay HaloPSA quote — pricing basis,
> which catalog item to use, and the build deltas from the opportunity-first procedure.
>
> **Learned:** 2026-08-21 building Bober Markey Fedorovich opportunity **51879** /
> quote **51879-1** (130 users, 09/01/2026 – 08/31/2027, $7,883.90/yr).
>
> **Instance:** `https://simvay.halopsa.com`
> **Companion runbooks:** 01 (overview), 02 (quote lines/groups/tax), 11 (opportunity-first
> procedure §4–§5 applies verbatim), 13 (Mimecast — the same "derive the sell price" problem).
> **Last updated:** 2026-08-21 (§5 — BMF lines pinned to `CUYAHOGA`)

---

## 1. ⚠️ QUOTER has NO KnowBe4 block

`QUOTER.xlsx` → **Cyber SKUS** sheet contains only three blocks: *Managed Detection and Response
S1*, *Risk Based Managed Patching A1*, and *Mimecast Email Security*. **There is no KnowBe4
row.** Verified 2026-08-21 by reading all four sheets via the M365 connector
(`sharepoint_search` "QUOTER" → `read_resource` the `file:///{driveId}/{itemId}` URI).

So, exactly as with Mimecast (Runbook 13 §2), the sell price must be **derived from the partner
cost on the KnowBe4 quote** — and the Halo catalog cannot be trusted to supply it (§2).

**Rule set by Ryan 2026-08-21: price KnowBe4 at 40% gross margin** (`price = cost / 0.60`),
the same rule already standing for Mimecast.

| Input | Value |
|---|---|
| KnowBe4 partner price (quote Q-1677396) | $30.62 / user / year |
| KnowBe4 list price on the same quote | $38.28 (20% partner program discount) |
| Simvay sell @ 40% GM | **$51.03 / user / year** |

## 2. ⚠️ Halo's KnowBe4 catalog is unusable as-is

`halo_get Item {"search":"KnowBe4","count":60}` returns **27 items**. Findings 2026-08-21:

- **None of them carry a SKU field value** that matches a KnowBe4 part number in a usable way —
  the picker's SKU column shows vendor-ish strings (`KSATD-N-C12`, `KMSATD-N-C12-G`,
  `PHISHER PLUS-NB12`) that do not correspond to the part numbers KnowBe4 puts on quotes today.
- **Names are truncated** in the API/picker (`KnowBe4 Security Awareness Training Subscription D`).
- **Every one is "Diamond"**, not the Advanced (SATA) tier KnowBe4 now sells.
- **Margins are all over the place**: 20.79%, 23.07%, 28.5%, 30%, 40%.
- Several are **zero-priced** (ids 83, 233, 234, 235, 350, 351, 371, 231, 337).
- **Billing period is inconsistent**: ids 77–92 are `item_default_billing_period: 2` (Monthly);
  ids 231–235, 349–351, 93, 94 are `3` (Yearly). **Pick a Yearly one** or the line lands in the
  wrong PDF section (Runbook 02 §6).

**The item to use: id 233 `KnowBe4 Security Awareness Training Subscription`.** It is generic
(no tier baked into the name), recurring, **Yearly**, and **zero-priced/zero-cost** — which is a
feature here, not a bug: nothing stale to fight, you type both numbers in the picker.

**The management item: id 94 `KnowBe4 Platform Management`** — $1,250.00, recurring **Yearly**,
Simvay supplier, SKU `SIM-SECTRAINING`. There is also id 93 *Platform Administration* at
$2,000.00/yr. Ryan chose **Platform Management ($1,250)** on 51879-1.

> **⚠️ Item 94 arrives with cost = price ($1,250) in the picker.** The inline Cost cell in the
> Add Item picker **did not take** an edit (typed 0, still showed 1250 on the footer commit).
> Fix it after adding: row pencil → **Cost = 0** → Tab (Base price stays 1250 because the margin
> recalc can't fire off a zero cost) → dialog Save. Profit% then reads 100%.

**Open item for Ryan:** the KnowBe4 item group deserves the same cleanup as the Mimecast one
(Runbook 13 §3) — retire the zero-priced and Monthly duplicates, add a correctly-SKU'd Advanced
(SATA) item, or every KnowBe4 quote repeats this fixup.

## 3. Naming (new business, per Runbook 13 §4)

- **Opportunity Summary:** `KnowBe4 <YYYY>-<YYYY>` → **`KnowBe4 2026-2027`**.
  (The `<ITEM>-MMDDYY-MMDDYY` pattern is for **renewals only**. Check
  `get_contracts client_id=<id>` for a prior KnowBe4/SAT contract before assuming.)
- **Details** — one short paragraph, not the full pricing audit trail. Include the KnowBe4 quote
  number so the cost basis is traceable: *"…Based on KnowBe4 partner quote Q-1677396."*
- **Quote Title:** `QUOTE | KnowBe4 Security Awareness Training - Advanced (MM/DD/YYYY - MM/DD/YYYY)`.
- **Expected Close Date:** a few days before term start (8/28/2026 for a 9/1 start).

## 4. Build deltas from Runbook 11 §4–§5

The opportunity-first flow is unchanged. KnowBe4-specific notes:

1. **Item picker search term: `KnowBe4`** — returns all 27 in one page (`1-27 of 27`).
2. Set **Price, Cost and Quantity inline** on the id-233 row (51.03 / 30.62 / 130) and
   **Quantity 1** on the id-94 row, then **Select once**. Read the footer echo:
   `KnowBe4 Security Awareness Training Subscription x 130, KnowBe4 Platform Management x 1`.
3. **Per line (pencil → Edit Line):**
   - Line 1 description → `KnowBe4 Security Awareness Training Subscription - Advanced (Per User) - 12 Months`;
     **SKU field is free text** → retype it to the KnowBe4 part number **`HRMSATA-N-C12`** so the
     PDF carries the real SKU without creating a catalog item (same trick as Runbook 13 §3).
   - Line 2 description → `KnowBe4 Platform Management - Simvay Managed Administration - 12 Months`;
     **Cost → 0**.
   - Both: **Number of Periods = 1**, **Start date = 09/01/2026**. Billing Period arrives
     **Yearly** already — confirm, don't change.
   - **Do not tab out of Gross Margin (%)** on line 1. It displayed `30` even though the line's
     true margin is 40% (price 51.03 / cost 30.62); tabbing out would recalculate Base price off
     that wrong figure. Price and cost are what matter — the line grid's Profit % column read the
     correct **40%**.
4. **Site** — the New Quotation form comes in with **Site: Select…** (empty). **Set it to Main
   before saving.** See §5.
5. **Quote-level Leasing:** right sidebar bottom → **Is Leased?** ✓ → **Term Limit = 12**.
   Confirmed persisted via the API: `is_leased: true, term_limit: 12`.
6. **PDF template** `*Default Template*` = inherit → Simvay Proposal. No action (Runbook 11 §10).
7. **Never click Send Quote — leave at Draft.**

## 5. ⚠️ Tax appears only after the Site is set

On the **New Quotation** form (before the first Save) the Tax column read **$0.00** on both
lines. After setting **Site = Main** and saving, tax recomputed to the client default:

| Line | Per-unit tax | Line tax |
|---|---|---|
| SAT subscription $51.03 × 130 | $4.08 | $530.71 |
| Platform Management $1,250.00 × 1 | $100.00 | $100.00 |
| | | **Total Tax $630.71** |

That is **8%** — BMF's client default (`item_tax_code: 3`, which resolves to **CUYAHOGA**).

> **⚠ Standing rule for BMF (Ryan, 2026-08-21): pin the tax code `CUYAHOGA` on EVERY line.**
> Do not leave BMF lines on `Default`. Applied to both lines of 51879-1 on 2026-08-21 and
> verified in the API (`item_tax_name: "CUYAHOGA"`, `override_tax_code: 3`, `tax_rate: 8`).
> The numbers are unchanged — the BMF client record already carries CUYAHOGA on all four tax
> code fields, so `Default` was resolving there anyway. Pinning makes the intent visible on the
> line and insulates the quote from a future change to the client default.
> Tax stayed **$630.71** through the change. Ryan confirmed the 8% is correct, closing the
> earlier open question about Ohio treatment of a SaaS training subscription.

**Do not read a $0.00 tax column on an unsaved quote as "this client is exempt."** Save first,
then check. `halo_get Client/<id>` and look at `item_tax_code` / `*_tax_code_name` if in doubt.

## 6. Worked example — Bober Markey Fedorovich 51879-1 (2026-08-21)

Opportunity **51879** "KnowBe4 2026-2027" (client **39**, contact **Bryan Smith**,
`bsmith@bmf.cpa`, site Main). Quote **51879-1**, Draft, expires 11/19/2026,
**Is Leased? Yes / Term 12**, both lines Yearly / Periods 1 / start 09/01/2026.
Source document: KnowBe4 partner quote **Q-1677396** (created 8/19/2026, expires 8/31/2026,
prepared by Jeff Garner, reseller Simvay LLC, end user BMF / Bryan Smith, Net 30).

| Halo item | SKU on line | Description | Qty | Cost | Price | Annual |
|---|---|---|---|---|---|---|
| 233 | `HRMSATA-N-C12` | KnowBe4 Security Awareness Training Subscription - Advanced (Per User) - 12 Months | 130 | $30.62 | $51.03 | $6,633.90 |
| 94 | `SIM-SECTRAINING` | KnowBe4 Platform Management - Simvay Managed Administration - 12 Months | 1 | $0.00 | $1,250.00 | $1,250.00 |

**Annual recurring $7,883.90** · cost **$3,980.60** · profit **$3,903.30** · **49.51%** ·
Tax **$630.71** (tax code **CUYAHOGA** pinned on both lines, 8%).

**Follow-ups for Ryan:**
- On acceptance, create the contract record — suggested ref **`KB4-090126-083127`**. BMF
  currently holds only `S1-120125-113026` and `A1-120125-113026`; there is no KnowBe4 contract.
- Decide whether 40% GM is the standing KnowBe4 rule or was a one-off for this deal (same open
  question Runbook 13 leaves for Mimecast).
- Clean up the KnowBe4 item group (§2).
