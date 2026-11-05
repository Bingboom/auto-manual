#!/usr/bin/env bash
# Compose and push one mirror commit: the auto-manual source tree plus the
# mirror's own content paths, which only the mirror maintains, with the
# mirror's own README when MIRROR_README names one.
#
# Run from a directory holding the two checkouts `source/` (auto-manual) and
# `mirror/` (the mirror, with push access on `origin`). Used by
# .github/workflows/sync-hello-docs.yml for Hello-Docs and Hello-Docs-Review.
#
#   MIRROR_KEEP_PATHS       paths the mirror owns and keeps (space separated)
#   SOURCE_FORBIDDEN_PATHS  paths auto-manual must never contain (defaults to the kept paths)
#   MIRROR_README           optional source file installed as the mirror's README.md
#                           (mirrors/<repository>/README.md, maintained in auto-manual)
#   MIRROR_PUSH_ATTEMPTS    pushes to try (default 3); a rejected push is retried only when
#                           the mirror branch moved meanwhile, recomposed on its new head
#   MIRROR_BRANCH, SOURCE_REPOSITORY, SOURCE_SHA, SOURCE_RUN_URL
#
# The mirror's own paths change while a sync runs (drafts are committed straight to
# Hello-Docs-Review main), so a push can be rejected as non-fast-forward. The sync then
# fetches the branch, rebuilds the commit on the new head, keeping that head's content,
# and pushes again. It never force-pushes.
set -euo pipefail

: "${MIRROR_BRANCH:?}" "${SOURCE_REPOSITORY:?}" "${SOURCE_SHA:?}" "${SOURCE_RUN_URL:?}"
keep_paths="${MIRROR_KEEP_PATHS:?}"
forbidden_paths="${SOURCE_FORBIDDEN_PATHS:-${keep_paths}}"

source_tree="$(git -C source rev-parse HEAD^{tree})"
mirror_parent="$(git -C mirror rev-parse HEAD)"

source_bundle="$(mktemp)"
git -C source bundle create "${source_bundle}" HEAD
git -C mirror fetch --quiet "${source_bundle}" HEAD

for content_path in ${forbidden_paths}; do
  if git -C mirror cat-file -e "${source_tree}:${content_path}" 2>/dev/null; then
    echo "::error::auto-manual must not own ${content_path}; maintain content through a PR on the mirror that owns it."
    exit 1
  fi
done

# Compose the source tree with the content paths of ${mirror_parent} into ${combined_tree}.
compose() {
  local mirror_index content_path content_tree readme_blob
  mirror_index="$(mktemp)"
  rm -f "${mirror_index}"
  GIT_INDEX_FILE="${mirror_index}" git -C mirror read-tree "${source_tree}"
  for content_path in ${keep_paths}; do
    content_tree="$(git -C mirror rev-parse --verify "${mirror_parent}:${content_path}" 2>/dev/null || true)"
    if [ -n "${content_tree}" ]; then
      GIT_INDEX_FILE="${mirror_index}" git -C mirror read-tree \
        --prefix="${content_path}/" "${content_tree}"
    fi
  done
  if [ -n "${MIRROR_README:-}" ]; then
    readme_blob="$(git -C mirror rev-parse --verify --quiet "${source_tree}:${MIRROR_README}" || true)"
    if [ -z "${readme_blob}" ] || [ "$(git -C mirror cat-file -t "${readme_blob}")" != "blob" ]; then
      echo "::error::${MIRROR_README} is not a file in ${SOURCE_REPOSITORY}@${SOURCE_SHA}; each mirror's README is maintained there."
      exit 1
    fi
    GIT_INDEX_FILE="${mirror_index}" git -C mirror update-index --add \
      --cacheinfo "100644,${readme_blob},README.md"
  fi
  combined_tree="$(GIT_INDEX_FILE="${mirror_index}" git -C mirror write-tree)"
}

git -C mirror config user.name "github-actions[bot]"
git -C mirror config user.email "41898282+github-actions[bot]@users.noreply.github.com"

attempts="${MIRROR_PUSH_ATTEMPTS:-3}"
local_head="${mirror_parent}"
attempt=1
while :; do
  compose
  if [ "${combined_tree}" = "$(git -C mirror rev-parse "${mirror_parent}^{tree}")" ]; then
    echo "Mirror code already matches ${SOURCE_REPOSITORY}@${SOURCE_SHA}; business content is preserved."
    exit 0
  fi

  mirror_commit="$(git -C mirror commit-tree "${combined_tree}" \
    -p "${mirror_parent}" \
    -m "chore(mirror): sync auto-manual main" \
    -m "Source: ${SOURCE_REPOSITORY}@${SOURCE_SHA}" \
    -m "Run: ${SOURCE_RUN_URL}")"

  git -C mirror update-ref "refs/heads/${MIRROR_BRANCH}" "${mirror_commit}" "${local_head}"
  local_head="${mirror_commit}"

  mirror_tree="$(git -C mirror rev-parse "${mirror_commit}^{tree}")"
  if [ "${combined_tree}" != "${mirror_tree}" ]; then
    echo "::error::Mirror tree ${mirror_tree} does not match composed tree ${combined_tree}."
    exit 1
  fi

  if git -C mirror push origin "${mirror_commit}:${MIRROR_BRANCH}"; then
    exit 0
  fi

  # Retry only a race: the mirror branch must have moved since ${mirror_parent}.
  git -C mirror fetch --quiet origin "${MIRROR_BRANCH}"
  remote_head="$(git -C mirror rev-parse FETCH_HEAD)"
  if [ "${remote_head}" = "${mirror_parent}" ]; then
    echo "::error::Push to ${MIRROR_BRANCH} failed and the branch has not moved; not retrying."
    exit 1
  fi
  if ! git -C mirror merge-base --is-ancestor "${mirror_parent}" "${remote_head}"; then
    echo "::error::${MIRROR_BRANCH} was rewritten (${mirror_parent} is no longer its ancestor); not retrying."
    exit 1
  fi
  if [ "${attempt}" -ge "${attempts}" ]; then
    echo "::error::Push to ${MIRROR_BRANCH} still rejected after ${attempts} attempts; rerun the sync."
    exit 1
  fi
  attempt=$((attempt + 1))
  echo "::notice::${MIRROR_BRANCH} moved to ${remote_head} during the sync; recomposing on it (attempt ${attempt} of ${attempts})."
  mirror_parent="${remote_head}"
done
