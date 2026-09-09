# Add-ManualEvidence v2.0 — wildcard-tolerant intake (2026-08-10, shipped to C:\Dev\Anvil)

Ryan's call: the strict `<slug>-<category>-NN.ext` intake was too rigid for real client variance. v2.0 loosens to prefix-convention + `*` wildcard tail; the evaluation step interprets each item's contents (it reads Category/Note from the manifest, so no evaluation-side change was needed — matrix `MAN-*-...-*` wildcard ids already cover free suffixes).

## What changed (Add-ManualEvidence.ps1 v1.9 → v2.0)

1. **Batch matching:** file ingests when its name contains a known category token bounded by `-` or the extension dot: `[<anything>-]<category>[-<anything>].<ext>`. Numbering optional; any suffix (dates, OU names, console names, export labels). Longest token alternates first; leftmost token wins on multi-token names; case-variant filenames normalize to canonical lowercase category (keeps MAN-* ids matrix-matchable). Old strict names still work.
2. **Single mode `-Files` accepts `*`/`?` wildcard patterns** and expands them; a zero-match pattern (and now any missing file) is recorded as a Failed manifest row instead of silently skipped.
3. **Multiple uploads:** unchanged mechanics confirmed — same-UTC-day re-runs append to the same run folder with sequential MAN-* ids and versioned copies; documented explicitly in README-Manual.md.

## Verified by live execution (pwsh 7.4.6, full end-to-end runs)

Batch with 6 messy filenames → correct 3-category plan, 1 correctly skipped; old strict names still ingest; same-day append continued ids 006-009; wildcard expanded 2 files; dead pattern → Failed row with error text; case-variant name → lowercase folder + id; bounded-token negative test skipped correctly; manifest/csv/context all rebuilt.

Files shipped: `1-Collection/collectors/manual/Add-ManualEvidence.ps1`, `README-Manual.md`. Uncommitted (git add/commit with the rest of today's work).
