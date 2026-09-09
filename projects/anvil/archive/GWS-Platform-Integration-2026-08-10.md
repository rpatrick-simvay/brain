# GWS Platform Integration — 2026-08-10 (multi-agent build, deployed to C:\Dev\Anvil)

**What shipped:** PrimaryPlatform three-way toggle (M365 / GoogleWorkspace / Hybrid) across Configurator, controls matrix, evaluation prompt, and GWS collector. Built by 3 Opus agents, verified by 2 adversarial QA agents, fix round applied, all 17 files written to Ryan's repo (uncommitted — git add/commit pending). Purpose: Ryan walks Olmsted Falls through collection → evaluation tomorrow (2026-08-11) for a working report.

## Terminology standard (Ryan, 2026-08-10)

**Use "MFA", not Google's "2SV"/"2-Step Verification", in all prose, docs, notes, and reports.** 42 prose occurrences replaced across 11 files same day. Machine field names that mirror Google's Admin SDK KEEP Google's token (`isEnrolledIn2Sv`/`isEnforcedIn2Sv`, derived `Enrolled2Sv`/`Enforced2Sv`/`AdminsWithout2Sv` etc.) so evidence stays schema-comparable across runs — a definitional note explaining this sits in README-GWS.md and EVALUATION-PROMPT.md ("Platform scoping"). Future GWS work: write MFA in anything human-readable.

## Version bumps

| Component | Version | Change |
|---|---|---|
| Anvil-Configurator.ps1 | 1.0 → **1.1** | Op='In' conditions, OptionValues label↔value mapping, collector-level DefaultWhen, hidden-field emit suppression, inert hidden values, pre-1.2 profile platform inference on load |
| collector-manifest.psd1 | 1.19 → **1.20** (ConfigSchema 1.1 → **1.2**) | PrimaryPlatform required choice field; 8 M365-only fields gated VisibleWhen In(M365,Hybrid); IdentityProvider gains first-class 'Google Workspace' option; per-platform collector-toggle defaults; 5 new warning CrossFieldRules |
| control-source-coverage-matrix | 3.15 → **4.0.1** (xlsx renamed **-v4.xlsx**; v3 xlsx moved to 2-Evaluation/_to_delete — Ryan: delete + git add -A) | `source_platforms` (m365/gws/neutral per source token) on all 304 controls; `platform_notes` on 82; GWS-* ids wired into **61 controls**; 13 all-m365 controls have not_applicable rationale for GWS clients; free-text ids canonicalized (MAN-M365-purview-labels-*, MAN-SAT-training-content-*); new Build-CoverageMatrixWorkbook.py regenerates xlsx from JSON |
| EVALUATION-PROMPT.md | 2.3 → **2.4** (both copies identical; .skill zip rebuilt) | Platform scoping section: infer platform from TechStack when PrimaryPlatform absent; wrong-platform absence ≠ gap; neutral-source absence = genuinely missing; `Hybrid` bool ≠ PrimaryPlatform='Hybrid' (it's the on-prem-AD flag — read TechStack.ActiveDirectory); by-definition satisfaction only when vendor actually in TechStack (OFCS: SIEM='SentinelOne' but SentinelOne=$false — must NOT auto-satisfy); Capped honesty in rationale; MFA terminology note |
| Collect-GWSEvidence.ps1 | 1.0 → **1.1** | Cap policy per Ryan: INVENTORY items uncapped to 100k safety ceilings (CHROMEOS 4k→100k, MOBILE 1k→100k, LICENSE 3k→100k/product); SAMPLE caps unchanged (TOKENS 300 users, AUDIT 3k/30d, GROUPS detail 100); `fields` partial-response projection on device lists (same evidence fields, smaller payloads); Capped flags now carried into client_context.json; prose says MFA |
| evaluation-schema.md | 2.2 → **2.3** | optional `primary_platform` top-level field |
| collector-registry.yaml | — | google_workspace section: 17 entries, auth model, profile keys, cap policy |

## OFCS profile updated (schema 1.2) — ready for tomorrow

`clients/Olmsted Falls City Schools/config/*.psd1`: PrimaryPlatform='GoogleWorkspace'; false `Hybrid=$true` removed (district has no AD); ProductionDomains=@('ofcs.net') added (GWS-EMAILAUTH now checks it); **ExcludedAccounts=@() with TODO — Ryan must add confirmed service accounts (gam-admin@, papercutconnector@, etc. from the AdminsWithout2Sv list) BEFORE the evaluation run** or they count as MFA gaps.

## Tomorrow's walkthrough — critical path notes

1. git add -A + commit first (all changes uncommitted; v3 xlsx in _to_delete).
2. Fill ExcludedAccounts in the OFCS profile (see TODO).
3. Re-run collector (v1.1) — the 174916Z run is evaluable but capped at v1.0 bounds; MOBILE hit its 1,000 cap and LICENSE hit 3,000/product, so v1.1 rerun gives true totals. Read Capped from the evidence items, not client_context, for the old run.
4. Manual capture is on the critical path: 4 controls cite `MAN-GWS-admin-security-settings-*`; identification-05 (password policy) and access-19 (session control) have NO other GWS source. Capture per-OU MFA enforcement, password mgmt, session control screens; ingest: `Add-ManualEvidence.ps1 -ClientName "Olmsted Falls City Schools" -Source GWS -Category admin-security-settings -Files <files>`.
5. If reloading OFCS in the Configurator GUI: v1.1 infers GoogleWorkspace on load (fixed defect); confirm the picker before saving.
6. Windows-only checks QA couldn't run on Linux: WPF renders the new non-editable PrimaryPlatform combo; toggles re-derive on picker change; startup seeds M365 toggle on for a fresh form.

## QA record (for audit trail)

QA1 (structural): zero parse errors repo-wide, zero line-ending/BOM damage (CRLF/LF conventions preserved), xlsx verified cell-by-cell (5,168 cells, 0 mismatches), prompt copies SHA-256 identical, no unexpected file touched. QA2 (integration): profile contract verified per-collector (ProductionDomains/ExcludedAccounts stay visible on GWS — collector reads them), headless simulation of all 3 platform profiles clean, matrix source_platforms re-derived independently 0 missing/0 phantom, manual id shape verified against Add-ManualEvidence emission logic, 5-control hand-simulation of the evaluation procedure on OFCS reality. 2 MAJOR defects found and fixed (silent M365 default when loading legacy profiles; hidden M365 fields emitting false Hybrid=$true into GWS profiles), plus 6 minors all fixed.

## Still open (backlog, unchanged)

SETUP-GUIDE-GWS.md v1.1 school-tenant rewrite; Anvil.cmd + CHROME-SETUP-RUNBOOK-GWS.md commit check; GWS-USERS (20k) and groups-list (4k) bounds left as defaults (fine for OFCS at 9,493 users / 216 groups); `system protection-38` flagged Partial-Automated with zero evidence ids (pre-existing).
