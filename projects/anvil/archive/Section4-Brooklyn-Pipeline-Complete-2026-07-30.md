# Section 4 — Brooklyn end-to-end pipeline run COMPLETE (2026-07-30 eve)

Full v2.0 vendor pipeline ran for City of Brooklyn: scan → research tier →
score → evaluate → **live Blacksmith staging**. Plus the security-stack tie-back.

## Evaluation (anvil-vendor-evaluation)
- Input: scored index `20260730-v2research-vendor-scan-index.json` + master
  Blacksmith fields. Output: `clients\City of Brooklyn\vendors\evaluation\
  20260730-202000Z-vendor-evaluation.json` + branded exec (2pp) + remediation
  (6pp) PDFs. 20 vendors: **14 elevated / 6 monitor** (mean 76). Driver: 13
  High/Critical vendors holding sensitive data with MFA Not Enforced.

## Upload (anvil-vendor-upload) — LIVE, tested end-to-end
- Chrome-driven staging into Blacksmith Vendor Admin (Browser 2 / Windows,
  analyst signed in, Brooklyn context). **19 of 20 scanned vendors staged live**
  (Evaluated Risk Rating written, compact one-line + `[ANVIL-VENDOR
  20260730-202000Z]` marker for idempotency). Only the Evaluated Risk Rating
  field was written — Criticality/MFA/data/contacts/owner untouched.
- **UI drift found + resolved:** the Blacksmith Edit Vendor dialog has NO
  separate Note field — only the free-text Evaluated Risk Rating. Ryan chose the
  compact one-line-with-marker format. Runbook should be updated to note this.
- **Key Bank = PENDING:** not in the Active vendor list (portal shows "Right
  Stuff Software" in its place). Scan+eval exist (B 79, two confirmed breaches).
  Analyst: widen Status filter / confirm if inactive or renamed, then re-run.
- **Right Stuff Software = skipped** (portal vendor, no domain, never scanned).
- Staging report: `...\vendors\fill\20260730-202000Z-vendor-staging-report.csv`.

## Security-stack tie-back (Phase 4 auto-import)
- Pulled Brooklyn's real stack from the configurator profile
  `clients\City of Brooklyn\config\City of Brooklyn.psd1` (SharePoint, generated
  2026-07-30 by GabeLister). Enabled: M365, ActiveDirectory, SentinelOne, Duo,
  Action1, KnowBe4, Meraki, Auvik, Mimecast (+ Veeam backup). **Umbrella=false →
  excluded.**
- vendor-master updated: Brooklyn tied to SentinelOne/Action1/KnowBe4/Mimecast
  (existing universal) + 4 new universal records (Cisco Duo, Cisco Meraki, Auvik,
  Veeam). Microsoft Cloud/On-Prem already tied.
- Import CSV (8 new stack vendors, all MFA=Enforced via SSO, Meraki business
  system=Client VPN) + business-systems proposal written to
  `...\vendors\fill\`. **Analyst imports the CSV** (bulk write is analyst-owned).

## Field-correction findings surfaced (for analyst)
- HealthEMS + Life Force Management: portal flags **NO BAA UPLOADED** on PHI
  vendors — obtain/upload BAA (eval master flags didn't carry these).
- Oktopost/Hootsuite: MFA Evidence review due 2026-04-30.
- Portfolio-wide: every Brooklyn vendor shows **MFA Status Not Enforced** — likely
  a data-entry default vs reality; worth a verification sweep (it drove the
  elevated ratings).

## Skills centralized
All five Anvil skills now in `E:\Projects\Anvil\skills\` (+ SharePoint):
anvil-evaluation, anvil-upload, anvil-vendor-scan, anvil-vendor-evaluation,
anvil-vendor-upload. Unpacked sources in `Development\skills\`.

## Working copy = E: (git). NOT YET PUSHED.
- Session consolidated into `E:\Projects\Anvil` (git repo, main →
  github.com/rpatrick-simvay/anvil). Brooklyn config pulled from SharePoint.
- **Stale `.git\index.lock`** blocks commit — delete it by hand (sandbox can't).
- Pre-existing unrelated working-tree mods present (collectors, 2-Evaluation,
  3-Upload) — scope the Section-4 commit or commit all, Ryan's call.
- SharePoint copy still has scoring-model v1.1 / older master EXCEPT the
  vendor-master (updated there too). Reconcile SharePoint ← E after push, or
  treat E as source and re-sync SharePoint.

## Next
1. git-commit + push Section 4 v2.0 from E (remove index.lock first).
2. Analyst imports the stack-vendors CSV; resolve Key Bank pending.
3. Optional BBB Chrome enrichment → re-score. Phase 4 OSINT monitor. Phase 5
   matrix/report integration (Parma Heights + Great Lakes zero-vendor auto-fill).
