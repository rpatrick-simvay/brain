---
title: HaloPSA log
type: log
updated: 2026-09-09
tags: [halopsa]
related: [projects/halopsa/STATUS]
---

# Log (append-only, newest last)

## 2026-09-09 - migration from the HaloPSA Claude Project
- Changed: 37 project docs pulled and placed. Runbooks and references to `runbooks/` with `halopsa-` / `knowbe4-` / `simvay-` prefixes and YAML frontmatter; dated records to `archive/`; sales-report v2 code extracted to `sales-report-v2/`; verbatim export of all sources to `archive/project-export-2026-09-09/`.
- Normalization: em and en dashes replaced in prose only (code fences and inline code untouched); `claude/HaloPSA-Runbook-NN-*.md` references rewritten to brain paths; a migration note added under each runbook's frontmatter; runbook 01's standing instruction now points at this repo.
- Fix: the teal S-mark data URI in `runbooks/simvay-logo-datauris.md` was re-derived from the white mark (same alpha, fill #00627B) because the original base64 did not survive transcription; the white mark is byte-identical to the source.
- Checked: no secrets found in any doc (trigger ids and a Cloudflare KV namespace id are identifiers, left in place).
- Decided: project docs stay in place, frozen, with a pointer doc; brain is canonical.
- Blocked: nothing.

## 2026-09-09 - user impersonation for Operations and Sales Executive
- Changed: `Can impersonate Users` Not set to Yes on Operations (70222833) and Sales Executive (febac04c) via Chrome; view-mode diff showed one line changed per role; API check confirms claim `Iu=1` on agents 15 and 25.
- Decided: Sales Executive, not the vacant Sales Rep role, is the "Sales exec" group (Ryan). Sales Rep, Executive, Finance untouched.
- Learned: claim code `Iu` = Can impersonate Users; edit-form lazy render technique recorded in runbook 09 section 11.18.
- Blocked: nothing. Schilling and Soltis may need to log out and back in before the permission shows.
