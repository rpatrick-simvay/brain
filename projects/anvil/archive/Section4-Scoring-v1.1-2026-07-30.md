# Section 4 — Scoring model v1.1 shipped (2026-07-30)

Follows the Brooklyn scan review (`Section4-Brooklyn-Scan-Review-2026-07-30.md`).
Both files written back to `E:\Projects\Anvil\4-VendorRisk\` and validated
(PowerShell parses clean; new scoring functions unit-tested; ransomware.live and
CDN-detection logic tested against live/synthetic cases). NOT yet git-committed.

## What changed

**Direction (Ryan, 2026-07-30):** stop weighting marketing landing pages as the
primary signal. Prioritize announced breaches, ransomware, bad hygiene, plus
BBB rating, HQ jurisdiction, and data subprocessors. Chosen weight balance:
"Balanced shift." Non-API signals collected via a **Claude-in-Chrome hybrid**.

**scoring-model.json v1.1** — 12-module weight table (sum 100):
breach 12, ransomware 12, attack_surface 13, email_auth 12, kev 10,
BBB 7, jurisdiction 7, subprocessors 5, tls 8, rdap 6, ssllabs 4, headers 4.
Marketing hygiene (ssllabs+headers) cut from 35 → 8. Bands widened
A≥85/B≥75/C≥65/D≥55 (from 90/80/70/60). Added scoring blocks: ransomware,
bbb, jurisdiction, subprocessors. Fixed failure semantics: crt.sh and headers
now score null on block/error (not a floor).

**Collect-VendorScan.ps1 v1.1** — the 5 evidence fixes from the review:
1. SSL Labs default `-SslLabsMaxWaitSec` 0→180 (poll for fresh scan; 0 was
   cache-only and missed 15/20 vendors).
2. Shodan nulls the module when ALL resolved IPs are a CDN/WAF edge
   (org/isp in `cdn_orgs`: cloudflare, incapsula/imperva, akamai, fastly,
   cloudfront, etc.). GoDaddy/GCE shared hosting deliberately NOT treated as
   CDN — those ports are the vendor's box. Only fires with a Shodan membership
   key (InternetDB carries no org).
3. SPF/DMARC DoH fallback (dns.google) when local Resolve-DnsName TXT is empty
   — fixes the microsoft/motorola/civicplus false negatives.
4. crt.sh retried once; empty/failed → null (was a misleading 60 on 10/20).
5. Headers scored only on HTTP < 400; a 403 block page → null (was 0).
Plus: new **VS-RANSOM-01** (ransomware.live v2, keyless), DNS A/AAAA read fix,
and `ScanCoverage`/`LowConfidence` fields in vendor_context (flags composites
built on <6 scored modules).

Note on ransomware.live matching: API keyword search is fuzzy (searching
"motorola" returned an unrelated "Wireless Solutions"). The module filters
strictly — victim-name-contains-needle OR exact domain match — so fuzzy API
hits are dropped. HTTP 404 from the API = "no victims" = score 100 (clean),
not a failure.

## The Chrome enrichment step — NEXT ACTION, not yet built

Three modules (VS-BBB-01, VS-JURISDICTION-01, VS-SUBPROC-01) score from a
`vendor_enrichment.json` the PS scanner reads but never writes. A separate
Claude-in-Chrome pass must produce that file per vendor. Contract (in the PS
header too):

```json
{ "Bbb": { "Rating": "A+", "Complaints12mo": 3, "ProfileUrl": "..." },
  "Hq":  { "Country": "US", "Region": "Utah, USA", "Source": "..." },
  "Subprocessors": { "Published": true, "Url": "...", "Count": 12,
                     "AdversarialJurisdiction": false, "List": [...] } }
```

Any missing block → that module scores null (renormalized away), so an
API-only rescan is still valid. Enrichment lands in the vendor's run dir, or
the newest prior run dir is reused.

To build: a Chrome-driven helper (likely a step in anvil-vendor-evaluation, or
a standalone Enrich-Vendor pass) that per vendor visits bbb.org, the vendor
site/registry for HQ country, and the vendor trust/subprocessor page, then
writes vendor_enrichment.json. ~20 vendors × 3 lookups = heavy; run on-demand,
not every sweep. Cloudflare on bbb.org is why this is browser-based not API.

## Remaining / open

1. **Build the Chrome enrichment pass** (above).
2. **Rescan Brooklyn** with v1.1: `.\Collect-VendorScan.ps1 -ClientName "City of Brooklyn"`
   (~40 min with SSL Labs polling). Then anvil-vendor-evaluation → anvil-vendor-upload.
3. **Populate vendor-master products[]** — KEV matching still can't discriminate
   because products[] is empty (all 20 matched on name only → all scored 100).
4. **HIBP + KEV parse paths still unexercised** (0 hits on Brooklyn). Synthetic
   test against a breached domain (adobe.com) + KEV-heavy vendor (fortinet.com).
5. **git-commit Section 4** — still never committed (runbook Step 0).
6. Consider softening `vuln_cap` for stale banner-inferred CVEs (Citizenserve's
   75 CVEs are 2007–2009 Apache banners).
