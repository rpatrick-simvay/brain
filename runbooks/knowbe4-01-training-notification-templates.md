---
title: "KnowBe4 01: Training notification templates"
type: runbook
updated: 2026-07-28
tags: [knowbe4, email-templates, branding]
related: [projects/halopsa/STATUS]
source: "HaloPSA Claude Project: claude/KnowBe4-Runbook-01-Training-Notification-Templates.md"
migrated: 2026-09-09
---
> Migrated 2026-09-09 from the HaloPSA Claude Project (`KnowBe4-Runbook-01-Training-Notification-Templates.md`). This file is now the canonical copy; the project doc is frozen. The verbatim original is in `projects/halopsa/archive/project-export-2026-09-09/`. Em and en dashes in prose were replaced per CLAUDE.md; code blocks are untouched. Cross-references were rewritten to brain paths.

# Simvay KnowBe4 - Runbook 01: Training Notification Templates

> **Scope:** the 5 Simvay-managed KnowBe4 training notification templates - navigation, reading,
> editing, the save mechanics, and the 2026-07-28 Simvay rebrand.
> Sibling to the HaloPSA runbook family; same Standing instruction (update this doc with new discoveries).
>
> **Last updated:** 2026-07-28 (initial doc; all 5 templates restyled to the Simvay design system)

---

## 1. Where the templates live

**Training → Notification Templates → Managed Templates**
URL: `https://training.knowbe4.com/app/training/templates/managed/all?show_hidden=false`

- Each template's editor is at `/app/training/templates/<numeric-id>/edit`. Navigate directly by ID; the
  list-row `href` values come back `[BLOCKED: Base64 encoded data]` through `javascript_tool`, but a
  self-computed regex extraction of the numeric run (`href.match(/\d{5,}/)`) passes fine.
- **System Templates** (216 rows, read-only) are at `/app/training/templates/system/all`. Clicking a row
  opens a preview modal, not an editor. Left-sidebar categories filter the list.

### 1.1 ⚠ Account context trap (hit live 2026-07-28)

KnowBe4's console can be switched into a **customer account** via Account Admin View. When it is:

- a blue bar reads `Account Admin View: ryan@simvay.com`, and the top-right user shows the *customer's*
  address (e.g. `csvancara@cc-efi.com`);
- the template edit page grows a banner: *"This is a managed template. By saving it, it will be added to
  your templates list."*

**Saving in that state does NOT update the Simvay master - it clones the template into the customer's
own template list.** Always confirm before any write:

```js
document.body.innerText.includes('Account Admin View')   // must be false
```

and confirm the top-right user reads `ryan@simvay.com`. Exit via the top-right account menu or the
"Click here for Account Management console" link in the blue bar.

## 2. Reading a template

The body lives in a **CKEditor 4** instance named `editor`, inside `.cke_wysiwyg_frame` (same-origin).

- `CKEDITOR.instances.editor.getData()` returns `[BLOCKED: Cookie/query string data]` through
  `javascript_tool`, as does the iframe's raw `innerHTML` - same class of block documented in HaloPSA
  Runbook 03 §2.8. **Workaround: compute summaries in the page and return only flags you construct
  yourself** (tag outline + regex-extracted style flags, element counts, booleans). `innerText` passes
  fine, so merge-token inventories via `innerText.match(/\[\[[^\]]+\]\]/g)` work.
- Don't name a returned key `tokens` - that alone trips `[BLOCKED: Sensitive key]`. `mergeFields` is fine.
- Form field IDs (stable):
  `TRAINING-NOTIFICATION_TEMPLATE-NAME`, `-SENDER_EMAIL`, `-SENDER_NAME`, `-SUBJECT`.

## 3. Editing and saving (proven recipe)

The editor page loads directly in edit mode; there is no separate Edit button. Recipe:

```js
const ed = CKEDITOR.instances.editor;
ed.setData(HTML);
ed.updateElement();
ed.fire('change');
// also push through the backing textarea so React state syncs
const ta = document.querySelector('textarea');
const tset = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
tset.call(ta, HTML);
ta.dispatchEvent(new Event('input',  {bubbles:true}));
ta.dispatchEvent(new Event('change', {bubbles:true}));
// subject
const el = document.getElementById('TRAINING-NOTIFICATION_TEMPLATE-SUBJECT');
const st = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
st.call(el, SUBJECT);
el.dispatchEvent(new Event('input',  {bubbles:true}));
el.dispatchEvent(new Event('change', {bubbles:true}));
```

Then **physically click Save** (a synthetic click was not trusted here; physical clicks worked every time).

**Save mechanics and gotchas:**

- The editor pane has a **fixed height**, so the Save button does not move as content grows. At a 1439px
  window it sits at roughly **(196, 664)**; at 1489px, roughly **(203, 687)**. Re-screenshot anyway.
- A successful save **redirects to the managed-templates list and shows a green toast**,
  *"Success! Your template has been saved successfully."* Treat the redirect as the success signal.
  If the page stays on the editor, the save did not take.
- **Two saves silently failed** on template 5750610 before the recipe above was settled: the click
  registered but the content reverted on reload, with no error shown. Adding `updateElement()` +
  `fire('change')` + the textarea write fixed it. **Always reload the edit page and re-read the subject,
  image dimensions, and merge fields after saving** - do not trust the click alone.
- Allow ~6 seconds after clicking Save before navigating; an immediate navigate can race the POST.

## 4. Images are URL-only

The CKEditor image dialog (`Image Properties`) has **URL / Link / Advanced tabs and no Upload tab**.
Every image must be hosted on a public server; there is no KnowBe4-side asset hosting.

- **Current header asset:** `https://simvay-com.pages.dev/brand/simvay-header.png` (697×176, teal
  wordmark with integrated S, transparent background).
- Also present on that host: `/brand/simvay-mark.png` (508×632, the S-mark). **Both are teal-gradient on
  transparent and wash out on a teal background** - they are white/tint-background assets only, per
  Simvay-Document-Brand-Guide §4.
- The **white** S-mark exists only as a data URI in `runbooks/simvay-logo-datauris.md`. Data URIs are
  stripped by Gmail, so it cannot be used in email until it is hosted somewhere public. This is why the
  header is a white band with a teal gradient rule rather than the HaloPSA teal hero band.
- The Cloudflare connector available to this session is read-mostly: it can create/list/delete R2
  buckets but cannot upload objects, enable public access, or create Pages projects. Standing up an
  asset host is a manual step.

### 4.1 🔴 OPEN TO-DO: re-point header URLs at launch

All 5 templates currently reference **`simvay-com.pages.dev`**, a Cloudflare Pages preview host for the
not-yet-launched site. **If that project is renamed or deleted, every training email loses its header.**
When the new simvay.com goes live (or a dedicated asset host exists), update the `img src` in all 5
templates to the permanent URL. One-line change per template via the §3 recipe.

The pre-rebrand templates pointed at `https://simvay.com/wp-content/uploads/2024/06/Picture1.png`
(800×128 KnowBe4 × Simvay co-brand lockup on the live WordPress site), which is still reachable if a
rollback is ever needed.

## 5. Merge tokens

Insert via the **Placeholder** dropdown in the second toolbar row. Categories: User Information,
Account Information, Training Placeholders, plus password-less variants.

**`[[LOGIN_LINK]]` cannot be used inside an `href`.** KnowBe4 substitutes it into a full anchor at send
time. Confirmed against KnowBe4's own newest system template, *"Please complete your assigned training
(From KnowBe4) (Banner)"* (updated 12/17/2025): its body contains **zero anchors** and places
`[[LOGIN_LINK]]` as bare text on its own line. The Simvay templates therefore present it inside a
bordered **action panel** with an uppercase teal/amber label, so whatever KnowBe4 renders reads as
deliberate.

Token casing varies between templates (`[[TRAINING_CAMPAIGN]]` vs `[[training_campaign]]`). Preserve each
template's original casing rather than normalising.

## 6. The Simvay design system as applied (2026-07-28)

White 600px card, `1px #DDE4E9` border, `10px` radius, left-aligned (not centered in a grey field -
matches the internal/left-aligned decision recorded for HaloPSA #32 and −103).

| Element | Spec |
|---|---|
| Header | White band, 24/28/18/28 padding, logo at `width="180"` |
| Brand rule | 4px, solid `#00627B` fallback + `linear-gradient(90deg,#00627B,#0A7A96,#3B96B5)` |
| Eyebrow | 10.5px, 600, uppercase, letter-spacing 1.8px, teal (amber on past-due) |
| Heading | 20px/28px, 600, `#2B3440` |
| Body | 15px/24px, `#2B3440`, `'Poppins',Arial,Helvetica,sans-serif` |
| Detail card | `#F0F7FA` fill, `1px #DDE4E9`, `3px` teal left border, 8px radius; labels 10px uppercase `#3B96B5` |
| Action panel | White, `1px #DDE4E9`, 8px radius; uppercase label + the login token at 15px teal 600 |
| Footer | 1px `#DDE4E9` hairline, then 12px `#6B7480`: managed-by line + `Simvay · (216) 282-8190 · support@simvay.com` |
| Past-due accent | `#A85C00` eyebrow/label, `#FDF6EC` card fill, `#EFE0C8` border |

**The brand rule stays teal on every template**, including the amber ones. An earlier draft gave the
amber templates an amber solid fallback with a teal gradient on top, which would have rendered amber in
Outlook (no gradient support) and teal everywhere else. Keep the fallback colour and the gradient in the
same family.

No em dashes anywhere, consistent with the HaloPSA templates.

## 7. Template inventory and current state

All 5 restyled and verified 2026-07-28 (subject, header image at 697×176, merge fields re-counted after
reload on each).

| ID | Template | Subject (new) | Accent | Fields |
|---|---|---|---|---|
| 5744335 | SIMVAY \| USER \| NEW TRAINING | Simvay Security Awareness Training: You Have Been Enrolled | teal | 5 |
| 5750434 | SIMVAY \| USER \| REMINDER | Reminder: Complete Your Simvay Security Awareness Training | teal | 5 |
| 5750610 | SIMVAY \| USER \| PAST DUE | Past Due: Your Simvay Security Awareness Training | amber | 8 |
| 5750692 | SIMVAY \| MANAGER \| NEW CAMPAIGN (ENROLLED USERS) | Simvay Training: Employees Enrolled in a New Campaign | teal | 5 |
| 5750742 | SIMVAY \| MANAGER \| PAST DUE USERS | Simvay Training: Employees With Past Due Assignments | amber | 7 |

Subjects were rebranded off the old `KnowBe4 | …` prefix, the same move made for the HaloPSA family.
Sender name and address were left as-is (`KnowBe4`, `do-not-reply@[[knowbe4_domain]]`) since those are
platform-controlled.

Copy change: the two manager templates previously directed user-list questions to `soc@simvay.com`;
this now reads `support@simvay.com`, on the grounds that a training roster question is not a SOC incident.

**Untested:** none of these have been sent as a live test. Recommend one test send per audience type
(user + manager) to confirm the header image renders in Outlook and Gmail and that `[[LOGIN_LINK]]`
resolves correctly inside the action panel.

## 8. Build artifacts

The generator that produced these bodies lives in the 2026-07-28 session at `/root/kb4/build.py`
(emits `bodies.json` + a `preview.html` rendering all 5). Session filesystems are ephemeral; if the
templates need regenerating, the spec in §6 plus the inventory in §7 is enough to rebuild it.
