---
title: Simvay Collector log
type: log
updated: 2026-09-09
---

# Session log (append-only)

Entries before 2026-09-09 are reconstructed from the Claude Project docs (HANDOFF.md, claude/gold-build-progress.md, claude/backlog.md), verbatim copies of which are in archive/.

## 2026-07 (Cowork and Claude in Chrome, with Ryan): PoC and design
Phase 1 proven: Meraki syslog into SIMVAY-NFR Data Lake, parsed, verified by query. Appliance plan, PoC plan and PoC build log written to the SharePoint project folder. Volume measured on a quiet lab network (3.7 events/sec without Appliance Flows, 25.8 with). Design decisions listed in DECISIONS.md.

## 2026-07 to 2026-08-03 (Cowork and Claude in Chrome, with Ryan): golden image
Unattended build (seed ISO, one keystroke of human input) built and run repeatedly; seeds v1 to v7 each fixed a batch of bugs (bugs 1 to 10, table in archive/HANDOFF.md section 3). Bug 6 (ufw never opened 8443, every fresh deployment deadlocked) produced the two build gates. Bug 10 (banner advertised the console before it could answer) produced the readiness screen. Setup console exercised on a live VM; validation rules audited against SentinelOne KB 000008665 and relaxed. Action1 agent staging added (v6). Hyper-V support dropped.

## 2026-08-03 (Cowork, with Ryan): 1.0.1 cleared to ship
Seed v8 (bug 11/11b/11c chrony first-boot death and EXIT trap, seal dotfile fix, 15-char passphrase rule, unique per-clone hostnames, Hyper-V stripped, ProductSection injector replaces instead of skips). Master rebuilt once after a BIOS-firmware slip on a hand-created VM. HANDOFF section 4 checks all green, test_web.py 70/70, hostname guard test, seed validated by extraction. Double-deploy seal test passed first run (clones 6ec7bb and 54b357: distinct hostnames, machine-ids, host keys; one clone configured and ingesting with no SSH). simvay-collector-1.0.1.ova (2.65 GB, vmx-19, 18 ProductSection properties) packaged via host-client GUI export and Prepare-Ovf.ps1. Deployment Guide v2.2 shipped. HANDOFF rewritten as the durable summary; gold-build-progress rotated to a release summary.

## 2026-08-04 (Cowork, with Ryan): 1.0.2 cut
1.0.1 found to have inoperative static networking (netdef merge bug); demoted to demo/dev. Seed v9 then v10 (adds the "DHCP assigned from" banner line). 1.0.2 packaged. Gold master destroyed after export; seed v10 is the source of record.

## 2026-08-05 (Cowork and Claude in Chrome, with Ryan): 1.0.2 validated, guide v2.3
1.0.2 deployed once from the OVA with a clean first boot (clone SIMVAY-TEST-102, 10.10.76.48). Deployment Guide v2.3 validated window by window against the ESXi 8.0 U3 host-client wizard via live browser walk: exact quirk text "A required disk image was missing.", an Additional settings window with OVF property categories on standalone ESXi 8.x, a License agreements sidebar step that disappears after parsing, Power on automatically pre-checked, about 7 minutes upload for the 2.6 GB OVA. Backlog written. Open: static-IP test on the .48 clone, OVF-properties-on-standalone question, datastore housekeeping.

## 2026-09-09 (Cowork, with Ryan): migration to brain
Project knowledge migrated from the Claude Project into projects/simvay-collector (BRIEF, DECISIONS, STATUS, LOG, archive of the three source docs). The gold VM OS password that appeared in HANDOFF section 10 was not copied; the archive copy carries a redaction marker. No project state changed. Blocked: none. Next: the three actions in STATUS.md, all Ryan's.
