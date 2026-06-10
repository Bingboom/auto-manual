#!/usr/bin/env bash
set -euo pipefail

preset="${1:-}"

case "${preset}" in
  feishu-build-queue|feishu-draft-build-queue)
    required=(
      FEISHU_APP_ID
      FEISHU_APP_SECRET
      FEISHU_PHASE2_BASE_TOKEN
      FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID
      FEISHU_PHASE2_SPEC_ROWS_SOURCE_VIEW_ID
      FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_TABLE_ID
      FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_VIEW_ID
      FEISHU_PHASE2_SPEC_FOOTNOTES_TABLE_ID
      FEISHU_PHASE2_SPEC_FOOTNOTES_VIEW_ID
      FEISHU_PHASE2_SPEC_NOTES_TABLE_ID
      FEISHU_PHASE2_SPEC_NOTES_VIEW_ID
      FEISHU_TRANSLATION_MEMORY_BASE_TOKEN
      FEISHU_TRANSLATION_MEMORY_TABLE_ID
      FEISHU_TRANSLATION_MEMORY_VIEW_ID
      FEISHU_PHASE2_SYMBOLS_BLOCKS_TABLE_ID
      FEISHU_PHASE2_SYMBOLS_BLOCKS_VIEW_ID
      FEISHU_PHASE2_LCD_ICONS_TABLE_ID
      FEISHU_PHASE2_LCD_ICONS_VIEW_ID
      FEISHU_PHASE2_TROUBLESHOOTING_TABLE_ID
      FEISHU_PHASE2_TROUBLESHOOTING_VIEW_ID
      FEISHU_PHASE2_VARIABLE_DEFAULTS_TABLE_ID
      FEISHU_PHASE2_VARIABLE_DEFAULTS_VIEW_ID
      FEISHU_PHASE2_VARIABLE_LANG_OVERRIDES_TABLE_ID
      FEISHU_PHASE2_VARIABLE_LANG_OVERRIDES_VIEW_ID
      FEISHU_PHASE2_MANUAL_COPY_SOURCE_TABLE_ID
      FEISHU_PHASE2_MANUAL_COPY_SOURCE_VIEW_ID
      FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID
      FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID
    )
    ;;
  feishu-start-review)
    required=(
      FEISHU_APP_ID
      FEISHU_APP_SECRET
      FEISHU_PHASE2_BASE_TOKEN
      FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID
      FEISHU_PHASE2_SPEC_ROWS_SOURCE_VIEW_ID
      FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_TABLE_ID
      FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_VIEW_ID
      FEISHU_PHASE2_SPEC_FOOTNOTES_TABLE_ID
      FEISHU_PHASE2_SPEC_FOOTNOTES_VIEW_ID
      FEISHU_PHASE2_SPEC_NOTES_TABLE_ID
      FEISHU_PHASE2_SPEC_NOTES_VIEW_ID
      FEISHU_TRANSLATION_MEMORY_BASE_TOKEN
      FEISHU_TRANSLATION_MEMORY_TABLE_ID
      FEISHU_TRANSLATION_MEMORY_VIEW_ID
      FEISHU_PHASE2_SYMBOLS_BLOCKS_TABLE_ID
      FEISHU_PHASE2_SYMBOLS_BLOCKS_VIEW_ID
      FEISHU_PHASE2_LCD_ICONS_TABLE_ID
      FEISHU_PHASE2_LCD_ICONS_VIEW_ID
      FEISHU_PHASE2_TROUBLESHOOTING_TABLE_ID
      FEISHU_PHASE2_TROUBLESHOOTING_VIEW_ID
      FEISHU_PHASE2_VARIABLE_DEFAULTS_TABLE_ID
      FEISHU_PHASE2_VARIABLE_DEFAULTS_VIEW_ID
      FEISHU_PHASE2_VARIABLE_LANG_OVERRIDES_TABLE_ID
      FEISHU_PHASE2_VARIABLE_LANG_OVERRIDES_VIEW_ID
      FEISHU_PHASE2_MANUAL_COPY_SOURCE_TABLE_ID
      FEISHU_PHASE2_MANUAL_COPY_SOURCE_VIEW_ID
      FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID
      FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID
    )
    ;;
  *)
    printf 'Usage: %s <feishu-build-queue|feishu-draft-build-queue|feishu-start-review>\n' "$0" >&2
    exit 2
    ;;
esac

missing=()
for name in "${required[@]}"; do
  if [ -z "${!name:-}" ]; then
    missing+=("$name")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  printf 'Missing required secrets/env vars:\n' >&2
  printf ' - %s\n' "${missing[@]}" >&2
  exit 1
fi

provider="$(printf '%s' "${AUTO_MANUAL_ARTIFACT_SINK_PROVIDER:-}" | tr '[:upper:]' '[:lower:]')"
mirror_provider="$(printf '%s' "${AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER:-}" | tr '[:upper:]' '[:lower:]')"
case "${provider}:${mirror_provider}" in
  dingtalk:*|dingtalk_alidocs_session:*|dingtalk-alidocs-session:*|alidocs:*|alidocs_session:*|*:dingtalk|*:dingtalk_alidocs_session|*:dingtalk-alidocs-session|*:alidocs|*:alidocs_session)
    dingtalk_required=(
      DINGTALK_DOCS_A_TOKEN
      DINGTALK_DOCS_XSRF_TOKEN
      DINGTALK_DOCS_COOKIE
    )
    dingtalk_missing=()
    for name in "${dingtalk_required[@]}"; do
      if [ -z "${!name:-}" ]; then
        dingtalk_missing+=("$name")
      fi
    done
    if [ "${#dingtalk_missing[@]}" -gt 0 ]; then
      printf 'Missing required DingTalk secrets/env vars for remote artifact upload:\n' >&2
      printf ' - %s\n' "${dingtalk_missing[@]}" >&2
      exit 1
    fi
    ;;
esac
