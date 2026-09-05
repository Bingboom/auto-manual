# Web Publish Pipeline

This document owns the release contract for responsive manuals published to
Read the Docs. Web delivery is intentionally separate from print delivery.

## 1. Two independent release actions

| `Workflow_action` | Worker | Output authority |
| --- | --- | --- |
| `Publish` | `feishu-build-queue.yml` | IDML, LaTeX, PDF, DOCX, formal Markdown and release manifests |
| `Web Publish` | `feishu-web-publish-queue.yml` | frozen MyST candidate under `Hello-Docs/publish:docs/publish/`, a scope-guarded PR into `main`, and `HTML_link` |

`Publish` never deploys HTML. `Web Publish` never uploads or rewrites print
artifacts. Both actions render reviewed content selected by
`Document_link.Git_ref` with the current `main` toolchain.

## 1.1 Semantic tables and frozen figures

The Web profile renders explicitly declared specification sections across
targets. `h2.hb-spec-section` with a source-authored
`.hb-spec-section-text` title and its adjacent `hb-spec-table` or
`manual-spec-table` are the declaration. The Web adapter in
[`web_spec_component.py`](../../tools/web_spec_component.py) projects their
label/value rows through the existing `HB-TABLE-SPEC` ComponentSpec and public
`web_spec_table_projection`. It keeps inline markup, row order, label spans,
references and adjacent footnotes/safety copy. Only the declared decorative
heading bullet is removed; the Web theme supplies its heading marker.

This semantic path runs before figure routing and does not require an artwork
grant. A matching filename or an ordinary two-column table is insufficient;
missing declarations stay unchanged, while malformed declared sections fail
the build. Section and reference counts come from the source, not a target
constant. `web_manual.json.specifications` remains readable for serialized
compatibility but its old `spec_*`, four-section and two-reference selectors
no longer route or constrain rendering. The `{spec-table}` Markdown directive
already consumes the same public adapter and requires no new interface.

Troubleshooting follows the same semantic-before-figure boundary. In the
RST-to-Web bundle path, [`word_bundle_html.py`](../../tools/word_bundle_html.py)
resolves the current target's `plan_materialized_pages` once and passes a
declaration for the exact materialized paths of `CsvPage(page="troubleshooting")`.
The existing planner owns language/capability selection and `slot_id` naming;
the Web adapter does not infer intent from filenames, translated headers or
error codes. This also covers unmarked `review-asis` snapshots without editing
their reviewed RST. Explicit `table.hb-troubleshooting-table` declarations can
scope individual tables in mixed HTML fragments.

[`web_troubleshooting_component.py`](../../tools/web_troubleshooting_component.py)
shares validation and DOM projection with `{troubleshooting}`. It consumes the
existing `HB-TABLE-TROUBLESHOOTING` CSS; that style binding is **not** a registered
ComponentSpec, and this adapter adds no public schema. The standalone Markdown
extension pack includes this module and is tested outside the repository's
import path. Directive headers and its optional label remain source-owned;
the existing English default headers and ` / ` step syntax remain supported.

A declared CSV page must have exactly one table. Each declared table requires
two nonempty, unspanned header cells and at least one two-cell data row; missing
or ambiguous declared content fails with its source reference. An unmarked
fragment without a page declaration stays unchanged. When an explicitly
declared table has no `thead` (the current JP template uses `header-rows: 0`),
its authored first row becomes `thead`/`th scope="col"`. Existing headers,
ordered body rows, lists, line blocks, links and inline markup are retained.
The existing figure scroll surface gains `tabindex="0"` for keyboard access;
its accessible label comes from the directive label or source header cells.
`web_manual.json.troubleshooting_table` remains readable for serialized
compatibility, but its source patterns no longer route rendering and there is
no fixed error-code inventory. CSV readers, templates and review snapshots
are unchanged.

`figure_targets`, per-figure source patterns, target instances and frozen
composite approval/hash checks retain their existing scope. Other semantic
compositions (LCD, warranty, etc.) still use their legacy target routing;
specifications and troubleshooting are migrated. For a target outside
the frozen figure contract, Web starts at its manifest's first included page;
it does not invent a preface. The frozen US target retains its preface rule.
Cover/TOC/back-cover exclusions remain in force.

Local verification uses the same Markdown-to-Sphinx path without a queue or
online source update. For example, with a separate staging directory:

```bash
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md --config configs/config.us.yaml --model JE-1000F --region US --source review-asis --data-root tests/fixtures/phase2 --staging-root .tmp/web-check --no-clean --skip-root-index
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md --config configs/config.ja.yaml --model JE-1000F --region JP --source runtime --data-root tests/fixtures/phase2 --staging-root .tmp/web-check --no-clean --skip-root-index
python tools/readthedocs_source.py --build-root .tmp/web-check/docs/_build --output-dir .tmp/web-check/docs/_build/rtd
python -m sphinx -b html .tmp/web-check/docs/_build/rtd .tmp/web-check/html
```

Inspect both targets at narrow and wide widths, compare all ordered copy and
asset hashes against the baseline, and compare document-profile outputs
separately. This is local rendering evidence; it does not grant asset approval,
change JP D1–D4 or promote production eligibility.

## 2. Web Publish transaction

1. The business-plane worker claims only rows whose normalized action is
   `web_publish`; `Git_ref` is required.
2. It always runs live `sync-data` with the HT-Docs bot. Approved
   `04_资产导出物` rows are downloaded and hash-verified; unapproved or ambiguous
   Web composites fail closed.
3. The web presentation profile runs `check -> md -> html`. The HTML render is
   a verification output; the MyST directory is the durable publishing input.
4. `latest/web/publish_meta.json` records the target, version, review ref,
   queue rows, MyST source and verified HTML directory.
5. `publish_branch_assembly.py` copies that source into
   `docs/publish/sources/web/<model>/<region>/md/`, preserves other targets,
   rebuilds `docs/publish/web/`, and writes a SHA-256 inventory in
   `docs/publish/publish_manifest.json`.
6. The workflow reconciles the generated `Hello-Docs/publish` candidate with
   current `main`, then refuses to push if the PR diff contains any path outside
   `docs/publish/**`. Review branches are build inputs only; they are never
   merged into either candidate or production history.
7. The workflow advances `publish` with an ordinary non-force push and creates
   or updates the single `publish -> main` PR. A human merges that PR after
   review; only the resulting `main` push is a production RTD trigger. One
   global concurrency group serializes the complete build, branch update, PR,
   and writeback transaction.
8. The assembler creates a collision-checked root alias named from the manual
   stem (for example `/manual_je1000f_us.html`) that forwards to the canonical
   nested Sphinx route. That concise deterministic URL is written to
   `Document_link.HTML_link`. Relative forwarding keeps the generated alias
   valid in both RTD single-version and `/en/latest` deployments. A seven-day
   workflow artifact retains the Web release evidence; the Git branch remains
   the durable snapshot.

## 3. Repository and hosting boundaries

- Code changes land only in `Bingboom/auto-manual`, then
  `sync-hello-docs.yml` mirrors the engineering tree into
  `Bingboom/Hello-Docs/main` while preserving the business-owned
  `docs/publish/**` subtree already merged there.
- `Hello-Docs/publish` is a generated release-candidate branch. Operators do
  not edit it by hand, and it is not the GitHub repository's development or
  production branch.
- The only release PR into `Hello-Docs/main` is `publish -> main`, and its diff
  must contain only `docs/publish/**`. A whole `review/*` branch is never a
  release PR and must never be merged into `main`.
- `docs/publish/**` is a Web-only Git surface: it may contain only frozen Web
  source/assets, the assembled Sphinx source, and `publish_manifest.json`.
  The assembler rejects IDML, InDesign, LaTeX, PDF, DOCX, source-artwork, and
  archive files before the candidate branch can be pushed. Print artifacts
  remain under release storage and short-lived GitHub Actions artifacts.
- The Read the Docs project uses `main` as its default build branch and builds
  `docs/publish/web/` through `.readthedocs.yaml`.
- RTD never receives Feishu credentials and never reads mutable attachments.
  It renders only the frozen, hash-inventoried Git snapshot.

The first Web Publish creates `publish` from the current business-plane `main`.
Later runs retain the existing target sources, record current `main` as an
ancestor, refresh the tracked code/config tree to current `main`, replace only
the newly published target, and append normal commits. A non-fast-forward push
fails instead of overwriting another publisher. The three-dot PR diff is checked
before the push so branch-history drift cannot smuggle code or review files into
the release PR.

## 4. Operator contract

Before dispatch, the `Document_link` row must have:

- `Workflow_action = Web Publish`
- `Git_ref = <review branch>`
- `是否触发文档构建 = Y`
- `是否立即构建 = checked` when immediate dispatch is required

For a composite figure plus its governed copy, the matching
`04_资产导出物` row must have one `export_file`, a selected `web_locale`, valid
`content_sha256` and `source_fragment_sha256`,
`artifact_kind = web-composite`, `gate_status = approved`,
`build_eligible = true`, and `visual_review_required = false`.

Success requires all three pieces of evidence:

- the GitHub run is green;
- `Hello-Docs/publish` contains the expected target and manifest hashes, and the
  open `publish -> main` PR contains no path outside `docs/publish/**`;
- after that PR is merged, `Hello-Docs/main` contains the same manifest and the
  RTD page opens at the `HTML_link` route.

## 5. Rollback

Do not force-push `publish`. Re-run Web Publish from the approved review ref and
asset rows to append a corrected candidate snapshot. For an urgent hosting
rollback, prepare a `docs/publish/**`-only revert PR into `main`, verify the
generated manifest, merge it, and let the `main` webhook rebuild RTD.
