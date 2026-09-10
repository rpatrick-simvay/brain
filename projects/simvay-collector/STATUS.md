---
title: Simvay Collector status
type: status
updated: 2026-09-09
owner: Ryan
---

# Simvay Collector: status as of 2026-09-09

Last substantive record is 2026-08-05. Nothing later was captured in the Claude Project, so the state below is a month old and should be confirmed against the ESXi host and the SharePoint project folder before acting on it.

## Where it stands
- Phase 1 (prove the collector, Meraki to SDL, parsed and verified by query) and Phase 2 (golden image) are complete.
- Release 1.0.2 is packaged, validated, and deployed once from the OVA with a clean first boot on clone SIMVAY-TEST-102 (10.10.76.48): banner with URL and passphrase, unique hostname simvay-collector-964538, new "DHCP assigned from 10.10.76.1" banner line. Seed v10 (sha256 d8c4c435...34c259) is the source-of-record seed. 1.0.0 is dead (bug 11); 1.0.1 is demo/dev only (static networking broken).
- Deployment Guide v2.3 (7 pages, client-ready) validated against the live ESXi 8.0 U3 host-client wizard; VALIDATE-ON-HOST markers stripped; structural-humanizer audit clean.
- The gold master was destroyed after export (2026-08-04); the next cut rebuilds from seed v10, which carries everything.
- Live systems at last record: demo clone 10.10.76.42 (hand-patched, forwarding to SIMVAY-NFR, keep it); Meraki syslog still enabled including Appliance Flows (about 2.2M events/day into SIMVAY-NFR), which was flagged as not something to leave running indefinitely.
- Not started: Veeam validation (no client Veeam server available); Hyper-V package (dropped, VMware only).

## Next three actions
1. Ryan: run the static-IP test on the .48 clone, the one fix 1.0.2 exists for. Sign in at https://10.10.76.48:8443 (click through the cert warning once), set a static address, confirm the browser reconnects at the new address and rollback-confirm works, then set it back or redeploy. About 30 minutes. If it passes, mark 1.0.2 released in this file.
2. Ryan: on the next deploy, set Hostname in the host-client Additional settings window and run journalctl -t s1-collector-firstboot | grep -i ovf on the clone to learn whether standalone ESXi delivers OVF properties. About 20 minutes. Record the answer as a DECISIONS line either way.
3. Ryan: housekeeping on ESX01-Local: delete seeds v1 to v9 from ISOs/, delete dead 1.0.0 and 1.0.1 artifacts and stale C:\Temp exports, tear down throwaway test VMs (keep 10.10.76.42), and confirm whether Meraki Appliance Flows syslog should stay on. About 30 minutes.

## Later
- Engineering debt: govc or PowerCLI scripted VM creation (vmx-19, EFI, 80/100 GB disks are all hand-set today and produced one BIOS-firmware slip); input validator in self-test; firstboot reorder so SSH key comments carry the clone hostname; pvscsi decision; netconfig SIGPIPE note.
- Guide screenshots (certificate interstitial needs a human browser) and the one-page quick card; capture at the first real client deployment.
- Live-messages re-check on a configured post-clone appliance (optional).
- Write runbooks/simvay-collector-image-test-and-seal.md from HANDOFF sections 4 and 5 once the next cut is scheduled.

## Blocked
- Nothing blocked. Veeam validation waits on a client Veeam server.
