# Closeout — SIM-ID rule fixes: dead `regionName` field + client-axis consumer VPN (2026-08-14 ~21:30Z)

Applied live to Grafana (10.10.99.11:3000, folder SOC/Identity `ffh405wysfls0a`, group "Identity Evaluation") via `/api/v1/provisioning/alert-rules` from Ryan's Home Desktop browser. Follows `claude/closeout-2026-08-14-identity-dashboard-realigned.md`, which surfaced both issues. Rule set is now **15 rules** (14 shipped + new SIM-ID-016).

## Fix 1 — `client_geo_regionName` does not exist (5 rules)

The envelope field is **`client_geo_region`** / **`approver_geo_region`** and it holds the full name ("Ohio", "Nevada"). `client_geo_regionName` was never emitted. Verified live: `mv client_geo_regionName regionBad, client_geo_region regionGood` returns rows carrying `regionGood` only — `mv` on an absent field drops it silently.

| Rule | Was | Impact of the bug |
|---|---|---|
| SIM-ID-002 | live | `region` label **empty on every alert** to S1 / PagerDuty |
| SIM-ID-006 | live | same |
| SIM-ID-007 | live | same |
| SIM-ID-011 | live | same |
| SIM-ID-014 | paused | `regionName` sat in the **composite dedup key** on both the current and 30-day baseline side, so first-seen silently degraded from (country, state) grain to (country) grain — duplicating Rule 9 instead of adding state sensitivity |

SIM-ID-005 was already correct (`client_geo_region`) — the 08-12 build caught it for the Action1 envelope only, which is why the error survived everywhere else.

**All five patched to `client_geo_region`.** Verified: zero `regionName` occurrences remain across all 15 rules; `region` now populates ("New Jersey", "Nevada", "Ohio").

## Fix 2 — consumer VPNs on the client axis (Rules 6/7/11 + new SIM-ID-016)

Rule 13 demotes known consumer privacy VPNs to Info, but **only on the approver axis**. The same providers hit the client axis, where Rules 6/7/11 paged them as High/Critical.

Measured client-axis infra population, **30 days**, Breezeline excluded — 19 events total:

| Org / ISP | Ev | Users | Disposition |
|---|---|---|---|
| iCloud Private Relay / Fastly + Akamai | 7 | 5 | → demoted to SIM-ID-016 (Info) |
| Mobilitie, LLC. / SWITCH (Las Vegas) | 5 | 1 | **keeps paging** — staff on untrusted venue Wi-Fi is what 6/7 are for (Ryan, 8/14) |
| Cloudflare WARP / Cloudflare | 2 | 2 | **keeps paging** — consistent with the 8/12 sign-off removing WARP for Cloudflare adjacency (Ryan reconfirmed 8/14) |
| CIE / Amazon | 2 | 1 | keeps paging — real hosting |
| LogicWeb Inc | 2 | 1 | keeps paging — real hosting |
| Cdnext BOS / Datacamp Limited | 1 | 1 | keeps paging — real hosting (Datacamp is NordVPN's underlying infra; brand names only, never the host) |

**`<CLIENT_VPN_MATCH>`** — client-axis twin of Rule 13's expression, same trimmed provider set, added as `NOT <CLIENT_VPN_MATCH>` to Rules 6, 7 and 11, and as the positive condition in Rule 16:

```
(client_geo_org:~"(?i)(icloud private relay|nordvpn|tefincom|expressvpn|surfshark|protonvpn|proton ag|private internet access)"
 OR client_geo_isp:~"(?i)(nordvpn|tefincom|expressvpn|surfshark|proton ag|private internet access)")
```

iCloud Private Relay is matched on **org only** — its ISP reads `Fastly, Inc.` and `Akamai Technologies, Inc.` in our live data, so an ISP match would whitelist both CDNs wholesale. This is the same caveat the Rule 13 table carries, now confirmed against production values.

### New rule — SIM-ID-016: Consumer Privacy VPN on Access Device

**Severity:** Info (log-only into S1, no PagerDuty) | **uid:** `cfv6zduvy9r7kb` | **Window:** 30m, eval every 5m

Client-axis twin of Rule 13, covering **both** the Entra and Duo client axes so every client-axis proxy/hosting event lands in exactly one of {6, 7, 11, 16}.

```
(record_type:entra_login_success OR (record_type:duo_auth auth_result:success))
(client_geo_hosting:true OR client_geo_proxy:true)
NOT client_geo_isp:("Breezeline" OR "Microsoft Corporation" OR "Microsoft Limited")
<CLIENT_VPN_MATCH> _time:30m
| mv <envelope → hook labels, incl. client_geo_region region>
| stats by (email, ip, isp, org, ismobile, isproxy, ishosting, country, city, region, event, tenant) count() total
```

Cloned from Rule 13 so labels, annotations, `noDataState=OK`, `execErrState=KeepLast` and the "N8N - Identity" notification settings match the rest of the group.

**Maintenance rule: 3, 13, 16 and the exclusions in 6/7/11 are now one matched set.** Editing the provider list means editing all six queries in the same change — approver axis (3/13) and client axis (6/7/11/16). Drift creates events that fire twice or not at all.

## Verification

- All 15 rules: `health=ok`, no `lastError`, evaluating on schedule. SIM-ID-016 first evaluation 17:22:50Z, clean.
- Residual after the change (30d): Rule 6 → CIE, LogicWeb, Cdnext (5 ev). Rule 7 → Mobilitie, WARP ×2 (7 ev). Rule 11 → 2 ev. Rule 16 → 8 ev. Nothing dropped; the split is exhaustive.
- Full pre-change export of the rule group was taken before any write (`/api/v1/provisioning/folder/ffh405wysfls0a/rule-groups/Identity%20Evaluation/export?format=json`, ~50 KB). Original query text for all five edited rules is reproduced in this document's git history via the dashboard closeout; re-export before the next bulk edit.

## Dashboard sync (v11 → v13)

The wallboard was updated in the same pass so it does not drift from the rules again:

1. `NOT <CLIENT_VPN_MATCH>` added to the 006 / 007 / 011 queue branches and to the "Infra / VPN Logins" tile.
2. New **SIM-ID-016** queue branch (INFO, rank 5).
3. **Bug found and fixed during verification:** the dashboard's 007 branch lacked `NOT client_geo_hosting:true`, which the live rule has — so events flagged *both* proxy and hosting appeared twice in the queue (once as 006, once as 007). Corrected in v13.

7-day reconciliation after the change — board matches rules exactly:

| Signal | 7d |
|---|---|
| SIM-ID-012 Generic-hostname unmanaged | 39 |
| SIM-ID-016 Consumer VPN access device | 8 |
| SIM-ID-007 Anonymizing proxy | 7 |
| SIM-ID-006 Hosting / VPS | 5 |
| SIM-ID-003 MFA approval from datacenter IP | 5 |
| SIM-ID-011 MFA from infra access device | 2 |

Panel-20 query is now 9,358 chars and returns in ~41 ms through `/api/ds/query` — comfortably under the threshold where the VL plugin hangs (22 k failed, 9.4 k fine).

## Still open

1. **Build Alert v2 (severity_id)** — unchanged top n8n follow-up from the 08-12 closeout. High/Critical still land in S1 as Low; the `[SIM-ID-XXX | Sev]` title prefix is the mitigation.
2. **Rules 12 and 14 remain paused.** 14's key is now correct, but it still needs the 30-day baseline to settle and Query B (mobile, country grain) is not built — the live rule has a single query. 12 needs the BYOD allowlist; the 7d population is 39 events dominated by one client (brooklynohio.gov on Verizon Business hotspots).
3. **`count()` vs `count_uniq(event_uid)`.** Spec §2 mandates `count_uniq`; the built rules use `count()` in the final `stats` on 003, 005, 006, 007, 011, 012, 013, 014, 015 (001, 002, 008, 009, 010 use `count_uniq`). Harmless for `>0` threshold rules, but the `total` label is inflatable by a Vector restart. Worth normalising in one pass.
4. **Queue/tile titles say "Last 24h" but follow the dashboard time picker** — accurate at the now-24h default, misleading if someone widens the range. Pin with `timeFrom: 24h` if that matters.
5. `client_geo_mobile` is still not surfaced on the wallboard; every SIM-ID-012 row reads "Chicago, Illinois" for Brooklyn OH users via Verizon gateway geo.
