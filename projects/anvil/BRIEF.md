---
title: Anvil brief
type: brief
updated: 2026-09-09
tags: [anvil, compliance, simvay]
related: [projects/anvil/STATUS, projects/anvil/DECISIONS, projects/anvil/DECISIONS-1x]
---

# Anvil

## What it is
Simvay's compliance evidence system for local government, K-12, law enforcement and commercial clients in Northeast Ohio. Collectors gather read-only configuration evidence from client platforms (M365, Google Workspace, AD/GP, SentinelOne, Duo, Action1, Mimecast, Meraki, Auvik, Umbrella, KnowBe4, manual captures), hashed and manifested per evidence item; an evaluation layer (Claude, under a versioned prompt and schema) judges the evidence against a 304-control coverage matrix (NIST CSF 2.0 with CJIS, CMMC, 800-171 and SOC 2 tags); a human reviews and attests in BlacksmithInfoSec. Three roles, never blurred: collectors gather, evaluation judges, a human attests. The Complete checkbox in Blacksmith is never automated.

## Anvil 1.x (production today)
PowerShell 7 collectors (~6,400 lines), a WPF Configurator driven by a manifest, Python renderers (executive report, full report, gap analysis, evidence packets), a Cowork skill for evaluation, a Chrome-agent runbook for Blacksmith staging, and a Section 4 vendor-risk pipeline. Repo: `C:\Dev\Anvil` (git, github.com/simvay/Anvil). Client data lives outside git (SharePoint working copy, E:\ masters). Analysts: Gabe day to day; Ryan owns development. Pain points that drove 2.0: three hand-synced copies, fixes waiting on git pulls, no cross-client visibility, secrets drifting onto disk, CLI-only manual evidence, whole-source re-runs, desktop-bound evaluation.

## Anvil 2.0 (approved direction, 2026-09-08)
A standalone, self-contained platform (backend, frontend, API, orchestration) built for eventual cloud hosting and SOC 2 audit. Simplest reliable modern stack: Python/FastAPI api, Python worker, React/TypeScript web, PostgreSQL as the only database, S3-compatible object store with object lock, OIDC to Entra ID, Bitwarden Secrets Manager behind an adapter, containers with Compose on one Ubuntu 24.04 LTS CIS Level 1 VM per environment on the Proxmox fleet, Grafana over Postgres views alerting to PagerDuty, GitHub Actions CI with signed images. Collectors reimplemented as a Python check framework (a check is one evidence id; a run is any selection of checks: one control, one source, full stack, scheduled). No Windows anywhere on Simvay's side; AD evidence via an Action1 automation that runs the existing script on the client DC and pushes the hashed zip to an ingest endpoint, run package as fallback. Client credentials written into Bitwarden through the portal, used by the worker, never read back. Every 1.x contract (evidence tree, manifests, matrix, evaluation prompt and schema, renderers, Blacksmith runbook) carries over unchanged.

## Why
Centralize collection and storage, give analysts one portal (run, re-run per control, review, stage), remove Gabe's folder-and-git workflow, be ready for a Blacksmith API, and be auditable as a product.

## Documents
- Plan v1.1 (2026-09-09): `Anvil-2.0-Project-Plan-v1.1-2026-09-09.pdf` (to be saved in `C:\Dev\Anvil\Development`).
- Proposal history v0.1 to v0.3 (superseded) in the same folder.
- 1.x source of truth: `C:\Dev\Anvil` README, ANALYST-GUIDE, Development/SESSION-RUNBOOK.
- Session records 2026-07-28 to 2026-09-09: `archive/` in this folder.
