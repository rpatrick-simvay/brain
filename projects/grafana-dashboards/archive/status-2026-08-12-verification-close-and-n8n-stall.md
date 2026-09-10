# Status — verification closed; n8n[DEV] scheduler stalled; Action1 added to scope (2026-08-12 ~01:10Z)

Follow-up to `claude/status-2026-08-11-james-api-verification.md`. Spreadsheet is now **v4** (in session).

## Closed

1. **src_endpoint.ip enrichment VERIFIED ✅** — 312/312 records in a 6h enriched sample carry the full ip-api block on both `device.ip` and `src_endpoint.ip` (numeric lat/lon, boolean proxy/hosting/mobile, original IP in `query`).
2. **Raw shape note:** enrichment replaces the IP string with an object, on records whose keys are flat-dotted under an `attributes` wrapper. Payload-shape QA gate at build step 3 remains mandatory.
3. **Decision (Ryan): Duo email resolution OUR side** — daily branch: `GET /duo/users` → n8n Data Table `duo_user_directory` → join by user.key in Duo Normalise (record email → directory email → absent). API ask withdrawn.
4. **ActorIpAddress enum member: James in progress** (gates step 5 enrichment only).
5. **Confirmed:** all normalization in n8n Normalise + Stamp nodes; API enriches; Vector dedups.

## Scope additions (Ryan, 8/12)

6. **This n8n instance (10.10.99.13, "n8n[DEV]") IS the deployment target.** The Identity flow replaces: Duo Push/Pull (whole), Action1 Push/Pull (login branch), Entra branch of SentinelOne Push/Pull. S1 inventory branches stay.
7. **Action1 console logins join the identity streams.** Reviewed live: branch pulls `GET /action1/audit/events/loginips` every 10 min with an exact zero-overlap window (boundary-loss risk), pushes DIRECT to VL :9428 (no dedup, no buffer). Sampled 30 records/24h: `id` (dedup key), `user_name`=email, `user_id` GUID, naive `timestamp`, `org_id/org_name`, `status_message`, and `ipv4` **already fully ip-api enriched**. Design: envelope mapping in spreadsheet sheet 6; new Vector chain `:9004 → dedup_action1 [id] → vlogs_action1` (disk-buffered); watermark+overlap replaces the exact window. Rollout step 2b.
8. **Open: Action1's stats branch** (usage/org stats → :9428) loses its home — recommend a slimmed 'Action1 Stats' workflow, NOT the Identity flow. Ryan to decide.
9. **Duo double-ingest confirmed by evidence:** Duo rows landed in VL 3+ hours after this instance's last Duo run (20:15:34Z) → a parallel legacy-n8n Duo feed exists; `dedup_duo` absorbs the overlap (explains James's "temporary dedup mechanism"). Retire it during step 2 or volume validation is meaningless.

## Open incident — n8n[DEV] scheduler stopped Aug 11 20:15:47Z (revised)

- Full execution feed shows activity until **20:15:47** including manual/test runs at 20:13–20:15 (test-flask icon on #308328) — someone was working in the instance right before it stopped. Nothing has executed since (4.5h+). Web UI healthy, workflows "Published".
- Entra→VL dark since; datalake accumulating normally. 12h-lookback self-heal window closes ~**08:15Z Aug 12**; after that a manual widened-window backfill run is needed.
- Fix: restart n8n service/container (production write — Ryan's go or James), verify executions resume, confirm VL backfills 20:00Z+.

## State

Blocker: scheduler restart (open decision #16). Then steps 1→2→2b→3→4 green; step 5 waits on ActorIpAddress enum. Spreadsheet v4 delivered.
