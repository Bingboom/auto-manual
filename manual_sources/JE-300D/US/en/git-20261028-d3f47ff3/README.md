# JE-300D / US / English — Git-only Web release

Operator instruction: 「继续转 剩下的美规说明书 为单语 网页版 仅选等于Y的 待转」. This package converts the English
single-language manual of the Jackery Explorer 300D (model JE-300D) from the 发布文档管理 Base row `reczz28SlRGJh85k`
(material 38-0001-000960, project HTE150). Route `JE-300D/US/en/md`, `legacy_default` (no US Web edition exists for
this model).

**Status: `operator-approved-git-only-release`.** On 2026-10-29 the operator confirmed 「上线提交发布：JE-300D、JE-500A、JE-600A、JE-1500C」 in the PR #1639 session after reviewing the 1280/390 renders beside the shared reference edition. `source/approval.json` binds that acceptance to these exact source inputs and the IR is publication-eligible. Merge needs a separate operator authorization. Review points are in [`audit/review.zh.md`](audit/review.zh.md).

## Source authority

- `original.pdf`: the row's 「单语言说明书」 English PDF, byte-exact (SHA-256 `d3f47ff3…`, 18 pages, 90 × 130 mm).
  Every glyph is outlined, so the PDF has no text layer.
- Print master (「说明书文件」): `38-0001-000960 HTE150300A-US-JAK 说明书 RoHS REACH.pdf`, one Illustrator artboard
  holding three booklet rows and the title block (V0.1, 第一次发行, 2025-10-11). Name, size and SHA-256 are recorded in
  `source_manifest.json:print_master`; it is not archived here and is not an extraction source.
- Identity (record id, material number, project, SKUs) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

`source/intake.py` holds the English copy, transcribed line by line from 300 dpi renders of the named physical pages
and kept as printed (print markup: bold, subscript, line break). It builds shared flow and shared components only
(`source/kit.py`); `source_manifest.json:component_map` maps every printed block and there are no plain-table
exceptions. Suspected source errors stay as printed and are listed in `source_manifest.json:source_concerns`.
The cover (p1) and contents (p3) are not Web content. The structure reference is the JE-300D EU English Web target
(`manual_sources/JE-300D/EU/en/candidate-2025-10-24`, rendered from `docs/manifests/manual_je300d_eu-en.yaml`).

## Artwork

Inventory first (Web artwork reuse order):

- **Symbols**: all 7 rows reuse a shared symbol byte for byte after the symbol admission's fixed comparison
  (warning `warning/outline-triangle-dark-hte162`, do-not-dismantle `do-not-dismantle/screwdriver-prohibited-dark-hte147`,
  read-manual, no-open-flame, keep-away-from-children, li-ion native-dark, WEEE). No new shared symbol is needed.
- **LCD glyphs**: input/output power and battery-power glyphs reuse the JE-300E US package glyphs (they pass the fixed
  comparison); the other 8 are this print's native vector paths (transparent SVG). The FCC mark reuses the shared
  `fcc_mark.svg`.
- **Panels**: the EU reference art (`docs/renderers/web/assets/je300d_eu_en/`) comes from the EU print (different
  panels and texts), so the 15 figures are cut from `original.pdf` at 4x just inside each print panel frame
  (`source/figures.json`); grey text pills printed inside panels are set as Web text.

## Rebuild

```sh
PKG=manual_sources/JE-300D/US/en/git-20261028-d3f47ff3
python3 "$PKG/source/extract_assets.py"
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output tmp/je300d-us/en
python3 -m sphinx -n -W --keep-going -b html tmp/je300d-us/en tmp/je300d-us-site
```

PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`). To re-freeze: remove `web/en`, rebuild into `web/en`, then run
`source/refresh_manifest.py`.

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; the only Feishu calls
were read-only downloads. No phase2 or print target is registered and no shared renderer, component, contract,
symbol or workflow changed.
