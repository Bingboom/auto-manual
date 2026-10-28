# JE-1500C / US / English — Git-only Web candidate

Operator instruction, 2026-10-28: 「继续转 剩下的美规说明书 为单语 网页版 仅选等于Y的 待转」.
This package converts the English single-language manual of the Jackery Explorer 1500 Ultra (model JE-1500C)
from the 发布文档管理 Base row `reczz28SlRGJhd6E` (material 38-0001-000936, project HTE118). Route
`JE-1500C/US/en/md`, `legacy_default` (no US Web edition exists for this model).

**Status: `review-candidate-no-release-authorization`.** No `source/approval.json` exists and the IR is not
publication-eligible. Release waits for the operator's 「上线提交发布」 on the 1280/390 renders and a separate
merge authorization. Review points are listed in [`audit/review.zh.md`](audit/review.zh.md).

## Source authority

- `original.pdf`: the row's 「单语言说明书」 English PDF, byte-exact (SHA-256 `46f58108…`, 22 pages,
  130 × 185 mm). Every glyph is outlined, so the PDF has no text layer.
- Print master (「说明书文件」): `38-0001-000936 说明书A1 HTE1181500A-US-JAK RoHS REACH Q.pdf` (59 spread pages,
  264 × 185 mm). Its name, size and SHA-256 are recorded in `source_manifest.json:print_master`; it is neither
  archived here nor used as an extraction source.
- Identity (record id, material number, project, SKUs) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

`source/intake.py` holds the English copy, transcribed line by line from 220-400 dpi renders of the named
physical pages and kept as printed (print markup: bold, line break). It builds shared flow and shared components
only (`source/kit.py`); `source_manifest.json:component_map` maps every printed block, and suspected source errors
are listed in `source_manifest.json:source_concerns` (preserved verbatim). The cover (p1) and contents (p3) are not
Web content. The review reference edition is the released JE-1500C TW Web
(`data/manual_sources/JE-1500C/TW/git-20261010-477dfbd7-reviewed`); its Chinese copy and art are not reused.

## Artwork

Inventory first (Web artwork reuse order):

- **Symbols**: all 11 rows reuse a shared symbol byte for byte (fixed comparison ≤ 2%); no new shared variant
  is needed.
- **LCD glyphs**: 11 of 23 reuse a passing candidate byte for byte (6 from the same-generation JE-1500D US Web,
  5 from the JE-1500C TW Web); the other 12 are this print's native vector paths (the candidates fail the
  comparison or its transparent-margin rule). `source/glyphs.json` records every comparison. The FCC mark reuses
  the shared `fcc_mark.svg`.
- **Panels**: the TW art carries Chinese labels and TW sockets, so the 26 figures are cut from `original.pdf` at 4x
  just inside each print panel frame (`source/figures.json`). Grey text bubbles and pills printed inside a panel
  (`remove_boxes`) are set as shared text panels; only the vector objects wholly inside those boxes are left out
  of the render.

## Rebuild

```sh
PKG=manual_sources/JE-1500C/US/en/git-20261028-46f58108
python3 "$PKG/source/extract_assets.py"
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output tmp/je1500c-us/en
python3 -m sphinx -n -W --keep-going -b html tmp/je1500c-us/en tmp/je1500c-us-site
```

PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`). To re-freeze: remove `web/en`, rebuild into
`web/en`, then run `source/refresh_manifest.py`.

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; the only
Feishu calls were read-only downloads. No phase2 or print target is registered and no shared renderer,
component, contract, symbol or workflow changed. Release follows the Git-only transaction
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction))
only after the operator accepts the renders and says 「上线提交发布」.
