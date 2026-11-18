#!/usr/bin/env bash
# Fail fast on malformed workflow_dispatch identifiers before any queue worker
# runs. Values arrive through the step's `env:` (never `${{ }}` in the script)
# and are only read here, never evaluated.
#
# Usage: validate_dispatch_inputs.sh <kind> <ENV_VAR_NAME> [<kind> <ENV_VAR_NAME> ...]
#   record-id   one Feishu Bitable queue record id, or empty
#   record-ids  comma-separated record ids (whitespace around items and empty
#               items are ignored, as the Python CLI does), or empty
#
# The record-id pattern mirrors _QUEUE_RECORD_ID_RE in
# tools/publish_locale_identity.py; tests/test_workflow_expression_injection.py
# keeps the two in step.
set -euo pipefail
export LC_ALL=C

RECORD_ID_RE='^rec[A-Za-z0-9_-]+$'
status=0

fail() {
  echo "::error::$1"
  status=1
}

check_record_id() {
  local name="$1" value="$2"
  if [ -n "${value}" ] && ! [[ "${value}" =~ ${RECORD_ID_RE} ]]; then
    fail "workflow input ${name,,} must be a queue record id matching ${RECORD_ID_RE}"
  fi
}

check_record_ids() {
  local name="$1" value="$2" item
  local -a items=()
  [ -n "${value}" ] || return 0
  IFS=',' read -r -d '' -a items < <(printf '%s\0' "${value}") || true
  for item in "${items[@]}"; do
    item="${item#"${item%%[![:space:]]*}"}"
    item="${item%"${item##*[![:space:]]}"}"
    if [ -n "${item}" ] && ! [[ "${item}" =~ ${RECORD_ID_RE} ]]; then
      fail "workflow input ${name,,} must be comma-separated queue record ids matching ${RECORD_ID_RE}"
      return 0
    fi
  done
}

if [ $(( $# % 2 )) -ne 0 ] || [ $# -eq 0 ]; then
  echo "usage: $0 <record-id|record-ids> <ENV_VAR_NAME> [...]" >&2
  exit 2
fi

while [ $# -gt 0 ]; do
  kind="$1" name="$2"
  shift 2
  value="${!name-}"
  case "${kind}" in
    record-id) check_record_id "${name}" "${value}" ;;
    record-ids) check_record_ids "${name}" "${value}" ;;
    *)
      echo "unknown kind: ${kind}" >&2
      exit 2
      ;;
  esac
done

exit "${status}"
