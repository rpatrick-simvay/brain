# Anvil 1.x open items

Every follow-up, TODO, or "next session" item found in the 28 project docs that a later doc does not clearly show as resolved. Format: date first mentioned, item, source filename in parentheses. Items a later doc resolved (e.g. Section 4 module parse verification, Add-ManualEvidence v1.6 validation, GWS first validation run, GWS matrix mapping, Mimecast probe deploy) are omitted. Where status is uncertain it is stated.

## Security and secrets

- 2026-07-28 Rotate the Meraki dashboard API key and Auvik API key shared in chat for build/test; consider read-only dedicated API users for both platforms (current keys are user-scoped to Ryan). No later doc records rotation. (Project-Update-2026-07-28.md)
- 2026-07-29 Rotate the Umbrella API key (key id 8b62515b...) shared in chat after validation. No later doc records rotation. (Project-Update-2026-07-29.md)
- 2026-08-11 Move the GWS service-account key `ofcs-google.json` out of the repo (`clients\...\config`) into the secrets store per standard. (OFCS-Evaluation-2026-08-11.md, GWS-Setup-OFCS-2026-08-10.md)
- 2026-08-11 Rotate the live SNMPv2c community string and type-7 RADIUS keys captured in the OFCS switch running-config after remediation. (OFCS-Evaluation-2026-08-11.md)

## Git, deployment and housekeeping

- 2026-07-28 Re-save rebuilt .skill packages to the Claude account: the 08-07 session lists FOUR bundles to re-save (anvil-evaluation plus the three vendor bundles); 07-31 also asked for anvil-evaluation re-save. Not confirmed done. (Project-Update-2026-07-28.md, Project-Update-2026-07-31.md, Manual-Audit-and-Fixes-2026-08-07.md)
- 2026-07-30 Confirm Section 4 v2.0 (scoring-model, trusted-sources, scripts, research findings, skills) is committed and pushed from E:; v1.1 was committed, v2.0 was repeatedly noted as uncommitted, and no later doc confirms the push. (Section4-v2.0-ResearchTier-Result-2026-07-30.md, Section4-NEXT-SESSION-START-HERE.md)
- 2026-08-07 Run `Anvil-Configurator.ps1 -ValidateManifest` against the current manifest (v1.16 through v1.20 were only balance-checked in the sandbox). (Manual-Audit-and-Fixes-2026-08-07.md)
- 2026-08-07 Regenerate Avon Lake's manual-evidence guides after manifest v1.16+ (expect 11 items, 7 in the Chrome doc); also regenerate Brooklyn and GLBC guides from the portable-path Configurator (carried since 07-28). (Manual-Audit-and-Fixes-2026-08-07.md, Project-Update-2026-07-28.md)
- 2026-08-07 Delete by hand: `4-VendorRisk\_to_delete\clients-misplaced-20260807\` and `2-Evaluation\_to_delete` (old v3 matrix xlsx), then `git add -A`. (Manual-Audit-and-Fixes-2026-08-07.md, GWS-Platform-Integration-2026-08-10.md)
- 2026-08-07 Next vendor run should confirm no `4-VendorRisk\clients\` folder reappears. (Manual-Audit-and-Fixes-2026-08-07.md)
- 2026-08-10 Commit check: `Anvil.cmd` (repo root) and `CHROME-SETUP-RUNBOOK-GWS.md` (collectors/gws/), plus the GWS collector `$pid` and SKU-map fixes on simwsryan. (GWS-NEXT-SESSION-START-HERE-2026-08-10.md, GWS-OFCS-Run-Review-2026-08-10.md)
- 2026-08-10 Commit the 17-file PrimaryPlatform integration, Add-ManualEvidence v2.0, and the ADGP v1.8 hotfix (all noted uncommitted at the time). (GWS-Platform-Integration-2026-08-10.md, Manual-Evidence-v2.0-2026-08-10.md, ADGP-v1.8-Hotfix-2026-08-10.md)
- 2026-08-10 Windows-only Configurator checks QA could not run on Linux: WPF renders the PrimaryPlatform combo, toggles re-derive on picker change, fresh form seeds the M365 toggle. (GWS-Platform-Integration-2026-08-10.md)

## Validation runs still owed

- 2026-07-28 Standing all-collector validation pass via the Configurator (profile fields + run buttons) on a real client, including Meraki, Auvik and Umbrella; Brooklyn Action1 re-run (~4,000 vulns expected) is the marquee test. Most collectors ran fresh on OFCS 2026-08-10/11, but the formal pass and the Brooklyn Action1 re-run are not recorded. (Project-Update-2026-07-28.md, Project-Update-2026-07-29.md)
- 2026-07-28 Grant the S1 service user Custom Alerts.view + XDR Inventory.view (carried from 07-07) and check the Action1 credential's audit-trail grant. (Project-Update-2026-07-28.md)
- 2026-07-28 Blacksmith previewer test (PDF/TXT/CSV) on the next staging session; evidence packets assume PDF previews. (Project-Update-2026-07-28.md)
- 2026-07-28 Carried 07-06 data-quality items: Duo DUO-ADMINS-01, M365 audit contradiction, ServerAd devices. (Project-Update-2026-07-28.md)
- 2026-08-07 Validation runs on Avon Lake for S1 v3.1 (expect MKTPL-02 and IDENT-01 Success), Add-ManualEvidence v1.7+ (38-file batch plus same-day second ingest), and KB4 v1.1 (Success with ReducedPageFallback or an honest 500 sidecar). v2.0 manual intake was verified in the sandbox and OFCS ingested 30 files, but the Avon Lake runs are not recorded. (Manual-Audit-and-Fixes-2026-08-07.md, Bug-Review-FieldNotes-2026-08-07.md)
- 2026-08-07 Resolve the PowerShell version question: confirm whether Gabe ran the S1 collector under 5.1 (unsupported; README mandates 7.x) with a `$PSVersionTable` diagnostic line. (Bug-Review-FieldNotes-2026-08-07.md)
- 2026-08-10 Sanity-check the OFCS GWS user count (9,493) against the console. (GWS-OFCS-Run-Review-2026-08-10.md)

## Evaluation and matrix backlog

- 2026-07-28 Export-Completed policy rule in the assembly prompt (22 `*-00` tasks). (Project-Update-2026-07-28.md)
- 2026-07-28 S1 SIEM extension (~19 controls including partials), then a HaloPSA collector (5 controls). S1 SIEM ids were partly wired 08-07; the HaloPSA collector was never built. (Project-Update-2026-07-28.md)
- 2026-07-30 Computers in a decommissioned OU are not covered by the ADGP collector (users only); consider an ADGP computer export if assessors ask. (Project-Update-2026-07-30.md)
- 2026-07-31 Quarterly link re-verification of remediation-resources.json (Cisco Umbrella and Mimecast hosts most likely to move). (Project-Update-2026-07-31.md)
- 2026-07-31 Extend remediation-resources.json as ATTEST controls acquire evidence paths; add `sdlc-12` once the client's WAF is known; add `config-11` (missing at the OFCS evaluation). (Project-Update-2026-07-31.md, OFCS-Evaluation-2026-08-11.md)
- 2026-08-07 client_context category counts in Add-ManualEvidence include Failed entries (overstates by failure count); ADGP has the same single-task ConvertTo-Json latent bug the manual collector fixed. (Manual-Audit-and-Fixes-2026-08-07.md)
- 2026-08-07 Live-check the S1 detection-rules endpoint against the console api-doc (S1-DETECT-01 and S1-SIEM-RULES-01 are two projections of one [VERIFY]-marked endpoint); then consider audit-06 Partial to Automated. (Manual-Audit-and-Fixes-2026-08-07.md)
- 2026-08-07 Wire-or-not decision on access-06's forwarding clause (S1-MKTPL-01/02 would fit). (Manual-Audit-and-Fixes-2026-08-07.md)
- 2026-08-07 Assign the surviving mc-tls capture a real evidence id (e.g. MC-TLS-01) so sp-07's dependency is enforceable, and reconcile the mc-tls slug vs registry MC.tls_policies naming. (Manual-Audit-and-Fixes-2026-08-07.md)
- 2026-08-07 Matrix `exported` date still says 2026-07-31 (stale metadata). (Manual-Audit-and-Fixes-2026-08-07.md)
- 2026-08-07 Configurator `Test-AnvilManifest` does not validate ManualEvidence entries (typo'd gates fail silently); cheap validator addition. (Manual-Audit-and-Fixes-2026-08-07.md)
- 2026-08-07 `$pwd` / `$args` variable shadowing in ADGP and KB4; `Collect-M365Evidence.ps1` still uses `$profile = @{}` (if renaming, use `$profileData`, never `$clientProfile`). (Manual-Audit-and-Fixes-2026-08-07.md, ADGP-v1.8-Hotfix-2026-08-10.md)
- 2026-08-07 Nothing downstream reads `TechStack.CisaCyhy`; it only drives the guide gate today. (Manual-Audit-and-Fixes-2026-08-07.md)
- 2026-08-07 Quarterly Mimecast `-ProbePolicyRoutes` re-check and watch the monthly "New API Endpoints" release notes; a probe SUCCESS warrants a dev session. (Manual-Audit-and-Fixes-2026-08-07.md)
- 2026-08-09 GWS v1.1 candidates: Reports `drive` application events (sharing audit) and Directory `asps` (app passwords) under the existing user.security scope. (GWS-Collector-v1.0-2026-08-09.md)
- 2026-08-10 Rewrite SETUP-GUIDE-GWS.md Parts A/B to v1.1 (school-tenant GCP project model, billing-wall dodge). (GWS-Setup-OFCS-2026-08-10.md, GWS-Platform-Integration-2026-08-10.md)
- 2026-08-10 `system protection-38` is flagged Partial-Automated with zero evidence ids (pre-existing). (GWS-Platform-Integration-2026-08-10.md)
- 2026-08-10 GWS-USERS (20k) and groups-list (4k) bounds left as defaults; fine for OFCS, revisit for larger districts. (GWS-Platform-Integration-2026-08-10.md)

## Section 4 vendor risk backlog

- 2026-07-29 Confirm the Vendors CSV import header against a fresh Blacksmith template download; verify `domain_inferred: true` domains before trusting those scans. (Project-Update-2026-07-29-Section4.md)
- 2026-07-29 Check whether Blacksmith exposes a Vendor Admin API (none found in recon; CSV plus Chrome remains the path). (Section4-VendorRisk-Plan-2026-07-29.md)
- 2026-07-29 Phase 4 OSINT monitor: weekly create_trigger sweep across the master (HIBP / KEV / ransomware / status / news, trusted-sources.json as input) plus deep on-demand; alert only on hits. (Section4-VendorRisk-Plan-2026-07-29.md, Section4-v2.0-ResearchTier-Result-2026-07-30.md)
- 2026-07-29 Phase 5 matrix/report integration: third-party / supply-chain controls (CJIS, NIST 800-171 3.x, SOC2 CC9) and vendor risk in the compliance exec report. (Section4-VendorRisk-Plan-2026-07-29.md, Project-Update-2026-07-29-Section4.md)
- 2026-07-29 Greenfield fill targets: Parma Heights and Great Lakes Brewing (0 vendors); propagate the Simvay security stack to every client that uses it (Brooklyn done 07-30, others not). (Project-Update-2026-07-29-Section4.md)
- 2026-07-29 Optional `vendor_scan:` section in collector-registry.yaml (deferred; scanner reads the master directly). (Project-Update-2026-07-29-Section4.md)
- 2026-07-30 Populate vendor-master `products[]` for high-criticality vendors; KEV still matches on vendor name only. (Section4-Scoring-v1.1-2026-07-30.md, Section4-NEXT-SESSION-START-HERE.md)
- 2026-07-30 Build the Chrome enrichment pass (BBB rating, HQ jurisdiction, subprocessors) writing `vendor_enrichment.json`; BBB module is still null everywhere. (Section4-Scoring-v1.1-2026-07-30.md, Section4-v2.0-ResearchTier-Result-2026-07-30.md)
- 2026-07-30 Consider softening `vuln_cap` for stale banner-inferred CVEs (e.g. Citizenserve's 2007-2009 Apache banners). (Section4-Scoring-v1.1-2026-07-30.md)
- 2026-07-30 Re-check score bands after a second client portfolio runs through v2.0 (Avon Local Schools ran 2026-08-06 per the 08-07 addendum, but no bands review is recorded). (Section4-v2.0-ResearchTier-Result-2026-07-30.md)
- 2026-07-30 Analyst-confirm items: Microsoft subprocessor jurisdiction (21Vianet China); Diligent and Motorola gated subprocessor lists (count unknown). (Section4-v2.0-ResearchTier-Result-2026-07-30.md)
- 2026-07-30 Resolve Key Bank pending in Blacksmith (not in the Active vendor list; scan and eval exist at B 79 with two confirmed breaches). (Section4-Brooklyn-Pipeline-Complete-2026-07-30.md, Section4-NEXT-SESSION-START-HERE.md)
- 2026-07-30 Scan the 8 new Brooklyn stack vendors (SentinelOne, Cisco Duo, Action1, KnowBe4, Cisco Meraki, Auvik, Mimecast, Veeam) marked "scan pending", then re-evaluate. (Section4-NEXT-SESSION-START-HERE.md)
- 2026-07-30 Upload MFA evidence for the stack vendors (portal flags MISSING MFA EVIDENCE) or assess/record MFA per vendor; portfolio-wide vendor MFA was never assessed. (Section4-NEXT-SESSION-START-HERE.md)
- 2026-07-30 HealthEMS and Life Force Management: NO BAA UPLOADED on PHI vendors; obtain/upload BAA. Oktopost/Hootsuite MFA evidence review was due 2026-04-30. (Section4-Brooklyn-Pipeline-Complete-2026-07-30.md)
- 2026-07-30 Update the Vendor-Fill-Runbook to state that the Edit Vendor dialog has no separate Note field (compact one-line plus marker is the format); v1.1 of the runbook added the path rule, Note-field text not confirmed. (Section4-NEXT-SESSION-START-HERE.md)

## OFCS (Olmsted Falls City Schools) client follow-ups

- 2026-08-10 Ryan to review the 9 AdminsWithout2Sv (esp. hsguidance@, klarson@); add confirmed service accounts to `ExcludedAccounts` (profile has no key yet) and re-evaluate; suggested exclusions listed in the 08-11 evaluation. (GWS-OFCS-Run-Review-2026-08-10.md, GWS-Platform-Integration-2026-08-10.md, OFCS-Evaluation-2026-08-11.md)
- 2026-08-10 Confirm whether the three disabled VMware Veeam backup jobs are intentional. (OFCS-Manual-Collection-2026-08-10.md)
- 2026-08-11 Create a Blacksmith profile for OFCS, generate the roadmap, and re-scope future runs from the export (carry-forward applies within 90 days of run 20260811-153000Z). (OFCS-Evaluation-2026-08-11.md)
- 2026-08-11 Collect: Gmail Safety + Gmail TLS screens, S1 FIM config, Veeam restore-test record, Google Workspace data backup evidence. (OFCS-Evaluation-2026-08-11.md)
- 2026-08-11 SDL retention is 14 days vs the 90-day standard: bundle/licensing review. (OFCS-Evaluation-2026-08-11.md)
- 2026-08-11 Unmitigated true-positive S1 threat 2026-05-20 (Bk1D2F.tmp, HS-302-KC-New); SIEM rule "OFCS | Duo VPN Success" disabled; one S1 integration LastEntitySeen 2025-05-22 to verify. (OFCS-Evaluation-2026-08-11.md)
- 2026-08-11 Align GWS collector InactiveDays (60) with the profile value (180) on the next run. (OFCS-Evaluation-2026-08-11.md)
- 2026-08-10 Before the next Chrome capture: pre-grant extension site permissions for usea1-017.sentinelone.net, dashboard.umbrella.com and simvay.halopsa.com; confirm the Google Admin tenant banner before capturing. (OFCS-Manual-Collection-2026-08-10.md)

## Anvil 2.0 items that touch 1.x assets

- 2026-09-08 Commit the Anvil 2.0 plan v1.0 and v1.1 PDFs to `C:\Dev\Anvil\Development` when the workstation is back. (Anvil-2.0-Plan-v1.0-2026-09-08.md)
- 2026-09-08 Roadblock R6: re-check the M365 keep/degrade/lose answer against the collector task table (needs the workstation, ~1 hr). (Anvil-2.0-Plan-v1.0-2026-09-08.md)
- 2026-09-08 Roadblock R7: pick parity tenants (one REST-only client, one M365+AD client) and take fresh 1.x runs as the port ship gate. (Anvil-2.0-Plan-v1.0-2026-09-08.md)
- 2026-09-08 Roadblock R8: prove Action1 automation can run the signed Collect-ADGPEvidence script on a DC with outbound HTTPS. (Anvil-2.0-Plan-v1.0-2026-09-08.md)
