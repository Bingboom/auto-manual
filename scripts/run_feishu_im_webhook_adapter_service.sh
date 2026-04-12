#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${FEISHU_IM_ENV_FILE:-${ROOT_DIR}/.tmp/feishu-im-webhook-adapter/env.sh}"
RUNTIME_DIR="${ROOT_DIR}/.tmp/feishu-im-webhook-adapter"
ADAPTER_DIR="${ROOT_DIR}/integrations/openclaw/feishu-im-webhook-adapter"

mkdir -p "${RUNTIME_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[feishu-im-webhook-adapter] missing env file: ${ENV_FILE}" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

if [[ -z "${AUTO_MANUAL_REPO_ROOT:-}" ]]; then
  export AUTO_MANUAL_REPO_ROOT="${ROOT_DIR}"
fi

if [[ -z "${AUTO_MANUAL_PYTHON:-}" && -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  export AUTO_MANUAL_PYTHON="${ROOT_DIR}/.venv/bin/python"
fi

if [[ -z "${NVM_DIR:-}" && -d "${HOME}/.nvm" ]]; then
  export NVM_DIR="${HOME}/.nvm"
fi
if [[ -n "${NVM_DIR:-}" && -s "${NVM_DIR}/nvm.sh" ]]; then
  # shellcheck disable=SC1090
  source "${NVM_DIR}/nvm.sh"
fi

if ! command -v node >/dev/null 2>&1; then
  echo "[feishu-im-webhook-adapter] node is not available on PATH after loading ${ENV_FILE}" >&2
  exit 1
fi

cd "${ADAPTER_DIR}"
exec node server.mjs
