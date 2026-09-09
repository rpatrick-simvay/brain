---
title: Anvil status
type: status
updated: 2026-09-09
owner: Ryan
---

# Anvil: status as of 2026-09-09 (evening)

## Where it stands
- Anvil 1.x is in production. Latest client work: OFCS first evaluation 2026-08-11 (186 NIST controls; 14 gaps, 21 partials). Open 1.x items in OPEN-ITEMS-1x.md; the ones that matter most: three test API keys shared in chat never recorded as rotated; the OFCS GWS service-account key sitting inside the repo; four rebuilt .skill bundles awaiting re-save.
- Anvil 2.0 plan v1.1 (2026-09-09) is the approved direction: standalone platform, Python check framework, PostgreSQL-only, containers on Ubuntu 24.04 CIS L1, Bitwarden credential vault, AD via Action1. Build has not started. The plan PDFs (v1.0, v1.1) exist in chat but are not yet saved to C:\Dev\Anvil\Development (workstation was offline).
- The Claude Code kickoff pack for simvay/anvil2 is prepared (CLAUDE.md, ADRs, phase specs, port specs, schema, skeletons, issue list) and waiting for the repo to exist.
- Roadblocks R1 to R9 (plan Section 14) are all Ryan's to clear; he said he can handle all of them directly.

## Next three actions
1. Ryan, at the work desktop: connect C:\Dev, say "commit the plans" (saves v1.0 and v1.1 PDFs), create simvay/anvil2 and simvay/brain (or rpatrick/brain), clone both to C:\Dev, add the folders, say "build the kickoff pack" and "build the knowledge skeleton". About 20 minutes plus Claude's work.
2. Ryan, portal work (no machine needed): Bitwarden spike (two machine accounts, SDK project create, allowance), two Entra app registrations (portal SSO; test tenant with read-only Graph application permissions), Action1 automation test on one DC. About half a day total.
3. Ryan and James: close decisions 1 to 4 (M365 items, AD channel, PostgreSQL-only, container carve-out) and confirm Ubuntu vs Debian for the Anvil VM. One conversation.

## Blocked
- M365 task-table re-check (R6) needs C:\Dev\Anvil reachable.
- Committing PDFs and packs needs the workstation online.
