# sales-report-v2-config.json

Saved 2026-09-01 from the August 2026 monthly sales report session. Copy into the simvay-monthly-sales-report skill (scripts/ or root) — the synced skill still carries the July build. See claude/HaloPSA-Runbook-17-Monthly-Sales-Report-v2.md.

```
{
  "brand": {
    "teal": "#00627B", "blue": "#6BBBD5", "slate": "#525E77", "ltgrey": "#A0A0A0",
    "mid": "#3B96B5", "ink": "#2B3440", "muted": "#6B7480", "tint": "#F0F7FA",
    "edge": "#BFD9E2", "line": "#DDE4E9"
  },
  "allocations": [
    {
      "note": "GLB MSA $12,000/mo carve-out per Ryan Patrick 2026-07-16",
      "client": "Great Lakes Brewing",
      "line_pattern": "Managed Services - MSA\\s*\\|",
      "effective_from": "2026-04",
      "split": [
        {"bucket": "advisory",    "cyber": true,  "amount": 3500.0, "family": "Advisory Services (ECRM · FISM · ISM · FCISO)"},
        {"bucket": "cyberrec",    "cyber": true,  "amount": 4000.0, "family": "Cyber Operations (SOC · SentinelOne · MEDR)"},
        {"bucket": "mtcontracts", "cyber": false, "amount": 4500.0, "family": null}
      ]
    }
  ],
  "prepaid_cost_ratio_threshold": 1.5,
  "internal_hourly_cost": 150.0,
  "hours_report_id": 290,
  "team_category_map": {
    "Cyber Ops (Analysts)": "Cybersecurity",
    "Cyber Ops (Mgmt)": "Cybersecurity",
    "Support (Sys Admins)": "Managed Technology",
    "Support (Mgmt)": "Managed Technology"
  },
  "hours_exclude_clients": ["Simvay"],
  "cost_corrections": [
    {
      "note": "Russell Township 'MSA | Monthly | Technology' recurring line carries unit_cost 21,000 on a 1,750 monthly line (12x the monthly price). Labour-only plan, so it is stripped as labour regardless; recorded here so the report can say whether the Halo template fix has taken. Observed 2026-07 and 2026-08 invoices (this run). effective_through is unknown to this run — the synced skill copy does not carry the dated block.",
      "client": "Russell Township",
      "line_pattern": "MSA\\s*\\|\\s*Monthly\\s*\\|\\s*Technology",
      "effective_from": "2026-07",
      "effective_through": "2026-07"
    },
    {
      "note": "Bober Markey Fedorovich SentinelOne component lines carried ANNUAL vendor cost on each MONTHLY invoice (~$17.6k/mo cost vs ~$3.5k/mo revenue), Apr-Jul 2026. Persistent defect - reported separately, excluded from adjusted GP. August 2026 invoice carries unit_cost 0 on those lines (defect gone, but true monthly vendor cost is now unrecorded).",
      "client": "Bober Markey Fedorovich",
      "line_pattern": "SentinelOne Complete with Purple AI|WatchTower Real Time|90 Day Data Retention|SINGULARITY XDR PLATFORM|^Premium \\{",
      "effective_from": "2026-04",
      "effective_through": "2026-07",
      "kind": "persistent_defect"
    }
  ],
  "confidential_footer": "Simvay LLC — Internal / Confidential"
}
```
