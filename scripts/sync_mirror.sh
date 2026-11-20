#!/usr/bin/env bash
# Compose and push one mirror commit: the auto-manual source tree plus the
# mirror's own content paths, which only the mirror maintains, with the
# mirror's own README when MIRROR_README names one.
#
# Run from a directory holding the two checkouts `source/` (auto-manual) and
# `mirror/` (the mirror, with push access on `origin`). Used by
# .github/workflows/sync-hello-docs.yml for Hello-Docs and Hello-Docs-Review.
#
#   MIRROR_KEEP_PATHS       strict paths the mirror owns (space separated): when the path is a
#                           directory in the mirror head, the mirror's subtree replaces the
#                           source's wholesale ("mirror wins"). A keep path that is a file in the
#                           mirror head is an error. Pair each with SOURCE_FORBIDDEN_PATHS.
#   MIRROR_OVERLAY_PATHS    optional transitional paths (space separated, files or directories):
#                           file-level union with the source winning. Source files are added and
#                           updated as before; files that exist only in the mirror head are kept,
#                           so removing a file or sub-directory upstream does not remove it
#                           downstream. Where a file and a directory collide, the source wins.
#   MIRROR_OVERLAY_PRUNE_EXTERNALIZED
#                           when "1", mirror-only overlay files absent from source/ and superseded
#                           by an upstream external-source-pointer/v1 pointer (direct sidecar or
#                           split archive_parts) are pruned instead of kept (default "0").
#   SOURCE_FORBIDDEN_PATHS  paths auto-manual must never contain (defaults to the kept paths)
#   MIRROR_README           optional source file installed as the mirror's README.md
#                           (mirrors/<repository>/README.md, maintained in auto-manual)
#   MIRROR_DRY_RUN          when "1", compose the tree, print the per-path summary, the diff
#                           against the mirror head and DRY_RUN composed_tree=<sha>, and exit 0
#                           without creating a commit or pushing (default "0")
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
overlay_paths="${MIRROR_OVERLAY_PATHS:-}"
prune_externalized="${MIRROR_OVERLAY_PRUNE_EXTERNALIZED:-0}"
forbidden_paths="${SOURCE_FORBIDDEN_PATHS:-${keep_paths}}"
script_repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${PYTHON:-python3}"

# Two path lists overlap when an entry equals, contains or lies under another.
overlaps() {
  [ "$1" = "$2" ] || [ "${1#"$2"/}" != "$1" ] || [ "${2#"$1"/}" != "$2" ]
}
check_disjoint() {
  local left_name="$1" left="$2" right_name="$3" right="$4" a b
  for a in ${left}; do
    for b in ${right}; do
      if [ "${left_name}" = "${right_name}" ] && [ "${a}" = "${b}" ]; then continue; fi
      if overlaps "${a}" "${b}"; then
        echo "::error::${left_name} entry ${a} overlaps ${right_name} entry ${b}; each path may have one rule only."
        exit 1
      fi
    done
  done
}
check_disjoint MIRROR_KEEP_PATHS "${keep_paths}" MIRROR_KEEP_PATHS "${keep_paths}"
check_disjoint MIRROR_OVERLAY_PATHS "${overlay_paths}" MIRROR_OVERLAY_PATHS "${overlay_paths}"
check_disjoint MIRROR_OVERLAY_PATHS "${overlay_paths}" MIRROR_KEEP_PATHS "${keep_paths}"
check_disjoint MIRROR_OVERLAY_PATHS "${overlay_paths}" SOURCE_FORBIDDEN_PATHS "${forbidden_paths}"

source_tree="$(git -C source rev-parse HEAD^{tree})"
mirror_parent="$(git -C mirror rev-parse HEAD)"

source_bundle="$(mktemp)"
snapshot_commit="$(git -C source -c user.name=sync -c user.email=sync@local commit-tree "${source_tree}" -m "sync snapshot")"
git -C source update-ref refs/sync/snapshot "${snapshot_commit}"
git -C source bundle create "${source_bundle}" refs/sync/snapshot
git -C source update-ref -d refs/sync/snapshot
git -C mirror fetch --quiet "${source_bundle}" refs/sync/snapshot
rm -f "${source_bundle}"

for content_path in ${forbidden_paths}; do
  if git -C mirror cat-file -e "${source_tree}:${content_path}" 2>/dev/null; then
    echo "::error::auto-manual must not own ${content_path}; maintain content through a PR on the mirror that owns it."
    exit 1
  fi
done

object_type() {  # object_type <tree-ish> <path>: tree, blob, commit or empty when absent
  git -C mirror cat-file -t "$1:$2" 2>/dev/null || true
}

# list_entries <index-file> <path>: NUL-separated "mode oid stage<TAB>path" index entries at,
# under, or above <path> (an entry above it is a file where a parent directory would go).
list_entries() {
  GIT_INDEX_FILE="$1" git -C mirror ls-files -s -z | awk -v P="$2" 'BEGIN { RS = ORS = "\0" }
    { t = index($0, "\t"); p = substr($0, t + 1)
      if (p == P || index(p, P "/") == 1 || index(P, p "/") == 1) print }'
}

# overlay_entries <source-entries> <mirror-entries> <stats-file>: print the mirror entries to add
# (ls-tree lines, NUL separated) and write "kept updated conflicts" to <stats-file>.
overlay_entries() {
  awk -v STATS="$3" 'BEGIN { RS = ORS = "\0" }
    function path_of(line) { return substr(line, index(line, "\t") + 1) }
    function oid_of(line,   f) { split(substr(line, 1, index(line, "\t") - 1), f, " "); return f[2] }
    FILENAME == ARGV[1] { p = path_of($0); S[p] = oid_of($0)
                n = split(p, c, "/"); d = c[1]
                for (i = 2; i <= n; i++) { D[d] = 1; d = d "/" c[i] }
                next }
    { m = path_of($0)
      split(substr($0, 1, index($0, "\t") - 1), f, " ")
      if (m in S) { if (S[m] != f[3]) updated++; next }
      if (m in D) { conflicts++; next }
      n = split(m, c, "/"); d = c[1]; blocked = 0
      for (i = 2; i <= n; i++) { if (d in S) { blocked = 1; break }; d = d "/" c[i] }
      if (blocked) { conflicts++; next }
      kept++; print }
    END { printf "%d %d %d\n", kept, updated, conflicts > STATS }' "$1" "$2"
}

# Compose the source tree with the content paths of ${mirror_parent} into ${combined_tree};
# collect one summary line per path in ${path_summary}.
compose() {
  local mirror_index content_path kind content_tree source_oid work stats a readme_blob kept updated conflicts pruned
  mirror_index="$(mktemp)"
  rm -f "${mirror_index}"
  work="$(mktemp -d)"
  path_summary=""
  GIT_INDEX_FILE="${mirror_index}" git -C mirror read-tree "${source_tree}"

  for content_path in ${keep_paths}; do
    kind="$(object_type "${mirror_parent}" "${content_path}")"
    source_oid="$(git -C mirror rev-parse --verify --quiet "${source_tree}:${content_path}" || true)"
    case "${kind}" in
      "")
        if [ -n "${source_oid}" ]; then
          echo "::warning::Keep path ${content_path} is not in the mirror yet, so the source copy passes through this time and the mirror owns it afterwards; add it to SOURCE_FORBIDDEN_PATHS or MIRROR_OVERLAY_PATHS."
        fi
        path_summary+="keep ${content_path}: absent in mirror head"$'\n'
        continue ;;
      tree) ;;
      *)
        echo "::error::Keep path ${content_path} is a ${kind}, not a directory, in the mirror head ${mirror_parent}; MIRROR_KEEP_PATHS entries must be directories (use MIRROR_OVERLAY_PATHS for a file)."
        exit 1 ;;
    esac
    content_tree="$(git -C mirror rev-parse "${mirror_parent}:${content_path}")"
    list_entries "${mirror_index}" "${content_path}" > "${work}/source"
    git -C mirror ls-tree -r -z --full-tree "${mirror_parent}" -- "${content_path}" > "${work}/mirror"
    # mirror_only: mirror files the source lacks; source_dropped: source files whose content
    # the mirror's subtree replaces or removes.
    stats="$(awk 'BEGIN { RS = "\0" }
      { t = index($0, "\t"); split(substr($0, 1, t - 1), f, " "); p = substr($0, t + 1) }
      FILENAME == ARGV[1] { S[p] = f[2]; next }
      { M[p] = f[3]; if (!(p in S)) mirror_only++ }
      END { for (p in S) if (!(p in M) || M[p] != S[p]) dropped++
            printf "%d %d", mirror_only, dropped }' "${work}/source" "${work}/mirror")"
    if [ -n "${source_oid}" ] && [ "${source_oid}" != "${content_tree}" ]; then
      echo "::warning::Keep path ${content_path} still exists in ${SOURCE_REPOSITORY} with different content; the mirror copy wins and source changes under it do not reach the mirror (mirror-only files ${stats% *}, source files dropped ${stats#* })."
    fi
    path_summary+="keep ${content_path}: mirror_only_kept=${stats% *} source_dropped=${stats#* }"$'\n'
    # A source file where a parent directory of the path belongs gives way to the mirror subtree.
    a="${content_path}"
    while [ "${a%/*}" != "${a}" ]; do
      a="${a%/*}"
      GIT_INDEX_FILE="${mirror_index}" git -C mirror update-index --force-remove -- "${a}"
    done
    GIT_INDEX_FILE="${mirror_index}" git -C mirror rm -r -f --cached --quiet --ignore-unmatch -- ":(literal)${content_path}"
    GIT_INDEX_FILE="${mirror_index}" git -C mirror read-tree --prefix="${content_path}/" "${content_tree}"
  done

  for content_path in ${overlay_paths}; do
    kind="$(object_type "${mirror_parent}" "${content_path}")"
    case "${kind}" in
      "") path_summary+="overlay ${content_path}: absent in mirror head (source passes through)"$'\n'; continue ;;
      tree|blob) ;;
      *) echo "::error::Overlay path ${content_path} is a ${kind} in the mirror head ${mirror_parent}; MIRROR_OVERLAY_PATHS entries must be files or directories."
         exit 1 ;;
    esac
    list_entries "${mirror_index}" "${content_path}" > "${work}/source"
    git -C mirror ls-tree -r -z --full-tree "${mirror_parent}" -- "${content_path}" > "${work}/mirror"
    overlay_entries "${work}/source" "${work}/mirror" "${work}/stats" > "${work}/add"
    read -r kept updated conflicts < "${work}/stats"
    pruned=0
    if [ "${prune_externalized}" = "1" ] && [ -s "${work}/add" ]; then
      PYTHONPATH="${script_repo}${PYTHONPATH:+:${PYTHONPATH}}" "${python_bin}" -m tools.web.mirror_overlay_prune filter-ls-tree \
        --source-root source \
        --overlay-paths "${overlay_paths}" \
        --input "${work}/add" \
        --output "${work}/add.pruned" \
        --stats-file "${work}/prune_stats"
      mv "${work}/add.pruned" "${work}/add"
      read -r kept pruned < "${work}/prune_stats"
    fi
    if [ -s "${work}/add" ]; then
      GIT_INDEX_FILE="${mirror_index}" git -C mirror update-index -z --index-info < "${work}/add"
    fi
    if [ "${pruned}" -gt 0 ]; then
      echo "::notice::Overlay path ${content_path} pruned ${pruned} externalized file(s) superseded by upstream pointers."
    fi
    if [ "${kept}" -gt 0 ]; then
      echo "::notice::Overlay path ${content_path} keeps ${kept} file(s) that exist only in the mirror (deleted upstream or written downstream)."
    fi
    if [ "${prune_externalized}" = "1" ]; then
      path_summary+="overlay ${content_path}: mirror_only_kept=${kept} source_updated=${updated} mirror_lost_to_source_conflict=${conflicts} pruned_externalized=${pruned}"$'\n'
    else
      path_summary+="overlay ${content_path}: mirror_only_kept=${kept} source_updated=${updated} mirror_lost_to_source_conflict=${conflicts}"$'\n'
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
  rm -rf "${work}" "${mirror_index}"
}

if [ "${MIRROR_DRY_RUN:-0}" = "1" ]; then
  compose
  printf 'DRY_RUN path summary:\n%s' "${path_summary}"
  echo "DRY_RUN diff against mirror head ${mirror_parent}:"
  git -C mirror -c core.quotePath=false diff-tree -r --no-renames --name-status \
      "${mirror_parent}^{tree}" "${combined_tree}" \
    | awk -F '\t' '{ n = split($2, c, "/"); g = (n > 2) ? c[1] "/" c[2] "/" : $2
                     count[$1 " " g]++ }
                   END { for (k in count) printf "  %s (%d files)\n", k, count[k] }' | sort
  echo "  $(git -C mirror diff-tree -r --shortstat "${mirror_parent}^{tree}" "${combined_tree}" | sed 's/^ *//')"
  echo "DRY_RUN composed_tree=${combined_tree}"
  exit 0
fi

# Third guard, independent of the workflow's expressions: in Actions, only a run of main may
# commit or push; every other ref (a branch, a pull request) is limited to a dry run.
if [ -n "${GITHUB_REF:-}" ] && [ "${GITHUB_REF}" != "refs/heads/main" ] && [ "${MIRROR_DRY_RUN:-0}" != "1" ]; then
  echo "::error::GITHUB_REF is ${GITHUB_REF}; only refs/heads/main may push a mirror. Set MIRROR_DRY_RUN=1 to compose without pushing."
  exit 1
fi

git -C mirror config user.name "github-actions[bot]"
git -C mirror config user.email "41898282+github-actions[bot]@users.noreply.github.com"

attempts="${MIRROR_PUSH_ATTEMPTS:-3}"
local_head="${mirror_parent}"
attempt=1
while :; do
  compose
  printf 'Sync path summary on %s:\n%s' "${mirror_parent}" "${path_summary}"
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
