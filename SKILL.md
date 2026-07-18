---
name: infinite-memory
description: >-
  Persistent, file-based project memory for Claude Code. No worker, no database,
  no cloud — just Markdown + raw transcripts on your own disk. Use this skill when
  the user types /infinite-memory, /recordar, /recall, says "save this to memory",
  "update the memory", "what do you know about this project", "where did we leave
  off", "bring context", or when closing meaningful work (a feature, fix, decision,
  delivery). Also at the START of a session to catch up. Survives PC shutdowns: the
  raw transcript is copied every turn by a Stop hook, so a session is never lost.
---

# Skill: Infinite-Memory

Persistent memory for every project you work on, stored as plain files under a
single **memory root** you choose once. Works across Windows / macOS / Linux.

## Where the memory lives (memory_root)

Everything is stored under a single root folder, resolved by
`scripts/mem_config.py` (env `INFINITE_MEMORY_ROOT` → `~/.claude/infinite-memory/config.json`
→ default `~/infinite-memory`). Structure:

```
<memory_root>/
  _global/
    PROFILE.md        # who the user is, fixed preferences (read every session)
    INDEX.md          # map of all projects (which exist; not auto-updated stats)
    CREDENTIALS.md    # optional, user-managed secrets (never commit)
  <project>/          # = basename of the project's working directory
    INDEX.md          # "Latest state" + decisions + focus (read on startup)
    sessions/
      YYYY-MM-DD.md   # per-day log: Asked / Done / Decided / Pending
    decisions.md      # optional: design decisions
    transcripts/      # raw .jsonl copies (auto, every turn — the black box)
```

`<project>` = the basename of the current working directory. Nothing is
hardcoded; if a project has no folder yet, it's created on first save.

## FIRST RUN — configure the memory root

When `/infinite-memory` is invoked, run `python scripts/mem_config.py` (or the
installed copy at `~/.claude/infinite-memory/scripts/mem_config.py`) to check if
`memory_root` is set.

- **If already configured:** proceed to "Active mode" below.
- **If NOT configured:** ask the user where to store their memory. Use
  AskUserQuestion with sensible options:
  - `~/infinite-memory` (default, in the home folder)
  - A synced folder (Dropbox / OneDrive / iCloud / Google Drive) so memory
    follows them across machines
  - An external drive / custom path
  Then persist it: `python scripts/mem_config.py set "<chosen path>"`. Create
  `_global/PROFILE.md` from `templates/PROFILE.md` and ask the 2-3 questions in it
  (name, role, fixed preferences). Confirm the location back to the user.

> Note: for the memory to follow you to another computer, put the root in a
> synced folder. On a cloud/web Claude Code that can't see your local disk, the
> file-based memory won't be available — use the desktop app or CLI on your own
> machine.

## Active mode (persists for the whole session once /infinite-memory is on)

Once activated, without being asked again:

1. **On startup:** immediately read the previous context —
   `_global/PROFILE.md`, `<project>/INDEX.md`, and the last 2-3 files in
   `<project>/sessions/`. If something doesn't add up, open the newest `.jsonl`
   in `transcripts/` and read the raw detail. Start up-to-date; never make the
   user re-explain.
2. **Auto-save (do NOT ask):** whenever a meaningful block of work closes (a
   feature, fix, decision, delivery, commit/deploy, or before a big topic
   switch), update `INDEX.md` ("Latest state" section) AND append to
   `sessions/YYYY-MM-DD.md` (Asked / Done / Decided / Pending). Update in place,
   don't duplicate. Touch BOTH the session file and the INDEX header — a stale
   INDEX header is what makes a new session look out of date.
3. **Power-off protection (already active):** the raw transcript is copied by a
   Stop hook every turn — never lost. The curated summary (INDEX/sessions) is
   what YOU keep current per block (step 2). On startup, if the newest `.jsonl`
   is clearly newer than the INDEX, a session died uncommitted: reconstruct from
   the raw transcript and bring the INDEX up to date BEFORE continuing.
4. **Continuous enrichment:** before re-asking the user about a decision, ID,
   credential, command, or "why did we do X", search memory first
   (INDEX/sessions/decisions/transcripts). Memory is the source of truth.

## /recordar  (or "save this", or when closing work)

1. `<project>` = basename of the current working directory. Memory dir =
   `<memory_root>/<project>/`.
2. Append/create `sessions/YYYY-MM-DD.md` (today) with **Asked**, **Done**,
   **Decided**, **Pending** — concrete: files, commands, decisions, IDs. If the
   day file exists, add what's new; don't repeat.
3. Update `INDEX.md` → "Latest state" with a 3-6 line summary of today + date.
   Keep the previous state below as history (don't delete it).
4. If there were design decisions or deliveries, also update
   `decisions.md` / `deliverables.md` (create if missing).
5. Copy the raw transcripts:
   `python <scripts>/sync_transcripts.py "<absolute path of the cwd>"`
6. Confirm to the user which files you touched (1-2 lines).

## /recall <topic>  (or "what do you know about X", "bring context")

1. Read `_global/PROFILE.md` + `<project>/INDEX.md` if not done yet.
2. Grep `<topic>` across `<memory_root>/<project>/` (INDEX, sessions/, decisions,
   deliverables) and `_global/`.
3. For deep recall of a conversation, grep/read the `.jsonl` in `transcripts/`.
4. Return a selective summary (top findings), not full dumps.

## Auto-save (anti power-off)

A global `Stop` hook (installed by `install/`) runs `sync_transcripts.py` in the
background after every turn → the durable copy in `<memory_root>/<project>/transcripts/`
stays current with zero manual action. It's a file copy, not a worker: it doesn't
block tools and can't crash a session. This does NOT replace /recordar: the curated
summary (INDEX/sessions) is still updated by you/the model when closing work; the
hook only shields the raw black box.

## Rules

- Files + ONE safe hook only (the async `Stop` sync). NO worker, NO blocking hooks.
- Update instead of duplicating. The raw layer (`transcripts/`) is ground truth:
  nothing is ever lost.
- Write `.md` files in UTF-8.
- `<project>` is always the basename of the working directory — never hardcode a path.
- If a project has no folder in the memory root yet, create it with a minimal
  `INDEX.md` (see `templates/project-INDEX.md`) on the first save.
