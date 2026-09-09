# Simvay Anvil — Project Update 2026-07-31

Development session, run mostly unattended. Three items, all from operational
feedback: the CISA Cyber Hygiene field note, the gap-analysis first-page
truncation, and a standing remediation-documentation reference.

All changes committed to `C:\Dev\Anvil` (verified on-device by md5) and
delivered in-session. **Not yet git-pushed** — Ryan pushes.

## 1. CISA Cyber Hygiene receipts are now evidence (FIELD-NOTES, Gabe)

`system info integrity-03` had no evidence path — every client landed on
`manual_attestation_required`. Clients enrolled in CISA's free Cyber Hygiene
scanning get a weekly report by email; the reports are password-protected, but
the recurring dated RECEIPT is evidence of an active CISA relationship.

- **Add-ManualEvidence v1.6** — new source `CISA` (categories
  `cyber-hygiene-report`, `alert-receipt`, `other`), plus a guard that throws
  when `-Note`/`-CollectedFrom` looks like it carries a password.
- **Matrix v3.12** — `ATTEST` → `CISA` primary, `Manual` →
  `Partial-Automated`. Satisfaction: ≥4 consecutive weekly receipts inside 90
  days, sender/recipient visible, cadence unbroken. STIX/TAXII or InfraGard
  remains an accepted alternate.
- **Prompt v2.2** — new §"CISA Cyber Hygiene receipts": judge sender,
  recipient, dates, cadence ONLY; never open, decrypt, or infer contents.

Hard rule encoded in the script, README, matrix, prompt, and skill: the report
decryption password is never written into any Anvil evidence field.

## 2. Gap-analysis first-page truncation fixed

Confirmed by rendering the live Brooklyn 20260730 run: the Prioritized
Remediation List chopped `remediation_steps[0]` at 120 chars and control names
at 55 — **all 48 rows** ended mid-word, and the Assessment meta cell was
carrying the full four-sentence `scope_note` and overflowing.

Fixed at both layers, since a renderer alone cannot know what the sentence was
going to say:

- **Schema/prompt v2.2 — `first_action`.** Every partial/gap/insufficient
  finding carries an authored imperative one-liner (≤100 chars) written to
  stand alone in that table. Prompt carries writing rules and examples.
- **Render-GapAnalysis v1.1.** Prefers `first_action`; without it, condenses
  step 1 on a sentence or clause boundary and drops trailing "Owner:" clauses
  — never mid-word. Meta cell shows "N controls in scope"; the full scope note
  moved to an Assessment Scope block at the end.

Verified three ways on the same JSON: v1.0 (all truncated), v1.1 fallback
(clean), v1.1 with authored actions (48 complete standalone lines).

## 3. `2-Evaluation\remediation-resources.json` v1.0 — the standing reference

Ryan's ask: link Microsoft/vendor docs for remediation guidance so the
evaluation agent stops generating it from scratch each run.

- **128 controls, 324 links.** Technical-source controls (primary source not
  ATTEST/BLACKSMITH/PHYSICAL) — 126 of 304 — plus `system info integrity-03`
  and `incident response-02`. Policy/attestation controls deliberately out.
- **Per control:** up to 3 links (title, url, publisher, type, verified) plus a
  `config_hint` — suggested Group Policy path and setting, or basic Intune
  profile/admin-center location, per Ryan's scoping.
- **Every URL fetch-verified 2026-07-31:** 178 on-topic, 4 redirect (Cisco
  moved the Umbrella docs), 3 dead and removed. One `verified:false` —
  cisa.gov 403s automated fetches.
- **JSON is truth, XLSX is the human view**, same pattern as the matrix.
- **Wired in:** prompt §"Remediation references" (copy VERBATIM, prefer
  verified, max 3, NEVER invent — misses go to
  `summary.missing_reference_controls`); schema `references` field;
  Render-GapAnalysis v1.1 + Render-FullReport v1.1 render a "Reference
  documentation" line per finding.

## Versions at close

Add-ManualEvidence **v1.6** | matrix **v3.12** (304 controls) | evaluation
prompt **v2.2** | schema **v2.2** | Render-GapAnalysis **v1.1** |
Render-FullReport **v1.1** | remediation-resources **v1.0** (NEW) |
anvil-evaluation.skill rebuilt (bundles remediation-resources.json).

## Example outputs

`C:\Dev\Anvil\Development\assessments\20260731-v22-example-*` — gap analysis
PDF, full assessment PDF, and source JSON, built from the Brooklyn 20260730
findings with v2.2 fields added. ILLUSTRATIVE renders of an existing run, not
a new evaluation of City of Brooklyn.

## Follow-ups

1. **Validation run** — Add-ManualEvidence v1.6 has not been executed. Run one
   CISA ingest and one batch ingest to confirm the new source and the password
   guard behave.
2. **Re-save the anvil-evaluation skill** from the delivered `.skill`.
3. **git commit + push `C:\Dev\Anvil`**, then reconcile SharePoint ← C:
   (SharePoint got only the FIELD-NOTES marks this session).
4. **Quarterly link re-verification** of remediation-resources.json — Cisco
   Umbrella and Mimecast are the hosts most likely to move again.
5. **Extend the reference file** as ATTEST controls acquire evidence paths, and
   add `sdlc-12` once the client's WAF is known.
6. Carried from 07-30: push Section 4 from E:, scan the 8 new stack vendors,
   resolve Key Bank in Blacksmith, upload stack-vendor MFA evidence.

## Session note

A mid-session sandbox mount cache served STALE copies of two files when read
back after commit (old bytes under new metadata). On-device md5 confirmed all
writes were correct. Verify device writes with `device_bash` md5, not by
re-staging the same path — the documented mount-staleness hazard, now seen on
the read-back path too.
