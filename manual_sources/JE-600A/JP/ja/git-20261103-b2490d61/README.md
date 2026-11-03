# JE-600A / JP / Japanese — Git-only Web candidate

Operator instruction, 2026-11-03 (relayed by the coordinating window): 「继续 转日语说明书」 — convert the 24
Japanese single-language manuals in the 发布文档管理 Base 日规 view that have a customer model and a
single-language PDF and no Web edition yet. This package converts the Japanese manual of the Jackery
ポータブル電源 600 New (model JE-600A) from the row `reczz28SfbsHdOvR` (material 38-0001-000959, project
HTE133, SKU 21-0001-000323 / 21-0014-000280). Route `JE-600A/JP/ja/md`, `legacy_default` (no Japanese Web
edition exists for this model).

**Status: `review-candidate-no-release-authorization`.** No `source/approval.json`; the IR is not
publication-eligible until the operator reviews the 1280/390 renders beside the reference editions and says
「上线提交发布」 in this package's PR session. Review points are in [`audit/review.zh.md`](audit/review.zh.md).

## Source authority

- `original.pdf`: the row's 「单语言说明书」 Japanese PDF, byte-exact (SHA-256 `b2490d61…`, 20 pages,
  129 × 185 mm). Every glyph is outlined, so the PDF has no text layer.
- Print master (「说明书文件」): `38-0001-000959 HTE133600A-JP-JAK 说明书 RoHS REACH-Q.pdf` (multi-artboard
  Illustrator PDF); name, size and SHA-256 in `source_manifest.json:print_master`. Not archived and not an
  extraction source.
- Identity (record id, material number, project, SKU) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

The Explorer outlined-PDF kit (`manual_sources/JE-600A/US/en/git-20261028-9bf5bbb1`), adapted for Japanese
(template: `manual_sources/JE-600C-SJ/JP/ja/git-20261103-3837e9fd`): `source/intake.py` holds the two-pass
line-by-line transcription (300–400 dpi renders) and binds every printed block, in printed order, to shared
flow or a shared component (`source_manifest.json:component_map`). The 液晶画面 table is the shared
numbered LCD icon catalog, the F0–F9 table the shared two-column troubleshooting table, the 保証について
chapter the shared warranty cards with grey `hb-text-panel` lead, 免責事項 and contact panels (JE-1000D JP
form). Two printed tables have no shared component and are declared plain tables
(`shared_component_exceptions`): the 充電式電池のリサイクルについて notice beside its Li-ion 32 mark and the
three-column LCDディスプレイ on/off table (JE-600A US precedent).

Pages: the cover (p1) and contents page (p2) are not Web content. The back cover (p20) carries only an
undecoded QR code with no caption or contact text, so it is left out (`excluded_pages.back_cover_qr_only`);
the print's contact pills (web / e-mail / phone, p19) stay at the end of the 保証について chapter.
Japanese copy is unchanged; suspected source errors stay as printed and are listed in
`source_manifest.json:source_concerns`. Review references: JE-600A US English Web
(`manual_sources/JE-600A/US/en/git-20261028-9bf5bbb1`, same model) and JE-1000D JP Web
(`manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2`, same family).

## Artwork

- **Inventory first**: the same model's US English Web edition exists. Its LCD glyphs are reused where the
  fixed comparison passes; its panels carry English words and are **not** reused — this print's panels have
  Japanese labels (オン / オフ / 1回押す, 取り外す, 車, Japanese 2-pin outlets) and are cut from this PDF.
- **LCD glyphs**: 13 rows. Ten reuse released glyphs byte for byte — UPS, AC power, input/output power, AC
  wall / car / solar charging, battery ring, fault code and energy saving (6H) from JE-600A US; high/low
  temperature from JE-300C US (the JE-600A US copies are that print's native paths and do not pass). The
  battery-percentage glyph (no released glyph passes; candidate has an opaque backdrop) and the Li-ion 32
  recycling mark (JE-600C-SJ JP / JE-1000D JP marks do not pass) are this print's native vector paths.
- **Symbols**: 6 rows (絵表示の説明), each compared with every shared variant by the symbol admission's
  fixed comparison. One reuses shared bytes (`mandatory/h1-jp-native`). Five (unplug, no disassembly, no
  wet hands, keep dry, prohibition) pass no shared variant: this print draws them on a light-grey filled
  disc the size of the ring (the unplug mark as a stroked ring over a dark disc), so the glyph background
  differs. They stay as pending native candidates and were reported to the coordinating window for the batch
  shared-symbol PR — release admission refuses them until the shared library carries them.
- **Panels**: 17 figures cut from `original.pdf` at 4x (`source/figures.json`), labels kept in the art and
  the alt text. Masks: the ● 右側面 heading inside the right-side panel rectangle, and the UPS speech bubble
  (its text is set as a shared text panel below the figure).

## Rebuild

```sh
PKG=manual_sources/JE-600A/JP/ja/git-20261103-b2490d61
python3 "$PKG/source/extract_assets.py"     # about 2.5 minutes (each page carries the whole artboard)
python3 "$PKG/source/intake.py"
rm -rf "$PKG/web" && python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output "$PKG/web/ja"
python3 "$PKG/source/refresh_manifest.py"
python3 -m sphinx -n -W --keep-going -b html "$PKG/web/ja" tmp/je600a-jp-site
```

PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`).

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; the only Feishu
calls were read-only downloads. No phase2 or print target is registered and no shared renderer, component,
contract, symbol library or workflow changed. Release follows the Git-only transaction
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction))
only after the operator accepts the renders and says 「上线提交发布」.
