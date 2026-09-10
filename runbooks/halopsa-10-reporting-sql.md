---
title: "HaloPSA 10: Reporting and custom SQL reports"
type: runbook
updated: 2026-08-21
tags: [halopsa, reporting, sql]
related: [runbooks/halopsa-01-overview, projects/halopsa/STATUS]
source: "HaloPSA Claude Project: claude/HaloPSA-Runbook-10-Reporting-SQL.md"
migrated: 2026-09-09
---
> Migrated 2026-09-09 from the HaloPSA Claude Project (`HaloPSA-Runbook-10-Reporting-SQL.md`). This file is now the canonical copy; the project doc is frozen. The verbatim original is in `projects/halopsa/archive/project-export-2026-09-09/`. Em and en dashes in prose were replaced per CLAUDE.md; code blocks are untouched. Cross-references were rewritten to brain paths.

# Simvay HaloPSA - Runbook 10: Reporting & Custom SQL Reports

> **Scope:** creating and editing HaloPSA saved reports - the Chrome report builder,
> the custom-SQL data source, the schema of the tables Simvay's financial reports
> actually use, the reporting-period enum, and how the read-only connector reads a
> report back.
>
> **Instance:** `https://simvay.halopsa.com`
> **Created:** 2026-08-02 (building report 290 "Billed Hours by Team")
> **Last updated:** 2026-08-21 (§7: report 291 "Team Time Metrics", agent-level report restriction behavior)

---

## 1. Connector vs Chrome for reports

| Task | Method |
|---|---|
| List saved reports | `mcp__HaloPSA__list_reports` |
| Read a report's definition (SQL, columns, group, period) | `halo_get` path `Report/N`, query `{"includedetails": true}` |
| Run a report and get rows | `halo_get` path `Report/N`, query `{"loadreport": true}` → rows at `report.rows`; or `run_report` |
| **Create or edit a report** | **Chrome only** - the connector is GET-only |

Reading a report definition is the cheapest way to learn Halo's schema: reports 173,
203 and 233 between them prove every table Simvay's financial reporting needs.

---

## 2. Creating a custom-SQL report (Chrome)

**Reporting** (left rail) → click the target **group** in the sidebar first (the new
report inherits it) → **+ New** (top right). URL pattern while building:
`/reports?mainview=reportgroup&selid=<groupId>&sellevel=1&...&id=-1`.

Wizard tabs: **Details / Data Source / Fields / Chart Setup / Appearance /
Availability / Scheduling / Preview Report**.

1. **Details** - Title, Group, Description, **Max Page Size** (default 1000 → set
   **10000**, matching reports 173/203/233, or the UI grid paginates).
2. **Data Source** - open the dropdown and type `sql`; pick
   **`*Write a custom SQL Query*`**. A **Monaco** editor appears with a **Test** button
   top-right.
3. **Fields** - leave empty. "If this list is empty, all fields will be shown", which
   preserves the SQL's column aliases verbatim. **Leave it empty whenever a downstream
   script depends on exact column names.**
4. **Save** (toolbar). Halo assigns the id and immediately renders the report.

### 2.1 Getting SQL into the editor

It is a Monaco editor, so `setValue` reaches the save payload - no fetch/XHR
interceptor needed (same as the portal CSS editor, Runbook 06 §2.1), and typing is
avoided so auto-indent can't mangle the SQL:

```js
const ed = window.monaco.editor.getEditors()[0];
ed.getModel().setValue(sql);           // build `sql` from an array joined with "\n"
({lines: ed.getModel().getLineCount()})   // small JSON return — passes the §3.4 filter
```

**Do not** try to capture the app's Authorization header to POST `/api/report`
directly (the Runbook 05 §3 pdftemplate trick). Wrapping `fetch`/`XHR.setRequestHeader`
to read an auth token is blocked by the Claude Chrome safety classifier. The report
builder UI is the supported path and works fine.

### 2.2 The Test button, and the ORDER BY trap

**Test** validates the SQL server-side and is worth clicking before every save.

⚠ **Halo wraps custom report SQL in a derived table**, so a bare `order by` fails:

> *Invalid SQL Statement. Failed with error: The ORDER BY clause is invalid in views,
> inline functions, derived tables, subqueries, and common table expressions, unless
> TOP, OFFSET or FOR XML is also specified.*

**Fix:** add `top 100 percent` (or an explicit `top N`) to the outer `select` - this is
exactly why reports 203 and 233 read `select distinct top 100 percent` / `top 11`.
Halo's grid re-sorts by its own column config anyway, so the `order by` is cosmetic.

---

## 3. Verified schema (the tables Simvay's financial reports use)

| Table | Key columns |
|---|---|
| `actions` | `faultid`, `whe_` (action date - this is the date to filter on), `timetaken`, `timetakenAdjusted`, `whoagentid`, `who` (agent name), `actioncode`, `ActionInvoiceNumber`, `actionbillingplanid`, `ActionChargeHours` |
| `faults` | `Faultid`, **`areaint` = the client id**, `FDeleted`, `Symptom`, `requesttypenew` |
| `area` | **`aarea` = client id (PK)**, `aareadesc` (client name), `aisinactive` |
| `uname` | `unum` (agent id), `uname` (name), **`usection` = the agent's team**, `ucostprice`, `usellprice` |
| `invoiceheader` / `invoicedetail` | `ihid`, `ihaarea`, `ihinvoice_date`, `ihchid`; `idihid`, `idnet_amount`, `idunit_cost`, `idqty_order` |
| `contractheader` | `chid`, `ChContractRef` |
| `calendar` | `date_id` - join against this to get a row per month even when there's no data |
| `chargerate` | `crrate`, `CRarea`, `CRchargeid` |
| `lookup` | `fid`/`fcode`/`fvalue` - e.g. `fid=17` is the charge-type list |

**The join direction that trips people up:** it is `area.aarea = faults.areaint`, i.e.
the *client* table's PK is `aarea` and the *ticket* table's FK is `areaint` - the
opposite of what the names suggest. Report 173's unqualified `join area on
Aarea=Areaint` reads the same way.

**`usection` is the agent's team** - confirmed 2026-08-02, it backs the `team` field
the Agents API returns (`Agent/3` → `"team": "Support (Mgmt)"`). Agents with no team
return blank, not null - guard with `isnull(nullif(u.usection, ''), '(no team)')`.

### 3.1 SQL variables Halo substitutes

- `@startdate` / `@enddate` - the reporting period. Setting these makes
  `sqlhasdatefilter` true on the saved report.
- `$agentid`, `$userid`, `$siteid`, `$clientid` - scheduled runs pass 0.
- `$QUOTEID` - quotation id.
- `$filters` - insert inside an existing `where` (e.g. `where 1=1 $filters`) to push
  report-builder filters into the query instead of applying them client-side.

---

## 4. Reporting periods

The saved report's period is set on the report screen itself (a **Reporting Period**
bar above the grid), not in the wizard. `reportingperiod` is an enum echoed back by
the API along with the resolved `reportingperiodstartdate` / `reportingperiodenddate`.

| N | Resolves to |
|---|---|
| 0 | today |
| 1 | yesterday |
| **6** | **All** (1899-12-30 → 2099-12-31) - the whole instance in one pull |
| 7 | last calendar month |
| 8 | this week |
| 9 | this month (MTD) |
| 10 | ~last 90 days |
| 11 | ~last quarter / instance history |
| 12 | tomorrow (empty) |
| 13 | next week |

Custom start/end dates are **ignored** by the GET API - you must select a period
through the enum. Always check the echoed start/end dates rather than trusting N.

A report whose SQL uses `@startdate`/`@enddate` and whose saved period is **6 (All)**
behaves like report 168: one pull returns every month, which is the easiest thing for
a downstream script to consume.

---

## 5. Worked example - report 290 "Billed Hours by Team"

Built 2026-08-02 for the labour reconciliation in the monthly sales report (cost and
margin there are **product cost only**; delivery labour is reconciled separately).

- **Id 290**, group **💰 Profitability**, Max Page Size 10000, period **6 (All)**,
  `sqlhasdatefilter: true`, Fields list empty.
- Columns - this is a **contract** `analyze.py` depends on, do not rename:
  `Month | Client | Team | Hours | Labour Cost`.
- Set `hours_report_id: 290` in the `simvay-monthly-sales-report` skill's `config.json`.

```sql
select top 100 percent
  format(a.whe_, 'yyyy-MM')                              as [Month]
, ar.aareadesc                                           as [Client]
, isnull(nullif(u.usection, ''), '(no team)')            as [Team]
, round(sum(isnull(a.timetaken,0) + isnull(a.timetakenAdjusted,0)), 2) as [Hours]
, round(sum((isnull(a.timetaken,0) + isnull(a.timetakenAdjusted,0))
            * isnull(u.ucostprice,0)), 2)                as [Labour Cost]
from actions a
join faults f  on f.faultid   = a.faultid
join area   ar on ar.aarea    = f.areaint
join uname  u  on u.unum      = a.whoagentid
where a.whe_ between @startdate and @enddate
  and f.FDeleted = 0
  and isnull(a.timetaken,0) + isnull(a.timetakenAdjusted,0) > 0
group by format(a.whe_, 'yyyy-MM'), ar.aareadesc,
         isnull(nullif(u.usection, ''), '(no team)')
order by 1 desc, 2, 3
```

**Two deliberate choices.** `timetakenAdjusted` is included (report 173 does the same),
and there is **no `ActionInvoiceNumber` filter** - so this counts hours *delivered*,
including contract-absorbed work, which is exactly what a product-only margin figure
leaves out.

### 5.1 Why the existing reports could not be used

| Report | Why it fails for this |
|---|---|
| 173 Billable Time | `where actions.ActionInvoiceNumber is null` - uninvoiced only |
| 203 Gross Agreement Profitability | Its labour subquery filters on the whole report period, not the month, so per-month Labour Cost double-counts (July $106,344 vs June $18,240) |
| 233 Effective Hourly Rate | Hours get multiplied by the number of invoices per agreement in the window (City of Avon Lake EMTS showed 182h) |
| `Actions` API | Does not accept date-range parameters through the connector |

### 5.2 First-run results (2026-08-02, period All - 199 rows, 2026-01 → 2026-07)

| Team | Hours | Share | Effective rate |
|---|---|---|---|
| Support (Sys Admins) | 998.33 | 58.3% | $144.00/h |
| Support (Mgmt) | 513.49 | 30.0% | $144.01/h |
| Cyber Ops (Analysts) | 150.48 | 8.8% | $135.41/h |
| Cyber Ops (Mgmt) | 28.57 | 1.7% | $144.07/h |
| `(no team)` | 22.75 | 1.3% | $144.00/h |
| **Total** | **1713.62** | | |

Monthly totals: 2026-01 0.02h · 02 0.08h · 03 4.96h · **04 352.06h · 05 397.27h ·
06 428.66h · 07 530.57h**. Anything before April is noise - treat **2026-04** as the
first usable month.

**Team → category map** (teams already carry the category, confirmed from the Agents
API 2026-08-02; held in the skill's `config.json` as `team_category_map`):

| Team | Dept | Category |
|---|---|---|
| Cyber Ops (Analysts) | 10 | Cybersecurity |
| Cyber Ops (Mgmt) | 10 | Cybersecurity |
| Support (Sys Admins) | 3 | Managed Technology |
| Support (Mgmt) | 3 | Managed Technology |
| Sales Team | 8 | *(not delivery - excluded)* |
| Contract Renewals | 3 | *(not delivery - excluded)* |

Sales Team and Contract Renewals log no action time, so they don't appear at all. A
team present in the data but absent from the map surfaces as "unmapped" rather than
being silently dropped.

### 5.3 Data-quality flags to re-check each run

- **`(no team)` - 22.75h, all Apr-May** (Herrick Memorial Library 17h, Village of
  Monroeville 3.5h, Benko Products 1.5h, Townsend Community School 0.75h). An agent
  with a blank `usection`, most likely departed/disabled. Fix the agent's team in Halo
  and this bucket empties.
- **Zero-cost rows - 2 rows, 1.25h** (Polaris Career Center, Russell Township, both
  Cyber Ops Analysts, June). Agents carrying `ucostprice` **0**. Every other delivery
  agent is **$144/h**; Simvay's own internal figure is **~$150/h**
  (`internal_hourly_cost`). The two bases should land within ~4% - a wider gap means an
  agent's cost price is stale.
- **Client "Unknown" - 6 rows, 2.85h.** Tickets with no client area set.

---

## 6. Gotchas (reporting-specific)

1. **`order by` needs `top 100 percent`** - Halo wraps report SQL in a derived table (§2.2).
2. **Leave the Fields list empty** if a script depends on exact column names.
3. **Max Page Size defaults to 1000** - raise it to 10000 on any report that can exceed it.
4. **`area.aarea = faults.areaint`**, not the reverse the names imply (§3).
5. **Auth-header capture is blocked by the Chrome safety classifier** - use the report
   builder UI, not an in-page POST to `/api/report` (§2.1).
6. **Custom start/end dates are ignored by the GET API** - use the `reportingperiod`
   enum and verify against the echoed resolved dates (§4).
7. **The Details form scrolls under you while typing** - the first title I typed landed
   nowhere and a later value went into *AI Prompt Override*. Screenshot and re-verify
   every field before saving.
8. **Reading a report definition is free schema documentation** - `Report/N` with
   `includedetails` beats guessing at Halo's table names.

---

## 7. Restricting a report to specific agents - worked example, report 291 "Team Time Metrics"

Built 2026-08-21 as the manager-only replacement for direct Timesheet API access
(the `Timesheet` endpoint returns ALL agents' hours to any role - row-level scoping
is UI-only; see Runbook 09 §11.11). Kris Oswald and Mike Karenke run this report
instead; the halopsa-oauth worker never exposes `Timesheet`.

- **Id 291**, group **🧑‍💼 Agent Utilization**, Max Page Size 10000, custom SQL,
  Fields list empty. Columns: `Date | Agent | Team | Hours Logged | Charge Hours |
  Tickets Touched` (per agent per day). First render: 914 rows.
- **Access (Availability tab):** Restrict access ✔ - Ryan Patrick (creator,
  auto-added, Read Only No), Kristoffer Oswald (Read Only Yes), Mike Karenke
  (Read Only Yes). User Access: none. Not published.

```sql
select top 100 percent
  format(a.whe_, 'yyyy-MM-dd')                       as [Date]
, u.uname                                            as [Agent]
, isnull(nullif(u.usection, ''), '(no team)')        as [Team]
, round(sum(isnull(a.timetaken,0) + isnull(a.timetakenAdjusted,0)), 2) as [Hours Logged]
, round(sum(isnull(a.ActionChargeHours,0)), 2)       as [Charge Hours]
, count(distinct a.faultid)                          as [Tickets Touched]
from actions a
join uname u on u.unum = a.whoagentid
where a.whe_ between @startdate and @enddate
group by format(a.whe_, 'yyyy-MM-dd'), u.uname,
         isnull(nullif(u.usection, ''), '(no team)')
order by 1 desc, 2
```

### 7.1 How the Availability tab actually works (verified 2026-08-21)

- Restriction is **per-agent, not per-role**: check **Restrict access to this
  report**, then **Agent Access → + Add** opens a dialog with a multi-select agent
  react-select and a **Read Only** checkbox that applies to every agent in that Add.
  The **creator is auto-added** (Read Only No) the moment restriction is enabled.
- The dialog re-lays itself out when the select menu closes - re-screenshot before
  clicking Read Only/Save, or the click lands on the old position (same class of
  trap as gotcha §6.7).
- **The restriction is enforced API-side, not just in the UI** (unlike Item Costs
  and Timesheet scoping): a non-granted agent gets **404** (not 403) on
  `Report/291` under every parameter combination, and the report is absent from
  their `Report` list. Verified with the MT-role API test user *and* with the
  admin read-only MCP connector - the connector's service account is not in the
  grant list, so **the admin connector cannot see or run report 291 either** while
  still seeing unrestricted reports (290 returns fine). Reach restricted reports
  through the per-user halopsa-oauth connector as a granted agent, or widen the
  grant list.
- A role with **Reporting Access Level = No Access** (e.g. Managed Technology,
  Cybersecurity Operations) 404s on the whole `Report` endpoint - restricted or
  not. Services Leadership has **Read Only** (confirmed in the role UI
  2026-08-21), which is enough to run reports; Read Only grant rows keep the
  report itself uneditable.
