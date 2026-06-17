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

optional_mirror_openclaw_secrets=(
  FEISHU_IM_APP_ID
  FEISHU_IM_APP_SECRET
  FEISHU_IM_VERIFICATION_TOKEN
  FEISHU_IM_ENCRYPT_KEY
  FEISHU_VERIFICATION_TOKEN
  FEISHU_ENCRYPT_KEY
  FEISHU_MANUAL_INDEX_BASE_TOKEN
  CLOUDFLARED_TUNNEL_TOKEN
)

optional_mirror_openclaw_variables=(
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
  FEISHU_IM_MANUAL_INDEX_LIMIT
  FEISHU_MANUAL_INDEX_TABLE_ID
  FEISHU_MANUAL_INDEX_VIEW_ID
  FEISHU_MANUAL_INDEX_IDENTITY
  FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOWED_SENDERS
  FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_WRITE
  FEISHU_IM_CLOUD_DOC_BACKPORT_ALLOW_PR_CREATE
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

secret_present() {
  local name="$1"
  printf '%s\n' "$mirror_secret_names" | contains_line "$name"
}

variable_present() {
  local name="$1"
  printf '%s\n' "$mirror_variable_names" | contains_line "$name"
}

mirror_can_create_prs() {
  local repo="$1"
  gh api "repos/${repo}/actions/permissions/workflow" --jq '.can_approve_pull_request_reviews' 2>/dev/null
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

printf 'Mirror Actions PR-creation permission\n'
pr_toggle="$(mirror_can_create_prs "$mirror_repo" || true)"
if [ "$pr_toggle" = "true" ]; then
  printf '  [ok] Actions may create pull requests (can_approve_pull_request_reviews=true)\n'
else
  printf '  [missing] Actions cannot create pull requests (can_approve_pull_request_reviews=%s); Start Review PR creation will 403\n' "${pr_toggle:-unknown}"
  printf '           Fix: gh api -X PUT /repos/%s/actions/permissions/workflow -f default_workflow_permissions=read -F can_approve_pull_request_reviews=true\n' "$mirror_repo"
  failures=$((failures + 1))
fi
printf '\n'

printf 'Mirror optional secrets\n'
for name in "${optional_mirror_secrets[@]}"; do
  if secret_present "$name"; then
    printf '  [ok] %s\n' "$name"
  else
    printf '  [optional-missing] %s\n' "$name"
  fi
done
printf '\n'

printf 'Mirror optional Feishu IM / OpenClaw secrets\n'
for name in "${optional_mirror_openclaw_secrets[@]}"; do
  if secret_present "$name"; then
    printf '  [ok] %s\n' "$name"
  else
    printf '  [optional-missing] %s\n' "$name"
  fi
done
if secret_present FEISHU_IM_APP_ID && secret_present FEISHU_IM_APP_SECRET; then
  printf '  [ok] Feishu IM adapter has explicit FEISHU_IM_APP_ID / FEISHU_IM_APP_SECRET\n'
elif secret_present FEISHU_APP_ID && secret_present FEISHU_APP_SECRET; then
  printf '  [ok] Feishu IM adapter can fall back to required FEISHU_APP_ID / FEISHU_APP_SECRET\n'
else
  printf '  [optional-missing] Feishu IM adapter app credentials are not yet available through FEISHU_IM_* or FEISHU_APP_*\n'
fi
printf '\n'

printf 'Mirror optional Feishu IM / OpenClaw variables\n'
for name in "${optional_mirror_openclaw_variables[@]}"; do
  if variable_present "$name"; then
    printf '  [ok] %s=%s\n' "$name" "$(variable_value "$mirror_repo" "$name")"
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

printf 'OpenClaw note: repo-level audit verifies the mirror repo variables plus optional Feishu IM adapter entries. The OpenClaw plugin host still needs its GitHub token in the OpenClaw plugin config or runtime environment; repository secrets are only available to GitHub Actions unless the runtime explicitly exports them.\n'

if [ "$failures" -gt 0 ] && [ "$report_only" -ne 1 ]; then
  exit 1
fi
