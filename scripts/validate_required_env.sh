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
      FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN
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
