---
title: Simvay Collector decisions
type: decisions
updated: 2026-09-09
---

# Decisions (append-only, one dated line each)

Dates before 2026-08-03 are the design phase; the exact day was not recorded in the source docs and is given as the phase.

- 2026-07 (Ryan): Product name is Simvay Collector; "SentinelOne" is reserved for SentinelOne's own products.
- 2026-07 (Ryan): Browser-first configuration; only vCenter was believed to deliver OVF properties and a browser works on every hypervisor. See 2026-08-05 note below.
- 2026-07 (Ryan): Ubuntu 24.04 for the golden image, not 26.04; Action1 documents 22.04 and 24.04 only, S1 agent support for 26.04 unverified.
- 2026-07 (Ryan): EFI firmware on the master.
- 2026-07 (Ryan): Netplan matches NICs by glob, never by name (VMXNET3 gives ens192).
- 2026-07 (Ryan): Spool disk found by shape, not /dev/sdb; disk 2 mounts at /var/lib/docker; spool is a Docker named volume.
- 2026-07 (Ryan): One collector per client; the config format holds exactly one tenant key.
- 2026-07 (Ryan): Match Meraki on srcip (Meraki puts an epoch timestamp where the hostname belongs, so hostname matching fails silently); other vendors may use any of the five attributes.
- 2026-07 (Ryan): One source-type per subnet (matchers within a source-type are ANDed); per-port syslog format because Meraki (RFC 3164) and Veeam (RFC 5424) both default to 514.
- 2026-07 (Ryan): S1 agent installed last and never activated on the master (KB 000005482); firstboot resets the UUID and starts it on the clone.
- 2026-07 (Ryan): Action1 package baked at build, installed and registered on the clone by firstboot.
- 2026-07 (Ryan): Setup console has no external dependencies; write key is entered in the browser only; status page is public (hostname, address, uptime only), setup pages are not.
- 2026-08-03 (Ryan): Hyper-V dropped; VMware only; open-vm-tools is a hard build gate; the hv-* masking loop and dual guest-tools install are deleted, not masked.
- 2026-08-03 (Ryan): Passphrase rule is a 15-character minimum only; the 16-char and 4-word rules and the lowercase requirement are gone. Generated factory secrets stay lowercase four-word phrases for console readability.
- 2026-08-03 (Ryan): Validation rules for collector name, source names and matcher globs relaxed to match SentinelOne KB 000008665; all five matcher attributes offered in a dropdown; names and matchers double-quoted in generated YAML.
- 2026-08-03 (Ryan): Default hostname is generated unique per clone (simvay-collector-<6 hex of machine-id>); OVF property s1.hostname still overrides; seal resets the master to s1collector-gold.
- 2026-08-03 (Ryan): Master built at hardware version vmx-19; ESXi 7.0 U2 is the supported floor; never relabel VirtualSystemType in the OVF in either direction (relabelling vmx-21 to vmx-15 produced an OVA that imported and failed to power on with pciRootBridge unsupported).
- 2026-08-03 (Ryan): OVA 1.0.0 is dead (bug 11) and must never be deployed; 1.0.1 cleared to ship after the double-deploy seal test passed.
- 2026-08-03 (Ryan): Deployment Guide default build is the client-ready edition with no internal blocks; python3 guide.py --internal produces the ops edition.
- 2026-08-03 (Ryan): OVA export uses the ESXi host-client GUI export, not ovftool vi:// (ESXi account lockout after 5 failed logins hid behind an open GUI session); ovftool vi:// kept only as fallback.
- 2026-08-04 (Ryan): 1.0.1 downgraded to demo/dev only; static networking inoperative (netdef merge bug). 1.0.2 cut from seed v10 to fix it.
- 2026-08-05 (Ryan): Deployment Guide v2.3 validated window by window against the real ESXi 8.0 U3 host-client wizard; standalone ESXi 8.x does show an Additional settings window with the OVF property categories, so the "only vCenter delivers OVF properties" rationale is under review; browser-first design stays regardless.
- 2026-09-09 (Ryan): Project knowledge migrated from the Claude Project "SentinelOne Collector (Simvay Collector)" into this brain repo; this folder is canonical from here on.
