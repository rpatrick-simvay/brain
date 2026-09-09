# Section 4 — v2.0 FULL research-tier run on Brooklyn (2026-07-30)

First real end-to-end v2.0 pass: API tier + research tier + deterministic
scorer. Supersedes the API-only re-score in
`Section4-v2.0-PenaltyOnly-Result-2026-07-30.md`.

## What ran

4 parallel research subagents covered all 20 Brooklyn vendors against the
trusted-source allowlist (Maine AG, CA AG, HHS OCR, SEC 8-K, HQ, subprocessor
pages). Each wrote `research_findings.json` into the vendor's run dir. The
deterministic scorer re-scored the sweep. All findings + the scored index are
written to the repo (`4-VendorRisk\scans\<vendor>\<run>\research_findings.json`
and `clients\City of Brooklyn\vendors\scans\20260730-v2research-vendor-scan-index.json`).

## Confirmed breaches (primary source, exact-name/domain match)

- **Diligent Corporation** — Maine AG, breach 2022-05-21, Name+SSN, 1,184
  affected (3 Maine). >3y → penalty 8 + regulated(SSN) 5 = **-13**.
- **Key Bank (KeyCorp)** — CA AG 2022 (Overby-Seawell vendor breach, notice in
  KeyBank's name) + Maine AG 2024-12-13 (1,227 affected). Most-recent within_3y
  = **-20**.
- **Microsoft** (both records) — SEC 8-K Item 1.05, Midnight Blizzard, disclosed
  2024-01-19, incident ~Nov 2023. within_3y = **-20**.

Name collisions correctly REJECTED (not scored): Emergent BioSolutions (≠
emergent.tech), Baldwin Insurance Group BWIN (≠ baldwingroup.com software co),
Marquis/Motility "Software Solutions" (≠ mysoftwaresolutions.com), Vermont
Systems (≠ MyRec). The exact-match guardrail held.

Health/EMS vendors checked at HHS OCR (HealthEMS/Sansio, Life Force, Emergent,
Fire Recovery) — no OCR records found.

## Full v2.0 result (research tier in) — run index 20260730-v2research

Mean 76. Spread 60–93. Grades **1 D / 9 C / 7 B / 3 A**. Avg 6.3 baseline
modules scored/vendor (was ~5 API-only → fewer LowConfidence flags).

| Vendor | v1.1 | v2.0 API-only | v2.0 +research | penalty |
|---|---|---|---|---|
| Life Force Mgmt | 71 C | 53 F | **60 D** | — |
| Citizenserve | 73 C | 60 D | 65 C | — |
| Microsoft Cloud | 89 A | 82 B | **66 C** | breach -20 |
| Microsoft On-Prem | 87 A | 82 B | **66 C** | breach -20 |
| MyRec | 75 B | 61 D | 67 C | — |
| Porter Lee | 75 B | 66 C | 70 C | — |
| My Senior Center | 75 B | 66 C | 70 C | — |
| TAC Computer | 78 B | 68 C | 72 C | — |
| Baldwin Group | 78 B | 68 C | 72 C | — |
| HealthEMS | 80 B | 69 C | 74 C | — |
| Fire Recovery USA | 81 B | 71 C | 75 B | — |
| Emergent | 83 B | 72 C | 75 B | — |
| Software Solutions | 85 A | 72 C | 78 B | — |
| Key Bank | 100 A | 99 A | **79 B** | breach -20 |
| Accurate Controls | 87 A | 79 B | 82 B | — |
| Diligent | 97 A | 96 A | **84 B** | breach -13 |
| CivicPlus | 89 A | 80 B | 84 B | — |
| iWorq | 92 A | 90 A | 90 A | — |
| Motorola | 95 A | 90 A | 93 A | — |
| Oktopost/Hootsuite | 97 A | 95 A | 93 A | — |

The research tier does two things: (1) lifts baselines modestly by populating
jurisdiction (all US/CA = trusted 100) + subprocessors where published, which is
why some API-only scores rose a few points; (2) applies the breach penalties
that actually discriminate — Microsoft A→C, Key Bank A→B, Diligent A→B on
primary-source-confirmed disclosures. Life Force stays the floor (worst hygiene,
no breach). This is the behavior penalty-only was designed for: clean vendors
scored on posture, breached vendors moved hard on confirmed evidence.

## Bands check (now allowed — full v2.0 sweep is in)

Distribution 1D/9C/7B/3A over 20 vendors reads sensibly: the C band is the
crowded middle (small muni-software vendors on shared hosting, thin public
security posture), B is solid, A is reserved for genuinely strong external
posture. No band change recommended yet — one client (n=20) is a thin basis;
re-check after a second client portfolio runs through v2.0. If anything, the D/F
boundary is worth watching (only Life Force lands below C).

## Still open / next

1. **git-commit Section 4 v2.0** — files + skill + research findings all on disk,
   NOT yet committed.
2. Downstream: anvil-vendor-evaluation → anvil-vendor-upload for Brooklyn using
   the v2 scored index (`20260730-v2research-vendor-scan-index.json`).
3. BBB module still null everywhere (needs Claude in Chrome; not attached this
   run) — a future enrichment pass adds it.
4. vendor-master `products[]` still empty → KEV matches on name only.
5. Phase 4 OSINT monitor (weekly create_trigger) — trusted-sources.json is its
   input. Phase 5 matrix/report integration. Parma Heights + Great Lakes Brewing
   zero-vendor auto-fill.
6. Analyst-confirm items surfaced: Microsoft subprocessor jurisdiction (21Vianet
   China), Diligent/Motorola gated subprocessor lists (count unknown, scored on
   "published" only).
