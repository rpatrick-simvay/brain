# Spec: identity collection field set + dedup strategy

**For:** James (Simvay API / collectors / n8n)
**From:** Ryan
**Date:** 2026-07-31
**Status:** proposal — nothing has been changed. All figures measured live against the Simvay API, VictoriaLogs and n8n on 2026-07-31.
**Background:** `claude/review-2026-07-31-n8n-identity-enrichment.md`

---

## 1. Why this exists

We want richer identity detections. The blocker is not the detection logic — it is that we collect a narrow slice of what is available, and the collection cadence is built in a way that makes widening it expensive.

Three measured problems:

| # | Problem | Measured |
|---|---|---|
| 1 | **We drop ~86% of the Entra fields.** | Records carry 66 attributes; the n8n query requests 9. |
| 2 | **We lose ~50% of Duo events.** | `/duo/authlogs` `limit` defaults to 100. One hour returns **118** events by default, **237** with `limit=1000`. Corroborated downstream: VictoriaLogs holds 3,098 Duo events over 24h, against ~5,700 expected at the observed 237/hr rate — a 46% shortfall. |
| 3 | **We push ~1.1M records/day to store ~1,650.** | The Entra pull runs every 60s over a 12-hour window: 790 records × 1,440 runs. Deduplication happens invisibly downstream. |

Problem 3 is what stops us fixing 1 and 2 cheaply. Widening the field set multiplies an already 700× redundant payload. So the dedup strategy has to land first, or alongside.

---

## 2. Field inventory — what to pull

### 2.1 Microsoft / Entra (via `POST /sentinelone/datalake/queryall`)

There are **three distinct record shapes** behind the Microsoft vendor. They do not share a field set, and a single query cannot capture all three. Each needs its own pull.

#### Stream A — `UserLoggedIn` (Office 365 audit successful sign-in)

~764 events / 12h. The bulk of the volume, and the richest per-record.

| Field | Cov. | Collected today | Why |
|---|---|---|---|
| `metadata.uid` | 100% | ✅ | **dedup key** |
| `metadata.original_time` | 100% | ✅ (dropped by parser) | event time — must survive to VL |
| `actor.user.email_addr` | 100% | ✅ | identity |
| `actor.user.uid` | 97% | ❌ | **Entra object GUID — stable join key, better than email** |
| `actor.session.uid` | 99% | ❌ | ties a sign-in burst together |
| `device.ip` | 100% | ✅ | keep, but see §2.3 — not always the client |
| `src_endpoint.ip` | 100% | ❌ | **true client IP** |
| `device.is_managed` | 100% | ✅ | needs boolean normalization |
| `device.is_compliant` | 97% | ❌ | **first-class field — no JSON parsing needed** |
| `device.os.type` | 100% | ✅ | |
| `device.os.type_id` | 99% | ❌ | numeric OS, no casing problems |
| `unmapped.DeviceProperties` | 97% | ✅ | device GUID, DisplayName, BrowserType, TrustType, SessionId |
| `status_id` / `status_detail` | 100% / 97% | ❌ | **success/failure exists** — corrects finding #10 in the 2026-07-27 status doc |
| `metadata.correlation_uid` | 100% | ❌ | correlate related events |
| `dst_endpoint.uid` | 97% | ❌ | which tenant/app was accessed |
| `unmapped.ExtendedProperties` | 97% | ❌ | carries UserAgent, UserAuthenticationMethod, RequestType |
| `unmapped.Operation` | 100% | ❌ | **required to tell the three streams apart** |
| `unmapped.RecordType` | 100% | ❌ | same |
| `type_name` | 100% | ✅ (dropped by parser) | |
| `cloud.org.uid` | 100% | ❌ | tenant — needed for multi-client separation |

#### Stream B — `SignInEvent` (Entra sign-in log)

~26 events / 12h. Small volume, but the only stream with browser/UA detail — and the one where `device.ip` is wrong (§2.3).

Everything in Stream A, plus:

| Field | Cov. within stream | Why |
|---|---|---|
| `http_request.user_agent` | 100% | full UA string |
| `unmapped.BrowserName` | 100% | parsed browser — better than `BrowserType` |
| `unmapped.BrowserVersion` | 100% | version-based risk |
| `unmapped.AuthenticationType` | 100% | e.g. `FormsCookieAuth` |
| `unmapped.GeoLocation` | 100% | Microsoft's own region code |
| `unmapped.AppAccessContext.ClientAppName` | 100% | client app |
| `unmapped.ApplicationDisplayName` | 100% | target app |

#### Stream C — `UserLoginFailed` — **not collected at all**

**303 events / 24h.** Excluded twice over by the current filter: `event.type='Logon'` does not match, and `device.ip = *` fails because these records have **no `device.ip` and no `src_endpoint.ip`**.

| Field | Cov. | Why |
|---|---|---|
| `metadata.uid` | 100% | dedup key |
| `actor.user.email_addr` | 97% | target account |
| `actor.user.uid` / `unmapped.UserKey` | 100% | 124 distinct users targeted in 24h |
| `unmapped.ActorIpAddress` | 99% | **client IP — different field name than the success path** |
| `unmapped.ClientIP` | 99% | same value; keep one |
| `unmapped.LogonError` | 98% | `IdsLocked`, `InvalidUserNameOrPassword`, … |
| `unmapped.ErrorNumber` | 100% | AADSTS code |
| `unmapped.ResultStatus` | 100% | `Failed` |
| `unmapped.DeviceProperties` | 99% | **device context is present on failures too** |
| `unmapped.ExtendedProperties` | 100% | UserAgent, UserAuthenticationMethod, RequestType |
| `unmapped.ApplicationId` | 100% | 41 distinct apps |
| `metadata.original_time` | 100% | |
| `cloud.org.uid` | 100% | tenant |

What this unlocks, measured over 24 hours:

| `unmapped.LogonError` | AADSTS | Count | Detection |
|---|---|---|---|
| `IdsLocked` | 50053 | **83** | smart lockout fired — active spray / brute force |
| `InvalidUserNameOrPassword` | 50126 | 81 | the spray itself |
| `UserStrongAuthClientAuthNRequiredInterrupt` | 50074 | 57 | MFA interrupt |
| `UserDisabled` | 50057 | **25** | attempts against disabled accounts |
| `ExternalSecurityChallenge` | 50158 | 15 | |
| 12 others | — | 42 | |

Top source IPs: `23.244.10.130` (61), `76.8.81.194` (29), `2600:382:dd0c:…` (14), `38.122.61.234` (7), `45.141.215.124` (3).
Most-targeted: `asimanella139719@polaris.edu` (27), `michelleb@greatlakesbrewing.com` (13), `tstohr@cc-efi.com` (13), `tp.admin@polaris.edu` (9).

83 lockouts and 25 disabled-account attempts in one day, with zero visibility today.

### 2.2 Duo (via `GET /duo/authlogs`)

The Duo record is already pulled whole — every field arrives. The problems here are **truncation** and **enrichment on the wrong endpoint**, not field selection.

| Field | Cov. (7d, VL) | Note |
|---|---|---|
| `txid` | 100% | **dedup key** — verified 237/237 unique in a 1h sample |
| `isotimestamp` / `timestamp` | 100% | |
| `email` | **20%** | ⚠️ only 7.6% in a fresh 1h API sample. See §5. |
| `user.name` | 100% | short username (`tothn`, `fabrizia`) — no domain |
| `user.key` | 100% | Duo user GUID — the reliable identity key |
| `user.groups` | — | AD sync groups |
| `access_device.ip` | 100% | ⚠️ **14% are `0.0.0.0`** |
| `access_device.hostname` | 17% | |
| `access_device.epkey` | — | Duo endpoint GUID |
| `access_device.location.{city,state,country}` | — | Duo's own geo, not enriched |
| `auth_device.{lat,lon,city,regionName,country,continent,isp,org,as,proxy,hosting,mobile,query}` | 16% | ip-api enriched — **the phone, not the workstation** |
| `application.{key,name}` | 100% | |
| `factor` | 100% | |
| `result` / `reason` | 100% | |
| `trusted_endpoint_status` | 100% | 97% `unknown`, 601 `trusted`, 62 `not trusted` (7d) |
| `passport_assessment` | — | |
| `ood_software` | — | out-of-date software |

### 2.3 The one API change that matters most

**Enrichment is applied only to `device.ip`.** On `SignInEvent` records that field holds a *Microsoft service IP*:

```
device.ip       = 2a01:111:2053:120b:0:afd:ad4:4ad0
                  → enriched to country "Canada", isp "Microsoft Corporation"
src_endpoint.ip = 67.144.164.6      ← the actual user, unenriched, discarded
```

21 of 790 records in 12h (2.7%, ~40/day). This is the root cause of the Canada false positives that forced the `!device.ip.isp:("Microsoft Corporation" OR "Microsoft Limited")` exclusion into Grafana panels 13, 15, 20, 30 and 31.

**Ask:** enrich `src_endpoint.ip`, or coalesce `src_endpoint.ip → device.ip → unmapped.ActorIpAddress` before enrichment. That single change retires a five-panel workaround and converts suppressed noise into usable signal.

Related, and already filed in `claude/spec-2026-07-27-duo-access-device-geo-enrichment.md`: enrich Duo's `access_device.ip` too, and emit `lat`/`lon` as numbers rather than strings.

---

## 3. Dedup strategy

### 3.1 What happens today

```
n8n (every 60s, 12h lookback)  ──790 records──►  parser :9001  ──~1 record──►  VictoriaLogs
        ~1,137,600 records/day pushed                                    ~1,650 rows/day stored
```

VictoriaLogs holds **1,656 Microsoft rows / 1,656 unique `metadata.uid`** and **3,098 Duo rows / 3,098 unique `txid`** over 24h. Zero duplicates. The push node returns HTTP 200 on all 790 items every minute.

So dedup already works — but it lives entirely in the "temporary parser" at `10.10.100.13:9001`. Its VictoriaLogs fingerprint (`source_type: http_server`, `path: /`) is consistent with a Vector `http_server` source plus a `dedupe` transform.

**This is the risk.** A component named "temporary" is silently absorbing a 700× write amplification and is the only thing preventing VictoriaLogs from filling with duplicates. Nothing else in the pipeline is idempotent. If it is retired, restarted with a cleared cache, or has its dedupe buffer overflow, duplicates flow straight through — and Duo does not pass through it at all.

### 3.2 Dedup keys — verified

| Source | Key | Verified |
|---|---|---|
| Duo | `txid` | 237/237 unique in a 1h sample; 3,098/3,098 in VL over 24h |
| Entra, all three streams | `metadata.uid` | 100% present on all record types |

An important detail: **the SentinelOne datalake itself returns duplicates.** In a 12h success-path pull, 795 records carried 739 unique `metadata.uid` (7% dupes); on failed logins, 303 records carried 290 unique (12 groups). I compared the colliding records field by field — they are **byte-identical, same timestamp, every attribute equal**. So they are true duplicates from the source, not distinct events sharing an ID. Deduping on `metadata.uid` is therefore strictly correct and strictly beneficial.

### 3.3 Proposed design

Four layers, each cheap, each independently useful. Layers 1–2 are the ones that matter.

**Layer 1 — Stop the overlap. Replace the fixed lookback with a watermark.**

The 12-hour window on a 60-second schedule exists because there is no memory of what was already fetched. Give it memory:

- Store `last_seen_time` per stream in an n8n **Data Table** (the pattern already exists — `Temporary Account Link`), or in workflow static data via `getWorkflowStaticData('global')` in a Code node.
- Each run queries `startTime = last_seen_time - safety_margin`, then writes the newest `metadata.original_time` back.
- Safety margin of 15 minutes covers the datalake's own ingest lag. That gives ~15× overlap instead of ~720×.

Effect: ~790 records/run → ~10-30 records/run. **A ~98% reduction in write volume**, which is what buys the headroom to add 50 more fields and a third stream.

**Layer 2 — Make n8n idempotent. Add a Remove Duplicates node.**

n8n on this instance is **2.6.4**. I confirmed against `/types/nodes.json` that `n8n-nodes-base.removeDuplicates` **v2** is present with:

```
operation: removeDuplicateInputItems | removeItemsSeenInPreviousExecutions | clearDeduplicationHistory
logic:     removeItemsWithAlreadySeenKeyValues | removeItemsUpToStoredIncrementalKey | removeItemsUpToStoredDate
options:   scope, historySize, disableDotNotation, removeOtherFields
```

Config per branch — `operation: removeItemsSeenInPreviousExecutions`, `logic: removeItemsWithAlreadySeenKeyValues`:

| Branch | `dedupeValue` |
|---|---|
| Duo | `={{ $json.txid }}` |
| Entra `UserLoggedIn` / `SignInEvent` | `={{ $json["metadata.uid"] }}` |
| Entra `UserLoginFailed` | `={{ $json["metadata.uid"] }}` |

Set `options.historySize` well above 24h of volume (~5,700 Duo + ~1,700 Entra) — 50,000 is comfortable. Set `options.scope` to `workflow` so the three branches keep separate histories.

Note `disableDotNotation: true` is required for the Entra branches — the field is literally named `metadata.uid` with a dot in it, and n8n would otherwise read it as a nested path.

This makes the collector correct on its own, independent of the parser, and it fixes Duo — which today has no dedup protection whatsoever and only avoids duplicates because its window happens not to overlap.

**Scope note:** this node dedupes *after* the API response, so it eliminates the ~1.1M/day of wasted **pushes** but not the wasted **pulls**. That is the right trade for 15 minutes of work — the push side is where the write amplification and the dependency on the parser live. Layer 1 is what fixes the pull side.

There is also a `removeItemsUpToStoredDate` logic mode that acts as a built-in watermark on `metadata.original_time`. It is worth considering, but it has the same limitation — the stored date is not readable back into the query expression, so it cannot narrow `startTime`. For Layer 1 a Data Table remains the cleaner mechanism.

**Layer 3 — Keep the parser dedupe, but make it explicit and monitored.**

Do not remove it; it is a good backstop. But it should be documented, given a non-"temporary" name, and its dedupe cache size/TTL written down. With Layers 1–2 in place it becomes a safety net rather than the load-bearing wall.

**Layer 4 — Query-time dedup as a last resort.**

If a duplicate ever does land, LogsQL can absorb it at read time:

```
metadata.product.vendor_name:Microsoft | uniq by ("metadata.uid")
```

Useful for backfills and incident cleanup. Not a substitute for Layers 1–2 — it costs query time on every dashboard refresh.

### 3.4 Cadence once this lands

| Stream | Today | Proposed | Rationale |
|---|---|---|---|
| Entra `UserLoggedIn` + `SignInEvent` | 60s / 12h window | 60s / watermark + 15m | same freshness, ~2% of the volume |
| Entra `UserLoginFailed` | not collected | 60s / watermark + 15m | spray detection wants minutes, not hours |
| Duo | 60m / 60m window, **limit 100** | 5m / watermark + 15m, **`limit=1000`** | fixes the 50% loss and the no-overlap data gap |

The Duo change is the one with a hard dependency: **`limit=1000` must be passed**, or a faster cadence just truncates more often. Worth confirming with James whether the limit is per-tenant or global, since the default returned 118 rather than exactly 100.

⚠️ **Care needed when testing Duo cadence.** The Duo Admin API is rate-limited. While probing, `limit=200` and `limit=5000` both returned zero records where `limit=1000` returned 237 — that may be parameter validation or it may be rate limiting. I stopped probing rather than risk starving the production hourly pull. Change Duo cadence in one step, then watch for empty responses.

---

## 4. Suggested implementation order

Ordered by value per unit of effort. Steps 1–3 are edits to a single n8n node each.

| # | Change | Where | Effort |
|---|---|---|---|
| 1 | Add `limit=1000` to the Duo pull | n8n, one query param | 1 min — **recovers ~50% of Duo events immediately** |
| 2 | Add the Stream A/B fields to `columns` | n8n, one string | 5 min |
| 3 | Add Remove Duplicates nodes (Layer 2) | n8n, 3 nodes | 15 min |
| 4 | Watermark instead of fixed lookback (Layer 1) | n8n, Data Table + expression | ~1 hr |
| 5 | New branch for `UserLoginFailed` (Stream C) | n8n, 4 nodes | ~1 hr |
| 6 | Enrich `src_endpoint.ip` / coalesce | **Simvay API — James** | unknown |
| 7 | Flatten `device_attributes`, normalize booleans, stop dropping `metadata.original_time` / `type_name` | **parser :9001 — James** | unknown |
| 8 | Promote device fields into Grafana alert labels; extend `Build Alert` | Grafana + n8n | ~2 hrs |

Steps 1–5 are ours and need no API change. Steps 6–7 are the asks for James.

---

## 5. Open items

1. **Duo `email` coverage is 20% in VL and 7.6% in a fresh API sample.** Everything else carries only `user.name` (a bare username, no domain). Any Duo↔Entra correlation keyed on email silently drops 80%+ of the Duo side. Can the collector resolve `user.key` → email, or can `email` be emitted on every record?
2. **Is the Duo `limit` per-tenant or global?** Default returned 118, not 100.
3. **What exactly is the parser at `:9001`?** Confirm it is Vector, what its dedupe key and cache TTL are, and whether "temporary" means it is scheduled for removal.
4. **Why does the parser drop `metadata.original_time` and `type_name`?** Both are requested and neither reaches VictoriaLogs.
5. Still open from 2026-07-27: why do only 15-16% of Duo auths carry `auth_device` geo? The `limit` truncation in §1 may be a partial answer — it was capping every hourly pull.
