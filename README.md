# Infinite-Memory

**Persistent, file-based memory for [Claude Code](https://claude.com/claude-code).**
No worker, no database, no cloud service — just Markdown files and raw transcript
copies on your own disk. Your projects stay *remembered* across sessions, and a
session is never lost to a crash or power-off.

> Activate it once in a project with `/infinite-memory`. From then on, start any
> new session, and Claude picks up exactly where you left off — decisions,
> pending items, IDs, the whole context — without you re-explaining anything.

---

## Why

Claude Code forgets everything between sessions. The usual fixes need a running
worker or a hosted service that breaks, costs money, or leaks your data. This is
the opposite: **plain files you own**, on a path you choose.

- **Curated summary** (`INDEX.md`, `sessions/`) — what was done, decided, pending.
  Written by the model with judgment, so a fresh session reads it and is instantly
  up to date.
- **Raw black box** (`transcripts/*.jsonl`) — the full conversation, copied
  **every turn** by a background hook. If the PC dies mid-task, nothing is lost;
  the next session reconstructs from it.

Works on Windows, macOS, and Linux. One safe async hook, zero background processes.

## Install

```bash
git clone https://github.com/<you>/Infinite-Memory.git
cd Infinite-Memory

# macOS / Linux
bash install/install.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File install\install.ps1
```

The installer:
1. Copies the skill to `~/.claude/skills/infinite-memory/`.
2. Copies its scripts to `~/.claude/infinite-memory/`.
3. Registers a global async `Stop` hook in `~/.claude/settings.json` (merged —
   it never clobbers hooks you already have).

Then, inside Claude Code, run:

```
/infinite-memory
```

The **first time**, it asks where to store your memory (a home folder, a synced
folder like Dropbox/OneDrive/iCloud so it follows you across machines, or a custom
path). That choice is saved in `~/.claude/infinite-memory/config.json`.

## How it works

```
<memory_root>/
  _global/
    PROFILE.md        # who you are, fixed preferences (read every session)
    INDEX.md          # map of all your projects
  <project>/          # = the basename of the project's working directory
    INDEX.md          # "Latest state" + decisions + focus (read on startup)
    sessions/
      YYYY-MM-DD.md   # per-day log: Asked / Done / Decided / Pending
    transcripts/      # raw .jsonl copies (auto, every turn)
```

- **On session start** (`/infinite-memory`): reads `PROFILE.md`, the project's
  `INDEX.md`, and the latest session notes — and opens the raw transcript if
  something doesn't add up.
- **On closing a block of work**: updates the project `INDEX.md` and appends a
  dated session note. Automatically, without being asked.
- **Every turn**: the `Stop` hook copies the raw transcript to your memory root.

## Commands

| Command | What it does |
|---|---|
| `/infinite-memory` | Activate persistent-memory mode for the session (first run: pick where memory lives). |
| `/recordar` | Force-save the current session now (INDEX + dated notes + transcript copy). |
| `/recall <topic>` | Search your memory (and raw transcripts) for a topic. |

*(`/recordar` and `/recall` are aliases the skill recognizes; plain English like
"save this to memory" or "what do you know about this project" works too.)*

## Configuration

`memory_root` is resolved in this order:

1. Env var `INFINITE_MEMORY_ROOT`
2. `~/.claude/infinite-memory/config.json`
3. Default `~/infinite-memory`

Change it any time:

```bash
python ~/.claude/infinite-memory/scripts/mem_config.py set "/path/you/want"
```

## Notes & limits

- **To sync across machines**, put `memory_root` in a cloud-synced folder.
- **Cloud/web Claude Code** (running on a remote sandbox) can't see your local
  disk, so file-based memory isn't available there — use the **desktop app** or
  **CLI** on your own machine.
- The **raw transcript** is 100% automatic (the hook). The **curated summary** is
  written by the model when closing work — a script can copy files but can't
  summarize with judgment, so that part is Claude's job (done automatically in
  active mode).
- Uninstall: `python install/install.py --uninstall` (removes the skill + hook;
  your memory files are left untouched).

## License

MIT — see [LICENSE](LICENSE).
