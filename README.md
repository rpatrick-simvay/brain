# brain

Ryan Patrick's working knowledge repository. Canonical, versioned, agent-readable. Every Claude session (Cowork, Claude Code, chat) starts by reading `INDEX.md`, then the `STATUS.md` of whatever it is working on, and ends by writing back.

This is not a wiki and not a notes dump. It holds what a future session needs to pick up work without re-deriving it: briefs, decisions, status, logs, runbooks, people and client context.

## Layout

```
INDEX.md                  map of contents; read first, every session
CLAUDE.md                 operating rules for any agent working in this repo
projects/<name>/          one folder per initiative
  BRIEF.md                what and why; stable
  DECISIONS.md            dated, append-only, one line each
  STATUS.md               where it stands and the next three actions; overwritten each session
  LOG.md                  session summaries; append-only
  archive/                verbatim copies of source docs, when they exist
clients/<slug>.md         per-client context (engagement, stack, contacts, quirks); no secrets, no evidence
people/<slug>.md          relationship and role context; no sensitive personal data
runbooks/<name>.md        repeatable procedures with exact steps
meetings/YYYY-MM-DD-<topic>.md   one-page meeting notes (decisions, actions, owners)
areas/<name>.md           standing responsibilities that are not projects (SOC, fractional CISO, partner track)
```

## Conventions

- Markdown with YAML frontmatter (`title`, `type`, `updated`, `tags`, `related`). Wikilinks (`[[projects/anvil/STATUS]]`) are welcome; Obsidian renders them, agents grep them.
- Dates are ISO (2026-09-09). Decisions carry the date and who made them.
- No secrets, tokens, key files, or client evidence, ever. Client names are allowed (this repo is private); client credentials and evidence live in Anvil.
- No em-dashes or en-dashes in anything written here. Files under `archive/` are verbatim records and are left as they were.
- Prefer editing STATUS.md over adding a new file. Prefer one line in DECISIONS.md over a paragraph.
