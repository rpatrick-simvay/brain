# Status log — SOC Wallboard quota + tile fixes (2026-07-21 → 07-22)

## 2026-07-22 v31–v32: trend chart high-only; Alert Volume urgency lines; x-axis formats

- **v31**: trend chart (panel 23) filtered to `urgency=high` + retitled "Daily MTTA / MTTR Trend — High Urgency" (Ryan: low-urgency acks skew the means). Verified vs raw: 07-20 n=22 0.4m/3.8m; 07-21 n=43 0.7m/6.8m; 07-22 n=3 3.2m/**65.5m** — today's MTTR climb real even high-only (1 long incident in a 3-incident sample).
- **v32 Alert Volume (panel 5)**: bars → two smooth 2px lines split by urgency, colors matching the tile semantics: **High Urgency #ff9830 orange = severity (CRITICAL|HIGH|MEDIUM), Low Urgency #5794F2 blue = (LOW|INFO)** (VM severities present: HIGH/MEDIUM/LOW/INFO; CRITICAL included preemptively). PromQL trick: duplicate label matchers AND together — `severity=~"$severity",severity=~"(CRITICAL|HIGH|MEDIUM)"` keeps the dashboard filter working. Legend bottom, stacking off, fillOpacity 8.
- **X-axis format discovery (KEY)**: overriding the TIME field's `unit` to `time:<moment format>` (override matcher byType time → unit `time:ddd HH` / `time:MM/DD`) **does control the timeseries x-axis tick labels** in Grafana 13. Alert Volume now shows "Sun 12, Sun 18, Mon 00…" (no minutes, short weekday). Trend chart shows "07/19 07/20 …" but REPEATS each day ~3–4× because uPlot places ticks every ~6h at a 3d window — tick density is width-derived and NOT configurable; repeats will collapse to one per day when the dashboard window widens to 7d (planned after 07-24). If it bugs Ryan sooner: barchart with string day labels is the only full-control alternative.

Dashboard now at **v32**.

## 2026-07-22 v30: layout, thresholds, MTTA/MTTR trend chart

- **Labels**: bargauge `options.text.titleSize` 15→12 on panels 14/15 (font size is the only name-column lever).
- **Thresholds**: panels 8/11 = green(base)/orange@1/red@5, AND the theme-JS TH map updated via base64 block replace (mkScript pattern). **JS TH map must be kept in sync with panel thresholds.**
- **New panel 23** (timeseries x0 y16 w14 h8; Alert Volume h16→8): consumes shared panel-1 query, zero extra PD calls. Daily-bucket chain: filterByValue → convertFieldType(created_at→time) → formatTime('YYYY-MM-DD', useTimezone) → groupBy(day, means) → convertFieldType(→time) → sortBy → organize rename. MTTA #5794F2 / MTTR #ff9830, unit s, min 0.

## 2026-07-22 v28–v29: responder credit + gauge fill

**Responder credit (v28):** Infinity computed columns are **govaluate: no array indexing, no functions** — arrays need the extractFields transform. Panel 15: filterByValue(acked) → extractFields on `acknowledged_user_names` (json) → organize rename `0`→`Responder` → groupBy + count(id) → sortBy. Stevie 66 / Shane 22 / James 18 = 106 acked exactly; pair-dup gone. `[0]` = first array element (PD order undocumented; SOC single-acker in practice).

**Gauge fill (v28–v29):** without min/max Grafana ranges over ALL numeric fields globally. Pattern: filterFieldsByName → reduce(reduceFields, sum) → panel lastNotNull → `min=0` (else smallest bar renders empty).

## 2026-07-22 v26–v27: API healthy, broken tiles fixed

Quota recovered between Tue ~12:30 EDT and Wed ~10:15 EDT.

**Blank MTTA/MTTR/SLA tiles root cause:** `fieldConfig.defaults.displayName` renames every field at display time and `reduceOptions.fields` regex matches DISPLAY names → no match → noValue. Total Triage worked by accident (calculateField sets field-level displayName). Fix: deleted defaults.displayName on 1,2,3,4,13 (textMode value never shows it).
**RULE: never combine defaults.displayName with a reduceOptions.fields regex on raw field names.**

Also: "Metrics Pipeline Lag" → "Time Since Last Alert" + honest tooltip (can't distinguish quiet vs dead collector until heartbeat metric); JS units matched Grafana.

## 2026-07-21: quota exhaustion diagnosis + hardening (v22–v25)

### Root cause + pull inventory
PD analytics `DAILY_LIMIT_EXCEEDED` (HTTP 200) 16h past midnight UTC — reset assumption wrong. Complete inventory: panel 1 shared query + panel 22 probe are the ONLY PD callers (2 calls/refresh or page load); consumers 2/3/4/12/13/14/15/23 via `-- Dashboard --`; live panels + ticker all VictoriaMetrics; old SOC Metrics jhx9xk5 manual-only; no alert rules/library panels/other PD DSs; scheduled tasks only Morning Brief (MCP connector). Grafana couldn't burn the quota → external consumer or non-midnight reset. Ryan: curl -i ratelimit headers; dedicated bot-user key for Grafana.

### Shipped v22–v25
1. SLA Breaches on shared query via computed column `sla_breach` (govaluate ternary, inline-mock validated).
2. p13 noValue "0"→"NO DATA".
3. PD API status tile (22): limit:1 probe `$exists($.status) ? $string($.status) : 'OK'` → green "API OK" / red "QUOTA EXHAUSTED" (rgb(223,20,16) crit pulse). Stat fields:'' = numeric-only; strings need `/.*/`.
4. 12h auto-refresh (PD ≈ 4 calls/day/open screen; page loads cost 2 — playlists dangerous until Simvay API caching proxy) + guarded theme-JS live counters (60s VM proxy → DOM update panels 8/11/9, text+unit+gradient recolor; reads URL vars; hooks `[data-viz-panel-key="panel-N"]` first leaf span, gradient div `div[style*="linear-gradient"]`).

### Durable technical notes
- Theme panel content can't be echoed through the extension (DLP) — string append/replace in page context only.
- Post-transform panel data: `window.__grafanaSceneContext` walk → `$data.state.data.series`.
- Infinity computed columns = govaluate (comparisons/ternary/`!= nil` only); arrays → extractFields. Test on `source:'inline'` first.
- Bargauge fill-relative-to-max: restrict fields + reduceFields(sum) + min 0.
- **Timeseries x-axis tick format: override time field unit to `time:<format>`** (e.g. `time:ddd HH`, `time:MM/DD`); tick DENSITY is width-derived and not configurable.
- Daily-bucket chain for PD raw: convertFieldType → formatTime day → groupBy means → convertFieldType → sortBy → organize.
- Grafana OSS: refresh global per dashboard; no per-panel refresh; query caching Enterprise-only.

### Remaining opens
Heartbeat metric; QBR spec update; dashboards-as-code export; Simvay API /pagerduty caching routes (THE fix before TVs/playlists); exact quota reset semantics (curl -i); trend-chart day labels collapse naturally at 7d window (or convert to barchart if wanted sooner).
