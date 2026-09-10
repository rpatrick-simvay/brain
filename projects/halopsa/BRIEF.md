---
title: HaloPSA brief
type: brief
updated: 2026-09-09
tags: [halopsa, psa, quotes, reporting, mcp-connector, scheduled-tasks]
related: [projects/halopsa/STATUS, runbooks/halopsa-01-overview]
---

# HaloPSA

## What it is
Simvay runs HaloPSA (`https://simvay.halopsa.com`) as its PSA: tickets, clients, sites, assets, agents, contracts, invoices, quotations, sales and purchase orders, and the reporting layer. This project holds everything Claude has learned about operating it: the read-only MCP connector and the OAuth worker behind it, the Chrome UI workflows for anything the connector cannot do (config, quotes, PDF and email templates, notifications, reports), the branded document templates, the scheduled reporting jobs that pull from it, and the employee Claude-access rollout.

## Why
HaloPSA work is repetitive and full of traps (multi-step saves, hover-only controls, framework models that ignore DOM edits, silent PDF omissions). The runbooks exist so no discovery is re-learned. The standing instruction in runbook 01 still applies: every session that learns something about HaloPSA writes it back to the relevant runbook before ending.

## Constraints
- The MCP connector is GET-only. All writes go through Chrome, and quotes are never sent from a Claude session (leave Draft).
- New deals are Opportunities stepped through the workflow with the quote raised from the opportunity (Ryan, 2026-08-04).
- Public-sector clients get tax code EXEMPT; `Default` resolves to the client's own rate.
- Never press Escape in quote edit mode. Save first.
- Scheduled tasks must be created with `create_trigger` from a live session so custom connectors bind (runbook 12).
- Simvay is a pure-play cybersecurity firm; where old text says MSP/MSSP, do not carry that framing forward.
- No secrets in this repo. Worker secrets live in Cloudflare; Halo API credentials live in Halo.

## Documents
Runbooks (canonical, normalized 2026-09-09; originals verbatim in `archive/project-export-2026-09-09/`):

| Runbook | Covers |
|---|---|
| `runbooks/halopsa-01-overview.md` | Environment map, connector vs Chrome, quotations basics, custom fields, PDF proposal template, consolidated gotchas, runbook index (section 9) |
| `runbooks/halopsa-02-quotations-lines-groups.md` | Building quote content: lines, recurring items, groups, tax codes, leasing, worked examples |
| `runbooks/halopsa-03-email-templates.md` | Email template editing mechanics, inventory, variables, redesign state |
| `runbooks/halopsa-04-notifications.md` | Notification rules, Cyber Ops rebuild, popup template family |
| `runbooks/halopsa-05-pdf-templates-so-po-invoice.md` | Branded SO / PO / Invoice PDF templates |
| `runbooks/halopsa-06-client-portal.md` | Self-service portal branding and custom CSS |
| `runbooks/halopsa-07-travel-notifications.md` | User travel workflow and travel conditional access |
| `runbooks/halopsa-08-action1-ticket-type-routing.md` | Action1 ticket type and contract-based routing |
| `runbooks/halopsa-09-claude-access-architecture.md` | OAuth MCP worker, role redesign waves, employee rollout, SARA plan, open items (section 10) |
| `runbooks/halopsa-10-reporting-sql.md` | Report builder, custom SQL, verified schema |
| `runbooks/halopsa-11-action1-renewal-quotes.md` | Action1 renewal quotes and the opportunity-first process |
| `runbooks/halopsa-12-scheduled-tasks-connector-binding.md` | Scheduled task inventory, connector binding behaviour, morning brief flow |
| `runbooks/halopsa-12a-brief-export-base64-truncation.md` | Base64 truncation trap on OneDrive upload |
| `runbooks/halopsa-13-mimecast-email-security-quotes.md` | Mimecast quotes |
| `runbooks/halopsa-14-m365-csp-quotes.md` | Microsoft 365 CSP quotes |
| `runbooks/halopsa-15-knowbe4-quotes.md` | KnowBe4 quotes |
| `runbooks/halopsa-15-sentinelone-soc-quotes.md` | SentinelOne / SOC quotes and multi-year options |
| `runbooks/halopsa-16-todo-closure-block.md` | Template-94 to-do item blocks closure |
| `runbooks/halopsa-17-monthly-sales-report-v2.md` | Monthly sales report v2 build record; code in `sales-report-v2/` |
| `runbooks/halopsa-weekly-renewals-deep-dive.md` | Weekly Renewals report spec and ops context |
| `runbooks/halopsa-weekly-ops-retrospective.md` | Weekly operations retrospective report |
| `runbooks/halopsa-ref-ticket-status-id-map.md` | Ticket status ID map (verified 2026-08-18) |
| `runbooks/halopsa-ref-email-templates-status.md` | Email template master status list |
| `runbooks/knowbe4-01-training-notification-templates.md` | KnowBe4 training notification templates |
| `runbooks/simvay-document-brand-guide.md`, `runbooks/simvay-logo-datauris.md`, `runbooks/simvay-report-starter-template.html` | Document brand system and assets |

Dated records (verbatim) in `archive/`: API access test plan (2026-08-19), role snapshots pre-Wave 1 and pre-Wave 3, MCP capability review (2026-08-12), PagerDuty-for-Cyber proposal (2026-08-04), notifications audit (2026-07-17).

Code: `sales-report-v2/` (config.json, analyze2.py, render_report.py), extracted from the project docs; the skill copy in `simvay-monthly-sales-report` may lag.

Related repos: `github.com/rpatrick-simvay/mcp-workers` (HaloPSA, Action1, SentinelOne, halopsa-oauth workers); a clone sits at `C:\Dev\mcp-workers`.
