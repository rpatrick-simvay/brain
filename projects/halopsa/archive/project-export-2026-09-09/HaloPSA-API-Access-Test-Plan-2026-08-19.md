# Simvay HaloPSA — Post-Redesign API Access Test Plan (Go-Live Confirmation)

**Date:** 2026-08-19 · **Owner:** Ryan Patrick · **Executor:** Claude (orchestrator) + one testing subagent · **Instance:** simvay.halopsa.com

## Purpose

Final pre-go-live confirmation for the per-user OAuth MCP connector (Runbook 09 §1–4). One
test API account is cycled through each production role; an identical read battery runs per
cycle; actual API access is compared against the expected access matrix from the approved
role redesign. Because the token's effective permissions mirror what the per-user MCP
connector will grant each employee, this is a direct rehearsal of connector scope.

## Design constraints

- **Sequential, not parallel** — one test account, one role at a time. Role is swapped
  between cycles, so runs cannot overlap.
- **Same battery every cycle** — 18 read probes (below), identical requests, results saved
  as JSON per role for machine comparison.
- **Fresh browser window** for the role swaps; a **testing subagent** runs the battery.
- The test key is temporary: revoked and the test agent deleted when testing completes.

## Prerequisites — Ryan (one-time, ~10 min; Claude cannot create accounts or handle key entry)

1. **Create the test agent:** Config → Teams & Agents → Agents → New.
   Name `API Test User`, email something inert (e.g. apitest@simvay.com), **no teams**,
   initial role: `Sales Rep` (cycle 1). Mark it clearly as a test account.
2. **Create the API application:** Config → Integrations → HaloPSA API → View Applications
   → New. Auth method **Client ID and Secret (Client Credentials)**, Login Type **Agent**,
   Log in as **API Test User**. Permissions: **read:all** (or "all" if read-only scoping is
   not offered — role permissions are the layer under test, not app scope).
3. **Provide credentials to Claude** as environment values for the harness (Client ID +
   Secret). Claude never types them into any web form; they are used only as API request
   parameters by the probe script.
4. After testing: **delete the API application and the test agent** (or Ryan revokes the
   secret). The plan is not complete until this is done.

## Role cycle order (8 cycles, ~10 min each ≈ 90 min total)

| Cycle | Role on API Test User | Why this order |
|---|---|---|
| 1 | Sales Rep | Most-restricted sales profile; validates ticket-type restriction list (5 types) |
| 2 | Sales Executive | Adds Projects/Project Task types + fuller sales flow |
| 3 | Operations | New role; order/invoice muscle intact |
| 4 | Executive | New role; reports + invoice receipt |
| 5 | Finance | Most-restricted overall (RO tickets, no assets/CRM, own-only visibility) |
| 6 | Cybersecurity Operations Role | No-pipeline enforcement |
| 7 | Managed Technology Role | No-pipeline enforcement, contracts RO |
| 8 | Services Leadership | Widest non-admin; both-units write + full pipeline |

## Per-cycle procedure

1. **Claude (fresh browser window):** open `API Test User` → Edit → set Roles = the cycle's
   single role → Save → verify the Roles line in view mode.
2. Wait 60 s (permission cache), then **testing subagent** runs:
   `python3 /home/claude/rollout/apitest/halo_api_probe.py <role_label>`
   — the script requests a **fresh token** (tokens carry permissions at issue time) and
   fires the 18-probe battery, saving `results/<role_label>.json`.
3. Claude spot-checks the JSON (HTTP codes + counts) before authorising the next swap.
4. After cycle 8: comparison script merges the 8 JSONs against the expected matrix and
   produces the pass/fail grid; deviations are reviewed one by one.

## The battery (18 read probes — mirrors the MCP connector's read surface)

| ID | Module exercised | Request | Special capture |
|---|---|---|---|
| T1 | Tickets list | `Tickets?page_size=10&includeclosed=true` | distinct tickettype ids returned |
| T2 | Ticket detail | `Tickets/2852` | |
| C1 | Clients | `Client?page_size=5` | |
| U1 | Users | `Users?page_size=5` | |
| AG1 | Agents | `Agent` | |
| A1 | Assets | `Asset?page_size=5` | |
| K1 | Knowledge Base | `KBArticle?page_size=5` | |
| OP1 | Sales pipeline | `Opportunities?page_size=5` | |
| Q1 | Quotations | `Quotation?page_size=5` | |
| SO1 | Sales Orders | `SalesOrder?page_size=5` | |
| PO1 | Purchase Orders | `PurchaseOrder?page_size=5` | |
| I1 | Invoices | `Invoice?page_size=5` | |
| CC1 | Client Contracts | `ClientContract?page_size=5` | |
| IT1 | Items | `Item?page_size=5` | which cost/price fields are visible |
| R1 | Reporting | `Report?page_size=5` | |
| TS1 | Timesheets | `Timesheet` | own-only vs all |
| W1 | Control probe | `Workflows` | expected readable everywhere |
| TT1 | Control probe | `TicketType` | expected readable everywhere |

Recorded per probe: HTTP status, record count, error text, latency. "Denied" in Halo may
surface as 401/403 **or** HTTP 200 with zero/filtered records — the comparison treats
both as DENY; which one Halo actually does per module is itself a finding worth logging
for the connector's error-message design.

## Expected results matrix

Legend: **A** = allow (data returns) · **D** = deny (4xx or empty) · **P** = partial
(returns but filtered) · **?** = verify against role page before scoring (uncertain cells
— not fully pinned during waves; treat mismatches as review-items, not failures).

| Probe | SalesRep | SalesExec | Operations | Executive | Finance | Cyber | MT | SvcLead |
|---|---|---|---|---|---|---|---|---|
| T1 Tickets | **P** (5 types only) | **P** (7 types) | A | A | P (RO, own/unassigned hidden) | A | A | A |
| T2 Ticket detail | P (type-dependent) | P | A | A | D/P (not assigned to it) | A | A | A |
| C1 Clients | A | A | A | A | A (RO) | A | A | A |
| U1 Users | A | A | A | A | A (RO) | A | A | A |
| AG1 Agents | A | A | A | A | A | A | A | A |
| A1 Assets | A (RO) | A (RO) | A (RO) | A (RO) | **D** | A | A | A |
| K1 KB | A | A | A | A | A (RO) | A | A | A |
| OP1 Pipeline | A | A | A | A | A (RO) | **D** | **D** | A |
| Q1 Quotations | A | A | A | A | A (RO) | **D** | **D** | A |
| SO1 Sales Orders | A (RO) | A | A | A | A (RO) | **D** | A | A |
| PO1 POs | **D** | A (RO) | A | ? (unchanged from Admin clone) | A (RO) | **D** | ? | A (RO) |
| I1 Invoices | **D** | A (RO) | A | A | A | **D** | ? | ? |
| CC1 Client Contracts | A (RO) | A | A | ? | A | A (RO) | A (RO) | A |
| IT1 Items | A (RO) | A | A | ? | A (RO) | A (RO) | ? | A |
| IT1 cost fields | **visible** (2026-08-19 policy) | visible | visible | visible | visible | **hidden** | **hidden** | visible |
| R1 Reporting | **D** | A (RO) | A (RO) | A | A | **D** | **D** | ? |
| TS1 Timesheets | P (own) | P (own) | A (all) | ? | A (all) | P (own) | P (own) | A (all) |
| W1 / TT1 controls | A | A | A | A | A | A | A | A |

Nine `?` cells: pin them by opening each role's Permissions page (view mode, 2 min per
role) before cycle 1, or let the run surface them and score afterwards.

## Go / no-go criteria

1. **GO** if every **D** cell actually denies, every cost-field cell matches, and the
   Sales ticket-type lists match (5 / 7 types).
2. Any **D-expected cell that returns data = NO-GO** for that role's connector rollout
   until fixed — that is real over-exposure the connector would inherit.
3. **A-expected cells that deny** are workflow bugs, not security failures — fix-forward,
   don't block go-live unless they hit Wave-critical flows.
4. `?` cells: reviewed with Ryan, then either accepted or role-edited and that cycle rerun.

## Security handling of the test key

- Secret lives only in the harness environment for the test window; never pasted into web
  forms; never written to the project or the workbook.
- Immediately after cycle 8: Ryan deletes the API application (or rotates the secret) and
  deletes/disables `API Test User`. Claude verifies via `Agent` list that the test account
  is gone/disabled and records completion in Runbook 09.

## Outputs

1. `results/<role>.json` × 8 — raw evidence.
2. `API_Access_Test_Results_2026-08-XX.xlsx` — actual-vs-expected grid, deviations
   highlighted, go/no-go per role.
3. Runbook 09 §11.11 — findings, including how Halo signals "denied" per module (feeds the
   connector's 401/403 handling).
