# n8n review — identity enrichment path and where Microsoft device context plugs in

**Instance:** `http://10.10.99.13:5678` (titled `n8n[DEV]`)
**Reviewed:** 2026-07-31 — read-only. Nothing saved, activated, executed, or modified.
**Reviewer:** Ryan (workflows are owned by James Hering / personal project `40awlt7wrkwzoyTC`)

---

## 0. Headline

Three things, in order of importance:

1. **The ip-api enrichment is not in n8n.** No workflow references ip-api, and there is no ip-api credential stored in n8n. Enrichment happens server-side in the Simvay API at `10.10.100.8:8000`, exposed as a query flag (`?enrich=true`) on at least the SentinelOne datalake endpoint. n8n only moves already-enriched records.
2. **The Microsoft/Entra device context is already being collected.** The `SentinelOne Push/Pull` workflow pulls Entra logon events every 60 seconds and explicitly requests `device.is_managed`, `device.os.type` and `unmapped.DeviceProperties`, then parses DeviceProperties into a `device_attributes` object. `IsCompliant`, `IsCompliantAndManaged`, `TrustType`, `BrowserType`, `OS`, device `DisplayName` and `SessionId` are all in the payload today.
3. **It never reaches the alert.** `Identity Alert Hook` builds its OCSF finding purely from Grafana alert *labels*, and the label set contains no device fields at all. Every alert this hook has processed was Duo-sourced. The gap is not collection — it is that the Entra device fields are not promoted into Grafana labels, and the alert builder has no slot for them.

---

## 1. Instance inventory

Six workflows (one archived). All owned personally by James, no tags, no folders.

| Workflow | ID | Active | Nodes | Last updated |
|---|---|---|---|---|
| PagerDuty/Alerting | `fK03zkD5kv9bqd68JS-Yy` | yes | 8 | 2026-07-21 |
| Identity Alert Hook | `TARIuJxalAZ8Q2-xELoSB` | yes | 9 | 2026-06-22 |
| SentinelOne Push/Pull | `a-PzLDvSUPp6PO2Y-SaQ8` | yes | 12 | 2026-06-15 |
| Duo Push/Pull | `09vPm6cRPx31iO0KVZSJX` | yes | 3 | 2026-04-20 |
| Action1 Push/Pull | `10z5LkMfMhNcwXkX3S2Il` | yes | 10 | 2026-04-13 |
| S1 Push/Pull *(archived)* | `IH-g-hXN5_z3oznvPpAsL` | no | 0 | 2026-04-20 |

Instance totals: 31,811 production executions, 687 failed (2.2%), avg run time 2.56s.

**Credentials stored in n8n:** only two — `PagerDuty` (httpCustomAuth) and `NFR` (httpBearerAuth). **No variables defined.** No ip-api, Duo, Microsoft, or SentinelOne credential lives in n8n; every collector call goes unauthenticated to the internal Simvay API, which holds the real keys.

**Hosts referenced:**

| Host | Role |
|---|---|
| `10.10.100.8:8000` | Simvay API — collectors + enrichment + alert ingest |
| `10.10.100.12:9428` | VictoriaLogs — `/insert/jsonline` |
| `10.10.100.13:9001` | "temporary parser" — only the Microsoft branch posts here |

---

## 2. The identity pipeline, end to end

```
Duo ──► Simvay API /duo/authlogs ──► [n8n: Duo Push/Pull, hourly] ──► VictoriaLogs
                (enrichment applied to auth_device only)

Entra ─► Simvay API /sentinelone/datalake/queryall?enrich=true
                    ──► [n8n: SentinelOne Push/Pull, every 60s] ──► temp parser :9001 ──► ? ──► VictoriaLogs

VictoriaLogs ──► Grafana alert rule (folder SOC/Identity) ──► webhook
                    ──► [n8n: Identity Alert Hook] ──► OCSF finding ──► Simvay API ingest
```

### 2a. `Duo Push/Pull` — 3 nodes, hourly

1. **Schedule Trigger** — `{interval:[{field:"hours"}]}`, i.e. every hour.
2. **Pull Duo Auth Logs** — `GET http://10.10.100.8:8000/duo/authlogs` with `mintime = timestamp - 3600000`, `maxtime = timestamp`. A one-hour window on an hourly schedule, with no overlap and no watermark — a late-arriving or slow run silently loses events.
3. **Push to Log DB** — `POST http://10.10.100.12:9428/insert/jsonline`, headers `VL-Msg-Field: event_type`, `VL-Time-Field: isotimestamp`, `VL-Stream-Fields: factor,event_type,result`.

Note this endpoint is called **without** `enrich=true` — enrichment behaviour differs per endpoint on the Simvay API side.

**Observed Duo record shape** (execution 249454, 111 records):

```jsonc
{
  "access_device": {                      // the workstation — THIN
    "epkey": "...", "hostname": null, "ip": "98.172.132.157",
    "location": { "city": "Cleveland", "state": "Ohio", "country": "United States" }
  },
  "auth_device": {                        // the 2FA phone — FULLY ENRICHED
    "ip": "...", "key": "...", "name": "330-421-9308", "serial": null, "type": null,
    "location": { "city": "...", "state": "...", "country": "..." },
    "as": "AS22773 Cox Communications Inc.", "city": "Cleveland",
    "continent": "North America", "country": "United States",
    "hosting": false, "isp": "Cox Communications Inc.", "lat": 41.5, "lon": -81.6938,
    "mobile": false, "org": "Cox Communications Inc.", "proxy": false,
    "query": "98.172.132.157", "regionName": "Ohio"
  },
  "application": { "key": "...", "name": "OlmstedTwp M365" },
  "email": "...", "event_type": "authentication",
  "factor": "Duo Push (passwordless)", "isotimestamp": "...",
  "ood_software": null, "passport_assessment": {...},
  "reason": "...", "result": "...", "trusted_endpoint_status": "unknown",
  "txid": "...", "user": {...}
}
```

Two things worth flagging, both new evidence for the ask already filed in `claude/spec-2026-07-27-duo-access-device-geo-enrichment.md`:

- Across all 111 records in that run, `access_device` carried **only** `epkey / hostname / ip / location`. No OS, no browser, no posture fields (`is_firewall_enabled`, `is_encryption_enabled`, `security_agents` were absent entirely, not merely null).
- `trusted_endpoint_status` was `"unknown"` on every record in that sample. *(Corrected against VictoriaLogs — see §6: it is 97% `unknown` over 7 days, not 100%. 601 `trusted` and 62 `not trusted` records do exist.)*

So "device context from Duo" today is effectively: an IP, an opaque endpoint key, a mostly-null hostname, and a Duo-supplied city/state.

### 2b. `SentinelOne Push/Pull` — the Microsoft branch

This workflow contains three independent trigger chains. The third is the Microsoft one:

1. **Output Microsoft Ingest to LogsDB** — Schedule Trigger, `minutesInterval: 1` (every 60 seconds).
2. **Pull Entra Logins in SentinelOne Datalake** — `POST http://10.10.100.8:8000/sentinelone/datalake/queryall?enrich=true`

   ```jsonc
   {
     "filter": "dataSource.vendor='Microsoft' dataSource.category='security' actor.user.email_addr=* device.ip=* event.type='Logon' dataSource.category='security'",
     "startTime": "12 hours",
     "columns": "metadata.product.vendor_name,actor.user.email_addr,type_name,device.ip,metadata.original_time,device.is_managed,device.os.type,unmapped.DeviceProperties,metadata.uid"
   }
   ```

   `enrich=true` is the ip-api hook. `dataSource.category='security'` appears twice in the filter string — harmless, but a sign of hand-editing.
3. **Prep 365 Data** — a Set node in raw mode that removes `unmapped.DeviceProperties` and re-adds it parsed:

   ```js
   { ...$json.attributes.removeField("unmapped.DeviceProperties"),
     "device_attributes": typeof $json.attributes?.['unmapped.DeviceProperties'] === 'string'
       ? JSON.parse($json.attributes['unmapped.DeviceProperties'])
       : ($json.attributes?.['unmapped.DeviceProperties'] || {}) }
   ```
4. **Push Logs to temporary Parser** — `POST http://10.10.100.13:9001/`, raw text body, one empty header parameter left in place.

**Observed Entra record** (execution 249496):

```jsonc
{
  "actor.user.email_addr": "bgoetz@simvay.com",
  "device.ip": { "as": "...", "city": "...", "continent": "...", "country": "...",
                 "hosting": true, "isp": "...", "lat": 41.5053, "lon": -82.0282,
                 "mobile": false, "org": "...", "proxy": false, "query": "...",
                 "regionName": "..." },
  "device.is_managed": "True",
  "device.os.type": "Windows10",
  "metadata.original_time": "2026-07-30T13:15:42",
  "metadata.uid": "a805621e-...",
  "metadata.product.vendor_name": "Microsoft",
  "device_attributes": [
    { "Name": "Id",                     "Value": "b8af4260-962e-48b3-9fcc-7a6c811ecbf8" },
    { "Name": "DisplayName",            "Value": "SIMSFCBGOETZ" },
    { "Name": "OS",                     "Value": "Windows10" },
    { "Name": "BrowserType",            "Value": "Edge" },
    { "Name": "IsCompliant",            "Value": "True" },
    { "Name": "IsCompliantAndManaged",  "Value": "True" },
    { "Name": "TrustType",              "Value": "1" },
    { "Name": "SessionId",              "Value": "006cfa89-..." }
  ]
}
```

**This is the source device context you are looking for, and it is already flowing.** It is richer than anything Duo gives: a stable device GUID, a device name, OS, browser, Intune compliance, Entra join/trust type, and a session ID that ties multiple sign-ins together.

Two structural notes:

- `device_attributes` is a **`[{Name, Value}]` array, not an object.** Anything consuming it needs a reshape step, or it should be flattened at the parser.
- The Microsoft branch is the only chain in the instance that posts to `10.10.100.13:9001` rather than straight to VictoriaLogs. **Resolved against VictoriaLogs — see §6: the parser does forward `device_attributes`, but leaves it as a raw JSON string rather than flattening it. That, not loss, is why no dashboard uses it.**

### 2c. `Identity Alert Hook` — 9 nodes, webhook-driven

```
Webhook - Medium/High ─► Split Out ─► Loop Over Items ─► Build Alert ─┬─► If row does not exist ─► Post to Simvay-API ────────────┐
                                          ▲                            └─► If row exists ─► Get row(s) ─► Post to ...-Known-Domain ┤
                                          └────────────────────────────────────────────────────────────────────────────────────────┘
```

| Node | Detail |
|---|---|
| `Webhook - Medium/High` | `POST /webhook/638bd38a-97c9-4d73-85c6-d5f4e0becb14`, no auth configured |
| `Split Out` | splits `body.alerts` — a Grafana Alertmanager payload |
| `Loop Over Items` | splitInBatches; output 0 unused, output 1 → Build Alert |
| `Build Alert` | 154-line Code node; builds the OCSF finding |
| `If row exists` / `If row does not exist` | dataTable `Temporary Account Link` (`N0uINWDrIWMH5fI8`), matched on `$json.resources[0].name.split('@')[1]` — the email domain |
| `Get row(s)` | fetches the matched row to obtain `ten_id` / `acct_key` |
| `Post to Simvay-API` | `POST 10.10.100.8:8000/sentinelone/unifiedalerts/ingest/detection` |
| `Post to Simvay-API-Known-Domain` | same URL, plus `?ten_id=…&acct_key=…` from the data table |

So the data table is a domain → tenant routing map: known domains post with tenant credentials, unknown domains post without.

**The incoming Grafana labels** (execution 243469) are the entire input to the alert:

```jsonc
{
  "alertname": "New Identity Alert - Duo - Low",
  "city": "Columbus", "region": "Ohio", "country": "United States",
  "email": "sudbrookc@avoneagles.org",
  "event": "Windows MFA",
  "grafana_folder": "SOC/Identity",
  "ip": "151.186.191.110",
  "isp": "Amazon.com, Inc.", "org": "CIE",
  "ishosting": "true", "ismobile": "false", "isproxy": "true"
}
```

Thirteen labels. **Every one is either identity, geo, or ip-api risk. There is not a single device field.** `event: "Windows MFA"` is the Duo *application* name, not a device.

**What Build Alert emits** — OCSF `class_uid 99602001` ("Security Alert", S1 extension `996`), severity mapped from the alertname suffix (`Medium` → severity_id 2 / priority medium; anything else → low):

- `finding_info.related_events[]` — five synthetic sub-events, one per signal:

  | type | message | severity |
  |---|---|---|
  | `Authentication` | "IP Authentication Info" (+ 6 observables: dst.ip.address, City, Region, Country, Organization, ISP) | Medium |
  | `Auth App` | the `event` label | Low |
  | `Is Proxy Detection` | `isproxy` | High if true |
  | `Is Hosting Detection` | `ishosting` | High if true |
  | `Is Mobile Detection` | `ismobile` | Low |

- `resources[]` — one entry, `type: "Email"`, uid/name = the email, `owner.name` = the IP (an odd mapping — owner is being used to carry the IP)
- `observables[]` — the IP and the email address
- `metadata` — product `SIMVAY`, extension `s1`/`996`, version 1.1.0

**Execution history: only 4 runs, ever** — 2026-07-28 and 2026-07-29, two per day, all `success`, all `alertname` = `New Identity Alert - Duo - {Low,Medium}`. **No Entra-sourced alert has ever entered this hook.**

### 2d. Other workflows (context only)

- **`PagerDuty/Alerting`** — scheduled; pulls incidents → splits → fetches alerts → flattens → reads the same `Temporary Account Link` data table → GraphQL → "Update Incident Priority to TRIAGE". Uses the `PagerDuty` credential.
- **`Action1 Push/Pull`** — 10 nodes, unrelated to identity.
- **`SentinelOne Push/Pull`**, other two chains — pull S1 accounts and integrations on a schedule and push to VictoriaLogs; these feed the Fleet Health integration matrix.

---

## 3. Where Microsoft device context should plug in

The collection work is done. Three gaps sit between `device_attributes` and an enriched detection, and only the middle one is in n8n.

### Gap 1 — parser (outside n8n, ask James)

Confirm `10.10.100.13:9001` forwards `device_attributes` into VictoriaLogs, and ask for it flattened at write time rather than left as a `[{Name,Value}]` array:

| Suggested field | From | Why |
|---|---|---|
| `device.uid` | `Id` | stable device GUID — the join key Duo cannot provide |
| `device.name` | `DisplayName` | human-readable in the investigation queue |
| `device.os` | `OS` | already partly available as `device.os.type` |
| `device.browser` | `BrowserType` | new signal — unusual browser per user |
| `device.is_compliant` | `IsCompliant` | Intune compliance |
| `device.is_compliant_and_managed` | `IsCompliantAndManaged` | |
| `device.trust_type` | `TrustType` | Entra joined / registered / hybrid |
| `device.session_uid` | `SessionId` | correlates a sign-in burst |

Emit booleans as real booleans. The 2026-07-27 notes already flag `device.is_managed` arriving as `True`/`true`/`False`/`false` — same trap applies to `IsCompliant`.

### Gap 2 — Grafana alert rule (the actual blocker)

`Identity Alert Hook` can only ever see what the rule emits as labels. Two changes:

1. Add the device fields above to the alert rule's label set (folder `SOC/Identity`, the Duo-Low rule is `cfq3ya3btmry8d`).
2. There appears to be **no Entra-sourced identity alert rule at all** — every firing so far is `- Duo -`. The Entra "Unexpected country" and "Infra/VPN IP" signals exist on the Anomalous Logins wallboard but do not appear to have an alerting counterpart pointed at this webhook. Worth confirming in Grafana.

Watch the cardinality: `device.uid` and `device.session_uid` are high-cardinality and will fragment Alertmanager grouping if used as grouping labels. Carry them as annotations, or keep grouping on `email`/`alertname` only.

### Gap 3 — `Build Alert` code node (small, mechanical)

Once labels arrive, the node needs new `related_events` entries and observables. It follows an obvious existing pattern, so the change is additive:

- new `related_events` of type `Device` — message `DisplayName`, carrying observables for device uid, OS, browser, trust type
- a `Non-Compliant Device Detection` event, High when `IsCompliant` is false — mirroring the existing proxy/hosting pattern
- an `Unmanaged Device Detection` event on `device.is_managed`
- a device observable in top-level `observables[]` so it is pivotable in the S1 console
- add a `Device` entry to `resources[]` alongside the existing `Email` entry

Severity today keys only off the alertname suffix. If a non-compliant or unmanaged device should escalate an otherwise-Low alert, that logic goes here too.

---

## 4. Other things noticed (not asked for, no action taken)

1. **Webhook is unauthenticated.** `Webhook - Medium/High` has `options: {}` — no header auth, no basic auth. Anything that can reach `10.10.99.13:5678` can inject an arbitrary OCSF finding into the S1 console. Low risk on an internal network; worth a header-auth credential regardless.
2. **Duo pull has no overlap window.** Hourly schedule, exactly 60 minutes of lookback, no watermark. Any run that is late, slow, or fails drops events permanently. Compare to the Microsoft pull, which uses a 12-hour lookback every 60 seconds — heavy overlap, but it cannot lose data.
3. **1,440 executions/day from the Microsoft branch alone** (60s schedule) against a 3,401-execution history on that workflow. This dominates the instance's 31,811 executions and the pruning window.
4. **Instance is titled `n8n[DEV]`** but every workflow is Published/active and clearly in production.
5. **`enrich=true` is passed only on the SentinelOne datalake call.** The Duo call does not pass it, yet Duo records come back enriched on `auth_device`. Enrichment behaviour is inconsistent across Simvay API endpoints — worth confirming with James which endpoints enrich by default, since that determines whether the `access_device` ask is a flag or a code change.
6. **Archived `S1 Push/Pull`** still exists with 0 nodes; harmless.
7. **`Loop Over Items` output 0 is unwired**, so the "done" branch of the batch loop goes nowhere. Functionally fine here, but it means the workflow has no completion/summary step.

---

## 6. Follow-up (2026-07-31): does Microsoft give us both the source device and the auth device?

Verified directly against VictoriaLogs (`10.10.100.12:9428`), 7-day window.

### Answer: no — Microsoft gives one device, and it is the source device.

The complete field list for the Microsoft stream is 26 fields, and there is exactly one device in it:

```
_msg  _stream  _stream_id  _time  path  source_type  timestamp
actor.user.email_addr
device.ip.as  device.ip.city  device.ip.continent  device.ip.country
device.ip.hosting  device.ip.isp  device.ip.lat  device.ip.lon
device.ip.mobile  device.ip.org  device.ip.proxy  device.ip.query  device.ip.regionName
device.is_managed  device.os.type  device_attributes
metadata.product.vendor_name  metadata.uid
```

No second IP, no second device object, no MFA-method or auth-app field. `metadata.original_time` and `type_name` are requested in the n8n query but do **not** survive into VictoriaLogs — the parser drops them and substitutes `timestamp`.

This is not a collection gap that better columns would fix. Entra sign-in logs record one client IP per sign-in. Microsoft has no `auth_device` concept in this schema — where the second endpoint exists at all, it exists because Duo brokered the MFA, and it is already in the Duo stream.

### Why that is the right answer anyway

Duo's enrichment is on the wrong endpoint. The rich, geo-enriched object is `auth_device` — the phone. The workstation (`access_device`) is the thin one. Microsoft is the mirror image: its single device is the source device, and it is the fully-enriched one.

**Coverage, 7 days, measured:**

| Signal | Duo (`_msg:authentication`, n=21,394) | Entra (`vendor_name:Microsoft`, n=12,335) |
|---|---|---|
| Source-device IP present | 21,393 (100%) — but **2,895 (14%) are `0.0.0.0`** | 12,344 (100%) |
| Source-device geo (lat/lon) | **0** | 12,344 (**100%**) |
| Source-device hostname / name | 3,585 (17%) | 7,107 (58%, `DisplayName`) |
| Source-device OS | — | 12,344 (100%, `device.os.type`) |
| Source-device browser | — | 11,801 (96%, `BrowserType`) |
| Device GUID | `epkey` (opaque, Duo-internal) | 11,801 (96%, Entra `Id`) |
| Compliance / trust | `trusted_endpoint_status`: 97% `unknown`, 601 `trusted`, 62 `not trusted` | `IsCompliant` 96%, `TrustType` 58%, `is_managed` 100% |
| User email | 4,349 (**20%** — the rest carry only `user.name`) | 12,344 (100%) |
| 2FA-device geo | 3,386 (16%) | n/a — no auth device |

Entra beats Duo on every source-device dimension, usually by a lot. The one thing Duo has that Entra does not is the second endpoint — and that is only useful for the geo-mismatch signal, which today runs off a state-string comparison on 16% of events.

### The actual blocker: `device_attributes` is stored as an unparsed string

It reaches VictoriaLogs intact, but as a JSON string in a single field:

```
device_attributes: "[{\"Name\":\"Id\",\"Value\":\"931676de-…\"},{\"Name\":\"DisplayName\",\"Value\":\"L345\"},
                     {\"Name\":\"OS\",\"Value\":\"Windows\"},{\"Name\":\"BrowserType\",\"Value\":\"Other\"},
                     {\"Name\":\"IsCompliant\",…},{\"Name\":\"TrustType\",…},{\"Name\":\"SessionId\",…}]"
```

Nothing can group or alert on `BrowserType` or `IsCompliant` until this is flattened. Two options:

1. **At the parser (preferred)** — flatten to `device.uid`, `device.name`, `device.browser`, `device.is_compliant`, `device.trust_type`, `device.session_uid`. Costs one change, fixes every consumer. This supersedes the "confirm it isn't dropped" item in §3 Gap 1.
2. **In LogsQL** — `unpack_json` / `extract` at query time. Works today with no upstream change, but has to be repeated in every panel and every alert rule.

Also worth fixing at the same time: `device.is_managed` arrives as four distinct values — `True` (4,343), `False` (7,458), `true` (118), `false` (403), plus 13 empty. Normalize to a boolean at the parser.

### Consequence for a Duo ↔ Entra join

Correlating the two sources on user is only partly viable today: **only 20% of Duo events carry `email`.** The rest have `user.name`, which is a short username (`tothn`, `fabrizia`) with no domain. Any join keyed on email silently drops 80% of the Duo side. A `user.key` → email mapping, or emitting `email` on every Duo record, would be needed first.

---

## 7. Follow-up (2026-07-31): queried the SentinelOne datalake directly — most of it is dropped, not missing

Ryan's call was right. I ran the **same filter with the `columns` restriction removed** against `POST /sentinelone/datalake/queryall` on the Simvay API. Read-only queries only; the `unifiedalerts/ingest` endpoint was not touched.

**The n8n query requests 9 columns. The records carry 66.** Fifty-seven fields are being discarded at the collector.

Also confirmed from `/openapi.json`: **`enrich` defaults to `true`** on both `/sentinelone/datalake/queryall` and `/duo/authlogs`. The explicit `enrich=true` in the n8n node is redundant, and the Duo endpoint enriches whether or not it is asked to. That closes open question #3.

### 7.1 The big one: we are enriching the wrong IP

Every Entra record carries **two** IP fields, and enrichment is applied to only one of them:

| | `device.ip` | `src_endpoint.ip` |
|---|---|---|
| Collected today | yes | **no — dropped** |
| ip-api enriched | yes (object) | no (plain string) |
| Coverage (12h, n=790) | 100% | **100%** |
| On `UserLoggedIn` records (764) | real client IP | identical to `device.ip` |
| On `SignInEvent` records (26) | **Microsoft service IP** | **real client IP** |

Live example from the last 12 hours:

```
device.ip        = 2a01:111:2053:120b:0:afd:ad4:4ad0
                   → enriched to country "Canada", isp "Microsoft Corporation"
src_endpoint.ip  = 67.144.164.6           ← the actual user, unenriched, discarded
```

**This is the root cause of the Canada false positives.** The 2026-07-27 status doc records ~400 bogus "Canada" hits for greatlakesbrewing.com alone, worked around with a mandatory `!device.ip.isp:("Microsoft Corporation" OR "Microsoft Limited")` exclusion inlined into panels 13, 15, 20, 30 and 31. That exclusion is compensating for enriching a Microsoft service IP instead of the client IP.

Rate measured: 21 of 790 records in 12 hours (2.7%) have `device.ip` in a Microsoft range, and **all 21 have a usable `src_endpoint.ip`.** That is roughly 40/day — the right order of magnitude for the 30-day false-positive count.

**Ask for James:** enrich `src_endpoint.ip`, or coalesce `src_endpoint.ip → device.ip` before enrichment. If that lands, the five-panel Microsoft exclusion can be deleted rather than maintained, and those sign-ins become real data instead of suppressed noise.

### 7.2 Failed logins exist and are 100% excluded

`unmapped.Operation='UserLoginFailed'` returns **304 events in 24 hours**. None of them reach VictoriaLogs, because the n8n filter excludes them **twice over**:

- `event.type = 'Logon'` — failures are not typed `Logon`
- `device.ip = *` — failure records have **no** `device.ip` and no `src_endpoint.ip` at all; the client IP is in `unmapped.ActorIpAddress`

Top failure reasons, 24 hours, all tenants:

| `unmapped.LogonError` | AADSTS | Count | Why it matters |
|---|---|---|---|
| `IdsLocked` | 50053 | **83** | smart lockout fired — active spray / brute force |
| `InvalidUserNameOrPassword` | 50126 | 81 | the spray itself |
| `UserStrongAuthClientAuthNRequiredInterrupt` | 50074 | 57 | MFA interrupt |
| `UserDisabled` | 50057 | **25** | sign-in attempts against disabled accounts |
| `ExternalSecurityChallenge` | 50158 | 15 | |
| `FlowTokenExpired` | 500121 | 8 | |

Top source IPs on failures: `23.244.10.130` (61), `76.8.81.194` (29), `2600:382:dd0c:…` (14), `38.122.61.234` (7), `45.141.215.124` (3).
Most-targeted accounts: `asimanella139719@polaris.edu` (27), `michelleb@greatlakesbrewing.com` (13), `tstohr@cc-efi.com` (13), `tp.admin@polaris.edu` (9).

83 lockouts and 25 disabled-account attempts in a single day is a live signal we have no visibility on. Password spray, credential stuffing, and failure-side impossible travel are all undetectable today. Failed logins need a **second pull** with its own filter and its own IP field — not a widening of the existing one.

### 7.3 Useful fields available and currently dropped

Coverage measured over 790 records / 12 hours:

| Field | Coverage | Why it is worth collecting |
|---|---|---|
| `src_endpoint.ip` | **100%** | true client IP — see §7.1 |
| `device.is_compliant` | 97% | first-class field; no JSON-string parsing needed, unlike `DeviceProperties` |
| `actor.user.uid` | 97% | Entra object GUID — a stable join key, far better than email |
| `actor.session.uid` | 99% | ties a sign-in burst together; matches `SessionId` in DeviceProperties |
| `status_id` / `status_detail` | 100% / 97% | **Entra does have a success/failure field** — this corrects finding #10 in the 2026-07-27 status doc |
| `metadata.correlation_uid` | 100% | correlate related sign-in events |
| `dst_endpoint.uid` | 97% | which tenant/app was accessed |
| `device.os.type_id` | 99% | numeric OS, no casing problems |
| `unmapped.ExtendedProperties` | 97% | carries `UserAgent`, `UserAuthenticationMethod`, `RequestType` |
| `http_request.user_agent` | 3% | full UA string — `SignInEvent` records only |
| `unmapped.BrowserName` / `BrowserVersion` | 3% | parsed browser + version, better than `BrowserType` |
| `unmapped.AuthenticationType` | 3% | e.g. `FormsCookieAuth` |
| `unmapped.GeoLocation` | 3% | Microsoft's own region code |

The 3%-coverage fields are all `SignInEvent`-only; the 97%+ fields are on `UserLoggedIn`. The two record types have genuinely different shapes, which is worth knowing before anyone writes a panel that assumes a field is always there.

`device.is_compliant` deserves special mention: it is a real field at 97% coverage, and today the same value is being read by string-parsing `DeviceProperties`. Adding one column removes the need for the flattening work in §6 for that particular field.

### 7.4 Revised recommendation

The §6 conclusion stands — Microsoft has no auth device, only a source device. But the ordering of work changes, because the cheapest fixes are now the highest-value ones:

1. **Add `src_endpoint.ip` to the column list** and ask James to enrich it. Kills the Canada false positives at the source and retires a five-panel workaround. *(One-line n8n change + one API change.)*
2. **Add a second Entra pull for `UserLoginFailed`** with its own filter and `unmapped.ActorIpAddress` as the IP. Unlocks spray/lockout/disabled-account detection. *(New n8n branch.)*
3. **Add `device.is_compliant`, `actor.user.uid`, `actor.session.uid`, `status_id`, `status_detail`, `metadata.correlation_uid`, `unmapped.ExtendedProperties` to the column list.** *(One-line n8n change.)*
4. **Then** flatten `device_attributes` at the parser (§6) for the fields that have no first-class equivalent — `DisplayName`, `TrustType`, `BrowserType`.
5. **Then** promote the device fields into Grafana alert labels and extend `Build Alert` (§3).

Steps 1 and 3 are edits to a single `columns` string in one n8n node.

---

## 5. Open questions for James

1. ~~Does the parser at `10.10.100.13:9001` forward `device_attributes`?~~ **Answered: yes, but as an unparsed JSON string.** The live ask is: can it flatten `device_attributes` into discrete fields, normalize `device.is_managed` to a boolean, and stop dropping `metadata.original_time` / `type_name`?
2. Why does the Microsoft path go through a "temporary" parser instead of posting to `9428` directly like every other collector? Is that meant to be retired?
2b. Can every Duo record carry `email`? Only 20% do today, which caps any Duo ↔ Entra correlation at 20% of the Duo side.
3. ~~Which Simvay API endpoints apply ip-api enrichment by default?~~ **Answered from `/openapi.json`: `enrich` defaults to `true` on both `/duo/authlogs` and `/sentinelone/datalake/queryall`.** The live ask is §7.1 — can enrichment be applied to `src_endpoint.ip` (or a `src_endpoint.ip → device.ip` coalesce) instead of `device.ip` alone?
3b. `/duo/authlogs` has a `limit` parameter defaulting to **100**, and the n8n node does not pass one. At ~127 Duo auth events/hour average, an hourly pull capped at 100 would be truncating. Is the limit per-tenant or global? This may be a second, independent cause of the 15% geo-coverage gap.
4. Is there an Entra-sourced Grafana alert rule pointed at the `638bd38a` webhook, or is that hook Duo-only by design?
5. Is `trusted_endpoint_status` expected to be `"unknown"` on 100% of Duo records, or is the Duo Trusted Endpoints integration not configured?
6. Still open from 2026-07-27: why do only 15% of Duo auth events carry `auth_device` geo?
