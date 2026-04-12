#!/usr/bin/env bash
set -euo pipefail

preset="${1:-}"

case "${preset}" in
  feishu-build-queue|feishu-draft-build-queue)
    required=(
      FEISHU_APP_ID
      FEISHU_APP_SECRET
      FEISHU_PHASE2_BASE_TOKEN
      FEISHU_PHASE2_SPEC_MASTER_TABLE_ID
      FEISHU_PHASE2_SPEC_MASTER_VIEW_ID
      FEISHU_PHASE2_SPEC_FOOTNOTES_TABLE_ID
      FEISHU_PHASE2_SPEC_FOOTNOTES_VIEW_ID
      FEISHU_PHASE2_SPEC_NOTES_TABLE_ID
      FEISHU_PHASE2_SPEC_NOTES_VIEW_ID
      FEISHU_PHASE2_SPEC_TITLES_TABLE_ID
      FEISHU_PHASE2_SPEC_TITLES_VIEW_ID
      FEISHU_PHASE2_SYMBOLS_BLOCKS_TABLE_ID
      FEISHU_PHASE2_SYMBOLS_BLOCKS_VIEW_ID
      FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID
      FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID
    )
    ;;
  feishu-start-review)
    required=(
      FEISHU_APP_ID
      FEISHU_APP_SECRET
      FEISHU_PHASE2_BASE_TOKEN
      FEISHU_PHASE2_SPEC_MASTER_TABLE_ID
      FEISHU_PHASE2_SPEC_MASTER_VIEW_ID
      FEISHU_PHASE2_SPEC_FOOTNOTES_TABLE_ID
      FEISHU_PHASE2_SPEC_FOOTNOTES_VIEW_ID
      FEISHU_PHASE2_SPEC_NOTES_TABLE_ID
      FEISHU_PHASE2_SPEC_NOTES_VIEW_ID
      FEISHU_PHASE2_SPEC_TITLES_TABLE_ID
      FEISHU_PHASE2_SPEC_TITLES_VIEW_ID
      FEISHU_PHASE2_SYMBOLS_BLOCKS_TABLE_ID
      FEISHU_PHASE2_SYMBOLS_BLOCKS_VIEW_ID
      FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID
      FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID
    )
    ;;
  *)
    printf 'Usage: %s <feishu-build-queue|feishu-draft-build-queue|feishu-start-review>\n' "$0" >&2
    exit 2
    ;;
esac

normalize_provider() {
  case "$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')" in
    dingtalk_openapi|dingtalk-openapi|openapi)
      printf 'dingtalk_openapi'
      ;;
    dingtalk_alidocs_session|dingtalk-alidocs-session|alidocs|alidocs_session|dingtalk)
      printf 'dingtalk_alidocs_session'
      ;;
    *)
      printf '%s' "${1:-}"
      ;;
  esac
}

missing=()
for name in "${required[@]}"; do
  if [ -z "${!name:-}" ]; then
    missing+=("$name")
  fi
done

provider="$(normalize_provider "${AUTO_MANUAL_ARTIFACT_SINK_PROVIDER:-}")"
if [ "${provider}" = "dingtalk_openapi" ]; then
  openapi_required=(
    DINGTALK_CLIENT_ID
    DINGTALK_CLIENT_SECRET
    DINGTALK_CORP_ID
    FEISHU_PHASE2_DINGTALK_CONTROL_TABLE_ID
    FEISHU_PHASE2_DINGTALK_CONTROL_VIEW_ID
  )
  for name in "${openapi_required[@]}"; do
    if [ -z "${!name:-}" ]; then
      missing+=("$name")
    fi
  done
fi

if [ "${#missing[@]}" -gt 0 ]; then
  printf 'Missing required secrets/env vars:\n' >&2
  printf ' - %s\n' "${missing[@]}" >&2
  exit 1
fi
