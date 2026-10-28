# JE-500A / US / English — Git-only Web candidate

Operator instruction, 2026-10-28: 「继续转 剩下的美规说明书 为单语 网页版 仅选等于Y的 待转」.
This package converts the English single-language manual of the Jackery Explorer 500 (model JE-500A)
from the 发布文档管理 Base row `reczz28SlRGJjcks` (material 38-0001-000918, project HTE132). Route
`JE-500A/US/en/md`, `legacy_default` (no US Web edition exists for this model).

**Status: `review-candidate-no-release-authorization`.** No operator acceptance is recorded: there is no
`source/approval.json` and the IR is not publication-eligible. Two symbol rows wait for shared variants
(see Artwork). The default layout decisions are listed in [`audit/review.zh.md`](audit/review.zh.md).

## Source authority

- `original.pdf`: the row's 「单语言说明书」 English PDF, byte-exact (SHA-256 `5c065d11…`, 18 pages,
  130 × 185 mm). Every glyph is outlined, so the PDF has no text layer.
- Print master (「说明书文件」): `38-0001-000918 HTE132500A-US-JAK 说明书 RoHS REACH Q.pdf`, one Illustrator
  artboard. Its name, size and SHA-256 are recorded in `source_manifest.json:print_master`; it is not
  archived here and is not an extraction source.
- Identity (record id, material number, project, SKUs) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

`source/intake.py` holds the English copy, transcribed line by line from 300 dpi renders of the named
physical pages and kept as printed (print markup: bold, subscript, line break). It builds shared flow and
shared components only (`source/kit.py`); `source_manifest.json:component_map` maps every printed block.
Two printed tables have no fitting shared component and stay plain shared tables, declared with their
reason in `shared_component_exceptions`: the LCD SCREEN ON/OFF table (the print has no drawing, and
HB-TABLE-LCD-MODE requires one) and the three-column fault table (HB-TABLE-TROUBLESHOOTING is code +
corrective measures). Suspected source errors are kept verbatim and listed in
`source_manifest.json:source_concerns`. The cover (p1) and contents (p3) are not Web content.

Reference editions: the JE-500A EU English Web edition (`manual_sources/JE-500A/EU/en/2.0`, review
reference shown beside this one) and the released JE-300C US English package (same print family).

## Artwork

- **Symbols** (7 rows, fixed 2% comparison against every shared variant of the family): warning,
  read-manual, do-not-dismantle (`screwdriver-prohibited-tw-477dfbd7`), Li-ion (`recycle-li-ion-native-dark`)
  and WEEE reuse shared bytes. **No shared variant passes for no-open-flame (closest 2.52%) and
  keep-away-from-children (closest 2.33%)**; their native paths are kept as
  `*-native-candidate.svg` and the release admission refuses them until the shared library carries a
  variant (raised with the operator; not added here).
- **LCD glyphs**: 10 of 13 reuse the JE-300C US glyphs, which pass the fixed comparison against this print;
  battery percentage and high/low temperature are this print's native vector paths. The FCC mark reuses
  the shared `fcc_mark.svg`.
- **Panels**: the EU edition draws 230 V sockets, so the 17 figures are cut from `original.pdf` at 4x
  just inside each print panel frame (`source/figures.json`).

## Rebuild

```sh
PKG=manual_sources/JE-500A/US/en/git-20261028-5c065d11
python3 "$PKG/source/extract_assets.py"   # about 10 minutes (each page carries the whole artboard)
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output tmp/je500a-us/en
python3 -m sphinx -n -W --keep-going -b html tmp/je500a-us/en tmp/je500a-us-site
```

PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`). To re-freeze: remove `web/en`, rebuild into
`web/en`, then run `source/refresh_manifest.py`.

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; the only
Feishu calls were read-only downloads. No phase2 or print target is registered and no shared renderer,
component, contract, symbol library or workflow changed. Release follows the Git-only transaction
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction))
only after the operator accepts the renders and says 「上线提交发布」.
