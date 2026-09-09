# Simvay Anvil — Project Update

Date: 2026-07-29. Supersedes `Project-Update-2026-07-28.md` for session-state;
that doc's structure/decisions sections still stand. Read
`Development\SESSION-RUNBOOK.md` first. (Repo copy:
`Development\project-updates\Project-Update-2026-07-29.md`.)

**Session arc:** Cisco Umbrella collector built, live-verified 13/13 against
City of Brooklyn (org 5362185), and integrated (registry, manifest v1.15,
matrix v3.10). Repo now also cloned to `C:\Dev\Anvil` on simwsryan (in
addition to `E:\Projects\Anvil` on ws-ludus) — all files this session were
committed to the C:\Dev\Anvil working tree; **git commit/push still pending**.

## Shipped

- **Collect-UmbrellaEvidence.ps1 v1.0** (`1-Collection\collectors\umbrella\`):
  12 evidence items — org identity + granted scopes (from OAuth token), admins
  (per-admin 2FA flag + role catalog), protected-egress inventory (networks/
  sites/internal networks/internal domains/network devices), roaming computers
  (status Encrypted|VA|Off, agent version, last sync), virtual appliances
  (route also returns AD connectors + DCs; version at settings.version; health),
  policy list, destination lists WITH contents, identity deployment status,
  request/block summary + per-category, top blocked dest/identities/categories,
  top threats/threat-types (empty = fact), blocked-event sample with identity
  attribution. Full live run: 13/13 success. Secret grep-verified absent from
  evidence.
- **Registry**: new `umbrella:` section (12 entries). **Manifest v1.15**:
  Umbrella entry (UmbrellaApiKey required; UmbrellaOrgId optional ASSERT;
  UmbrellaBaseUrl). **Matrix v3.10** (+ xlsx regenerated, sheet 'Coverage
  Matrix v3.10'): system protection-34 (trusted/encrypted DNS + malicious-
  domain blocking) → **Automated**; UMB-* ids added to 7 more (system
  protection-21/-09, audit-15, system info integrity-01, access-39/-28,
  security assessment-03). Coverage now: Automated 52 | Partial 59 |
  Manual 150 | no-collector 17 | Blacksmith-Native 26.
- **README-Umbrella.md** run guide.

## Hard-won API facts (do not re-learn)

- Umbrella keys are **ORG-scoped** — no MSP-wide key exists (opposite of
  Meraki/Auvik). No org field required; org id comes from the OAuth token
  `sub` claim (`org/{id}/client/{key}`). `UmbrellaOrgId` profile field only
  asserts the expected org (fail-fast on wrong-client key).
- OAuth2 client-credentials at `POST /auth/v2/token` (Basic key:secret);
  token lives 1 h.
- Several routes enforce **max limit=100** (`deployments/v2/policies` 400s
  above it); reports/v2/top-* require from,to,offset,limit — offset is
  mandatory.
- **Per-policy enforcement settings NOT API-readable** (`policies/v2/settings`
  403 regardless of scope) — policy contents stay manual intake
  (dns-policy-config screenshot). `deployments/v2/tunnels` 403 = "SIG not
  enabled" (subscription fact). `admin/v2/organizations` returns [] for
  org-scoped keys.
- **PowerShell trap (load-bearing comment in Invoke-UmbGet):**
  `return Invoke-RestMethod ...` emits a JSON array as ONE un-enumerated
  object → caller's `@()` wraps the whole array as a single item → all-null
  Select-Object downstream. Assign to a variable, then return it (Meraki's
  helper already did this; hit live 2026-07-29).
- Roaming-client status values observed live: Encrypted / VA / Off.

## Standing decision (Ryan, 2026-07-29): Umbrella satisfaction doctrine

**Network-level resolution is the enforcement evidence.** Org networks with
egress registered and resolving through Umbrella's public resolvers get
filtering enforced with NO user context and NO per-device agent. Satisfied =
registered networks + ACTIVE Networks identity + request/block volume
(client_context `NetworkDnsEnforcement.Enforcing`). Roaming-client gaps,
stale agents, and inactive AD/user identity attribution are **CALLOUT
detections** (client_context `CalloutDetections`) - surfaced, never a
control fail on their own; user context is pullable from the SIEM. Encoded
in the collector notes/context, README, and matrix sp-34 satisfaction_logic.

**Umbrella admin 2FA flag (Ryan, 2026-07-29):** `twoFactorEnable` on
admin/v2/users is Umbrella-LOCAL only and NOT trustworthy as an MFA gap -
admins signing in via Cisco Security Cloud Sign-On (SecureX) get Duo MFA
enforced upstream while the flag stays false (known quirk, confirmed for the
Simvay admin account). Collector callout carries the caveat; verify login
path per admin before treating false as a finding. Encoded in UMB-ADMINS-01
note, CalloutDetections text, README, matrix access-39.

## Brooklyn validation-run results (per the doctrine above)

**Enforcing: TRUE** - 1/1 registered network active, 20.1 M requests /
148 K blocked in 30 d. Callouts (informational): 27/36 roaming clients Off,
22 stale >30 d; 6/13 VA-connector records health error|warning; AD Users
0-active-of-249 + AD Computers 0-of-291 (identity attribution inactive -
SIEM covers context); 2/2 admins twoFactorEnable=false (LOCAL flag only - SecureX/Duo enforces MFA upstream, not a gap); 0 threat-categorized
detections in window.

## Follow-ups

1. **ROTATE the Umbrella key** shared in chat this session (key id
   8b62515b...) after validation — same standing rule as the Meraki/Auvik
   keys from 07-28 (those are still pending rotation too).
2. git commit/push `C:\Dev\Anvil` (7 files incl. this doc) and pull on
   ws-ludus.
3. Validation run via Configurator on Brooklyn (profile fields + run button);
   add Umbrella to the standing all-collector validation pass (backlog #1
   from 07-28, still open).
4. Dev-env note: fresh cloud sandboxes do NOT have PowerShell preinstalled —
   this session installed 7.5.2 to /opt/pwsh (the 07-28 note said /opt/pwsh
   exists; it did not in this container).
5. Prior backlog carries: rotate Meraki/Auvik keys, regenerate manual-evidence
   guides, Export-Completed rule, S1 SIEM extension, HaloPSA collector.
