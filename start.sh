#!/usr/bin/env bash
set -e

# Change directory to the repository root where this script resides
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Detect Python executable (prefer virtual environment if present)
if [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif [ -f "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "[Error] Python 3 was not found in your PATH or virtual environment." >&2
    echo "Please install Python 3 or add it to PATH." >&2
    exit 1
fi

exec "$PYTHON_BIN" run.py "$@"
