# JSG-2404A / JP / ja — material38-0001-000491

Review candidate of **Jackery Solar Generator 240 40W Mini** from the current Feishu【竖版说明书】attachment. Source identity and the20physical pages are bound by SHA-256 in `source_manifest.json`. Publication/content/pixel approval remains pending.

The included station is JE-240A; the bundle also contains SolarSaga40Mini (JS-40A). Every substantive cover/body/back-cover page is represented. Original blank pages2–3, logos, duplicate cover artwork/title and print folios are omitted. The package preserves this bundle’s own specifications, wording and source concerns; another JS-40A version does not override them.

Run from the repository root with the repository Python environment:

```sh
python manual_sources/JSG-2404A/JP/ja/git-20261112-e59cc1bc-m000491/prepare.py
python manual_sources/JSG-2404A/JP/ja/git-20261112-e59cc1bc-m000491/render.py --output /tmp/jsg-2404a-jp-replay
python -m sphinx -b html -n -W --keep-going /tmp/jsg-2404a-jp-replay /tmp/jsg-2404a-jp-html
```

`render.py` checks the original PDF and every frozen source/repository input before creating ManualIR, shared components/theme and replayable MyST. It additionally enforces the prepared-document shared-style gate and reconstructs all6symbol references from this package’s actual source page13. It fails on input drift. `refresh.py` is only for intentionally reviewed source changes, before revalidation; do not refresh historical packages to bypass their pins.

The checked-in `web/ja` is the frozen replay result, not an editable source. Body text and tables are semantic. Shared artwork is copied byte-for-byte; selected assets are local, so replay does not require the unselected000348 package or any live Base. The first4 unfolding illustrations’ true donor000348 and the matching selected000464 copy are recorded, without claiming operator approval. New bundle-specific panels are reproducible with `tools/asset_intake.py` and `source/asset_recipe.json`; all remain quarantined candidates.

Evidence:

- `source/page_review.json`: every physical page, omission decision, source render/OCR hashes and destination.
- `source/paragraph_review.json`: every native flow block, exact source page span and component text slots.
- `source/parameter_review.json`: every specification row plus body numeric checks.
- `source/reference_differences.json`: rejected older single-station additions and current bundle choices.
- `source/asset_decisions.json`, `source/figures.json`, `source/symbols.json`: actual selected bytes, complete figure geometry and current-PDF symbol provenance.
- `source/ocr/`: raw350dpi Japanese OCR drafts, explicitly not copy authority.
- `evidence/validation.json`: strict compile, cold replay and1280/390browser verification; reference comparison is assembled by the root batch review.

Source concerns stay visible in `source_manifest.json`; fixes require a separate explicit source decision. No phase2model config, shared asset library, live table, publication route or approval record is changed by this candidate.
