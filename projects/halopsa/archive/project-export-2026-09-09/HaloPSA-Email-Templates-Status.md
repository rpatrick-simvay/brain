# Simvay HaloPSA Email Templates — Master Status List

**As of:** 2026-07-26 — CORE + PHASE 2 + SALES ORDERS + ALL REMAINING SUBJECTS COMPLETE · #32 internal update de-boxed · 90 standard + 4 custom templates (95 originally; 2 deleted, 1 added)
**Design system:** teal #00627b shell, white S mark + SIMVAY wordmark, corrected footer ((216) 282-8190 / support@simvay.com / SOC line), no em dashes. **Internal/agent emails: left-aligned, NO grey outer background** (−103 style; applied to #32 on 2026-07-26).
**Subject family:** `Simvay Ticket <what happened>: $symptom [ID:$faultid]` (and Simvay-branded equivalents for quotes/billing/portal/appointments), applied 2026-07-17.

---

## ✅ DONE — applied in HaloPSA (27 bodies + 22 subjects)

| ID | Template | New subject | Flow it's tied to |
|---|---|---|---|
| 1 | New Ticket Logged | Simvay Ticket Received: $SYMPTOM [ID:$faultid] | Auto-acknowledgement when a client opens a ticket. CTA → `$linkToRequestUser` |
| 150 | New Ticket Logged (OOH) | Simvay Ticket Received (After Hours): $symptom [ID:$faultid] | After-hours acknowledgement (subject previously had NO ID token — added) |
| 11 | Ticket Update | Simvay Ticket Update: $symptom [ID:$faultid] | Default tech-reply template — highest-traffic client email |
| 65 | Ticket In Progress | Simvay Ticket In Progress: $symptom [ID:$faultid] | SLA response-email flow when work starts |
| 159 | Status Changed | Simvay Ticket Status Update: $symptom [ID:$faultid] | Per-status change notifications |
| 89 | SLA Hold Reminder | Simvay Ticket Needs Your Reply: $symptom [ID:$faultid] | Waiting-on-you reminder (old subject had zero identifiers) |
| 38 | Closure Reminder | Simvay Ticket Resolved - Please Confirm: $symptom [ID:$faultid] | Pending Closure confirmation request |
| 14 | Ticket Closed | Simvay Ticket Resolved: $symptom [ID:$faultid] | Closure email; CSAT smileys preserved |
| 327 | Ticket Closed (Pending Closure) | Simvay Ticket Resolved: $symptom [ID:$faultid] | Green resolved layout; CSAT preserved |
| 41 / 240 | Ticket Closed Automatically (+SLA) | Simvay Ticket Auto-Closed: $symptom [ID:$faultid] | Auto-closure after no response |
| 180 | Closed Ticket Update Reply | Simvay Ticket #$faultid Is Closed: Reply Not Added | Reply-to-closed-ticket bounce notice |
| 142 | Merged Request | Simvay Ticket Merged: Now Tracked as #$mergedrequestid | Ticket merge notice |
| 92 | Quotation Message | Your Simvay Proposal: $QUOTETITLE ($QUOTEREF) | Proposal delivery; CTA → $QUOTEAPPROVAL |
| 249 | Approval of Quote | Approval Needed - Simvay Quote: $QUOTETITLE ($QUOTEREF) | Client quote-approval request; CTA → $QUOTELINK |
| 246 | Quote Approved | *(subject kept — feeds Outlook tracking rules; Ryan's call)* | Post-approval confirmation |
| 136 | Invoice Email | Invoice #$INVOICEID from Simvay | Invoice card |
| 345 | Invoice Reminder | Payment Reminder from Simvay: Invoice #$INVOICEID | Amber payment reminder (was vague + identical to credit note) |
| 342 | Credit Note | Credit Note from Simvay (#$INVOICEID) | **Bug fixed: subject used to say "Invoice from $ORNAME"** |
| 80 | Welcome Email | Welcome to the Simvay Support Portal | Password removed; "Login details" subject was now-false + phishy |
| 252 | Welcome Email (Quote) | Welcome to the Simvay Support Portal | Same no-password rework |
| 156 | End User Appointment | Your Simvay Appointment: $APStartDate | Booked-with card |
| 192 | Appointment Reminder | Reminder: Your Simvay Appointment $apstarttime | Old subject had zero identifiers |
| −106 | Ticket Completed (custom) | *(subject untouched)* | Full client shell; fires from Resolve Ticket / Ready to Invoice |
| −103 | NEW TICKET (custom) | *(pipe subject kept — 10 notification rules)* | Light internal card |
| −112 | Invoice Paid (custom) | *(pipe subject kept — mailbox rules)* | Light internal card |
| — | *Cleanup* | | Phone typo fixed; −100/−109 deleted; #318/32 internals left as-is by design |

**⚠ Recommended before heavy reliance:** one test ticket + an emailed reply to confirm inbound reply-matching still lands on the ticket (the `[ID:$faultid]` token is retained everywhere, but threading wasn't test-verified).

## ✅ DONE — 2026-07-18 session (Phase 2 + sales orders + fixes, 17 more)

| ID | Template | New subject | Notes |
|---|---|---|---|
| 74 | Sales Order | Simvay Sales Order #$ORDERID: $ORDERTITLE | Client-safe card (ID/title/date/PO/total/notes). **$ORDERCOST and $ORDERPROFIT removed — margin no longer leaks.** ⚠ The internal NEW SALES ORDER notification uses this same template, so the internal alert no longer shows cost/margin; if that data is wanted internally, clone a custom internal template (like −103) and rewire the notification |
| 165 | Order Confirmation | Your Simvay Order Confirmation | Branded "order attached" shell |
| −106 | Ticket Completed | Simvay Ticket Completed: $symptom [ID:$faultid] | **Date bug fixed:** $datecleared is empty when the Resolve action fires (ticket not yet cleared/closed — verified on ticket 51442), so "completed by Simvay on ." rendered blank. Removed the date phrase; the email timestamp carries it. Also killed the fake "Re:" subject (Halo auto-appends [ID:...] only when missing, so no double token) |
| 186 | Password Reset | Reset Your Simvay Portal Password | CTA → $PASSWORDRESETLINK |
| 189 | Password Reset Confirmation | Your Simvay Portal Password Was Changed | Amber security-notice treatment |
| 147 | User Validate Email | Simvay Support Portal Login Validation (kept) | **Plaintext $password removed** (same policy as Welcome emails); CTA → $validate |
| 201 | Two Factor Verification Code | Your Simvay Verification Code (was "HaloPSA") | $CODE in large monospace card |
| 231 | Email Address Confirmation | Confirm Your Email for the Simvay Support Portal (was "Welcome to HaloPSA...") | CTA → $CODE; portal link $linkToWebapp; "Powered by HaloPSA" removed |
| 255 | New User Account Request | Finish Setting Up Your Simvay Portal Account | CTA → $CODE |
| 291–309 | 7 account-security notices (password/username/email changed, 2FA on/off, authenticator added/removed) | "...on Your Simvay Account" family | Amber Security Notice shell + "didn't make this change?" card; $CURRENTDATE / $NEWUSERNAME / $NEWEMAILADDRESS preserved |
| 318 | Quote Viewed by End User | (pipe subject kept for Outlook rules) | Light internal SIMVAY card + data grid, scannable |

## ✅ DONE — 2026-07-26: #32 Technician Update de-boxed (internal ticket-update email)

| ID | Template | Subject | Notes |
|---|---|---|---|
| 32 | Technician Update | `[ID:$faultid] \| $ACTIVITY/$USERNAME/$AREA` (pipe format kept) | **This is the internal agent "Ticket Updated" email** — Notification id 30 "Ticket Update by User \| Cybersecurity" (+ the per-agent UPDATED TICKET notifications) → template #32. Body already had the full client shell (earlier docs wrongly listed it as stock). Per Ryan: removed the wide grey background + centered 600px box, left-aligned the card (−103-style internal look). Inner card untouched (teal header, info grid, $ALLACTIONS conversation box, centered View Ticket button, footer). Done via direct DOM mutation — see Runbook 03 §2.8 for the insertHTML shell-wrapping gotcha + blocked-read workaround. Verified persisted after reload |

## 🗺 SALES ORDER / APPROVED ORDER EMAIL FLOWS (mapped 2026-07-18)

**External (client-facing):**
| Trigger | Template | Notes |
|---|---|---|
| Agent emails a Sales Order to the client ("Sales Order emailed") | #74 Sales Order | Now branded + client-safe (no cost/margin) |
| Order confirmation emailed | #165 Order Confirmation | Branded; no config wiring (built-in flow) |
| Client approves a quote | #246 Quote Approved | Sent to the quote recipient after approval; pipe subject kept |

**Internal (agent notifications, Config > Notifications):**
| Notification | Trigger + conditions | Recipients | Template |
|---|---|---|---|
| NEW SALES ORDER | Sales Order created, Status = 1 - NEW ORDER | 6 agent subscribers (email + popup + push) | **−115 NEW SALES ORDER (Internal)** — created 2026-07-18 with $ORDERCOST/$ORDERPROFIT restored; pipe subject "NEW SALES ORDER \| $ORDERID \| $AREA \| $ORDERTITLE" kept for mailbox rules. Rewired from #74 |
| APPROVED QUOTE | Quote approved by User, Approval Status = Approved | 5 agent subscribers (email) | #246 Quote Approved (dual audience: same email the client gets) |
| Ticket Update by User \| Cybersecurity (id 30) | Ticket Updated by User - Assigned to Recipient | 6 agent subscribers (email) | #32 Technician Update — de-boxed/left-aligned 2026-07-26 |
| PURCHASE ORDER ISSUED | Purchase Order created | 3 subscribers | Show in Halo only (no email) |
| ORDER to INVOICE | Ticket Status Changed (on the auto-created ORDER ticket) | 2 subscribers | Show in Halo only (no email) |

Also: every new Sales Order auto-creates a ticket via template "ORDER \| Sales Order: $ORDERID \| $ORDERTITLE" (Config > Sales Orders) for delivery/admin comms — client emails from that ticket use the normal ticket templates.

## ✅ REMAINING SUBJECTS — all updated 2026-07-18 (21)

234 "Your Simvay Account Details" · 35 "Simvay Ticket: $symptom $SUPP…" · 56 "Simvay Ticket Cancellation $SUPP…" · 59 "Simvay SLA Breach Notice $SUPP…" · 62 "Simvay Request Update $SUPP…" · 171 "Simvay Ticket Feedback Received" · 330 "Simvay Quote Rejected: $QUOTEREF" · 351 "Simvay Quote Countersigning Needed: $QUOTEREF" · 153 "Your Simvay Contract" · 261 "Your Simvay Agreement Overview" · 195 "Your Simvay Appointment Schedule" · 198 "Simvay Contract Schedule Closure" · 204 "Your Simvay Project Schedule" · 357 "Simvay Agent Booking Reminder" · 279 "Simvay Invoice Approved: #$INVOICEID" · 282 "Approval Needed - Simvay Invoice" · 130 "Approval Needed - Simvay Purchase Order" · 285 "Simvay Payment Failed: Invoice #$INVOICEID" · 276 "Simvay Payment Notification" · 174 "Simvay Knowledge Base: $kbsubject" · 312 "Simvay Knowledge Base: $KBTITLE". Supplier subjects keep the $SUPPSTART$SUPPREF$SUPPEND tokens (supplier reply matching). Kept as-is on purpose: #95 (already Simvay-branded), pipe internals #32/#318/#246/−103/−112 (mailbox rules), and the not-doing bucket (unused features).

## 🔧 PHASE 3 — supplier & internal (light touch, ~7)

| ID | Template | Flow it's tied to |
|---|---|---|
| 95 | Supplier PO Message | PO emailed to suppliers — **subject still says "Simvay Systems"; fix naming at minimum** |
| 35 / 56 / 59 / 62 | Supplier Ticket / Recall / SLA Breach / Message | Supplier ticket correspondence (B2B; light branding) |
| ~~32~~ | ~~Technician Update~~ | **Done 2026-07-26** — was already Simvay-branded (not stock as previously listed); de-boxed/left-aligned per Ryan |
| 171 | Feedback Notification | Internal alert when CSAT feedback arrives |
| 234 | Agent Invitation | New agent account setup |

## ⏸ DEFERRED — confirm whether the flow is used before touching

| ID | Template | Flow it's tied to |
|---|---|---|
| 330 / 351 | Quote Rejected / Quote Countersigning | Fire only if quote rejection / countersigning flows are enabled — confirm |
| 153 / 261 | Client Contract / Contract ("Agreement Overview") | Contract emailed to client |
| 195 / 198 | Appointment Schedule / Contract Schedule Closure | Contract-schedule digest emails |
| 204 / 357 | Project Schedule / Agent Booking Reminder | Project appointments / agent booking flows |
| 279 / 282 | Invoice Approved / Approval of Invoice | Internal recurring-invoice approval flow |
| 130 | Approval of PO Message | Internal PO approval flow |
| 285 | Stripe Payment Failure | Only fires if Stripe payments are configured |
| 276 | Payment Notification | Internal billing notification list |
| 174 / 312 | KB Article emails | Only when manually emailing a KB article |

## 🚫 NOT DOING

| ID | Template | Reason |
|---|---|---|
| 86 | Unapproved Change Message | **Change-control/CAB workflow — not set up at Simvay (per Ryan 2026-07-17). Marked unused** |
| 50 / 53 / 258 | Approval Message / Approval Outcome / Approval Reminder | Tied to Ticket Approval Processes — the same change-control machinery that isn't set up. **Marked unused** (note: quote approvals use #249/#246 instead, so nothing client-facing is lost) |
| 139 | Release Email | Halo software-release management feature — not used |
| 183 | Remote Support Invitation | GoToAssist/BeyondTrust integration only |
| 243 | Service Status Update | Service-catalog subscriber feature — not used |
| 321 / 324 / 333 | Asset Drop Off / Collection / Swap | Lapsafe/asset-logistics Actions — not used |
| 360 | Campaign Approval | Mail Campaigns feature |
| 270 / 273 / 348 / 354 | User Status Reminder / NHServer Error / Admin Mode / Teams Chat Closure | Internal/system notices, fine as stock |
| 315 / 336 / 339 | Timesheet notices | Internal agent nudges, fine as stock |

## 🗑 REMOVED / INERT

| ID | Template | Status |
|---|---|---|
| −100 | Purchase Order Created | **Deleted 2026-07-17** (empty body, zero usage) |
| −109 | Quote Viewed By Client | **Deleted 2026-07-17** (zero usage; live alerts come from #318) |
| 100 | "NOT IN USE" | Halo system row — cannot be deleted, inert |
| 103–127 | User Email 02–10 (9 rows) | Legacy placeholders — cannot be deleted, inert |

---

**Tally:** 46 templates with redesigned/adjusted bodies (incl. new −115 and the 2026-07-26 #32 de-box) · ~60 new subjects · every subject in the instance is now either Simvay-branded, an intentional pipe format, or in the unused not-doing bucket.
**Remaining body work (subjects done, bodies still stock):** Phase 3 suppliers/internal (95, 35/56/59/62, 171, 234) and the deferred bucket (330/351, 153/261, 195/198/204/357, 279/282/130, 285, 276, 174/312) — light-touch restyles when Ryan wants them.
**Outstanding recommendation:** test one ticket + emailed reply to confirm inbound reply-threading.
