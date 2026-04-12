#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${FEISHU_IM_ENV_FILE:-${ROOT_DIR}/.tmp/feishu-im-webhook-adapter/env.sh}"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "[feishu-im-cloudflared] cloudflared is not available on PATH" >&2
  exit 1
fi

if [[ -n "${CLOUDFLARED_TUNNEL_TOKEN:-}" ]]; then
  exec cloudflared tunnel run --token "${CLOUDFLARED_TUNNEL_TOKEN}"
fi

if [[ -n "${CLOUDFLARED_TUNNEL_CONFIG:-}" ]]; then
  exec cloudflared tunnel --config "${CLOUDFLARED_TUNNEL_CONFIG}" run
fi

echo "[feishu-im-cloudflared] set CLOUDFLARED_TUNNEL_TOKEN or CLOUDFLARED_TUNNEL_CONFIG in ${ENV_FILE}" >&2
exit 1
