# Simvay HaloPSA — Runbook 17: Monthly Sales Report (v2 cost basis) — build record and gotchas

> **Purpose:** what the August 2026 monthly executive sales report run (2026-09-01) learned, where the
> v2 scripts live, and the data-quality items to re-check next month. Companion to the
> `simvay-monthly-sales-report` skill, Runbook 10 §5 (report 290) and Runbook 12 §13 (binding ladder).
>
> **Last updated:** 2026-09-01 · **Deliverable:** `Simvay_Sales_Report_August_2026.pdf` (6 pages, 220 KB)

## 1. 2026-09-01 firing — binding record (belongs in Runbook 12 §11.2 / §13.1)

Monthly Sales Report v3.3 (`trig_0143X2LEwHMUYFVFYGn25XUT`) fired 11:00Z. HaloPSA / Action1 /
SentinelOne **absent at T+0, T+15 and T+30** (11:33Z), each absence confirmed by `ToolSearch`
("No matching deferred tools found"). Unbound table: memory, Plaud_ai, PagerDuty, Microsoft_365,
claude-code-remote. Halt PushNotification sent 11:33Z per §13 step 4; the turn ended. **No in-session
recovery observed.** Ryan typed "try now" ~13:45Z (2h12m later) and the deferred-tool notice listing
all 68 Worker tools arrived **with the reply itself**; `RefreshMcpTools` then showed 9 servers
(a new `visualize` server with 2 tools appeared alongside the usual 8). The whole job ran in that
session. No desktop bridge came with the reply (`ToolSearch` for `mcp__remote-devices__get_device_info`
→ none), so the PDF stayed in the conversation; that is the normal case.

*Runbook 12's log tables were not patched in place this run (avoiding a hand re-emission of a 45 KB
document); add this row there on the next edit.*

## 2. The synced skill is the JULY build — the v2 logic lives in the project

The task prompt references `scripts/render_report.py`, `references/hours-report.md`, `config.json`
keys `internal_hourly_cost` / `team_category_map` / `hours_report_id` / `cost_corrections`, and an
Appendix C. **None of these exist in the synced skill** (`/root/.claude/skills/synced/<uuid>/
simvay-monthly-sales-report/` still has `analyze.py`, `build_charts.py`, `build_pdf.py`,
`extract_rows.py` and the July `config.json`). Whatever session built the July report with v2
rules did not write its scripts back into the skill.

This run re-implemented v2 from the task specification and saved the result to the project:

| Project doc | Put it at (inside the skill) |
|---|---|
| `claude/sales-report-v2-analyze2.py.md` | `scripts/analyze2.py` (supersedes `analyze.py`) |
| `claude/sales-report-v2-render_report.py.md` | `scripts/render_report.py` (HTML → PDF via Playwright Chromium; `build_charts.py` / `build_pdf.py` retired) |
| `claude/sales-report-v2-config.json.md` | `config.json` |

**Ryan: copy those three into the skill folder so the October run does not start from the July
build again.** Until then every scheduled run must fetch them from the project first.

### 2.1 Pipeline as run

```
Report/168 {loadreport:true}                    → raw/r168.txt   (period 6 "All"; rows array closes even when
                                                                 the 500k cap trims table_html)
Report/288 {loadreport:true, reportingperiod:10} → raw/r288_p10   (echoed window 2026-07-01 → 2026-09-30)
Report/288 {loadreport:true, reportingperiod:11} → raw/r288_p11   (echoed window 2025-10-01 → 2026-09-30; data starts 2026-04-02)
Report/290 {loadreport:true, reportingperiod:11} → raw/r290_p11   (Month | Client | Team | Hours | Labour Cost)
scripts/extract_rows.py on each  → check array_closed=True, then split 288 by Invoice Date prefix into data/lines_YYYY-MM.json
Invoice API for the focus month  → data/inv_aug.json (per-line unit_cost, qty, ticket_id, contract_id)
python3 scripts/analyze2.py data --config config.json --focus 2026-08     → data/analysis.json, data/audit.txt
python3 scripts/render_report.py data --config config.json --focus 2026-08 --summary summary.txt \
        --extra-notes notes.txt --out Simvay_Sales_Report_August_2026.pdf --logo simvay-mark-white.png
pdf2image at 80 dpi → eyeball every page
```

**Getting per-invoice cost without blowing the context:** `halo_get Invoice {includelines:true,
page_size:100, order:"invoice_date", orderdesc:true}` returns ~30 complete invoices with lines before
the 500k cap trims the array — parse the `"invoices": [` array with the balanced-brace scanner from
`extract_rows.py`. Fetch the stragglers with `get_invoice` inside a Sonnet subagent that writes
compact JSON files (each `get_invoice` payload is ~15k tokens; do not read them in the main session).
Keep only: `item_shortdescription, item_name, productcode, qty_order, unit_price, net_amount,
unit_cost, ticket_id, contract_id, recurring_invoice_id, salesorder_line_id, isgroupdesc`.

`reportingperiod` 10 and 11 both resolved as labelled on 2026-09-01 (unlike 2026-08-01's value 7).
Always read the echoed dates anyway.

## 3. August 2026 results (for next month's MoM)

| Metric | Aug 2026 | Jul 2026 |
|---|---|---|
| Revenue (net of tax, by invoice date) | **$138,135.33** (32 invoices) | $634,591.67 (58) |
| Advisory / Managed Tech / Cyber Ops / SaaS / One-time | 23,350 / 64,022 / 15,185 / 3,374 / 32,205 | 27,850 / 71,772 / 172,469 / 40,376 / 322,124 |
| Recurring | $105,930 (76.7%) | $312,467 (49.2%) |
| Cybersecurity category | $38,535 (27.9%) | $215,384 (33.9%) |
| Cost as recorded (168) → product cost | $44,786.74 → **$23,712.74** | $431,485 → $410,234 |
| Product GP | **$114,422.59 (82.8%)** | $224,358 (35.4%); adjusted $236,494 (37.3%) |
| Delivery hours (excl. internal "Simvay") | 526.50 h (Cyber 55.33 / MT 471.17) | 542.82 h (29.74 / 513.08) |
| Fully-loaded margin (ceiling) | **$35,448 (25.7%)** | $142,935 (22.5%) |

Trend, product GP % as-recorded / adjusted: Apr 72.3/94.5 · May 63.8/77.2 · Jun 24.3/53.8 ·
Jul 35.4/37.3 · Aug 82.8/82.8.

## 4. Cost-basis findings (the part that bites)

- **Russell Township "MSA | Monthly | Technology" carries `unit_cost` 21,000 on a $1,750 line** —
  on the 7/1 and 8/4 invoices (12× the monthly price). It is a labour-only plan and is stripped
  regardless, but **the recurring-invoice template fix has not taken**: the 8/4 invoice still carries
  it. Recorded in `config.json` → `cost_corrections` with `effective_through: 2026-07` so the report
  says so if it fires again. **Ryan, 2026-09-01: Kris (Oswald) owns resolving the template.** Until
  the 9/1 invoice shows unit cost 0, keep the correction firing and keep naming it in Appendix B.
- **Bober Markey Fedorovich SentinelOne component lines: Apr–Jul carried ANNUAL vendor cost on each
  MONTHLY invoice** (~$17.6k/mo cost vs ~$3.5k/mo revenue) — the persistent defect, reported
  separately and excluded from adjusted GP. **August lines carry `unit_cost` 0.** The overstatement
  is gone; the true monthly vendor cost is now unrecorded (invoice 20170 reads 100% margin).
  Recommend loading the monthly S1 cost on the recurring template. (Ryan acknowledged 2026-09-01.)
- Olmsted Falls City Schools ECRM line carries `unit_cost` −1 every month (cosmetic; stripped).
- Ticket-raised time in report 168 is recognisable by description: `Remote Support - ID: …` /
  `On-Site Support - ID: …` / `Time Taken`. Pre-Delivery Prep lines at 144/288 cost are ticket time
  (1 h / 2 h × $144), not vendor cost.
- Staffco "Laptop Install (Per Hour Labour)" $125 with `unit_cost` 75 (ticket_id −1) — a one-off
  labour line with an internal estimate; stripped as labour (`LABOUR_LINE` pattern).
- **Aztek "Internet" $50/mo** is a pass-through at cost = revenue; bucketed SaaS, footnoted.
- 288 vs 168/Invoice-API revenue differ by **$0.53** in August (Bober line 175 × $3.3330 rounds
  differently). 288 stays the revenue basis; note it in Appendix B.

## 5. Classification findings

- **New: Polaris Career Center "Professional Services {8/17/2026 - 8/16/2027}" $5,000 (20 h
  retainer, contract RETAINER-080326-080227).** Contract-billed → recurring → placed in Managed
  Technology (same treatment as Russell's MTS hours) via `^Professional Services \{` in `MTC`.
  **Confirmed by Ryan 2026-09-01: Managed Technology is correct.** No longer an open question.
- New patterns added to `analyze2.py`: `Simgularity`, `Wayfinder`, `EMDR`, `Purple AI`,
  `Complete Protection` (without "Platform"), `Managed Technology Services` (Russell MTS hours),
  `Auvik|Monitoring Per Billable Device` → Managed Technology (not SaaS), `Plate Recognizer|Parkpow`
  → SaaS, `Intune|Entra|Copilot|Acrobat` → SaaS. Umbrella is SaaS by bucket, Cybersecurity by
  category (the standing example). Cyber Operations is ONE product line (SOC + SentinelOne + MEDR/EMDR
  + threat-intel ingest).
- 288's line descriptions concatenate the group name ("SentinelOne - Security Operations Center -
  MEDR …", "Simvay - A1 - Vulnerability …"); the Invoice API's `item_shortdescription` does not.
  Classify on 288, cost on the API — the patterns must match both forms.
- July's Advisory ($27,850) and Managed Tech included Avon Lake's Apr–Jun ECRM-MC catch-up billing
  ($4,500 + $4,500) — August's $23,350 Advisory is the true run rate, not a decline.

## 6. Hours (report 290) findings

- **Internal client "Simvay" carried 50.25 h in August (Cyber Ops Mgmt 50.0 h)** — consistent with
  the uncorrected 50.0 h "No Charge" entry flagged in the weekly ops retrospective. Excluded from
  delivery hours via `hours_exclude_clients: ["Simvay"]` in `config.json`; footnoted. Without the
  exclusion Cyber Ops (Mgmt) reads 60.58 h and fully-loaded margin drops to $27,911 (20.2%).
- Cyber Ops external hours were 55.33 h (Jul 29.74, Jun 71.75) — rose, not fell. Report factually.
- Report 290 with `reportingperiod: 11` returned 248 rows, 2026-01 → 2026-09, array closed.

## 7. Layout lessons (render_report.py)

- Container width **720 px** (Letter minus 0.5 in margins); the brand starter's 760 px overflows.
- Per-page `.confidential` divs pushed footers onto blank pages; the confidential line now lives in
  Chromium's `footerTemplate` with page numbers. Keep it there.
- Two-column blocks take charts at w=326 and tables of ≤5 columns; 6-column tables clip.
- Appendix C fits on one page at 32 invoices with `font-size 7.8px`, `white-space:nowrap`, client
  truncated to 30 chars. Watch it at 50+ invoices (split the table).
- Fonts: Poppins is installed locally; Montserrat is not (falls back to Poppins for the wordmark).
  The Google Fonts link is harmless when offline.

## 8. Pre-ship checks (all passed 2026-09-01)

Appendix C total = month total ($138,135.33); 32 invoices = 32; per-invoice GP sum = month GP
($114,422.59); Invoice-API cost $44,786.74 = report-168 cost; `cost_attribution_pct` 100.0;
288 p10 vs p11 agree to the cent on Jul, Aug, Sep-stub; both 288 arrays and the 168 array closed.

## Standing instruction

Any future monthly-report run that changes a classification pattern, a cost-basis rule, a
`cost_corrections` entry or the layout updates this runbook and re-saves the three script docs in §2.
