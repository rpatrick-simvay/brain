---
title: HaloPSA status
type: status
updated: 2026-09-09
owner: Ryan
---

# Status as of 2026-09-09

## Where it stands
The Claude Project migration into this repo is complete (see the 2026-09-09 migration LOG entry); project docs are frozen and this repo is canonical. Later the same day, Operations and Sales Executive roles were granted `Can impersonate Users` so they can approve quotes on a client's behalf (runbook 09 section 11.18, API-verified as claim `Iu=1`).

Operational state carried over from the runbooks: the OAuth MCP worker is live and employees are on it (runbook 09, post-go-live incidents 1 to 4 resolved through 2026-09-01); five scheduled reporting tasks are enabled (runbook 12 section 5), with connector binding still nondeterministic (0 to >30 min) and handled by the retry ladder; monthly sales report v2 cost basis ran for August 2026.

## Next three actions
1. Ryan: tell Schilling and Soltis to log out and back in, then have one of them approve a directly-sent quote via impersonation to confirm the flow end to end (15 min).
2. Ryan: review the normalized runbooks for any dash replacement that changed meaning (search ` - ` in a file you know well, 20 min), then commit and push the migration plus today's role change.
3. Claude, next HaloPSA session: work runbook 09 section 10 open item 3 (empty-vs-populated Access Control semantics test on one low-traffic ticket type) and record the result in that runbook and in DECISIONS.md.

## Blocked
Nothing blocked. Runbook 09 open item 11 (narrow the OAuth worker allowlist) waits on deployment step 5.5 by design.
