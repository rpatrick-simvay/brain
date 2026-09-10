# Simvay HaloPSA — Runbook 15: SentinelOne / SOC Quotes & Multi-Year Options

> **Purpose:** How Simvay's SentinelOne + Managed SOC quotes are structured in Halo, and how to
> spin a **multi-year option** off an existing single-year quote without rebuilding it.
>
> **Learned:** 2026-08-21 building the Avon Local Schools 3-year option
> (opportunity **50894**, quote **50894-2**) from Carahsoft quote **66843121** (08/11/2026),
> alongside the existing FY27 single-year quote **50894-1**.
>
> **Instance:** `https://simvay.halopsa.com`
> **Companion runbooks:** 01 (overview), 02 (quote lines/groups/tax), 11 (A1 renewals).
> **Last updated:** 2026-08-21

---

## 1. How a SentinelOne/SOC quote is structured

The Avon FY27 quote (50894-1) is the reference shape. **The SentinelOne licence lines carry
COST ONLY (price $0.00); all client-facing revenue sits on the Simvay SOC lines.**

| Seq | Group / Line | Item | Qty | Price | Cost |
|---|---|---|---|---|---|
| 10 | *group* **SentinelOne Product** | — | — | — | — |
| 20 | Singularity Commercial (Per Server) - 12 months · `S1-SCM-CW-S1` | 428 | 16 | $0.00 | Carahsoft unit cost |
| 30 | Singularity Commercial (Per Endpoint) - 12 months · `S1-SCM-EN-S1` | 429 | 550 | $0.00 | Carahsoft unit cost |
| 40 | *group* **Managed Security Services** | — | — | — | — |
| 50 | SOC - AI SIEM Per Endpoint - 12 Months · `SIM-SOC-MSIEM-T3` | 65 | 566 | $110.00 | 0 |
| 60 | Add-On - SOC Identity Detection & Response Per User · `SIM-SOC-IDR-T2` | 187 | 550 | $22.00 | 0 |
| 70 | Add-On - Simvay Threat Intelligence Ingestion · `SIM-SOC-TI` | 62 | 1 | $0.00 | 0 |
| 80 | DISCOUNT - Security Services - Per Endpoint (EDU2) · `DISCOUNT - EDU` | 66 | 566 | **-$42.00** | 0 |
| 90 | *group* **Onboarding** | — | — | — | — |
| 100 | SOC - Deployment Support for Identity - One-Time · `SIM-SOC-DEPLOY` | 69 | 1 | $1,500.00 | 0 |

Notes:

- **Endpoint counts differ by line on purpose:** 550 licensed workstations + 16 servers = **566**
  for the per-endpoint SOC/AI-SIEM and discount lines; **550** for the per-*user* IDR add-on.
- All recurring lines are **Yearly** (`billingperiod: 3`).
- **The EDU/GOV discount line is the client-specific price lever.** Adjust that line rather than
  the $110 AI-SIEM list price when a client's net per-endpoint number has to move — it keeps the
  published SKU prices intact across the book.
- Tax: Avon Local Schools is public sector → **EXEMPT** (Runbook 02 §5). Discount line sits on
  `No Tax`. Total Tax $0.00 either way.

---

## 2. Cloning a quote to create an option on the SAME opportunity

Ryan's standing rule is that quotes are raised FROM an opportunity (Runbook 11 §1). For a
**variant of an existing quote** — a 3-year option, an alternate tier — do NOT rebuild from
`Raise Quote`; clone instead:

1. Open the source quote → toolbar **Clone**.
2. The **Clone** dialog asks for a **Ticket ID** — type the *same* opportunity number (`50894`),
   pick the autocomplete row, **Save**.
3. Halo creates a new **Draft** quote in a second tab, named `NNNNN-1 (1)`, with **every line,
   group, price, cost, tax code and billing period copied**. Date/expiry reset to today/+90 days.
4. **Rename the Reference** (right sidebar, Quotation details → *Reference*) from `NNNNN-1 (1)`
   to **`NNNNN-2`**. It is a plain text field; the clean reference is what shows on the PDF
   header (`Quote #50894-2`) and in the opportunity sidebar.
5. **The clone does NOT inherit the PDF template pin** — it comes back as `*Default Template*`
   even when the source was pinned. Re-pin to **Simvay Proposal** (Print Options → PDF Template).

This turned a ~10-line rebuild into 6 line edits.

---

## 3. Reading a Carahsoft multi-year quote

Carahsoft prices a 3-year SentinelOne term as **six lines — one pair (server + workstation) per
contract year** — with a **flat unit price across all three years** and an annual invoice
schedule. From quote 66843121:

- Year 1 / 2 / 3 each: 16 × `S1-SCM-CW-S1` @ **$90.89** + 550 × `S1-SCM-EN-S1` @ **$46.55**
- Each year = **$27,056.74**; total quote **$81,170.22**
- Terms: *3 year, non-cancellable, annual payment structure*; Payment 1 on PO date, Payments 2–3
  on/around October 2027 and 2028, all Net 30. Missing an instalment accelerates the remainder.
- Expires 02/21/2027. Requires the customer's written acceptance of SentinelOne's Public Sector
  Terms of Service before Carahsoft accepts the PO.

**Compare per-YEAR, not per-quote.** Divide the Carahsoft total by 3 and put it beside the
single-year quote's `cost` figure.

### 3.1 Avon 1-year vs 3-year cost (2026-08-21)

| Unit | 1-yr basis (50894-1) | 3-yr option (66843121) | Δ |
|---|---|---|---|
| Per server (`S1-SCM-CW-S1`) | $89.10 | **$90.89** | +$1.79 (+2.01%) |
| Per workstation (`S1-SCM-EN-S1`) | $45.33 | **$46.55** | +$1.22 (+2.69%) |
| **Annual cost** (16 srv + 550 ws) | $26,357.10 | **$27,056.74** | **+$699.64/yr (+2.65%)** |

**The 3-year option is NOT cheaper per year — it is ~2.65% more.** What it buys is a *locked*
unit price for FY28 and FY29 (no renewal uplift in years 2–3) in exchange for a non-cancellable
commitment. Say this explicitly when presenting the option; the usual assumption is the reverse.

---

## 4. Building the multi-year option (procedure used for 50894-2)

Decisions taken with Ryan 2026-08-21: **pass the cost increase through** to the client, **annual
lines with the term noted** (not a 3-Yearly billing period), **no repeat of the one-time
onboarding line**.

1. Clone per §2; set **Title** to `… - 3-Year Term (FY27-FY29)`.
2. Update the two SentinelOne licence lines' **Cost** to the new unit costs (90.89 / 46.55).
   With Base price 0 the margin-recalc gotcha (Runbook 02 §2) does not fire.
3. Set **Number of Periods = 3** on every recurring line (Yearly × 3 = the 3-year term).
   Billing Period stays **Yearly** so the PDF's ANNUAL RECURRING COSTS section and the annual
   Carahsoft invoice schedule agree.
4. **Recover the cost delta on the DISCOUNT line**, not the list price:
   $699.64 ÷ 566 endpoints = $1.236 → discount **-$42.00 → -$40.76** (recovers $701.84/yr,
   margin held at ~$24,233/yr vs $24,230.90 on the 1-year).
5. Delete the **Onboarding** group row and its `SIM-SOC-DEPLOY` line (hover row → trash icon).
   Identity deployment was already sold on 50894-1.
6. Rename the group headers to carry the term
   (`SentinelOne Product (3-Year Term, Billed Annually)` etc.).
7. Re-pin **PDF Template = Simvay Proposal**, top-toolbar **Save**, verify with **Preview Print**.

### 4.1 Result — quote 50894-2 (Draft, 2026-08-21)

| | Annual | 3-year term |
|---|---|---|
| Client price | **$51,289.84** | **$153,869.52** |
| Cost | $27,056.74 | $81,170.22 |
| Margin | $24,233.10 (47.25%) | $72,699.30 |
| Tax | $0.00 (EXEMPT) | $0.00 |

vs 50894-1 (FY27, 1 year): $50,588.00 price / $26,357.10 cost / $24,230.90 margin, plus a
$1,500 one-time onboarding line ⇒ $52,088.00 year-one total.

---

## 5. Gotchas

1. **Group headers only render on the PDF when lines are ASSIGNED to the group.** On these
   quotes the group rows sit in the line sequence but every item line is `Group: No Grouping`
   (`group_id: 0`), so the Simvay Proposal PDF prints one flat ANNUAL RECURRING COSTS table with
   no teal sub-headers. Renaming a group therefore changes the Halo line table only — **term
   wording that must reach the client belongs in the quote Title or the line descriptions.**
2. **A clone loses the PDF template pin** (§2 step 5).
3. **`Number of Periods` is invisible on the PDF.** It records the term on the quote record;
   the client sees it only via the title/description.
4. **The PDF "TOTAL · incl. tax" banner shows ONE year** ($51,289.84), not the 3-year contract
   value. If the full term value must appear, add it to the title, a line description, or a
   canned-text block — do not assume the reader computes ×3.
5. **`get_quote` / `get_quotes` overflow the inline token limit** on these quotes — parse the
   saved file with `jq`, never re-request inline.
6. Halo's clone lands in a **second tab** inside the same modal; the original quote stays open in
   tab 1. Confirm the tab header reads the new reference before editing.

---

## 6. Open items for Ryan

- 50894-2 is **Draft** and not sent. Decide whether the client-facing PDF should state the
  **$153,869.52 3-year contract value** (gotcha 4) before it goes out.
- The cost pass-through was applied by moving the **EDU2 discount** from -$42.00 to -$40.76.
  If the discount tier is meant to be a fixed published number, the alternative lever is the
  AI-SIEM line price ($110.00 → $111.25) — say which is preferred so it is consistent next time.
- Carahsoft requires **written customer acceptance of SentinelOne's Public Sector ToS** before
  accepting a PO on either option (§3).
- Carahsoft quote 66843121 expires **02/21/2027**; term start on the quote is **10/27/2026**.
