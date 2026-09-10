# Closeout — Anomalous Logins Wallboard realigned to SIM-ID detection rules (2026-08-14 ~18:35Z)

Dashboard `identity-anomalous-logins-draft` (Testing folder `cfbra19dmoyrka`), **v6 → v11**. Built live from Ryan's Home Desktop browser via the Grafana HTTP API. Companion to `claude/closeout-2026-08-12-detection-rules-live.md` and `claude/spec-2026-08-12-identity-detection-rules-v1.md` rev.8.

## Why it needed fixing

The board was built 2026-07-27 with hand-rolled heuristics on **pre-normalization field names**, and was never updated when the Identity Push/Pull v1.1 envelope and the 12 live SIM-ID rules landed. Four faults, all measured live:

1. **Breezeline flood.** 588 of 595 "Infra / VPN IP" hits in 24h were Breezeline flagged `hosting:true` by ip-api (480 Entra + 108 Duo). Spec §2 documents this and every shipped rule (3, 5, 6, 7, 11, 13) carries `NOT <axis>_isp:"Breezeline"`. The dashboard had no exclusion — the Investigation Queue was ~100% false positives.
2. **Old field names.** Panels queried `metadata.product.vendor_name:Microsoft`, `device.ip.*`, `_msg:"authentication"`, `auth_device.*`, `access_device.location.*`, `actor.user.email_addr`.
3. **"MFA Fraud Reports" dead by construction.** Queried `result:fraud`; Duo only ever emits `success` / `denied`. Permanently 0 — the same finding that withdrew Rule 4.
4. **`count()` not `count_uniq(event_uid)`** — violated the §2 counting discipline, so a Vector restart inflates every tile.

**Result: 595 rows/24h → 13.** ~20 real events/day across all rules.

## Final state (v11)

Layout unchanged — 26 grid rows, verified `scrollHeight - innerHeight === 0` (1080p kiosk safe). Refresh **1m → 5m** (matches High/Medium rule eval cadence).

**Tiles (24h)** — each maps to shipped rules:

| id | Tile | Rules | Now |
|---|---|---|---|
| 10 | Page-Tier Alerts | 001, 002, 008, 009, 011, 015 | 0 |
| 11 | Infra / VPN Logins | 006, 007 | 6 |
| 12 | MFA Anomalies | 003, 013 (approver axis) | 1 |
| 13 | Disabled-Acct Probes | 010 | 0 |
| 14 | Unmanaged Devices | 012 | 6 |
| 15 | Users Flagged | distinct users across the queue | 11 |

**Investigation Queue (panel 20)** — 13-branch union, one branch per shipped rule, rule-identical logic (Breezeline allowlist, NAT shared-egress guards, consumer-VPN match, `eq_field`). Threshold rules (001, 008, 009, 010) select **raw rows via `in()` subqueries** so every queue line keeps `_time`. Columns: Time / Severity / Signal / **Client** / User / Location / Detail / Source, sorted by `rank` then time.

**7d panels:** Signals by Day now stacks by **severity** (`groupingToMatrix` columnField `signal` → `sev`); Most-Flagged Users unchanged in shape.

## Technical notes (do not relearn)

1. **Query length is the binding constraint, not VL speed.** First build appended a 17-entry client `replace` chain to all 13 branches → ~22,000-char query. VL answered it in 45ms via the datasource proxy, but the **Grafana VL plugin hung** (`/api/ds/query` never returned; panels blank; renderer froze). Fix: extract the domain **once after the union** (`| extract if (user:*) "@<client>" from user`) and do the friendly-name mapping as a Grafana **value mapping** on the Client column. Query dropped to 7,869 chars; `/api/ds/query` returns in 43ms. Keep panel queries under ~8k.
2. **Region field is `client_geo_region` / `approver_geo_region`** (holds the full name, e.g. "Ohio", "Nevada"). **`client_geo_regionName` does not exist.** Rule 14 Query A in the spec uses `client_geo_regionName` in its composite key — **that rule is paused; fix before arming or the key silently degrades.** Approver axis *does* carry a clean `region` (the 08-12 closeout said it did not — superseded).
3. **`extract` + `replace` chains work after a `union`**, applied once to the merged stream. Wrapping a piped query in parens as a subquery (`(<union>) | stats ...`) returns nothing — append the pipe directly instead.
4. **POST /api/dashboards/db without `folderUid` moves the dashboard to General.** Always pass `folderUid`.
5. **Extension screenshots return stale frames on this Grafana.** Panels read blank while `document.body.innerText` and the scene data showed correct content. A 1-tick scroll forces a repaint and a true capture. Verify data via `/api/ds/query` or the scene walk (`$data.state.data.series`), not screenshots.
6. Severity value mappings extended with LOW (`#5794F2`) and INFO (`#8e8e8e`) alongside the existing CRITICAL/HIGH/MEDIUM.

## Client naming

Client column = email domain, rendered via Grafana value mappings (17 domains). This is a **separate map from the Inventory Wallboard's `replace ... at name` chain**, which keys on SentinelOne account names, not domains. Both must be updated when a client is added or renamed.

## Findings worth acting on

1. **iCloud Private Relay and Cloudflare WARP are firing SIM-ID-006/007 on the client axis.** Rule 13's consumer-VPN demotion list only applies to the **approver** axis. Two of six current Infra/VPN hits are Private Relay (phpd.us) and one is WARP (cc-efi.com). Recommend extending the demotion pattern to the client axis, or allowlisting these two providers in Rules 6/7.
2. **`koswald@simvay.com` from Las Vegas / Mobilitie (SWITCH), proxy-flagged, 4 hits.** Plausible conference travel — worth confirming out-of-band since it is Simvay staff.
3. **Verizon Business mobile rows geolocate to Chicago, Illinois for Brooklyn, OH users** — the documented carrier-gateway effect, visible on every SIM-ID-012 row. Analysts must read Location with the mobile flag in view; the queue does not yet carry `client_geo_mobile`. Candidate column for v2.
4. **SIM-ID-012 is dominated by one client** (brooklynohio.gov, 6 of 6) on Verizon Business hotspots — matches the spec's "one under-managed client fleet" note. This is the allowlist population to build before arming rule 012.

## Open / next

1. Extend consumer-VPN handling to the client axis (finding 1) — affects both the rules and this board.
2. Fix `client_geo_regionName` → `client_geo_region` in Rule 14 before arming it.
3. Apply Build Alert v2 (severity_id) — still the top n8n follow-up, unchanged from the 08-12 closeout.
4. Consider adding `client_geo_mobile` as a queue column or a Location suffix.
