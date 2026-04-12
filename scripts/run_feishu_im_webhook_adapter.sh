#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
adapter_dir="$repo_root/integrations/openclaw/feishu-im-webhook-adapter"
env_file="${FEISHU_IM_ENV_FILE:-$repo_root/.tmp/feishu-im-webhook-adapter/env.sh}"

if [ -f "$env_file" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$env_file"
  set +a
fi

export AUTO_MANUAL_REPO_ROOT="${AUTO_MANUAL_REPO_ROOT:-$repo_root}"
export AUTO_MANUAL_CONTROL_CONFIG="${AUTO_MANUAL_CONTROL_CONFIG:-config.us.yaml}"
export FEISHU_IM_STATE_FILE="${FEISHU_IM_STATE_FILE:-$repo_root/.tmp/feishu-im-webhook-adapter/state.json}"

mkdir -p "$(dirname -- "$FEISHU_IM_STATE_FILE")"

cd "$adapter_dir"
exec npm start
