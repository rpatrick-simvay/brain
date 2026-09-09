# Simvay Anvil — Section 4 (Vendor Risk Management) session log

Date: 2026-07-29. New Anvil section scoped, planned, and Phases 1-3 built.
Complements the same-day Umbrella session update.

**REPO STATE WARNING (read first):** Section 4 was built against
`C:\Dev\Anvil` on **simwsryan** and was NEVER git-committed/pushed. Mid-session
Ryan moved to **ws-ludus** and git-cloned to `E:\Projects\Anvil` — that clone
therefore does NOT contain `4-VendorRisk\`. The Cowork device bridge stayed pinned
to simwsryan for the session's lifetime and could not write to E: (repeated
attach attempts failed with "not inside a folder connected to Cowork"), so the
complete section was delivered as `Anvil-Section4-bundle.zip` for manual drop
into `E:\Projects\Anvil\`. **Verify `4-VendorRisk\` exists on whichever box is
authoritative before building further, and git-commit it.**

## Decisions (Ryan, 2026-07-29)

- Section 4 = **Vendor Risk Management** (`4-VendorRisk\`), managing Blacksmith's
  Vendor Admin (Vendors + Business Systems).
- Scan engine: **build our own passive scanner** (not BitSight/SecurityScorecard —
  median ~$23.6k/yr priced per company monitored; out of proportion for MSP scale).
- Master vendor list store: **JSON + XLSX in repo** (coverage-matrix pattern).
- OSINT monitoring: **weekly light sweep + deep on-demand** (Phase 4, NOT built).
- **The vendor pipeline stays SEPARATE from compliance** — its own evaluation step,
  its own executive report, its own upload skill. Skills named
  **`anvil-vendor-evaluation`** and **`anvil-vendor-upload`** (Ryan's naming).
- Exec report: **both modes, selectable** (per-client and portfolio roll-up).
- Evaluation basis: **scan score + Blacksmith-tracked fields** (criticality, MFA
  status, sensitive data types, BAA/MFA-evidence flags).
- **Do ALL vendors listed in Blacksmith**, even those not yet run through Anvil.
- Shodan **membership key** provided; stored in a gitignored local config, not
  hardcoded in tracked files, no runtime prompt.

## Blacksmith recon (live, 2026-07-29) — schema ground truth

Vendors edit form: Name, Business Systems (multi-link), Criticality
(Low/Medium/High/**Critical**), Sensitive Data Types (CBI/CJI/PII/SPII in dialog;
list view also shows PHI/ePHI, NPI, PCI, CJIS), **Evaluated Risk Rating = FREE
TEXT** (where the scan score lands), MFA Status (Not Enforced / Enforced /
Enforced via SSO / Enabled / Not Applicable), Vendor Contact/Email/Phone(+Ext),
Internal Owner, Status. Row actions: pencil / **red archive icon (never touch)** /
documents.
Business Systems form: Name, Vendor (single-select), Criticality, data types,
Business Owner, Technical Owner, Privileged + Standard user audit frequencies.
**Vendors has CSV IMPORT ONLY — no export.** Business Systems has both.
Import header (9 cols, from Ryan's template): `Name, Criticality, Evaluated Risk
Rating, MFA Status, Sensitive Data Types, Vendor Contact, Vendor Email, Vendor
Phone, Internal Owner`.

Blacksmith's own Risk-Assessment "Automated Scans" = 7 passive scanners against a
CLIENT domain (SSL/TLS certs, DNS, email auth, RDAP, security headers, Shodan,
SSL Labs). **No vendor-level scanning exists** — that is the whitespace Section 4
fills.

## Shipped

### Phase 1 — master vendor list (DONE)
Scraped Vendors live from ALL 7 clients: Brooklyn 21, Olmsted 11, Avon Lake 23,
Fairview Park 1, Parma Heights 0, Great Lakes Brewing 0, Avon Schools 46 =
**102 raw records → 86 unique vendors**.
- `vendor-master.json` v1.0 — vendor_id, name, aliases, scope, simvay_stack,
  primary_domain (+`domain_inferred`), products, per-client detail blocks,
  unions, flags, scan/osint placeholders.
- Scope rule: **universal = 2+ clients OR Simvay stack; local = single client.**
  13 universal, 73 local.
- `vendor-master.xlsx` — 3 sheets (Master w/ per-client X-matrix + COUNTIF, Raw
  Records 102 rows, Gaps & Notes). recalc clean; counts verified against JSON.
- Canonicalization: CitizenServe→Citizenserve, Action1 Corporation→Action1,
  KnowBe4 Inc→KnowBe4, Cisco Umbrella→Cisco (aliases retained for matching).
- Quirks recorded: Brooklyn system "Cisco" linked to Microsoft On-Premise; Avon
  Schools "SDPC Vendors" is a directory placeholder; Fairview owner "simvay null".
  Only **4 of 102** records carry any Evaluated Risk Rating.

### Phase 2 — passive scanner (DONE; one live vendor run succeeded on ws-ludus)
- `Collect-VendorScan.ps1` v1.0 — full collector pattern (banner, trap/
  Wait-AnvilExit, manifest.csv/json, SHA-256, per-module JSON, vendor_context.json).
- **Four scopes:** `-VendorId`, `-Domain`, **`-ClientName <client>`** (every vendor
  that client uses; case-insensitive + substring with ambiguity guard — "Avon"
  correctly errors naming both Avon clients; writes
  `clients\<Client>\vendors\scans\<stamp>-vendor-scan-index.json` for the
  evaluation step), `-All`. Resolution logic tested against the real master for all
  7 clients + ambiguous/missing cases.
- 10 modules: VS-DNS-01, VS-EMAIL-01, VS-TLS-01 (crt.sh), VS-SSLLABS-01,
  VS-HEADERS-01, VS-RDAP-01, VS-SHODAN-01, VS-HIBP-01, VS-KEV-01, VS-STATUS-01.
  DNS + STATUS informational; other 8 scored.
- **Shodan: membership Host API** (banners, products, CPEs, org/ISP/ASN) when a key
  is present, keyless InternetDB fallback otherwise. Key resolution order: param →
  `vendor-scan.local.psd1` (**gitignored via `*.local.psd1`**) → `$env:SHODAN_API_KEY`.
  Banner prints the active mode.
- `scoring-model.json` v1.0 — weights (ssllabs 20, headers 15, email 15,
  attack_surface 15, tls 10, rdap 10, kev 10, breach 5 = 100), re-normalized over
  successful modules, A–F bands. **Simvay risk INDICATOR, explicitly not a
  commercial rating.**
- `.gitignore` updated: `*.local.psd1`, `/4-VendorRisk/scans/`.
- Verified: pwsh syntax OK; scoring math + re-normalization + bands tested;
  SSL Labs v3 and Shodan InternetDB shapes live-verified via WebFetch.

### Phase 3 — evaluation + upload, both SEPARATE from compliance (DONE)
- **`anvil-vendor-evaluation.skill`** — SKILL.md + `references/vendor-evaluation-prompt.md`
  + `references/vendor-evaluation-schema.md` + 3 scripts.
  Schema v1.0 statuses: `acceptable | monitor | elevated | critical_risk |
  insufficient_scan | not_assessed`. Risk-factor vocabulary (12 stable keys:
  mfa_not_enforced_on_sensitive_vendor, missing_baa, kev_product_match,
  recent_breach, dmarc_not_enforcing, weak_tls, exposed_attack_surface, …).
  Required `remediation_steps` on elevated/critical_risk/insufficient_scan.
  Hard rules: 90-day scan staleness bar; `domain_inferred` blocks `acceptable`;
  KEV/Shodan are indicators not verdicts; live MCP data never evidence;
  universal-vendor scans shared but attribute risk client-specific;
  **risk = scan posture × what the client has riding on the vendor.**
- **`Render-VendorExecReport.py`** — branded exec PDF, `--mode client|portfolio|auto`.
  Distinct output names so both can render into one folder.
- **`Render-VendorGapAnalysis.py`** — remediation PDF, per-vendor cards grouped by
  status, `remediation_steps` verbatim, attribute row, severity-tagged factors.
- **`vendor_report_brand.py`** — shared Simvay brand system (logo data URI extracted
  programmatically from Render-ExecutiveReport.py, not retyped) + headless-browser
  PDF printer. **Section 4 is self-contained — no import from 2-Evaluation.**
- **`anvil-vendor-upload.skill`** — SKILL.md + `references/Vendor-Fill-Runbook.md` v1.0
  (verified UI map, field table, CSV header, staging-report format).
  Mirrors anvil-upload's spine: parallel per-STATUS agents in own tabs (disjoint
  lists), **unrated first**, already-current skip via **`[ANVIL-VENDOR <stamp>]`**
  marker (deliberately different from compliance's `[ANVIL <stamp>]` so the two
  pipelines never collide), replace-don't-append, staging-report CSV as
  cross-session memory.
  Two hard rules: **never archive/delete a vendor or business system** (red row
  icon is the analyst's), **never delete an uploaded vendor document**.
  Writes ONLY Evaluated Risk Rating + note; Criticality/MFA/data types/owners are
  read-only → field problems become `SuggestedFieldCorrections`.
  `insufficient_scan`/`not_assessed` are never staged.
  Auto-fill of known security/technical vendors sourced ONLY from TechStack,
  collector inventory (M365→Microsoft Cloud, ADGP→Microsoft On-Premise,
  SentinelOne, Duo, Action1, Mimecast, KnowBe4, Meraki, Auvik, Umbrella), or the
  master's universal record — never guessed. Bulk CSV is built for the analyst;
  **the agent never clicks import.**
- Verified: both renderers run from the packaged skill dir; PDFs rendered and
  **visually inspected** (2-page client exec, 3-page portfolio, 6-page remediation)
  using a synthetic evaluation JSON built from REAL Brooklyn master data.

## First-run verification still owed
1. `Collect-VendorScan.ps1 -Domain <known>` → open each `VS-*.json` and confirm the
   documented-contract modules parse: **HIBP** casing (Name/BreachDate/PwnCount/
   IsSensitive/DataClasses), **CISA KEV** keys (cveID/vendorProject/product/
   vulnerabilityName/knownRansomwareCampaignUse), **RDAP** (events[].eventAction/
   eventDate, status[], secureDNS.delegationSigned), **crt.sh** (name_value/
   not_after/issuer_name), and now **Shodan Host API** (ip_str/ports/vulns/
   data[].{port,product,version,cpe}/org/isp/asn/last_update). Fix drift → v1.1.
2. Verify `domain_inferred: true` domains before trusting those scans.
3. Confirm the Vendors CSV import header against a fresh template download.

## Backlog — Section 4
- **Phase 4: OSINT monitor** — weekly `create_trigger` sweep (HIBP/KEV/status/news
  across the master) + deep on-demand; alert only on hits.
- **Phase 5: matrix/report integration** — third-party/supply-chain controls (CJIS,
  NIST 800-171 3.x, SOC2 CC9); surface vendor risk in the compliance exec report.
- Registry/manifest: optional `vendor_scan:` section in collector-registry.yaml
  (deferred — the scanner reads the master directly, no per-client profile needed).
- Greenfield fill targets: **Parma Heights and Great Lakes Brewing (0 vendors)**.
- Propagate the Simvay stack to every client that uses it (inconsistently entered
  today) — the highest-value auto-fill win.

## Plan doc
`4-VendorRisk\Anvil-Section4-VendorRisk-Plan.md` (project copy:
`Section4-VendorRisk-Plan-2026-07-29.md`).
