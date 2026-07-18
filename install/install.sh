#!/usr/bin/env bash
# Infinite-Memory installer (macOS / Linux). Wrapper around install.py.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "Python 3 is required but was not found in PATH." >&2
  exit 1
fi
exec "$PY" "$DIR/install.py" "$@"
