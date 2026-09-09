# Section 4 — Brooklyn scan review & scoring feedback (2026-07-30)

Full sweep (20 vendors, 240 evidence files) reviewed against scoring-model.json v1.0.
Composite math verified: renormalization is implemented correctly — every vendor_context
CompositeScore recomputes exactly. The problem is not the arithmetic; it is what feeds it.

## Verdict

Do NOT re-weight yet. Five evidence-integrity defects distort the inputs more than any
weight change would. Grades are directionally right at the extremes (Diligent 90, Key Bank 93,
Oktopost 90 deserved; Life Force 55 deserved) but the mid-range ordering is mostly noise.
Portfolio: 11/20 D or F, mean 69.3 — largely artifacts.

## Evidence defects (fix in Collect-VendorScan.ps1 → v1.1 before rescoring)

1. **SSL Labs missing on 15/20** — `SslLabsMaxWaitSec = 0` means cached-results-only
   (`fromCache=on`). Only famous domains (Key Bank, Microsoft ×2, Motorola, Oktopost) had
   cache entries; all scored 95–100. The heaviest module (w20) silently dropped for everyone
   else and renormalized away. Filling missing SSL Labs at A(95) moves the mean 69.3 → 73.7.
   Fix: run with polling (e.g. `-SslLabsMaxWaitSec 300`), accept the slower sweep.

2. **Shodan scores the CDN, not the vendor.**
   - Motorola → Imperva Incapsula edge IPs (45.60.12/14.243): ~160 "open ports" are the WAF
     answering everything → module 0, dragging an A+ TLS / DMARC-reject / DNSSEC vendor to 65 D.
   - CivicPlus (Cloudflare), HealthEMS (WPEngine/CF), Software Solutions (HubSpot/CF): the
     standard Cloudflare edge port set (2052–2096, 8080, 8443, 8880) → 12.
   - Emergent (CloudFront, 80/443 only) → 100. Same real exposure class, 88-point spread.
   Fix: when Shodan `Org/ISP` is a known CDN/shared-edge (Cloudflare, Incapsula/Imperva,
   Akamai, Fastly, CloudFront, HubSpot, WPEngine), null the module (unmeasurable passively)
   or score only vendor-attributable IPs. GoDaddy/GCE shared *hosting* (Life Force, MyRec,
   Accurate Controls) is different — those ports likely ARE the vendor's box; keep scoring.

3. **SPF false negatives.** microsoft.com, motorolasolutions.com, civicplus.com all publish
   SPF (verified 2026-07-30 via dns.google DoH) but scans recorded `SpfPresent=false` with
   empty TXT — local `Resolve-DnsName` returned nothing on large TXT record sets (UDP
   truncation pattern). −30 email-module points each, wrongly. Fix: DoH fallback
   (dns.google/resolve) when TXT comes back empty.

4. **crt.sh failure scored as evidence.** 10/20 vendors have `CertCount=0` → scored 60
   "none_found" (CivicPlus, Diligent, Oktopost etc. certainly have CT entries — the query
   failed, not the vendor). Key Bank and Microsoft Cloud scored 50 "expired_only" from a
   stale/capped 200-row response whose newest cert was Feb 2025 — both obviously hold current
   certs. (Note: crt.sh ignores the `limit` param; the key.com query also pulled `xn--key.com`
   lookalike-domain certs — junk for scoring, though interesting as phishing-infra signal.)
   Fix: retry crt.sh, and on empty/failed response set Score=null (module failed), never 60.

5. **Blocked ≠ measured, and inconsistently handled.** Accurate Controls headers module got 0
   because its WAF returned 403 to the scanner (no headers on the block page); Key Bank's
   headers request hard-failed and the module was excluded (null). So being blocked = max
   penalty, total failure = neutral. Fix: only score headers when HTTP < 400 (or at least
   not 403/406/429); otherwise null.

Also: **KEV matched on vendor NAME only** (`MatchedOn` shows just the vendor name, never
`products[]`, contrary to the scoring-model note). All 20 scored 100 — the module currently
adds zero discrimination. And **HIBP + KEV parse paths remain unexercised** (0 hits across all
20), so runbook Step-1 verification for those two modules is still open — run a synthetic scan
against a domain with known breaches (e.g. adobe.com) and a KEV-heavy vendor (e.g. fortinet.com).
RDAP / TLS / Shodan / SSL Labs field reads ARE now live-verified by this sweep.

## Weighting feedback (apply after evidence fixes)

- 50 of 100 points sit on the vendor's **marketing-site hygiene** (ssllabs 20 + headers 15 +
  email 15) vs 30 on compromise-relevant signal (surface 15, KEV 10, breach 5). For municipal
  supply-chain risk (CJIS lens), rebalance toward incident-predictive signals:
  suggested v1.1 weights — ssllabs 15, headers 10, email_auth 15, attack_surface 15,
  tls_certs 10, rdap 10, kev 15, breach 10. (SSL Labs is near-constant 95–100 when it runs —
  low discrimination; KEV/breach deserve more once matching actually works.)
- `renormalize_over_successful_modules` hides failure that correlates with vendor type
  (cache-only SSL Labs, WAF blocking). Keep renormalization but add a visible
  `ScanCoverage: n/8 modules` to vendor_context and flag composites built on <6 scored modules
  as low-confidence rather than presenting them as equally solid.
- Shodan version-inferred CVE piles are stale banner matches (Citizenserve: 75 CVEs dated
  2007–2009; MyRec 32; Life Force 26). `vuln_cap=40` for ANY indexed CVE is blunt — consider
  capping only for KEV-listed (already 15) or CVSS-high-and-recent, else −10.
- Grade bands read like school grades; with current modules most SMB vendors can never reach B.
  Fix evidence first (mean moves ≈69 → ≈75), then re-check the distribution before touching
  bands. If D/F still maps to elevated/critical in Blacksmith for half the portfolio, shift
  bands to A≥85 / B≥75 / C≥65 / D≥55.

## Real findings the scan DID surface (worth analyst action regardless)

- **Life Force Management (55 F)** — EMS billing vendor on a GoDaddy shared box with FTP(21),
  IMAP/POP, and MySQL(3306) exposed + 26 indexed CVEs. Legitimately the portfolio's worst.
- **MyRec (40 surface)** — same GoDaddy shared-host pattern, 32 indexed CVEs.
- **Citizenserve** — self-hosted at Iron Mountain DC, 75 banner-inferred CVEs on 80/443;
  stale Apache banners likely, but worth a look.
- **DMARC p=none / missing** on Citizenserve, CivicPlus, HealthEMS, Software Solutions,
  My Senior Center, Porter Lee, TAC, Baldwin, Emergent — genuine, cheap-to-cite findings.
- **key.com lookalike certs** (`*.xn--key.com`, Let's Encrypt, Jan 2025) — possible phishing
  infra against Key Bank; not a scoring item but a nice OSINT-monitor (Phase 4) test case.

## State / next steps

1. Patch Collect-VendorScan.ps1 → v1.1 (5 fixes above), bump header with verified field facts.
2. Rescan Brooklyn (20 vendors, ~40 min with SSL Labs polling).
3. Then run anvil-vendor-evaluation → anvil-vendor-upload (runbook Step 2).
4. Still open from runbook Step 0: **Section 4 has never been git-committed.**
5. DNS module minor bug: AAAA field shows an NS hostname (accurate-controls) — wrong record
   type read; informational only.
