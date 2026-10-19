# JA-AD500A-SIL / JP / ja — solar-Voc correction edition

Operator instruction, 2026-10-15/16: replace the solar-panel Voc paragraph so it cites the Jackery DC Input Module's DC input voltage range (16V～60V) instead of the downstream SlimPower H1 / Battery Pack ranges (“整段替换”), keeping the disclaimer (“不删免责句”); on 2026-10-16 the operator dropped the opening accessory warning, which contradicted the recommendation and the disclaimer (“删掉第①句”).
This edition applies that correction to the live [Web-layout edition](../git-20261009-ac3a1f82-web-layout/README.md) of the approved package (MA-272). The base edition, its printed source and its release evidence remain immutable.

**Status: `operator-approved-git-only-release`.** Accepted by the operator on 2026-10-16 (「全部验收并发布上线」; 「验收记录 允许你写」, MA-312): `source/approval.json` binds every reviewed `source/` and `assets/` input, and the IR is publication-eligible. Release is the Git-only Web Publish sealed at the merged `main` commit.

## What changed

- **Copy:** the first two sentences of one paragraph in `source/page/charging_ja.rst`; see `source/differences.md`. The rendered visible copy is the base edition's copy with exactly that paragraph replaced (`tests/test_jp_solar_voc.py`). `source/native_pages.json` and `source/original.pdf` keep the printed wording.
- **Shared styles:** the re-frozen locale must pass the prepared-document shared-style gate (`tools/web/prepared_style_audit.py`), which the base edition predates (it stays in `prepared_style_baseline.json`). On operator instruction (“889 日规 也要删掉第一句”, accepting the style fixes) `derive_solar_voc.py` (`STYLE_EDITS`, `STYLE_BLOCKS`, `PRESENTATION_CSS`) replaces the base's page-local styles with shared theme classes; no copy changes:
  - `jpad-welcome-lead`, `jpad-tight`, `jpad-hang` dropped (plain flow); `jpad-small` → `manual-spec-note`; the grey `jpad-panel` → shared `hb-text-panel`.
  - Product overview: the inline-styled width wrapper moved to a geometry rule on the figure.
  - LED table: inline-styled raw HTML → a list table on the shared `hb-source-status` / `hb-source-status-table` classes, declared in `source_manifest.json` → `shared_component_exceptions` (no shared LED-state component exists).
  - Contact lines: source `hb-manual-page-end` capsules → one shared `hb-text-panel`; the QR size moved to a geometry rule.
  - `source/presentation.css` is geometry and typography only: the base's backgrounds, borders, radii and colours (warranty note capsules, joined warranty intro panel, 免責事項 panel, contact capsules) are gone, so those blocks take the shared look.

Every other copied `source/` and `assets/` file is a byte-for-byte copy of the base edition.

## Reconstruction

```sh
PKG=manual_sources/JA-AD500A-SIL/JP/ja/git-20261016-ac3a1f82-solar-voc
python "$PKG/derive_solar_voc.py"
python "$PKG/render.py" tmp/jaad500a-jp-voc
python -m sphinx -n -W --keep-going -b html tmp/jaad500a-jp-voc tmp/jaad500a-jp-voc-html
python -m unittest tests.test_jp_solar_voc
```

Replace `web/ja` with a fresh render after any source change, then re-run the derivation.
