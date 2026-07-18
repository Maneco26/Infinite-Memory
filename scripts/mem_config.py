# -*- coding: utf-8 -*-
"""Infinite-Memory — resolución de configuración (portable, sin dependencias).

El único dato configurable es `memory_root`: la carpeta raíz donde vive la
memoria de TODOS los proyectos. Se guarda en:

    ~/.claude/infinite-memory/config.json   ->  {"memory_root": "<ruta absoluta>"}

Orden de resolución de memory_root:
  1. Variable de entorno INFINITE_MEMORY_ROOT (útil para CI / overrides).
  2. config.json (lo que el usuario eligió al activar la skill).
  3. Default: ~/infinite-memory

Cross-platform: usa pathlib, funciona en Windows / macOS / Linux.
"""
import os
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".claude" / "infinite-memory"
CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_ROOT = Path.home() / "infinite-memory"


def _read_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def get_memory_root() -> Path:
    env = os.environ.get("INFINITE_MEMORY_ROOT")
    if env and env.strip():
        return Path(env).expanduser().resolve()
    cfg = _read_config()
    root = cfg.get("memory_root")
    if root and str(root).strip():
        return Path(root).expanduser().resolve()
    return DEFAULT_ROOT.resolve()


def set_memory_root(path: str) -> Path:
    root = Path(path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "_global").mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg = _read_config()
    cfg["memory_root"] = str(root)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return root


def is_configured() -> bool:
    return bool(_read_config().get("memory_root"))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "set" and len(sys.argv) > 2:
        r = set_memory_root(sys.argv[2])
        print(f"memory_root = {r}")
    else:
        print(f"memory_root = {get_memory_root()}")
        print(f"configured  = {is_configured()}")
        print(f"config file = {CONFIG_PATH}")
