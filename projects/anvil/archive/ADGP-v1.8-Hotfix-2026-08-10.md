# ADGP Collector v1.8 Hotfix — 2026-08-10

Two fatals hit back-to-back on the Olmsted Falls City Schools ADGP run (package built 2026-08-10 19:04). Both fixed in `E:\Projects\Anvil` the same evening.

## Bug 1 — profile path clobbered by variable collision
**Symptom:** `FATAL: Client profile not found: System.Collections.Hashtable` at line 101, immediately at startup.
**Cause:** v1.7 (2026-08-07) renamed the internal variable `$profile` → `$clientProfile` to stop shadowing the automatic `$PROFILE`. PowerShell variable names are **case-insensitive**, so `$clientProfile` is the *same variable* as the `$ClientProfile` parameter — line 99 (`$clientProfile = @{}`) overwrote the caller's path with an empty hashtable (truthy) before the `Test-Path` check. Every v1.7 run that passed `-ClientProfile` was broken.
**Fix:** internal variable renamed to `$profileData`.

## Bug 2 — manifest.json write used a PS7-only parameter
**Symptom:** after Bug 1 was patched, run collected all 15 evidence items then died: `FATAL: A parameter cannot be found that matches parameter name 'Path'` at the manifest step.
**Cause:** `Out-File -Path` — Windows PowerShell 5.1 (what DCs run) has no `-Path` on `Out-File`; that alias for `-FilePath` is PS 7-only. Every other `Out-File` in the script already used `-FilePath`; the manifest.json line was the one typo. Evidence + manifest.csv had already written; only manifest.json was lost.
**Fix:** `-Path` → `-FilePath`.

## Same typo fixed in six more collectors
The identical `Out-File -Path (Join-Path $runDir "manifest.json")` line existed in **action1, duo, m365, manual (Add-ManualEvidence), mimecast, sentinelone** — likely never bit because those run under PS 7 on the analyst workstation, where `-Path` is a valid alias. All six fixed as a line-only change (no version bump; visible in git diff). Collectors that didn't have the typo: auvik, gws, knowbe4, meraki, umbrella.

## Build impact
Anvil-Configurator copies collector scripts from source at package build time (Anvil-Configurator.ps1:877), so all packages built after 2026-08-10 evening carry both fixes. The Olmsted on-site copy was hand-patched line-by-line to complete the run.

## Related, not fixed
`Collect-M365Evidence.ps1` line 87 still uses `$profile = @{}` — shadows automatic `$PROFILE` (cosmetic, works today), but renaming it to `$clientProfile` would recreate Bug 1. If renaming, use `$profileData`.

## Lessons
1. Any variable rename in the collectors must be checked case-insensitively against the param block — PS treats `$clientProfile` and `$ClientProfile` as one variable.
2. Collectors destined for DCs must stick to Windows PowerShell 5.1 parameter surface (`Out-File -FilePath`, etc.); PS7-only aliases pass testing on the workstation and fail in the field.
