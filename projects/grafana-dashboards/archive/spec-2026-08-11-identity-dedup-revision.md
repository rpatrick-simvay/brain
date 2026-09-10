# Revised: identity dedup and ingest strategy

**For:** Ryan (review) → build session (on-computer)
**From:** architecture (opus agent), amended with 2026-08-11 live verification
**Date:** 2026-08-11
**Status:** proposal awaiting Ryan's approval. Nothing has been changed. Supersedes §3 (dedup strategy) and §4 (implementation order) of `claude/spec-2026-07-31-identity-collection-fields-and-dedup.md`, and §3 and §6.3 of `claude/handoff-2026-07-31-identity-pipeline-for-james.md`. §2 (field inventory) of the 7/31 spec stands unchanged.
**Basis:** 7/31 measurements, the 8/1 PagerDuty implementation record, and fresh VictoriaLogs measurements taken 2026-08-11 over a 24h window (via browser; lab unreachable from the cloud session).
**Scope decision (Ryan, 8/11):** full identity pipeline — dedup re-architecture, Duo routing, batching, watermark, widened Entra columns, UserLoginFailed branch. The work formerly earmarked for James on Vector is ours; API-side enrichment asks remain his (§7).

Every decision below is marked **Settled** or **Pending #n**, referring to the numbered verification items in §8. Nothing marked Pending should be built.

---

## 1. What changed since 7/31

### 1.1 The PagerDuty work invalidated Layer 2

The 7/31 design put four layers of dedup in the pipeline; Layer 2 was an n8n `removeDuplicates` node per branch using `removeItemsSeenInPreviousExecutions`. The 8/1 PagerDuty build removed exactly that node before it ever ran, for a reason that applies identically here:

> `removeItemsSeenInPreviousExecutions` commits its keys when the node runs, not when the workflow succeeds. A POST failing partway through a batch marks every remaining record as "seen".

For PagerDuty the consequence was permanent silent loss, because resolved incidents never get re-fetched. For identity it is **worse**, not better. An Entra or Duo auth event is a historical audit record: once the pull window has moved past it, nothing will ever re-present it. A single failed POST would burn a hole in the identity record with no error anywhere in n8n, no gap visible in a count, and no way to detect it after the fact. Layer 2 is withdrawn in full.

Four further learnings carry over as constraints, all verified live on 8/1:

| Learning | Applies to identity as |
|---|---|
| One POST per record exhausted Vector's FDs and crashed the whole topology (1,244 records / 6s against a 1,024 limit) | The Entra branch pushes ~790 single POSTs/min today — the same shape, at sustained rate. `LimitNOFILE=65535` is now set, which raises the ceiling but does not remove the pattern. §4 |
| `http_server` with `encoding: json` splits a JSON array into one event per element, types intact | Batch to arrays of 200. §4 |
| Content-hash (`payload_hash`, FNV-1a) dedup keys, because `updated_at` is not guaranteed to move | **Does not apply.** Identity events are immutable; this is the one PagerDuty pattern we should deliberately not copy. §2.1 |
| All three sinks now carry disk buffers (`when_full: block`) | Done. Any new sink must carry one. |
| n8n REST edits land as drafts; a workflow must be explicitly published | Ops constraint on every change below. #8 |

### 1.2 Fresh measurements (2026-08-11, VictoriaLogs, 24h)

| Measure | 7/31 | 8/11 | Read |
|---|---|---|---|
| Duo events | 3,098 | **7,284** | Truncation appears fixed — but by whom and when is unknown (#3) |
| Duo unique `txid` | 3,098 | **7,284** | Key still perfect. Zero dupes |
| Duo hourly rate | ~129 avg | **~350/hr, steady 12:00–17:00Z** | Consistent with `limit` fixed, not a burst |
| Duo `email` present | 20% | **964 / 7,283 (13%)** | Coverage fell as volume rose. Correlation ask unchanged |
| Duo `auth_device` geo | 15–16% | **672 / 7,283 (9%)** | Absolute count up 35%, volume up 135% |
| Duo `access_device.location` | — | 339 (4.7%) | Duo's own geo is thinner than assumed |
| Duo `access_device` enriched | 0 | **0** | Unchanged ask |
| Entra `src_endpoint.ip` | 0 | **0** | Unchanged |
| Entra `device.is_compliant` | 0 | **0** | Unchanged |
| Entra `unmapped.LogonError` | 0 | **0** | Stream C still not collected |
| Entra `device.is_managed` variants | 4 | **4** (True 520 / False 1,015 / true 14 / false 53) | Unchanged |
| Entra 24h rows / unique uid | — | **1,602 / 1,602** | dedup_microsoft currently producing zero dupes |
| Microsoft-ISP enriched records | ~40/day | **~62/day** | The Canada FP root cause is growing |

**The `auth_device` geo question from 7/27 is answered, and the answer is no.** The 7/31 spec speculated that `limit` truncation was capping enrichment. Volume rose 135% while enriched records rose only 35% — so the recovered events were disproportionately un-enriched. Truncation was not the cause; whatever gates enrichment to a minority of Duo records is a separate, still-unexplained behaviour on the API side.

### 1.3 Correction: the parser does not drop `metadata.original_time` or `type_name`

The 7/31 handoff asked James to "stop dropping `metadata.original_time` and `type_name`" at :9001. That ask is wrong and should be withdrawn. The `vlogs` sink is configured `_msg_field: type_name`, `_time_field: metadata.original_time` — VictoriaLogs **consumes** whatever those name. This is the identical behaviour the PagerDuty work documented for `description` and `isotimestamp`, and the same reason Duo's `isotimestamp:*` returns zero rows.

**Confirmed live 8/11:** a sampled Microsoft record carries `_msg: "Authentication: Logon"` and `_time` at event time (16:xxZ on a record queried at 18:xx). Both fields are present — in `_time` and `_msg`. If separately queryable copies are wanted (they are, for filtering on event time independent of `_time` and grouping on record type), the fix is the PagerDuty pattern: n8n emits duplicate fields (`event_time`, `record_type`) alongside the consumed originals. One-line Code node change on our side, not an ask for James. This also invalidates acceptance check 8 as written (§9). **Settled.**

---

## 2. Revised dedup architecture

**Principle: Vector owns all dedup. No `removeDuplicates` node exists anywhere in the identity workflows, in any operation mode.**

The layer model from 7/31 collapses to two real layers plus a read-time fallback:

| Layer | 7/31 | Now |
|---|---|---|
| 1 — watermark | n8n Data Table | **Kept.** Scope narrowed: cost control only, never correctness. §3 |
| 2 — n8n `removeDuplicates` | per-branch node | **Removed entirely** |
| 3 — Vector dedupe | "backstop" | **Promoted to sole owner of correctness** |
| 4 — LogsQL `uniq by` | last resort | Kept as read-time fallback for post-restart windows. §2.5 |

### 2.1 Do identity records mutate after first write? No — and this drives everything

A PagerDuty incident is a **stateful object**: created, acknowledged, resolved, with derived metrics settling hours later. Re-fetching the same `id` legitimately returns different content — hence `[id, payload_hash]` matching and per-panel `stats by (id)` reduction.

An Entra sign-in or Duo authentication is an **immutable fact**. The 7/31 field-by-field comparison of colliding `metadata.uid` records found them **byte-identical, same timestamp, every attribute equal**.

Consequence, **Settled**: identity dedup keys are **identity-only**. `txid` for Duo, `metadata.uid` for all three Entra streams. No content hash, no timestamp, no field triple.

The corollary: with exactly one row per event, identity panels need **no reduction stage**. `count()`, `avg()` and `stats by (...)` are directly correct — none of the two-stage machinery the PagerDuty feed requires.

**The one real cost, accepted explicitly:** key-only dedup means a stored record is never re-written even when the pipeline improves. When `src_endpoint.ip` enrichment lands, already-ingested records stay unenriched; only forward data benefits. Pipeline improvements require a deliberate backfill into a new stream, not a re-run of the collector. Plan for it; do not discover it (#11).

### 2.2 The S1 datalake's own 7% duplicates

The datalake returns byte-identical duplicates inside a single response: 795/739 unique on the success path, 303/290 on failures. Three consequences: (1) they are **intra-response** — no watermark or window change removes them; Vector dedupe is the only thing that catches them. (2) Byte-identical → collapsing loses nothing. (3) They prove dedup must be downstream of the pull, not a function of the window.

**Optional diagnostic:** carry `payload_hash` (FNV-1a, already written for PagerDuty) on Entra records as a normal field *excluded from the match list*, so the immutability assumption stays falsifiable.

### 2.3 The current `dedup_microsoft` key is defective — found in this revision

As of the 7/31 read, `dedup_microsoft` matches the content triple `(metadata.original_time, device.ip.query, actor.user.email_addr)` against a 5,000-event cache. Two defects:

1. It collapses two genuinely distinct sign-ins sharing user, IP and timestamp — a burst of session refreshes is exactly that shape.
2. **`UserLoginFailed` records have no `device.ip` at all**, so on the new stream the triple degenerates to `(time, email)`, collapsing distinct failed attempts against one account in one second — precisely the spray pattern the stream exists to detect, under-counted in the direction that looks like good news.

Hard ordering constraint: **the key change lands before the `UserLoginFailed` branch** (§6, phase 1 → phase 5).

### 2.4 Transform config

**Pending #1 and #4 — do not apply until the path-syntax question is resolved.** #1 has a catastrophic quiet failure mode (§8).

```yaml
transforms:
  dedup_microsoft:
    type: dedupe
    inputs: [microsoft_ingest]
    cache:
      num_events: 50000
    fields:
      match:
        - metadata.uid          # if the payload arriving at :9001 is NESTED
      # match:
      #   - '"metadata.uid"'    # if the payload is FLAT with a literal dotted key

  dedup_duo:                    # already exists per 8/1 read; key already correct
    type: dedupe
    inputs: [duo_ingest]
    cache:
      num_events: 50000
    fields:
      match: [txid]
```

Use `fields.match`, never `fields.ignore`: match caches only the matched value (36-char GUID, single-digit MB at 50k entries); ignore caches the whole event and would multiply with the widened field set. Match mode is also immune to the column-widening transition (#5).

### 2.5 Cache sizing and restart behaviour

Sizing is driven by the worst realistic re-presentation burst (a stalled watermark catching up ≈ 1,000 records), not daily volume. 50,000 for all transforms; raising `dedup_microsoft` from 5,000 costs nothing. **Settled.**

Vector's dedupe cache is in-memory: lost on restart, and lost per-transform on SIGHUP if that transform's config changed. After a restart the next overlap window re-presents records and they land as duplicate rows — bounded at ≤ ~30 (Entra post-watermark), ≤ ~790 (pre-watermark), ≤ ~380 (Duo). Every such duplicate is byte-identical, so the cost is storage only, **provided panels count with `count_uniq(metadata.uid)` / `count_uniq(txid)`, never `count()`**. Mitigations in order: panel discipline (free), a rows-vs-unique-keys daily health check (check 10), SIGHUP-not-restart hygiene. Persisting the cache is not worth operating.

---

## 3. Watermark for the Entra pull

**Kept, mechanism unchanged, purpose narrowed to cost control.** `last_seen_time` per stream in an n8n Data Table, `startTime = last_seen_time - 15m`, write back newest `metadata.original_time`. Takes ~790 records/run to ~10–30:

| | Records pushed/day | POSTs/day | Relative payload bytes |
|---|---|---|---|
| Today (9 cols, 12h lookback, 1 POST/record) | 1,137,600 | 1,137,600 | 1.00 |
| Watermark only | ~29,000 | ~29,000 | 0.025 |
| Watermark + batching + 30 cols | ~29,000 | ~1,440 | **~0.08** |

**Mandatory: the watermark advances only after the POST succeeds.** A Data Table write beside the POST has exactly the commit-on-run failure mode that got `removeDuplicates` deleted. The write sits strictly downstream on the success path; a failed run then self-heals (watermark stays, next run re-pulls, Vector drops what already landed).

Division of labour, strict: watermark fixes pull cost only and must never be treated as dedup; Vector dedupe fixes correctness only. If the watermark misbehaves the store is still correct and the bill is higher; if Vector dedup is wrong the store is wrong.

---

## 4. Batching

**Settled.** n8n Code node groups records into JSON arrays of 200; one POST per array (verified 8/1: Vector splits arrays into events with types intact). The Entra branch today is the crash shape from 8/1 as a steady drip — the latent risk is any catch-up burst. Batching removes the shape, not just the margin.

| Branch | Today | After |
|---|---|---|
| Entra | ~790 POSTs/run | 1 POST/run post-watermark (~4 pre-watermark) |
| Duo | ~304/run if one-per-item (#2) | 2 POSTs/run |

---

## 5. Duo routing

**End state (same under both hypotheses of #2): Duo terminates at Vector :9002 → `dedup_duo` → `vlogs_duo`.**

Evidence conflicts: the 7/31 review read the n8n node as POSTing directly to VL :9428 (`/insert/jsonline` with `VL-*` headers); the 8/1 vector.yaml read found `vlogs_duo` configured with the exact equivalent parameters. Both paths produce byte-identical rows in VL, so only reading the n8n node URL settles it (#2). Either way the change is n8n-side only; no Vector config change needed.

| If Duo posts to | Change |
|---|---|
| VL :9428 directly | POST URL → `http://10.10.100.13:9002`, drop the three `VL-*` headers (sink supplies equivalents), add batching, republish |
| Vector :9002 already | Add batching, republish |

Gains: Duo stops being the one stream with zero idempotency (today it survives only because its window happens not to overlap), inherits the disk buffer, one ingestion pattern across the environment. **Do not change Duo cadence in the same step** (#3, #10).

---

## 6. Field-set rollout — phased build plan

| Phase | Change | Where | Gate before proceeding |
|---|---|---|---|
| **0** | Verification sweep: #1, #2, #3, #4 | read-only | All answered in writing |
| **1** | `dedup_microsoft` match → `metadata.uid`; cache → 50,000 | vector.yaml, SIGHUP | Check 10 holds 24h; Entra count still advances |
| **2** | Batching (Entra + Duo); Duo re-routed to :9002 | n8n, republish | Checks 11, 12; Duo holds ~7,284/24h |
| **3** | Watermark, Data Table write downstream of POST | n8n, republish | Check 13; deliberately fail one run, watermark must not advance |
| **4** | Widen Entra columns (7/31 §2 list); emit `event_time`/`record_type`; optional `payload_hash` | n8n, republish | Checks 3, 4, 6, 8 |
| **5** | `UserLoginFailed` branch | n8n, 4 nodes | Check 5. **Hard-blocked on phase 1** (§2.3) |
| **6** | Duo cadence / limit review | n8n | Rate-limit watch (#10) |

Phase 4 consideration: add `unmapped.Operation` to the `vlogs` sink `_stream_fields` so the three Entra streams separate cleanly; accept the visible transition boundary in stream listings.

---

## 7. What stays with James (API-side)

1. **Enrich `src_endpoint.ip`**, or coalesce `src_endpoint.ip → device.ip → unmapped.ActorIpAddress` before enrichment — root cause of the Canada FPs (~62/day, growing); retires the 5-panel Grafana workaround.
2. **Enrich Duo `access_device.ip`** — 0 of 7,284 records carry it; it's the workstation.
3. **Emit `lat`/`lon` as numbers** — carried from 7/27.
4. **Fix the 4-hour timestamp offset** — the phase-3 watermark is timestamp arithmetic and should not be built on an unquantified offset without knowing whether it applies to `/sentinelone/datalake/queryall` (#14).

**Withdrawn:** the "stop dropping original_time/type_name" ask (§1.3).
**Open, unassigned:** Duo `email` at 13% caps Duo↔Entra correlation; needs a decision before detection work (resolve `user.key` → email, or key correlation differently).

---

## 8. Risks and open verification items

Phases 1–5 must not be built until **1, 2, 3, 4** are answered.

1. **Vector dedupe path syntax vs payload shape — BLOCKER.** The 7/31 spec says Entra fields are literally named `metadata.uid` (flat, dot in the name — n8n needed `disableDotNotation`). But `dedup_microsoft` matches unquoted `metadata.original_time` etc., which Vector parses as *nested* paths — and that transform demonstrably works. Both cannot be true of one payload. VL storage can't settle it (VL flattens nested JSON on ingest — confirmed 8/11 that VL rows show flat dotted names either way). If the match list resolves to undefined on every event, every event gets the same key and **only the first event ever passes — the stream silently stops**. Verify by POSTing two probe records with differing `metadata.uid` to a scratch port carrying a copy of the transform; confirm two rows land. Never test on :9001.
2. **Duo POST target + request shape.** Read the `Push to Log DB` node URL in n8n; record one-per-item vs single body. One-per-item at 304/hr is a live FD hazard today.
3. **Who changed Duo limit/cadence?** 3,098 → 7,284/day with no project doc recording it. Confirm current `limit`, schedule, and the execution-history date of the change. An unowned production change is a risk regardless of whether it was correct. Ask James before assuming.
4. **Current `dedup_microsoft` match fields and cache size** — live vector.yaml read; the file was edited 8/1 (PagerDuty path, buffers) after the 7/31 read.
5. **Column widening vs byte-identity.** Under match-on-`metadata.uid` alone: widening is transition-safe (uid unchanged → recognised as seen). Under any content matching: every re-fetched record becomes a new row the moment columns change. Independent argument for key-only matching. Flip side: enrichment improvements never reach stored rows (#11).
6. **§1.3 confirmed 8/11** — `_msg`/`_time` carry type/event-time on the Microsoft stream. Closed.
7. **Restart duplicate admission — accept or mitigate.** Recommendation: accept, with `count_uniq` panel discipline + check 10. Ryan's call.
8. **n8n draft vs published.** Every REST edit needs an explicit publish; the tell is the orange dot. A draft-only change presents as "the fix did nothing" and invites a second, wrong fix.
9. **Disk buffer headroom.** Worst case 768 MB against 3.7 GB free on /; phase 4 triples Entra record size, phase 5 adds a stream. Re-check before phase 4.
10. **Duo API rate limiting.** `limit=200` and `limit=5000` returned zero where `limit=1000` returned 237 (7/31). Change cadence in one step, watch for empty responses, never combined with the routing change.
11. **Enrichment retro-fill.** When `src_endpoint.ip` lands, decide forward-only vs backfill-to-new-stream deliberately. Key-only dedup makes an in-place re-run a silent no-op.
12. **Pull-scope filters are not airtight** (PagerDuty precedent: 16 incidents leaked through a service filter). Panels filter on `Operation`/`record_type` explicitly.
13. **`metadata.uid` uniqueness across streams** — assumed, unproven until phase 5's first 24h confirms no uid appears in both a success and failure record.
14. **n8n access from browser sessions:** the Chrome extension blocks credentialed fetch (cookies/JWT sanitized), so REST via browser JS is not viable; UI-only. On-computer sessions use the REST API directly as before.

---

## 9. Acceptance checks

1–9 from the 7/31 handoff, baselines refreshed 8/11, check 8 rewritten per §1.3. 10–16 new.

| # | Check | Query | Now (8/11) | Want | Phase |
|---|---|---|---|---|---|
| 1 | Duo volume holds | `_msg:authentication \| stats count() n` (24h) | 7,284 | ≥7,000 stable | 2 |
| 2 | No Duo dupes | `\| stats count_uniq(txid) n` | = total | = total | 2 |
| 3 | Client IP present | `…Microsoft "src_endpoint.ip":* \| stats count() n` | 0 | ~100% | 4 |
| 4 | Compliance queryable | `…"device.is_compliant":* \| count()` | 0 | ~97% | 4 |
| 5 | Failed logins landing | `unmapped.LogonError:* \| count()` (24h) | 0 | ~300 | 5 |
| 6 | Device fields flattened | `…"device.browser":* \| count()` | 0 | ~96% | 4 |
| 7 | Booleans normalized | `…stats by ("device.is_managed") count()` | 4 variants | 2 | 4 |
| 8 | Event time queryable (rewritten) | `…"event_time":* \| count()` + `_time` at event time | 0 / confirmed | ~100% | 4 |
| 9 | Canada FPs gone | `…"device.ip.isp":"Microsoft Corporation" \| count()` | ~62/day | 0 | James |
| 10 | Entra dedup healthy | `…Microsoft \| stats count() rows, count_uniq("metadata.uid") uniq` | 1,602 = 1,602 | rows = uniq ± restart window | 1 |
| 11 | Duo terminates at Vector | n8n node URL = `:9002`; `vlogs_duo` events > 0 | unconfirmed | confirmed | 2 |
| 12 | Batching in effect | POSTs per run (n8n execution detail) | ~790 / ~304? | ≤5 / ≤2 | 2 |
| 13 | Watermark advancing and safe | Data Table `last_seen_time`; force-fail one run | n/a | fresh; unchanged after failed run | 3 |
| 14 | Duo email coverage | `email:* \| count()` | 964 (13%) | decision needed | — |
| 15 | Duo access_device enriched | `"access_device.isp":* \| count()` | 0 | >0 | James |
| 16 | Duo auth_device geo | `"auth_device.lat":* \| count()` | 672 (9%) | explained, then raised | James |

Checks 1–5 unblock detection work. 10–13 gate this document's own changes.
