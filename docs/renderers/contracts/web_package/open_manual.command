#!/bin/sh
set -eu
manual_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$manual_dir/open_manual.py"
