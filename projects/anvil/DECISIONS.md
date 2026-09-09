---
title: Anvil decisions (2.0)
type: decisions
updated: 2026-09-09
related: [projects/anvil/DECISIONS-1x]
---

# Anvil 2.0 decisions (append-only, one line each)

For 1.x conventions see DECISIONS-1x.md.

- 2026-08-31 (Ryan): Project "Anvil 2.0" exists: migrate Anvil to an internally hosted platform with a web GUI; centralize collection and storage; per-control re-runs; remove Gabe's folder-edit and git-sync workflow; be Blacksmith-API-ready.
- 2026-08-31 (Ryan): Keep credential passthrough so collectors are not rebuilt (superseded 2026-09-08).
- 2026-09-08 (Ryan): Client API keys live in Bitwarden Secrets; analysts write them in through the platform; collectors use them; no one views them after entry.
- 2026-09-08 (Ryan): Collection should run on something that leaves no artifacts behind (ephemeral runner idea; superseded same day by the no-Windows decision).
- 2026-09-08 (Ryan and James): Anvil 2.0 is a standalone, self-contained platform (backend, frontend, API, orchestration) so it can be cloud-hosted and SOC 2-audited later.
- 2026-09-08 (Ryan and James): Build the simplest, most reliable, modern implementation possible.
- 2026-09-08 (Ryan and James): Collectors are reimplemented in a modern framework that can run individual control checks or the whole stack; no ephemeral Windows VMs.
- 2026-09-08 (Ryan and James): AD collection via Action1-run PowerShell on a DC or the current run package with returned evidence.
- 2026-09-08 (Ryan): If dropping PowerShell on the Microsoft side only loses Purview, drop Purview; if more, game-plan a separate method. Answer (plan v1.0): 10 items keep, 5 degrade to Secure Score plus DNS plus audit-log query, 2 lose (Exchange transport TLS and connectors to manual; Purview DLP dropped). Exchange sidecar deferred to backlog.
- 2026-09-08 (plan v1.0, recommended, pending Ryan and James sign-off): PostgreSQL is the only database; ClickHouse retired from Anvil's runtime, optional analytics export later.
- 2026-09-08 (plan v1.0, recommended): containers with Compose on one VM per environment; needs the fleet's no-container carve-out from James.
- 2026-09-09 (Ryan): Field notes replaced by a platform-hosted feedback and tracking flow; recommendation is in-portal Feedback filing GitHub Issues with GitHub Projects as the board; self-hosted board (Quackback or Fider) if outside voting is needed later.
- 2026-09-09 (Ryan): Client onboarding is three pages: New client (creates the Bitwarden project), Configuration (replaces the .psd1), Connectors (status per source, write-only credential entry, test, rotate, revoke).
- 2026-09-09 (Ryan): Host OS for the Linux side: Ubuntu LTS, CIS hardened. Refined to Ubuntu 24.04 LTS Server, CIS Level 1 Server via Ubuntu Pro usg; Docker from Docker's apt repo; Level 2 avoided because it breaks the container runtime; confirm Ubuntu vs Debian with James since fleet roles target Debian.
- 2026-09-09 (Ryan): Anvil 2.0 work moves to a new repository (simvay/anvil2); project knowledge replicated into the brain repo.
