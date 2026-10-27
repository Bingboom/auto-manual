# JS-100I / JP / ja — Git-only manual candidate (Jackery SolarSaga 100 Air)

Operator instruction, 2026-10-26 (coordination session): 「分几个窗口把这个目录下面的文档都转成网页文档」,
then 「韩语文档除外」. This window converts the SolarSaga 100 Air Japanese manual only; the
JE-1000D JP manual and the solar connection-guide leaflet are converted in other windows.
JS-100I already ships a nine-language EU Web edition; this package adds the JP market.

**Status: `operator-approved-git-only-release`.** The operator reviewed the 1280/390 renders
of candidate `1d8250e` and instructed 「全部照录，版式都接受，上线提交发布，保留疑点后续纠正」 on
2026-10-27. `source/approval.json` binds every reviewed `source/` and `assets/` input; the IR is
publication-eligible. The listed source concerns stay verbatim for the source owner to correct.
The engineering PR is merged by the operator (AGENTS.md §8.6), not by an agent grant;
Hello-Docs/RTD publication follows the Git-only transaction below.

## Source authority

- Product: Jackery SolarSaga 100 Air, printed model JS-100I; JP / ja.
- Supplied file: `Jackery SolarSaga 100 Air说明书.pdf` (Feishu wiki node `TC9MwqDAsihTJ0kPlsJcVj4JnNf`, read-only download).
- `source/original.pdf`, byte-exact, 3,403,400 bytes, SHA-256 `cc8b3421221bf11b03f2ddd0ce86519605189fbe0721a7d8a536520d75513e6f`.
- Twelve 130×185 mm portrait pages exported from the Illustrator master (creator「PDF portrait export」).
- No printed manual version, material number or ERP code: `printed_manual_version` stays unknown; the technical snapshot is `git-20261026-cc8b3421`.
- Every glyph is outlined, so there is no text layer. `source/transcription.json` is the line-by-line transcription the Web copy is tested against. Spelling, punctuation and model notation are kept as printed; the questions for the source owner are in `source_manifest.json:source_concerns`.

## Layout

The JP rules of the JA-CK01A-BK / JA-AD500A-SIL packages apply: the cover is not on the Web page and no Japanese wording is edited. The shared reference edition is the JS-100I EU en Web (structure, components, artwork; no facts). Every printed block maps to a shared component (`source_manifest.json:component_map`); the one plain table (電気データ, three columns with spans) is declared in `shared_component_exceptions`. `source/differences.md` lists each deliberate layout difference; `source/presentation.css` is geometry and typography only.

The PDF prints no symbol table, so no symbol admission applies.

## Artwork

`source/discovery.md` records the inventory before extraction. Eleven figures whose drawing matches the published JS-100I EU Web art are byte-identical copies (`source/asset_decisions.json` records source path and SHA-256; the target test re-checks the bytes). Twelve JP-specific figures (Japanese power-station models, this manual's cover, figures whose EU art bakes English labels, the QR code) are cropped by `derive_assets.py` through the shared asset pipeline. Labels on those figures are native text placed on the source coordinates (`source/figure_labels.json`): `whiteout` clears outlined glyphs on the white page; on the grey print panels `copy_pdf_region` repaints glyphs and note bubbles with a measured blank square of the same panel.

## Rebuild

From the repository root (`requirements.lock`, Python 3.12, PyMuPDF 1.28.0 / MuPDF 1.29.0, Pandoc 3.9.0.2):

```sh
PKG=manual_sources/JS-100I/JP/ja/git-20261026-cc8b3421
python "$PKG/derive_assets.py"
python "$PKG/refresh_manifest.py" inputs
python "$PKG/render.py" tmp/js100i-jp
python -m sphinx -n -W --keep-going -b html tmp/js100i-jp tmp/js100i-jp-html
python -m unittest tests.test_js100i_jp_web
```

Replace `web/ja` with a fresh render after any source change, then run `refresh_manifest.py frozen`. `render.py` checks every input hash, runs the existing prepared RST → manual-ir/v2 → shared Web/MyST pipeline, checks the component counts, carries `source/presentation.css` as the IR source stylesheet and enforces the prepared-document shared-style gate. The JE-1000F JP `build.py check` is a repository regression gate only; it does not validate this body (no phase2 target is registered).

## Release boundary

After the operator's release instruction and the engineering PR merge, the Git-only transaction continues per [web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction): seal at the merged `main` commit, assemble from Hello-Docs `main`, open a `docs/publish/**`-only PR, then verify RTD.

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows, dependencies and the JS-100I EU packages (read-only reuse).
