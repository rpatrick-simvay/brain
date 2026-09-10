---
title: HaloPSA decisions
type: decisions
updated: 2026-09-09
tags: [halopsa]
related: [projects/halopsa/STATUS]
---

# Decisions (append-only, one line each, newest last)

- 2026-07-18 (Ryan): quote-screen Send button hidden instance-wide; quotes go out via the opportunity's Send Quote action. Runbook 03 section 5b.
- 2026-07-18 (Ryan): email redesign uses the teal Simvay Proposal identity, no em dashes, white S left of the wordmark. Runbook 03 section 5.
- 2026-08-04 (Ryan): new deals are Opportunities stepped through the workflow, quote raised from the opportunity, never standalone. Runbook 01 section 4, runbook 11.
- 2026-08-04 (Ryan): public-sector clients get tax code EXEMPT. Runbook 02 section 5.
- 2026-08-04 (Ryan): cyber tickets arrive unassigned on Cyber Ops (Analysts); team email on exactly three events (new, client update, closed); rule 27 deleted, rules 57/58/59 created; client-level auto-assign unticked on 8 cyber clients. Runbook 04 section 0.
- 2026-08-12 (Ryan + Claude): every scheduled task is created with `create_trigger` from a live session so custom connectors are captured. Runbook 12.
- 2026-08-17 (Ryan): Sales Order Created popup template 65 trimmed (dead agent variables removed, T/C/M labels). Runbook 04 section 0.
- 2026-08-17 (Ryan): role renames and pipeline access approved as proposed (Karenke role becomes Services Leadership; Executive full, Finance partial read-only). Runbook 09 section 10.
- 2026-08-24 (Ryan): scheduled reports export by joining a local folder to the session; SharePoint upload retired for the binary jobs; SOC Tuning task v2.0 is its own flow and is not touched. Runbook 12 section 5.
- 2026-09-09 (Ryan): HaloPSA knowledge moves from the Claude Project to this repo; project docs frozen, brain canonical.
- 2026-09-09 (Ryan): Operations and Sales Executive roles get Can impersonate Users = Yes so they can approve quotes on a client user's behalf when the quote went to the client directly; Sales Rep (vacant), Executive and Finance unchanged. Runbook 09 section 11.18.
