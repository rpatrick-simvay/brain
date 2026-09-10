# Simvay Identity Detection Rules — v1 Proposal for Sign-off

**For:** Ryan (sign-off per rule)
**Date:** 2026-08-12
**Data source:** VictoriaLogs, normalized identity envelope (Identity Push/Pull v1.1, live since 2026-08-12)
**Alert path:** Grafana → Alerting → Alert Rules → n8n (Identity Alert Hook) → PagerDuty
**Status:** APPROVED WITH MODIFICATIONS (Ryan, 8/12) — severities adjusted per review; Rule 4 withdrawn (S1 library coverage); Rule 15 added pending approval; queries in live validation before build. All existing alert rules are treated as EOL per Ryan's direction and are not referenced here.

> **⚠ AMENDED 2026-08-14 — read §7 before using any query in this document.** Two post-sign-off corrections are applied inline below and logged in §7: (a) `client_geo_regionName` **does not exist** — the field is `client_geo_region`; (b) consumer-VPN demotion now covers the **client axis** as well, via new Rule 16. Rules 2, 6, 7, 11, 14 were edited live. Full detail: `claude/closeout-2026-08-14-rule-fixes-regionname-and-client-axis-vpn.md`.

---

## 1. Sign-off summary

| # | Rule ID | Alert name | Severity | Est. volume | FP risk | Status |
|---|---|---|---|---|---|---|
| 1 | SIM-ID-001 | Password Spray — Single Source vs Multiple Accounts | High | ~0–2/day | Very low | Approved (sev. adjusted) |
| 2 | SIM-ID-002 | Spray-to-Success — Login from Known Attack Source | Critical | rare | Very low | Approved |
| 3 | SIM-ID-003 | MFA Approval from Datacenter / Anonymized IP | Medium | rare | Low | Approved (sev. adjusted) |
| 4 | SIM-ID-004 | Duo Push Marked Fraudulent by User | — | — | — | **Withdrawn** — S1 library unified alert |
| 5 | SIM-ID-005 | RMM Console (Action1) Login Anomaly | Medium | rare | Low | Approved (sev. adjusted; routes to NFR) |
| 6 | SIM-ID-006 | Interactive Login from Hosting / VPS Infrastructure | High | baseline first | Medium until tuned | Approved — **amended 8/14 (§7)** |
| 7 | SIM-ID-007 | Interactive Login via Anonymizing Proxy | High | baseline first | Medium until tuned | Approved — **amended 8/14 (§7)** |
| 8 | SIM-ID-008 | MFA Fatigue — Repeated Duo Denials | High | ~0–1/day | Low | Approved |
| 9 | SIM-ID-009 | Multi-Country Sign-ins — Single User | High | ~0–2/day | Medium | Approved |
| 10 | SIM-ID-010 | Credential Attempts Against Disabled Accounts | Low | ~0–1/day | Very low | Approved (sev. adjusted) |
| 11 | SIM-ID-011 | MFA Transaction from Hosting / Proxy Access Device | Critical | rare | Low | Approved — **amended 8/14 (§7)** |
| 12 | SIM-ID-012 | Login from Generic-Hostname Unmanaged Device | Medium | baseline first | Medium until tuned | Approved — paused, awaiting BYOD allowlist |
| 13 | SIM-ID-013 | MFA Approval via Known Consumer Privacy VPN | Info | baseline first | n/a (log-only) | Approved (list trimmed) |
| 14 | SIM-ID-014 | First-Seen Sign-in Location for User (30-Day Baseline) | Medium | baseline first | Medium until tuned | Approved — paused; **key fixed 8/14 (§7)** |
| 15 | SIM-ID-015 | Access-Device vs Auth-Device Country Mismatch (Duo) | High | baseline first | Low | Approved |
| 16 | SIM-ID-016 | Consumer Privacy VPN on Access Device | Info | ~8/30d | n/a (log-only) | **Added 8/14 (Ryan) — client-axis twin of Rule 13** |

Severity uses the **SentinelOne priority scale** — `Critical` / `High` / `Medium` / `Low` / `Info` — carried verbatim as the Grafana label `severity` so alerts ingest into S1 with native priorities (no remapping in the n8n hook). Downstream PagerDuty mapping: `Critical` → P1 page, `High` → P2 page, `Medium` → P3 ticket, `Low`/`Info` → log only, no incident. `Low` is used by Rule 10, `Info` by Rules 13 and 16.

Implementation order (post-approval): 2 and 11 (Critical page tier), then 1 and 8 (High, no baseline needed), then 3+13 (matched pair, list trimmed), 5, 10; baseline-gated rules 6, 7, 9, 12, 14, 15 after the 7-day baseline run (§4). Rule 4 does not ship.

---

## 2. Conventions used in every rule

**Field names** are the normalized envelope emitted by Identity Push/Pull v1.1: `record_type`, `event_uid`, `user_email`, `user_uid`, `client_ip`, `client_geo_*` (full ip-api block: country, city, isp, org, as, lat/lon numeric, proxy/hosting/mobile booleans), `approver_geo_*` (Duo phone axis), `error_code`, `result_detail`, `auth_result`, `application`, `tenant_uid`, plus preserved nested source fields (`reason`, `factor`, etc. on Duo).

> **Field-name correction (8/14, verified live).** The state/province field is **`client_geo_region`** / **`approver_geo_region`** and it carries the full name ("Ohio", "Nevada"). There is **no `client_geo_regionName`** — earlier drafts of Rules 2, 6, 7, 11 and 14 used it. `mv` on an absent field drops it silently, so the bug is invisible at query time: rules still fire, they just emit an empty `region` label (and, in Rule 14, silently degrade the composite key). Both axes carry `region`. See §7.

**Counting discipline:** all counts use `count_uniq(event_uid)`, never `count()`. Vector's dedupe cache is in-memory; a restart admits a bounded window of byte-identical duplicate rows. `count_uniq` makes every rule immune to that (per spec-2026-08-11 §2.5). *Build note (8/14): the as-built rules use `count()` in the final `stats` on 3, 5, 6, 7, 11, 12, 13, 14, 15 — harmless for `>0` threshold conditions but the `total` label is inflatable. Normalisation is an open item.*

**Known data nuance (from the v1.1 closeout):** MFA-interrupt failures (AADSTS 50074/50076) carry `ResultStatus=Succeeded` upstream, so `auth_result` can read `success` on `entra_login_failed` rows. Every rule below filters on `record_type` + `error_code`, never on `auth_result` alone, for exactly this reason.

**Geo semantics:** absent `client_geo_*` / `approver_geo_*` = non-routable IP (RFC1918/0.0.0.0) = on-prem or invisible-to-vendor. It is a signal, not missing data. No rule treats absent geo as a match.

**Mobile & IPv6 geo skepticism (Ryan, 8/12):** carrier CGNAT and IPv6 egress geolocate to regional gateway metros, not the subscriber — Verizon in NE Ohio routinely reads as Chicago, IL. Consequences applied throughout: city/state on `client_geo_mobile:true` records are treated as unreliable in every rule; geo-novelty logic drops mobile rows to country grain (Rule 14 runs a separate mobile query at country level); country-grain rules (9) are inherently robust to gateway jitter since the gateway stays in-country; and hosting/proxy rules (6/7/11/13) never blanket-exclude mobile — mobile-proxy networks are a commercial attacker product, so carrier-CGNAT proxy misflags are handled by carrier-ISP allowlists from the V1 baseline instead. IPv6 rows get the same treatment: state/city are hints, country + ISP/ASN are the workable signals. Analysts should read every geo label with the `client_geo_mobile` flag and IP version in view (`client_ip` is carried on every rule for exactly this).

**Regional-ISP infra-flag allowlist (from live testing, 8/12):** ip-api flags large parts of **Breezeline** (the dominant client-side regional cable ISP) as `hosting:true`/`proxy:true`. Measured over 7d: 1,127 of 1,128 Rule 6 hits, 148 of 150 Rule 3 hits, 80 of 81 Rule 11 hits, and all 3 Rule 5 hits were Breezeline. Every hosting/proxy rule (3, 5, 6, 7, 11, 13) therefore carries `NOT <ISP>_isp:"Breezeline"` (client axis or approver axis as appropriate) as the first entry of a per-tenant regional-ISP allowlist — maintained from the V1 baseline, exactly as the mobile-skepticism convention prescribes (allowlist the carrier, never blanket-exclude the flag). Residual 7d signal after the exclusion: single approvals via zenlayer and GTHost (real datacenter hosts) and single logins via Fastly and Cloudflare — precisely the population these rules exist to surface.

**Consumer-VPN matched set (as of 8/14):** the demotion list is now referenced by **six** queries across two axes — Rules 3 and 13 (approver axis, `<CONSUMER_VPN_MATCH>`) and Rules 6, 7, 11 and 16 (client axis, `<CLIENT_VPN_MATCH>`). The two expressions are the same provider list on different field prefixes. **Edit all six in one change.** Drift creates events that fire twice or not at all.

**Grafana rule settings (all rules unless stated):** instant LogsQL query against the VictoriaLogs datasource; condition `last() > 0` (thresholds live inside the query via `filter` pipes, so any returned row is already actionable); evaluate every 1m for Critical, every 5m for High/Medium; pending period 0 for Critical, 5m otherwise; **No data → OK**; **Query error → Alerting** (a broken query must page us, not silently disarm). *As-built (8/12): `execErrState=KeepLast` was used instead, matching the working legacy rules, to avoid paging on transient VL errors.* Each `stats by (...)` group becomes its own alert instance, so `tenant_uid` in the group-by gives per-client PagerDuty routing labels for free.

---

## 3. The rules

### Rule 1 — SIM-ID-001: Password Spray — Single Source vs Multiple Accounts

**Severity:** High (adjusted from Critical per sign-off) | **MITRE:** T1110.003 (Password Spraying)
**Window:** 30m, evaluated every 1m (kept at fast cadence — spray moves quickly even at High)

One source IP generating failed logins across many distinct accounts is the defining spray shape. Measured baseline (7/31): ~81 `InvalidUserNameOrPassword` (50126) and ~83 `IdsLocked` (50053) events/day, concentrated in a handful of source IPs (top source 61 events). Requiring ≥5 distinct target accounts from one IP in 30 minutes is a shape no legitimate user produces.

```
record_type:entra_login_failed error_code:(50126 OR 50053) _time:30m
NOT client_ip:in(
    record_type:entra_login_success _time:30d
    | stats by (client_ip) count_uniq(user_email) u
    | filter u:>=10
    | fields client_ip
  )
| stats by (client_ip, client_geo_country, client_geo_isp, tenant_uid)
    count_uniq(user_email) accounts,
    count_uniq(event_uid) attempts
| filter accounts:>=5
```

**Revised after live testing (8/12):** the shared-egress guard (exclude IPs with ≥10 distinct successful users over 30d) was added because the only two IPs that fired in 7 days of replayed 30m windows were client office NATs (Hinkley/Breezeline, Polaris/Zayo — 87 successful users each). With the guard, a busy office morning cannot fire; a fresh attacker IP still does. Known trade: a spray launched from inside a client network is not caught here — the 50053 lockout volume it generates still surfaces on dashboards.

**Why low FP:** a shared NAT egress (client office) can produce multiple users failing, but 5 distinct accounts failing with wrong-password/lockout codes inside 30m from one IP is spray or a broken integration — both worth a page. 50074/50076 MFA interrupts are excluded by the error_code filter, so normal MFA friction never counts.
**Tuning knobs:** `accounts` threshold (start 5), window, add per-client office-egress allowlist only if a real FP occurs.
**Analyst action on fire:** block source IP at the tenant CA policy / named locations, check Rule 2 for any success from the same IP.

---

### Rule 2 — SIM-ID-002: Spray-to-Success — Login from Known Attack Source

**Severity:** Critical | **MITRE:** T1110 → T1078 (Valid Accounts)
**Window:** success in last 1h, source qualified over prior 24h

The highest-value alert in this set: a successful login from an IP that has been failing against multiple accounts in the last 24 hours. This is the moment a spray works.

```
record_type:entra_login_success _time:1h
client_ip:in(
    record_type:entra_login_failed error_code:(50126 OR 50053) _time:24h
    | stats by (client_ip) count_uniq(user_email) sprayed
    | filter sprayed:>=3
    | fields client_ip
)
NOT client_ip:in(
    record_type:entra_login_success _time:30d
    | stats by (client_ip) count_uniq(user_email) u
    | filter u:>=10
    | fields client_ip
)
| stats by (user_email, client_ip, client_geo_country, client_geo_isp, tenant_uid)
    count_uniq(event_uid) hits
```

**Revised after live testing (8/12):** without the second subquery, client office NATs qualified as "spray sources" (many users fail *and* succeed behind one egress) and the rule returned dozens of false hits. The shared-egress guard (same as Rule 1) zeroed them; the double-`in()` construct is verified working on our VL.

**Amended 8/14:** the as-built `mv` pipe carried `client_geo_regionName region`; corrected to `client_geo_region region`. Detection logic unchanged — this only affected the `region` label on the emitted alert. Deliberately **no** consumer-VPN exclusion: spray-to-success must never be suppressed by provider.

**Why low FP:** the qualifying set (IPs that failed against ≥3 distinct accounts) excludes the classic self-FP of one user fat-fingering their own password and then succeeding. An IP in that set that then succeeds against anyone is compromise-until-proven-otherwise.
**Dependency:** relies on the LogsQL `in(<subquery>)` construct — validate on our VL version before enabling (§4, check V2).
**Analyst action on fire:** treat as active account compromise — revoke sessions, reset credential, review the account's activity from that IP.

---

### Rule 3 — SIM-ID-003: MFA Approval from Datacenter / Anonymized IP

**Severity:** Medium (adjusted from Critical per sign-off) | **MITRE:** T1621 (MFA Request Generation) / T1557 (AiTM)
**Window:** 15m, evaluated every 1m

A Duo approval where the *approving device* (the phone — `approver_geo_*` axis) sits on hosting or proxy infrastructure. Phones live on cellular and residential networks; an approval originating from a VPS or anonymizer is the signature of an attacker-controlled enrollment or an AiTM relay. This axis only exists because of James's dual-axis enrichment — flexing exactly the capability we just built.

```
record_type:duo_auth auth_result:success
(approver_geo_proxy:true OR approver_geo_hosting:true)
NOT <CONSUMER_VPN_MATCH> _time:15m
| stats by (user_email, approver_geo_isp, approver_geo_country, application, tenant_uid)
    count_uniq(event_uid) approvals
```

`<CONSUMER_VPN_MATCH>` is the shared consumer-VPN match expression defined in Rule 13. **Rules 3 and 13 are a matched pair:** every approver-axis proxy/hosting event lands in exactly one of them. Edit the match list in both queries in the same change, always — drift between the two creates events that fire twice or not at all. *(Since 8/14 the same discipline extends to the client axis — Rules 6, 7, 11, 16. Six queries, one list.)*

**Why low FP:** with known consumer privacy VPNs carved out to Rule 13 (revision on Ryan's review, 8/12 — staff run these on personal phones), the remaining population is tiny — only routable approver IPs carry geo (~9–16% of duo_auth), and of those, hosting/proxy-flagged ones should be near zero. Residual FPs are unrecognized consumer VPN brands — those are list additions to Rule 13, not per-user allowlists.
**Analyst action on fire:** verify the user's enrolled devices in Duo admin; an unrecognized device = immediate credential + MFA reset.

---

### Rule 4 — SIM-ID-004: Duo Push Marked Fraudulent by User

**Status: WITHDRAWN (sign-off, 8/12)** — the SentinelOne alert library ships a unified alert for fraudulent push notifications; duplicating it in Grafana would double-page the same event. **Follow-up before relying on it:** confirm the library rule is enabled on every tenant with Duo telemetry and that its S1 alert routes to PagerDuty. Original design retained below for the record.

**Severity:** (was Critical) | **MITRE:** T1621
**Window:** 15m, evaluated every 1m

The user pressed "I did not request this — mark as fraud." Zero-FP by definition: the end user has already triaged it for us. Today this signal dies in the Duo admin panel.

```
record_type:duo_auth (auth_result:fraud OR reason:user_marked_fraud) _time:15m
| stats by (user_email, application, client_ip, client_geo_country, tenant_uid)
    count_uniq(event_uid) reports
```

**Why low FP:** it is a human report, not a heuristic. Worst case is a user mis-tap, and even that deserves a call.
**Validation note:** confirm the exact `result`/`reason` values as they land in VL (nested Duo fields are preserved alongside the envelope; §4 check V3).
**Analyst action on fire:** the password is compromised (something triggered the push) — reset credentials, hunt the pushing source IP in `entra_login_*`.

---

### Rule 5 — SIM-ID-005: RMM Console (Action1) Login Anomaly

**Severity:** Medium (adjusted from Critical per sign-off) | **MITRE:** T1078.004, TA0008 via RMM
**Window:** 30m, evaluated every 1m

Action1 is the blast-radius account: console access means endpoint control across client fleets. Volume is ~31 logins/day total, so we can afford an aggressive rule. Fires on any console login from hosting/proxy infrastructure or from outside the US.

```
record_type:action1_login _time:30m
(client_geo_hosting:true OR client_geo_proxy:true OR NOT client_geo_country:"United States")
| stats by (user_email, client_ip, client_geo_country, client_geo_isp, tenant_uid)
    count_uniq(event_uid) logins
```

**Why low FP:** the whole population is ~31 events/day from a known, small set of Simvay technicians on US networks. Any technician travel or sanctioned VPN can be allowlisted by `user_email` + country in minutes.
**Extension (recommended, same rule family later):** a failed-login burst variant on `status_message` once we confirm its failure values (§4 check V4).
**Routing (answering the sign-off question):** Action1 console logins are Simvay-internal infrastructure auth — the users are Simvay technicians, and `org_id`/`org_name` on each record only says which Action1 org was in view. Fanning these to client S1 tenants would put Simvay staff telemetry in client consoles. **Recommendation: all SIM-ID-005 alerts route to the NFR/internal Simvay tenant**, with `org_name` carried as a label for context — one static mapping in the n8n hook (`record_type:action1_login` → NFR), no per-client routing.
**Analyst action on fire:** confirm with the named tech out-of-band; if unrecognized, disable the Action1 account before anything else.

*Note: this is the only rule that used `client_geo_region` correctly from the start (caught during the 8/12 build for the Action1 envelope) — which is why the `regionName` error survived undetected everywhere else until 8/14.*

---

### Rule 6 — SIM-ID-006: Interactive Login from Hosting / VPS Infrastructure

**Severity:** High | **MITRE:** T1078.004
**Window:** 30m, evaluated every 5m

Successful Entra login where the client IP is flagged `hosting:true` — datacenter address space (AWS, DO, Vultr, M247…). End users do not browse from VPSes; attackers and commercial VPN egress nodes do.

```
record_type:entra_login_success client_geo_hosting:true
NOT client_geo_isp:"Breezeline"
NOT <CLIENT_VPN_MATCH> _time:30m
| stats by (user_email, client_ip, client_geo_isp, client_geo_org, client_geo_country, tenant_uid)
    count_uniq(event_uid) logins
```

**Amended 8/14:** `NOT <CLIENT_VPN_MATCH>` added (Rule 16 definition) and `regionName` → `region` in the `mv` pipe. Before the change, iCloud Private Relay accounted for 7 of the 19 client-axis infra events over 30 days and paged as High.

**FP profile — honest assessment:** corporate VPNs and some SD-WAN egress will trip this. That is why it ships **after a 7-day baseline query** (§4 check V1) that tells us exactly which ISPs/orgs are legitimate per tenant; those become a `NOT client_geo_isp:in(...)` allowlist in the query. Post-tuning this is a high-confidence rule.
**Residual after the 8/14 amendment (30d):** CIE/Amazon (2), LogicWeb (2), Cdnext BOS/Datacamp (1) — all real hosting, exactly the intended population.
**Analyst action on fire:** check whether the user also has a normal-geo login nearby (token theft pattern), verify device_managed/compliant on the session.

---

### Rule 7 — SIM-ID-007: Interactive Login via Anonymizing Proxy

**Severity:** High | **MITRE:** T1090 / T1078.004
**Window:** 30m, evaluated every 5m

Same shape as Rule 6 on the `proxy:true` flag — Tor exits, commercial anonymizers, residential proxy networks. Kept separate from Rule 6 because the infrastructure class, the allowlist, and the analyst response differ (residential proxies are the current AiTM norm and deserve harder scrutiny than a VPS).

```
record_type:entra_login_success client_geo_proxy:true
NOT client_geo_hosting:true
NOT client_geo_isp:"Breezeline"
NOT <CLIENT_VPN_MATCH> _time:30m
| stats by (user_email, client_ip, client_geo_isp, client_geo_org, client_geo_country, tenant_uid)
    count_uniq(event_uid) logins
```

**`NOT client_geo_hosting:true` matters.** ip-api sets both flags on some IPs; without this clause the same event fires Rules 6 and 7 simultaneously. (The 7/27-lineage wallboard omitted it and double-counted until 8/14.)

**Amended 8/14:** `NOT <CLIENT_VPN_MATCH>` added; `regionName` → `region`.

**FP profile:** employee privacy VPNs, plus carrier CGNAT ranges that ip-api misflags as proxy (mobile users). Same treatment: 7-day baseline → per-tenant ISP allowlist (carrier ISPs included) → enable. Do NOT blanket-exclude `client_geo_mobile:true` — mobile-proxy networks are a commercial attacker product and that would be the evasion path. Where a client has a written no-VPN policy, no allowlist and every fire is actionable.
**Residual after the 8/14 amendment (30d):** Mobilitie/SWITCH (5 — Simvay staff on Las Vegas venue Wi-Fi; **left alerting by decision, 8/14**) and Cloudflare WARP (2 — **deliberately not demoted**, see Rule 13 sign-off note).
**Analyst action on fire:** as Rule 6, plus correlate with any `duo_auth` for the same user in the window — proxy login + MFA approval from a different-axis anomaly (Rule 3) is a compound critical.

---

### Rule 8 — SIM-ID-008: MFA Fatigue — Repeated Duo Denials

**Severity:** High | **MITRE:** T1621
**Window:** 20m, evaluated every 5m

Five or more denied Duo attempts against one user in 20 minutes — the push-bombing pattern that precedes an exhausted-user approval. The compromised password is a given at this point; the alert exists so we act *before* the user gives in.

```
record_type:duo_auth auth_result:failure _time:20m
| stats by (user_email, tenant_uid)
    count_uniq(event_uid) denies,
    count_uniq(client_ip) src_ips
| filter denies:>=5
```

**Corrected after live testing (8/12):** Duo `auth_result` values in VL are `success`/`failure` — the drafted `denied` matched **zero rows** and would have been a silently dead rule. Live failure reasons: `no_response` (42/7d — the fatigue signal), `user_cancelled`, `no_user_allowed`, `invalid_passcode`. Replayed in 20m windows over 7 days: zero firing windows; max per-user failures 6/7d — the ≥5-in-20m threshold is comfortably above normal friction.

**Why low FP:** legitimate users produce 1–2 denials (mis-tap, wrong phone in hand), not five in twenty minutes. `src_ips` is carried as a label for instant triage context, not as a condition.
**Tuning knobs:** threshold (start 5), optionally exclude `reason:locked_out` repeats once VL values are confirmed (§4 check V3).
**Analyst action on fire:** call the user, reset the password *first* (it is burned), then review whether any push was approved.

---

### Rule 9 — SIM-ID-009: Multi-Country Sign-ins — Single User

**Severity:** High | **MITRE:** T1078
**Window:** 1h, evaluated every 5m

Successful sign-ins for one user from two or more countries inside an hour. This is the v1 approximation of impossible travel; proxy/hosting IPs are excluded so it doesn't double-fire on Rules 6/7 territory.

```
(record_type:entra_login_success OR record_type:entra_signin)
client_geo_country:* NOT client_geo_proxy:true NOT client_geo_hosting:true _time:1h
| stats by (user_email, tenant_uid)
    count_uniq(client_geo_country) countries,
    count_uniq(event_uid) logins
| filter countries:>=2
```

**FP profile:** cellular roaming near borders and users mid-flight. Ohio-based client geography makes both rare, but not zero — hence High, not Critical. Carrier-gateway geo jitter (the Verizon→Chicago effect) is intra-country, so this rule's country grain is inherently robust to it; mobile rows are deliberately kept in.
**Upgrade path (v2, explicitly deferred):** true haversine velocity on the numeric `client_geo_lat`/`lon` James now emits — either via LogsQL `math` pipes or a small n8n post-processing rule. Worth doing once v1 proves the signal; not a blocker for shipping this.
**Analyst action on fire:** compare the two sessions' device/browser/ISP; token theft shows the same session UID from the new geo.

---

### Rule 10 — SIM-ID-010: Credential Attempts Against Disabled Accounts

**Severity:** Low (adjusted from Medium per sign-off — log-only into S1, no PagerDuty) | **MITRE:** T1110.004 (Credential Stuffing)
**Window:** 1h, evaluated every 5m

AADSTS 50057 — authentication attempts against disabled accounts. Measured baseline: ~25/day. Nobody legitimate retries a disabled account three times in an hour; clustered attempts mean stuffing with stale breach creds, or probing of leaver accounts (a favorite for re-enable-and-ride persistence).

```
record_type:entra_login_failed error_code:50057 _time:1h
| stats by (client_ip, client_geo_country, client_geo_isp, tenant_uid)
    count_uniq(user_email) accounts,
    count_uniq(event_uid) attempts
| filter attempts:>=3
```

**Why low FP:** the ≥3 clustering threshold removes the one-off (a former employee's phone still trying its cached password). What remains is deliberate.
**Why Low:** the accounts are disabled — the attempt failed by design. The value is pure intelligence: source IPs feeding this rule are attack infrastructure, in S1 for hunt and correlation against Rules 1/2 history.
**Analyst action:** none live — reviewed in hunt/correlation context; sources feed the watch/block list.

---

### Rule 11 — SIM-ID-011: MFA Transaction from Hosting / Proxy Access Device

**Severity:** Critical | **MITRE:** T1557 (AiTM) / T1621
**Window:** 15m, evaluated every 1m

Added on Ryan's review (8/12). The complement to Rule 3, on the other Duo axis: a completed MFA transaction where the *access device* — the "workstation" Duo sees initiating the auth (`client_geo_*` on duo_auth) — sits on hosting or proxy infrastructure. In an AiTM/evilginx flow, the device Duo observes is the attacker's relay VPS, not the victim's machine. This is the Duo-visible signature of session-token BEC, and it fires even when the Entra-side record is missing or coalesces to a service IP. Rules 6/7 cover the Entra client axis; this covers the Duo one.

```
record_type:duo_auth auth_result:success
(client_geo_hosting:true OR client_geo_proxy:true)
NOT client_geo_isp:("Breezeline" OR "Microsoft Corporation" OR "Microsoft Limited")
NOT <CLIENT_VPN_MATCH> _time:15m
| stats by (user_email, client_ip, client_geo_isp, client_geo_country, application, tenant_uid)
    count_uniq(event_uid) auths
```

**Amended 8/14:** `NOT <CLIENT_VPN_MATCH>` added; `regionName` → `region`. Residual 30d after the change: 2 events (LogicWeb, CIE).

**Why low FP:** the Microsoft-ISP exclusion (per Ryan's note) removes service-IP noise; corporate VPN egress is the remaining FP class and shares the Rule 6/7 per-tenant ISP allowlist once V1 baselines it. Only routable access-device IPs carry geo (RFC1918/on-prem is absent = no match), so the matched population is small and hostile-leaning.
**Tuning knobs:** shared ISP/org allowlist with Rules 6/7; optionally widen to denied attempts (relay recon) after the success-only version proves quiet.
**Analyst action on fire:** treat as AiTM until disproven — revoke the user's sessions/refresh tokens (password reset alone does not evict a stolen session), then compare against the same user's Entra records in the window.

---

### Rule 12 — SIM-ID-012: Login from Generic-Hostname Unmanaged Device

**Severity:** Medium (escalation path to High) | **MITRE:** T1078.004; BEC precursor
**Window:** 1h, evaluated every 5m

Added on Ryan's review (8/12). Successful Entra login from an unmanaged device whose hostname is a Windows factory default — `DESKTOP-XXXXXXX` (Win10/11), `WIN-XXXXXXXXXXX` (server/eval builds), occasionally `LAPTOP-XXXXXXX`. Attack boxes are habitually fresh VMs nobody renames. The value is exactly where Rules 6/7 go blind: an attacker on a *residential* proxy defeats the hosting/proxy flags, but their throwaway VM still announces itself in the hostname.

```
record_type:entra_login_success device_managed:false
device_hostname:~"^(DESKTOP|LAPTOP)-[A-Z0-9]{7}$|^WIN-[A-Z0-9]{11}$" _time:1h
| stats by (user_email, device_hostname, client_ip, client_geo_country, client_geo_isp, tenant_uid)
    count_uniq(event_uid) logins
```

**FP profile — honest assessment:** real BYOD machines also keep factory hostnames, which is why this ships as Medium after the same 7-day baseline as Rules 6/7 (V1). Expect the baseline to surface a known-BYOD population per tenant; recurring user+hostname pairs get allowlisted (or handled later as a first-seen condition), and what remains — a *new* generic-hostname unmanaged device for a user — is a strong compound signal. Escalate to High when it co-occurs with hosting/proxy/foreign-geo labels.
**Status (8/14): still PAUSED.** Current 7d population is 39 events, dominated by brooklynohio.gov on Verizon Business hotspots — that is the allowlist to build before arming.
**Validation dependency:** `device_hostname` envelope coverage and casing on the success stream needs confirming (new check V7) — it derives from `unmapped.DeviceProperties` DisplayName (~97% coverage upstream).
**Analyst action on fire:** check whether the device also appears for other users (shared attack box), review the session's ISP/geo labels, and verify with the user before escalating.

---

### Rule 13 — SIM-ID-013: MFA Approval via Known Consumer Privacy VPN

**Severity:** Info (log-only into S1, no PagerDuty incident) | **MITRE:** context for T1621/T1557
**Window:** 15m, evaluated every 5m

Added on Ryan's review (8/12). The demotion half of the Rule 3 pair: same base condition — a successful Duo approval from a proxy/hosting-flagged phone IP — but where the provider matches a curated list of consumer privacy VPNs that staff run on personal phones (iCloud Private Relay, NordVPN-class apps). These are real proxy flags but expected user behavior, so they land in S1 as Info for correlation and baselining instead of paging as a Critical anonymizer hit.

```
record_type:duo_auth auth_result:success
(approver_geo_proxy:true OR approver_geo_hosting:true)
NOT approver_geo_isp:"Breezeline"
<CONSUMER_VPN_MATCH> _time:15m
| stats by (user_email, approver_geo_isp, approver_geo_org, approver_geo_country, tenant_uid)
    count_uniq(event_uid) approvals
```

Where `<CONSUMER_VPN_MATCH>` is (single source of truth, pasted into both Rule 3 and Rule 13):

```
(approver_geo_org:~"(?i)(icloud private relay|nordvpn|tefincom|expressvpn|surfshark|protonvpn|proton ag|private internet access)"
 OR approver_geo_isp:~"(?i)(nordvpn|tefincom|expressvpn|surfshark|proton ag|private internet access)")
```

and `<CLIENT_VPN_MATCH>` is the identical list on the client axis (used by Rules 6, 7, 11, 16):

```
(client_geo_org:~"(?i)(icloud private relay|nordvpn|tefincom|expressvpn|surfshark|protonvpn|proton ag|private internet access)"
 OR client_geo_isp:~"(?i)(nordvpn|tefincom|expressvpn|surfshark|proton ag|private internet access)")
```

**List trimmed per sign-off (8/12):** WARP removed (too risky — Cloudflare adjacency), Mullvad removed (attacker-favored), and everything below PIA removed (IPVanish, Windscribe, TunnelBear, Pango family, Avast). Final demotion set: **iCloud Private Relay, NordVPN, ExpressVPN, Surfshark, Proton VPN, Private Internet Access.** Removed providers fire as Rule 3 (Medium) on the approver axis and Rules 6/7/11 (High/Critical) on the client axis. **Reconfirmed 8/14:** WARP stays out of the list on both axes; it currently accounts for 2 Rule 7 fires per 30 days.

**Seed threat-intel list** (validated against 30 days of live values on 8/14):

| Provider | Match on | Caveat |
|---|---|---|
| Apple iCloud Private Relay | org `iCloud Private Relay` | **org only.** Confirmed live: its ISP reads `Fastly, Inc.` and `Akamai Technologies, Inc.` — matching ISP would whitelist both CDNs wholesale |
| NordVPN | `NordVPN`, `Tefincom` | Rides Datacamp/M247 datacenter space — match brand names only, never the underlying host. Confirmed live: a `Datacamp Limited` host (`Cdnext BOS`) correctly still pages as Rule 6 |
| ExpressVPN | `ExpressVPN` | |
| Surfshark | `Surfshark` | |
| Proton VPN | `Proton AG`, `ProtonVPN` | |
| Private Internet Access | `Private Internet Access` | |

**Accepted residual risk — stated deliberately:** attackers also buy NordVPN subscriptions. Demoting these providers is a conscious trade: the event still lands in S1 as Info (correlatable against Rules 1/2/6/7 activity for the same user/window), and the v2 first-seen condition (this user has never had this approver ISP before) restores the signal without re-paging on every staff VPN user. Mullvad is the marginal call — flag per tenant.

**Intel maintenance:** this list is threat intel, not config — it decays. Review quarterly and on every Rule 3 FP; every unrecognized consumer brand seen in a Rule 3 fire is a candidate addition here. **Six queries reference it** (3, 6, 7, 11, 13, 16) — edit together.

**Analyst action:** none live. Reviewed in baseline/hunt context and as correlation data on other fires.

---

### Rule 14 — SIM-ID-014: First-Seen Sign-in Location for User (30-Day Baseline)

**Severity:** Medium (escalation path to High) | **MITRE:** T1078
**Window:** current 1h vs per-user 30-day baseline, evaluated every 5m

Added on Ryan's review (8/12). Fires when a user successfully signs in from a (country, state) combination that user has not produced in the prior 30 days. Proxy/hosting IPs are excluded — those are Rules 6/7/13 territory — so this catches the quieter case: a plausible-looking residential IP that simply isn't anywhere this user works from. The per-user pairing is built with a `format` pipe (`user|country|region` composite key) checked against the 30-day set of the same composite.

**Query A — non-mobile, state grain** (carrier CGNAT geolocates to gateway metros — the Verizon→Chicago effect — so mobile rows are excluded here and handled at country grain in Query B):

```
(record_type:entra_login_success OR record_type:entra_signin)
client_geo_country:* NOT client_geo_proxy:true NOT client_geo_hosting:true
NOT client_geo_mobile:true _time:1h
| format "<user_email>|<client_geo_country>|<client_geo_region>" as user_loc
| filter NOT user_loc:in(
    (record_type:entra_login_success OR record_type:entra_signin)
    client_geo_country:* _time:30d offset 1h
    | format "<user_email>|<client_geo_country>|<client_geo_region>" as user_loc
    | fields user_loc
  )
| stats by (user_email, client_geo_country, client_geo_region, client_geo_city, client_geo_isp, tenant_uid)
    count_uniq(event_uid) logins
```

**Query B — mobile, country grain** (second query in the same Grafana rule; a Verizon user "moving" Ohio→Chicago never fires, a mobile login from a first-seen country still does):

```
(record_type:entra_login_success OR record_type:entra_signin)
client_geo_country:* client_geo_mobile:true
NOT client_geo_proxy:true NOT client_geo_hosting:true _time:1h
| format "<user_email>|<client_geo_country>" as user_loc
| filter NOT user_loc:in(
    (record_type:entra_login_success OR record_type:entra_signin)
    client_geo_country:* _time:30d offset 1h
    | format "<user_email>|<client_geo_country>" as user_loc
    | fields user_loc
  )
| stats by (user_email, client_geo_country, client_geo_isp, tenant_uid)
    count_uniq(event_uid) logins
```

**Amended 8/14 — this was a real correctness bug, not a label bug.** The as-built rule used `client_geo_regionName` in the composite key on *both* the live side and the 30-day baseline side. Since the field does not exist, both sides resolved to `user|country|` and the rule silently degraded to country grain — duplicating Rule 9 instead of adding state sensitivity. Corrected to `client_geo_region`. **Query B is still not built** — the live rule carries a single query. Build it before arming.

The baseline sets deliberately include all connection types — spurious gateway-metro states in the baseline can only suppress fires, never create them, which is the safe direction.

**On the 50-mile ask — honest scoping:** a true 50-mile radius against every prior location is pairwise haversine across the baseline set, which a single LogsQL alert query cannot express. v1 grain is (country, state): for an Ohio-centric client base that approximates the intent at metro scale with far fewer moving parts. The true-radius version — n8n post-processing computing haversine from the numeric `client_geo_lat`/`lon` against a cached per-user location set — is the v2 item, shared with Rule 9's velocity upgrade. A middle option if state proves too coarse: swap `region` for a rounded lat/lon grid cell (~0.5° ≈ 35 mi) in the composite key; noted as tuning, not v1.
**FP profile:** travel and new hires. A new employee's first login always fires (no baseline) — acceptable, arguably desirable, but expect a small burst per onboarding; tunable later by requiring the user to exist in the baseline set. Business travelers fire once per new state per 30 days, then go quiet — self-limiting by design. Escalate to High when combined with `device_managed:false` or a generic hostname (Rule 12 labels).
**Dependencies:** the `format` + `in(<subquery>)` composite-key pattern is the load-bearing construct — validate on our VL version before enabling (new check V9, same family as V2). Baseline query cost over 30d also needs a look during V9 (eval every 5m re-runs it; widen eval interval if heavy).
**Analyst action on fire:** ticket — confirm with the user or their manager; check the same IP against Rules 1/2/10 history and whether Duo followed the sign-in.

---

### Rule 15 — SIM-ID-015: Access-Device vs Auth-Device Country Mismatch (Duo)

**Severity:** High | **MITRE:** T1078 / T1621
**Window:** 15m, evaluated every 5m

Fires when the two axes of a single Duo transaction disagree on country: the access device (the computer, `client_geo_*`) and the auth device (the phone, `approver_geo_*`) are far apart. Either direction is suspicious — victim's computer at home while an attacker-enrolled phone approves from abroad, or an attacker driving the session from abroad while the victim's US phone approves. Per Ryan's scoping: computer IPs only (hosting/proxy access devices are Rule 11's job), country grain because the approver is usually cellular (gateway jitter — mobile skepticism convention), and internal/non-routable IPs drop out automatically since absent geo never matches.

```
record_type:duo_auth auth_result:success
client_geo_country:* approver_geo_country:*
NOT client_geo_hosting:true NOT client_geo_proxy:true
NOT approver_geo_hosting:true NOT approver_geo_proxy:true
NOT <CONSUMER_VPN_MATCH>
NOT client_geo_country:eq_field(approver_geo_country) _time:15m
| stats by (user_email, client_geo_country, approver_geo_country, client_geo_isp, approver_geo_isp, application, tenant_uid)
    count_uniq(event_uid) auths
```

**Why low FP:** the matched population needs geo on both axes (routable both sides — a minority of duo_auth), both sides on plain networks (proxy/hosting/consumer-VPN excluded — those route to Rules 3/11/13), and a country-level disagreement. What survives is a physically implausible transaction. Country grain absorbs the Verizon→Chicago effect entirely.
**Tuning knobs:** none expected at country grain for an Ohio-based population; if a cross-border commuter pattern appears, per-user country-pair allowlist. v2 upgrade: degree-delta distance on numeric lat/lon for sub-country precision on non-mobile pairs.
**Dependencies:** the `eq_field` cross-field comparison needs validation on our VL version (check V11), alongside a dual-axis geo coverage measurement — if too few records carry both axes, this rule sees little traffic (which is fine: silence is cheap, and what does fire is high-quality).
**Analyst action on fire:** treat like Rule 11 — session/token revocation first, verify enrolled Duo devices, compare Entra records in the window.

---

### Rule 16 — SIM-ID-016: Consumer Privacy VPN on Access Device

**Severity:** Info (log-only into S1, no PagerDuty incident) | **MITRE:** context for T1078/T1557
**Window:** 30m, evaluated every 5m | **Added 8/14 (Ryan)** | **uid** `cfv6zduvy9r7kb`

The client-axis twin of Rule 13. Rule 13 demotes known consumer VPNs seen on the *phone*; this does the same for the *computer*. It covers **both** client-axis streams — Entra sign-ins (Rules 6/7 territory) and Duo access devices (Rule 11 territory) — so that every client-axis proxy/hosting event lands in exactly one of {6, 7, 11, 16}, mirroring the 3/13 property on the approver axis.

```
(record_type:entra_login_success OR (record_type:duo_auth auth_result:success))
(client_geo_hosting:true OR client_geo_proxy:true)
NOT client_geo_isp:("Breezeline" OR "Microsoft Corporation" OR "Microsoft Limited")
<CLIENT_VPN_MATCH> _time:30m
| stats by (user_email, client_ip, client_geo_isp, client_geo_org, client_geo_country,
            client_geo_region, client_geo_city, record_type, tenant_uid)
    count_uniq(event_uid) logins
```

**Why it exists:** before this rule, iCloud Private Relay was paging as High (Rule 6) — 7 of the 19 client-axis infra events over 30 days, across 5 users at 3 clients. Staff run Private Relay on managed Macs and iPhones; that is expected behavior, not a VPS login.
**Measured population:** 8 groups / 30d, all iCloud Private Relay.
**Deliberately NOT demoted here:** Cloudflare WARP (Cloudflare adjacency — sign-off 8/12, reconfirmed 8/14) and Mobilitie/SWITCH venue Wi-Fi (staff on untrusted networks is what Rules 6/7 are for — 8/14). Both continue to page as Rule 7.
**Accepted residual risk:** identical to Rule 13 — an attacker on Private Relay is demoted to Info. The event is still in S1 and correlatable, and the v2 first-seen condition restores the signal.
**Analyst action:** none live. Correlation context only.

---

## 4. Pre-implementation validation (gates enabling, ~1–2 hours total)

| # | Check | Gates |
|---|---|---|
| V1 | Run each rule query in Grafana Explore over a **7-day** `_time` window; record fire counts. Rules 6/7 additionally produce the per-tenant ISP allowlists from their result sets. | All rules; hard gate for 6, 7, 9 |
| V2 | Probe the `in(<subquery>)` construct on our VictoriaLogs version with the Rule 2 query verbatim. If unsupported, fallback: two-query Grafana rule (A = success IPs, B = spray IPs) with an expression join. | Rule 2 |
| V3 | Sample live `duo_auth` rows in VL: confirm exact stored names/values for `auth_result`, `reason` (`user_marked_fraud`), `factor`. Duo nested source fields are preserved alongside the envelope — confirm flattened names. | Rules 3, 4, 8 |
| V4 | Sample `action1_login` rows: confirm envelope names and enumerate `status_message` values (enables the failed-login extension of Rule 5). | Rule 5 |
| V5 | Confirm the n8n Identity Alert Hook passes the `severity`, `rule_id`, and group-by labels through to PagerDuty, and that per-`tenant_uid` routing behaves. One synthetic test alert per severity, verified through to S1 — confirm the exact severity enum casing the S1 ingest path expects (`Critical`…`Info`) and that the label passes through unmangled. | All |
| V6 | **Dependency flag:** follow-up E1 from the v1.1 closeout (n8n Error Workflow → PagerDuty for Identity Push/Pull) is still open. Until it lands, a stalled ingest silently disarms every rule here (Aug 11 scheduler stall precedent). Recommend E1 plus a meta-rule: alert if `record_type:entra_login_success _time:30m` count_uniq = 0. | Program-level |
| V7 | Sample `entra_login_success` rows for `device_hostname`: confirm envelope emission, coverage, and casing of DeviceProperties DisplayName; verify the default-hostname regex against live values. Also confirm Duo `client_geo_*` (access-device axis) coverage post dual-axis enrichment. | Rules 11, 12 |
| V8 | Run the Rule 3 base condition (no VPN exclusion) over 7 days; classify every distinct `approver_geo_org`/`isp`/`as` as consumer-VPN vs unknown. Seed/extend the `<CONSUMER_VPN_MATCH>` list from observed values; confirm no over-broad matches (Cloudflare/Datacamp collisions). Decide the Mullvad question per tenant. | Rules 3, 13 |
| V9 | Validate the Rule 14 construct on our VL version: `format` composite key + `NOT ...in(<subquery>)` with `_time:30d offset 1h`, verbatim. Measure baseline-subquery cost at the 5m eval cadence; widen the interval if heavy. If the construct is unsupported, Rule 14 falls back to the v2 n8n post-processing design. | Rule 14 |
| V10 | Quantify mobile/IPv6 geo jitter over 7 days: per user, distinct states on `client_geo_mobile:true` rows vs non-mobile (confirms the Verizon→Chicago effect and Rule 14's split); measure `mobile:true` ∧ `proxy:true` co-occurrence to build the carrier-CGNAT ISP allowlist for Rules 6/7 without excluding mobile. | Rules 6, 7, 9, 14 |
| V11 | Validate `eq_field` cross-field comparison for Rule 15 on our VL version; measure dual-axis geo coverage (`client_geo_country:* approver_geo_country:*` on duo_auth) to size the rule's visible population. Confirm the S1 library unified alert for fraudulent push is enabled per tenant and routes to PagerDuty (Rule 4 withdrawal dependency). | Rules 4 (withdrawal), 15 |
| **V12** | **Added 8/14.** Before adding any field to an `mv` rename pipe, confirm it exists: `<record filter> \| fields <candidate>` must return rows carrying it. `mv` on an absent field fails silently — this is what hid the `regionName` error across five rules for two days. | All future rule edits |

---

## 5. Live validation results (2026-08-12, run against production VL from Ryan's browser)

Every construct the rules depend on was probed verbatim against VictoriaLogs at 10.10.100.12; all volumes below are measured, not estimated.

| # | Check | Result |
|---|---|---|
| V2 | `in(<subquery>)` — Rule 2 | ✅ **Works**, including two `in()` clauses in one query. NAT-guard revision added (see Rule 2); refined query returns 0 false hits over 24h |
| V9 | `format` composite + `NOT in()` + `_time offset` — Rule 14 | ✅ **Works.** 6 first-seen groups in a 6h window vs 7d baseline; 30d baseline will run quieter. Subquery cost acceptable at test time; confirm at 5m cadence during build |
| V11 | `eq_field` — Rule 15 | ✅ **Works** (also proven in the 7/27 wallboard). 0 country-grain mismatches over 7d; dual-axis geo coverage 225/6,295 duo_auth (3.6%) — quiet by design. Old state-grain panel found 17/7d if more sensitivity is ever wanted |
| — | `filter` after `stats`; time-bucketed `stats by (_time:30m)` | ✅ Both work — used throughout testing |
| V3 | Duo field values | ⚠️ `auth_result` is `success`/`failure`, **not** `denied` — Rule 8 corrected. No `fraud` value observed in 7d (Rule 4 withdrawal consistent). Failure reasons enumerated |
| V4 | Action1 values | `status_message` = `OK` only in 7d (no failure vocabulary yet — failed-login variant stays parked). Stray `Action1LoginsTEST` stream (2 rows, no event_uid) should be deleted |
| V1 | 7-day fire volumes | Rule 1: 2 firing windows/7d, both office NATs → 0 with guard. Rules 2, 8, 9, 15: **0**. Rule 3 residual: ~2/7d (zenlayer, GTHost). Rules 6/7 residual: ~2/7d (Fastly, Cloudflare). Rule 11 residual: ~1/7d. Rule 12: 14 recurring user+hostname pairs/7d (mostly one under-managed client fleet — allowlist at baseline; the shared-box signal legitimately flagged one PC used by 3 users). Rule 14: ~6/6h vs 7d baseline, will settle with 30d |
| V7 | `device_hostname` coverage | 2,176/3,534 success events (62%) carry it — lower than the 97% upstream expectation but workable; regex verified against live values |
| V8/V10 | Consumer-VPN + mobile jitter | Trimmed VPN list matches **0** current events (list stays for when staff VPNs appear). The dominant infra-flag population is Breezeline CGNAT — handled by the regional-ISP allowlist, not the VPN list |
| V5/V6 | Alert-path checks | **Still open** — n8n hook label pass-through + synthetic alerts per severity, S1 enum casing, E1 error workflow, S1 library fraud-push alert confirmation. These are build-time, not query-time |

**Verdict: queries hold up.** Three revisions were required and are already applied above (Rule 1 guard, Rule 2 guard, Rule 8 value fix) plus the Breezeline allowlist convention. Post-fix expected alert volume across all 14 shipping rules: **roughly 5–10 alerts per week total**, nearly all Medium/Info — with the page-tier rules silent except during real attacks. Green to implement pending V5/V6.

**Correction to the V8/V10 line (8/14):** "Trimmed VPN list matches 0 current events" was true *on the approver axis only*. On the client axis the same list matches ~8 events per 30 days, all iCloud Private Relay — which is why Rule 16 exists. The 8/12 validation only ran the approver-axis expression.

---

## 6. What v2 unlocks (parked, not for sign-off)

True impossible-travel velocity and the Rule 14 50-mile-radius upgrade (both haversine on numeric lat/lon via n8n post-processing against a cached per-user location set); Duo↔Entra cross-stream correlation (Entra success with no Duo auth in window) — keyed on email now that directory-join coverage is ~97%; `device_managed:false` / `device_compliant:false` conditioning as an escalation label on Rules 6/7/9; per-client geo-fence policies as code; first-seen-provider condition on Rules 13/16 to restore signal on consumer-VPN events without re-paging every staff VPN user.

---

## 7. Post-sign-off amendments

### 2026-08-14 — `client_geo_regionName` → `client_geo_region` (Rules 2, 6, 7, 11, 14)

The field never existed in the envelope. `mv` on an absent field drops it silently, so the rules kept firing and the error was invisible until the wallboard rebuild surfaced it. Impact: empty `region` label on every alert from Rules 2/6/7/11; on Rule 14 (paused) the dead field sat in the composite dedup key on both sides, silently degrading first-seen from (country, state) to (country) grain. All five corrected live. New check **V12** added to §4 to prevent recurrence.

### 2026-08-14 — consumer-VPN demotion extended to the client axis (Rules 6, 7, 11 + new Rule 16)

Rule 13 only ever covered the approver axis. The same providers appear on the client axis, where they paged as High/Critical. `<CLIENT_VPN_MATCH>` (same provider list, `client_geo_*` prefix) added as a `NOT` clause to Rules 6, 7 and 11, and as the positive condition of new **Rule 16** (Info, log-only), which covers both the Entra and Duo client streams. Decisions taken with Ryan on 8/14: **WARP stays paging** (consistent with the 8/12 sign-off), **Mobilitie/SWITCH venue Wi-Fi stays paging**. Measured effect over 30 days: 19 client-axis infra events → 11 still paging (all real hosting plus the two deliberate keeps), 8 demoted to Info.

### 2026-08-14 — `NOT client_geo_hosting:true` documented as load-bearing in Rule 7

ip-api sets `proxy` and `hosting` together on some IPs. The as-built rule had the clause; the 7/27-lineage wallboard did not, and double-counted those events across Rules 6 and 7 until corrected. Called out explicitly in Rule 7 so it survives the next rewrite.

### Open items carried forward

1. **Build Alert v2 (severity_id)** — High/Critical still ingest into S1 as Low. Title prefix `[SIM-ID-XXX | Sev]` is the interim mitigation. Top follow-up.
2. **Rule 14 Query B (mobile, country grain) is not built** — the live rule has a single query. Required before arming.
3. **Rules 12 and 14 remain paused**, awaiting the BYOD allowlist and the 30-day baseline settle respectively.
4. **`count()` → `count_uniq(event_uid)`** normalisation across 3, 5, 6, 7, 11, 12, 13, 14, 15.
5. **V5/V6 alert-path checks** still open from 8/12.
