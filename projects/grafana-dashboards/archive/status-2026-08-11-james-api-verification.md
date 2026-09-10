# Status — verification of James's API changes (2026-08-11 ~23:20Z)

Live probes from the Vector LXC console against the Simvay API + VictoriaLogs. Read-only.

## Verified working

1. **Duo dual-axis enrichment ✅** — 3h/863-record sample: both `access_device` and `auth_device` now carry the full ip-api pro block (`isp, org, as, proxy, hosting, mobile, lat, lon, city, regionName, country, continent, query`).
2. **lat/lon numeric ✅** — floats on both axes (e.g. 41.5053), no longer strings.
3. **Datalake `enrich_fields` selector ✅ (schema level)** — new param on `/sentinelone/datalake/queryall` backed by new `SentinelOneIpField` enum: `['device.ip', 'src_endpoint.ip', 'src.ip.address', 'dst.ip.address']`.

## Not working / gaps

4. **Duo email resolution ❌** — still 100/863 (11.6%) after the change window; no `resolve_email` param exists and coverage is unchanged. The user.key→email join is either not deployed or not working. Back to James.
5. **`unmapped.ActorIpAddress` missing from `SentinelOneIpField` ⚠️** — Stream C (UserLoginFailed) client IPs can't be enriched. Only blocks step 5 detections' geo, not collection. Ask James to add the enum member.
6. **Unverified: src_endpoint.ip enrichment output** — probes during what appears to have been James's deploy window returned transient tenant 500s ("Tenant 17/21 failed... check credentials") and empty arrays; by end of session `enrich=true` returned 1,712 records consistently but the browser bridge dropped before a record with an enriched `src_endpoint.ip` block could be sampled. First check next session.

## Operational note — Entra ingest gap ~19:00–23:00Z

VL received zero Microsoft rows after ~19:00Z while the datalake itself holds events through 21:33Z (1,720 records in an 8h direct query). Timing + transient tenant errors are consistent with the API being down/flaky during James's deploy. The production pull re-fetches a 12h window every 60s, so the gap should self-heal now that the API answers — **confirm VL Microsoft count recovers (hours 20:00–23:00Z backfill) before building anything**. If it hasn't recovered, check n8n SentinelOne Push/Pull execution history first.

## Raw-shape observation (for the build session)

Un-enriched datalake responses wrap records as `{"attributes": {flat dotted keys}}` (seen live: `attributes["metadata.uid"]`). Production dedupe demonstrably resolves nested paths (`device.ip.query`), implying the enrichment/prep path restructures records to nested before Vector. The step-3 QA gate (payload-shape probe against the actual widened+enriched payload) covers this — do not skip it.

## Bottom line

Build steps 1–4 fully unblocked. Step 5's enrichment gap (#5) is non-blocking for collection. Outstanding for James: email resolution (#4), ActorIpAddress enum member (#5). Outstanding to verify: src_endpoint enrichment sample (#6) + VL gap recovery.
