# Simvay Document Brand Guide

> **Purpose:** the single reference for styling any Simvay-branded deliverable Claude
> produces — HTML reports, PDFs, decks, one-pagers. Extracted 2026-07-20 from the live
> HaloPSA PDF templates (Simvay Proposal / Sales Order / Purchase Order / Invoice,
> sentinel family SIMVAY-*) so future documents match the client-facing paper trail.
>
> **Sources of truth, in order:** (1) this guide; (2) the live template CSS
> (HaloPSA template 29/30/31/32 via the pdftemplate API — Runbook 05 §3);
> (3) `simvay-monthly-sales-report/config.json` and the QBR deck script (same palette).

---

## 1. Color palette

### Core brand

| Token | Hex | Use |
|---|---|---|
| **Teal (primary)** | `#00627B` | Headings, table header base, accents, rules, links |
| **Teal mid** | `#0A7A96` | Gradient midpoint |
| **Blue mid** | `#3B96B5` | Gradient end, small labels (meta-label) |
| **Teal alt** | `#1B7C97` | Table-header gradient end |
| **Light blue** | `#6BBBD5` | Charts/decks secondary series (from deck kit; not used on paper docs) |
| **Slate** | `#525E77` | Signature rules, secondary chart series |

### Ink & neutrals

| Token | Hex | Use |
|---|---|---|
| **Ink** | `#2B3440` | Body text |
| **Muted** | `#6B7480` | Secondary text, SKU column, sub-labels |
| **Soft slate** | `#5A6B7B` | Closing/legal note text |
| **Ice** | `#CFE9F1` | Light text on teal (taglines, sub-notes on gradient) |
| **Edge** | `#BFD9E2` | Section-title underline, tinted borders |
| **Line** | `#DDE4E9` | Table borders, row dividers, block borders |
| **Line light** | `#EFF3F5` | Interior cell dividers |
| **Tint row** | `#F6FAFC` | Zebra-stripe even rows |
| **Tint block** | `#F7FBFC` / `#F7FAFC` | Notes/payment block backgrounds |
| **Tint panel** | `#F0F7FA` | Deck panel fill ("tint" in skill config) |
| **Block edge** | `#E4EBF0` | Payment-block border |

### Gradients (signature look — use these exact stops)

- **Hero band:** `linear-gradient(120deg, #00627B 0%, #0A7A96 55%, #3B96B5 100%)`
- **Table header:** `linear-gradient(90deg, #00627B 0%, #1B7C97 100%)`
- **Grand-total / KPI bar:** `linear-gradient(100deg, #00627B 0%, #0A7A96 60%, #3B96B5 100%)`
- Shadows on gradient elements: `0 4px 14px rgba(0,98,123,0.28)` (hero),
  `0 3px 10px rgba(0,98,123,0.25)` (total bar).
- Always set a solid `background: #00627B` fallback line *before* the gradient line
  (PDF engines that miss gradients degrade gracefully).

## 2. Typography

- **Body:** `'Poppins', Arial, sans-serif` — weights 400/500/600/700.
- **Display (wordmark only):** `'Montserrat', 'Poppins', Arial, sans-serif` — 500/600/700.
- Google Fonts load: families `Poppins:400;500;600;700` + `Montserrat:wght@500;600;700`
  (link tag in HTML; for offline PDF generation the fonts must be installed or the
  document falls back to Arial).
- **Environment fallbacks:** matplotlib/reportlab PDFs → Carlito
  (`/usr/share/fonts/truetype/crosextra/Carlito-*.ttf`); PowerPoint decks → Calibri.

### Type scale (print docs; base font-size 10px on `.container`)

| Element | Size | Weight | Case / spacing |
|---|---|---|---|
| Wordmark "SIMVAY" | 26px | 700 Montserrat | UPPERCASE, letter-spacing **8px** |
| Wordmark tagline / address | 8px | 400 | UPPERCASE, ls 1.2px, color Ice |
| Doc type ("INVOICE") | 13px | 600 | UPPERCASE, ls **4px**, white |
| Doc ref/date under type | 9px | 400 | Ice |
| Document title line | 14px | 600 | sentence case, Ink |
| Section title (`proposal-table-title`) | 10.5px | 600 | UPPERCASE, ls 1.5px, Teal, 1px `#BFD9E2` bottom border |
| Meta label | 7.5px | 600 | UPPERCASE, ls 1.5px, Blue mid |
| Meta body | 9.5px / 14px line-height | 400 | Ink |
| Table header | 8.5px | 600 | UPPERCASE, ls 0.5px, white, `white-space:nowrap` |
| Table body | 9px | 400 | Ink; SKU/code cells 8px Muted |
| Grand-total label | 11px | 600 | UPPERCASE, ls 1.5px, white |
| Grand-total value | 17px | 700 | white, nowrap |
| Notes/payment/closing text | 9px / 14px line-height | 400 | Ink (closing: Soft slate) |
| Confidential footer | ~7.5–8px | 400 | UPPERCASE-ish, ls 2px, Muted, centered |

Letter-spacing is a core brand signature: generous tracking on ALL uppercase labels.

## 3. Component library

Order on a document page: **hero band → meta-strip → section title + table → subtotal →
grand-total bar → notes/payment blocks → closing note → confidential footer.**

- **Hero band** (`.brand-band`): flex row, hero gradient, radius **14px**,
  padding 16px 22px, hero shadow. Left: white S-mark (height 62px, 18px right margin) +
  stacked wordmark/tagline. Right (`.doc-meta`, margin-left auto, right-aligned):
  doc type + ref/date.
- **Meta-strip** (`.meta-strip`): flex; 1px `#DDE4E9` border with a **2px solid `#00627B`
  top border**; 3–4 `.meta-cell`s (equal width, padding 8px 12px, 1px `#EFF3F5`
  right-divider), each = tiny uppercase `.meta-label` + `.meta-body`.
- **Section title** (`.proposal-table-title`): see scale; 4px bottom padding + 1px
  `#BFD9E2` underline; 20px top margin.
- **Data table** (`.table-container` > `.styled-table`): container has 1px `#DDE4E9`
  border, radius **10px**, `overflow:hidden`. Table: collapse, 100% width. Header row:
  table-header gradient, white. Cells padding 6px 8px. Rows: 1px `#DDE4E9` bottom
  border; even rows `#F6FAFC`. **Alignment rules: text columns left, quantity center,
  money right. Description gets ~52% width.** (The Halo quote layout is 6-col with a
  92px SKU first; the invoice variant `.invoice-table` is Description 52% / Qty 60px /
  Unit Price 70px / Tax 60px / Price 80px.)
- **Subtotal table** (`.subtotal-table-container`): right-aligned, 30% width, 9px;
  labels Muted left, values right; final row 2px `#00627B` top border, teal 600 10px.
- **Grand-total bar** (`.grand-total`): full-width, KPI gradient, radius **12px**,
  shadow; label cell (uppercase, ls 1.5px, with optional `.grand-total-note` in Ice) +
  17px/700 value right. Reuse as a KPI/highlight bar in reports.
- **Notes block** (`.notes-block`): 1px `#DDE4E9` border with a **3px teal left
  border**, radius 8px, bg `#F7FBFC`, padding 10px 14px; auto-heading via `::before`
  ("Notes & Terms" style: 9.5px 600 uppercase teal); `:empty { display:none }`.
- **Payment/info block** (`.payment-block`): quieter variant — 1px `#E4EBF0` border,
  radius 6px, bg `#F7FAFC`, same auto-heading pattern at 8.5px.
- **Closing note** (`.closing-note`): 9px Soft slate paragraph.
- **Confidential footer:** centered hairline + "CONFIDENTIAL — this document …" line
  (deck version: "Simvay LLC — Internal / Confidential", 8px, ls 2px, light grey).
- **Signature row** (`.signature-row`): two 50% tiles, 1px `#525E77` top rule,
  name 600 / role Muted / date floated right (quotes only).
- **Radii vocabulary:** 14px hero, 12px total bar, 10px tables, 8px notes, 6px quiet
  blocks. Don't invent new radii.

## 4. Logo assets

- **S-mark (zig-zag "S" with ringed ends):** white-on-transparent and
  teal-on-transparent PNGs (206×256) regenerated 2026-07-20 from the template-embedded
  original (77×96 native). Both live as ready `data:` URIs in the project doc
  `claude/Simvay-Logo-DataURIs.md`; the starter template
  (`claude/Simvay-Report-Starter-Template.html`) already embeds the white mark.
  To materialize a .png, strip the data-URI prefix and base64-decode.
- **White mark on gradient/teal only; teal mark on white/tint only.** Never place the
  teal mark on the gradient or the white mark on white.
- **Canonical high-res originals:** SharePoint →
  `SecurityOperationsHub - Documents/INTERNAL/04 - MDR/QBRs/Assets/` —
  wordmark `Simvayheader_New.png`, S-mark `SimvayLogo_New.png` (stage via the desktop
  app when pixel-perfect print assets are needed).
- The wordmark can also be typeset live: "SIMVAY" Montserrat 700, uppercase,
  8px letter-spacing (this is exactly what the PDF templates do).
- Company line under wordmark: `29570 CLEMENS RD · WESTLAKE, OH 44145` (docs) /
  phone `216-282-8190` where a From block is used. Checks payable to **Simvay LLC**.

## 5. Charts & decks

- Chart series order: Teal `#00627B` → Light blue `#6BBBD5` → Slate `#525E77` →
  Light grey `#A0A0A0`; benchmark/reference series grey, Simvay series teal.
- Deck surface: white with `#F0F7FA` tint panels, rounded rectangles, soft shadow
  (`blur 7 / offset 2 / 14% opacity`), Calibri, teal 30pt titles, uppercase
  letter-spaced kickers (charSpacing 3–4).
- KPI tiles: tint panel, teal 24–30pt number, ink label, muted italic benchmark line.

## 6. Do / don't

- DO keep everything on white; color arrives via the gradient band, table headers,
  and the total bar — not via colored body text.
- DO use uppercase + tracking for every label; sentence case for body.
- DO right-align money, center quantities, left-align text (headers follow columns).
- DO include the confidential footer on anything client-facing or financial.
- DON'T use pure black (`#000`) — Ink is `#2B3440`.
- DON'T introduce new accent hues (no greens/oranges except semantic chart needs).
- DON'T use broad `!important` overrides in multi-page Halo templates — see
  Runbook 05 §3 for the cascade rules (fix blocks go in the LAST page's stylesheet).
