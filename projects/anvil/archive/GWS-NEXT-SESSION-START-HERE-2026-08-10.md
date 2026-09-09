# GWS — NEXT SESSION START HERE (written 2026-08-10, end of Chrome-setup session)

**State:** OFCS (ofcs.net / Olmsted Falls) Google Workspace API access is FULLY CONFIGURED and Ryan **completed a collector run** for Olmsted Falls on his work desktop (repo clone: `C:\Dev\Anvil` on device "simwsryan"). **The run is UNREVIEWED** — the session's device bridge was bound to ws-ludus (offline) and could not read the run folder. That review is the first job of the next session.

## First actions next session

1. **Review the OFCS run:** `C:\Dev\Anvil\clients\<Client>\evidence\gws\<newest stamp>\` — read `manifest.json` (expect 16 items + CONTEXT row), `client_context.json`, and every `*.error.txt` sidecar. Judge against SETUP-GUIDE-GWS.md Part C checklist: staff AND student rows in GWS-MFA-01 rollup, users captured ≈ console count, caps honest, AdminsWithout2Sv reviewed. `[VERIFY]` watch items: Chrome Policy paging, Education SKU ids, Alert Center filter.
2. If Ryan ran without OU paths in the profile: everything is Unclassified — fill `GwsStaffOuPaths`/`GwsStudentOuPaths` from GWS-ORGUNITS-01's list and rerun (or just re-derive).
3. FIELD-NOTES entries for anything surprising; then matrix mapping + configurator "Google-primary" work (see below).

## Two files Ryan may not have saved (re-delivered in chat 2026-08-10; regenerate from this doc's session records if lost)

| File | Destination |
|---|---|
| `Anvil.cmd` | repo ROOT (`C:\Dev\Anvil\Anvil.cmd`) — double-click Configurator launcher (pwsh-preferring, -STA, error-pause) |
| `CHROME-SETUP-RUNBOOK-GWS.md` | `1-Collection\collectors\gws\` — repeatable per-client Chrome-agent setup runbook with OFCS record |

Both need `git add` + commit. Everything from the 08-09 build session is already pushed (Ryan confirmed 08-10).

## OFCS configuration record (authoritative)

- Model: GCP project **in the school's own tenant** (billing-wall dodge: sign in, skip "Start free", re-paste console.cloud.google.com — no billing account ever linked)
- Project `simvay-anvil` under org ofcs.net; 5 APIs enabled + verified (Admin SDK, Groups Settings, Chrome Policy, Enterprise License Manager, Alert Center)
- Service account `anvil-ofcs@simvay-anvil.iam.gserviceaccount.com`, client ID `107093667844954999559`, no GCP roles
- DWD: all 15 scopes authorized (verified +13 More chip in Admin console)
- Key: `simvay-anvil-579b585af1c4.json` → Ryan's secrets store / local path OUTSIDE repo (suggested `...\Secrets\gws-ofcs.json`). Location = wherever Simvay's password manager is; Anvil never pins it. Exposure response: delete key in console, mint new; client ID/DWD unchanged.
- Impersonation: Ryan's existing OFCS global admin (temporary-engagement decision), passed via `-ImpersonateAdmin` or profile `GwsImpersonateAdmin` (his first run failed on this until passed explicitly — profile likely still needs the key added)

## Automation facts (also in the runbook)

- Permission classifier blocks the Chrome agent from typing the ~21-digit client ID → analyst pastes it (agent sends it fenced, zoom-verified)
- Key download needs explicit analyst approval
- DWD dialog takes the whole 15-scope comma line in one field
- DWD propagation: allow ~5 min before debugging all-groups `unauthorized_client`

## Open backlog (unchanged priorities)

1. OFCS run review (above)
2. SETUP-GUIDE-GWS.md v1.1 rewrite to the school-tenant model
3. Matrix mapping of GWS-* ids (post-validation, as planned)
4. Configurator "Google-primary" session: PrimaryPlatform concept, hide/un-require M365-assumption fields, cross-field rule "IdP=Google but GWS off?", assembly ownership re-keying. Stopgap in use: IdentityProvider custom value "Google Workspace", EmailGatewayVendor empty, M365 collector off where no tenant.
