# Anvil Section 4 — Vendor Risk Management (`4-VendorRisk`)

Plan doc. Date 2026-07-29. Author: Ryan + Claude (Cowork). Status: **design, pre-build.**
Supersedes nothing. Feeds the Anvil repo (`C:\Dev\Anvil` / `E:\Projects\Anvil`).

---

## 1. What we're building (one paragraph)

A fourth Anvil section that manages Blacksmith's **Vendor Admin** area (Vendors +
Business Systems) the way Sections 1-3 manage Compliance. Three moving parts:
(a) a **master vendor list** we own, that distinguishes universal vendors
(Microsoft, one record, reused everywhere) from local vendors (client-specific);
(b) a **passive vendor scanner** that replicates and exceeds Blacksmith's own
Risk-Assessment automated scans, producing an evidence-grade risk score per
vendor domain; (c) an **OSINT monitor** for breach/news/KEV hits against tracked
vendors. Plus a **fill workflow** that mirrors the anvil-upload skill — it stages
vendor + business-system records into Blacksmith and auto-fills the ones we
already know from compliance/tech-stack data.

Decisions locked (Ryan, 2026-07-29): scan engine = **build our own passive
scanner** (not BitSight/SSC); store = **JSON + XLSX in repo**; monitoring =
**weekly light sweep + deep on-demand**; a **separate Blacksmith fill workflow**
mirroring the compliance upload skill/runbook, auto-filling known
security/technical vendors and systems from compliance management.

---

## 2. Blacksmith recon — verified fields (2026-07-29, live in Chrome)

This is the ground truth the schema mirrors 1:1. Confirmed on
`simvay.blacksmithinfosec.com`, acting on behalf of City of Brooklyn.

**Vendor Admin > Vendors** (Edit Vendor form fields):

| Blacksmith field | Type | Notes |
|---|---|---|
| Name | text (req) | e.g. "Accurate Controls", "Microsoft" |
| Business Systems | multi-checkbox | links to Business System records |
| Criticality | select (req) | Low / Medium / High |
| Sensitive Data Types | checkboxes | CBI / CJI / PII / SPII |
| Evaluated Risk Rating | **free text** (req) | default "Not yet evaluated" — **our scan score lands here** |
| MFA Status | select (req) | Enforced / Not Enforced / (others) |
| Vendor Contact | text | "Support" etc. |
| Vendor Email | email | |
| Phone (+ Ext) | text | |
| Internal Owner | select | Simvay staff dropdown |
| Status | Active/Inactive | list filter |
| Upcoming Document Reviews | derived | doc-review tracker per vendor |

**Vendor Admin > Business Systems** (Add/Edit form fields):

| Blacksmith field | Type | Notes |
|---|---|---|
| Name | text (req) | e.g. "Access Control/Cameras", "Board Docs" |
| Vendor | **single-select** (req) | one vendor per system |
| Criticality | select (req) | Undefined / Low / Medium / High |
| Sensitive Data Types | checkboxes | CBI / CJI / PII / SPII |
| Business Owner | select (req) | client staff |
| Technical Owner | select (req) | client/Simvay staff |
| Privileged Users audit freq | select (req) | Monthly / Quarterly / Annually |
| Standard Users audit freq | select (req) | Monthly / Quarterly / Annually |

**Both pages have CSV Import + Export buttons.** Import is the bulk-staging path;
Chrome-driving is the per-field fallback. Exact export column headers to be
captured at build time (analyst runs one export).

**Blacksmith's own scanners** (Risk Assessments > a client assessment >
Automated Scans tab) — 7 passive scanners against a **single client domain**,
NOT per-vendor. This is the exact stack we replicate:

1. SSL/TLS Certificates (cert transparency logs)
2. DNS Records (A / MX / TXT inventory)
3. Email Authentication (SPF / DMARC — flags `p=none` not enforcing)
4. Domain Registration (RDAP — flags transfer-lock state)
5. Security Headers (graded A-F, counts issues)
6. External Attack Surface (Shodan — open ports across IPs)
7. SSL Labs Analysis (deep TLS grade)

Output shape observed: per-scanner card, COMPLETE/IN-PROGRESS badge, summary
line, expandable "Issues Found (N)", plus a domain-level total ("13 issues").
**Key gap in Blacksmith:** these scans exist only at the client-domain level.
There is zero vendor-level scanning. That is the whitespace Section 4 fills.

---

## 3. Data model

### 3.1 Master vendor list — `4-VendorRisk\vendor-master.json` (source of truth) + regenerated XLSX

Same pattern as the coverage matrix: versioned JSON is truth, XLSX is the human
view, git history is the audit trail.

```
vendor-master.json
{
  "version": "1.0",
  "generated": "<UTCstamp>",
  "vendors": [
    {
      "vendor_id": "microsoft",            // slug, stable key
      "name": "Microsoft",
      "scope": "universal",                // universal | local
      "primary_domain": "microsoft.com",
      "scan_domains": ["microsoft.com","office.com"],
      "products": ["Microsoft 365","Azure AD","Windows"],  // for KEV matching
      "default_criticality": "High",
      "default_data_types": ["PII"],
      "vendor_contact": {"name":"Support","email":"","phone":""},
      "notes": "",
      "last_scan_stamp": "<UTCstamp>",
      "last_scan_score": 82,
      "last_osint_stamp": "<UTCstamp>"
    }
  ]
}
```

`scope: universal` → scan once, apply the result to every client that uses it.
`scope: local` → client-specific vendor, scanned in that client's context.

### 3.2 Client mapping — reuse per-client roots

Each client already has `clients\<Client>\`. Add:

```
clients\<Client>\vendors\
  vendor-map.json            // which master vendors + local vendors this client uses,
                             //   with client-specific overrides (criticality, owner,
                             //   business-system links, data types)
  scans\<vendor_id>\<UTCstamp>\   // scan evidence for local vendors (universal scans
                                 //   live once under 4-VendorRisk\scans\)
  fill\<stamp>-vendor-staging-report.csv   // fill-workflow memory (mirrors upload)
```

Universal-vendor scan results live once under `4-VendorRisk\scans\<vendor_id>\<stamp>\`
and are referenced by every client's `vendor-map.json` — that's the "scan
Microsoft once, apply everywhere" mechanic.

---

## 4. Component A — the passive scanner (`Collect-VendorScan.ps1`)

Built in the existing collector pattern (registry entry, manifest fields,
evidence JSON + SHA-256, secret-redaction rule). Runs per vendor domain. Every
module is a free/public API.

| Module | Source | Free? | What it produces |
|---|---|---|---|
| SSL/TLS certs | crt.sh (cert transparency) | yes | cert inventory, expiry, weak/duplicate |
| DNS records | direct DNS resolve | yes | A/MX/TXT/NS inventory |
| Email auth | DNS TXT parse | yes | SPF present, DMARC policy (flag `p=none`) |
| Domain registration | RDAP | yes | registrar, transfer-lock, age |
| Security headers | HTTP HEAD/GET of vendor site | yes | header grade A-F, missing headers |
| External attack surface | Shodan API | free tier / ~$69/mo paid | open ports, exposed services, banners |
| Deep TLS | SSL Labs API | yes (rate-limited) | TLS grade, protocol/cipher weaknesses |
| **Breach exposure** | HIBP domain search | ~$4/mo key | breached accounts on vendor domain |
| **Known-exploited vulns** | CISA KEV catalog | yes | KEV entries matching vendor `products[]` |
| **Status / uptime** | vendor status page probe | yes | current incident state (best-effort) |

First 7 = Blacksmith parity. Last 3 = our edge over Blacksmith.

**Scoring:** each module contributes to a 0-100 composite with a documented
weight table (`4-VendorRisk\scoring-model.json`, versioned). Output is a
**risk indicator**, explicitly labeled as Simvay-computed, not a BitSight-grade
rating — defensible and honest. The composite + top findings get written to the
Blacksmith **Evaluated Risk Rating** free-text field by the fill workflow.

**Evidence rule (inherits Anvil doctrine):** raw JSON is the SHA-256 anchor;
live API pulls used only for dev verification are never evidence; any secret
(Shodan key, HIBP key) is redacted from evidence output.

**Hybrid slot (future, not now):** `scoring-model.json` leaves a
`commercial_feed` field per vendor so a BitSight/SSC grade could be dropped in
for high-criticality vendors later without reworking the schema.

---

## 5. Component B — OSINT monitor

Two cadences, per Ryan's decision.

**Weekly light sweep** — a scheduled Cowork task (create via `create_trigger`,
NOT local cron — survives session end). Every Monday it sweeps the full
`vendor-master.json`:
- HIBP domain breach corpus (new breaches since last stamp)
- CISA KEV additions matching any vendor `products[]`
- Vendor status-page incident states
- Security news search per vendor name (breach/ransomware/CVE keywords)

Writes `4-VendorRisk\osint\<UTCstamp>-sweep.json` + a dated findings summary,
and pushes an alert (PushNotification / email) only on a real hit. Quiet weeks =
one-line "no new findings" so absence is a recorded fact.

**Deep on-demand sweep** — runs when a vendor review is due or an assessment
kicks off: everything the weekly does plus per-vendor news deep-read, historical
breach timeline, and a written per-vendor OSINT brief for the file.

---

## 6. Component C — the Blacksmith fill workflow (mirrors anvil-upload)

**This is the new piece Ryan asked for.** A skill + runbook pair, structured
exactly like `anvil-upload` + `Blacksmith-Ingestion-Runbook.md`, but targeting
**Vendor Admin** instead of the Compliance Roadmap.

### 6.1 What it does

1. **Reads what we already know.** Pulls the security/technical vendor + system
   list from compliance-management data: the client's TechStack in
   `<Client>.psd1`, the collector inventory (M365, SentinelOne, Duo, Action1,
   Mimecast, KnowBe4, Meraki, Auvik, Umbrella — each *is* a known vendor+system),
   and any vendors named in the compliance export. Cross-references
   `vendor-master.json` to reuse universal vendor records.
2. **Auto-fills the known ones.** For each known security/technical
   vendor+system, it proposes the Blacksmith record fully populated: Name,
   Vendor link, Criticality (from master defaults + client override), Sensitive
   Data Types, Owners (from profile), audit frequencies (from policy defaults),
   MFA Status (from collector evidence where we have it — e.g. Duo/M365 tell us
   MFA state), and Evaluated Risk Rating (from the latest scan score).
3. **Stages into Blacksmith** two ways:
   - **Bulk:** build the CSV in Blacksmith's import format, analyst imports it
     (fastest for first-load of many vendors/systems).
   - **Per-field Chrome:** parallel per-category subagents drive the Vendors and
     Business Systems forms for updates/edits, mirroring the upload skill's
     parallel-tab, disjoint-work-list pattern.

### 6.2 Rules mirrored from anvil-upload (the safety spine)

- **Analyst attests.** The workflow proposes and stages; it never finalizes a
  vendor as risk-accepted. (Blacksmith equivalent of the Complete checkbox — TBD
  at build which control is the attestation act; treat conservatively.)
- **Replace, don't append** on the Evaluated Risk Rating note; standard
  `[ANVIL <stamp>]` marker for idempotent re-staging.
- **Never delete** an uploaded vendor document.
- **Autonomous, real-time reporting**, incomplete/unfilled records first,
  already-current records skipped via marker match.
- **Staging report** written at completion:
  `clients\<Client>\vendors\fill\<stamp>-vendor-staging-report.csv`
  (VendorOrSystem, Name, Action, FieldsFilled, Source, ScanScore, RunStamp,
  Notes) — cross-session memory, read at start of every run.

### 6.3 Where auto-fill values come from (the "known from compliance" mapping)

| Blacksmith field | Auto-fill source |
|---|---|
| Vendor Name / System Name | TechStack + collector registry + compliance export |
| Vendor link | `vendor-master.json` (universal) or created local record |
| Criticality | master default, overridable per client |
| Sensitive Data Types | client profile + system role (e.g. CJI for CJIS clients) |
| Business/Technical Owner | `<Client>.psd1` owner map |
| Audit frequencies | policy defaults (privileged Monthly / standard Quarterly) |
| MFA Status | **collector evidence** — Duo/M365/Umbrella MFA state |
| Evaluated Risk Rating | latest `Collect-VendorScan.ps1` composite + top findings |

Unknown vendors (not in TechStack, not a collector, not in master) are listed
for the analyst to fill by hand — never guessed.

---

## 7. Build order (phased)

**Phase 1 — Foundation (1 session).** `vendor-master.json` schema + seed with
Simvay's universal vendors and Brooklyn's current vendor list (already visible in
Blacksmith). XLSX generator. Per-client `vendor-map.json` schema. Registry +
manifest stubs.

**Phase 2 — Scanner (2 sessions).** `Collect-VendorScan.ps1` with the 7 parity
modules first, live-verified against a real vendor domain (e.g. microsoft.com),
then the 3 edge modules (HIBP/KEV/status). `scoring-model.json` + composite.
Wire into registry/manifest like the other collectors.

**Phase 3 — Fill workflow (2 sessions).** Capture Blacksmith CSV import headers
(one analyst export). Build the fill skill + `Vendor-Fill-Runbook.md` mirroring
anvil-upload. Test bulk import on a sandbox/low-stakes client, then per-field
Chrome on Brooklyn.

**Phase 4 — OSINT monitor (1 session).** Weekly `create_trigger` sweep + deep
on-demand sweep. Alerting.

**Phase 5 — Matrix + report integration (1 session).** Optional: surface vendor
risk in the exec report; add vendor-risk controls to the coverage matrix where
frameworks require third-party/supply-chain risk management (CJIS, NIST 800-171
3.x, SOC2 CC9).

Rough total: ~7 build sessions. Phases 1-2 deliver standalone value (own the
master list + scan). Phase 3 is the highest-leverage piece (the auto-fill).

---

## 8. Open questions for build time

1. Exact Blacksmith CSV import column headers (analyst export — 5 min).
2. Which Blacksmith vendor action is the "attestation"/risk-accept act to never
   automate? (Confirm in UI before the fill workflow writes anything.)
3. Shodan: free tier vs the ~$69/mo membership — depends on how many
   vendor domains and how much port detail we want.
4. Scoring weights — draft a first table, tune against a few known-good vs
   known-bad vendor domains.
5. Does Blacksmith expose a Vendor Admin API? (Would replace Chrome-driving with
   direct writes — worth a 15-min check; none found in this recon, CSV is the path.)
```
