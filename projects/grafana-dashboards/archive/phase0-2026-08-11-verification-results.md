# Phase 0 verification results — all four items answered (2026-08-11)

Read-only sweep run live via Chrome (n8n UI + Proxmox console on LXC 101 TEMP-Vector, SIMSRV-PVE2 — note: reached via SIMSRV-PVE1 web UI at 10.10.98.5:8006). Gate for spec §6 phase 0 is **met**. Nothing was changed; the one scratch Vector instance used for the probe was killed and `/tmp/vector-probe` removed (port 9009 free, production `vector` service `active` after cleanup).

## #1 — Payload shape vs dedupe path syntax (was BLOCKER): RESOLVED — payload is NESTED; use unquoted `metadata.uid`

Probe: scratch Vector 0.55.0 instance on :9009, dedupe transform `match: [metadata.uid]` (unquoted), file sink. Five POSTs, all HTTP 200:

| # | Body | Landed? |
|---|---|---|
| 1 | `{"metadata":{"uid":"N1"},"tag":"nested-first"}` | yes |
| 2 | `{"metadata":{"uid":"N1"},"tag":"nested-dup"}` | **dropped (correct dedup)** |
| 3 | `{"metadata":{"uid":"N2"},"tag":"nested-distinct"}` | yes |
| 4 | `{"metadata.uid":"F1","tag":"flat-first"}` | yes |
| 5 | `{"metadata.uid":"F2","tag":"flat-distinct"}` | **DROPPED — silent swallow** |

Unquoted `metadata.uid` resolves only on nested payloads. On flat literal-dotted keys it resolves to null for every record → all share one cache key → **everything after the first record is silently dropped** (row 5 proved the catastrophic failure mode is real).

Payload at :9001 is therefore **nested**: production `dedup_microsoft` uses unquoted nested paths for its match triple and demonstrably distinguishes events (1,602 distinct rows/24h). If the payload were flat, all three match fields would resolve null and ~1 row/day would land. The 7/31 spec's "flat with literal dotted keys" reading described n8n's internal item shape, not the JSON on the wire.

**Phase 1 config is confirmed safe as written: `match: [metadata.uid]`, unquoted.**

## #2 — Duo POST target + request shape: RESOLVED — already Vector :9002, one-POST-per-item

`Push to Log DB` node in Duo Push/Pull: `POST http://10.10.100.13:9002`, auth none, no headers, Body Raw = `{{ JSON.stringify($json) }}` → **one POST per record**. The 7/31 review's "direct to VL :9428" reading is stale (see #3 — James re-routed it Jul 31). Phase 2 for Duo = **batching only, no re-route**. One-per-item at current volume (~29 records/5-min run) is mild, but catch-up bursts keep the FD-hazard shape — batching still warranted.

## #3 — Duo limit/cadence change attribution: RESOLVED — James Hering, Jul 31 15:14:58

n8n version history, Duo Push/Pull v0.92, James Hering, **Jul 31 at 15:14:58**, commit note: *"Duo now goes through the temporary dedup mechanism."* Current params: `limit=1000`, schedule every **5 min**, window `mintime = now − 15 min` → 3× overlapping window. That overlap is why `dedup_duo` matters: Duo volume recovery (3,098 → 7,284/day) dates to Jul 31 PM and the zero-dupe result is Vector actively deduping, not luck-of-the-window. Two follow-ups: (a) confirm with James there wasn't also an API-side change; (b) he labeled the Vector path "**temporary**" — align with him before he reverts it, since the revised architecture makes it permanent.

## #4 — Live `dedup_microsoft`: RESOLVED — defective triple confirmed still in place

`/etc/vector/vector.yaml` live read:

- `dedup_microsoft`: match `(metadata.original_time, device.ip.query, actor.user.email_addr)`, cache **5,000** — the defective content triple from §2.3, unchanged.
- `dedup_duo`: match `txid`, cache **50,000** — already at spec target; phase 1 only touches dedup_microsoft.
- `dedup_pagerduty`: match `(id, payload_hash)`, cache 50,000.
- All three sinks: VL :9428 elasticsearch, disk buffers 256 MB. Microsoft sink `_msg_field: type_name`, `_time_field: metadata.original_time` (consumption behavior re-confirmed).

## Spec deltas

1. §5 routing table: hypothesis "Vector :9002 already" is true — phase 2 Duo work shrinks to batching.
2. §2.4: nested variant confirmed; delete the flat-variant comment branch.
3. dedup_duo cache change is a no-op (already 50k).
4. New risk: James's "temporary" framing of the Duo→Vector path — coordinate before build so it isn't reverted mid-rollout.

## State

Phase 0 complete. Phases 1–6 unblocked pending Ryan's approval of the phase table (spec §6).
