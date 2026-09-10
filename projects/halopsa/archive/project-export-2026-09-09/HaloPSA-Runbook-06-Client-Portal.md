# Simvay HaloPSA — Runbook 06: Client-Facing Self-Service Portal (branding & custom CSS)

> **Scope:** The customer-facing portal at `https://simvay.halopsa.com/portal`. How it's
> configured, the exact DOM hooks, and the branded dark redesign applied via Custom CSS.
> **Last updated:** 2026-07-20 (fourth pass: even/tight card grid, visible glass + ambient
> glows, new-ticket form restyle, search moved to a floating top-right pill with a centered
> magnifier; record 707 now carries blocks V1–V12).

Config and portal edits here are **Chrome-only** (the read-only MCP connector can't reach
portal config). Portal config lives at **Config → Self Service Portal**
(`/config/selfservice`). `/config/branding` **404s** — don't use it.

---

## 1. Config page: `/config/selfservice` (auto-saves — NO Save button)

Top-of-page fields (each **auto-saves on blur/change**; verify by reload — there is no
Save button, same pattern as `/config/salesorders`):

| Field | Value set 2026-07-20 | Notes |
|---|---|---|
| Web portal URL | `https://simvay.halopsa.com/portal/` | read-only-ish |
| **Portal Title** | **`Simvay Support Portal`** | was "Support Portal"; shows in browser tab + login |
| **Welcome Message** | **`How can we help?`** | renders as the `h1.search-title` hero on the home page. Was the emergency phone line — that callout now lives in an **amber chip rendered by CSS** (V8 `form.container::after`). ⚠ If you edit the emergency number/wording, change it in the **CSS chip content**, not here. Language-pack backed |
| **Portal Theme** | **`Halo PSA Dark`** | options: *Halo PSA Standard* (light), *Halo PSA Dark*, *Use browser preference*. ⚠ **The light "Standard" theme has a contrast bug** — tile text + welcome message are hard-coded white → white-on-white (invisible) on the light cards. Dark reads cleanly. If you ever switch to light, you MUST fix text colors in Custom CSS. |
| **Portal Color** | **`#00627B` (R0 G98 B123)** | Simvay teal. Was `#525E77` (slate — also a brand color, the tertiary one). Drives the top header band (`.nhd-nav`) + the DEFAULT tile-icon circle color. Hex box display rounds oddly (showed `006278`); **trust the R/G/B numbers**. (Footer color is overridden dark in CSS — see V4.) |
| Portal Logo | SIMVAY wordmark (base64 PNG) | The header logo is forced **pure white via CSS filter** (`filter:brightness(0) invert(1)`, see V3) — no re-upload needed, dodges the flaky Windows upload path. |

Lower on the page: login-requirement toggles, anonymous-user, approval-page options (behavioral, left as-is).

### 1.1 Menu Buttons (the home tiles / nav buttons)
Section "Menu Buttons" lists every tile. Hover a row → pencil to edit. Each button modal has
**"Override default name, hint and icon"** → **Icon** (FontAwesome name) + **Icon color**
dropdown (`Default` | `Custom Color`), plus **"Show on home screen"** and **"Show on
navigation bar"** checkboxes.

- **Invoices icon fix (2026-07-20):** it had Icon color = **Custom Color #C45100 (orange)**,
  clashing with the teal tiles. Cleared via the **X** on the "Icon color" dropdown → set to
  **Default** (inherits the teal Portal Color) → modal **Save**.
- **Hidden tiles (2026-07-20, per Ryan):** **Documents** and **My Dashboards** — unchecked
  **"Show on home screen"** in each button modal (both already had nav off), so they're fully
  hidden. Home now shows 7 tiles: Managed Technology Support, Cybersecurity Support, User
  Lifecycle, Tickets, Projects, Quotes, Invoices. Re-check the box to bring one back.
- **Tile → ticket-type map (observed):** Managed Technology Support →
  `/portal/newticket?tickettype_id=1&btn=43`; Cybersecurity Support →
  `?tickettype_id=34&btn=75` (its subtitle carries the SOC emergency line "…Option 4").
  Both use the SAME New Ticket template, so the V10 form styling covers every ticket type.
- Nav button alignment = Right. **⚠ Keep "Show the search bar" ON** — V11 repositions the
  rendered search element; turning the config toggle off would remove the search entirely.

### 1.2 Home Screen backgrounds (two Halo-stock fields)
- **Home screen background image URL** and **Service catalogue** one both default to Halo
  stock `https://usehalo.com/wp-content/uploads/2025/03/ssp-ext.png`. The custom CSS
  overrides the visible home background (`.page-portal-background`) with a branded dark
  gradient + ambient glows (V9), so these were left as-is.
- Home Screen toggles: Show search bar (on — required by V11), Show my Tickets widget (on).
  "Display custom HTML" is on with an empty Custom-HTML box (spot for a future banner / SOC line).

### 1.3 Top nav: hamburger vs. expanded buttons (both states exist)
Halo's portal header has TWO nav states and switches between them itself:
- **Collapsed (fresh page load):** the nav BUTTONS exist in the DOM at **width 0** and the
  **hamburger `button.menubtn`** is active. Its stock glyph is a `background-image` — killed
  by any `background:` **shorthand** override, so V6 redraws it with a `::before "\2630"`.
  Clicking it opens a functional **left drawer `.app-nav-menu`** listing all nav items.
- **Expanded (after in-app navigation / sometimes on load):** the buttons render on the right
  of the header; V5 makes them transparent so they blend into the gradient.
Do NOT force one state (a force-shown hamburger in expanded mode has no drawer). Style both;
that's what V5+V6 do.

---

## 2. Custom CSS — the real styling lever

**Config → Self Service Portal → "Custom CSS" button** does NOT open an inline box. It
navigates to **`/config/email/templates?portalcss=true`** — the portal CSS is stored as an
**email-template-style record**:

- **ID 707, "Portal Custom CSS", Message Group 0** (= the **global/default** CSS, applies to
  ALL clients).
- Open the row → **Edit** → body is a **Monaco code editor** (not a textarea).
- Pre-existing CSS imports **Poppins** and created the old translucent-gray cards — the muddy
  card look was custom CSS, not the theme. We append our blocks after it.

### 2.1 How to edit/persist the Monaco CSS reliably (hard-won recipe)
1. **The first "Edit" click after a page navigation is often swallowed** (sometimes 2–4
   clicks with ~2s waits). Loop: click Edit → wait 2s → JS-check
   `!!document.querySelector('.monaco-editor')` → repeat until true. No "Please wait…" spinner.
2. In edit mode, JS: `const m=monaco.editor.getModels()[0]; m.setValue(m.getValue()+block)`.
   **`setValue` propagates into the save payload** (verified V1–V12). Always append AFTER
   re-reading `getValue()` (it reflects the true server copy) and guard with
   `if(cur.includes('SENTINEL')) return` so retries can't double-append. To EDIT an already-
   appended block pre-save, string-replace in the model and `setValue` the result.
3. **Do NOT install the fetch/XHR save-interceptor for THIS form** — unnecessary and it can
   hang the save on a never-clearing "Please wait…" spinner (record does not commit).
4. Physical-click **Save** (toolbar Save top-left, or the bottom Save). Returns to view mode.
5. **Recover a stuck editor:** re-navigate to `…?portalcss=true&id=707` and redo.
6. **Definitive verification:** reload `/portal` and check *computed styles*. A sentinel scan
   over `document.styleSheets[].cssRules` returns false even when live (comments aren't in
   cssRules); computed styles read in the same JS tick as a style insert can be stale.
- Bump a **sentinel comment** per revision (`SIMVAY-PORTAL-V1…V12`).
- **Preview trick:** inject `<style id="simvay-vN">` into the live portal tab and screenshot;
  reloading drops the injection. **Bisect trick:** truncate the in-page 707 `<style>` at
  `indexOf('/*SIMVAY-PORTAL-V1')` to get a stock-CSS-only state without touching the record.

### 2.2 Portal DOM selector map (dark theme, verified 2026-07-20)

**Chrome / shell**
| Element | Selector | Notes |
|---|---|---|
| Root | `#app-container.portal` (`.portal`) | scope rules under `.portal` |
| Page background (home) | `div.page-portal-background` | stock bg-image lives here; override (V9 adds ambient glows) |
| Header bar | `div.nhd-nav` (fixed, **z-index 99**) | bg follows Portal Color |
| Header logo | `img.nhd-nav-brandingLogo` | white via `filter:brightness(0) invert(1)` |
| Nav buttons / hamburger / avatar | `button.nhd-nav-btn` / `.menubtn` / `.profile-btn` | ⚠ `.menubtn` icon is a background-image — never override with `background:` shorthand; V6 redraws glyph via `::before` |
| Nav drawer | `.app-nav-menu` | dark-teal slide-in panel |
| **⚠ Stacking gotcha** | `div.main{ position:relative; z-index:1 }` | creates a stacking context — **nothing inside `.main` can paint above the nav (z 99)**, regardless of z-index. Don't try to overlay the header from content; hence the V11 pill sits BELOW the bar (top:62px). Don't raise `.main`'s z — scrolled content would cover the header |
| Footer | `footer.page-footer` + `.box1` + `.langdrop` react-select | see V4/V5/V7 notes (navy band = `> div:first-child`, hidden) |

**Home screen**
| Element | Selector | Notes |
|---|---|---|
| Hero title | `h1.search-title` | = Welcome Message ("How can we help?") |
| Emergency chip | `.searchbar-container form.container::after` (V8) | edit the `content` string to change wording/number |
| Search (now a pill) | `.searchscreen .searchbox` → `> div` (flex `row-reverse`) → `svg` + `.searchholder > #searchscreen-searchbar` | V11 pins it `position:fixed; top:62px; right:24px`, 44px circle expanding to 320px on `:hover`/`:focus-within`. **V12 absolutely centers the magnifier** (`svg{position:absolute; right:13px; top:50%; translateY(-50%)}` — the flex layout had left it off-center clipping the bubble edge). Halo autofocuses the input on home load → pill starts expanded until first click elsewhere. Home-screen only |
| Tile grid | `.dashbuttons` (V9: flex, `gap:20px`, `max-width:1260px`, centered); cols `.hvr-bob` neutralized (no width/padding) | stock bootstrap cols made huge uneven gutters |
| Tile card | `button.card.dashbtn` — V9: `width:300px`; V8: `min-height:250px`; glass gradient + `backdrop-filter:blur(16px)` | glass only READS as glass with the V9 ambient glows behind it — over a flat dark bg it looks solid |
| Tile icon circle | `.dashbtn .card-img` — flex-centered (V8; stock baseline layout left icons ~7px low) | teal→sky gradient, brightens on hover |
| Tile title / desc | `.card-title` (1.15rem) / `.card-text` | |
| My Tickets widget | `.portal .main .col-xl-12.px-xl-5` + heading `h1.listwidget-title` (stock near-black → light) | glass treatment shared with cards |

**New Ticket pages (`/portal/newticket?tickettype_id=N`) — V10, all ticket types**
| Element | Selector | Notes |
|---|---|---|
| Page canvas | `main.portal-container-height` | brand gradient replaces flat `#353535` |
| Page title | `.page-title h1` (+ inner `*`) | ⚠ pre-existing custom CSS colored it near-black `#07101b` → forced light |
| Section slabs | `.details-group.card-panel` (stock `#404040`) | glass panels, 16px radius |
| Labels / mandatory hint | `.details-form label` / `.mandatory-hint` (stock pure red) | light gray / soft coral |
| Text inputs | `.details-form input:not(.Select__input):not(.nhd-button):not([type=checkbox]):not([type=radio])`, `textarea` | dark `#141a21`, teal focus ring |
| Dropdowns | `.details-form .Select__control` (+ `--is-focused`, `.Select__menu/__option`) | dark, teal focus |
| Rich-text editor | `.fr-box.dark-theme` → `.fr-toolbar`, `.fr-wrapper` (stock WHITE), `.fr-element`, `.fr-placeholder`, **`.fr-second-toolbar` (stock WHITE strip at bottom)** | all dark; box rounded + clipped |
| Attachments dropzone | `.attachment-container.edit` | teal dashed border, faint teal fill |
| Submit | `input.nhd-button.glow-btn.curve` | teal→sky gradient pill, hover lift |
| Scoping | All V10 rules scoped `.portal .main …` | the footer's language form is ALSO `.details-form` but sits outside `.main` — scoping keeps it untouched |

### 2.3 ⚠ Page-scroll gotcha (the footer became unreachable)
Halo pins `main.portal-container-height`, `.main`, and `.page-portal-background` to exact
viewport-minus-nav heights, and `html/body` are fixed at 100%. With shorter home content the
footer overflowed below a non-scrollable viewport — wheel/keyboard/scrollTop all dead
(bisect-proven not our CSS). **Fix (V7):** `html/body { height:auto; min-height:100(vh|%);
overflow-y:auto }`. Do **NOT** set `main.portal-container-height`/`.page-portal-background`
to `height:auto` — that re-renders the tile area blank.

---

## 3. The applied redesign (record 707, appended after the pre-existing CSS)

Direction (Ryan 2026-07-20): **simple, modern, sharp, clean; dark; clearly-visible
glass/gradient cards with the hover glow; tight even card spacing (wider cards ok); hamburger
nav; footer minimal matching the page background; hero = welcome + emergency chip; search as
a top-bar icon; branded ticket-submission forms.** Brand kit: teal **#00627b**, sky
**#6bbbd5**, slate **#525e77**, grays **#787a7a / #a0a0a0**.

Blocks V1–V8 are listed in the previous sections of this file's history and remain in the
record verbatim; the LATEST blocks (which supersede parts of them) are:

```css
/*SIMVAY-PORTAL-V9 - even card grid + visible glass (ambient glows)*/
.portal .dashbuttons{ display:flex !important; flex-wrap:wrap !important; justify-content:center !important; gap:20px !important; max-width:1260px !important; margin:0 auto !important; }
.portal .dashbuttons .hvr-bob{ width:auto !important; max-width:none !important; flex:0 0 auto !important; padding:0 !important; margin:0 !important; }
.portal button.card.dashbtn{ width:300px !important; max-width:300px !important; }
.page-portal-background{
  background-image:none !important;
  background:
    radial-gradient(900px 420px at 50% -6%, rgba(0,98,123,.45), rgba(0,98,123,0) 60%),
    radial-gradient(560px 420px at 16% 52%, rgba(0,144,179,.20), rgba(0,144,179,0) 70%),
    radial-gradient(620px 460px at 84% 68%, rgba(107,187,213,.14), rgba(107,187,213,0) 70%),
    radial-gradient(500px 380px at 55% 95%, rgba(82,94,119,.25), rgba(82,94,119,0) 72%),
    linear-gradient(180deg,#151b22 0%, #0e131a 100%) !important;
}
.portal button.card.dashbtn, .portal .dashbtn.card,
.portal .main .col-xl-12.px-xl-5{
  background: linear-gradient(158deg, rgba(96,120,146,.30) 0%, rgba(23,32,42,.42) 55%, rgba(14,19,26,.5) 100%) !important;
  -webkit-backdrop-filter: blur(16px) saturate(140%) !important;
  backdrop-filter: blur(16px) saturate(140%) !important;
  border: 1px solid rgba(129,196,219,.28) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.14), inset 0 0 40px rgba(107,187,213,.05), 0 10px 30px rgba(0,0,0,.38) !important;
}
.portal button.card.dashbtn:hover, .portal .dashbtn.card:hover{
  background: linear-gradient(158deg, rgba(110,140,170,.38) 0%, rgba(28,40,53,.5) 55%, rgba(16,22,30,.55) 100%) !important;
  border-color: rgba(107,187,213,.65) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.18), 0 16px 40px rgba(0,98,123,.5) !important;
}

/*SIMVAY-PORTAL-V10 - new-ticket form styling (scoped to .main; footer untouched)*/
.portal main.portal-container-height{
  background: radial-gradient(900px 420px at 50% -6%, rgba(0,98,123,.28), rgba(0,98,123,0) 60%),
              linear-gradient(180deg,#151b22 0%, #0e131a 100%) !important;
}
.portal .main .details-group.card-panel{
  background: linear-gradient(158deg, rgba(96,120,146,.16) 0%, rgba(23,32,42,.42) 55%, rgba(14,19,26,.48) 100%) !important;
  border:1px solid rgba(129,196,219,.18) !important;
  border-radius:16px !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.09), 0 8px 24px rgba(0,0,0,.30) !important;
}
.portal .page-title h1, .portal .page-title h1 *{ color:#eaf3f7 !important; }
.portal .main .details-form label{ color:#c9d4dd !important; }
.portal .mandatory-hint{ color:#ffb4a8 !important; }
.portal .main .details-form input:not(.Select__input):not(.nhd-button):not([type="checkbox"]):not([type="radio"]),
.portal .main .details-form textarea{
  background:#141a21 !important; border:1px solid rgba(255,255,255,.10) !important;
  border-radius:10px !important; color:#eef3f7 !important; padding:8px 12px !important;
}
.portal .main .details-form input:not(.Select__input):focus{ border-color:#6bbbd5 !important; box-shadow:0 0 0 3px rgba(107,187,213,.22) !important; outline:none !important; }
.portal .main .details-form .Select__control{ background:#141a21 !important; border:1px solid rgba(255,255,255,.10) !important; border-radius:10px !important; box-shadow:none !important; }
.portal .main .details-form .Select__control--is-focused{ border-color:#6bbbd5 !important; box-shadow:0 0 0 3px rgba(107,187,213,.22) !important; }
.portal .main .Select__menu{ background:#141a21 !important; color:#c9d4dd !important; border:1px solid rgba(255,255,255,.10) !important; }
.portal .main .Select__option{ background:transparent !important; color:#c9d4dd !important; }
.portal .main .Select__option--is-focused{ background:rgba(107,187,213,.14) !important; }
.portal .main .fr-box{ border-radius:10px !important; overflow:hidden !important; border:1px solid rgba(255,255,255,.10) !important; }
.portal .main .fr-toolbar{ background:#10161d !important; border-color:rgba(255,255,255,.08) !important; }
.portal .main .fr-wrapper{ background:#141a21 !important; }
.portal .main .fr-element{ background:transparent !important; color:#eef3f7 !important; }
.portal .main .fr-placeholder{ color:#8a97a3 !important; }
.portal .main .fr-second-toolbar{ background:#141a21 !important; border:none !important; }
.portal .main .attachment-container.edit{ border:2px dashed rgba(107,187,213,.4) !important; border-radius:14px !important; background:rgba(107,187,213,.04) !important; color:#8a97a3 !important; }
.portal .main input.nhd-button{
  background:linear-gradient(135deg,#00627b 0%, #0090b3 100%) !important;
  border:none !important; padding:10px 34px !important;
  box-shadow:0 6px 18px rgba(0,98,123,.45) !important;
  transition:box-shadow .18s ease, transform .18s ease !important;
}
.portal .main input.nhd-button:hover{ box-shadow:0 10px 26px rgba(107,187,213,.5) !important; transform:translateY(-2px) !important; }

/*SIMVAY-PORTAL-V11 - search as floating top-right pill (expands on hover/focus)*/
.portal .searchscreen .searchbox{
  position:fixed !important; top:62px !important; right:24px !important; left:auto !important; z-index:50 !important;
  width:44px !important; height:44px !important;
  background:rgba(20,26,33,.85) !important;
  border:1px solid rgba(107,187,213,.35) !important;
  border-radius:999px !important; overflow:hidden !important;
  box-shadow:0 6px 18px rgba(0,0,0,.4) !important;
  -webkit-backdrop-filter: blur(8px) !important; backdrop-filter: blur(8px) !important;
  transition:width .25s ease, border-color .25s ease !important;
}
.portal .searchscreen .searchbox:hover, .portal .searchscreen .searchbox:focus-within{
  width:320px !important; border-color:#6bbbd5 !important;
}
.portal .searchscreen .searchbox > div{ display:flex !important; align-items:center !important; height:42px !important; flex-direction:row-reverse !important; }
.portal .searchscreen .searchbox svg{ margin:0 0 0 13px !important; flex:0 0 auto !important; height:42px !important; }
.portal .searchscreen .searchbox svg path{ fill:#9fd3e6 !important; }
.portal .searchscreen .searchholder{ flex:1 1 auto !important; }
#searchscreen-searchbar{ height:42px !important; padding:0 10px !important; font-size:.9rem !important; }
.portal .search-title{ margin-bottom:10px !important; }

/*SIMVAY-PORTAL-V12 - center the magnifier in the search pill*/
.portal .searchscreen .searchbox svg{ position:absolute !important; right:13px !important; top:50% !important; transform:translateY(-50%) !important; margin:0 !important; height:17px !important; width:17px !important; }
#searchscreen-searchbar{ padding-right:40px !important; }
```
*(Superseded-by-later-blocks: V3/V8 card sizing → V9's 300px; V5's inline search-bar styling →
V11's pill; V11's flex svg placement → V12's absolute centering (44px pill ⇒ icon center at
exactly 22,22); V3's glass → V9's stronger glass. All old text remains in 707 harmlessly.)*

**Result (verified live from record 707 + config on clean fresh loads, Mac Chrome,
2026-07-20):** compact hero ("How can we help?" + amber emergency chip) with the **search as
a floating magnifier pill** top-right under the bar (icon perfectly centered; expands to a
field on hover/focus; Enter searches; starts expanded on landing because Halo autofocuses
it); **7 glass cards, 300px wide, uniform 20px gaps, centered** — glass clearly visible
thanks to ambient teal/sky glows behind the grid, brighter top sheen, and stronger blur;
hover glow + lift retained; **New Ticket pages fully branded for every ticket type** (glass
section panels, dark inputs/dropdowns/rich-text editor, teal focus rings, teal dashed
dropzone, gradient Submit); footer and scroll behavior intact.

---

## 4. Done / verified vs. remaining

**Done 2026-07-20 (four passes):** Portal Color→teal; Title→"Simvay Support Portal"; Welcome
Message→"How can we help?" (+CSS emergency chip); Invoices icon fix; theme=Dark; Documents +
My Dashboards hidden; glass redesign with visible glass (V9 glows), tight even 20px grid of
300px cards, centered icons, 1.15rem titles; white logo; hamburger + drawer; blended nav;
search → floating top-right pill with centered magnifier (V11+V12); New Ticket forms restyled
for all ticket types (V10); footer redesign; page-scroll fix (V7). All verified from record
707 + config on clean reloads: home, MT ticket form (type 1), Cyber ticket form (type 34),
Tickets list.

**Remaining / optional:**
- **Login screen** (logged-out) still not visually verified — check in a private window.
- Emergency chip is CSS `content` (not clickable); a `tel:` link would need the Custom HTML box.
- Optionally clear the two Halo-stock background-image URL fields.
- The V11 pill exists only on the home screen (the search element only renders there).
- **Light theme** remains a one-field switch (fix white-on-white text first).
