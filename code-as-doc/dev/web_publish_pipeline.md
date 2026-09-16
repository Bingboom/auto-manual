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

The table above describes the queue-driven input path. An authorized Git-only
release can instead use reviewed, committed sources and assets without creating
queue rows or reading or writing online tables. It does not change either
workflow. Both input paths converge on the same assembler, the same
`docs/publish/**`-only release PR, and the same Read the Docs production build.
Explicit Git-only [withdrawal/restoration](web_publication_withdrawal.md) uses
the same assembly and atomic promotion helpers with a durable action ledger.
Publication omission still means preservation; withdrawn versions cannot be
reintroduced by an ordinary retry.

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
composite approval/hash checks retain their existing scope. Warranty is a
shared semantic composition and runs independently of that artwork grant: its
source-owned localized unit and label are retained while the Web adapter supplies
the common 3-year/2-year badge treatment. LCD, specifications, troubleshooting
and Inbox likewise follow their own declaration/semantic admission rules. For a
target outside the frozen figure contract, Web starts at its manifest's first
included page; it does not invent a preface. The frozen US target retains its
preface rule. Cover/TOC/back-cover exclusions remain in force.

Figure carrier choice is part of the component contract, not an extraction
default:

- Product Overview, the five Operation panels, and the four Charging panels use
  locale-matched `localized-full-page` composites. Their visible callouts,
  prerequisites, connection labels, and Operation `On` / `Off` instructions are
  intentionally embedded in the approved crop. Extraction may crop the panel but
  must not redact that localized text. The section heading remains live HTML.
- The Operation LCD screen-mode block is deliberately hybrid: only the
  market-correct product/display artwork is an image, while the six-row state /
  action / explanation table remains searchable, responsive HTML. A screenshot
  of the complete LCD table is not a valid replacement.
- Specifications, troubleshooting, the LCD-icon glossary, Warranty and other
  semantic tables remain live components unless their own contract explicitly
  says otherwise.

Target reuse follows inheritance plus narrow overrides. A child Product Overview
instance may `extend` a validated base instance; lists whose members have stable
`id` values merge by `id`, so the child can override only target identity,
market-specific artwork keys and locale declarations while inheriting callout
order and Web/IDML geometry. Ordinary lists still replace as a unit. Composite
locale resolution prefers the materialized document language; filename patterns
remain only a legacy fallback. Coverage provenance identifies an approved
composite by `asset_key + locale + content_sha256`, including the case where two
locales intentionally share identical bytes.

`JE-1000F / EU` is admitted to the figure contract and its Overview instance
extends `je1000f-us-v1`; EN/FR/ES/DE/IT use one shared component definition with
locale-specific composite bindings. EU does not inherit the US-only preface
rule. Extracted PDF composites remain quarantine candidates until pixel review
and normal manifest/registry approval; contract admission alone is not asset
promotion.

Every newly generated Web `manual.ir.json` contains a
`metadata.web_figure_coverage` payload with schema
`web-figure-coverage/v1`. It audits actual rendered Overview, Operation and
Charging slots through one status vocabulary:

| Status | Meaning |
| --- | --- |
| `finished-panel` | A `web-illustrations/v1` entry replaced one or more source images with one approved, hash-pinned panel. |
| `approved-composite` | A target/locale/source-matched `web-composite-manifest/v1` asset overrides the semantic fallback. |
| `editable-fallback` | The governed semantic figure remains live/searchable because no approved composite was bound. |
| `missing` | The rendered source image has neither an approved finished panel nor an admitted semantic fallback. |

The inventory records page, section and stable slot identity; approved rows
also retain their packaged path and SHA-256 evidence. Its totals are validated
again before IR replay. It is an audit, not an automatic approval gate: known
asset debt remains buildable and visible. A missing row is closed only by
adding an approved manifest/recipe asset; copying another region's panel or
adding page-specific Python/CSS is not a valid override.

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

## 2. Web Publish input paths and shared release outlet

### 2.1 Queue-driven transaction

1. The business-plane worker claims only rows whose normalized action is
   `web_publish`; `Git_ref` is required.
2. It always runs live `sync-data` with the HT-Docs bot. Approved
   `04_资产导出物` rows are downloaded and hash-verified; unapproved or ambiguous
   Web composites fail closed.
3. The web presentation profile runs `check -> md -> html`. The HTML render is
   a verification output; the MyST directory is the durable publishing input.
   With an explicit target language, each successful action captures the
   canonical projection and complete include closure. The captures must agree;
   the [receipt](web_language_release_evidence.md) is sealed with md/html in the
   same new immutable version. A shared-language config uses the selected
   language for release paths, not its first configured language.
4. `latest/web/publish_meta.json` records the target, version, review ref,
   queue rows, MyST source and verified HTML directory. Explicit-language
   metadata also requires the verified receipt path and SHA-256 before it can
   claim `language_scope=single`; language and evidence must be supplied together.
5. `publish_branch_assembly.py` copies that source into
   `docs/publish/sources/web/<model>/<region>/<lang>/md/`, preserves other targets,
   rebuilds `docs/publish/web/`, and writes a SHA-256 inventory in
   `docs/publish/publish_manifest.json`. Assembly rechecks fresh md/html against
   evidence and retains the receipt plus projection manifest with stored MyST.
   Stored replay rechecks the retained MyST/assets; the HTML digest is historical
   evidence, not a new HTML render check. Legacy links retain their redirects.
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

### 2.2 Git-only transaction

Use this path only when the operator has designated reviewed Git content as the
release authority and explicitly excluded online-table writes. It never
creates synthetic queue rows, and assembly/build/verification never write any
online table. Writing `Document_link.HTML_link` and the published-manual
catalog row is a distinct, explicit, human-gated step
(`build.py web-receipt --write`, step 7 below) run only after the release PR
has merged and production has been verified — never automatically as part of
build, staging, or the release PR.

`python build.py web-release --config <config> --model <M> --region <R> --lang
<L> --version <V>` is the formal entry point for steps 2 and 3 below: it runs
the warm-up + check/md/html web-profile build, captures and seals the
per-language projection receipt, runs the local strict `sphinx -W`
verification, stages the sealed bundle under
`<model>/<region>/<lang>/versions/<version>/web/`, and writes
`latest/web/publish_meta.json` — the same library functions the queue-driven
Web Publish worker uses (`tools.queue_build_execution`,
`tools.queue_bound_outputs`, `tools.web_language_release_evidence`), run
directly against the current checkout instead of a queue row. `--dry-run`
prints the resolved target list and exits without building. `--targets-file`
runs a batch of `MODEL,REGION,LANG[,VERSION]` rows and keeps going past a
single failed book, so a multi-language family (for example three rows for
one model/region) does not abort the rest. It does not perform step 1
(authoring `source_manifest.json`) or steps 4–6 (assembling into
`docs/publish/**` and opening the release PR) below; those remain manual until
a later conveyor-belt command covers them. See
[`tools/web_publish.py`](../../tools/web_publish.py) for the implementation
and `tests/test_web_publish.py` for its contract.

`python build.py web-assemble [--releases-root <path>] [--title <title>]
[--hello-docs-repo <owner/repo>] [--push]` is the formal entry point for steps
4 and 5 below: it makes an isolated blobless clone of Hello-Docs
(`--filter=blob:none`: the full commit graph up front, file contents fetched
lazily on checkout — never `--depth`, since the ancestry check below needs
real history) under a scratch temporary directory (never the operator's own
local Hello-Docs checkout), reconciles it against the existing `publish`
branch tip when one exists (preserving any targets already staged there),
assembles every book staged under `--releases-root` (default
`reports/releases`) with the same `tools/publish_branch_assembly.py` this
section already documents, and runs
the same aggregate `sphinx -W -b html` verification. It then checks the
candidate's three-dot diff against `main` and refuses to continue if any path
outside `docs/publish/**` changed — the same scope guard the queue workflow's
"Validate publish PR scope" step enforces. By default it stops there
(assemble + verify + scope guard only, no network write); only `--push`
advances the shared `publish` branch with an ordinary, never-forced push and
opens or updates the single `publish -> main` PR. It never merges that PR —
merging stays a human step in every path. It does not author
`source_manifest.json` (step 1) or perform the post-merge verification (step
6); those remain manual. See [`tools/web_assemble.py`](../../tools/web_assemble.py)
for the implementation and `tests/test_web_assemble.py` for its contract.

`python build.py web-receipt --config <config> [--model <M> --region <R>
--lang <L>] [--write]` is the formal entry point for step 7 below: for every
`latest/web/publish_meta.json` target under `--releases-root` (default
`reports/releases`, narrowed by `--model`/`--region`/`--lang` when given), it
resolves the `Document_link` row through a priority chain (explicit
`--receipt-record-id` overrides > `publish_meta.json`'s `queue_record_ids` >
a live search by model/region/lang, needed because a Git-only book never had
a queue row and so `queue_record_ids` is always empty for it), writes
`HTML_link`, then creates or updates the matching published-manual catalog
(发布文档管理) row by (model, region, lang, `doc_type=web`), and GETs each
written record back to confirm the persisted value before reporting success.
Zero matching `Document_link` rows is reported, not auto-repaired — this
command never creates a queue row. More than one candidate row (for either
table) is rejected with every candidate listed; resolving that is an
operator decision. Defaults to dry-run: without `--write` it only reads local
`publish_meta.json` files and prints the resolved plan, touching no live
table; `--write` performs the live writes. See
[`tools/web_receipt.py`](../../tools/web_receipt.py) and
[`tools/manual_catalog_writeback.py`](../../tools/manual_catalog_writeback.py)
for the implementation and `tests/test_web_receipt.py` /
`tests/test_manual_catalog_writeback.py` for their contract.

1. Commit the complete target structure, sources and assets with a
   `source_manifest.json`. Record the target identity, source authority,
   original filename and SHA-256, included pages, deliberate normalizations,
   and an input SHA-256 inventory. If the printed-manual version is unknown,
   keep it unknown. A technical snapshot version such as
   `git-<date>-<source-sha-prefix>` identifies the Git release input; it is not
   a paper-manual version.
2. At the exact source Git ref, run the target `build.py check`, render the Web
   presentation profile to MyST, build it with strict Sphinx, and inspect the
   actual page at desktop and mobile widths for image URLs and page overflow.
   When the target uses public IR or packaged assets, retain cold-replay and
   asset-tamper evidence as applicable.
3. Put the verified MyST and verification HTML in an isolated release root.
   Write a real `auto-manual-web-publish/v1` record at
   `<model>/<region>/<lang>/latest/web/publish_meta.json`. Its
   `md_output_path` and `html_dir` must stay inside that release root, and the
   HTML directory must contain `index.html`. Record at least `model`, `region`,
   `lang`, `version`, `built_at`, `git_ref`, `md_output_path`, and `html_dir`.
4. Start from current `Hello-Docs/main:docs/publish/**` in an isolated checkout
   so previously published targets remain present. Assemble and verify the
   candidate with:

   ```bash
   python tools/publish_branch_assembly.py --releases-root <isolated-release-root> --output-dir <hello-docs-candidate>/docs/publish
   python -m sphinx -W -b html <hello-docs-candidate>/docs/publish/web <isolated-verification-html>
   ```

   The assembler replaces matching target routes, retains the other stored
   targets, rebuilds the aggregate Sphinx tree, and rewrites
   `publish_manifest.json`. `python build.py web-assemble` (without `--push`)
   runs exactly this step against a fresh isolated clone.
5. Commit that candidate on the normal Hello-Docs release branch and open the
   usual `docs/publish/**`-only PR. Do not include engineering code, review
   branches, print artifacts, or unrelated targets. `python build.py
   web-assemble --push` runs this step too: a non-force `publish` push plus
   opening or updating the single `publish -> main` PR.
6. After the approved PR merges, verify the Read the Docs build commit, each
   canonical target route, each short root alias, all referenced assets, and
   desktop/mobile rendering.
7. Only once that verification is in hand, run `build.py web-receipt --write`
   for the released target(s) to write `Document_link.HTML_link` and the
   published-manual catalog row, and confirm the reported per-target GET
   readback for both records.

The durable evidence is the source Git commit, source-manifest and input hashes,
release metadata, publish-manifest hash, Hello-Docs snapshot commit, Read the
Docs build commit, and the verified production URLs. For a Git-only
transaction, `Document_link.HTML_link` and the published-manual catalog row
are written only by the explicit step 7 receipt above, after that evidence is
already in hand; no earlier step in this section writes online staging,
source, asset, build, or link records.

### 2.3 PDF sideload bypass

Steps 2-3 above assume the target's structured intake (spec extraction,
templating) is already done, so `build.py check`/render can actually run.
Some books must go live before that is true — the printed PDF exists but
`spec-sheet-structured-intake` has not landed real phase2 data for the
target yet. `python build.py web-sideload --config <config> --model <M>
--region <R> --lang <L> --version <V> --md-dir <bundle>
[--debt "category:location:payoff action"]... [--dry-run]` is the bypass for
exactly that gap: it stages an **externally converted** MyST Markdown
source — never rendered by this repo's RST -> Web-profile pipeline — using
the same `tools.queue_bound_outputs.stage_web_publish_assets_to_host_repo`
and `write_web_publish_metadata` that `web-release` uses, so `web-assemble`
collects it with equal standing to a pipeline-built book.

`--md-dir` must already be shaped like a staged `md/` bundle: a
`manual_<stem>.md` whose filename matches what the config's output-naming
template would produce for that exact model/region/lang (the same
derivation `resolve_md_output_path_for_target` uses for `web-release`'s
collision precheck), an `index.md` toctree naming that stem, `conf.py`, and
an optional `assets/`. A wrong filename fails with the exact expected name
rather than silently staging under the wrong route. Before staging,
`web-sideload` runs its own local strict `sphinx -W -b html` build of that
bundle — the same rigor `web-release` applies to a pipeline build, just
against externally supplied source — and that HTML output is staged
directly (there is no separate pipeline HTML build to reuse here).

Because there is no RST -> Web-profile pipeline run, there is no per-language
projection evidence to seal. The staged `publish_meta.json` instead carries
an explicit `"source_kind": "pdf_sideload"` marker (a pipeline-built
target either omits `source_kind` or carries `"source_kind": "pipeline"`,
unchanged from before this marker existed). That marker is the **only**
thing `tools.publish_locale_identity` / `tools.publish_branch_assembly`
accept as exempting a target from the otherwise-mandatory
`language_projection_evidence_*` gate described in §1 and §2.2 above; every
pipeline target — with or without an explicit `source_kind` — stays exactly
as fail-closed on that evidence as it was before sideload existed. The
marker is carried through unconditionally into the stored
`docs/publish/sources/web/**/publish_meta.json` and from there into
`publish_manifest.json`'s per-target entry, so which targets bypassed the
pipeline is always auditable from the assembled release, not just from a
local `reports/releases/` snapshot.

Every `web-sideload` run also records one **unconditional** debt-ledger
entry (category `整本未结构化`, payoff action "run
`spec-sheet-structured-intake`, then re-run `web-release`"), through the
same `tools.web_publish.record_debt_entries` ledger `web-release` uses —
regardless of any `--debt` entries also passed. Payoff is mechanical, not a
separate withdrawal step: once real phase2 data exists for the target, an
ordinary `build.py web-release` run for the same model/region/lang writes
the same `latest/web/publish_meta.json` identity, overwriting the sideloaded
metadata with a real pipeline build (and its evidence) in place. From there,
`web-assemble` and `web-receipt` proceed exactly as documented in §2.2.

See [`tools/web_sideload.py`](../../tools/web_sideload.py) for the
implementation, `tests/test_web_sideload.py` for its contract, and
`tests/test_publish_branch_assembly.py`'s `pdf_sideload`/`pipeline`
control-pair tests for the evidence-gate exemption boundary. The full
operator workflow, including PDF extraction guidance, lives in
[`.agents/skills/pdf-web-sideload/SKILL.md`](../../.agents/skills/pdf-web-sideload/SKILL.md).

## 3. Repository and hosting boundaries

- Code changes land only in `Bingboom/auto-manual`, then
  `sync-hello-docs.yml` mirrors the engineering tree into
  `Bingboom/Hello-Docs/main` while preserving the business-owned
  `docs/publish/**` subtree already merged there.
- `Hello-Docs/publish` is a generated release-candidate branch. It is produced
  by the Web Publish workflow or by the same assembler in an isolated Git-only
  checkout. Operators do not edit its generated files by hand, and it is not
  the GitHub repository's development or production branch.
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

The requirements below apply to the queue-driven path only.

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

For the Git-only path, use the evidence contract in section 2.2. Do not create
placeholder online records or write `HTML_link` to imitate queue completion.

## 5. Rollback

Do not force-push `publish`. For the queue-driven path, re-run Web Publish from
the approved review ref and asset rows. For the Git-only path, rebuild from the
recorded source Git ref and release metadata. In either case, append a corrected
candidate snapshot or prepare a `docs/publish/**`-only revert PR into `main`,
verify the generated manifest, merge it, and let the `main` webhook rebuild RTD.
