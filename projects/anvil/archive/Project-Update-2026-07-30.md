# Simvay Anvil — Project Update

Date: 2026-07-30. Scope: FIELD-NOTES reingestion (Gabe, 2 entries) — scoring
changes for two controls. Supplements `Project-Update-2026-07-29.md`.
Repo: E:\Projects\Anvil on ws-ludus (authoritative per Ryan; SharePoint sync
not a concern this session).

## Shipped

- **Matrix v3.11** (JSON + XLSX regenerated, sheet 'Coverage Matrix v3.11'):
  - **identification-06** (Prevent reuse of user identifiers): a dedicated
    decommissioned/disabled/old users-computers OU with retained (disabled,
    not deleted) accounts is accepted directory evidence — identifiers stay
    occupied and cannot be reassigned. Policy/process attestation is now
    supplemental. Evidence ids ADGP-USR-01 + ADGP-USR-02; coverage Manual →
    **Partial-Automated**, automation Manual → Semi.
  - **incident response-02** (Automated incident tracking): HaloPSA
    security-incident tickets ARE the tracking mechanism — accept Halo ticket
    evidence (manual staging; no Halo collector, live MCP never evidence)
    alongside S1-THREATS-01. Clients whose incident management is outsourced
    to Simvay's SOC satisfy via the service contract (contract/attestation +
    Halo tickets). Context, not documented in the control: SOC alerting runs
    on PagerDuty + SentinelOne incident management; escalations become
    client-facing Halo tickets.
  - Metadata fix: the JSON `version` field had been stale at 3.1/2026-07-07
    while content advanced through v3.10 (Umbrella) — corrected to 3.11,
    `exported` 2026-07-30. XLSX cleanup: the old generator wrote the literal
    string "None" in empty Framework Control Refs cells; now blank. Verified
    cell-level: only the 8 intended cell changes vs v3.10 beyond that.
- **ADGP collector v1.6**: ADGP-USR-01 and ADGP-USR-02 now export
  `DistinguishedName`, making OU membership visible in the user evidence
  (supports the identification-06 OU logic). README table updated. Encoding/
  line-endings preserved (no BOM, LF).
- **FIELD-NOTES**: both entries marked `[PROCESSED 2026-07-30 → …]` in the
  SharePoint working copy (repo copy has no entries; file is gitignored).

## Owed / backlog

1. **ADGP v1.6 validation run** on a DC (banner check + confirm
   DistinguishedName appears in ADGP-USR-01/-02 JSON). No logic changes
   beyond the two Select-Object additions.
2. Computers in a decommissioned OU are NOT covered by the collector (users
   only) — manual OU screenshot/export remains the path for the computers
   half if an assessor asks. Consider an ADGP computer export if it recurs.
3. Git commit pending for this session's changes (E:\Projects\Anvil).
