---
title: Simvay Collector brief
type: brief
updated: 2026-09-09
tags: [simvay-collector, sentinelone, siem, syslog, appliance]
related: [projects/simvay-collector/STATUS, projects/simvay-collector/DECISIONS, projects/simvay-collector/LOG]
---

# Simvay Collector

## What it is
A deployable VM appliance that receives syslog from a client's network devices and forwards it, parsed, into that client's SentinelOne Singularity Data Lake (Cloud SIEM). The forwarding engine is the three-container Docker stack SentinelOne publishes ("SentinelOne Collector for Syslog", KB 000008665). The appliance wraps it with Ubuntu 24.04, unattended build automation (cloud-init seed ISO), a browser-based setup console on 8443, a self-test, a watchdog, a status page and a console banner, so a site deployment is repeatable rather than hand-built. Shipped as an OVA for VMware (ESXi 7.0 U2 and later, hardware version vmx-19).

Product name is Simvay Collector. "SentinelOne" is reserved for the actual SentinelOne product (Data Lake, agent, console, upstream container images).

## Why
Simvay's SOC needs client network-device logs (firewalls, switches, APs, Veeam) in each client's Data Lake. Hand-building a forwarder per site is slow and inconsistent; the appliance makes it one OVA deploy plus a browser walk (accept cert, sign in, change passphrase, paste write key, add one source, Apply, confirm self-test green), with no SSH and no write key ever touching a command line.

## Architecture in brief
- Ubuntu 24.04 LTS, EFI, two disks: disk 1 = 80 GB root, disk 2 = 100 GB spool mounted at /var/lib/docker (spool is a Docker named volume). Spool disk is found by shape, not by device name.
- Build: make-gold-iso.sh produces a seed ISO; gold-build.sh and provision.sh run unattended on the master; s1-collector-seal purges identity and config before export.
- Runtime: s1-collector-firstboot (per-clone identity: machine-id, SSH keys, hostname simvay-collector-<6 hex of machine-id>, Action1 agent install, S1 agent uuid reset), s1-collector-web (setup console and status page), s1-collector-configure, s1-collector-selftest, s1-collector-console (banner), health timer watchdog.
- One collector per client (config holds exactly one tenant key). One source-type per subnet; matchers within a source-type are ANDed; five matcher attributes (proto, srcip, destport, hostname, appname); per-port syslog format (rfc3164 or rfc5424).
- Two build gates: the ISO refuses to build unless provision.sh opens ufw 8443/tcp, and provision.sh refuses to finish unless the rule took and vmtoolsd is present. A completed build is proof that 8443 is open.

## Constraints
- VMware only. Hyper-V dropped 2026-08-03; a purpose-built Hyper-V VM may follow later.
- Ubuntu 24.04, not 26.04: Action1 documents 22.04 and 24.04 only; S1 agent support for 26.04 unverified.
- SentinelOne Linux agent, if baked in, is installed last and never activated on the master (KB 000005482: UUID is generated at OS boot).
- Setup console has no external dependencies (must work on an isolated VLAN). Status page is public but shows only hostname, address and uptime; everything else sits behind the session.
- Passphrase rule: 15-character minimum, nothing else.
- Sizing: 100 GB disk 2 is a floor derived from a quiet lab (Meraki MX with Appliance Flows: about 25.8 events/sec, roughly 2.2M events/day, about 0.5 GB/day). Re-derive from a daytime sample at the first real client site.

## Environment
- Dev ESXi host 10.10.75.10 (HPE DL380 Gen10, ESXi 8.0 U3, standalone, no vCenter). Port group Tech-Prod_VL76_10.10.76.0/24. Datastore ESX01-Local, ISOs in ISOs/. 10.10.76.0/24 must be in Tailscale approved subnets to reach the console from a workstation.
- PoC tenant SIMVAY-NFR (usea1-300-nfr.sentinelone.net). Write keys: tenant console, AI SIEM, API Keys, Log Access Keys.
- Gold VM OS login: user simvay; password pinned via GOLD_PASSWORD in the build. The value is not recorded here; it is in the project HANDOFF in the SharePoint project folder.
- Cloud sandboxes cannot reach the 10.10.x addresses (an egress gateway answers for every private IP, so a connectivity test lies). Claude in Chrome can reach them but cannot click through a self-signed certificate interstitial; a human clicks once per browser.

## Documents
- Working folder: SharePoint, SecurityOperationsHub - Documents/INTERNAL/03 - Projects/SentinelOne Collector (HANDOFF.md, README.md, docs/, runbooks/, build/, appliance/, tests/, ovf/, installers/).
- Deployment Guide v2.3 (client-ready, 7 pages) built from docs/guide-src/guide.py; --internal flag produces the ops edition.
- OVA Validation Guide: docs/Simvay-Collector-OVA-Validation-Guide.pdf (follow its sections 3 and 5).
- ovf/README.md holds the real packaging procedure (host-client GUI export, Prepare-Ovf.ps1, manifest regeneration, repack).
- Verbatim records as of 2026-08-05 in archive/ in this folder: HANDOFF (2026-08-03, seed v8), backlog (2026-08-05), gold-build-progress (2026-08-03).
