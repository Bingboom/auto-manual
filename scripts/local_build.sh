#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
cd "$repo_root"

if [ -n "${PYTHON:-}" ]; then
  python_cmd="$PYTHON"
elif command -v python3 >/dev/null 2>&1; then
  python_cmd="python3"
elif command -v python >/dev/null 2>&1; then
  python_cmd="python"
else
  echo "[local-build] Python 3 is required to run scripts/local_build.sh." >&2
  exit 1
fi

exec "$python_cmd" "$repo_root/scripts/local_build.py" "$@"
