# HaloPSA Runbook 16 — Template-94 "try upsell by 20%" to-do item blocks closure (found 2026-08-31)

**Symptom.** Closing renewal opp **50486** (NRCS RETAINER, quote 10248 sent 8/13) was refused. The ticket carries one open to-do item, **"try upsell by 20%"**, `addedby: 0` (system-added, not an agent). Halo refuses closure while any to-do item is incomplete.

**Where it comes from.** Every ticket carrying it is `source: 2` (Automated Tickets rule "Expiring Agreements | 90 Days") on **template 94**. The template's to-do list evidently carried the item for roughly **2026-03-27 to 2026-06-06**; no ticket created after 06-06 has it (33 checked). Some same-day siblings have no item, which is consistent with agents deleting it on those tickets before closing (a deleted to-do leaves no trace). Survey: 79 automation/pattern renewal opps checked, 13 carried the item.

**Tickets still carrying it, incomplete, and OPEN (will hit the same wall):**

| Opp | Summary | Client | Status |
|---|---|---|---|
| 50486 | RETAINER-080125-073127 | North Royalton City Schools | 27 Quote Sent |
| 50646 | M365-081225-081126 | City of Brooklyn | 27 Quote Sent |
| 50863 | EMTS-090125-083126.2 (merged with 50864/50865) | City of Parma Heights | 4 |
| 50867 | M365-090122-083126 | Great Lakes Brewing | 24 Qualified |
| 50039 | C2-062825-062726 | Olmsted Township | 19 Rejected |

Also carried it, already closed: 50026, 50034, 50067, 50068, 50839 (ticked done by Oswald/Soltis), 50864, 50865, 50936 (closed with the item still open, so the block is either newer than 7/21 or bypassable via merge/other route).

**Fix per ticket.** Ticket sidebar → To-Do list → tick the item (or `...` → delete it) → then Close. Nothing to do on template 94 itself; it no longer emits the item. If the block should not exist at all: Configuration → Tickets → General Settings → To-Do Lists, "prevent closure until all to-do items complete" (not readable through the connector; unverified).

**Report rule (Runbook_Renewal_DeepDive §6.5).** The weekly run should flag any open renewal opp with `todo_count > 0` and an undone item in §5 Data hygiene, since it silently blocks the close-out step.


**Decision (Ryan, 2026-08-31):** not actively replicating (none since 06-06), so no cleanup sweep. Leave the remaining five to be cleared one at a time as each opp is closed. Do not raise them as action items in the weekly report; a one-line hygiene note is enough.

**Standing instruction:** update this doc when the to-do source is confirmed (template 94 history or a ticket rule) or when the closure-block setting is verified.
