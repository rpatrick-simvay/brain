# Status — Fleet Health 1080p fit + new Anomalous Logins wallboard (2026-07-27)

TVs were dropped to 1080p today. Fleet Health overflowed; fixed. New Identity board built to replace the SOC > Identity > Anomalous Authentication table (the Auth Map stays on its own TV).

## 1. Fleet Health Wallboard — now fits 1920x1080 (v14)

**Measured kiosk geometry (Grafana 13, `?kiosk`, 1920x1080):**

- Viewport 1092px; grid starts at y=70 (kiosk toolbar); usable ≈ **1014px**.
- Grid row = 30px, gap = 8px → panel px = `h*30 + (h-1)*8`.
- **26 grid rows = 980px is the practical ceiling.** Old layout was 30 rows / 1132px → 118px overflow (Western Reserve LS was cut off).

**New layout** (was: three full-width stat tiles above an 18-wide matrix + 6-wide headlines):

| Panel | id | gridPos (x,y,w,h) |
|---|---|---|
| Header/theme | 20 | 0,0,24,2 |
| S1 API Health — 24h | 31 | 0,2,18,2 |
| Client Integration Matrix | 30 | 0,4,18,22 |
| Metrics Pipeline Lag | 3 | 18,2,6,3 |
| Accounts Reporting (24h) | 4 | 18,5,6,3 |
| Open Alerts Now | 5 | 18,8,6,3 |
| Security Headlines | 40 | 18,11,6,15 |

Stats moved into a right rail so the matrix keeps its height. Matrix table content is 778px and needs h≥21; h=22 gives headroom for new clients.

Also: matrix `custom.width` 115→**104**, `minWidth` 125→**90** — at 18 columns wide the old widths pushed VirusTotal off and produced a horizontal scrollbar.

Verified: `document.scrollingElement.scrollHeight - window.innerHeight === 0`.

## 2. New dashboard: Anomalous Logins Wallboard (Draft)

`identity-anomalous-logins-draft`, Testing folder, **v6**. Time `now-24h`, refresh 1m (VictoriaLogs only — no PagerDuty quota exposure). 26 grid rows, verified zero overflow.

**Why not just port the old table:** the existing `Anomalous Authentications` library panel (proxy OR hosting IP, 3-source union) returned **5 rows in 7 days**. Too sparse for a TV. Ryan chose tiered rules + auth-device vs access-device geo variance, per-domain expected countries, 24h main view with a 7d context strip.

### Layout

- y0 h2 — header/theme panel (copied from Fleet Health p20, "FLEET HEALTH" → "ANOMALOUS LOGINS").
- y2 h4 — six stat tiles w4: MFA Fraud Reports, MFA Denials, Infra / VPN IP Logins, Unexpected Country, Device Geo Mismatch, Users Flagged.
- y6 h14 — **Investigation Queue — Last 24h** (table): Time, Severity, Signal, User, Location, Detail, Source.
- y20 h6 — **Signals by Day — 7d** (barchart, w16) + **Most-Flagged Users — 7d** (bargauge, w8), both `timeFrom: 7d`.

### Signal tiers (one LogsQL union, sorted `rank` asc then `_time` desc)

| Signal | Severity / rank | Source | 7d volume |
|---|---|---|---|
| MFA fraud reported (`result:fraud`) | CRITICAL / 1 | Duo | 1 |
| MFA denial (`no_user_allowed`, `deny_unenrolled_user`, `frequent_attempts`) | HIGH / 2 | Duo | 21 |
| Unexpected country (non-US, see rule below) | HIGH / 2 | Entra ID | 10 |
| Infra / VPN IP (proxy or hosting) | HIGH / 2 | Duo + Entra + Action1 | 29 |
| Device geo mismatch (workstation state ≠ 2FA device state, non-mobile only) | MEDIUM / 3 | Duo | 17 |

Deliberately excluded as noise: `no_response` (134/7d), `user_cancelled`, `touch_id_*`, and **mobile** auth-device geo mismatches (236 of 253 — carrier NAT geolocation).

### Country rule — SETTLED 2026-07-27 (Ryan)

**Every domain is US-only. The single exception is gzgreatlakes.com**, which is allowed China, Philippines, Japan, Singapore, Vietnam (Guangzhou office). All clients are Ohio HQ; travel is domestic, so any non-US sign-in is worth a look.

Second, mandatory exclusion: **drop sign-ins whose `device.ip.isp` or `device.ip.org` is Microsoft Corporation / Microsoft Limited.** Microsoft's own service IPs geolocate to Canada and generated ~400 false "Canada" hits for greatlakesbrewing.com alone (cellartechs@, canningline@, brewhouse@, aaronh@…). Without this exclusion the tile is unusable; with it the signal is real.

Net volume after both rules: **69 events / 30d, 10 / 7d** (~1.4/day) — e.g. `paragon@hinkley.com` via Rogers Canada (23), `mmizak@polaris.edu` via Digiweb Ireland (14) and Vodafone UK (9), `ceschweiler@brooklynohio.gov` via Niagara Regional Broadband (13). Ryan reviewed these and confirmed they are travel/outliers — correct to surface, not to suppress.

Inlined in the queries as:

```
| filter !(domain:"gzgreatlakes.com" "device.ip.country":("China" OR "Philippines" OR "Japan" OR "Singapore" OR "Vietnam"))
| filter !"device.ip.isp":("Microsoft Corporation" OR "Microsoft Limited")
| filter !"device.ip.org":("Microsoft Corporation" OR "Microsoft Limited")
```

Present in panels 13, 15, 20, 30, 31 — patch all five together if the rule changes.

## 3. Durable technical findings (LogsQL / VictoriaLogs in Grafana)

1. **`eq_field` works** — `!"access_device.location.state":eq_field("auth_device.regionName")` does field-to-field comparison server-side. This is what makes the geo-variance tile possible; Grafana transforms cannot compare two fields.
2. **`format` pipe interpolates with `<field>`** and supports `format if (<filter>) "..." as x` — used for severity labels, fallback user (email → user.name) and fallback location (auth_device → access_device → "—").
3. **`extractFields` must use `replace:false`.** With `replace:true` the `Time` field is destroyed → table loses its Time column and charts report "Data is missing a time field". Follow with `filterFieldsByName` include-regex instead.
4. **`statsRange` rejects `union`**: "the pipe `union ...` cannot be put in front of `stats`, since it may modify or delete `_time`". Workaround: bucket inside LogsQL (`| stats by (_time:1d, signal) count() n`) as an **instant** query and shape it with transforms.
5. **Day buckets need a timezone offset.** `_time:1d` buckets on UTC midnight; rendered in America/New_York every label lands on the previous day. Use `_time:1d offset 4h` (EDT). Revisit at the DST change.
6. **Barchart beats timeseries for daily bars** — uPlot tick density is width-derived and repeats labels ("Tue 07/21, Tue 07/21…"). Chain: convertFieldType Time→time → sortBy Time asc → `formatTime 'ddd MM/DD'` → `groupingToMatrix` → barchart `xField: "Time\\signal"`.
7. **`rowsToFields` for bargauge** needs a `filterFieldsByName` first, or field names come out as `user {Line="", Time="178…"}`.
8. **Geo-IP vendor attribution matters more than country.** Microsoft-owned ranges geolocate to Canada; iCloud Private Relay and Cloudflare WARP show as proxy/hosting. Filter on `isp`/`org` before trusting `country` or `proxy`.
9. Duo record shapes differ: some carry `email`, all carry `user.name` (sometimes a short username like `fabrizia`). Entra uses `actor.user.email_addr`, Action1 uses `user_name`.
10. Entra has no auth success/failure field — `device.is_managed` exists but with inconsistent casing (`True`/`true`/`False`/`false`), so any tile using it needs normalization.

## 4. Planned: travel-line arcs on the map TV (BLOCKED on data)

Ryan wants animated arcs between the workstation and the 2FA device on the Auth Map board. Decisions taken 2026-07-27: **wait for proper enrichment** (no city-lookup stopgap), and add it as a **new panel on the map TV board** rather than replacing the existing geomap.

- Panel plugin is available: `volkovlabs-echarts-panel` is installed (also `vaduga-mapgl-panel`). ECharts `lines` + `effect` gives the animated flight-path look.
- **Blocker:** only the `auth_device` side has coordinates. `access_device.location.lat` is populated 0 times in 30 days. Duo gives the workstation city/state/country only.
- Coverage today (30d): 91,961 Duo auths → 13,914 with `auth_device.lat` (15%) → 5,281 with workstation city *and* 2FA lat/lon. 80 distinct workstation cities.
- Ask written up in `claude/spec-2026-07-27-duo-access-device-geo-enrichment.md` and handed to Ryan for James: run `access_device.ip` through the same geo-IP enrichment, emit lat/lon as **numbers**, plus isp/org/as/proxy/hosting/mobile.
- Bonus once it lands: the geo-mismatch signal can use real distance instead of a state-string comparison, and we get workstation-side VPN/hosting detection.
- Open question for James: why only 15% of auths carry `auth_device` geo at all — passcode vs push, remembered-device sessions, or no auth-device IP returned?

## Open follow-ups

1. Old `Identity Wallboard (Draft)` (`identity-wallboard-draft`) still holds the Auth Map + the original Anomalous Authentications library panel — decide whether to strip it to just the map for the map TV.
2. `device.is_managed` unmanaged-device sign-ins (396 false + 7813 False in 7d) are not on the board yet; too noisy without a per-client baseline.
3. DST: revisit `offset 4h` in November.
4. Promotion: move drafts out of Testing, set kiosk URLs per TV, playlist rotation.
