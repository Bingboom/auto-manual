# Build guide: command reference

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

## 1. Recommended Entrypoint

```powershell
python build.py validate
python build.py sync-data --config configs/config.us.yaml --data-root data/phase2
python -m tools.content_lint --data-root data/phase2 --json --write-report
python -m tools.data.source_intake run --input <spec.md-or-doc-url> --document-key <MODEL_REGION> --source-lang en --data-root data/phase2 --out reports/source_intake/<run-id>
python -m tools.data.source_intake spec-extract --input <spec.pdf> --rules <rules.json> --document-key <MODEL_REGION> --region <REGION> --reference <sibling-spec.json> --out reports/source_intake/<run-id>
python -m tools.data.source_intake stage-plan --spec-candidates reports/source_intake/<run-id>/spec_intake_candidates.json --spec-sibling <sibling-spec.json> --placeholder-sibling <sibling-placeholders.json> --overrides <target-differences.json> --document-key <MODEL_REGION> --localized-lang <lang> --out reports/source_intake/<run-id>
python -m tools.data.source_intake approve --report reports/source_intake/<run-id>/source_intake_source_table_change_request.json --approve <delta_hash> --out reports/source_intake/<run-id>
python -m tools.data.source_intake apply --report reports/source_intake/<run-id>/source_intake_source_table_change_request.json --approval reports/source_intake/<run-id>/source_intake_approval.json --out reports/source_intake/<run-id>
python -m tools.data.source_intake verify --candidates reports/source_intake/<run-id>/source_intake_candidates.json --change-request reports/source_intake/<run-id>/source_intake_source_table_change_request.json --approval reports/source_intake/<run-id>/source_intake_approval.json --apply-report reports/source_intake/<run-id>/source_intake_apply.json --check-command "sync-data=python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --table spec_master" --check-command "build=python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US" --out reports/source_intake/<run-id>
python -m tools.backport.cloud_doc run-review-branch --doc-name <doc name> --cloud-doc <url>
python -m tools.backport.cloud_doc run-review-branch --doc-name <doc name> --cloud-doc <url> --write --push
python -m tools.backport.cloud_doc run-review --doc-url <doc-or-fixture.md> --source-path docs/_review/<model>/<region>/page/<page>.rst --out reports/cloud_doc_backport/<run-id>
python -m tools.backport.cloud_doc open-pr --manifest reports/cloud_doc_backport/<run-id>/cloud_doc_backport_run.json
python -m tools.backport.cloud_doc diff --doc-url <doc-or-fixture.md> --source-path docs/_review/<model>/<region>/page/<page>.rst --doc-type review --out reports/cloud_doc_backport/<run-id>
python -m tools.backport.cloud_doc apply-review --report reports/cloud_doc_backport/<run-id>/cloud_doc_backport_report.json --write --allow-rst-baseline
python -m tools.backport.cloud_doc verify-review --report reports/cloud_doc_backport/<run-id>/cloud_doc_backport_report.json
python -m tools.backport.cloud_doc diff --doc-url <doc-or-fixture.md> --template docs/templates/page_zh/00_preface.rst --doc-type template --out reports/cloud_doc_backport/<run-id>
python -m tools.backport.cloud_doc apply-template --report reports/cloud_doc_backport/<run-id>/cloud_doc_backport_report.json --write
python build.py rst
python build.py review
python scripts\local_build.py check
python build.py asset-check --json
python build.py asset-check --asset-key operation/ac_output --asset-format png --json
python build.py asset-intake --asset-source-key source/manual_je1000f_us_master --asset-source-file '<local-master.ai>' --asset-recipe data/asset_recipes/manual_je1000f_us_master.json --asset-output-root .tmp/asset-intake/manual_je1000f_us_master/run-01
python build.py sync-review
python build.py process-review-start-queue --config configs/config.us.yaml --data-root .tmp/review-start/phase2
python scripts\local_build.py publish --config configs/config.ja.yaml --model JE-1000F --region JP
python scripts\local_build.py release-manifest --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py process-build-queue --config configs/config.us.yaml
python build.py message-control-dry-run --message "publish JE-1000F us-merged from branch feature/review-123"
python build.py handoff --config configs/config.us-en.yaml --model JE-1000F --region US --version V0.1 --baseline docs/_build/JE-1000F/US/en/rst
python build.py preview --config configs/config.ja.yaml --model JE-1000F --region JP --page 03_product_overview_placeholder
python build.py fast --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py html
python build.py word
python build.py pdf
python build.py md
python build.py all
python build.py diff-report
python build.py clean
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word,pdf,md
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --build-action validate --languages en,fr
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html --open-html
```

Local PDF font override:

- for local-only Gilroy preview, set `AUTO_MANUAL_LOCAL_GILROY_DIR=<absolute-font-dir>` before `python build.py pdf ...` or `python build.py publish ...`
- the font directory must contain `gilroy-regular-3.otf`, `gilroy-bold-4.otf`, `Gilroy-LightItalic-12.otf`, and `Gilroy-ExtraBoldItalic-10.otf`
- the helper only patches the generated `_build/latex/fonts.tex` copy for that run; unset the env var to return to the shared fallback chain, and remote CI workers are unaffected

Meaning:

- `validate`: validate config and [`data/layout_params.csv`](../../data/layout_params.csv)
- new-line: Stage 3 scaffold plan or controlled write. The default is
  read-only: resolve one config's inheritance chain, target identity, page
  manifest, and template/recipe references, then print
  new-line-scaffold/v1 with whitelist_diff=0 for the KR/AU replay
  calibration. --write requires explicit --output-config and
  --output-manifest paths inside the repository, refreshes only the
  committed fixture through fixture-refresh, and runs build.py check
  against that fixture. It never writes data/phase2 or Feishu; production
  source-table writes remain the separately approved F6 operation. An
  optional `--asset-override-root docs/_review/<model>/<region>/overrides`
  creates only the controlled `_assets`, `_static`, and `renderers` review
  directories plus a README; it never replaces an existing user override
  unless `--force` is explicit. Use --skip-auto-check only when a caller
  will run the check as a separate gate, and use --plan-output <path> to
  retain the JSON plan/report.
- `python build.py new-line --seed-plan` is the Stage 3 F6 preflight. It is
  read-only and reports three separate actions: create the target
  `02_主数据_Document_key` row if absent, clone `Page_Placeholders_Source`
  rows from an explicitly selected source document, and inspect/create missing
  source-table fields from `phase2_source_tables.json`. It reads only the
  selected local snapshot, never calls Feishu, never writes `data/phase2`, and
  abstains with `needs_input` when the source document is ambiguous. Use
  `--seed-source-document-key <key>` to select the clone source; any actual
  row/field creation remains an approved F6 write operation.

- `rst`: materialize [`docs/_build/<model>/<region>/rst/`](../../docs/_build)
- `review`: seed [`docs/_review/<model>/<region>/`](../../docs/_review) from runtime draft
- `--source review-asis`: render the committed `docs/_review/<model>/<region>/` page bytes without re-deriving them from the build data-root — only the conf/asset skeleton is materialized and the review overlay supplies content. The prepared bundle still enforces the current target language scope: an older merged review index may contain standalone pages for a language the model no longer ships, so out-of-scope pages identified by explicit `\HBApplyLang{...}` declarations are removed from both the generated index and its generated page copies; symlink/escaping page paths are rejected and the original review files stay untouched, and multi-language pages continue through the inline language-block trimmer, including a fully recognized `English / French / ...` scope catalogue. Unlike `--source review` this mode neither pre-syncs review params from data nor runs the Spec_Master identity guard, so it renders a review target whose model is absent from the active data-root (e.g. the CI `Review Preview Package` fixtures under `tests/fixtures/phase2`). The `Review Preview Package` workflow uses this mode, which is why a newly onboarded model (not yet in the fixtures) previews instead of failing the whole package
- With `AUTO_MANUAL_PRESENTATION_PROFILE=web` and an explicit `--lang`, bundle preparation first freezes the complete configured-language RST source under `docs/_build/<model>/<region>/<lang>/web/source/rst/`, including the full shared review overlay, then projects the requested language into canonical `docs/_build/<model>/<region>/<lang>/rst/`. `check`, `md`, and `html` all consume that canonical projection. Web builds without `--lang` and every non-Web build retain their previous source and output paths. This projection is a build input boundary, not evidence that an independent-language publication has been released.
- `check`: run validation + prepare bundle + content checks, including stale identity scan, contract validation, and duplicate RST/raw HTML text consistency checks

- `publish`: run `check -> diff-report -> word -> pdf -> md -> release-manifest` for one explicit target
- `release-manifest`: write JSON / CSV release traceability for one explicit target; when `--version <version>` is present, freeze and bind the phase2 input at the version archive path
- `handoff`: create a minimal explicit target design handoff package with rule-based diff outputs and traceability metadata
- `preview`: materialize one exact page selector under a preview-only output root
- `fast`: materialize a runtime draft only, with `prepare-only + no-clean`
- `html`, `word`, `pdf`, `md`: prepare RST first, then export; Markdown uses a native MyST writer when Pandoc provides one, otherwise a MyST-compatible CommonMark writer
- `all`: export `html + word + pdf + md`
- `diff-report`: export Git-based revision tables, defaulting to the resolved target review root
- `clean`: remove [`docs/_build/`](../../docs/_build), [`docs/_review/`](../../docs/_review), old legacy output directories, and generated [`params.tex`](../../docs/renderers/latex/params.tex)
- `build_us_jp_manuals.ps1`: PowerShell wrapper over the shared Python matrix runner for the fixed `US/en + US/es + US/fr + JP/ja` target set; supports either `--formats` or one explicit `--build-action`
- `--open-html`: after the batch finishes, open the generated HTML entry pages for the selected language set
- DOCX export normalizes image relationships to embedded media before the final style pass so Feishu / other third-party viewers are less likely to hide image-backed table rows in preview

## 5. Typical Commands

Build all targets defined in one config:

```powershell
python build.py rst --config configs/config.us.yaml
python build.py word --config configs/config.us.yaml
python build.py all --config configs/config.ja.yaml
```

Build one explicit target:

```powershell
python build.py word --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py word --config configs/config.eu-en.yaml --model JE-1000F --region EU
python build.py pdf --config configs/config.ja.yaml --model JE-1000F --region JP
```

Word styling note:

- `configs/config.us-en.yaml` now post-processes the generated DOCX so non-safety / non-spec pages inherit the `reference_en.docx` heading, table, and default paragraph styling
- the multi-page bundle HTML remains unchanged as a trace artifact. Immediately
  before Pandoc only, the exporter removes opening and closing `<main ...>`
  wrappers with a bounded tag matcher, preserves their children byte order, and
  deletes the temporary HTML after conversion. This prevents Pandoc from
  selecting an earlier empty `<main></main>` and emitting an empty DOCX; do not
  replace this with DOM reserialization, which can reorder component markup

Single-page preview and fast draft:

```powershell
python build.py preview --config configs/config.us-en.yaml --model JE-1000F --region US --page 03_product_overview_placeholder
python build.py fast --config configs/config.us-en.yaml --model JE-1000F --region US
```

Standalone release traceability:

```powershell
python build.py release-manifest --config configs/config.ja.yaml --model JE-1000F --region JP
```

When `finalize_report.json` is present beside the production IDML, the release
JSON records native `page_count` and the overset-story count under
`indesign_package.preflight`. The release CSV flattens them as
`indesign_preflight_page_count` and
`indesign_preflight_overset_stories`. A blank value means native preflight did
not report that signal; the string `0` means it explicitly reported no overset
stories. Release-manifest generation remains non-blocking when native finalize
has not run.

Keep existing build artifacts:

```powershell
python build.py html --config configs/config.us.yaml --no-clean
```

Open generated artifacts if the backend supports it:

```powershell
python build.py pdf --config configs/config.us.yaml --open
```

Override PDF backend:

```powershell
python build.py pdf --config configs/config.us.yaml --pdf-mode latex
python build.py pdf --config configs/config.us.yaml --pdf-mode word
```

The LaTeX backend keeps presentation in
[components_base.tex](../../docs/renderers/latex/components_base.tex) and
[components_safety.tex](../../docs/renderers/latex/components_safety.tex).
Page RST should call those components and keep content separate from the
visual frame. Fixed-format boundaries use **HBPageBreak**; rounded tables use
an independent outer frame while their tabular content owns only the internal
grid. In LaTeX output, one-row label/body tables whose labels resolve to
WARNING, CAUTION, NOTE, or TIP (including the supported localized labels) are
automatically rendered by the shared rounded callout component; HTML and Word
keep the source table. Tune shared geometry in
[layout_params.csv](../../data/layout_params.csv), then regenerate params.tex
with python -m tools.csv_to_tex_params.

## 6. Diff Report

Typical usage:

```powershell
python build.py diff-report --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py diff-report --config configs/config.ja.yaml --model JE-1000F --region JP --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config configs/config.ja.yaml --tracked-root docs/_review/JE-1000F/JP
python build.py diff-report --config configs/config.ja.yaml --tracked-root docs/_review/JE-1000F/JP --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config configs/config.ja.yaml --tracked-root docs/_review/JE-1000F/JP --include-initial-adds
```

Generated report types:

- `*_files.csv` / `*_files.html`
- `*_pages.csv` / `*_pages.html`
- `*_fields.csv` / `*_fields.html`
- `*_index.html`

The current report defaults are review-oriented, not `_build`-oriented.
If `--tracked-root` is omitted, `build.py` resolves `docs/_review/<model>/<region>/` and `reports/version_tracking/<model>/<region>/` automatically from the target.
Initial baseline Added rows are now hidden by default so the first non-baseline review round is easier to read. Pass `--include-initial-adds` when you need the full initial import noise.
Field pairing now prefers stable source back-mapping before falling back to rendered labels, so placeholder/spec label rewrites are more likely to appear as one `M` row with clearer `old_value/new_value` instead of separate `A/D` rows.
