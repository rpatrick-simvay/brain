# Simvay Anvil — Project Update

Date: 2026-07-28 (end of session). Supersedes `Project-Update-2026-07-07.md`.
Read `Development\SESSION-RUNBOOK.md` first. (Repo copy:
`Development\project-updates\Project-Update-2026-07-28.md`.)

**Session arc:** operator/developer split shipped, then superseded the same day
by the 3-PHASE RESTRUCTURE (1-Collection / 2-Evaluation / 3-Upload + per-client
roots); runbooks streamlined; Ryan's six-item improvement list cleared
(close-guard consoles, branded exec report, standard Blacksmith notes, evidence
packet PDFs, Action1 MCP assessment, compliance-export ingestion); Action1
collector reforged from the Brooklyn run review with live-API verification;
matrix grown to a 304-control running catalog (v3.7); collector-gap review and
manual-evidence-flow validation delivered.

## Structure (the ground truth changed today — trust this, not memory)

Repo root = analyst folder. `1-Collection\` (configurator + 7 collectors +
registry), `2-Evaluation\` (assembly prompt/schema, matrix JSON+XLSX, ingester,
3 renderers), `3-Upload\` (Blacksmith runbooks), `skills\` (.skill packages),
`Development\` (this doc, runbook, skill sources, assessments), root docs
README / ANALYST-GUIDE / FIELD-NOTES (gitignored) / .gitignore. CLIENT DATA:
`clients\<Client>\{config, evidence\<tool>\<UTCstamp>, manual-staging, guides,
run-packages, determinations}` — pre-provisioned by Configurator v0.9 on
profile save. SharePoint client data migrated 2026-07-28 (see
`clients\MIGRATION-LOG-20260728.md`); pre-migration determinations carry
old-layout evidence pointers (historical records — do not "fix").

NOTE (2026-07-28 evening session): the repo now lives at `E:\Projects\Anvil`
on ws-ludus (git repo, main branch).

## Versions at close (ALL awaiting validation runs — banner-check everything)

M365 v2.7 | ADGP v1.5 | S1 v2.9 | Duo v1.6 | Action1 v1.6 | Mimecast v1.4 |
KnowBe4 v1.0 | **Meraki v1.0 (NEW)** | **Auvik v1.0 (NEW)** |
Add-ManualEvidence v1.5 | Configurator v0.9 / manifest **v1.13** | assembly
prompt v1.4 | determination schema v1.2 | Blacksmith runbook v1.3 | matrix
**v3.9** (304 controls) | Render-ExecutiveReport v2.0 | Render-EvidencePackets
v1.0 | Ingest-ComplianceExport v1.1. Both .skill packages rebuilt for the new
layout — RE-SAVE BOTH (installed copies point at dead paths until then).

## ADDENDUM — evening session 2026-07-28: Meraki + Auvik collectors shipped

Backlog item 5 (Meraki, the "biggest single automation win") built and
extended with Auvik for the monitoring half of the NETWORK source.

- **Collect-MerakiEvidence.ps1 v1.0** (`1-Collection\collectors\meraki\`):
  14 evidence items — org/networks, devices+availability, dashboard admins
  (per-admin 2FA), loginSecurity, attributed config change log, firmware
  current+history, uplink statuses (cellular failover), per-network L3+L7
  firewall rules, VLANs ("not enabled" = fact), SSIDs (auth/encryption),
  IDS/IPS+AMP+content filtering, site-to-site VPN, syslog/SNMP/alert
  settings, Air Marshal rogue-AP scan. Every endpoint verified live against
  the Simvay MSP tenant; full live run on City of Brooklyn: 15/15 success.
  **SECRET REDACTION is a design rule:** wireless PSKs, SNMP community
  strings, SNMPv3 passphrases are written as `[REDACTED len=N]` — grep-
  verified no live secret lands in evidence. MSP dashboard keys see every
  client org → `MerakiOrgId` REQUIRED in profile (Action1 pattern: run
  without it lists visible orgs).
- **Collect-AuvikEvidence.ps1 v1.0** (`1-Collection\collectors\auvik\`):
  9 evidence items — tenant, monitored device inventory, monitoring depth
  (SNMP/WMI/login discovery), network/topology inventory, device config
  backup recency, EOL/warranty lifecycle, 30-day alert history, per-device
  uptime+outage statistics, Auvik entity audit log. Live run on
  cityofbrooklyn tenant: 10/10 success (331 devices, 89 networks). Auth is
  Basic (user email + user-scoped key); Simvay cluster is **us5**;
  `AuvikTenantPrefix` REQUIRED (MSP keys see all 13 client tenants). The
  availability stats route is `stat/deviceAvailability/{uptime|outage}` —
  NOT `statistics/...` (verified; wrong guess 404s). Visual network map is
  not API-exportable — stays manual intake (network-diagram); config backup
  CONTENT deliberately not exported (existence+recency is the evidence).
- **Registry**: new `meraki:` (14) + `auvik:` (9) sections; NETWORK section
  note updated (API collectors now exist; manual intake remains for
  non-Meraki gear, client-VPN config, visual map).
- **Configurator manifest v1.13**: Meraki + Auvik entries (zero GUI code, as
  designed). Meraki fields: MerakiOrgId (req), MerakiBaseUrl. Auvik fields:
  AuvikUserName (req), AuvikTenantPrefix (req), AuvikBaseUrl.
- **Matrix v3.9** (+ xlsx regenerated, sheet 'Coverage Matrix v3.9'): 6
  controls → Automated (access-21/22, system protection-11/20/23,
  config-21), 13 → Partial-Automated with MER-*/AUV-* evidence ids
  (audit-15, config-01/02/15/16/18/26, system protection-01/03/32,
  access-15/39, security assessment-03, continuity plan-17). Coverage now:
  Automated 51 | Partial 60 | Manual 150 | no-collector 17 |
  Blacksmith-Native 26.
- **Dev-environment fact:** the cloud Cowork sandbox CAN run PowerShell 7
  (installed at /opt/pwsh) — both collectors were live-tested in-session
  against real APIs. The "no PowerShell in the sandbox" runbook rule was
  written for the OneDrive-mount era; cloud sessions can validate runs
  directly (GET-only collectors).

### Follow-ups from this session

1. **ROTATE BOTH TEST KEYS** — a Meraki dashboard API key and an Auvik API
   key were shared in chat for build/test; regenerate them after validation.
2. Validation runs via the Configurator (profile fields + run buttons) on a
   real client; add Meraki/Auvik to the standing validation pass.
3. Client-VPN config + visual network map remain manual intake; Meraki
   TechStack overlap (FirewallVendor='Meraki MX' etc.) may warrant a
   cross-field rule so manual network guide items don't duplicate what the
   collector now automates.
4. Consider read-only dedicated API users for both platforms (current test
   keys are user-scoped to Ryan).

## Shipped this session

- **Console close guard** (all collectors): keypress-to-close incl. on fatal
  errors (trap), `-NoPause` for automation. Found and fixed en route: the
  2026-07-21 restructure had corrupted every collector's default OutputRoot
  (`clients\profiles\profiles\evidence\...`).
- **Executive report v2.0:** Simvay brand system (hero band + S-mark, KPI bar,
  branded tables), HTML → headless-browser PDF (Edge/Chrome/Chromium;
  ANVIL_BROWSER override; exit 2 + kept HTML when no browser). The brand kit's
  logo assets were ALL corrupt (fully transparent PNGs) — regenerated white +
  teal marks from SimvayLogo_New.png; simvay-brand-styling skill repackaged.
- **Standard Blacksmith note format** (assembly v1.3): `[ANVIL <run-stamp>]`
  marker line + Finding/Cleanup/Missing/Evidence/Basis; notes carry an evidence
  COUNT + determinations-report pointer, never per-file hash lists; staging
  pastes VERBATIM; marker = idempotent re-staging skip signal.
- **Evidence packets** (assembly v1.4): one branded PDF per evidence-carrying
  determination (`<stamp>-evidence-packets\`) — control/status, finding,
  evidence table with verbatim hashes, raw-content appendix (300-line cap).
  PACKETS are what staging uploads; raw JSON stays as the SHA-256 anchor.
- **Action1 v1.5→v1.6** (Brooklyn review + live MCP verification): pager
  continues via explicit from= offsets when an endpoint omits next_page (vulns
  silently truncated 100/4038 with Capped:false); honest Capped; "500+" total
  parse (merged the production-only 2026-07-21 hotfix — version fork closed);
  audit log tries org then ENTERPRISE scope (logs/all and bare logs are not
  valid routes — verified) and records the permission-gap fact on 0 events.
  OrgId now REQUIRED in the Configurator; lookup via Action1 MCP or
  `clients\action1-org-ids.md` (all 20 org UUIDs, pulled 2026-07-28).
- **Compliance-export ingestion** (standard pre-assembly step): Blacksmith
  Compliance-tab CSV export → verbatim archive + scope inventory (+ Completed/
  DueDate/Owner) + matrix catalog diff. Chrome scrape = fallback. Ingested
  Brooklyn (130/130 known = CJIS baseline confirmed) and Simvay (296 tasks, 81
  new stubs) → matrix v3.7 with normalized framework tags (CJIS, NIST,
  CMMC-L1/L2, NIST-800-171, SOC2) and per-framework control refs on stubs.
  XLSX regenerated from JSON (functional format).
- **Assessments** (`Development\assessments\`): Action1 MCP viability (keep
  collector for evidence; MCP for dev verification/lookups/sanity checks —
  now a Hard Rule in the assembly prompt: LIVE MCP DATA IS NEVER EVIDENCE);
  matrix v3.7 gap review; manual-evidence flow validation (flow is
  production-proven; guides must be REGENERATED — old ones hardcode Gabe's
  absolute staging path, fixed in v0.9 to portable client-root paths).

## Standing decisions (additions 2026-07-28)

Evidence packet PDFs are the Blacksmith upload artifact; raw JSON anchors.
Standard note format is mandatory and pasted verbatim. Live MCP/connector data
is never evidence. Compliance CSV export replaces the roadmap scrape; the
matrix is the RUNNING LIST of every control ever discovered (unmapped stubs
carry task text + framework refs until mapped). OrgId is a required profile
field. Ingest/hashing remains the analyst attestation step in the manual flow.
The audit trail in Action1 is tenant-scoped in practice. Meraki/Auvik secrets
returned by APIs (PSKs, SNMP strings) are REDACTED in evidence by design.

## Backlog (priority order)

1. **Validation runs — everything.** One pass covers all NINE collectors (new
   banners + per-client-root paths incl. Meraki v1.0 + Auvik v1.0),
   Configurator v0.9 + manifest v1.13 (profile save pre-provisioning, run
   packages, guide regeneration), exec report + packets on a real assembly,
   staging with the standard note format. Brooklyn Action1 re-run is the
   marquee test (~4,000 vulns expected, audit-log answer either way). Grant
   S1 service user Custom Alerts.view + XDR Inventory.view (carried from
   07-07) and check the Action1 credential's audit-trail grant.
2. **Rotate the Meraki + Auvik test keys** shared in chat this session.
3. **Regenerate manual-evidence guides** for Brooklyn + GLBC from v0.9.
4. **Export-Completed policy rule** in the assembly prompt (22 `*-00` tasks).
5. **S1 SIEM extension** (~19 controls incl. partials); then HaloPSA
   collector (5).
6. Blacksmith previewer test (PDF/TXT/CSV) on the next staging session —
   evidence packets assume PDF previews.
7. Carried: remaining 07-06 data-quality items (Duo DUO-ADMINS-01, M365 audit
   contradiction, ServerAd devices).
