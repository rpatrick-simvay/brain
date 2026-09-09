# GWS Collector — OFCS Tenant Setup (2026-08-10, Chrome session)

First live execution of the Google Workspace API setup, done via Claude in Chrome with Ryan. Produces the repeatable runbook `1-Collection\collectors\gws\CHROME-SETUP-RUNBOOK-GWS.md` (delivered this session; Ryan to commit).

## Model change vs SETUP-GUIDE-GWS.md v1.0

Google Cloud's new-account onboarding now pushes a payment-method wall. **Dodge confirmed by Ryan:** sign in, ignore/skip the "Start free" flow, re-paste `console.cloud.google.com` in the address bar — console loads with no billing. All 5 APIs are free-tier; no billing account is ever linked. **Revised model:** GCP project lives in the SCHOOL'S tenant, created with the global admin Simvay already holds there (no Simvay GCP org, no cross-tenant trust). Existing global admin doubles as `GwsImpersonateAdmin` (temporary-engagement decision; dedicated svc- super-admin still recommended for standing engagements). SETUP-GUIDE-GWS.md Parts A/B need a v1.1 rewrite to this model — follow-up.

## What was configured (OFCS / ofcs.net)

- Project `simvay-anvil` (in-tenant, Ryan pre-created)
- 5 APIs enabled + dashboard-verified: Admin SDK, Groups Settings, Chrome Policy, Enterprise License Manager, Alert Center
- Service account `anvil-ofcs@simvay-anvil.iam.gserviceaccount.com`, no GCP roles, OAuth2 client ID `107093667844954999559`
- DWD authorized in Admin console with all 15 scopes (verified: user.readonly, orgunit.readonly +13 More)
- JSON key `simvay-anvil-579b585af1c4.json` downloaded → Ryan moves to secrets store as `gws-ofcs.json`

## Agent-automation facts (encoded in the runbook)

- Direct API-library URLs with `?project=` skip all navigation; Enable-click → redirect-to-metrics = enabled signal.
- Permission classifier BLOCKS the agent from typing/form-filling the ~21-digit client ID (sensitive-number filter) — by design the analyst pastes it; agent sends it fenced in chat, zoom-verified from the SA list first.
- Key download requires explicit analyst approval (credential file to Downloads).
- DWD dialog accepts the whole 15-scope line comma-delimited in one field.

## Remaining before first collection run

1. Ryan: key file → secrets store (`gws-ofcs.json`)
2. Profile: GoogleWorkspace toggle + `GwsImpersonateAdmin` (the OFCS global admin) + staff/student OU paths
3. Validation run per SETUP-GUIDE-GWS.md Part C checklist
4. Docs follow-up: SETUP-GUIDE v1.1 (school-tenant model), commit runbook
