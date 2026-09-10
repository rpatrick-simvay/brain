# Sales Executive role — pre-Wave 3 snapshot (2026-08-18)

GUID: `febac04c-a0f4-4c36-bc6e-549c06dcb710` (id_int 8). Holders per §6.1: Fogarty(22, disabled), Schilling(25, live holder), Oswald(3).

Captured VIEW-mode Permissions panel text (5931 chars) immediately before Wave 3 edits, via Claude/Chrome. Local copy: `/home/claude/rollout/snapshots/SalesExec_pre-wave3_2026-08-18.txt`.

Values relevant to the Wave 3 target list (brief: `salesexec.md`), as found before editing:

- Reporting Access Level = **No Access** (target: Read Only)
- Assets Access Level = **Read, Modify and Delete** (target: Read Only)
- Knowledge Base Access Level = **Read, Modify and Delete** (target: Read and Modify)
- Suppliers Access Level = Read and Modify (target: Read Only — expect non-editable per Runbook 09 §11.5 carry-forward flag)
- Sales Orders Access Level = **Read, Modify and Delete** (target: Read and Modify)
- Purchase Orders Access Level = Read and Modify (target: Read Only)
- Billing Details Access Level = raw **3** = Read and Modify per Runbook 09 finding 10 (target: Read Only)
- Invoices Access Level = **Read, Create, Modify and Delete** (target: Read Only)
- Supplier Contracts Access Level = Read and Modify (target: No Access — expect non-editable)
- Timesheets Access Level = Read and Modify (All) (target: Read and Modify (own))
- Software Licencing Access Level = Read and Modify (target: No Access)
- Tickets Permissions: Can edit closed Tickets=Yes, billing-time adjust=All, billing recalc=Yes, cross-team assign=Yes, edit unassigned-to-them=Yes, priority escalation override=Yes, Treat as Spam=Yes, action visibility edit=Yes, export=Yes — all target No
- Ticket Type Restrictions: Allow use of all Ticket Types = Yes (target: No + explicit allow-list: Lead, Opportunity, Quick Quote, Contract Renewal, New Order, Project, Project Task)
- Approval Process: My Approvals Page Access = No Access (target: the non-"No Access" access-granting option)
- Billing Permissions: Can View Agent Costs = Yes (target No), Can review Expenses = Agents I manage (target None); Item Costs/Prices/SKU untouched (Read and Modify, declined to stay)
- Configuration: Can Create SQL Data Sources = Yes (target No); Can Use Data Sources = Query Builder and Data Sources (target: cleared/Not set)

Not touched per brief: Services Access Level, CRM, Sales, Quotations, Client Contracts Access Level, Asset Type Restrictions (stays Allow all=Yes).

See `claude/HaloPSA-Runbook-09-Claude-Access-Architecture.md` §11 for the Wave 3 deployment-plan context and reconciled targets.
