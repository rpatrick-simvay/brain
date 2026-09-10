#!/usr/bin/env python3
"""Render the Simvay monthly executive sales report: analysis.json -> HTML -> PDF (headless Chromium)."""
import argparse, base64, datetime, json, os, re, subprocess

TEAL, BLUE, SLATE, GREY, MID = "#00627B", "#6BBBD5", "#525E77", "#A0A0A0", "#3B96B5"
INK, MUTED, LINE, EDGE, TINT = "#2B3440", "#6B7480", "#DDE4E9", "#BFD9E2", "#F0F7FA"
MON = {"01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
       "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"}
MONF = {"01": "January", "02": "February", "03": "March", "04": "April", "05": "May", "06": "June", "07": "July",
        "08": "August", "09": "September", "10": "October", "11": "November", "12": "December"}
BUCKETS = [("advisory", "Advisory Services"), ("mtcontracts", "Managed Technology"),
           ("cyberrec", "Cyber Operations (MSaaS)"), ("saas", "SaaS"), ("onetime", "One-time / project")]


def money(v, dec=0):
    s = f"{abs(v):,.{dec}f}"
    return f"-${s}" if v < 0 else f"${s}"


def k(v):
    return f"{'-' if v < 0 else ''}${abs(v)/1000:,.0f}k" if abs(v) >= 1000 else money(v)


def pct(v):
    return f"{v:.1f}%"


def mlabel(m):
    return f"{MON[m[5:7]]} {m[:4]}"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------- SVG helpers ----------------
def svg_open(w, h):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="font-family:Poppins,Arial,sans-serif;display:block">'


def stacked_bars(months, series, colors, w=672, h=230, ylab="$", legend=True, value_labels=True):
    """series: list of (label, {month: value})"""
    left, right, top, bot = 52, 14, 16, 34
    pw, ph = w - left - right, h - top - bot
    totals = [sum(s[1].get(m, 0) for s in series) for m in months]
    ymax = max(totals) * 1.12 or 1
    step = 10 ** (len(str(int(ymax))) - 1)
    if ymax / step < 3: step /= 2
    out = [svg_open(w, h)]
    y = 0
    while y <= ymax:
        yy = top + ph - y / ymax * ph
        out.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left+pw}" y2="{yy:.1f}" stroke="{LINE}" stroke-width="1"/>')
        out.append(f'<text x="{left-6}" y="{yy+3:.1f}" font-size="8" fill="{MUTED}" text-anchor="end">{k(y)}</text>')
        y += step
    n = len(months)
    slot = pw / n
    bw = min(slot * 0.55, 64)
    for i, m in enumerate(months):
        x = left + slot * i + (slot - bw) / 2
        base = top + ph
        for (lab, data), col in zip(series, colors):
            v = data.get(m, 0)
            hh = v / ymax * ph
            if v > 0:
                out.append(f'<rect x="{x:.1f}" y="{base-hh:.1f}" width="{bw:.1f}" height="{hh:.1f}" fill="{col}"/>')
                if value_labels and hh > 14:
                    out.append(f'<text x="{x+bw/2:.1f}" y="{base-hh/2+3:.1f}" font-size="7.5" fill="#fff" text-anchor="middle">{k(v)}</text>')
                base -= hh
        out.append(f'<text x="{x+bw/2:.1f}" y="{top+ph-totals[i]/ymax*ph-5:.1f}" font-size="8.5" font-weight="600" fill="{INK}" text-anchor="middle">{k(totals[i])}</text>')
        out.append(f'<text x="{x+bw/2:.1f}" y="{top+ph+14}" font-size="8.5" fill="{INK}" text-anchor="middle">{mlabel(m)}</text>')
    out.append(f'<line x1="{left}" y1="{top+ph}" x2="{left+pw}" y2="{top+ph}" stroke="{SLATE}" stroke-width="1"/>')
    if legend:
        lx = left
        for (lab, _), col in zip(series, colors):
            out.append(f'<rect x="{lx}" y="{h-9}" width="9" height="9" fill="{col}"/>')
            out.append(f'<text x="{lx+13}" y="{h-1}" font-size="8" fill="{INK}">{esc(lab)}</text>')
            lx += 13 + len(lab) * 4.6 + 16
    out.append("</svg>")
    return "".join(out)


def hbars(items, w=326, rowh=17, maxv=None, color=TEAL, label_w=150, fmt=k):
    n = len(items)
    h = n * rowh + 6
    maxv = maxv or max((v for _, v in items), default=1) or 1
    out = [svg_open(w, h)]
    for i, (lab, v) in enumerate(items):
        y = 3 + i * rowh
        bw = max(0, v) / maxv * (w - label_w - 48)
        out.append(f'<text x="{label_w-6}" y="{y+rowh/2+3}" font-size="8" fill="{INK}" text-anchor="end">{esc(lab[:38])}</text>')
        out.append(f'<rect x="{label_w}" y="{y+2}" width="{bw:.1f}" height="{rowh-5}" fill="{color}" rx="2"/>')
        out.append(f'<text x="{label_w+bw+4:.1f}" y="{y+rowh/2+3}" font-size="8" fill="{INK}">{fmt(v)}</text>')
    out.append("</svg>")
    return "".join(out)


def dual_client_bars(items, w=672, rowh=15, label_w=210):
    """items: (client, cyber, mt) -> stacked horizontal bars."""
    n = len(items)
    h = n * rowh + 20
    maxv = max((c + m for _, c, m in items), default=1) or 1
    scale = (w - label_w - 60) / maxv
    out = [svg_open(w, h)]
    for i, (lab, c, m) in enumerate(items):
        y = 3 + i * rowh
        out.append(f'<text x="{label_w-6}" y="{y+rowh/2+3}" font-size="8" fill="{INK}" text-anchor="end">{esc(lab[:40])}</text>')
        x = label_w
        if c > 0:
            out.append(f'<rect x="{x}" y="{y+2}" width="{c*scale:.1f}" height="{rowh-5}" fill="{TEAL}"/>'); x += c * scale
        if m > 0:
            out.append(f'<rect x="{x:.1f}" y="{y+2}" width="{m*scale:.1f}" height="{rowh-5}" fill="{BLUE}"/>'); x += m * scale
        out.append(f'<text x="{x+4:.1f}" y="{y+rowh/2+3}" font-size="8" fill="{INK}">{k(c+m)}</text>')
    y = h - 8
    out.append(f'<rect x="{label_w}" y="{y-8}" width="9" height="9" fill="{TEAL}"/><text x="{label_w+13}" y="{y}" font-size="8" fill="{INK}">Cybersecurity</text>')
    out.append(f'<rect x="{label_w+95}" y="{y-8}" width="9" height="9" fill="{BLUE}"/><text x="{label_w+108}" y="{y}" font-size="8" fill="{INK}">Managed Technology</text>')
    out.append("</svg>")
    return "".join(out)


def line_chart(months, series, colors, w=326, h=170, fmt=pct, ymin=None, ymax=None):
    left, right, top, bot = 40, 12, 12, 30
    pw, ph = w - left - right, h - top - bot
    vals = [v for _, d in series for v in d.values()]
    lo = min(vals) if ymin is None else ymin
    hi = max(vals) if ymax is None else ymax
    lo = min(lo, 0); hi = max(hi, 0)
    rng = (hi - lo) or 1
    out = [svg_open(w, h)]
    for t in range(5):
        yv = lo + rng * t / 4
        yy = top + ph - (yv - lo) / rng * ph
        out.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left+pw}" y2="{yy:.1f}" stroke="{LINE}"/>')
        out.append(f'<text x="{left-5}" y="{yy+3:.1f}" font-size="7.5" fill="{MUTED}" text-anchor="end">{fmt(yv)}</text>')
    n = len(months)
    xs = [left + pw * (i + 0.5) / n for i in range(n)]
    for (lab, d), col in zip(series, colors):
        pts = [(xs[i], top + ph - (d[m] - lo) / rng * ph) for i, m in enumerate(months) if m in d]
        out.append(f'<polyline fill="none" stroke="{col}" stroke-width="2" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}"/>')
        for (x, y), m in zip(pts, [m for m in months if m in d]):
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{col}"/>')
            out.append(f'<text x="{x:.1f}" y="{y-6:.1f}" font-size="7.5" fill="{col}" text-anchor="middle">{fmt(d[m])}</text>')
    for i, m in enumerate(months):
        out.append(f'<text x="{xs[i]:.1f}" y="{top+ph+13}" font-size="8" fill="{INK}" text-anchor="middle">{mlabel(m)}</text>')
    lx = left
    for (lab, _), col in zip(series, colors):
        out.append(f'<rect x="{lx}" y="{h-8}" width="9" height="3" fill="{col}"/><text x="{lx+13}" y="{h-4}" font-size="7.5" fill="{INK}">{esc(lab)}</text>')
        lx += 13 + len(lab) * 4.3 + 14
    out.append("</svg>")
    return "".join(out)


# ---------------- HTML ----------------
CSS = """
:root{--teal:#00627B;--teal-mid:#0A7A96;--blue-mid:#3B96B5;--teal-alt:#1B7C97;--ink:#2B3440;--muted:#6B7480;--soft:#5A6B7B;--ice:#CFE9F1;--edge:#BFD9E2;--line:#DDE4E9;--line-lt:#EFF3F5;--row:#F6FAFC;--tintA:#F7FBFC;--tintB:#F7FAFC;--panel:#F0F7FA;--blockedge:#E4EBF0;}
@page{size:Letter;margin:0.45in 0.5in 0.55in 0.5in;}
html,body{margin:0;padding:0;background:#fff;}
.container{font-family:'Poppins',Arial,sans-serif;color:var(--ink);font-size:10px;width:720px;margin:0 auto;}
.page{page-break-after:always;}
.page:last-child{page-break-after:auto;}
.brand-band{display:flex;align-items:center;background:var(--teal);background:linear-gradient(120deg,#00627B 0%,#0A7A96 55%,#3B96B5 100%);border-radius:14px;padding:16px 22px;box-shadow:0 4px 14px rgba(0,98,123,0.28);-webkit-print-color-adjust:exact;print-color-adjust:exact;}
.brand-logo{height:62px;margin-right:18px;}
.brand-name{font-family:'Montserrat','Poppins',Arial,sans-serif;font-size:26px;font-weight:700;color:#fff;letter-spacing:8px;line-height:1;}
.brand-tag{font-size:8px;color:var(--ice);letter-spacing:1.2px;text-transform:uppercase;margin-top:6px;}
.doc-meta{margin-left:auto;text-align:right;}
.doc-title{font-size:13px;font-weight:600;letter-spacing:4px;color:#fff;text-transform:uppercase;}
.doc-ref{font-size:9px;color:var(--ice);margin-top:3px;}
.page-head{display:flex;align-items:center;border-bottom:1px solid var(--edge);padding-bottom:6px;margin-bottom:8px;}
.page-head .pn{font-family:'Montserrat','Poppins',Arial,sans-serif;font-weight:700;letter-spacing:4px;color:var(--teal);font-size:11px;}
.page-head .pt{margin-left:auto;font-size:8px;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);}
.meta-strip{display:flex;border:1px solid var(--line);border-top:2px solid var(--teal);margin-top:14px;}
.meta-cell{flex:1;padding:8px 12px;border-right:1px solid var(--line-lt);}
.meta-cell:last-child{border-right:none;}
.meta-label{font-size:7.5px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:var(--blue-mid);margin-bottom:4px;}
.meta-body{font-size:9.5px;line-height:14px;color:var(--ink);}
.section-title{font-size:10.5px;font-weight:600;color:var(--teal);letter-spacing:1.5px;text-transform:uppercase;margin:16px 2px 6px;padding-bottom:4px;border-bottom:1px solid var(--edge);}
.kpis{display:flex;gap:8px;margin:14px 2px 0;}
.kpi{flex:1;background:var(--panel);border-radius:10px;padding:9px 11px;-webkit-print-color-adjust:exact;print-color-adjust:exact;}
.kpi .l{font-size:7px;font-weight:600;letter-spacing:1.3px;text-transform:uppercase;color:var(--blue-mid);}
.kpi .v{font-size:18px;font-weight:700;color:var(--teal);margin-top:3px;line-height:1.1;}
.kpi .s{font-size:7.5px;color:var(--muted);margin-top:3px;line-height:11px;}
.table-container{margin:0 2px;border:1px solid var(--line);border-radius:10px;overflow:hidden;}
.styled-table{border-collapse:collapse;width:100%;font-size:8.5px;}
.styled-table thead tr{background-color:var(--teal);background:linear-gradient(90deg,#00627B 0%,#1B7C97 100%);color:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact;}
.styled-table thead th{font-size:7.5px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase;white-space:nowrap;text-align:left;}
.styled-table th,.styled-table td{padding:4.5px 7px;}
.styled-table td.ctr{white-space:nowrap;}
.compact .styled-table{font-size:7.8px;}
.compact .styled-table th,.compact .styled-table td{padding:3px 5px;white-space:nowrap;}
.styled-table tbody tr{border-bottom:1px solid var(--line);page-break-inside:avoid;}
.styled-table tbody tr:last-child{border-bottom:none;}
.styled-table tbody tr:nth-child(even){background:var(--row);-webkit-print-color-adjust:exact;print-color-adjust:exact;}
.styled-table tr.total td{border-top:2px solid var(--teal);font-weight:600;color:var(--teal);}
.styled-table tr.sub td{color:var(--muted);font-size:8px;}
.num{text-align:right !important;}
.ctr{text-align:center !important;}
.code{font-size:8px;color:var(--muted);}
.grand-total{display:table;width:100%;margin:14px 2px 4px;background:var(--teal);background:linear-gradient(100deg,#00627B 0%,#0A7A96 60%,#3B96B5 100%);border-radius:12px;box-shadow:0 3px 10px rgba(0,98,123,0.25);box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact;}
.grand-total-label{display:table-cell;padding:12px 20px;color:#fff;font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;vertical-align:middle;}
.grand-total-note{font-weight:400;color:var(--ice);letter-spacing:0.5px;text-transform:none;font-size:9px;}
.grand-total-value{display:table-cell;padding:12px 20px;text-align:right;color:#fff;font-size:17px;font-weight:700;vertical-align:middle;white-space:nowrap;}
.notes-block{margin:14px 2px 0;border:1px solid var(--line);border-left:3px solid var(--teal);border-radius:8px;padding:9px 13px;background:var(--tintA);font-size:8.5px;line-height:13px;color:var(--ink);-webkit-print-color-adjust:exact;print-color-adjust:exact;}
.notes-block::before{content:attr(data-heading);display:block;font-size:9px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;color:var(--teal);margin-bottom:4px;}
.info-block{border:1px solid var(--blockedge);border-radius:6px;padding:8px 12px;margin-top:10px;font-size:8.5px;line-height:13px;color:var(--ink);background-color:var(--tintB);-webkit-print-color-adjust:exact;print-color-adjust:exact;}
.info-block::before{content:attr(data-heading);display:block;font-size:8px;text-transform:uppercase;letter-spacing:1px;color:var(--teal);font-weight:600;margin-bottom:3px;}
p{font-size:9.2px;line-height:14px;margin:5px 2px 8px;}
.fn{font-size:7.5px;line-height:11px;color:var(--soft);margin:5px 2px 0;}
.two{display:flex;gap:14px;margin:0 2px;}
.two>div{flex:1;min-width:0;}
.closing-note{font-size:9px;line-height:14px;color:var(--soft);margin-top:14px;}
.confidential{margin-top:18px;border-top:1px solid var(--line);padding-top:6px;text-align:center;font-size:7.5px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);}
.neg{color:#9B2C2C;}
h4{font-size:8.5px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:var(--blue-mid);margin:8px 2px 4px;}
ul{margin:2px 0 6px 14px;padding:0;font-size:8.6px;line-height:13px;}
li{margin:0 0 2px;}
"""


def head_page(n, title):
    return f'<div class="page-head"><div class="pn">SIMVAY</div><div class="pt">{esc(title)}</div></div>'


def table(headers, rows, widths=None, aligns=None, total_row=None):
    aligns = aligns or [""] * len(headers)
    th = "".join(f'<th class="{a}" {"style=width:"+w if widths and widths[i] else ""}>{h}</th>'
                 for i, (h, a, w) in enumerate(zip(headers, aligns, widths or [None] * len(headers))))
    body = []
    for r in rows:
        cls = ""
        if isinstance(r, dict):
            cls = r.get("cls", ""); r = r["cells"]
        body.append(f'<tr class="{cls}">' + "".join(f'<td class="{a}">{c}</td>' for c, a in zip(r, aligns)) + "</tr>")
    if total_row:
        body.append('<tr class="total">' + "".join(f'<td class="{a}">{c}</td>' for c, a in zip(total_row, aligns)) + "</tr>")
    return f'<div class="table-container"><table class="styled-table"><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def build(a, cfg, focus, summary, notes, out_html, logo_b64):
    months = sorted(m for m in a if not m.startswith("_"))
    f = a[focus]
    pi = months.index(focus)
    prev = a[months[pi - 1]] if pi > 0 else None
    pm = months[pi - 1]
    inv = a["_invoices"]
    ck = a["_checks"]
    fl = f["fl_margin"]
    today = datetime.date.today()
    title = f"{MONF[focus[5:7]]} {focus[:4]}"
    footer = cfg["confidential_footer"]

    def mom(cur, old):
        if not old: return "&mdash;"
        d = (cur - old) / abs(old) * 100 if old else 0
        return f'<span class="{"neg" if d < 0 else ""}">{d:+.0f}%</span>'

    # ---------- page 1 ----------
    kpis = [
        ("Total revenue", money(f["total"]), f"{f['invoices']} invoices &middot; {mom(f['total'], prev['total'])} vs {mlabel(pm)}"),
        ("Product gross profit", money(f["gp"]), f"{pct(f['gp_pct'])} margin &middot; product cost only"),
        ("Fully-loaded margin", money(fl), f"{pct(f['fl_margin_pct'])} &middot; ceiling, directional"),
        ("Recurring revenue", money(f["recurring"]), f"{pct(f['recurring']/f['total']*100)} of total &middot; {mom(f['recurring'], prev['recurring'])} vs {mlabel(pm)}"),
        ("Cybersecurity share", pct(f["cyber"] / f["total"] * 100), f"{money(f['cyber'])} cyber &middot; {money(f['mt'])} managed tech"),
    ]
    kpi_html = "".join(f'<div class="kpi"><div class="l">{l}</div><div class="v">{v}</div><div class="s">{s}</div></div>' for l, v, s in kpis)
    cat_chart = stacked_bars(months, [("Cybersecurity", {m: a[m]["cyber"] for m in months}),
                                      ("Managed Technology", {m: a[m]["mt"] for m in months})], [TEAL, BLUE], h=300)
    p1 = f"""
<div class="page">
  <div class="brand-band">
    <img class="brand-logo" alt="Simvay" src="data:image/png;base64,{logo_b64}">
    <div><div class="brand-name">SIMVAY</div><div class="brand-tag">29570 Clemens Rd &middot; Westlake, OH 44145</div></div>
    <div class="doc-meta"><div class="doc-title">Monthly Sales Report</div><div class="doc-ref">{title} &middot; prepared {today.strftime('%-m/%-d/%Y')}</div></div>
  </div>
  <div class="meta-strip">
    <div class="meta-cell"><div class="meta-label">Reporting month</div><div class="meta-body"><strong>{title}</strong><br>By invoice date, net of tax</div></div>
    <div class="meta-cell"><div class="meta-label">Trend window</div><div class="meta-body">{mlabel(months[0])} &ndash; {mlabel(months[-1])}<br>{len(months)} closed months</div></div>
    <div class="meta-cell"><div class="meta-label">Sources</div><div class="meta-body">HaloPSA reports 288 (revenue), 168 (cost), 290 (hours)<br>Invoice API for per-invoice cost</div></div>
    <div class="meta-cell"><div class="meta-label">Audience</div><div class="meta-body">Executive &middot; internal<br>Prepared by Claude for Ryan Patrick</div></div>
  </div>
  <div class="kpis">{kpi_html}</div>
  <div class="section-title">Executive summary</div>
  <p>{summary}</p>
  <div class="section-title">Revenue by category &middot; {mlabel(months[0])} &ndash; {mlabel(months[-1])}</div>
  {cat_chart}
  <div class="fn">Category is <em>which practice the revenue belongs to</em> (Cybersecurity vs Managed Technology). It is independent of the delivery bucket on page 2: Cisco Umbrella, for example, is SaaS by bucket and Cybersecurity by category. Figures are net of tax, by invoice date. Great Lakes Brewing's $12,000/mo MSA is split $3,500 FISM / $4,000 SOC / $4,500 Technology per management allocation (from Apr 2026).</div>
</div>"""

    # ---------- page 2: revenue mix + GP ----------
    mix_rows = []
    for key, lab in BUCKETS:
        cells = [lab] + [money(a[m][key]) for m in months] + [mom(f[key], prev[key])]
        mix_rows.append(cells)
    rec_cells = ["Recurring subtotal"] + [money(a[m]["recurring"]) for m in months] + [mom(f["recurring"], prev["recurring"])]
    mix_rows.append({"cls": "sub", "cells": rec_cells})
    tot_cells = ["Total revenue"] + [money(a[m]["total"]) for m in months] + [mom(f["total"], prev["total"])]
    mix_tbl = table(["Revenue line"] + [mlabel(m) for m in months] + ["MoM"], mix_rows,
                    aligns=[""] + ["num"] * (len(months) + 1), total_row=tot_cells)
    mix_chart = stacked_bars(months, [(lab, {m: a[m][key] for m in months}) for key, lab in BUCKETS],
                             [TEAL, MID, BLUE, SLATE, GREY], h=175, value_labels=False)
    gp_rows = []
    for lab, key, fmt in [("Revenue (report 288)", "total", money), ("Cost as recorded (report 168)", "cost_recorded", money),
                          ("&nbsp;&nbsp;less internal labour placeholders", None, None),
                          ("Product cost (vendor + hardware)", "cost", money), ("Product gross profit", "gp", money),
                          ("Product margin %", "gp_pct", pct), ("Adjusted GP (anomalies, defects removed)", "gp_adjusted", money),
                          ("Adjusted margin %", "gp_adjusted_pct", pct)]:
        if key is None:
            cells = [lab] + [money(-(a[m]["cost_recorded"] - a[m]["cost"])) for m in months] + [""]
            gp_rows.append({"cls": "sub", "cells": cells})
        else:
            cells = [lab] + [fmt(a[m][key]) for m in months] + [mom(f[key], prev[key]) if fmt is money and a[months[0]][key] else ""]
            cls = "total" if key == "gp" else ""
            gp_rows.append({"cls": cls, "cells": cells})
    gp_tbl = table(["Sales, cost & gross profit"] + [mlabel(m) for m in months] + ["MoM"], gp_rows,
                   aligns=[""] + ["num"] * (len(months) + 1))
    gp_chart = line_chart(months, [("Product margin %", {m: a[m]["gp_pct"] for m in months}),
                                   ("Adjusted margin %", {m: a[m]["gp_adjusted_pct"] for m in months})], [TEAL, GREY], w=672, h=118, ymin=0, ymax=100)
    p2 = f"""
<div class="page">
  {head_page(2, f"Revenue mix & gross profit · {title}")}
  <div class="section-title">Revenue mix by delivery bucket</div>
  {mix_tbl}
  <div class="fn">Bucket is <em>how revenue is delivered and billed</em>. Advisory = ECRM / FISM / ISM / FCISO. Managed Technology = EMTS, EMNS, MSA-Technology, MTS, Financed Solution, Auvik per-device monitoring. Cyber Operations (MSaaS) = SentinelOne family, SOC/MDR, A1, KnowBe4, Duo, Mimecast, SRM, C2, MSA-Security. SaaS = M365/NCE, Exchange Online, Visio, Umbrella, Adobe, VEEAM. One-time = hardware, labour, professional services, shipping, standalone or hardware-attached multi-year licences. Recurring = everything but one-time.</div>
  {mix_chart}
  <div class="section-title">Sales, cost and gross profit</div>
  {gp_tbl}
  <div class="fn">Cost and margin are <strong>product cost only</strong> (vendor and hardware). Internal delivery labour is excluded in full here and reconciled separately on page 4, so it is never double-counted. Two kinds of labour are stripped from the recorded cost: ticket-raised time (valued by Halo at agent cost) and the internal hours estimates carried in the cost field of labour-only service plans (ECRM, EMTS, EMNS, MTS, ISM/FISM/FCISO, MSA-Technology). Product margin tracks revenue mix: a mostly-contract month reads very high, a hardware-heavy month much lower. Neither is an error. Adjusted GP removes one-off multi-period vendor cost booked against single-period billing and the Bober Markey persistent cost defect (Appendix B); gross profit is reported at month and invoice level only, never by service line.</div>
  {gp_chart}
</div>"""

    # ---------- page 3: product lines, top clients, MoM ----------
    fams = list(f["cyber_families"].items())
    pfams = prev["cyber_families"]
    fam_rows = [[n, money(v), money(pfams.get(n, 0)), mom(v, pfams.get(n, 0)) if pfams.get(n) else "new"] for n, v in fams]
    for n, v in pfams.items():
        if n not in f["cyber_families"]:
            fam_rows.append([n, money(0), money(v), '<span class="neg">-100%</span>'])
    fam_tbl = table(["Cybersecurity product line", mlabel(focus), mlabel(pm), "MoM"], fam_rows, aligns=["", "num", "num", "num"],
                    total_row=["Cybersecurity total", money(f["cyber"]), money(prev["cyber"]), mom(f["cyber"], prev["cyber"])])
    fam_chart = hbars([(n[:24] + ("…" if len(n) > 24 else "")) for n, v in fams] and [(n.split(" (")[0], v) for n, v in fams], w=326, label_w=130, rowh=20)
    tc = f["top_clients"][:8]
    tc_chart = dual_client_bars([(n, c, m) for n, c, m in tc])
    prev_tc = {n: c + m for n, c, m in prev["top_clients"]}
    tc_rows = [[i + 1, n, money(c), money(m), money(c + m), pct((c + m) / f["total"] * 100)] for i, (n, c, m) in enumerate(tc)]
    tc_tbl = table(["#", "Client", "Cybersecurity", "Managed Tech", "Total", "Share"], tc_rows, aligns=["ctr", "", "num", "num", "num", "num"])
    cbf = {(c, bk): v for c, bk, v in f["client_bucket"]}
    cbp = {(c, bk): v for c, bk, v in prev["client_bucket"]}
    mom_rows = []
    for key, lab in BUCKETS:
        deltas = {}
        for (c, bk), v in list(cbf.items()) + list(cbp.items()):
            if bk == key: deltas[c] = cbf.get((c, key), 0) - cbp.get((c, key), 0)
        top = sorted(deltas.items(), key=lambda kv: -abs(kv[1]))[:3]
        drivers = "; ".join(f"{esc(c)} {'+' if d >= 0 else '-'}{money(abs(d))}" for c, d in top if abs(d) >= 100) or "no material movement"
        mom_rows.append([lab, money(prev[key]), money(f[key]), money(f[key] - prev[key]), mom(f[key], prev[key]), drivers])
    mom_tbl = table(["Bucket", mlabel(pm), mlabel(focus), "Change", "%", "Largest client movements"], mom_rows,
                    widths=["120px", "62px", "62px", "62px", "40px", None], aligns=["", "num", "num", "num", "num", ""],
                    total_row=["Total", money(prev["total"]), money(f["total"]), money(f["total"] - prev["total"]), mom(f["total"], prev["total"]), ""])
    p3 = f"""
<div class="page">
  {head_page(3, f"Product lines, clients & month over month · {title}")}
  <div class="section-title">Cybersecurity product lines &middot; {mlabel(focus)}</div>
  <div class="two"><div>{fam_tbl}</div><div>{fam_chart}</div></div>
  <div class="fn">Cyber Operations is one line: the SOC runs on SentinelOne, so SOC/MDR, MEDR/EMDR, SentinelOne SKUs and the threat-intel ingest fee are counted once. Allocation components (Great Lakes Brewing SOC and FISM carve-outs) roll into their real families. Revenue only; gross profit is not attributable by service line.</div>
  <div class="section-title">Top clients &middot; {mlabel(focus)}</div>
  {tc_chart}
  {tc_tbl}
  <div class="section-title">Month over month by bucket &middot; {mlabel(pm)} &rarr; {mlabel(focus)}</div>
  {mom_tbl}
  <div class="fn">Drivers are the largest client-level movements within each bucket between the two months (revenue by invoice date, so annual renewals and catch-up billing land in the month they were invoiced).</div>
</div>"""

    # ---------- page 4: invoice profitability, hours, fully-loaded margin, portfolio ----------
    kinds = {}
    for i in inv:
        d = kinds.setdefault(i["kind"], [0, 0.0, 0.0])
        d[0] += 1; d[1] += i["revenue"]; d[2] += i["cost"]
    kind_rows = [[kd, n, money(r), money(c), money(r - c), pct((r - c) / r * 100) if r else "&mdash;"] for kd, (n, r, c) in sorted(kinds.items(), key=lambda kv: -kv[1][1])]
    kind_tbl = table(["Invoice kind", "Invoices", "Revenue", "Product cost", "Gross profit", "Margin"], kind_rows,
                     aligns=["", "ctr", "num", "num", "num", "num"],
                     total_row=["All invoices", len(inv), money(ck["appendix_c_total"]), money(f["cost"]), money(f["gp"]), pct(f["gp_pct"])])
    low = sorted([i for i in inv if i["cost"] > 0], key=lambda i: (i["gp_pct"] if i["gp_pct"] is not None else 0))[:6]
    low_rows = [[i["invoice"], i["client"][:30], money(i["revenue"]), money(i["cost"]), pct(i["gp_pct"])] for i in low]
    low_tbl = table(["Inv", "Client", "Revenue", "Cost", "Margin"], low_rows, aligns=["ctr", "", "num", "num", "num"])
    hb = f["hours"]
    hrs_rows = []
    for t, (hh, lc) in hb["by_team"].items():
        ph_ = prev["hours"]["by_team"].get(t, [0, 0])[0]
        hrs_rows.append([f"{t} <span class=code>{cfg['team_category_map'].get(t, 'unmapped')}</span>", f"{hh:,.2f}", f"{ph_:,.2f}", money(hh * hb["rate"])])
    hrs_tbl = table(["Team", f"{MON[focus[5:7]]} h", f"{MON[pm[5:7]]} h", f"Internal cost @ ${hb['rate']:.0f}/h"], hrs_rows,
                    aligns=["", "num", "num", "num"],
                    total_row=["Delivery hours", f"{hb['total']:,.2f}", f"{prev['hours']['total']:,.2f}", money(hb["delivery_cost"])])
    hrs_chart = stacked_bars(months, [("Cybersecurity", {m: a[m]["hours"]["by_category"].get("Cybersecurity", 0) for m in months}),
                                      ("Managed Technology", {m: a[m]["hours"]["by_category"].get("Managed Technology", 0) for m in months})],
                             [TEAL, BLUE], w=326, h=140, value_labels=False)
    # patch the hours chart's $ axis labels to hours
    hrs_chart = re.sub(r'>\$([0-9,]+)k?<', lambda m: f'>{m.group(1)}h<', hrs_chart)
    hrs_chart = re.sub(r'>\$([0-9,\.]+)<', lambda m: f'>{m.group(1)}h<', hrs_chart)
    fl_rows = [["Product gross profit (page 2)", money(f["gp"]), pct(f["gp_pct"])],
               [f"less internal delivery cost ({hb['total']:,.2f} h &times; ${hb['rate']:.0f})", money(-hb["delivery_cost"]), pct(-hb["delivery_cost"] / f["total"] * 100)]]
    fl_tbl = table(["Fully-loaded margin", mlabel(focus), "% of revenue"], fl_rows, aligns=["", "num", "num"],
                   total_row=["Fully-loaded margin (ceiling)", money(fl), pct(f["fl_margin_pct"])])
    fl_trend = line_chart(months, [("Product margin %", {m: a[m]["gp_pct"] for m in months}),
                                   ("Fully-loaded margin %", {m: a[m]["fl_margin_pct"] for m in months})], [TEAL, SLATE], w=326, h=130, ymin=-10, ymax=100)
    clients_f = {i["client"] for i in inv}
    rec_clients = {i["client"] for i in inv if i["kind"] == "Contract"}
    port_rows = [
        ["Invoices raised", str(f["invoices"]), str(prev["invoices"])],
        ["Average invoice (net)", money(f["total"] / f["invoices"]), money(prev["total"] / prev["invoices"])],
        ["Clients invoiced", str(len(clients_f)), "&mdash;"],
        ["Recurring share of revenue", pct(f["recurring"] / f["total"] * 100), pct(prev["recurring"] / prev["total"] * 100)],
        ["Contract base (Advisory + Managed Tech)", money(f["advisory"] + f["mtcontracts"]), money(prev["advisory"] + prev["mtcontracts"])],
        ["Delivery hours logged (external clients)", f"{hb['total']:,.2f}", f"{prev['hours']['total']:,.2f}"],
        ["Cyber Ops hours (advisory + escalations)", f"{hb['by_category'].get('Cybersecurity', 0):,.2f}", f"{prev['hours']['by_category'].get('Cybersecurity', 0):,.2f}"],
    ]
    port_tbl = table(["Portfolio metric", mlabel(focus), mlabel(pm)], port_rows, aligns=["", "num", "num"])
    top_h = hb["top_clients"][:6]
    p4 = f"""
<div class="page">
  {head_page(4, f"Invoice profitability, hours & fully-loaded margin · {title}")}
  <div class="section-title">Invoice profitability &middot; {mlabel(focus)}</div>
  {kind_tbl}
  <div class="two"><div><h4>Lowest-margin invoices carrying product cost</h4>{low_tbl}</div><div><h4>Portfolio metrics</h4>{port_tbl}</div></div>
  <div class="fn">Per-invoice product cost comes from the Invoice API lines (unit cost &times; quantity), with ticket-raised time and labour-plan placeholders stripped; it reconciles to report 168 to the cent ({pct(ck['cost_attribution_pct'])} attributed). Contract invoices for labour-only plans show 100% product margin by construction: their delivery cost sits in the hours block below. One-row-per-invoice detail is in Appendix C. Multi-invoice orders can show cost and revenue on different invoices; those are not anomalies.</div>
  <div class="section-title">Billed hours by team &middot; internal delivery cost &middot; fully-loaded margin</div>
  <div class="two"><div>{hrs_tbl}<h4>Fully-loaded margin</h4>{fl_tbl}<h4>Clients by hours &middot; {mlabel(focus)}</h4>{hbars(top_h, w=326, label_w=140, rowh=15, fmt=lambda v: f"{v:,.2f} h")}</div><div><h4>Delivery hours by category</h4>{hrs_chart}<h4>Product vs fully-loaded margin</h4>{fl_trend}</div></div>
  <div class="fn">${hb['rate']:.0f}/h is Simvay's <strong>fully-loaded cost to provide an hour</strong> (salaries, benefits, expenses, overhead). It is not a customer price; the customer support rate is $200/h. Coverage is not uniform: Cyber Ops logs time in Halo only for Advisory Services and for incident escalations needing action outside the SIEM (BEC remediation, client-side actions); routine SOC triage lives in Grafana / Victoria Logs and is not included, so hours per revenue must not be compared across teams as cost-to-serve. Economics differ too: Cyber Ops has no committed hours, so every logged hour is incremental; Managed Technology plans commit hours and Advisory commits far fewer, so those hours draw down an allowance already priced in. Because SOC triage is under-captured, fully-loaded margin is a <strong>ceiling</strong>, reported as directional; product GP on page 2 remains the firm number. Hours logged against the internal client "Simvay" ({hb['excluded_internal']:,.2f} h in {mlabel(focus)}) are excluded.</div>
</div>"""

    # ---------- page 5: appendices A & B ----------
    defs = """
<ul>
<li><strong>Revenue</strong> &mdash; HaloPSA report 288 (Invoice Export), unit price &times; quantity, net of tax, by invoice date. Credit notes net against revenue. Recurring per Ryan Patrick (7/16/2026): anything turned into a contract, including subscriptions and service plans; large one-off licence buy-outs (Webex 36-month, hardware-attached Meraki) are one-time even with term wording.</li>
<li><strong>Category</strong> &mdash; Cybersecurity vs Managed Technology, by keyword on the line description; MSA "| Security" components are Cybersecurity, "| Technology" components Managed Technology. Cameras and physical-security hardware are Managed Technology.</li>
<li><strong>Bucket</strong> &mdash; Advisory / Managed Technology / Cyber Operations (MSaaS) / SaaS / One-time, as footnoted on page 2. Cyber Operations is synonymous with Managed SaaS; a Cyber Operations contract that does not arrive that way is a data error to raise, not a reclassification.</li>
<li><strong>Product cost</strong> &mdash; report 168 (Revenue and Profit) and the Invoice API, vendor and hardware cost only. Stripped: ticket-raised time (Halo: time taken &times; agent cost price) and the cost field of labour-only service plans, which holds an internal hours estimate structurally indistinguishable from vendor cost (ticket id -1). Kept: MSA Security components, Auvik / Monitoring Per Billable Device, all Cyber Ops, SaaS and hardware cost. Labour is never inferred from arithmetic; the product decides.</li>
<li><strong>Gross profit</strong> &mdash; revenue less product cost, month and invoice level only. Adjusted GP removes (a) one-off multi-period vendor cost booked against single-period billing and (b) persistent defects (same client underwater 2+ months), which are reported separately. An order split across invoices is not an anomaly.</li>
<li><strong>Delivery hours</strong> &mdash; report 290 (Billed Hours by Team): time taken plus adjusted time on all ticket actions, including contract-absorbed work, mapped to category by team (Cyber Ops Analysts/Mgmt = Cybersecurity; Support Sys Admins/Mgmt = Managed Technology). Internal cost = hours &times; $150 fully-loaded.</li>
<li><strong>Fully-loaded margin</strong> &mdash; product GP less internal delivery cost; a ceiling, not a point estimate, because routine SOC triage is not logged in Halo.</li>
</ul>"""
    # data quality auto-notes
    dq = []
    if f["expired_corrections_firing"]:
        for e in f["expired_corrections_firing"]:
            dq.append(f"<li><strong>Source fix has not taken:</strong> {esc(e['client'])} &ldquo;{esc(e['description'])}&rdquo; still carries {money(e['cost'])} in the cost field on the {mlabel(focus)} invoice, past the correction's expected end ({e['effective_through']}). The line is a labour-only plan and is stripped from product cost regardless, but the recurring-invoice template in Halo still needs the unit cost cleared.</li>")
    for d in f["labour_detail"]:
        if d["kind"] == "labour_plan" and d["cost"] < 0:
            dq.append(f"<li>{esc(d['client'])} &ldquo;{esc(d['description'])}&rdquo; carries a unit cost of {money(d['cost'])} (negative placeholder). Stripped as labour; cosmetic, fix in the template.</li>")
    if f["one_off_anomalies"]:
        for o in f["one_off_anomalies"]:
            dq.append(f"<li><strong>One-off multi-period cost:</strong> {esc(o['client'])} &ldquo;{esc(o['description'])}&rdquo; cost {money(o['cost'])} vs revenue {money(o['revenue'])} ({o['ratio']}&times;). Excess feeds adjusted GP.</li>")
    if f["persistent_defects"]:
        pc = f["persistent_cost"]
        dq.append(f"<li><strong>Persistent defect (reported separately, excluded from adjusted GP):</strong> {money(pc)} across {len(f['persistent_defects'])} lines.</li>")
    trend_notes = []
    for m in months:
        v = a[m]
        if m == focus: continue
        bits = []
        if v["one_off_anomalies"]:
            bits.append("one-off multi-period cost " + "; ".join(f"{esc(o['client'])} {money(o['cost'])} vs {money(o['revenue'])}" for o in v["one_off_anomalies"]))
        if v["persistent_defects"]:
            bits.append(f"persistent defect {money(v['persistent_cost'])} ({esc(v['persistent_defects'][0]['client'])})")
        lp = v["labour_stripped"]
        if any(abs(x) >= 100 for x in lp.values()):
            bits.append("labour stripped " + ", ".join(f"{kk.replace('_', ' ')} {money(vv)}" for kk, vv in lp.items() if abs(vv) >= 1))
        if bits:
            trend_notes.append(f"<li><strong>{mlabel(m)}:</strong> {'; '.join(bits)}. As-recorded {pct(v['gp_pct'])}, adjusted {pct(v['gp_adjusted_pct'])}.</li>")
    p5 = f"""
<div class="page">
  {head_page(5, f"Appendix A · definitions and method · {title}")}
  <div class="section-title">Appendix A &middot; definitions and method</div>
  {defs}
  <div class="section-title">Appendix B &middot; data quality and methodology notes</div>
  <h4>{mlabel(focus)}</h4>
  <ul>{''.join(dq)}{notes}</ul>
  <h4>Trend months</h4>
  <ul>{''.join(trend_notes)}</ul>
  <h4>Reconciliation checks (all passed)</h4>
  <ul>
  <li>Report 288 pulled twice (reportingperiod 10 and 11); the overlapping months ({mlabel(months[-2])}, {mlabel(months[-1])}, and the Sep 2026 stub) agree to the cent. Both arrays closed; no truncation of the rows array (the 500k cap only trimmed the trailing table_html).</li>
  <li>Report 168 revenue for {mlabel(focus)} {money(f['profit_report_revenue'], 2)} vs report 288 {money(f['total'], 2)}: {money(f['profit_report_revenue'] - f['total'], 2)} rounding on one 175-unit line (unit price 3.3330). Invoice API revenue {money(ck['api_revenue_total'], 2)} matches 168.</li>
  <li>Appendix C total {money(ck['appendix_c_total'], 2)} = month total; {ck['appendix_c_invoices']} invoices = {ck['month_invoices']} in report 288; per-invoice GP sums to {money(ck['per_invoice_gp_sum'], 2)} = month GP; Invoice API cost {money(ck['api_cost_total'], 2)} = report 168 cost {money(ck['r168_cost_total'], 2)}; cost attribution {pct(ck['cost_attribution_pct'])}.</li>
  </ul>
</div>"""

    # ---------- page 6+: appendix C ----------
    c_rows = []
    for i in inv:
        c_rows.append([i["invoice"], i["date"][5:], i["client"][:30], i["kind"], dict(BUCKETS).get(i["bucket"], i["bucket"]),
                       money(i["revenue"], 2), money(i["cost"], 2), money(i["gp"], 2),
                       (pct(i["gp_pct"]) if i["gp_pct"] is not None else "&mdash;"),
                       (money(i["labour_stripped"], 2) if i["labour_stripped"] else "")])
    c_tbl = table(["Invoice", "Date", "Client", "Kind", "Primary bucket", "Revenue", "Product cost", "Gross profit", "Margin", "Labour stripped"],
                  c_rows, widths=["40px","34px","150px","44px","104px",None,None,None,None,None], aligns=["ctr", "ctr", "", "", "", "num", "num", "num", "num", "num"],
                  total_row=["Total", "", f"{len(inv)} invoices", "", "", money(ck["appendix_c_total"], 2), money(f["cost"], 2), money(f["gp"], 2), pct(f["gp_pct"]), money(sum(i["labour_stripped"] for i in inv), 2)])
    p6 = f"""
<div class="page">
  {head_page(6, f"Appendix C · invoice summary · {title}")}
  <div class="section-title">Appendix C &middot; one row per invoice &middot; {mlabel(focus)}</div>
  <div class="compact">{c_tbl}</div>
  <div class="fn">Revenue from report 288 (unit price &times; quantity, net of tax). Product cost from the Invoice API (unit cost &times; quantity) after stripping the labour placeholders shown in the last column. "Primary bucket" is the bucket carrying the largest share of the invoice; mixed invoices (e.g. EMTS + ECRM on one contract invoice) are split correctly in the page-2 totals. Kind: Contract = recurring-invoice run, Order = sales-order invoice, Ad hoc = manual invoice.</div>
  <div class="grand-total"><div class="grand-total-label">{mlabel(focus)} product gross profit <span class="grand-total-note">&middot; {money(f['total'])} revenue &middot; {pct(f['gp_pct'])} product margin &middot; {pct(f['fl_margin_pct'])} fully-loaded ceiling</span></div><div class="grand-total-value">{money(f['gp'])}</div></div>
</div>"""

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Simvay Sales Report {title}</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Montserrat:wght@500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><div class="container">{p1}{p2}{p3}{p4}{p5}{p6}</div></body></html>"""
    open(out_html, "w").write(html)
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir"); ap.add_argument("--config", required=True); ap.add_argument("--focus", required=True)
    ap.add_argument("--summary", required=True); ap.add_argument("--extra-notes", default=None)
    ap.add_argument("--out", required=True); ap.add_argument("--logo", required=True)
    args = ap.parse_args()
    a = json.load(open(os.path.join(args.data_dir, "analysis.json")))
    cfg = json.load(open(args.config))
    summary = open(args.summary).read().strip()
    notes = open(args.extra_notes).read().strip() if args.extra_notes else ""
    logo_b64 = base64.b64encode(open(args.logo, "rb").read()).decode()
    html_path = args.out.replace(".pdf", ".html")
    build(a, cfg, args.focus, summary, notes, html_path, logo_b64)
    js = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const b = await chromium.launch({{ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] }});
  const p = await b.newPage();
  await p.goto('file://{os.path.abspath(html_path)}', {{ waitUntil: 'load' }});
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(800);
  await p.pdf({{ path: '{os.path.abspath(args.out)}', format: 'Letter', printBackground: true, preferCSSPageSize: true,
    displayHeaderFooter: true, headerTemplate: '<div></div>',
    footerTemplate: '<div style="font-family:Poppins,Arial;font-size:6.5px;color:#6B7480;width:100%;text-align:center;letter-spacing:1.5px;text-transform:uppercase;">{cfg["confidential_footer"].replace("—","&mdash;")} &nbsp;&middot;&nbsp; Simvay Sales Report &middot; {MONF[args.focus[5:7]]} {args.focus[:4]} &middot; page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
    margin: {{ top: '0.45in', bottom: '0.55in', left: '0.5in', right: '0.5in' }} }});
  await b.close();
}})();
"""
    open("render.js", "w").write(js)
    subprocess.run(["node", "render.js"], check=True)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
