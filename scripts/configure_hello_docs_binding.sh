#!/usr/bin/env bash
set -euo pipefail

mirror_repo="Bingboom/Hello-Docs"
pause_value="true"
unpause=0
dry_run=0
include_optional=0

usage() {
  cat <<'EOF'
Usage: scripts/configure_hello_docs_binding.sh [options]

Writes the Hello-Docs mirror binding from current environment variables into
GitHub repository Secrets / Variables. Secret values are never printed.

Options:
  --mirror-repo OWNER/REPO    Mirror repo, default Bingboom/Hello-Docs
  --pause                     Set FEISHU_BUILD_QUEUE_PAUSED=true, default
  --unpause                   Set FEISHU_BUILD_QUEUE_PAUSED=false after audit passes
  --include-optional          Also write optional Vercel / DingTalk / Feishu IM / OpenClaw values when present
  --dry-run                   Show what would be written without changing GitHub
  -h, --help                  Show this help

Required environment variables are the same Feishu runtime secrets reported by
scripts/audit_hello_docs_binding.sh. Missing required values stop the script.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --mirror-repo)
      mirror_repo="${2:?missing value for --mirror-repo}"
      shift 2
      ;;
    --pause)
      pause_value="true"
      unpause=0
      shift
      ;;
    --unpause)
      pause_value="false"
      unpause=1
      shift
      ;;
    --include-optional)
      include_optional=1
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  printf 'gh is required. Install GitHub CLI and authenticate first.\n' >&2
  exit 2
fi

required_secret_names=(
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

optional_secret_names=(
  FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN
  VERCEL_TOKEN
  VERCEL_ORG_ID
  VERCEL_PROJECT_ID
  DINGTALK_DOCS_TARGET_NODE_URL
  DINGTALK_DOCS_A_TOKEN
  DINGTALK_DOCS_XSRF_TOKEN
  DINGTALK_DOCS_COOKIE
  DINGTALK_DOCS_BX_V
  FEISHU_IM_APP_ID
  FEISHU_IM_APP_SECRET
  FEISHU_IM_VERIFICATION_TOKEN
  FEISHU_IM_ENCRYPT_KEY
  FEISHU_VERIFICATION_TOKEN
  FEISHU_ENCRYPT_KEY
  CLOUDFLARED_TUNNEL_TOKEN
)

optional_variable_names=(
  AUTO_MANUAL_GITHUB_DEFAULT_BRANCH
  AUTO_MANUAL_GITHUB_API_BASE_URL
  AUTO_MANUAL_GITHUB_METADATA_ARTIFACT_NAME
  AUTO_MANUAL_GITHUB_DISPATCH_TIMEOUT_SECONDS
  AUTO_MANUAL_CONTROL_CONFIG
  FEISHU_IM_WEBHOOK_HOST
  FEISHU_IM_WEBHOOK_PORT
  FEISHU_IM_WEBHOOK_PATH
  FEISHU_IM_HEALTH_PATH
  FEISHU_IM_REQUIRE_MENTION
  FEISHU_IM_ENABLE_MESSAGE_REACTIONS
  FEISHU_IM_BATCH_DISPATCH_DELAY_MS
  FEISHU_IM_BATCH_STATUS_TIMEOUT_SECONDS
  FEISHU_IM_BATCH_STATUS_POLL_SECONDS
  FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS
  FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_WRITE
  FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_PR_CREATE
)

missing=()
for name in "${required_secret_names[@]}"; do
  if [ -z "${!name:-}" ]; then
    missing+=("$name")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  printf 'Missing required environment variables; no GitHub changes were made:\n' >&2
  printf ' - %s\n' "${missing[@]}" >&2
  exit 1
fi

mirror_owner="${mirror_repo%%/*}"
mirror_name="${mirror_repo#*/}"

set_variable() {
  local name="$1"
  local value="$2"
  if [ "$dry_run" -eq 1 ]; then
    printf '[dry-run] set variable %s=%s in %s\n' "$name" "$value" "$mirror_repo"
  else
    gh variable set "$name" --repo "$mirror_repo" --body "$value" >/dev/null
    printf '[ok] set variable %s in %s\n' "$name" "$mirror_repo"
  fi
}

set_secret_from_env() {
  local name="$1"
  if [ "$dry_run" -eq 1 ]; then
    printf '[dry-run] set secret %s in %s from environment\n' "$name" "$mirror_repo"
  else
    printf '%s' "${!name}" | gh secret set "$name" --repo "$mirror_repo" >/dev/null
    printf '[ok] set secret %s in %s\n' "$name" "$mirror_repo"
  fi
}

set_variable_from_env() {
  local name="$1"
  if [ -n "${!name:-}" ]; then
    set_variable "$name" "${!name}"
  else
    printf '[skip] optional variable %s is not present in environment\n' "$name"
  fi
}

set_variable AUTO_MANUAL_GITHUB_REPO_OWNER "$mirror_owner"
set_variable AUTO_MANUAL_GITHUB_REPO_NAME "$mirror_name"
set_variable FEISHU_BUILD_QUEUE_PAUSED true

for name in "${required_secret_names[@]}"; do
  set_secret_from_env "$name"
done

if [ "$include_optional" -eq 1 ]; then
  for name in "${optional_secret_names[@]}"; do
    if [ -n "${!name:-}" ]; then
      set_secret_from_env "$name"
    else
      printf '[skip] optional secret %s is not present in environment\n' "$name"
    fi
  done
  for name in "${optional_variable_names[@]}"; do
    set_variable_from_env "$name"
  done
fi

if [ "$dry_run" -eq 1 ]; then
  if [ "$unpause" -eq 1 ]; then
    printf '[dry-run] run audit, then set variable FEISHU_BUILD_QUEUE_PAUSED=false in %s\n' "$mirror_repo"
  fi
  printf 'Dry run complete; no GitHub changes were made.\n'
  exit 0
fi

if [ "$unpause" -eq 1 ]; then
  scripts/audit_hello_docs_binding.sh --mirror-repo "$mirror_repo"
  set_variable FEISHU_BUILD_QUEUE_PAUSED "$pause_value"
else
  scripts/audit_hello_docs_binding.sh --mirror-repo "$mirror_repo" --report-only
fi
