# Olmsted Falls City Schools — Manual Evidence Collection Run
Collected 2026-08-10 (Cowork + Claude in Chrome, per ClaudeChromeInstructions.md v1.1).
Staging: `E:\Projects\Anvil\clients\Olmsted Falls City Schools\manual-staging` — 30 files, all 12 items covered.
NOT yet ingested — analyst runs `Add-ManualEvidence.ps1` (hashing/provenance is the attestation step).

## Item status

| # | Item | Files | Source |
|---|------|-------|--------|
| 1 | SIEM retention | `retention-01` | SentinelOne usea1-017, OFCS account scope |
| 2 | NAT / port forwarding | `nat-rules-02` + b–e | Meraki MX, Middle School network |
| 3 | L3 ACLs / inter-VLAN | `acls-03` + b | Meraki MX firewall (L3 routed at firewall) |
| 4 | Cisco IOS switch config | `switch-config-04.txt` | `show running-config`, MS_MDF_R1_9407, IOS-XE 17.3 (analyst-supplied) |
| 5 | Remote-access VPN | `vpn-config-05` + b, c | Meraki MX Middle School — both tabs captured |
| 6 | Network diagram | `network-diagram-06.pdf` | Auvik map export, 2026-08-10 (analyst-supplied) |
| 7 | Umbrella DNS policy | `dns-policy-config-07` + b | dashboard.umbrella.com org 6097671 |
| 8 | Veeam job coverage | `job-status-08` | Veeam B&R 13.0.1.2067 on OCEANUS via BeyondTrust |
| 9 | Offsite replication | `offsite-replication-09` | same console, Backup Copy node |
| 10 | Restore test | `restore-test-10` | same console, History — **absence evidence** |
| 11 | Google Admin security policy | `admin-security-settings-11` + b–g | admin.google.com, ofcs.net |
| 12 | CISA Cyber Hygiene receipts | `cyber-hygiene-report-12` + b–e | HaloPSA tickets 51723/51634/51547/51469/51373 |

## Findings worth carrying into evaluation

- **SDL data retention = 14 days**, against a ≥90-day target. Clear gap. Ingestion 4.6 MB/day; only two sources feeding the SDL (Cisco Duo, Windows Event Logs).
- **2SV enforcement is Off at the `ofcs.net` root and Off for Students** — and the Students OU has "allow users to turn on 2-Step Verification" unchecked, so students cannot enable it. Staff OU is On (overridden), 1-month new-user enrollment, methods = Any.
- **Password policy is identical and weak across every OU** (root/Staff/Students all inherited): strong password NOT enforced, min length 8, reuse allowed, never expires. Google session control = 24 hrs.
- **No restore testing exists.** Veeam History has no Restore node at all — no restore sessions on record — and the analyst confirmed no SIM-FRM-BRV-001 backup test form has ever been completed. Both halves of item 10 are absent.
- **Three VMware backup jobs show Next Run `<Disabled>`** (Full Backup, Full Backup – Discover Video Server, OCEANUS). Only the two Windows Agent jobs and the C2 Cloud copy are actively scheduled. Worth confirming whether that is intentional.
- **Umbrella has exactly one DNS policy** — the Default Policy applied to all identities. No per-OU or per-segment differentiation. SafeSearch on, Log All Requests, allow-only mode off, 3 destination lists (2 block / 1 allow).
- **No port-forwarding rules on the MX** — inbound exposure is 10 1:1 NAT mappings across both uplinks, each with an allowed-remote-IP restriction except the two SMTP Relay entries, which allow no inbound connections at all. IP source-address spoofing protection = Block.
- **VPN: IPsec/L2TP disabled, Cisco Secure Client enabled with SAML** (Duo SSO), split-tunnel to 3 destinations, 8-hour session timeout. The disabled IPsec tab was captured deliberately — the disabled state is itself the evidence.

## Collection notes for next run

- Chrome extension site permissions had to be granted mid-session for `usea1-017.sentinelone.net`, `dashboard.umbrella.com`, and `simvay.halopsa.com`. Grant these before starting.
- Google Admin re-prompts for credentials and may land on the wrong account (rpatrick@simvay.com vs rpatrick@ofcs.net). Confirm the tenant on the "Showing settings for users in" banner before capturing.
- Item 12 is far faster from HaloPSA tickets than from a mailbox — search "OFCSOH - Cyber Hygiene Report". Receipts show sender, recipient, date and attachment filename without opening anything.
- The Auvik map export and the IOS running-config both land in the analyst's Downloads, which is not a Cowork-connected folder. Have the analyst drop them straight into `manual-staging`.
