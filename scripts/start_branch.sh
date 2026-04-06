#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
cd "$repo_root"

if [ "$#" -lt 1 ]; then
  echo "[start-branch] Usage: ./scripts/start_branch.sh codex/<topic> [--allow-dirty]" >&2
  exit 1
fi

branch_name=$1
shift

if [ -n "${PYTHON:-}" ]; then
  python_cmd="$PYTHON"
elif [ -x "$repo_root/.venv/bin/python" ]; then
  python_cmd="$repo_root/.venv/bin/python"
elif [ -x "$repo_root/.venv/Scripts/python.exe" ]; then
  python_cmd="$repo_root/.venv/Scripts/python.exe"
elif command -v python3 >/dev/null 2>&1; then
  python_cmd="python3"
elif command -v python >/dev/null 2>&1; then
  python_cmd="python"
else
  echo "[start-branch] Python 3 is required to run scripts/start_branch.sh." >&2
  exit 1
fi

exec "$python_cmd" "$repo_root/scripts/git_branch_guard.py" \
  start-branch \
  --repo-root "$repo_root" \
  --branch "$branch_name" \
  "$@"
