# OFCS — First Anvil Evaluation (run 20260811-153000Z, 2026-08-11)

## Scope decision (analyst-directed)
- OFCS has **no Blacksmith profile** (BlacksmithProfile=$false). Ryan directed: evaluate the **NIST CSF-tagged controls of the v4.0.1 master matrix** → **186 controls** (frameworks token `NIST`, incl. `CJIS+NIST`). No compliance export exists/possible; **no carry-forward** (first run). Assessment-only language throughout.
- PrimaryPlatform=GoogleWorkspace (profile-declared) with on-prem AD (TechStack.ActiveDirectory=true) → judged on GWS+AD planes; M365/Mimecast absence never a finding.

## Results
| Status | Count |
|---|---|
| satisfied | 29 |
| partial | 21 |
| gap | 14 |
| insufficient_evidence | 3 |
| manual_attestation_required | 97 |
| not_applicable (Blacksmith-native) | 22 |
| **Total** | **186** |

Missing remediation-reference entry: `config-11` (extend remediation-resources.json).

## The 14 gaps
identification-05 (no password policy either plane), access-18 (blank logon banner), audit-01 (**SDL retention 14 days** — deviates from 90-day Commercial standard, licensing fix), config-23 (4×Win7, 10×Win10-22H2 EOL, 3,428 past-AUE Chromebooks), training-01/-03/-04/-06 (KB4 has **zero training campaigns ever** — phishing sims only), system protection-06 & -15 (no BitLocker: 0 GPOs, 0 escrowed keys), system protection-20 (MX IDS/IPS + AMP disabled), system protection-24 (host firewall: 1 disabled S1 rule + "Disable Windows Firewall" GPO exists), system protection-40 (Office 2019 deployed, no macro policy), config-11 (blocklist-only, no allow-listing).

## Notable partials
identification-03 (staff 2SV enforced 87.4%; **9 admins w/o 2SV incl. super admins**; students no-2SV by design — confirm accepted risk), access-25 (12 Domain Admins incl. 4 service accts; 12 GWS super admins), config-05 (telnet vty 0-4, enable-auth none, SNMPv2c, http server on core switch), audit-15/16/17 (DC audit subcategories off; no Meraki syslog), system protection-38 (DC JUPITER published via 1:1 NAT, LDAPS to 5 external IPs; external VNC path).

## Evidence state
All 10 sources fresh (Aug 10–11): action1, adgp(232447Z), auvik, duo, gws, knowbe4, manual(20260811-001422Z — 30 files, perfect manifest reconciliation), meraki, sentinelone, umbrella. CISA CyHy: 5 consecutive weekly receipts → satisfied. Veeam: server jobs + C2 offsite good; restore-test capture showed History view only → insufficient_evidence; **no Google Workspace data backup evidence** → insufficient_evidence.

## Field notes (action items)
1. **SDL retention 14 days** (console capture) — bundle/licensing review; drives audit-01 gap.
2. **Secrets exposure**: switch capture holds live SNMPv2c community + type-7 RADIUS keys (reversible) → rotate after remediation. **GWS service-account key `ofcs-google.json` sits inside the repo** clients\…\config — move to secrets store per standard.
3. Unmitigated true-positive S1 threat 2026-05-20 (Bk1D2F.tmp, HS-302-KC-New).
4. SIEM rule "OFCS | Duo VPN Success" disabled.
5. GWS collector used InactiveDays=60 vs profile 180 — align next run.
6. One S1 integration LastEntitySeen 2025-05-22 — verify freshness.

## Exclusion suggestions (profile has NO ExcludedAccounts key)
AD: vectra_ldap, smartdeploy, Cisco_Connector, sps-k12-admin (all in Domain Admins). Duo: sa_auvik (bypass), sa_duoauth. GWS: gam-admin, gaps-admin, overdrivelogin, papercutconnector, sps-portal-service, simvay. Add confirmed ones to profile → re-evaluate only.

## Outputs (committed to E:\Projects\Anvil\clients\Olmsted Falls City Schools\evaluation\)
- 20260811-153000Z-evaluation.json (schema 2.0, `scope_basis` documents the NIST-scope direction)
- -evaluation-report.pdf/.html, -gap-analysis.pdf (38 findings), -executive-report.pdf (posture 18% of 164 in-scope)
- -evidence-packets\ (77 packets)

## Next session
- Blacksmith profile creation for OFCS → roadmap generation → re-scope future runs from the export (carry-forward will apply within 90 days of this run for Completed+satisfied).
- Collect: Gmail Safety + Gmail TLS screens, S1 FIM config, Veeam restore-test record, GWS backup evidence (4 insufficient/partial collection to-dos).
- Extend remediation-resources.json with config-11.
