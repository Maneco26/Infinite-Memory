# -*- coding: utf-8 -*-
"""Infinite-Memory — copia los transcripts crudos (.jsonl) del proyecto actual
a  <memory_root>/<proyecto>/transcripts/.

Sin worker, sin dependencias. Dos modos de uso:

  1. Manual (desde la skill /recordar):
        python sync_transcripts.py "/ruta/al/proyecto"

  2. Automático (hook Stop de Claude Code): Claude Code entrega un JSON por
     stdin con el campo "cwd". El script lo lee y sincroniza el proyecto
     correcto, SIN depender de os.getcwd() del proceso-hook.

Detección del proyecto, por prioridad: argv[1] > stdin.cwd > getcwd().

Es copia de archivos: si el proceso muere o la PC se apaga, el crudo ya
quedó copiado turno a turno — nunca se pierde una sesión.
"""
import os
import sys
import re
import json
import shutil
import glob
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mem_config import get_memory_root  # noqa: E402


def resolve_project_dir() -> str:
    # 1) argumento explícito (uso manual)
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return os.path.abspath(sys.argv[1])
    # 2) stdin del hook Stop ({"cwd": "...", ...}). Solo si no hay argv[1],
    #    para no bloquear el uso manual.
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
            if raw and raw.strip():
                data = json.loads(raw)
                cwd = data.get("cwd") or data.get("project_dir")
                if cwd:
                    return os.path.abspath(cwd)
    except (json.JSONDecodeError, OSError, ValueError):
        pass
    # 3) último recurso
    return os.path.abspath(os.getcwd())


def encode_project_path(cwd: str) -> str:
    # Claude Code codifica la ruta del proyecto reemplazando todo carácter
    # no alfanumérico por '-' (igual en Windows / macOS / Linux).
    return re.sub(r"[^A-Za-z0-9]", "-", cwd)


def main() -> int:
    cwd = resolve_project_dir()
    project = os.path.basename(cwd.rstrip("/\\")) or "proyecto"

    encoded = encode_project_path(cwd)
    src_dir = Path.home() / ".claude" / "projects" / encoded

    memory_root = get_memory_root()
    dst_dir = memory_root / project / "transcripts"
    dst_dir.mkdir(parents=True, exist_ok=True)

    if not src_dir.is_dir():
        print(f"[infinite-memory] sin transcripts en: {src_dir}")
        print("  (el proyecto pudo abrirse desde otra ruta; revisar ~/.claude/projects)")
        return 0

    copied = 0
    for f in glob.glob(str(src_dir / "*.jsonl")):
        dst = dst_dir / os.path.basename(f)
        if (not dst.exists()) or dst.stat().st_size != os.path.getsize(f):
            shutil.copy2(f, dst)
            copied += 1

    print(f"[infinite-memory] proyecto: {project}")
    print(f"  origen:  {src_dir}")
    print(f"  destino: {dst_dir}")
    print(f"  copiados/actualizados: {copied}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
