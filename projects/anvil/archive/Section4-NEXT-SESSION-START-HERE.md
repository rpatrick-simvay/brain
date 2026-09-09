# Section 4 (Vendor Risk) — START HERE next session

Updated 2026-07-30 (late). Read this, then
`Section4-Brooklyn-Pipeline-Complete-2026-07-30.md`. The v2.0 pipeline ran
end-to-end for City of Brooklyn AND staged live into Blacksmith.

## State: v2.0 COMPLETE + staged live

- **penalty-only scoring (v2.0)** + **anvil-vendor-scan** skill shipped. Brooklyn
  scanned (API + research tier), scored, evaluated.
- **anvil-vendor-evaluation updated to v1.1**: MFA portal-default "Not Enforced"
  is now treated as UNASSESSED (a data-gap caveat + collection to-do), NOT a
  high-severity risk factor. This was the big correction — it had inflated 14
  vendors to `elevated`. Corrected distribution: **1 elevated / 13 monitor / 5
  acceptable** (Life Force the lone elevated, D band). Skill re-delivered; repo
  docs (`4-VendorRisk\evaluation\VENDOR-EVALUATION-PROMPT.md` + schema) updated.
- **Blacksmith Vendor Admin staged LIVE** (Browser 2, Ryan signed in):
  - 19 of 20 scanned vendors have Evaluated Risk Rating written (compact one-line
    + `[ANVIL-VENDOR 20260730-202000Z]` marker), re-staged with MFA-corrected
    wording ("MFA pending assessment"). Only that field written; nothing else.
  - **8 security-stack vendors CREATED** via the Add Vendor form: SentinelOne,
    Cisco Duo, Action1, KnowBe4, Cisco Meraki (business system = Client VPN),
    Auvik, Mimecast, Veeam — all MFA = Enforced via SSO, Criticality per stack,
    PII where applicable, rating "scan pending". (Umbrella excluded per profile.)
  - **Key Bank = PENDING**: not in the Active vendor list (portal shows "Right
    Stuff Software" in its place). Scan+eval exist (B 79, 2 confirmed breaches).
    Widen the Status filter / confirm inactive, then stage it.
  - Right Stuff Software = skipped (no scan). Staging report:
    `clients\City of Brooklyn\vendors\fill\20260730-202000Z-vendor-staging-report.csv`.

## FIRST ACTIONS next session

1. **git-commit + push Section 4 from E:** (`Projects--Anvil` mount = E:, main →
   github.com/rpatrick-simvay/anvil). **Delete `E:\Projects\Anvil\.git\index.lock`
   by hand first** (sandbox can't). Working tree also has pre-existing unrelated
   mods (collectors, 2-Evaluation, 3-Upload) — scope the commit to Section 4
   unless Ryan wants everything. Tracked Section-4 changes: scoring-model.json
   (v2.0), trusted-sources.json, scripts/*, vendor-master.json (stack tie-back),
   evaluation/ docs, skills/*.skill.
2. **Scan the 8 new stack vendors** (they're "scan pending"): run anvil-vendor-scan
   for their domains, then re-evaluate → their ratings fill.
3. **Resolve Key Bank pending** in Blacksmith.
4. **Upload MFA evidence** for the stack vendors (portal flags MISSING MFA
   EVIDENCE since SSO is claimed) — or the analyst assesses/records MFA per vendor.

## Open field-corrections surfaced (for analyst)

- HealthEMS + Life Force: NO BAA UPLOADED on PHI vendors — obtain/upload BAA.
- Portfolio-wide: vendor MFA was never assessed (portal default). Now handled in
  the eval methodology; the actual assessment is still a to-do.

## Folder note

Work is consolidated in **E:** (git repo). SharePoint copy
(`C:\Users\RyanP\...\03 - Projects\Anvil`, also a git checkout) holds the most
up-to-date CONFIGS and got the vendor-master tie-back too, but still has
scoring-model v1.1 etc. After the E push, reconcile SharePoint ← E (or re-sync).

## Carried / later

- vendor-master `products[]` empty → KEV matches on name only.
- Phase 4 OSINT monitor (weekly create_trigger); Phase 5 matrix/report
  integration; Parma Heights + Great Lakes zero-vendor auto-fill.
- Runbook update: Blacksmith vendor Edit dialog has NO separate Note field — only
  the free-text Evaluated Risk Rating (compact one-line + marker is the format).
