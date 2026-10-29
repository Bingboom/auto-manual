# JE-600A / US / English — Git-only Web candidate

Operator instruction, 2026-10-28: 「继续转 剩下的美规说明书 为单语 网页版 仅选等于Y的 待转」 (发布文档管理 Base,
「是否要转网页文档」=Y and 「是否已转网页版」 unticked). This package converts the English single-language manual of
the Jackery Explorer 600 (model JE-600A, V2) from the row `reczz28SlRGJjY3F` (material 38-0001-000923, project
HTE133). Route `JE-600A/US/en/md`, `legacy_default` (no Web edition exists for this model).

**Status: `review-candidate-no-release-authorization`.** No `source/approval.json`; the IR is not
publication-eligible. Approval is written only after the operator accepts the renders and says 「上线提交发布」.
Review points: [`audit/review.zh.md`](audit/review.zh.md).

## Source authority

- `original.pdf`: the row's 「单语言说明书」 English PDF, byte-exact (SHA-256 `9bf5bbb1…`, 18 pages, 130 × 185 mm).
  Every glyph is outlined, so the PDF has no text layer.
- Print master (「说明书文件」): `38-0001-000923 HTE133600A-US-JAK 说明书A1 RoHS REACH Q.pdf`, one Illustrator
  artboard; name, size and SHA-256 in `source_manifest.json:print_master`. Not archived and not an extraction source.
- Identity (record id, material number, project, SKUs) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

The outlined-PDF method of `manual_sources/JE-300C/US/en/git-20261027-a1128b25` (same Explorer layout family):
`source/intake.py` holds the line-by-line transcription and builds shared flow and shared components only
(`source_manifest.json:component_map`). Two printed tables have no shared component and are declared plain
tables (`shared_component_exceptions`): LCD SCREEN ON/OFF (this print has no artwork, which HB-TABLE-LCD-MODE
requires) and the three-column TROUBLESHOOTING table. Cover (p1) and contents (p3) are not Web content; the back
cover (p18) is the closing contact chapter. Source slips stay as printed (`source_manifest.json:source_concerns`).
Review reference: the same-generation JE-500A EU English Web (`manual_sources/JE-500A/EU/en/2.0`); its EU panels
draw 230 V sockets and another product, so none of its art is reused.

## Artwork

- **Symbols**: 7 rows, each compared with every shared variant of its family by the symbol admission's fixed
  comparison. Five reuse a shared symbol byte for byte (`warning/outline-triangle-tinted`,
  `read-manual/book-information`, `do-not-dismantle/screwdriver-prohibited-tw-477dfbd7`,
  `li-ion/recycle-li-ion-native-dark`, `weee/crossed-bin-bar`). No-open-flame and keep-away-from-children
  reuse `no-open-flame/fire-match-prohibited-dark-5c065d11` and
  `keep-away-from-children/adult-child-prohibited-dark-5c065d11` from the shared-symbol PR #1640 (0.41% / 0.37%).
  All 7 rows reuse shared bytes.
- **LCD glyphs**: 10 of 13 reuse the JE-300C US Web glyphs (fixed comparison against this print); battery
  percentage and the two temperature glyphs are this print's native vector paths. The FCC mark reuses the shared
  `fcc_mark.svg`.
- **Panels**: 17 figures cut from `original.pdf` at 4x just inside each print panel frame (`source/figures.json`).

## Rebuild

```sh
PKG=manual_sources/JE-600A/US/en/git-20261028-9bf5bbb1
python3 "$PKG/source/extract_assets.py"     # about 8 minutes (each page carries the whole artboard)
python3 "$PKG/source/intake.py"
rm -rf "$PKG/web/en" && python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output "$PKG/web/en"
python3 "$PKG/source/refresh_manifest.py"
python3 -m sphinx -n -W --keep-going -b html "$PKG/web/en" tmp/je600a-us-site
```

PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`).

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; the only Feishu
calls were read-only downloads. No phase2 or print target is registered and no shared renderer, component,
contract, symbol library or workflow changed. Release follows the Git-only transaction
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction))
only after the operator accepts the renders and says 「上线提交发布」.
