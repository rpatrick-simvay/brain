# Section 4 — v1.1 baseline rescan result (Brooklyn, 2026-07-30 night)

Run `20260730-031954Z`, 20 vendors, 0 module failures. All 5 v1.1 evidence
fixes verified working. But the run exposed a scoring-philosophy problem that
is the key input for the skill build.

## All 5 fixes confirmed

- SSL Labs polling: now scored for the CDN/famous set; still null where SSL Labs
  couldn't complete in 180s (fine — renormalized).
- Shodan CDN neutralization: Motorola null (matched `incapsula`), HealthEMS null
  (`cloudflare`,`wpengine`), CivicPlus/Key Bank similar. Life Force correctly
  STILL scored (20) — GoDaddy shared host, not a CDN. Working exactly as designed.
- SPF DoH fallback: Motorola SPF=true source `doh` (was false-negative in v1.0).
- crt.sh: Key Bank TLS = null (crt.sh returned nothing after retry), not a fake
  "expired_only" 50.
- Headers HTTP<400 gate: Accurate Controls headers = null on its 403 block page
  (was 0 in v1.0).

## The problem: absence-of-bad is inflating everyone

Scores vs v1.0 (mean 69 → 84). Distribution: 10 A / 8 B / 2 C / 0 D / 0 F.

Every vendor scores 100 on HIBP breach (w12), CISA KEV (w10), and ransomware
(w12) = 34 of 100 weight, because Brooklyn has NO announced breaches, NO KEV
product matches, NO ransomware listings. We moved weight onto those modules;
for this portfolio they are constant-100, so they add no discrimination and
just compress the range upward. Simultaneously the v1.1 fixes correctly removed
the low scores that WERE discriminating (CDN-noise 0s, block-page 0s).

Net: the passive API tier has almost no discriminating power for a portfolio of
small municipal-software vendors. Life Force Management — exposed FTP + MySQL +
26 CVEs, genuinely the worst vendor — lands at 71 "C" because a 13-weight
Shodan=20 is the only thing pulling against an otherwise all-100 field. Key Bank
hit 100 on just 5 scored modules (flagged LowConfidence=true — the flag worked).

This VALIDATES the architecture pivot: discrimination must come from the
research tier (announced breaches via Maine/CA AG + HHS OCR + SEC 8-K, plus BBB
/ jurisdiction / subprocessors), which currently score null and renormalize
away.

## Scoring-philosophy question for the skill build

Should breach / ransomware / KEV be **penalty-only** modules — neutral baseline
(e.g. not counted, or a mid anchor), subtract only on a confirmed hit — instead
of scoring +100 when clean? "No announced breach" is the norm for nearly every
small vendor; rewarding it as +100×(34 weight) is what inflates the portfolio.
Penalty-only would let the hygiene/exposure signals (Shodan, email, RDAP) and
the research-tier findings actually drive the rating, and make a real breach hit
move the needle hard. Decide this when wiring the scorer; it changes the model
more than any weight tweak.

Corollary: re-check bands only AFTER this decision + research tier are in.
Tuning bands now would just paper over the inflation.

## Full v1.1 scores (run 20260730-031954Z)

Diligent 97 A, Oktopost 97 A, Motorola 95 A, iWorq 92 A, Key Bank 100 A(lowconf),
CivicPlus 89 A, MS Cloud 89 A, Accurate Controls 87 A, MS On-Prem 87 A,
Software Solutions 85 A, Emergent 83 B, Fire Recovery 81 B, HealthEMS 80 B,
TAC 78 B, Baldwin 78 B, My Senior Center 75 B, MyRec 75 B, Porter Lee 75 B,
Citizenserve 73 C, Life Force 71 C.
