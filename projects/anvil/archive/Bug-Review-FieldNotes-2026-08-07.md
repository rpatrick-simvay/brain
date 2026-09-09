# Anvil Bug Review — Field-Notes Entries 2026-08-05/06

**Session:** 2026-08-07 review-only (no changes made to E:\ or SharePoint)
**Scope:** all 8 unprocessed FIELD-NOTES entries flagged by Gabe (+2 agent observations)
**Method:** four parallel review agents (static analysis of E:\ masters + SharePoint deployed copies + run evidence/sidecars), plus live SentinelOne API queries against the Avon Lake tenant via the S1 MCP connector.

---

## Verdict summary

| # | Entry | Bug real? | Reported root cause | Priority |
|---|-------|-----------|--------------------|----------|
| 1 | S1-MKTPL-02 type mismatch (line 343) | **CONFIRMED** | **REFUTED** — real cause found | P2 |
| 2 | S1-IDENT-01 type mismatch (line 387) | **CONFIRMED** | **REFUTED** — same real cause | P2 |
| 3 | Add-ManualEvidence batch dies after 2 files | **CONFIRMED — worse than reported** | Diagnosis correct, scope understated | **P1** |
| 4 | KB4-AUDIT-01 persistent 500 | **CONFIRMED** (upstream: plausible) | Correct (no 5xx retry) | P3 |
| 5 | Mimecast console URL wrong | **REFUTED as stated** — but real gap | Guide has NO URL at all | P4 |
| 6 | KnowBe4 console URL wrong | **CONFIRMED** (doc text) | Correct | P4 |
| 7 | KnowBe4 MSP account-switch hop missing | **CONFIRMED** (absent from guides) | Correct | P4 |
| 8 | Mimecast Consolidated Policy Viewer | **CONFIRMED** (guide says scroll index) | Correct | P4 |
| 9 | Meraki dual VPN tabs not in guide | **CONFIRMED** (absent) | Correct | P4 |
| 10 | Veeam multi-console assumption | **CONFIRMED** (absent) | Correct | P4 |
| 11 | Network diagram per-site assumption | **CONFIRMED** (absent) | Correct | P4 |
| 12 | ADGP docs stale (all sub-claims) | **CONFIRMED** (every sub-item verified) | Correct | P3 |

All four verification agents worked from the staged E:\ masters, SharePoint deployed copies, error sidecars, manifests, and RUN.txt files. No file was modified anywhere.

---

## 1–2. SentinelOne collector — both bugs confirmed, but Gabe's theories are wrong

### What the sidecars show
Both failures: `System.ArgumentException: Argument types do not match`, stack traces containing **only** the Collect scriptblock and line 427 (`& $task.Collect`) — no `Get-S1Paged`/`Invoke-S1Get` frame. The HTTP calls succeeded; the throw is at the consumption site.

### The real root cause (shared)
`Get-S1Paged` (line 141/153) returns `Items` as a live `System.Collections.Generic.List[object]`, never materialized. Lines 343 (`foreach ($app in @($apps))`) and 387 (`Captured = @($page.Items).Count; Assets = @($page.Items)`) are **the only two places in the script** that apply `@( )` directly to that raw List — and they are exactly the two tasks that failed. All 17 other `.Items` consumers (pipeline, bare foreach, `@()` around a pipeline) succeeded in the same run. Controlled A/B: `Collect-KB4Evidence.ps1` uses the byte-identical consumption shape but its pager materializes `Items = @($items)` from an ArrayList — succeeded 10/10 across two runs on the same workstation. Prior art: the v2.4 changelog records S1-BLOCK-01 hitting this exact message in v2.3 with the same helper, fixed by abandoning it for an ArrayList.

Suspected engine layer: DLR binder over the List's value-typed struct enumerator ("Argument types do not match" is a System.Linq.Expressions resource string). Mechanism is inferred (no PowerShell in the review sandbox); the discriminator is established from evidence.

### Why Gabe's theories don't hold
- MKTPL-02: `.Items` can never be a scalar/non-enumerable — line 141 hard-constructs the List unconditionally. And `foreach ($x in @($scalar))` is well-defined anyway.
- IDENT-01: assigning `$null` into a hashtable literal cannot raise ArgumentException, and **live API check (this session)**: `xdr/assets/identity` for Avon Lake returns `pagination.totalItems: 941` — a real integer, not null. `Capped` is always `[bool]`. No JArray exists anywhere in this pipeline (Invoke-RestMethod never produces Newtonsoft types).

### Live API context (S1 MCP connector, Avon Lake tenant, 2026-08-07)
- `singularity-marketplace/applications?limit=100` → HTTP 200, **6 apps** (Cisco Duo, M365 Log Ingestion, Entra ID, Entra ID Protection, Teams, Mimecast), `totalItems: 6`, `nextCursor: null`. Matches S1-MKTPL-01's captured evidence exactly. Each app carries a `scopes` array (per-instance detail) — the data line 343's loop body wants is there and healthy.
- `xdr/assets/identity?limit=5` → HTTP 200, `totalItems: 941`, non-null `nextCursor`. Licensing confirmed working (matches `SingularityIdentityLicensed: true` in client_context). Note: at `-Limit 100 -MaxPages 3` the collector will capture 300 of 941 and set `Capped = $true` — expected, not a defect.
- Conclusion: **both endpoints are healthy; the failures are 100% local script bugs.** A fixed collector should collect both items successfully on the next run.

### Proposed fix (S1 v3.1 — not applied)
1. **One line, fixes both:** line 153 `Items=$items` → `Items=@($items)` (mirrors Get-KB4Paged:136). Blast radius reviewed across all 19 consumers: none indexes/mutates the list — object[] is safe or better everywhere.
2. **Secondary defect (worth same pass):** IDENT-01's try/catch wraps local object construction inside a licensing-shaped catch — narrow the try to the API call only, else a future local error could be swallowed into a false `IdentityInventoryAvailable = $false` compliance fact. Same too-wide-try pattern at S1-RANGER-01 (lines 296–306).
3. Latent: `$manifest` (line 413) is also a Generic.List — convert to ArrayList to match KB4 and kill the defect class.
4. Banner v3.0 → v3.1 in all three places + README-S1 version paragraph + changelog entry citing the v2.3/v2.4 precedent.

### Open question for the fix session
Script header and README-S1 mandate **PowerShell 7.x**; the field note was filed as PS 5.1. If Gabe ran 5.1, that's an unsupported-configuration finding on its own — `Invoke-S1Get`'s HTTP-error text parsing depends on PS7 `ErrorDetails` semantics, so the licensing-absence catch may also misbehave on 5.1. One diagnostic line at the top of the next run settles it (`$PSVersionTable`). Suggested pre-fix trace (run once, then delete): print `$apps.GetType().FullName` alone before line 343 — if it prints anything other than `List[object]`, the analysis is wrong.

---

## 3. Add-ManualEvidence — confirmed, and the blast radius is bigger than reported

### Diagnosis verified, with one major correction
The reported chain is correct step-by-step (empty-array-from-`if` → `$null` → scalar after first `+=` → `op_Addition` throw on second `+=`; exact exception text matches the PSObject LHS shape). Deployed copy line 124; **the identical line exists in master v1.6 at line 146 — the bug is in the authoritative code too** and predates v1.5.

**Correction — "resume path unaffected" is wrong.** The `@(...)` in the *then* branch is enumerated on the way out of the `if` just like the else branch, so a **1-entry** intake-log reloads as a scalar and the *first* `+=` of the next invocation throws. Since the only run a fresh invocation can ever complete is a single-file run (which writes a 1-entry log), the practical truth is:

> **The script can only ever ingest ONE file per client per UTC day. Every other invocation shape fails.** The README's own "repeat for each category" workflow cannot work.

The resume-failure variant is nastier than the fresh one: it leaves a *valid but stale* manifest (file on disk, no manifest row) — a "manifest missing" check won't catch it; only file-vs-manifest reconciliation will.

### Also found
- **Version drift is operational, not cosmetic:** deployed copy is v1.5, which has **no CISA source in its ValidateSet** — the Brooklyn CISA Cyber Hygiene ingest fails at parameter binding on the analyst's copy. (Consistent with FIELD-NOTES: "v1.6 NOT YET VALIDATED".)
- Master v1.6 banner inconsistency: ASCII art says v1.5 (line 69), Write-Host says v1.6 (line 73).
- Probable EvidenceId off-by-one on fresh runs: `(@($log).Count + 1)` where `@($null).Count` is 1 → first file may get `-002`. 30-second console check during the fix.
- The `$x = if ... { @() }` anti-pattern occurs exactly once across both trees (this line). All other accumulators are safely seeded with direct `@()` assignment.

### Proposed fix (v1.7 — not applied)
1. Replace `$log` accumulator with `Generic.List[object]` + `.Add()` — the ADGP collector already uses exactly this pattern (line 239); it kills the `+=` hazard permanently and fixes the off-by-one. (Minimal alternative: `$log = @( if (Test-Path $logPath) { ... } )`.)
2. Wrap the copy loop in `try/finally`; write intake-log + both manifests + client_context from `finally` so a partial run still leaves a hashed, citable manifest. Per-file try/catch recording `Status=Failed` rows, mirroring ADGP's failure semantics.
3. Fix the v1.5 banner string; ship as a single v1.7; **re-sync the SharePoint deployed copy** (it's a full version behind).
4. Separate work item (evaluation layer, not this script): treat a manual run folder with evidence files but no/stale manifest as a **failed ingest**, not an empty evidence set — needs file-vs-manifest reconciliation in EVALUATION-PROMPT/skill.
5. Regression test: the 38-file Avon Lake staging folder, run **twice on the same UTC day** to cover the resume path.

---

## 4. KB4-AUDIT-01 — failure confirmed; 5xx retry alone won't fix it

- Both manifests confirm: KB4-AUDIT-01 `Failed` in runs 20260804-181722Z **and** 20260806-012754Z (the retry produced run folder 20260806-012754Z — the field note said no new folder; there is one). All 7 other items + context succeeded both times. Distinct server trace IDs (`ab: a7d4ea15…` vs `30d27a1b…`) → two independent server-side failures, 2 days apart.
- **"No 5xx retry" confirmed:** `Invoke-KB4Query`'s retry branch is gated strictly on `$code -eq 429` (delays 1s/60s). Everything else throws on first attempt.
- The audit query is the only non-paginated pull in the file and its `first: 200` is **hardcoded** — `-PageLimit` does not apply to it. It's the single heaviest one-shot request in the script; that's the only in-code stressor visible.
- Verdict on "upstream": PLAUSIBLE, not confirmed. Deterministic 2-day repro argues against transient flakiness — so **retry-on-5xx by itself is unlikely to fix this**; the smaller-page fallback is the part that actually tests the visible stressor.

### Proposed fix (v1.1 — not applied)
Bounded 5xx retry (500/502/503/504, short backoff ~2s/5s so persistent failures still surface fast) → on exhaustion, one fallback attempt at `first: 50` → then fail honestly through the existing sidecar/manifest path. Parameterize as `-AuditPageSize` (default 200). Banner + changelog bump.

---

## 5–11. Manual Evidence Guide entries — all real gaps; one misattributed

Every fix lands in **`collector-manifest.psd1`** (the strings are hardcoded there, not per-client), then regenerate the Avon Lake guides — hand-patching the generated files only helps until the next regeneration.

| Claim | Finding | Fix location (manifest lines) |
|---|---|---|
| Mimecast URL wrong | **The guide contains no Mimecast URL at all** ("login.mimecast.com" appears nowhere) — the gap is real but it's a missing URL, not a wrong one | Add partner admin URL to `mc-tls`/`mc-ttp`/`mc-spam` (~431–443) |
| KB4 URL | Confirmed: bare `https://training.knowbe4.com`, no `/ui/management/login` | 501, 503, 506, 511 |
| MSP account-switch hop | Confirmed absent (no "MSP"/"Partner Dashboard"/"account switch" anywhere in corpus) | Add sub-step to `sat-config` (~499–503) |
| Consolidated Policy Viewer | Confirmed: guide says "virtualized table — scroll to the S entries" | Replace nav text, `mc-*` entries |
| Meraki dual VPN tabs | Confirmed absent — no mention of IPsec vs Cisco Secure Client tabs | `net-vpn` (~490–493) |
| Veeam multi-console | Confirmed absent from items 19–21, manifest, and README-Manual. NN[b\|c] suffix convention already exists (README-Manual line 42) — only the *instruction* to use it is missing | `bkp-jobs`/`bkp-offsite`/`bkp-restore` (~514–528) + README-Manual call-out |
| Diagram per-site | Confirmed absent, same pattern | `net-diagram` (~494–498) |

Live-console behaviors (what login.mimecast.com actually shows, the MSP landing page, the Meraki tabs) are unverifiable from docs — but Gabe/Claude observed them first-hand during capture sessions, and the doc-side gaps are all confirmed.

---

## 12. ADGP docs — every sub-claim verified, exact line numbers

Master and deployed copies are byte-identical (CRLF only), so one fix covers both.

1. Script line 22 `.EXAMPLE`: stale `clients\profiles\city-of-brooklyn.psd1` path + hyphenated slug — **confirmed** (path abolished by the 2026-07-28 restructure per the script's own changelog).
2. README line 54: literal unquoted `<Client>` — **confirmed**; hard parse error in PS 5.1 *and* 7 ("The '<' operator is reserved for future use").
3. Unquoted paths — **confirmed** on the same line.
4. README line 59 "-ClientName … no spaces" — **confirmed contradiction**: both RUN.txt files use `"Avon Local Schools"` / `"City of Brooklyn"`, and the Configurator itself builds profile filenames from the raw display name (line 567).
5. README line 61 `-OutputRoot` default — **confirmed stale** (actual default: `Join-Path $PSScriptRoot '..\..\..\clients'`, script line 49).
6. `$profile` shadowing at line 95 — **confirmed** (harmless internally; clobbers `$PROFILE` if dot-sourced).
7. Line 97 hard-throw on missing profile — **confirmed and protective**: stale docs produce loud failures, not silent misconfiguration. No change needed there.

Fix: align `.EXAMPLE` + README §3 + parameter table with the RUN.txt one-liner (quoted, display-name, real client name), add a troubleshooting line for the `<` parse error, rename `$profile` → `$clientProfile`. The suggested doc-vs-Configurator consistency sweep across the other collector READMEs (Action1, Duo, M365, Meraki, Mimecast, Auvik, Umbrella) was **not** staged this session and remains open.

---

## Cross-cutting findings

1. **Deployment drift check (all staged pairs):** S1, KB4, ADGP, Configurator masters vs SharePoint copies = byte-identical after CRLF normalization. **The one real drift is Add-ManualEvidence (deployed v1.5 vs master v1.6)** — and it's operationally blocking (no CISA source deployed).
2. **PS version question** (S1 §above) — worth one diagnostic run before fixing.
3. `collector-manifest.psd1` has no deployed copy in SharePoint — expected (Configurator reads from its own script root), but there's no way to verify which manifest version generated the Avon Lake guides.

## Recommended fix order (next session)

1. **Add-ManualEvidence v1.7** — sole blocker of all multi-file manual ingest; 38 Avon Lake files are waiting. (~1–2 h incl. dual same-day regression runs through Gabe/you)
2. **Collect-S1Evidence v3.1** — two controls short of evidence at Avon Lake; one-line core fix + try-narrowing. (~1 h incl. re-run)
3. **Collect-KB4Evidence v1.1** — 5xx retry + AuditPageSize fallback. (~45 min incl. re-run)
4. **collector-manifest.psd1 guide-text updates** + regenerate Avon Lake guides. (~45 min)
5. **ADGP doc corrections** + open the README consistency sweep as its own item. (~30 min)

After fixes land: mark the eight FIELD-NOTES entries `[PROCESSED 2026-08-XX → …]` per the runbook, re-sync deployed copies, commit with version banners bumped.
