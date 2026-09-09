# Anvil — Google Workspace Collector v1.0 (2026-08-09 session)

**Status:** all 7 files written to `E:\Projects\Anvil` masters. **Nothing committed to git and nothing deployed to the SharePoint working copy** — staged for Ryan's review, same convention as 08-07. Driver: schools on Google Workspace need a collector for this source.

## Shipped

| File | Change |
|---|---|
| `1-Collection\collectors\gws\Collect-GWSEvidence.ps1` | **NEW v1.0** — 16 evidence items (GWS-DOMAIN/ORGUNITS/USERS/MFA/ADMINS/GROUPS/TOKENS/AUDIT-ADMIN/AUDIT-LOGIN/USAGE/CHROMEOS/MOBILE/CHROMEPOLICY/EMAILAUTH/LICENSE/ALERTS-01) |
| `1-Collection\collectors\gws\README-GWS.md` | **NEW** — evidence table, profile keys, known limits |
| `1-Collection\collectors\gws\SETUP-GUIDE-GWS.md` | **NEW** — per-school DWD setup: one SA per client in a Simvay `simvay-anvil` GCP project; school pastes client ID + scope line; informed-decision list for the 3 no-read-only-variant scopes |
| `1-Collection\collector-registry.yaml` | **MOD** — new `google_workspace:` source, 17 entries (16 API + `GWS.security_settings` screenshot) |
| `1-Collection\configurator\collector-manifest.psd1` | **MOD v1.19** — GWS collector entry (fields: `GwsImpersonateAdmin` req, `GwsCustomerId` assert, `GwsStaffOuPaths`, `GwsStudentOuPaths`; TechStackKey `GoogleWorkspace`); ManualEvidence item `gws-security-settings` |
| `1-Collection\collectors\manual\Add-ManualEvidence.ps1` | **MOD v1.9** — new Source `GWS` (category `admin-security-settings`) |
| `1-Collection\collectors\clients\_TEMPLATE-client-profile.psd1` | **MOD** — GWS block + `TechStack.GoogleWorkspace` |

## Design decisions (Ryan-confirmed in session)

- **Auth:** service account + domain-wide delegation, impersonating a super-admin. Key **file path** prompted at runtime (a JSON key can't be typed as SecureString); key stays in the secrets store, never in profile/evidence. Recommended per-school impersonation identity: dedicated `svc-simvay-audit@<district>` super-admin.
- **Per-scope-group tokens** (core / reports / tokens / chromepolicy / licensing / groupssettings / alerts): a school declining an optional grant fails only that group's items. `unauthorized_client` errors name the exact missing scopes.
- **Accepted scope decisions** (Duo-settings pattern — Google has no read-only variant): `admin.directory.user.security` (GWS-TOKENS-01), `apps.licensing` (GWS-LICENSE-01), `apps.groups.settings` (GWS-GROUPS-01 settings half). Collector only GETs; schools may decline, documented in the setup guide.
- **School-aware per-OU design** (Ryan: "global configs don't always tell the full story"): profile declares staff/student OU paths; GWS-MFA-01 derives per-OU 2SV posture with staff-vs-student rollups + admins-without-2SV; GWS-ADMINS-01 resolves ORG_UNIT-scoped delegated admin to OU paths; GWS-CHROMEPOLICY-01 resolves Chrome user+device policies per key OU with inheritance source.
- **GWS-TOKENS-01 is a capped sweep** (admins first, then staff-OU by recency, `-TokenUserCap` 300 default) — tokens.list is per-user; a full student sweep is thousands of calls. Cap + strategy recorded honestly.
- **Admin console security POLICY screens are not API-readable** (per-OU 2SV enforcement config, password mgmt, session length) — per-user `isEnrolledIn2Sv`/`isEnforcedIn2Sv` are the enforcement OUTCOME; policy screens are new manual item `gws-security-settings` with per-OU capture instructions (staff and student OUs captured separately).
- Licensing = control **capability** evidence (Education Standard/Plus ⇒ security center/Vault/investigation tool); Education Fundamentals shows zero assignments — absence + GWS-USAGE-01 = the edition evidence.
- S1 pager lesson applied: pager materializes `Items = @($items)` (the v3.0 line-343/387 DLR bug class).

## Verification done in-session (cloud sandbox, PS 7.4.6)

- Parse: both .ps1 files clean; manifest + template load via `Import-PowerShellDataFile`; registry YAML parses; GWS entry/fields/manual-item asserted; TechStackKeys still unique.
- **Live auth-chain smoke against Google's real token endpoint** with a throwaway local RSA key: PKCS#8 import → RS256 JWT sign/verify → form POST → Google answered `invalid_grant: Not a valid email or user ID` (i.e. JWT structurally accepted) → mapped to the collector's clean FATAL hint. The whole chain up to a real tenant is proven.

## NOT yet done / backlog

1. **Validation run against the first school client** (Ryan: "build and test with a client that requires assessment" — no tenant creds existed at build time). Checklist is in SETUP-GUIDE-GWS.md Part C. `[VERIFY]` flags: Chrome Policy `policies:resolve` paging, current Education SKU ids, Alert Center filter syntax.
2. **Setup with the school:** create the `simvay-anvil` GCP project + per-client SA (guide Part A), school authorizes DWD (Part B).
3. **Matrix mapping** — GWS-* evidence ids are NOT yet referenced by the coverage matrix (v3.15). Map after the first validation run proves field names, same as Meraki/Auvik did.
4. **Configurator sanity pass** — manifest v1.19 entry follows the schema; confirm the GUI renders the GWS toggle + fields and pre-provisions `evidence\gws\` on profile save.
5. **SharePoint working copy deploy + git commit** — Ryan reviews first (08-07 working tree was already staged uncommitted).
6. v1.1 candidates: Reports `drive` application events (sharing audit), Directory `asps` (app passwords) under the existing user.security scope.
