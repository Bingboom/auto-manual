# Build guide: release outputs and output layout

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

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
- Git-only external Web source: freeze its source/input hash inventory and one real single-language receipt per locale before the same `docs/publish/**` assembly. The existing `build.py check` is a regression gate when the external languages are absent from phase2. For JE-1000F/EU four-language re-intake, use the [native-PDF shared-IR adapter](../dev/four_language_shared_ir_alignment.md): fresh editable PDF text plus exact AI glyph recovery and hash-bound governed assets → `manual-ir/v2` → registered ComponentSpecs and neutral flow → the public Web consumer. Printed Contents and table/panel screenshots are not body content. Diagram labels use declared live-label bindings to stay inside their shared ReferenceFigure panel; they must not fall through as separate body paragraphs. Pending asset bindings block candidate generation; the historical screenshot adapter remains for audit replay only. Verify content parity, strict Sphinx and browser layout before the [Git-only Web transaction](../dev/web_publish_pipeline/input-paths.md#22-git-only-transaction).
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

Review working bundle:

- [`docs/_review/<model>/<region>/`](../../docs/_review)

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
