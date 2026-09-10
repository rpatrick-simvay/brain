#!/usr/bin/env python3
"""v2 analysis for the Simvay monthly sales report (Aug 2026 run).

Extends the synced analyze.py with the v2 rules from the task spec:
  * five revenue-mix lines: advisory / mtcontracts / cyberrec / saas / onetime
  * category axis (Cybersecurity vs Managed Technology) independent of bucket
  * PRODUCT-only cost basis: ticket-raised time and labour-only service plans
    are stripped from cost; vendor/hardware cost is kept
  * cost anomalies split into three kinds (one-off multi-period / persistent
    defect / order split)
  * per-invoice profitability for the focus month from the Invoice API lines
  * billed hours (report 290) by team -> internal delivery cost @ $150/h and
    a fully-loaded margin CEILING
"""
import argparse, collections, glob, json, os, re

# ---------- classification ----------
CYB = re.compile(
    r"ECRM|FISM|\bISM\b|FCISO|SentinelOne|Singularity|Simgularity|\bS1\b|WatchTower|Wayfinder|XDR|MEDR|EMDR|"
    r"Simvay - A1|\bA1\b|\bDuo\b|Mimecast|KnowBe4|\bKB4\b|PhishER|Security Awareness|Umbrella|"
    r"\bSRM\b|\bC2\b|\bNDR\b|Managed Detection|SOC MDR|Security Operations? Center|"
    r"Threat Intelligence|AI SIEM|Identity Detection|Configuration, Ingest|"
    r"Secure Endpoint|Complete Protection|Cloud Workload Security|Purple AI|"
    r"Vulnerability and Patch|Data Retention|\|\s*Security\b|DISCOUNT - K-12", re.I)
ADV = re.compile(r"ECRM|FISM|\bISM\b|FCISO", re.I)
MTC = re.compile(r"Managed Services - (EMTS|EMNS|MSA|MTS)|Financed Solution|Managed Technology Services|"
                 r"^(MSA|EMTS|EMNS|MTS)\s*\|(?!.*Security)|Auvik|Monitoring Per Billable Device|"
                 r"^Professional Services \{", re.I)
SAAS = re.compile(r"\(NCE\)|M365|Microsoft 365|Exchange Online|Visio|Umbrella|Adobe|Acrobat|VEEAM|"
                  r"Intune|Entra|Copilot|Synology Managed Cloud|Plate Recognizer|Parkpow|^Internet \{", re.I)
SUBPROD = re.compile(r"KnowBe4|\bKB4\b|PhishER|Security Awareness|\bSRM\b|\bDuo\b|Umbrella|"
                     r"Mimecast|SentinelOne|Singularity|Simgularity|WatchTower|Wayfinder|\bA1\b|VEEAM|\bC2\b|Adobe|"
                     r"\(NCE\)|M365|Auvik|Secure Endpoint|Complete Protection|Cloud Workload|"
                     r"Vulnerability and Patch", re.I)
SUBTERM = re.compile(r"Subscription|\b\d+\s*months?\b|\byear term\b|\bProrated\b", re.I)
KB4EXACT = re.compile(r"^Security Awareness Training\s*$")
# large one-time license buy-outs even with term wording (Webex 36-month precedent, hardware-attached Meraki)
ONETIME_OVERRIDE = re.compile(r"Webex|Meraki", re.I)

FAMILIES = [
    ("Advisory Services (ECRM · FISM · ISM · FCISO)", r"ECRM|FISM|\bISM\b|FCISO"),
    ("KnowBe4 / Security Awareness", r"KnowBe4|\bKB4\b|PhishER|Security Awareness"),
    ("A1 (vuln & patch mgmt)", r"Simvay - A1|\bA1\b|Vulnerability and Patch"),
    ("Cyber Operations (SOC · SentinelOne · MEDR)",
     r"SentinelOne|Singularity|Simgularity|WatchTower|Wayfinder|XDR|MEDR|EMDR|Secure Endpoint|Complete Protection|"
     r"Cloud Workload|AI SIEM|Identity Detection|Data Retention|Purple AI|Managed Detection|SOC MDR|"
     r"Security Operations? Center|Threat Intelligence|Configuration, Ingest|\|\s*Security\b|DISCOUNT - K-12|\bS1\b"),
    ("Umbrella (DNS security)", r"Umbrella"),
    ("Mimecast (email security)", r"Mimecast"),
    ("Duo (MFA)", r"\bDuo\b"),
    ("SRM (compliance portal)", r"\bSRM\b"),
    ("C2 (secure cloud storage)", r"\bC2\b"),
]

# ---------- cost basis ----------
# (1) ticket-raised time (Halo values at agent cost)
TICKET_TIME = re.compile(r"(Remote|On-Site|Onsite) Support - ID:|Time Taken", re.I)
# (2) labour-only service plans: cost field holds an internal hours estimate
LABOUR_PLAN = re.compile(r"^(ECRM|EMTS|EMNS|MTS|ISM|FISM|FCISO)\s*\||Managed Services - (ECRM|EMTS|EMNS|MTS|ISM|FISM|FCISO)|"
                         r"MSA\s*\|.*Technology|Managed Technology Services - Hours|^MSA\s*\|\s*Monthly\s*\{|"
                         r"Managed Services - MSA\s*\|\s*Monthly", re.I)
# (3) one-off labour lines sold with an internal hourly estimate
LABOUR_LINE = re.compile(r"Per Hour Labou?r|Pre-Delivery Prep|Laptop Install", re.I)


def labour_kind(desc):
    if TICKET_TIME.search(desc):
        return "ticket_time"
    if LABOUR_PLAN.search(desc):
        return "labour_plan"
    if LABOUR_LINE.search(desc):
        return "labour_line"
    return None


def net(r):
    return float(r["Order Line - Unit Price"]) * float(r["Order Line - Count"])


def is_cyber(d):
    return bool(CYB.search(d) or KB4EXACT.match(d))


def is_recurring(d):
    if ONETIME_OVERRIDE.search(d) and "{" not in d:
        return False
    return "{" in d or bool(SUBPROD.search(d) and SUBTERM.search(d)) or bool(KB4EXACT.match(d))


def base_bucket(d):
    if not is_recurring(d):
        return "onetime"
    if ADV.search(d):
        return "advisory"
    if MTC.search(d):
        return "mtcontracts"
    if SAAS.search(d) and not re.search(r"Mimecast|Duo|KnowBe4", d, re.I):
        return "saas"
    if is_cyber(d):
        return "cyberrec"
    return "saas"


def family_of(d):
    for name, pat in FAMILIES:
        if re.search(pat, d, re.I):
            return name
    return "Other cybersecurity"


def pieces(r, allocations, month):
    d = r["Order Line - Description"]
    v = net(r)
    for alloc in allocations:
        if (r.get("Client Name") == alloc["client"] and re.search(alloc["line_pattern"], d)
                and month >= alloc.get("effective_from", "0000-00")):
            total = sum(p["amount"] for p in alloc["split"])
            scale = 1.0 if abs(v - total) <= 0.01 else (v / total if total else 0)
            for p in alloc["split"]:
                yield (p["bucket"], p["cyber"], p["amount"] * scale, p.get("family"))
            return
    yield (base_bucket(d), is_cyber(d), v, None)


MONNAME = {"01": "January", "02": "February", "03": "March", "04": "April", "05": "May", "06": "June",
           "07": "July", "08": "August", "09": "September", "10": "October", "11": "November", "12": "December"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir")
    ap.add_argument("--config", required=True)
    ap.add_argument("--focus", required=True)
    args = ap.parse_args()
    cfg = json.load(open(args.config))
    allocations = cfg.get("allocations", [])
    threshold = cfg.get("prepaid_cost_ratio_threshold", 1.5)
    corrections = cfg.get("cost_corrections", [])
    rate = cfg["internal_hourly_cost"]
    team_map = cfg["team_category_map"]
    hours_excl = set(cfg.get("hours_exclude_clients", []))

    months = {}
    for path in sorted(glob.glob(os.path.join(args.data_dir, "lines_*.json"))):
        months[os.path.basename(path)[6:-5]] = json.load(open(path))
    profit = json.load(open(os.path.join(args.data_dir, "profit_rows.json")))
    hours = json.load(open(os.path.join(args.data_dir, "hours_rows.json")))
    inv_api = json.load(open(os.path.join(args.data_dir, "inv_aug.json")))

    out, audit = {}, []
    for mkey, rows in months.items():
        b, c, fams = collections.Counter(), collections.Counter(), collections.Counter()
        clients = collections.defaultdict(lambda: [0.0, 0.0])
        cb = collections.Counter()
        for r in rows:
            for bk, cy, v, fam in pieces(r, allocations, mkey):
                cb[(r["Client Name"], bk)] += v
                b[bk] += v
                c["cyber" if cy else "mt"] += v
                clients[r["Client Name"]][0 if cy else 1] += v
                if cy:
                    fams[fam or family_of(r["Order Line - Description"])] += v
            if abs(net(r)) >= 200:
                audit.append(f"{mkey} {base_bucket(r['Order Line - Description']):11s} {'CYB' if is_cyber(r['Order Line - Description']) else 'MT ':3s} "
                             f"{net(r):>11,.2f}  {r['Client Name'][:22]:22s} {r['Order Line - Description'][:80]}")
        tot = sum(b.values())
        assert abs(c["cyber"] + c["mt"] - tot) < 0.01

        # ---- month-level cost from report 168, product-only ----
        pk = f"{mkey[:4]} {MONNAME[mkey[5:7]]}"
        mprofit = [p for p in profit if p.get("Date") == pk]
        cost_recorded = sum(float(p["Cost"]) for p in mprofit)
        labour = collections.Counter()
        labour_detail = []
        product_cost = 0.0
        prod_rows = []
        for p in mprofit:
            cst = float(p["Cost"])
            lk = labour_kind(p["Description"])
            if lk:
                labour[lk] += cst
                if abs(cst) >= 1:
                    labour_detail.append({"kind": lk, "client": p["Customer"], "description": p["Description"][:80], "cost": cst})
            else:
                product_cost += cst
                prod_rows.append(p)
        # ---- anomalies: three kinds ----
        one_off, persistent = [], []
        persist_excess = 0.0
        for p in prod_rows:
            rev, cst = float(p["Revenue"]), float(p["Cost"])
            hit = None
            for corr in corrections:
                if corr.get("kind") == "persistent_defect" and p["Customer"] == corr["client"] and re.search(corr["line_pattern"], p["Description"]) \
                        and corr["effective_from"] <= mkey:
                    hit = corr
            if hit and cst > 0:
                persistent.append({"client": p["Customer"], "description": p["Description"][:80], "revenue": rev, "cost": cst,
                                   "past_effective_through": mkey > hit["effective_through"]})
                persist_excess += cst - rev if cst > rev else 0
            elif rev > 500 and cst > rev * threshold:
                one_off.append({"client": p["Customer"], "description": p["Description"][:90], "revenue": rev, "cost": cst,
                                "ratio": round(cst / rev, 2)})
        one_off_excess = sum(a["cost"] - a["revenue"] for a in one_off)
        # persistent-defect cost is reported separately and excluded entirely from adjusted cost
        persist_cost = sum(a["cost"] for a in persistent)
        gp = tot - product_cost
        gp_adj = gp + one_off_excess + persist_cost
        # correction expiry check
        expired_firing = []
        for corr in corrections:
            if corr.get("kind") == "persistent_defect":
                continue
            for p in mprofit:
                if p["Customer"] == corr["client"] and re.search(corr["line_pattern"], p["Description"]) and float(p["Cost"]) > 0 \
                        and mkey > corr["effective_through"]:
                    expired_firing.append({"client": corr["client"], "description": p["Description"][:80], "cost": float(p["Cost"]),
                                           "effective_through": corr["effective_through"]})

        # ---- hours ----
        hrows = [h for h in hours if h["Month"] == mkey]
        by_team = collections.defaultdict(lambda: [0.0, 0.0])
        excl_hours = 0.0
        by_client = collections.defaultdict(float)
        for h in hrows:
            if h["Client"] in hours_excl:
                excl_hours += float(h["Hours"])
                continue
            by_team[h["Team"]][0] += float(h["Hours"])
            by_team[h["Team"]][1] += float(h["Labour Cost"])
            by_client[h["Client"]] += float(h["Hours"])
        by_cat = collections.Counter()
        for t, (hh, _) in by_team.items():
            by_cat[team_map.get(t, "unmapped")] += hh
        tot_hours = sum(v[0] for v in by_team.values())
        delivery_cost = tot_hours * rate
        fl_margin = gp - delivery_cost
        fl_margin_adj = gp_adj - delivery_cost

        out[mkey] = {
            "total": round(tot, 2), "cost_recorded": round(cost_recorded, 2),
            "labour_stripped": {k: round(v, 2) for k, v in labour.items()}, "labour_detail": labour_detail,
            "cost": round(product_cost, 2), "gp": round(gp, 2), "gp_pct": round(gp / tot * 100, 1) if tot else 0,
            "gp_adjusted": round(gp_adj, 2), "gp_adjusted_pct": round(gp_adj / tot * 100, 1) if tot else 0,
            "one_off_anomalies": one_off, "one_off_excess": round(one_off_excess, 2),
            "persistent_defects": persistent, "persistent_cost": round(persist_cost, 2),
            "expired_corrections_firing": expired_firing,
            "recurring": round(tot - b["onetime"], 2),
            "advisory": round(b["advisory"], 2), "mtcontracts": round(b["mtcontracts"], 2),
            "cyberrec": round(b["cyberrec"], 2), "saas": round(b["saas"], 2), "onetime": round(b["onetime"], 2),
            "cyber": round(c["cyber"], 2), "mt": round(c["mt"], 2),
            "invoices": len({r["Invoice No"] for r in rows}), "lines": len(rows),
            "cyber_families": {k: round(v, 2) for k, v in fams.most_common() if round(v, 2) != 0},
            "top_clients": [[k, round(v[0], 2), round(v[1], 2)]
                            for k, v in sorted(clients.items(), key=lambda kv: -(kv[1][0] + kv[1][1]))[:10]],
            "client_bucket": [[c, bk, round(v, 2)] for (c, bk), v in cb.items()],
            "profit_report_revenue": round(sum(float(p["Revenue"]) for p in mprofit), 2),
            "hours": {"total": round(tot_hours, 2), "excluded_internal": round(excl_hours, 2),
                      "by_team": {t: [round(v[0], 2), round(v[1], 2)] for t, v in sorted(by_team.items())},
                      "by_category": {k: round(v, 2) for k, v in by_cat.items()},
                      "top_clients": sorted(((k, round(v, 2)) for k, v in by_client.items()), key=lambda kv: -kv[1])[:10],
                      "delivery_cost": round(delivery_cost, 2), "rate": rate},
            "fl_margin": round(fl_margin, 2), "fl_margin_pct": round(fl_margin / tot * 100, 1) if tot else 0,
            "fl_margin_adj": round(fl_margin_adj, 2), "fl_margin_adj_pct": round(fl_margin_adj / tot * 100, 1) if tot else 0,
        }
        assert abs(sum(b.values()) - tot) < 0.01
        if mprofit and abs(out[mkey]["profit_report_revenue"] - tot) > 5:
            print(f"WARNING {mkey}: 288 total {tot:,.2f} vs 168 revenue {out[mkey]['profit_report_revenue']:,.2f} differ > $5")

    # ---- per-invoice profitability for the focus month (Invoice API lines) ----
    fm = args.focus
    rows288 = months[fm]
    rev_by_inv = collections.defaultdict(float)
    for r in rows288:
        rev_by_inv[int(r["Invoice No"])] += net(r)
    inv_out = []
    tot_prod_cost = 0.0
    labour_by_inv = []
    for k, v in sorted(inv_api.items(), key=lambda kv: int(kv[0])):
        pc, lab = 0.0, 0.0
        buckets = collections.Counter()
        cy = 0.0
        for l in v["lines"]:
            cst = (l["unit_cost"] or 0) * (l["qty_order"] or 0)
            if l["ticket_id"] and l["ticket_id"] > 0:
                lab += cst
                if cst: labour_by_inv.append((int(k), v["client"], "ticket_time", l["item_shortdescription"][:70], cst))
            elif labour_kind(l["item_shortdescription"]):
                lab += cst
                if cst: labour_by_inv.append((int(k), v["client"], labour_kind(l["item_shortdescription"]), l["item_shortdescription"][:70], cst))
            else:
                pc += cst
        for r in [x for x in rows288 if int(x["Invoice No"]) == int(k)]:
            for bk, cyf, amt, fam in pieces(r, allocations, fm):
                buckets[bk] += amt
                if cyf: cy += amt
        rev = rev_by_inv[int(k)]
        tot_prod_cost += pc
        kind = "Order" if v.get("type") == 2 else ("Contract" if (v.get("contract_ref") or any((l.get("contract_id") or 0) > 0 for l in v["lines"])) else "Ad hoc")
        inv_out.append({"invoice": int(k), "date": v["invoice_date"][:10], "client": v["client"], "kind": kind,
                        "contract_ref": v.get("contract_ref") or "", "revenue": round(rev, 2), "cost": round(pc, 2),
                        "labour_stripped": round(lab, 2), "gp": round(rev - pc, 2),
                        "gp_pct": round((rev - pc) / rev * 100, 1) if rev else None,
                        "cyber": round(cy, 2), "mt": round(rev - cy, 2),
                        "bucket": max(buckets, key=buckets.get) if buckets else "", "lines": len(v["lines"])})
    month = out[fm]
    checks = {
        "appendix_c_total": round(sum(i["revenue"] for i in inv_out), 2), "month_total": month["total"],
        "appendix_c_invoices": len(inv_out), "month_invoices": month["invoices"],
        "cost_attribution_pct": round(tot_prod_cost / month["cost"] * 100, 1) if month["cost"] else None,
        "per_invoice_gp_sum": round(sum(i["gp"] for i in inv_out), 2), "month_gp": month["gp"],
        "api_revenue_total": round(sum(v["revenue"] for v in inv_api.values()), 2),
        "api_cost_total": round(sum((l["unit_cost"] or 0) * (l["qty_order"] or 0) for v in inv_api.values() for l in v["lines"]), 2),
        "r168_cost_total": month["cost_recorded"],
    }
    out["_focus"] = fm
    out["_invoices"] = inv_out
    out["_invoice_labour_stripped"] = labour_by_inv
    out["_checks"] = checks
    json.dump(out, open(os.path.join(args.data_dir, "analysis.json"), "w"), indent=1)
    open(os.path.join(args.data_dir, "audit.txt"), "w").write("\n".join(audit))
    for mkey, v in out.items():
        if mkey.startswith("_"): continue
        print(f"{mkey}: total={v['total']:,.0f} rec={v['recurring']:,.0f} cyber={v['cyber']:,.0f} "
              f"cost_rec={v['cost_recorded']:,.0f} cost_prod={v['cost']:,.0f} gp={v['gp']:,.0f} ({v['gp_pct']}%) "
              f"adj={v['gp_adjusted']:,.0f} ({v['gp_adjusted_pct']}%) hrs={v['hours']['total']} FL={v['fl_margin']:,.0f} ({v['fl_margin_pct']}%) "
              f"1off={len(v['one_off_anomalies'])} persist={len(v['persistent_defects'])}")
    print(json.dumps(checks, indent=1))


if __name__ == "__main__":
    main()
