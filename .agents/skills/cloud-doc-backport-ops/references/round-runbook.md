# Backport round runbook

Everything here was earned in real rounds (JE-2000F CN 2026-07-03, JE-900B JP
07-07, JE-1800B JP 07-08/09, AU/JP sweep 07-03). Command shapes were verified
against `tools/cloud_doc_backport_args.py` — if a flag disagrees with this file,
trust `--help` and fix this file in the same PR.

## 1. Preflight

- **Resolve the target.** `python tools/cloud_doc_backport.py resolve-review-branch
  --cloud-doc <url>` maps the doc to its review branch (`Git_ref`) +
  `docs/_review/<model>/<region>` via the build table. When the URL is an
  unregistered 副本/copy, pass `--doc-name manual_<model>_<region>_<ver>` so the
  name resolves model+region. `run-review-branch` performs the same resolution
  and creates a sparse worktree (default root `../review-worktrees`;
  `--full-checkout` to materialize everything).
- **Data snapshot decides classification quality.** The F2 value index needs a
  synced `Spec_Master.csv`. `--data-root` defaults to the repo's `data/phase2`
  *only when it holds a synced Spec_Master* — otherwise Class D falls back to a
  heuristic that has mislabeled real deltas (a JP UPS text was classed D and
  dropped a round). Before load-bearing routing: sync-data in an environment
  with `FEISHU_PHASE2_*` secrets, or point `--data-root` at a current snapshot.
  No usable index ⇒ expect Class D deltas to abstain as `snapshot_only`.
- **Pass `--lang` explicitly** (`zh`, `ja`, `ko`, `fr`, …) unless the doc name
  carries it — auto-derivation exists but a wrong lang silently empties the
  value index.
- **Know your baseline before diffing.** Two baselines, fixed priority:
  ① the build-table row's 「基线文档」 frozen copy (fetch prefers it) >
  ② the branch's `.backport/<doc>.baseline.md` seed file. If ① exists, editing
  or reseeding ② changes nothing — old deltas will re-report idempotently.

## 2. Dry-run

```bash
python tools/cloud_doc_backport.py run-review-branch \
  --cloud-doc <url> [--doc-name manual_je1000f_eu_en_0.8] \
  [--page 05_operation_guide.rst] \
  --lang <lang> [--data-root <phase2-snapshot>] \
  --out reports/cloud_doc_backport/<round>
```

Omit `--page` to diff the whole doc against every
`docs/_review/<model>/<region>/page/*.rst`. Read the WHOLE report, not just the
applied list: the `abstain` / structural-deletion entries are where escapes
live. `--run-id` defaults to `backport-<branch>-<UTC date>` so each round is a
distinct revision-ledger run.

## 3. Route every delta

Decision tree (delta classes come from the report; with no value index the
class is heuristic — re-check against the tree, don't trust the label blindly):

| Signal | Route | How |
| --- | --- | --- |
| Value/data-origin (Class D): old text matches a source value, spec/placeholder row exists | **Source table via F6** | see "apply-source-table forward recipe" below |
| Target-local prose (Class R) in a review page | **Review page** | `--write` applies it; authored (placeholder-free) review-page content is durable — `sync-review` merge_params only re-fills placeholder lines, so per-model fixes need only `docs/_review/...`, never the shared template |
| Family/shared wording (Class T, sibling pages match) | **Template PR + propagation** | edit `docs/templates/...` on a normal branch; in-flight review branches build from their own frozen manifest/pages and will NOT pick it up — same round also edit the affected review pages, or rebuild those branches after merge (`.githooks/pre-push` prints the affected-branch reminder via `tools/check_review_branch_sync.py`) |
| Composite edit (rename + reorder, cross-row) | **Manual mapping** | abstain is by design; map record_ids by hand and batch-write with lark-cli, one logical group at a time, readback each |
| Whole-table / whole-section deletion | **Deletion handling** | never auto-skip; verify against the built artifact (is content really duplicated/removed?), then: review-page structural edit via a `backport/...` sub-branch PR (guarded row-by-row "apply" hollows tables and the rebuild+rediff gate correctly rejects it), or manifest/template fix when the duplication is upstream (e.g. two manifest entries rendering the same 「安全上のご注意」 block) |
| Diff on a *generated* page (`page/spec_*.rst`, csv_page products) | **Fix the data, never the page** | e.g. a missing 認証 line is a Spec_Notes row |
| "New row" in reviewer's table | **Check the source table first** | it is often a rowspan/Row_label split of an existing row, not an F6 row-create |
| Text not found in any source table | **Authored review text** | direct `_review` edit; do not hunt for a source row that doesn't exist |
| Needs a new mechanism / asset that doesn't exist | **Debt** | log it explicitly (PR body follow-up + build-table remark), don't block the round |

Reviewer-input hygiene while routing:

- **Symmetric term pairs:** a reviewer changing one of a pair (输入端口→输入)
  while its mirror (输出端口) is untouched is usually a漏改 — surface it, ask,
  and apply the confirmed pair family-wide, not just the edited half.
- **Reviewer typos** (e.g. a duplicated 「最大30W」) are normalized with
  operator approval before they enter any source table — never transcribe a
  typo into the source of truth.
- **Localized value columns:** for KR/JP/CN targets a spec fix must set BOTH
  `Value_source` and the row's `Value_<lang>` (localized formatting included),
  then the review branch must be re-seeded (Start Review) to pick the new
  values up — `Value_source` alone leaves the localized page printing the old
  value.

### apply-source-table forward recipe (F6)

`run-review-branch` emits `cloud_doc_backport_source_table_change_request.json`
alongside the run report. The write path is R9-gated: human approval + exact
record_id + content field + idempotent. Steps:

1. Open the change-request report; each request carries a `delta_hash`.
2. Present the requests to the operator; collect explicit approval per delta.
3. Dry-run first (default), then write:

   ```bash
   python tools/cloud_doc_backport.py apply-source-table \
     --report reports/.../cloud_doc_backport_source_table_change_request.json \
     --approve <delta_hash> [--approve <delta_hash> ...] \
     --table-binding '<Table>=<BASE_TOKEN>:<TABLE_ID>' [...] \
     --identity bot --write
   ```

   `--table-binding` is required per table with `--write`; unmapped tables are
   skipped safely. TM suggestions are gated separately (`--tm-write
   --tm-binding BASE:TABLE_ID` — widest blast radius, ask before using).
4. The tool GET-checks each cell, skips `already_applied`, abstains on drift,
   and GET-verifies every write — still report record_id + field + new value
   back to the operator per row.

## 4. Post-apply — run the checklist

`references/post-apply-checklist.md`, every item, every round. The deletion
sweep is the one that has caught real escapes twice; treat skipping it as
skipping tests.

## 5. Re-verify to zero

Re-run the §2 dry-run: the round is closed only at deltas=0 (`NO_DIFF`).
Limits to know:

- Local `build.py sync-data` preflight fails without `FEISHU_PHASE2_*` secrets
  (CI-only), and a local `data/phase2/Spec_Master.csv` may be stale — a
  *rebuild-based* rediff=0 can only be produced on the CI/build-queue side.
  `lark-cli` direct reads/writes are unaffected.
- If the review branch was re-seeded mid-round, a `backport/...` sub-branch
  goes DIRTY: reset it onto the new tip and replay the patch, don't merge.

## 6. Advance the baseline (the full posture)

`--seed --reseed --push` only updates baseline ② (the branch seed file). If the
build-table row carries baseline ① (「基线文档」), diff keeps using ① and every
closed delta re-reports next round. Actually advancing = re-snapshot ①:

1. `lark-cli wiki +node-copy` the current review cloud doc into 过程文档管理
   (wiki node `AvBhwdpNxivgXfkPm1VcCG01nPh`, child of the 文档构建 base node) —
   title carries the date; the old baseline copy stays for traceability.
2. Upsert the build-table row (document_link table `tblbnRHjpJeCVTtj`)
   「基线文档」 field to the new copy's URL, and read it back.

## 7. Worktree hygiene

- Recreating a review worktree: `git worktree remove --force` the old one
  first — a stale worktree left on the branch blocks the tool.
- Long-lived worktrees belong under a durable root (e.g.
  `~/Documents/GitHub/auto-manual-worktrees/`), never the session scratchpad
  (`/private/tmp/...` gets reaped by the OS).
- `sync-review-worktrees` bootstraps a worktree for every InReview branch when
  doing a multi-doc sweep.
