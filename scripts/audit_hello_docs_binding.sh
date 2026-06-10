#!/usr/bin/env bash
set -euo pipefail

source_repo="Bingboom/auto-manual"
mirror_repo="Bingboom/Hello-Docs"
source_branch="main"
mirror_branch="main"
report_only=0

usage() {
  cat <<'EOF'
Usage: scripts/audit_hello_docs_binding.sh [options]

Audits the one-way Hello-Docs mirror binding without reading secret values.

Options:
  --source-repo OWNER/REPO   Source repo, default Bingboom/auto-manual
  --mirror-repo OWNER/REPO   Mirror repo, default Bingboom/Hello-Docs
  --source-branch BRANCH     Source branch, default main
  --mirror-branch BRANCH     Mirror branch, default main
  --report-only              Print missing items but exit 0
  -h, --help                 Show this help
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --source-repo)
      source_repo="${2:?missing value for --source-repo}"
      shift 2
      ;;
    --mirror-repo)
      mirror_repo="${2:?missing value for --mirror-repo}"
      shift 2
      ;;
    --source-branch)
      source_branch="${2:?missing value for --source-branch}"
      shift 2
      ;;
    --mirror-branch)
      mirror_branch="${2:?missing value for --mirror-branch}"
      shift 2
      ;;
    --report-only)
      report_only=1
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

required_source_secrets=(
  HELLO_DOCS_SYNC_TOKEN
)

required_mirror_variables=(
  AUTO_MANUAL_GITHUB_REPO_OWNER
  AUTO_MANUAL_GITHUB_REPO_NAME
  FEISHU_BUILD_QUEUE_PAUSED
)

required_mirror_secrets=(
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

optional_mirror_secrets=(
  FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN
  VERCEL_TOKEN
  VERCEL_ORG_ID
  VERCEL_PROJECT_ID
  DINGTALK_DOCS_TARGET_NODE_URL
  DINGTALK_DOCS_A_TOKEN
  DINGTALK_DOCS_XSRF_TOKEN
  DINGTALK_DOCS_COOKIE
  DINGTALK_DOCS_BX_V
)

contains_line() {
  local needle="$1"
  grep -Fxq -- "$needle"
}

repo_ref_sha() {
  local repo="$1"
  local branch="$2"
  gh api "repos/${repo}/git/ref/heads/${branch}" --jq '.object.sha'
}

commit_tree_sha() {
  local repo="$1"
  local commit="$2"
  gh api "repos/${repo}/git/commits/${commit}" --jq '.tree.sha'
}

list_secrets() {
  local repo="$1"
  gh secret list --repo "$repo" | awk '{print $1}'
}

list_variables() {
  local repo="$1"
  gh variable list --repo "$repo" | awk -F '\t' '{print $1}'
}

variable_value() {
  local repo="$1"
  local name="$2"
  gh variable list --repo "$repo" | awk -F '\t' -v key="$name" '$1 == key {print $2; exit}'
}

expected_owner="${mirror_repo%%/*}"
expected_name="${mirror_repo#*/}"
failures=0

printf 'Auditing mirror binding\n'
printf '  source: %s@%s\n' "$source_repo" "$source_branch"
printf '  mirror: %s@%s\n\n' "$mirror_repo" "$mirror_branch"

source_sha="$(repo_ref_sha "$source_repo" "$source_branch")"
mirror_sha="$(repo_ref_sha "$mirror_repo" "$mirror_branch")"
source_tree="$(commit_tree_sha "$source_repo" "$source_sha")"
mirror_tree="$(commit_tree_sha "$mirror_repo" "$mirror_sha")"

printf 'Code tree\n'
printf '  source commit: %s\n' "$source_sha"
printf '  mirror commit: %s\n' "$mirror_sha"
if [ "$source_tree" = "$mirror_tree" ]; then
  printf '  [ok] tree matches: %s\n\n' "$source_tree"
else
  printf '  [missing] mirror tree %s does not match source tree %s\n\n' "$mirror_tree" "$source_tree"
  failures=$((failures + 1))
fi

source_secret_names="$(list_secrets "$source_repo")"
mirror_secret_names="$(list_secrets "$mirror_repo")"
mirror_variable_names="$(list_variables "$mirror_repo")"

printf 'Source sync secrets\n'
for name in "${required_source_secrets[@]}"; do
  if printf '%s\n' "$source_secret_names" | contains_line "$name"; then
    printf '  [ok] %s\n' "$name"
  else
    printf '  [missing] %s\n' "$name"
    failures=$((failures + 1))
  fi
done
printf '\n'

printf 'Mirror variables\n'
for name in "${required_mirror_variables[@]}"; do
  if printf '%s\n' "$mirror_variable_names" | contains_line "$name"; then
    value="$(variable_value "$mirror_repo" "$name")"
    case "$name" in
      AUTO_MANUAL_GITHUB_REPO_OWNER)
        if [ "$value" = "$expected_owner" ]; then
          printf '  [ok] %s=%s\n' "$name" "$value"
        else
          printf '  [missing] %s expected %s, got %s\n' "$name" "$expected_owner" "${value:-<empty>}"
          failures=$((failures + 1))
        fi
        ;;
      AUTO_MANUAL_GITHUB_REPO_NAME)
        if [ "$value" = "$expected_name" ]; then
          printf '  [ok] %s=%s\n' "$name" "$value"
        else
          printf '  [missing] %s expected %s, got %s\n' "$name" "$expected_name" "${value:-<empty>}"
          failures=$((failures + 1))
        fi
        ;;
      FEISHU_BUILD_QUEUE_PAUSED)
        printf '  [ok] %s=%s\n' "$name" "$value"
        ;;
    esac
  else
    printf '  [missing] %s\n' "$name"
    failures=$((failures + 1))
  fi
done
printf '\n'

printf 'Mirror required Feishu runtime secrets\n'
for name in "${required_mirror_secrets[@]}"; do
  if printf '%s\n' "$mirror_secret_names" | contains_line "$name"; then
    printf '  [ok] %s\n' "$name"
  else
    printf '  [missing] %s\n' "$name"
    failures=$((failures + 1))
  fi
done
printf '\n'

printf 'Mirror optional secrets\n'
for name in "${optional_mirror_secrets[@]}"; do
  if printf '%s\n' "$mirror_secret_names" | contains_line "$name"; then
    printf '  [ok] %s\n' "$name"
  else
    printf '  [optional-missing] %s\n' "$name"
  fi
done
printf '\n'

pause_value="$(variable_value "$mirror_repo" FEISHU_BUILD_QUEUE_PAUSED || true)"
if [ "$failures" -eq 0 ]; then
  if [ "$pause_value" = "true" ]; then
    printf 'Summary: mirror binding is complete and ready to unpause.\n'
  else
    printf 'Summary: mirror binding is complete and already unpaused.\n'
  fi
elif [ "$pause_value" = "true" ]; then
  printf 'Summary: mirror binding is incomplete, but Feishu runtime workflows are paused.\n'
else
  printf 'Summary: mirror binding is incomplete and Feishu runtime workflows are not paused.\n'
fi

printf 'OpenClaw note: repo-level audit can verify AUTO_MANUAL_GITHUB_REPO_OWNER/NAME only. Keep FEISHU_IM_APP_ID, FEISHU_IM_APP_SECRET, and any OpenClaw gateway tokens in the actual OpenClaw runtime environment.\n'

if [ "$failures" -gt 0 ] && [ "$report_only" -ne 1 ]; then
  exit 1
fi
