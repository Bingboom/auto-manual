# Build guide: review preview, release outputs and output layout

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

### 3.6 Package a Review Preview for Design

Use this when design needs the rendered review HTML plus the current family-level diff package:

```powershell
python -m tools.process_docs.build_review_preview --config configs/config.us-en.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD --all-review-models
```

Config note:

- omit `--config` to resolve the config from the explicit `--model` / `--region` target declaration; omitting `--model` and `--region` as well derives the default target from the changed review bundle, then from the existing review tree
- keep `--config configs/config.us-en.yaml` when you want the packaged workspace to open on the explicit US English single-language target by default
- the Vercel review-preview fallback scans the registered `configs/config*.yaml` files for those family defaults and uses the first registered target only when neither environment variables nor a review-tree target is available

Default packaged output:

- [`../site/review-preview/dist/`](../../site/review-preview/dist)

This package contains:

- `index.html`: the workspace root for family/model/language navigation
- `manual/`: review-based HTML, grouped by family, model, and language
- `changes/`: family hubs plus model-level diff pages at `changes/<family>/<model>/`
- `downloads/`: model-scoped `review-manual.docx`, `change-report.xlsx`, and copied diff-report CSV files
- `generated/meta.json`: branch / commit metadata
- `generated/changes.json`: grouped changed files, review pages, and download metadata
- `generated/workspace.json`: the workspace data contract used by the root page
- `manual/index.html`: compatibility redirect to the default manual
- `changes/index.html`: family selector that links the packaged `US / JP` diff pages instead of dropping reviewers into one default family report

Packaging rule:

- the review preview output contract is `index.html`, `manual/`, `changes/`, `downloads/`, and `generated/`
- CI treats `index.html`, `manual/`, `changes/`, and `generated/` as the required smoke-packaging surface
- `--skip-word` is now used by the CI smoke workflow so review-preview packaging can stay stable without requiring the heavier Word path on every run
- the workspace hides families with no `_review` content, so the packaged site only shows available families
- with `--all-review-models`, the packaged site includes every existing review model and keeps the requested target as the default landing entry
- diff, workbook, and CSV outputs stay shared inside one `family + model` package, not per-language artifacts
- the default change entry in the packaged workspace now opens the selected model diff page, while `changes/index.html` and `changes/<family>/index.html` stay available as hubs

### 3.7 Publish a Final Word Release

```powershell
python build.py publish --config configs/config.ja.yaml --model JE-1000F --region JP
```

This is the formal release command.
It requires an explicit `--model` and `--region`.

Outputs:

- direct `build.py publish`: review diff report plus final build outputs under [`../docs/_build/`](../../docs/_build) by default, or under `<staging-root>/docs/_build/` when staging is enabled
- queue-driven print Publish: staged DOCX/PDF/Markdown under [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../../reports/releases), with Markdown sidecars such as `assets/`, `conf.py`, and `index.md` preserved when present
- queue-driven Web Publish: staged MyST plus verification HTML under `reports/releases/<model>/<region>/<lang>/versions/<version>/web/`, then frozen Sphinx candidate under `Hello-Docs/publish:docs/publish/` and a scope-guarded PR into `Hello-Docs/main`
- Git-only external Web source: freeze its source/input hash inventory and one real single-language receipt per locale before the same `docs/publish/**` assembly. The existing `build.py check` is a regression gate when the external languages are absent from phase2. For JE-1000F/EU four-language re-intake, use the [native-PDF shared-IR adapter](../dev/four_language_shared_ir_alignment.md): fresh editable PDF text plus exact AI glyph recovery and hash-bound governed assets → `manual-ir/v2` → registered ComponentSpecs and neutral flow → the public Web consumer. Printed Contents and table/panel screenshots are not body content. Diagram labels use declared live-label bindings to stay inside their shared ReferenceFigure panel; they must not fall through as separate body paragraphs. Pending asset bindings block candidate generation; the historical screenshot adapter remains for audit replay only. Verify content parity, strict Sphinx and browser layout before the [Git-only Web transaction](../dev/web_publish_pipeline.md#22-git-only-transaction).
  A reviewed source with a different native chapter map uses SHA-bound `source_profiles` in the committed prepared-component admission contract. Historical phase2 mappings stay intact; the source profile does not waive source, shared-asset, strict-build or browser acceptance. See the [JE-3600A nine-language review](../reviews/je3600a_eu_nine_language_web_2026-10.md).
- JE-2000F/EU and JE-2000E/EU native intake use the same pipeline with [hash-pinned target geometry](../dev/je2000_eu_new_locales_ir_adapters_2026-09.md). A preview may carry pending source decisions, but release evidence refuses an adjacent `manual.ir.json` with `publication_eligible: false` or nonempty `pending_source_review`; resolve and record the source decisions before rebuilding a publishable package. Reused prefaces require dated operator approval on both the pinned binding and every paragraph before the review banner and pending marker can be removed. Operation diagrams use their own hash-bound crop coordinates and the existing live-copy art canvas; verify leader alignment and complete illustration boundaries for each target. Charging diagrams must also inherit the reference live-label bindings: captions are consumed once, and note pills are HTML/CSS over artwork without baked text or white pills. This shared presentation is available to other portable power stations while device/interface art remains model-bound.
- Native PDF figure bindings may select `native_captions: true` when one PDF text block combines several spatial labels. The adapter rereads the hash-pinned caption rectangles from the declared physical page, rejects empty/duplicate/out-of-figure labels and artwork hash drift, and passes each label once to the existing ReferenceFigure live-copy renderer. It cannot be combined with exact-string `live_labels`. Merged safety notices recognize a known label at either end of a native block; the body remains one shared callout. JE-3000C/EU pt/nl/pl use this path; their source decisions and validation are in the [intake report](../../reports/je3000c-eu-three-language/README.md).
- release manifest: [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../../reports/releases) by default, or `<staging-root>/reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv` when staging is enabled

## 4. Output Layout

Runtime outputs:

- default: [`docs/_build/<model>/<region>/rst/`](../../docs/_build), [`docs/_build/<model>/<region>/preview/<page>/rst/`](../../docs/_build), [`docs/_build/<model>/<region>/html/`](../../docs/_build), [`docs/_build/<model>/<region>/word/`](../../docs/_build), [`docs/_build/<model>/<region>/pdf/`](../../docs/_build)
- staged verification/local queue runs: `<staging-root>/docs/_build/<model>/<region>/...`
- each prepared `rst/` bundle root contains `asset_usage_manifest.json`, `asset_registry_snapshot.csv`, and finalized `bundle_manifest.json`; `bundle_manifest.json.bundle_sha256` fingerprints the final RST include closure, configuration, support trees, and the two asset sidecars

HTML output starts at the first manual content section. Generated cover pages are preserved for PDF/LaTeX output, not rendered as a standalone HTML home screen.
In manual preview mode, the HTML view also suppresses most Furo navigation chrome, stays in a continuous reading flow instead of browser-side fake pagination, regenerates a lightweight left outline from manual headings, and applies a restrained neutral manual-reader treatment to generic headings, copy width, figures, ordinary docutils tables, and the multilingual preface notice while preserving dedicated component layouts such as `SPECIFICATIONS`.
For review-preview workspace packaging, the manual pages now reuse the same manual HTML/CSS/JS treatment as the local build, including the generated heading sidebar and the same no-top-switcher layout.

Review working bundle:

- [`docs/_review/<model>/<region>/`](../../docs/_review)

Review handoff workspace:

- [`../site/review-preview/dist/`](../../site/review-preview/dist)

Latest publish HTML site:

- [`../site/publish-latest/dist/`](../../site/publish-latest/dist)

Read the Docs bundle source for the generated public catalog:

- [`../docs/_build/rtd/`](../../docs/_build)
- per-manual entries under `../docs/_build/rtd/<model>/<region>/md/`

Revision reports:

- default: [`reports/version_tracking/<model>/<region>/`](../../reports/version_tracking)
- staged verification/local queue runs: `<staging-root>/reports/version_tracking/<model>/<region>/`

Release manifests:

- default: [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../../reports/releases)
- staged verification/local queue runs: `<staging-root>/reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`
