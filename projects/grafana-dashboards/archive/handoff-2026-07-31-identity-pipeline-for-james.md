# Handoff: identity pipeline changes

**To:** James
**From:** Ryan
**Date:** 2026-07-31
**Scope:** data collection only. No detection or dashboard work here — that starts once this lands.

Nothing was changed. This came out of a read-only pass over n8n (`10.10.99.13:5678`), the Simvay API (`10.10.100.8:8000`) and VictoriaLogs (`10.10.100.12:9428`) on 2026-07-31. Every figure below was measured live.

Detail lives in `claude/review-2026-07-31-n8n-identity-enrichment.md` and `claude/spec-2026-07-31-identity-collection-fields-and-dedup.md`. This doc is the actionable list.

---

## The short version

Three things are wrong with identity collection, and none of them are detection-logic problems:

1. **Duo is dropping ~50% of its events** to an unset `limit` parameter.
2. **We collect 9 of 66 available Entra fields**, and 303 failed logins/day are excluded entirely.
3. **We're enriching a Microsoft-owned IP** instead of the client IP, which is the root cause of the Canada false positives we papered over on 2026-07-27.

Plus one structural risk: the Entra branch pushes ~1.1M records/day and something undocumented at `:9001` is silently deduping it down to ~1,650.

---

## 1. Duo: add `limit=1000` — 1 minute, biggest single win

**Workflow:** `Duo Push/Pull` → node `Pull Duo Auth Logs`

`GET /duo/authlogs` has a `limit` that **defaults to 100**. The node doesn't pass one.

| Query | Events returned (1 hour) |
|---|---|
| default | 118 |
| `limit=1000` | **237** |

Corroborated downstream: VictoriaLogs holds 3,098 Duo events over 24h against ~5,700 expected at the observed rate — a 46% shortfall. This has been truncating every hourly pull since February.

Add `limit=1000` as a query parameter alongside `mintime`/`maxtime`.

⚠️ **Test gently.** While probing I found `limit=200` and `limit=5000` both returned zero where `limit=1000` returned 237. That's either parameter validation or Duo API rate limiting — I stopped rather than risk starving the production pull. Change it once, then watch for empty responses.

Also worth knowing: the pull uses a 60-minute window on a 60-minute schedule with no overlap and no watermark. Any late, slow, or failed run loses those events permanently.

## 2. Entra: widen the column list — 5 minutes

**Workflow:** `SentinelOne Push/Pull` → node `Pull Entra Logins in SentinelOne Datalake`

The records carry **66 attributes**; the query requests 9. Suggested replacement for `columns`:

```
metadata.uid,metadata.original_time,metadata.correlation_uid,metadata.product.vendor_name,
type_name,event.type,cloud.org.uid,
actor.user.email_addr,actor.user.uid,actor.session.uid,
device.ip,src_endpoint.ip,device.is_managed,device.is_compliant,device.os.type,device.os.type_id,
dst_endpoint.uid,status_id,status_detail,http_request.user_agent,
unmapped.DeviceProperties,unmapped.ExtendedProperties,unmapped.Operation,unmapped.RecordType,
unmapped.BrowserName,unmapped.BrowserVersion,unmapped.AuthenticationType,unmapped.GeoLocation,
unmapped.ApplicationDisplayName,unmapped.AppAccessContext.ClientAppName
```

The ones that matter most, with measured coverage over 790 records / 12h:

| Field | Cov. | Why |
|---|---|---|
| `src_endpoint.ip` | 100% | **true client IP** — see §5 |
| `device.is_compliant` | 97% | first-class field; today we string-parse `DeviceProperties` for the same value |
| `actor.user.uid` | 97% | Entra object GUID — stable join key, better than email |
| `actor.session.uid` | 99% | ties a sign-in burst together |
| `status_id` / `status_detail` | 100% / 97% | **Entra does have success/failure** — corrects finding #10 in the 7/27 status doc |
| `unmapped.Operation` / `RecordType` | 100% | required to tell the record types apart |
| `cloud.org.uid` | 100% | tenant separation |

Note there are **two record shapes** in this stream: `UserLoggedIn` (764/12h) and `SignInEvent` (26/12h). Only `SignInEvent` carries the browser/UA fields, so those will show ~3% coverage overall. That's expected, not a bug.

Also: `enrich=true` is redundant — it already defaults to `true` on both endpoints per `/openapi.json`.

## 3. Dedup the n8n branches — 15 minutes

`n8n-nodes-base.removeDuplicates` **v2** is available on this instance (2.6.4). Verified operations: `removeDuplicateInputItems`, `removeItemsSeenInPreviousExecutions`, `clearDeduplicationHistory`.

Add one node per branch, `operation: removeItemsSeenInPreviousExecutions`, `logic: removeItemsWithAlreadySeenKeyValues`:

| Branch | `dedupeValue` |
|---|---|
| Duo | `={{ $json.txid }}` |
| Entra logons | `={{ $json["metadata.uid"] }}` |
| Entra failures | `={{ $json["metadata.uid"] }}` |

Set `options.historySize` to 50,000 and `options.scope` to `workflow`.

**Set `options.disableDotNotation: true` on the Entra branches** — the field is literally named `metadata.uid`, dot included, and n8n will otherwise read it as a nested path.

Keys verified: Duo `txid` 237/237 unique in a 1h sample and 3,098/3,098 in VL over 24h; Entra `metadata.uid` 100% present on all record types.

Worth knowing: **the S1 datalake returns duplicates of its own** — 795 records carried 739 unique `metadata.uid` (7%). I compared colliding records field by field and they are byte-identical, same timestamp. Deduping on `metadata.uid` is strictly correct.

## 4. Add a `UserLoginFailed` branch — ~1 hour

**303 failed logins in 24 hours, none collected.** The current filter excludes them twice: `event.type='Logon'` doesn't match, and `device.ip = *` fails because these records have **no `device.ip` and no `src_endpoint.ip`** — the client IP is in `unmapped.ActorIpAddress`.

Needs its own pull:

```jsonc
{
  "filter": "dataSource.vendor='Microsoft' unmapped.Operation='UserLoginFailed'",
  "startTime": "1 hour",
  "columns": "metadata.uid,metadata.original_time,metadata.product.vendor_name,type_name,cloud.org.uid,actor.user.email_addr,actor.user.uid,unmapped.UserKey,unmapped.ActorIpAddress,unmapped.ClientIP,unmapped.LogonError,unmapped.ErrorNumber,unmapped.ResultStatus,unmapped.DeviceProperties,unmapped.ExtendedProperties,unmapped.ApplicationId,unmapped.Operation,unmapped.RecordType,status_id"
}
```

What's in there, measured over 24h:

| `unmapped.LogonError` | AADSTS | Count |
|---|---|---|
| `IdsLocked` | 50053 | **83** |
| `InvalidUserNameOrPassword` | 50126 | 81 |
| `UserStrongAuthClientAuthNRequiredInterrupt` | 50074 | 57 |
| `UserDisabled` | 50057 | **25** |
| `ExternalSecurityChallenge` | 50158 | 15 |
| 12 others | — | 42 |

83 smart-lockout events and 25 attempts against disabled accounts in a single day. Top source IPs: `23.244.10.130` (61), `76.8.81.194` (29), `38.122.61.234` (7), `45.141.215.124` (3). Most-targeted: `asimanella139719@polaris.edu` (27), `michelleb@greatlakesbrewing.com` (13), `tstohr@cc-efi.com` (13).

`unmapped.DeviceProperties` is present on 99% of failures too, so device context survives on this path.

## 5. API: enrich the client IP, not the Microsoft IP

**This is the one that needs you rather than the n8n config.**

Enrichment is applied only to `device.ip`. On `SignInEvent` records that field holds a Microsoft service IP:

```
device.ip       = 2a01:111:2053:120b:0:afd:ad4:4ad0
                  → enriched to country "Canada", isp "Microsoft Corporation"
src_endpoint.ip = 67.144.164.6      ← the actual user, unenriched, discarded
```

21 of 790 records in 12h (~40/day). This is why we had to inline `!device.ip.isp:("Microsoft Corporation" OR "Microsoft Limited")` into Grafana panels 13, 15, 20, 30 and 31 — it's compensating for enriching the wrong field.

**Ask:** enrich `src_endpoint.ip`, or coalesce `src_endpoint.ip → device.ip → unmapped.ActorIpAddress` before enrichment. If that lands we delete the five-panel workaround instead of maintaining it, and those sign-ins become real signal.

Still open from 7/27 and unchanged: enrich Duo's `access_device.ip` the same way, and emit `lat`/`lon` as numbers rather than strings (`claude/spec-2026-07-27-duo-access-device-geo-enrichment.md`).

## 6. Parser at `10.10.100.13:9001`

Four things:

1. **Flatten `device_attributes`.** It reaches VictoriaLogs intact but as an unparsed JSON string, so nothing can group or alert on it. Suggested targets: `device.uid`, `device.name`, `device.browser`, `device.trust_type`, `device.session_uid`. (`IsCompliant` becomes unnecessary once §2 adds the first-class `device.is_compliant`.)
2. **Normalize booleans.** `device.is_managed` arrives as four values: `True` (4,343), `False` (7,458), `true` (118), `false` (403), plus 13 empty.
3. **Stop dropping `metadata.original_time` and `type_name`.** Both are requested and neither survives into VictoriaLogs.
4. **What is this thing?** It's the only component between the Entra branch and VictoriaLogs, and it appears to be absorbing ~1.1M pushes/day down to ~1,650 unique rows — its VL fingerprint (`source_type: http_server`, `path: /`) looks like Vector with a `dedupe` transform. If that's right, it's load-bearing and named "temporary". Worth documenting its dedupe key and cache TTL, and renaming it. Duo doesn't pass through it at all.

## 7. Optional: watermark instead of a fixed lookback

The Entra pull runs every 60s over a 12-hour window — each record is fetched ~720 times. §3 fixes the wasted *pushes*; this fixes the wasted *pulls*.

Store `last_seen_time` per stream in an n8n Data Table (the `Temporary Account Link` pattern already exists), query `startTime = last_seen_time - 15m`, write back the newest `metadata.original_time`. Takes ~790 records/run down to ~10-30.

Not urgent if §3 lands. Worth doing before the field set grows much further.

---

## Acceptance checks

Run these against VictoriaLogs once the changes are in. Current values measured 2026-07-31.

| # | Check | Query | Now | Want |
|---|---|---|---|---|
| 1 | Duo volume recovered | `_msg:authentication \| stats count() n` (24h) | 3,098 | ~5,700 |
| 2 | No Duo dupes | `_msg:authentication \| stats count_uniq(txid) n` | = total | = total |
| 3 | Client IP present | `metadata.product.vendor_name:Microsoft "src_endpoint.ip":* \| stats count() n` | 0 | ~100% |
| 4 | Compliance queryable | `metadata.product.vendor_name:Microsoft "device.is_compliant":* \| stats count() n` | 0 | ~97% |
| 5 | Failed logins landing | `unmapped.LogonError:* \| stats count() n` (24h) | 0 | ~300 |
| 6 | Device fields flattened | `metadata.product.vendor_name:Microsoft "device.browser":* \| stats count() n` | 0 | ~96% |
| 7 | Booleans normalized | `metadata.product.vendor_name:Microsoft \| stats by ("device.is_managed") count() n` | 4 variants | 2 |
| 8 | Event time preserved | `metadata.product.vendor_name:Microsoft "metadata.original_time":* \| stats count() n` | 0 | ~100% |
| 9 | Canada FPs gone | `metadata.product.vendor_name:Microsoft "device.ip.isp":"Microsoft Corporation" \| stats count() n` | ~40/day | 0 |

Checks 1-5 unblock the detection work. 6-9 make it clean.

---

## What this unblocks

Once the data lands, the detection and dashboard work becomes straightforward — none of it needs further pipeline changes:

1. **Password spray / brute force** — `IdsLocked` and `InvalidUserNameOrPassword` by source IP and by target account. Nothing exists today.
2. **Disabled-account probing** — `UserDisabled` (25/day) is a clean post-offboarding signal.
3. **Device-trust signals** — non-compliant and unmanaged sign-ins, using real fields instead of string-parsed ones.
4. **Delete the Microsoft exclusion** from Grafana panels 13, 15, 20, 30, 31, and recover those sign-ins as real data.
5. **Device context in the OCSF alert** — the `Build Alert` node in `Identity Alert Hook` needs new `related_events` entries once the Grafana rules can emit device labels.

One caveat for later: **Entra has no auth-device concept.** It gives one device, and it's the source device — richer than Duo's on every dimension, but there's no second endpoint. Duo remains the only source for the workstation-vs-2FA geo comparison.

## Open questions

1. Is the Duo `limit` per-tenant or global? Default returned 118, not 100.
2. Can the Duo collector emit `email` on every record? Only 20% carry it in VL (7.6% in a fresh API sample); the rest have only `user.name`, a bare username with no domain. Any Duo↔Entra correlation keyed on email drops 80%+ of the Duo side.
3. What exactly is the parser at `:9001`, and is "temporary" a plan or a leftover?
4. Still open from 7/27: why do only 15-16% of Duo auths carry `auth_device` geo? The `limit` truncation in §1 may be part of the answer.
