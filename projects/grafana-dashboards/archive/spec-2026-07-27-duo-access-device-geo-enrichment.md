# Data ask: geo-enrich the Duo access device

**For:** James (Simvay API / collectors)
**From:** Ryan
**Date:** 2026-07-27
**Why:** unblocks travel-line arcs on the SOC map TV, and materially improves the anomalous-login detection we shipped today.

---

## 1. The ask in one line

Run `access_device.ip` through the **same geo-IP enrichment already applied to `auth_device`**, and write the results into the Duo authentication records in VictoriaLogs.

## 2. What we have today

Duo authentication records are enriched on one side only.

**`auth_device` (the 2FA phone) — fully enriched:**

`auth_device.lat`, `auth_device.lon`, `auth_device.city`, `auth_device.regionName`, `auth_device.country`, `auth_device.continent`, `auth_device.isp`, `auth_device.org`, `auth_device.as`, `auth_device.proxy`, `auth_device.hosting`, `auth_device.mobile`, `auth_device.query` (the IP)

**`access_device` (the workstation) — raw:**

`access_device.ip`, `access_device.location.city`, `access_device.location.state`, `access_device.location.country` (these three come from Duo itself, not from enrichment), plus posture fields (`is_firewall_enabled`, `is_encryption_enabled`, `security_agents`, `hostname`, …)

**Counts over 30 days:**

| Measure | Count |
|---|---|
| Duo authentication events | 91,961 |
| …with `auth_device.lat` populated | 13,914 (15%) |
| …with workstation city **and** 2FA lat/lon | 5,281 |
| …with `access_device.location.lat` | **0** |
| Distinct workstation cities seen | 80 |

## 3. What we want written

Mirror the `auth_device` field set, so dashboards can treat both endpoints identically:

| Field | Type | Notes |
|---|---|---|
| `access_device.lat` | **number** | not a string — the current `auth_device.lat` arrives as a string and every panel needs a convertFieldType step |
| `access_device.lon` | **number** | same |
| `access_device.city` | string | |
| `access_device.regionName` | string | |
| `access_device.country` | string | |
| `access_device.isp` | string | |
| `access_device.org` | string | |
| `access_device.as` | string | |
| `access_device.proxy` | bool | |
| `access_device.hosting` | bool | |
| `access_device.mobile` | bool | |

Keep the existing `access_device.location.*` fields as they are; the new fields sit alongside them.

## 4. What this unlocks

1. **Travel lines on the map TV.** An animated arc from workstation → 2FA device per authentication (the ECharts panel plugin is already installed on our Grafana). Impossible today: one endpoint has no coordinates.
2. **Better anomaly detection on the new Anomalous Logins wallboard.** The "device geo mismatch" signal currently compares `access_device.location.state` to `auth_device.regionName` — a string comparison between two US states. With coordinates we can compute actual distance and flag on a real threshold instead of any-state-difference.
3. **Workstation-side VPN/proxy detection.** `proxy` / `hosting` / `isp` / `org` on the access device would let us flag "workstation logged in from a hosting IP" directly. Today we only see that for the 2FA device and for Entra sign-ins.
4. **Less false positive noise.** We already had to exclude Microsoft-owned IP ranges from the country signal (Microsoft service IPs geolocate to Canada and produced ~400 false hits in 30 days). Having `isp`/`org` on both endpoints makes that filtering consistent.

## 5. One question to check while you're in there

Only 15% of authentication events carry `auth_device` geo at all (13,914 of 91,961). Is enrichment skipped for certain record types — passcode vs push, cached/remembered-device sessions, or events where Duo doesn't return an auth-device IP? If some of that gap is recoverable, the map gets substantially denser.

## 6. Related open asks (same list as the PagerDuty spec)

See `claude/spec-2026-07-27-pagerduty-api-gaps-for-v2.md` for the PagerDuty items: `urgency` and `service_ids` dimensions, 15-minute scrape cadence with a collector heartbeat, and a per-incident raw feed into VictoriaLogs.
