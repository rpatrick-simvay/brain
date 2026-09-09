# Anvil — Manual Collection Audit + Remaining Fixes (2026-08-07 evening session)

**Status:** all changes written to E:\ masters AND the SharePoint working copy. **Nothing committed** — the working tree is staged for your review/test/commit in the morning. FIELD-NOTES: all 13 open entries now marked PROCESSED (validation caveats noted per entry).

---

## 1. The audit answer

**Can manual browser ingestion be removed entirely? No — but it shrinks by two thirds.**

For an Avon Lake-class stack (M365 + Mimecast + S1 + Meraki + KnowBe4 + Veeam), guide items drop **21 → 11**, and browser-capture items drop **20 → 7**. The irreducible browser core for nearly every client is just three items: **SIEM retention** (S1 has no public API endpoint), **NAT/port-forwarding** (no collector exports it — not even Meraki), and **VPN client config** (Meraki Client VPN is not API-readable). The rest of the surviving manual set is analyst-file or native-console, not browser: network diagrams, Veeam items, restore-test form, Purview labels, Mimecast TLS pages, plus stack-dependent items (firewall/SAT for clients without the covering collector).

### Retired outright (evidence replaced by collectors)
| Manual item | Replaced by | Matrix proof |
|---|---|---|
| SIEM log-sources | S1-MKTPL-01/02 | audit-13 logic names them |
| SIEM alert-rules | S1-DETECT-01, S1-SIEM-RULES-01 | audit-06/13, config-22, personnel-09 |
| SIEM unified-alerts | S1-UALERT-01 | audit-17: "manual capture becomes fallback" (now removed) |
| SIEM rbac | S1-USERS-01 | audit-04, access-25 |
| Mimecast ttp-definitions | MC-TTPATT/TTPURL-01 + co-listed ids | sii-01, sp-08 both Automated |
| Mimecast spam-dnsauth | MC-ANTISPOOF/BLOCKED/GREYLIST/DKIM-01 + M365 ids | sp-08, sp-35 both Automated |

### Retired conditionally (new `SupersededBy` mechanism — item auto-drops when the covering collector is enabled, survives for other stacks)
`net-fw` → Meraki (MER-FW-01 exports the complete L3+L7 rule base incl. the default rule); `sat-config`/`sat-completions`/`sat-phish` → KnowBe4 (KB4-TRAIN-01/KB4-ENROLL-01/KB4-PHISH-01). SAT items are now platform-generic in wording (KnowBe4 URLs stripped) since they only render for non-KB4 platforms — which also closes the KnowBe4-URL and MSP-account-switch field notes as moot.

### Two judgment calls I made on your behalf (both reversible pre-commit)
1. **mc-ttp + mc-spam deleted.** Matrix logic is fully satisfied by API evidence, but two honest gaps are now documented in matrix v3.13 instead of screenshotted: TTP **definition scope** (logs prove the engines run, not their targeting), and **inbound** DNS-auth + spam-scan definitions (MC-DKIM-01 is outbound-only). If you want definition-scope evidence, restore these two entries from the diff and I'll re-add matrix references.
2. **sat-config + sat-phish superseded** alongside the clear-cut sat-completions. Known gap: KB4-PHISH-01 exports campaign cadence, not per-campaign sent/opened/clicked stats (currentPpp is the outcome proxy) — noted in matrix training-02.

### Kept manual — and why (the audit refutes any temptation to remove these)
Purview labels (no API item; only source for data management-07), SIEM retention (audit-01/02/03 would be orphaned), NAT rules (`system protection-38`, primary_source Manual — **counter-intuitive: for a Meraki client, firewall retires but NAT does not**), ACLs + switch config (no Meraki MS ACL endpoint; Auvik intentionally exports config existence, not content), VPN (3 independent "not API-readable" citations), diagrams (config-01), all Backup items (continuity plan-01..04 are no-collector with empty ids; no backup collector exists).

---

## 2. What changed tonight (all deployed to both roots)

1. **Collect-KB4Evidence v1.0 → v1.1** — bounded 5xx retry (2s/5s, separate from the untouched 429 ladder), new `-AuditPageSize` (default 200; the old `first: 200` was hardcoded and untunable), one-shot fallback at `first: 50` on persistent 5xx, then honest failure with the original error. Reduced pulls are visible in evidence (`PageSize`/`ReducedPageFallback`). Worst-case stall on a hard-failing audit item ≈14s.
2. **Collect-ADGPEvidence v1.6 → v1.7** — docs only: `.EXAMPLE` + README §3/param table aligned with the RUN.txt convention (quoted display names, real paths, correct -OutputRoot default), reserved-`<` troubleshooting line, `$profile` → `$clientProfile`.
3. **README sweep** — same defect class fixed in README-Action1, README-Duo, m365 README, README-Mimecast. Auvik/Meraki/Umbrella were clean.
4. **Anvil-Configurator v0.9 → v1.0** — three new ManualEvidence keys: `SupersededBy` (collector-enabled ⇒ item retires; defensive on unknown ids), `Ext` (`'<file>'` stops the guide from naming a Visio/PDF ".png"), `NoBrowser` (item omitted from Claude-Chrome-Instructions.md — applied to diagram + 3 Veeam items). Numbering stays positional and shared between the two docs; the Chrome doc skips NoBrowser numbers without renumbering.
5. **collector-manifest.psd1 v1.15 → v1.16** — 6 entries deleted, 4 SupersededBy, rewords: mc-tls (partner admin URL + Consolidated Policy Viewer + search terms), net-vpn (both Client VPN tabs), net-diagram (per-site, native extension, gate removed), bkp-* (multi-console check + -CollectedFrom). Schema block documents the new keys.
6. **Coverage matrix v3.12 → v3.13** (JSON + xlsx in-place, both stay in sync) — MER-FW-01 added to system protection-02/21/25; SAT manual ids removed from training-01..04 (KB4-ENROLL-01 added to -03/-04); retired-category references cleaned across 14 more controls; honesty notes for the Mimecast gaps; dated changelog.
7. **collector-registry.yaml** — siem section rewritten (retention is the only manual SIEM capture), stale SIEM entries deleted, NET.nat_rules/NET.switch_config added (load-bearing for sp-38), NET.ios.* marked aspirational (no collector exists), Meraki duplicates removed, sat→knowbe4 cross-ref, new cisa section.
8. **README-Manual + ANALYST-GUIDE** — manual-scope descriptions updated; multi-site/multi-console call-outs; SupersededBy note. Agent-contract headers verified byte-identical.

---

## 3. Morning checklist (in order, ~45 min)

1. `git diff` on E:\Projects\Anvil — review, especially collector-manifest.psd1 and the matrix. Decision point: keep the mc-ttp/mc-spam deletion? (§1 above)
2. `.\Anvil-Configurator.ps1 -ValidateManifest` — validates manifest v1.16 (I could only balance-check, not parse-run).
3. Open the Configurator, regenerate Avon Lake's guides — confirm 11 items, Chrome doc has 7, diagram save-as shows native-extension wording. **Note: item numbers shift vs the old 1–21 guides.** Ingest is category-keyed so old evidence filenames still parse; it's only a visual mismatch.
4. Validation runs still outstanding from last night's fixes: S1 v3.1 (Avon Lake; expect MKTPL-02 + IDENT-01 Success), Add-ManualEvidence v1.7 (38-file batch + same-day second ingest), KB4 v1.1 (expect either a Success with ReducedPageFallback or the same honest 500 sidecar).
5. Commit everything (my earlier commit e019f36 with S1 v3.1 + Manual v1.7 is already on main, unpushed).

## 4. Follow-ups surfaced by the audit (not done tonight — say the word)

1. `dns-policy-config` is documented in the registry and referenced by the Umbrella collector but missing from Add-ManualEvidence `$validCats` — Umbrella policy screenshots currently cannot be ingested (real break, needs a v1.8 category addition).
2. No CISA guide item exists despite system info integrity-03 depending on MAN-CISA-* evidence — should become a manifest entry (NoBrowser, file-intake).
3. Registry lacks EP.s1.* entries for S1-DETECT-01/S1-SIEM-RULES-01/S1-USERS-01 (asserted automated but not inventoried); 6 controls carry "id not yet listed — follow-up" notes in v3.13.
4. Evaluation layer should treat a manifest-less/stale-manifest manual run folder as a failed ingest (EVALUATION-PROMPT + skill change; carried over from the v1.7 fix).
5. Collector scripts' internal `.EXAMPLE` blocks (m365/mimecast/action1/duo) still show pre-restructure paths; several README version strings lag their script banners.
6. client_context category counts in Add-ManualEvidence include Failed entries (overstates by failure count); ADGP has the same single-task ConvertTo-Json latent bug the manual collector just fixed.

---

# ADDENDUM — later the same evening (vendor path fix + dns-policy-config)

Both follow-on items are done and deployed; add these to the morning review.

**Vendor pipeline path defect (Ryan-reported).** The Aug 6 Avon Local Schools vendor run wrote its evaluation JSON, both PDFs, the fill CSV, and one scan index into `4-VendorRisk\clients\` because the vendor skills/docs used cwd-relative `clients\` paths while working in `4-VendorRisk\`. Fixed: all 5 files copied to the real `clients\Avon Local Schools\vendors\` tree; the stray folder is parked at `4-VendorRisk\_to_delete\clients-misplaced-20260807\` (**delete by hand** — the sandbox can't); `anvil_vendor_api_scan.py` client-index default is now script-anchored (cwd-immaterial); a prominent "Path rule" (clients\ = repo root, never cwd-relative) landed in all three vendor SKILL.md files, VENDOR-EVALUATION-PROMPT v1.2, Vendor-Fill-Runbook v1.1, and README-VendorScan; all three `.skill` bundles rebuilt into `skills\`. Bonus finds fixed in the same pass: the evaluation bundle shipped a stale v1.0 prompt missing the July 30 MFA unassessed-vs-assessed correction (synced to v1.2), and `Development\skills\` was missing the anvil-vendor-evaluation/upload sources entirely (now reconstructed). **Re-save the three rebuilt .skill files to your Claude account** (attached in chat) so the installed skills match — the installed copies still carry unanchored paths and the stale MFA prompt until you do. Section-4 changes are E:\ only, consistent with the standing SharePoint reconciliation note.

**dns-policy-config (follow-up #1).** Add-ManualEvidence v1.8 accepts the new Network category; manifest v1.17 adds guide item `net-dns-policy` (Umbrella-gated: dashboard > Policies > Management > DNS Policies, per-policy enforcement settings incl. the default policy — the API answers 403 on policy settings); README-Manual + registry updated. Deployed to both roots.

**Morning checklist additions:** (6) delete `4-VendorRisk\_to_delete\` contents by hand; (7) re-save the three rebuilt .skill files; (8) next vendor run should confirm no `4-VendorRisk\clients\` reappears; (9) `-ValidateManifest` now validates v1.17.

---

# ADDENDUM 2 — all 5 backlog items closed (later 2026-08-07)

Everything below is deployed to E:\ (and SharePoint where the tree exists there); still nothing committed.

**1. Failed-ingest rule — EVALUATION-PROMPT v2.3.** New "Manual evidence run reconciliation" section: files-on-disk are reconciled against manifest.csv before a manual run counts as evidence; no manifest = FAILED INGEST reported in those words with a caveat naming the run — never an empty evidence set, never a downgrade rationale; stale manifests use the manifested rows and name the uncitable files. Big catch while syncing: **the shipped anvil-evaluation skill bundle was a full version stale** — v2.1 prompt (no first_action, no remediation-references, no CISA logic) and pre-v1.1 renderers. Bundle rebuilt fully current (v2.3 prompt, v2.2 schema, v1.1 renderers); `Development\skills\anvil-evaluation\` source tree created. **Re-save anvil-evaluation.skill to your account** — that makes FOUR bundles to re-save total.

**2. SharePoint ← E:\ Section-4 reconciliation — done.** SP now carries scoring-model v2.0, trusted-sources, v2.0 scripts, vendor-master, VENDOR-EVALUATION-PROMPT v1.2, Vendor-Fill-Runbook v1.1, the 3 rebuilt vendor bundles, and both clients' vendors\ outputs (ALS + Brooklyn). Deliberately NOT synced: `4-VendorRisk\scans\` evidence (stays consolidated on E:\ per the July decision — flag if you want it mirrored) and `vendor-scan.local.psd1` secrets.

**3. CISA guide item — manifest v1.18.** New TechStack checkbox `CisaCyhyEnrolled` (bool, default off) + gated ManualEvidence item `cisa-cyhy` (NoBrowser, file-intake, ≥4 weekly receipts/90d bar, hard password rule in the capture text). Renders only for enrolled clients. Note: nothing downstream reads `TechStack.CisaCyhy` yet — it only drives the guide gate.

**4. Registry + matrix v3.14 — wired honestly, not blindly.** Three new registry rows (EP.s1.detection_rules / siem_rules / console_users, with the [VERIFY] endpoint caveat carried honestly). Matrix: audit-17, audit-06, audit-18, access-03 wired with the S1 ids; **audit-07, audit-05, access-06 deliberately NOT wired** — a detection-rule inventory doesn't evidence logging-failure alerting, storage-limit alerting, or privileged-function logging; each note now states exactly what evidence would close it. Caveat recorded: DETECT-01 and SIEM-RULES-01 are two projections of ONE [VERIFY]-marked endpoint — a live check against the console api-doc is still worth doing. XLSX in sync, 304×15 fields verified.

**5. Doc drift closed.** .EXAMPLE blocks fixed + version bumps: M365 v2.8, Mimecast v1.5, Action1 v1.7, Duo v1.7 (docs-only changes). All 7 READMEs now match their script banners; README-M365's output-tree diagram fixed (phantom nested folder). Historical changelog mentions of old paths intentionally preserved.

**Mimecast API research (your "make it API-driven" question) — definitive as of 2026-08-07:** Secure Delivery/Receipt TLS definitions, spam-scanning definitions, and INBOUND DNS-auth definitions are **not exposed in API 2.0** — confirmed across two years of Mimecast's endpoint release notes, the indexed developer-portal route catalog, and the Config-Backup API scope (which covers only Managed Senders/URLs/Profile Groups). The screenshot fallback was correctly diagnosed, not a collector gap. Two paths forward: (a) **cheap spike** — legacy-style `/api/policy/{type}/get-definition` routes still work for some types (address-alteration, webwhiteurl); worth probing tls/spam/dns-auth-inbound slugs against your existing 2.0 app — a 403/404 is clean negative confirmation, a hit means it runs on 1.0-vintage plumbing (Phase-1 EOL'd, no shutoff date) usable with a revisit flag; (b) watch Mimecast's monthly "New API Endpoints" Zendesk series — they ship policy-family drops every 3–9 months. Also: a 10-minute logged-in browse of developer.services.mimecast.com/apis (the portal blocks anonymous readers) would confirm the route inventory first-hand. mc-ttp/mc-spam retirement stays on hold per your call; full research with cited sources is in the chat.

# ADDENDUM 4 — Mimecast API question CLOSED: live probe verdict (v1.7, deployed)

Ryan supplied a temporary v2 API key (rolled after session; credentials held in tmpfs only, shredded). Live probe against the tenant, 2026-08-07:

- **All 22 candidate routes** (legacy `/api/policy/*` + modern `policy-management/cloud-gateway/v1/*` for secure-delivery, secure-receipt, spam-scanning, dns-authentication-inbound): `app_forbidden`.
- **Discriminators made it decisive:** a garbage slug returns the identical `app_forbidden` (it's the catch-all for unregistered routes); the control route `address-alteration/get-definition` answered **200** through the same app; sibling families (anti-spoofing, greylisting, dns-authentication-outbound) answer 200. The app holds the Policy Management product — within it, the gap-area routes behave exactly like nonexistent ones.
- **No v1 key can be created** (1.0 EOL Phase 1 blocks new registrations), closing the last untestable path.

**VERDICT: the three policy-definition areas are NOT API-readable in this tenant — verified, not presumed. The Consolidated Policy Viewer screenshot (mc-tls guide item) is the permanent evidence source unless Mimecast ships new endpoints.**

**Collector v1.7 (deployed both roots):** default runs are back to 13 items; `ApiCoverageGaps` strings now carry the dated verified verdict; the probe harness is retained behind a new `-ProbePolicyRoutes` switch (default off) as a quarterly re-check — a future probe SUCCESS is a change-of-state signal worth a dev session (inbound DNS-auth is likeliest to flip; Mimecast already ships the outbound twin). Also worth watching: Mimecast's monthly "New API Endpoints" release notes.

**Bearing on the held mc-ttp/mc-spam decision:** the definitions-scope gap documented in matrix v3.13 is now permanent-unless-Mimecast-moves. If definitions evidence matters, the only path is restoring those screenshot items; the API will not provide it.

**DECISION FINALIZED (Ryan, 2026-08-07): mc-ttp/mc-spam stay retired.** Sealed as matrix **v3.15** (live-probe citations added to sii-01, sp-08, sp-35, and a do-not-retire note on sp-07's surviving TLS screenshot) and the registry's MC.ttp_definitions / MC.spam_definitions rows tombstoned `status: retired`. Deployed both roots. Small backlog adds from this pass: assign the surviving mc-tls capture a real evidence id (e.g. MC-TLS-01) so sp-07's dependency is enforceable, and reconcile the mc-tls slug vs registry MC.tls_policies naming.

---

# ADDENDUM 3 — Mimecast v1.6 probe collector (superseded by Addendum 4)

Per Ryan's "let's build it": **Collect-MimecastEvidence v1.6** adds four `[VERIFY]` probe tasks (MC-SECDEL-01, MC-SECREC-01, MC-SPAMDEF-01, MC-DNSAUTHIN-01) that attempt the three screenshot-only policy areas via the legacy `/api/policy/{type}/get-policy|get-definition` route family — the same family the collector's proven-working `blockedsenders` call uses, so auth is not the question; only the slugs are. 22 candidate paths (best odds: `dns-authentication-inbound`, since the outbound twin is a live 2.0 family). Every candidate outcome is classified (SUCCESS / EMPTY / NOTFOUND / FORBIDDEN / FAIL-ENVELOPE) into a ProbeLog; all-negative probes record an `ApiReadable=$false` absence fact (manifest row stays Success — absence is a fact, not a failure); `client_context.json` gains a one-screen `LegacyPolicyProbes` roll-up. New `-SkipPolicyProbes` switch. The manual mc-tls item and the matrix stay untouched until the probe results are in. Note: Wayback Machine was unreachable from the sandbox, so all slugs are convention-derived guesses — a 403 (FORBIDDEN) on any path is the "route exists, permissions block it" signal worth chasing; all-404s is a clean negative that finally closes the API question.

**DEPLOY PENDING:** the device bridge disconnected before the two files (Collect-MimecastEvidence.ps1 v1.6 + README-Mimecast.md) could be written. They are attached in the chat. Either reopen the desktop app and tell Claude "deploy the Mimecast files", or drop the two attachments into `1-Collection\collectors\mimecast\` on both roots by hand.

**Reading the first run:** any SUCCESS → send the Raw block for a dev session (field-shape verification + matrix/manifest updates + 1.0-EOL longevity flag). Any FORBIDDEN → likely a Products/permissions gate, same class as the MC-DOMAINS-01 app_forbidden finding. All NOTFOUND → the screenshot path stays, question closed with evidence.

**New follow-ups from this pass (small):** wire-or-not decision on access-06's forwarding clause (S1-MKTPL-01/02 would fit); consider audit-06 Partial→Automated once the [VERIFY] endpoint is confirmed live; matrix `exported` date still says 2026-07-31; Configurator's `Test-AnvilManifest` doesn't validate ManualEvidence entries at all (typo'd gates fail silently — cheap validator addition); `$pwd`/`$args` variable shadowing in ADGP/KB4.
