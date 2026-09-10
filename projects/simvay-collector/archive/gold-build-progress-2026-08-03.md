# Golden image → OVA — SHIPPED

## 2026-08-03 (night): 1.0.1 CLEARED TO SHIP

**`simvay-collector-1.0.1.ova` — 2.65 GB, manifest validates, `Families: vmx-19` (ESXi 7.0 U2
floor), all 18 ProductSection properties, NVRAM included.** The double-deploy seal test passed on
its first-ever run; full evidence table is in HANDOFF §5.4 (clones `simvay-collector-6ec7bb` /
`-54b357` — distinct hostnames, machine-ids, host keys; one clone configured and ingesting into
SIMVAY-NFR with a green self-test, no SSH used). Deployment Guide v2.2 (client-ready) shipped the
same day. Post-release items live in `claude/backlog.md`; nothing blocks handing the OVA to the
managed-tech team.

### What this release cycle taught (for the next cut)

1. **The one keystroke of drift theory held**: hand-created VMs produced the BIOS-firmware slip
   this cut (caught by the build report's `firmware:` line — the check worked). Script VM creation
   with govc/PowerCLI before the next cut; vmx-19 + EFI + 80/100 GB disks are all hand-set.
2. **The host-client deploy wizard says "Required disk image is missing" on its final page** for
   multi-file OVAs. Cosmetic. Documented in the guide §3, troubleshooting §11, and ovf/README.
3. **Prepare-Ovf.ps1** now does all four OVF edits + the vmx-19 gate + manifest regeneration in one
   run. The exporter writes `<Item ovf:required="false">` — any Item-matching regex must allow
   attributes (first run failed safe on exactly this).
4. **Firstboot regenerates SSH keys before it renames the host**, so the key comment reads
   `root@s1collector-gold` on every clone. Keys differ; cosmetic; reorder steps on the next cut.
5. The hostname generator's factory pattern MUST match its own generated names
   (`simvay-collector-[0-9a-f]+`) — firstboot re-runs on the master after any reboot, and seal now
   also resets the hostname. Guard test: `tests/test_hostname_logic.sh`.

### The release in one table

| | |
|---|---|
| Seed | v8 — sha256 `eca415acdd46d8ad20f382ffedf327682971bf20311795f27aaaf0c6bb29e2a2` |
| Image | Ubuntu 24.04.4, EFI, vmx-19, Docker 29.7.1, 3 images pre-pulled, open-vm-tools 13.0 gated |
| Changes vs v7 | bug 11/11b/11c, seal dotfile fix, 15-char-only passphrase rule, unique per-clone hostnames, Hyper-V stripped, injector replaces ProductSection |
| Verification | HANDOFF §4 all green (twice — BIOS respin), test_web.py 70/70, hostname guard test, seed validated by extraction |
| Seal test | PASSED (first ever run) — identity divergence + ingest proven |
| Guide | v2.2 client-ready; `--internal` flag for the ops edition |
| Dead artifacts | 1.0.0 OVA (bug 11), seeds v1–v7, BIOS-firmware v8 VM — all listed for deletion in backlog §3 |

Historical packaging procedure and the vmx/pciRootBridge scar are preserved in `ovf/README.md`.
The blow-by-blow of the earlier cycles was rotated out of this doc on 2026-08-03; git history in
the session workspace and HANDOFF §3's bug table carry the details.
