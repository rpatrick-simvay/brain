---
title: Index
type: index
updated: 2026-09-09
---

# Index

Read this first. One line per thing. Follow the link, read STATUS, stop.

## Projects (active)
- **Anvil 2.0**: standalone compliance evidence platform replacing the PowerShell toolkit. Plan v1.1 approved direction; build not started. [[projects/anvil/STATUS]]
- **HaloPSA**: Simvay's PSA; connector, Chrome workflows, quotes, templates, reporting jobs, employee Claude access. 26 runbooks under `runbooks/halopsa-*`; start at [[runbooks/halopsa-01-overview]] section 9 for the map. [[projects/halopsa/STATUS]]
- **Simvay Data Platform** (James): dlt, ClickHouse, dbt, Grafana, Dagster on the Proxmox fleet; PVE-Ansible not yet run on real hosts. Context only; not Ryan's project. [[projects/data-platform/STATUS]]
- **Knowledge repo (this)**: skeleton 2026-09-09; Anvil and HaloPSA populated. [[projects/brain/STATUS]]

## Projects (maintenance)
- **Anvil 1.x**: production evidence toolkit until 2.0 cutover; field notes and open items tracked. [[projects/anvil/OPEN-ITEMS-1x]]
- **Anvil Section 4 Vendor Risk**: scan, score, report pipeline; v2.0 results on Brooklyn and Avon Local; folds into 2.0 Phase 5. [[projects/anvil/archive/Section4-NEXT-SESSION-START-HERE]]

## Areas
- Simvay security services: SOC, fractional CISO program, compliance delivery. `areas/` (to populate)
- Partner track. `areas/` (to populate)

## Clients
- Populate `clients/<slug>.md` as engagements are touched. Known Anvil clients: City of Brooklyn, City of Avon Lake, Olmsted Falls City Schools, Avon Local Schools, Great Lakes Brewing.

## People
- James (direct report; owns the fleet and data platform). Gabe (Anvil day-to-day operator). Populate `people/` as needed.

## Runbooks
- **HaloPSA** (`runbooks/halopsa-*`): 01 overview and gotchas, 02 quotes, 03 email templates, 04 notifications, 05 PDF templates, 06 portal, 07 travel, 08 Action1 routing, 09 Claude access architecture, 10 reporting SQL, 11 to 15 quote playbooks (Action1, Mimecast, M365 CSP, KnowBe4, SentinelOne), 12 scheduled tasks and connector binding, 16 closure block, 17 monthly sales report, weekly renewals and ops reports, plus `halopsa-ref-*` lookup tables.
- **KnowBe4**: [[runbooks/knowbe4-01-training-notification-templates]].
- **Brand**: [[runbooks/simvay-document-brand-guide]], [[runbooks/simvay-logo-datauris]], `runbooks/simvay-report-starter-template.html`.
- To write: Anvil 1.x analyst workflow (from ANALYST-GUIDE), Blacksmith staging, GWS per-school setup, brain session routine.
