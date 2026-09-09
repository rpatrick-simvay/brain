# Anvil process changes — 2026-07-29 (skills + docs updated)

Ryan streamlined the anvil-evaluation and anvil-upload skills. Updated: both SKILL.md files (.skill files delivered for account save), plus the authoritative project docs committed to C:\Dev\Anvil (Ryan git-pushes to SharePoint) — EVALUATION-PROMPT.md v2.1, evaluation-schema.md v2.1, Blacksmith-Ingestion-Runbook.md v1.4, and two NEW render scripts in 2-Evaluation: Render-FullReport.py and Render-GapAnalysis.py (both tested; also bundled in the skill's scripts/).

## Evaluation (prompt/schema v2.1)
- Fresh Compliance-tab CSV export is REQUIRED at every run, analyst-provided (no Chrome dependency, scrape retired for scope). Ingested via Ingest-ComplianceExport.py; stop and ask if missing/stale.
- Carry-forward rule: Completed=true in export + prior evaluation satisfied + prior run ≤90 days → carried forward verbatim (carried_forward/carried_from_run fields, counted in satisfied + own summary line), never re-evaluated.
- New required schema field: remediation_steps (1-5 concrete steps with owner) on every partial/gap/insufficient_evidence evaluation.
- New standard outputs, rendered deterministically: <stamp>-evaluation-report.pdf via Render-FullReport.py (PDF twin of the HTML report, full SHA-256 inventory) and <stamp>-gap-analysis.pdf via Render-GapAnalysis.py (partial/gap/insufficient findings, remediation_steps rendered verbatim; client-facing language, internal-review depth). Both reuse the exec-report brand system and pull the S-mark logo from Render-ExecutiveReport.py beside them.

## Upload (runbook v1.4)
- Autonomous run to completion — no per-control stops; real-time progress, analyst interjects if needed.
- Parallel subagents, one per status category (satisfied/partial/gap), each in its own Chrome tab; disjoint task lists prevent collisions.
- Ordering: incomplete controls first; Completed controls reviewed only after all incomplete are current.
- Completed touch policy: modify a Completed task ONLY if evidence >6 months old OR note not in standard [ANVIL] format.
- Note policy: REPLACE notes wholesale on update (append-under-dated-header retired); improved findings and pre-Anvil manual note text are deleted with the replacement. Evidence file uploads are still never deleted by agents.
- New artifact: clients\<Client>\upload\<stamp>-staging-report.csv (per-task action record; read at start of each run as cross-session memory).
- Unchanged: Complete checkbox is never automated.
