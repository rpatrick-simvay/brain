# OFCS GWS Collector Run Review — 2026-08-10

Two runs same day. Run 2 (post-fix) is the keeper: **16/16 Success + CONTEXT**.

## Run 2: 20260810-174916Z — VALIDATED, all [VERIFY] items closed

- GWS-LICENSE-01 now succeeds. License facts: **Education Plus Legacy ×104** (SkuId 1010310002), **Teaching & Learning Upgrade ×3**, **Google-Apps product = Fundamentals ×3000 (Capped=true)**, Vault product 0 assignments.
- Second collector fix applied post-run: added `'1010070001'='Google Workspace for Education Fundamentals'` to the $knownSkus map (it returned SkuName=null in run 2). Written to simwsryan. **Needs git commit; harmless to leave run 2 as-is — the SkuId is in evidence, only the friendly name was missing.**
- Edition takeaway for evaluation: OFCS has Education Plus (Legacy) licenses → security center / Vault / investigation tool CAPABILITY exists for the 104 licensed users; bulk of tenant on Fundamentals.

## Run 1: 20260810-171255Z — 15/16, one bug (fixed)

- GWS-LICENSE-01 failed: `foreach ($pid ...)` at Collect-GWSEvidence.ps1:702 collided with PowerShell's read-only automatic `$PID`. Never reached API. Fixed same day: `$pid` → `$prodId` (lines 702–713).

## Part C checklist (both runs consistent)

| Check | Result |
|---|---|
| 16 items + CONTEXT | ✓ (run 2: 16/16 Success) |
| Staff AND student rows in GWS-MFA-01 | ✓ Staff 634 active (2SV 79.7% enrolled / 87.4% enforced), Student 3889 (0%/0%), Unclassified 77 (28.6%/31.2%) |
| Users captured ≈ console | 9,493, Capped=false (4,600 active / 4,893 suspended). Ryan to eyeball vs console |
| Caps honest | ✓ all capped files self-declare Capped=true (ChromeOS 4,000; Mobile 1,000; Tokens 300 users; audit logs 3,000; license Google-Apps 3,000). Nit: client_context.json shows some capped counts without the flag — cosmetic |
| AdminsWithout2Sv | 9 accounts — mostly service accounts, 2 human-looking: hsguidance@, klarson@ — Ryan to review |

## [VERIFY] watch items — ALL CLOSED

- Chrome Policy paging ✓ (10 OUs, 99–104 user + 57–58 device policies each)
- Education SKU ids ✓ (1010310002 + 1010370001 resolved; 1010070001 was missing from map, now added)
- Alert Center filter ✓ (29 alerts/30d: 12 suspicious login, 10 user phishing reports, 3 spam spike, 2 admin pw reset, 2 suspended)

## Tenant facts worth remembering (OFCS)

- 2,410 active users stale >60 days; students zero 2SV (expected for district)
- Chrome fleet: 1,931 ACTIVE / 1,775 DEPROVISIONED / 294 DISABLED (at 4k cap), 1,302 past AUE, 4 dev mode
- Email auth: SPF ✓ DMARC quarantine ✓ DKIM(google) ✓
- OAuth: 417 distinct apps across first 300 users (capped)

## Next actions

1. git add + commit: collector (both fixes), Anvil.cmd (repo root), CHROME-SETUP-RUNBOOK-GWS.md (collectors/gws/) if not yet committed
2. Ryan: review 9 AdminsWithout2Sv (esp. hsguidance@, klarson@); sanity-check 9,493 users vs console
3. Backlog unchanged: SETUP-GUIDE-GWS.md v1.1 rewrite → matrix mapping of GWS-* ids → Configurator Google-primary session
