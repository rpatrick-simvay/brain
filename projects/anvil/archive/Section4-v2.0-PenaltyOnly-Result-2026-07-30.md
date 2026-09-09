# Section 4 — v2.0 penalty-only scorer shipped + Brooklyn re-score (2026-07-30)

Continuation of the night's work. The FIRST DECISION (penalty-only vs
positive-when-clean) was made: **penalty-only** (Ryan, 2026-07-30 day). The
`anvil-vendor-scan` skill was then built and the Brooklyn v1.1 baseline
re-scored under the new model. This is the comparison the START-HERE doc asked
for.

## What shipped

**scoring-model.json v2.0** (written to `E:\Projects\Anvil\4-VendorRisk\`,
overwrites v1.1 on disk — git preserves v1.1). Architecture change:

- Baseline composite is built ONLY from hygiene/exposure/trust modules
  (attack_surface 22, email_auth 18, tls 12, rdap 10, ssllabs 5, headers 5,
  bbb 10, jurisdiction 10, subprocessors 8 — sum 100), renormalized over modules
  that scored.
- breach / ransomware / KEV are now **penalty-only**: clean earns 0, a confirmed
  hit SUBTRACTS from the baseline and can cap the grade. New `breach_announced`
  penalty module fed by the research tier (regulator/SEC-confirmed disclosures).
- Dedupe: an incident announced AND on ransomware.live counts once (as
  ransomware); breach_announced supersedes an HIBP hit for the same incident.
  Total penalty capped at 70.
- Bands UNCHANGED (A85/B75/C65/D55) — per the standing instruction, do not tune
  bands until a full v2.0 sweep with the research tier is in.

**anvil-vendor-scan skill** (`.skill` delivered, description 1012/1024 chars —
installs clean). Three tiers:
1. `anvil_vendor_api_scan.py` — Python API-tier collector (successor to the PS
   scanner), collects VS-*.json, scores NOTHING. Same evidence shapes as v1.1 PS
   so the scorer reads either generation.
2. Research tier — agent + `trusted-sources.json` + `references/research-runbook.md`.
   Agent discovers/extracts breach disclosures (Maine/CA AG, HHS OCR, SEC 8-K)
   and trust signals (BBB, jurisdiction, subprocessors) → `research_findings.json`.
3. `anvil_vendor_score.py` — the ONLY thing that scores. Deterministic guardrail.

Files written to repo: `scoring-model.json`, `trusted-sources.json`,
`scripts/anvil_vendor_api_scan.py`, `scripts/anvil_vendor_score.py`,
`scripts/research-runbook.md`. **NOT git-committed yet.**

## Verification done

- API-tier scan run live against adobe.com + fortinet.com (synthetic tests):
  HIBP parse path EXERCISED (Adobe 2013 breach found), KEV parse path EXERCISED
  (Fortinet = 29 KEV matches incl. Known-ransomware), ransomware.live 200/404
  both handled. These were the two carried-open unexercised parse paths — now
  closed.
- Synthetic penalty vendor (ransomware within_1y + HIBP + KEV-ransomware +
  announced breach flagged same-incident): base 97 → penalties 70 (capped) →
  final 27 F. Dedupe worked (announced breach dropped as same-incident;
  ransomware kept). Grade-cap logic works.
- Scorer re-scored the real Brooklyn v1.1 baseline (run 20260730-031954Z),
  reading the actual staged VS-*.json evidence, no failures.

## Brooklyn v1.1 → v2.0 re-score (API-tier only; research tier not yet run)

Mean 84 → 76. Spread widened from 71–100 to **53–99**. Grades went from
10A/8B/2C/0D/0F to **5A / 4B / 8C / 2D / 1F**.

| Vendor | v1.1 | v2.0 |
|---|---|---|
| Life Force Management | 71 C | **53 F** |
| Citizenserve | 73 C | 60 D |
| MyRec | 75 B | 61 D |
| Porter Lee | 75 B | 66 C |
| My Senior Center | 75 B | 66 C |
| TAC Computer | 78 B | 68 C |
| The Baldwin Group | 78 B | 68 C |
| HealthEMS | 80 B | 69 C |
| Fire Recovery USA | 81 B | 71 C |
| Emergent | 83 B | 72 C |
| Software Solutions | 85 A | 72 C |
| Accurate Controls | 87 A | 79 B |
| CivicPlus | 89 A | 80 B |
| Microsoft Cloud | 89 A | 82 B |
| Microsoft On-Prem | 87 A | 82 B |
| iWorq | 92 A | 89 A |
| Motorola Solutions | 95 A | 90 A |
| Oktopost/Hootsuite | 97 A | 95 A |
| Diligent | 97 A | 96 A |
| Key Bank | 100 A | 99 A |

**This fixes the inflation.** Life Force (worst real exposure — FTP+MySQL+CVEs)
is now correctly the floor at 53 F, not a soft 71 C. The A-tier compressed to
the genuinely-strong (Key Bank/Diligent/Hootsuite/Motorola/iWorq). The middle
(muni-software vendors on shared hosting) spread into C where they belong.
Removing the 34-weight all-100 breach/KEV/ransomware block is what did it: the
baseline now discriminates on real hygiene/exposure signal.

Note: most v2.0 scores carry LowConfidence (<6 scored baseline modules) because
the research tier (bbb/jurisdiction/subprocessors) has not run — those three
modules score null and renormalize away. Running the research tier will add
coverage AND is where real differentiation now comes from.

## Still open / next

1. **git-commit Section 4** — v1.1 was committed; v2.0 files + this skill are NOT.
2. **Run the research tier on Brooklyn** — first real end-to-end v2.0 pass
   (parallel per-vendor subagents → research_findings.json → re-score). THEN
   re-check bands against the fuller distribution.
3. vendor-master `products[]` still empty → KEV discriminates poorly until
   populated for high-criticality vendors.
4. Then anvil-vendor-evaluation → anvil-vendor-upload (downstream unchanged).
5. Phase 4 OSINT monitor (weekly, create_trigger) — trusted-sources.json is its
   input list. Phase 5 matrix/report integration. Parma Heights + Great Lakes
   Brewing have zero vendors (auto-fill target).
