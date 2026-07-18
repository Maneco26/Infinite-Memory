# -*- coding: utf-8 -*-
"""Infinite-Memory installer (cross-platform).

Does three things, idempotently:
  1. Copies the skill to ~/.claude/skills/infinite-memory/
  2. Copies scripts/ and templates/ to ~/.claude/infinite-memory/
  3. Registers a global async `Stop` hook in ~/.claude/settings.json that runs
     sync_transcripts.py after every turn (merges — never clobbers existing hooks).

Run:  python install/install.py
Then, inside Claude Code:  /infinite-memory   (first run asks where to store memory)

Uninstall:  python install/install.py --uninstall
"""
import sys
import json
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOME = Path.home()
CLAUDE = HOME / ".claude"
SKILL_DST = CLAUDE / "skills" / "infinite-memory"
DATA_DST = CLAUDE / "infinite-memory"
SETTINGS = CLAUDE / "settings.json"
HOOK_TAG = "infinite-memory/scripts/sync_transcripts.py"


def python_exe() -> str:
    # Prefer the interpreter running this installer (absolute, reliable).
    return sys.executable or "python3"


def copy_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.is_dir():
            copy_tree(item, dst / item.name)
        else:
            shutil.copy2(item, dst / item.name)


def load_settings() -> dict:
    if SETTINGS.exists():
        try:
            return json.loads(SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"WARNING: {SETTINGS} is not valid JSON — leaving hooks untouched.")
            return None  # type: ignore
    return {}


def hook_command() -> dict:
    sync_path = str((DATA_DST / "scripts" / "sync_transcripts.py"))
    return {
        "type": "command",
        "command": python_exe(),
        "args": [sync_path],
        "timeout": 30,
        "async": True,
        "statusMessage": "Infinite-Memory: syncing...",
    }


def has_our_hook(stop_hooks: list) -> bool:
    for group in stop_hooks:
        for h in group.get("hooks", []):
            for a in (h.get("args") or []):
                if HOOK_TAG in str(a).replace("\\", "/"):
                    return True
    return False


def install() -> None:
    print("Infinite-Memory — installing...")
    # 1) skill
    if SKILL_DST.exists():
        shutil.rmtree(SKILL_DST)
    SKILL_DST.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO / "SKILL.md", SKILL_DST / "SKILL.md")
    print(f"  skill  -> {SKILL_DST}")

    # 2) scripts + templates
    copy_tree(REPO / "scripts", DATA_DST / "scripts")
    copy_tree(REPO / "templates", DATA_DST / "templates")
    print(f"  data   -> {DATA_DST}")

    # 3) Stop hook (merge)
    settings = load_settings()
    if settings is None:
        print("  hook   -> SKIPPED (settings.json invalid). Add it manually — see README.")
    else:
        hooks = settings.setdefault("hooks", {})
        stop = hooks.setdefault("Stop", [])
        if not isinstance(stop, list):
            stop = []
            hooks["Stop"] = stop
        if has_our_hook(stop):
            print("  hook   -> already registered")
        else:
            # add to the first matcher-"" group, or create one
            group = next((g for g in stop if g.get("matcher", "") == ""), None)
            if group is None:
                group = {"matcher": "", "hooks": []}
                stop.append(group)
            group.setdefault("hooks", []).append(hook_command())
            SETTINGS.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS.write_text(json.dumps(settings, indent=2), encoding="utf-8")
            print(f"  hook   -> registered async Stop hook in {SETTINGS}")

    print("\nDone. In Claude Code, run  /infinite-memory  to pick where your memory lives.")


def uninstall() -> None:
    print("Infinite-Memory — uninstalling (memory data is NOT deleted)...")
    for p in (SKILL_DST, DATA_DST):
        if p.exists():
            shutil.rmtree(p)
            print(f"  removed {p}")
    settings = load_settings()
    if settings:
        stop = settings.get("hooks", {}).get("Stop", [])
        for group in stop:
            group["hooks"] = [
                h for h in group.get("hooks", [])
                if not any(HOOK_TAG in str(a).replace("\\", "/") for a in (h.get("args") or []))
            ]
        SETTINGS.write_text(json.dumps(settings, indent=2), encoding="utf-8")
        print("  removed Stop hook")
    print("Done. Your memory files under memory_root are untouched.")


if __name__ == "__main__":
    if "--uninstall" in sys.argv:
        uninstall()
    else:
        install()
