---
title: Simvay Data Platform status (context)
type: status
updated: 2026-09-09
owner: James
---

# Simvay Data Platform (James): context for Anvil, not Ryan's project

## What it is
dlt (extract) → ClickHouse (store and compute) → dbt (model and test) → Grafana (dashboards and alerts to PagerDuty), orchestrated by Dagster, secrets in Bitwarden Secrets Manager, on the Proxmox fleet provisioned by PVE-Terraform and configured by PVE-Ansible (Base, Storage, Engine, Verify layers; no addresses or secrets in git; no containers; nftables; Debian-targeted roles). Repo simvay-platform (SOC-Data-Engineering) and PVE-Ansible, cloned at C:\Dev.

## Status (from James's September 2026 summary and repo state)
- Pipeline framework and scheduling: done. SentinelOne alerts, policies, inventory: done. Live-console validation: in progress. Action1, Duo, PagerDuty sources: not started. Grafana cutover: not started.
- PVE-Ansible: all roles and playbooks written, nothing has run against a real host; inventory exists only once Terraform applies tags. Backup strategy undecided (backup_verify.yml fails by design).

## Touch points with Anvil 2.0
- Shared: Bitwarden Secrets, Entra ID sign-in, Grafana and PagerDuty, Proxmox hosting.
- Not shared: database, scheduler, deploy pipeline (Anvil is standalone).
- Later: nightly Anvil analytics export to the warehouse; shared vendor client library (S1, Action1, Duo).
- Rule: pipeline data is never compliance evidence.

## Next actions (Ryan's side)
1. Confirm with James: container carve-out for the Anvil VM; Ubuntu 24.04 vs Debian for that VM.
2. Ask James for the timing of the first real site.yml run.
3. Nothing else pending.
