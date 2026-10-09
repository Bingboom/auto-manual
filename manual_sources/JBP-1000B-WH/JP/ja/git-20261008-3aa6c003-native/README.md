# JBP-1000B-WH / JP / ja — native PDF Web review candidate

This Git-only package converts the supplied Japanese Battery Pack manual through existing `manual-ir/v2`, prepared-document admission, registered ComponentSpecs and shared Web replay. The operator accepted the reviewed candidate and authorized public Git-only submission and release on 2026-10-08 (“上线提交发布”), recorded under MA-275. Asset registry promotion is excluded. The remote repository is public; a draft PR exposes its text, illustrations and provenance. No phase2 target, Base, queue, attachment, HTML_link or asset-registry record was written.

## Source identity

- Original: `Jackery Battery Pack取扱説明書V2.0-2026-07-29.pdf`
- SHA-256: `3aa6c0039b413716274089e5335dc2ce5853264dca4d7b0a6e5e110b6b0b302c`
- Actual target: **JBP-1000B-WH / Japan / Japanese**. This is a SlimPower H1 companion pack; historical JBP-2000B/2000 Plus content is unsuitable.
- 20 physical pages: cover 1, print TOC 2, body 3–19 (printed 01–17), blank 20.
- `V2.0-2026-07-29` is a filename version; it is not printed in the PDF body.

## Editing and reconstruction

`source/document.json` is the editable semantic source: native Japanese copy, chapter/page attribution and shared ComponentSpecs. `source/admission.json` independently records source-derived chapter/component applicability; do not relax it to accommodate missing content. `source/figures.json` records native panel bounds, caption geometry and exact art hashes. `source/asset_recipe.json` and `source/native_icon_recipe.json` explain offline acquisition; all artwork remains an unpromoted candidate. `source/reuse.json` records byte-identical reuse and concrete glyph exceptions. `source/differences.md` records visible-source decisions and operator questions.

Run from the repository root, using the repository Python environment:

```sh
python manual_sources/JBP-1000B-WH/JP/ja/git-20261008-3aa6c003-native/rebuild.py --output tmp/jbp1000b-jp-web
python -m sphinx -n -W --keep-going -b html tmp/jbp1000b-jp-web tmp/jbp1000b-jp-html
python -m http.server 8896 --bind 127.0.0.1 --directory tmp/jbp1000b-jp-html
```

Open `http://127.0.0.1:8896/manual_jbp1000bwh_jp_ja.html`. Each reconstruction requires a new output directory and needs neither the PDF nor live data. Inputs are checked against `source_manifest.json` before any output is written. After an intentional reviewed source change, refresh only the changed `inputs` entries with the new byte size and SHA-256, reconstruct to a fresh directory, run admission/strict Sphinx/tests, then replace the frozen `web/ja` package with that candidate. Source-local presentation also makes LCD and troubleshooting tables fit the mobile viewport without horizontal panning; numeric LCD labels stay on the drawing. The frozen package includes IR, MyST, CSS, scaffold and assets; generated HTML is local only.

To replay the committed package offline without re-extracting:

```sh
python -c 'from pathlib import Path; from tools.web.frozen_ai_web import replay_package; replay_package(Path("manual_sources/JBP-1000B-WH/JP/ja/git-20261008-3aa6c003-native/web/ja"))'
```

The original PDF is retained unchanged for source-bound symbol admission during release sealing; cold reconstruction still requires no PDF. `source_manifest.json` inventories construction inputs. The release-side `frozen_source_manifest.json` inventories a projection of tracked files, including actual Web files and evidence, and is bound to the real source Git commit by the shared release sealer. Its two explicit `release_excluded_files` are Web-directory audit reports: their unchanged bytes are retained as `evidence/web-*` files. Keep those audit sidecars outside the sealed Markdown directory because the existing assembler copies only Web scaffold, IR, HTML carrier, assets and CSS. The committed cold-rebuild package retains its reports; only the isolated release projection omits them.

The source-local `rebuild.py` is the ordinary maintenance entrypoint for this package. It calls shared components and admission rather than introducing a renderer, shared configuration or model-specific pipeline branch.

## Validation and release boundary

The native package has 17 source-derived chapters and zero declared legacy debt. Its source-local policy excludes absent UPS, App, automatic-resume and button-combination content; a portable-host applicability registry would fabricate chapters. The JP `JE-1000F` `build.py check` is a shared regression check only; it does not register or validate this target's native content. See `evidence/validation.json` and `evidence/browser-acceptance.json` for exact commands and viewport results.

Operator acceptance is hash-bound in `source/approval.json`; reconstruction rejects changes to any reviewed source input even after its manifest hash is refreshed. The approved frozen IR sets `publication_eligible=true` and clears `pending_source_review`; native technical questions remain recorded without rewriting. Engineering and generated Hello-Docs release PRs each require all checks green under MA-275. Original candidate evidence is retained in `evidence/validation.json`; current release validation and environment recovery are recorded separately. RTD deployment and browser acceptance require their own final evidence. No asset registry promotion or live business-plane write is included.
