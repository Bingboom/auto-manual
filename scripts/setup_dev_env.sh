#!/usr/bin/env bash
# Create a local virtualenv that matches CI: the pinned Python from pyproject.toml
# ([tool.mypy] python_version) plus the exact pins in requirements.lock, then prove
# it with `tools/env_preflight.py --strict`.
#
# Usage: scripts/setup_dev_env.sh [--venv DIR] [--python BIN] [--recreate]
#   --venv DIR     virtualenv location (default: .venv at the repo root)
#   --python BIN   interpreter to build the venv from (default: search for the pinned version)
#   --recreate     delete an existing venv first (needed when it was built on another Python)
# Exit codes: 0 ready; 1 installed but preflight still reports drift; 2 usage or setup error.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT/.venv"
PYTHON_BIN=""
RECREATE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --venv) VENV_DIR="${2:?--venv needs a directory}"; shift 2 ;;
    --python) PYTHON_BIN="${2:?--python needs an interpreter}"; shift 2 ;;
    --recreate) RECREATE=1; shift ;;
    -h|--help) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "[setup-dev-env] unknown argument: $1" >&2; exit 2 ;;
  esac
done

PINNED="$(sed -n 's/^python_version *= *"\([0-9]*\.[0-9]*\)".*/\1/p' "$ROOT/pyproject.toml" | head -n 1)"
if [[ -z "$PINNED" ]]; then
  echo "[setup-dev-env] no [tool.mypy] python_version pin found in pyproject.toml" >&2
  exit 2
fi

version_of() {
  "$1" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")' 2>/dev/null || true
}

if [[ -z "$PYTHON_BIN" ]]; then
  for candidate in "python$PINNED" python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && [[ "$(version_of "$candidate")" == "$PINNED" ]]; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi
if [[ -z "$PYTHON_BIN" ]]; then
  echo "[setup-dev-env] Python $PINNED not found; install it or pass --python /path/to/python$PINNED" >&2
  exit 2
fi
FOUND="$(version_of "$PYTHON_BIN")"
if [[ "$FOUND" != "$PINNED" ]]; then
  echo "[setup-dev-env] $PYTHON_BIN is Python ${FOUND:-unknown}, but the repo pins $PINNED" >&2
  exit 2
fi

VENV_PY="$VENV_DIR/bin/python"
if [[ -d "$VENV_DIR" && "$RECREATE" -eq 1 ]]; then
  echo "[setup-dev-env] removing $VENV_DIR"
  rm -rf "$VENV_DIR"
fi
if [[ -x "$VENV_PY" ]]; then
  EXISTING="$(version_of "$VENV_PY")"
  if [[ "$EXISTING" != "$PINNED" ]]; then
    echo "[setup-dev-env] $VENV_DIR was built with Python ${EXISTING:-unknown}; rerun with --recreate" >&2
    exit 2
  fi
  echo "[setup-dev-env] reusing $VENV_DIR (Python $EXISTING)"
else
  echo "[setup-dev-env] creating $VENV_DIR with $PYTHON_BIN (Python $FOUND)"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo "[setup-dev-env] installing requirements.lock"
"$VENV_PY" -m pip install --quiet --upgrade pip
"$VENV_PY" -m pip install --quiet -r "$ROOT/requirements.lock"

echo "[setup-dev-env] checking the environment against CI"
if (cd "$ROOT" && "$VENV_PY" tools/env_preflight.py --strict); then
  echo "[setup-dev-env] ready: source ${VENV_DIR#"$ROOT/"}/bin/activate"
else
  echo "[setup-dev-env] installed, but the environment still differs from CI (see WARN rows above)" >&2
  exit 1
fi
