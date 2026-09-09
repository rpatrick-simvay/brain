---
title: Anvil log
type: log
updated: 2026-09-09
---

# Anvil session log (append-only)

Older 1.x sessions (2026-07-07 to 2026-08-11) are in TIMELINE.md with the source docs in archive/.

## 2026-08-31 (Cowork, unattended planning)
Full Anvil 2.0 proposal v0.1 written from the 1.x repo, field notes and session records: Linux control plane plus persistent Windows runner with console passthrough, ClickHouse plus object store, Claude API evaluation service, Blacksmith staging package. Seven decisions listed. PDF committed to C:\Dev\Anvil\Development.

## 2026-09-08 (Cowork, with Ryan)
James's architecture summary and the PVE-Ansible and SOC-Data-Engineering repos reviewed (cloned to C:\Dev). Proposal v0.2: aligned to the Proxmox fleet, Bitwarden, Grafana, Dagster; ephemeral Windows runner design. v0.3: client credential vault at Ryan's direction. Then Ryan met James: standalone platform, modern collectors, no Windows VMs, AD via Action1 or run package. Plan rebuilt as v1.0 (19 pages): Python check framework, PostgreSQL-only, containers, M365-without-PowerShell analysis (10 keep, 5 degrade, 2 lose), SOC 2 mapping, phases (about 20 to 24 weeks). Workstation went offline; v1.0 not committed.

## 2026-09-09 (Cowork, with Ryan)
Plan v1.1 (21 pages): client onboarding in three pages with Bitwarden feasibility (yes, with the honest caveat that the worker must hold plaintext in memory during a vendor call), field notes replaced by in-portal Feedback plus GitHub Issues and Projects (Quackback or Fider as the self-hosted alternative), roadblocks R1 to R9, kickoff-pack contents. Host OS decided: Ubuntu 24.04 LTS CIS Level 1 (Decision 7). Knowledge strategy decided: a private brain repo of markdown as the canonical layer, Claude Projects for per-initiative working context, no paid memory platform. Prepared tonight: brain repo skeleton with all 28 Anvil project docs archived plus TIMELINE, DECISIONS-1x and OPEN-ITEMS-1x; anvil2 kickoff pack. Both wait for repos and the workstation.
