# JE-240A JP Japanese — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SfbsHdX6k` (子物料编码 38-0001-000445, 项目号 HTE110, SKU 21-0001-000215, 日规),
  field 单语言说明书 「【Jackery ポータブル電源 240】说明书-JP.pdf」, read-only bot download; 3,448,108 bytes,
  SHA-256 `e227d165efcd389a260bb1b3f1a234c365c81465c01492c7e86d674afd8af2cf` (stored as `JE-240A-JP-JA.pdf`).
- 14 pages, 130 × 185 mm ("Manual portrait export"); no text layer (all copy outlined).
  p1 cover (V2, thank-you notes, support e-mail, QR), p2–p14 printed 1–13. No paper TOC and no back cover.
- Field 说明书文件: print master 「38-0001-000445 说明书 HTE110256A-JP-JAK RoHS REACH 0314 Q.pdf」, 11,213,268 bytes,
  SHA-256 `d670c612a9f798ab196c5edb89348aef944a06abc7a4fbee030136db3329d6f4`. Recorded only; not an extraction source.
- The shared native-SVG selector maps this export's path stream (unlike the US export), so symbols and the
  Li-ion mark use original vector paths. The 88H glyph is the exception: its native export renders the H as a solid block.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `manual_sources/JE-240A/US/en/git-20261027-ae3aea4b/assets/` (same model) | every panel and LCD icon, side by side |
| `manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/assets/` (same JP template generation) | LCD vectors, Li-ion 32 mark, symbols (admission metric) |
| `manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed/web/ja/assets/shared-lcd/` | battery ring, F8 |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (all variants incl. #1632/#1640/#1641) | the six 絵表示の説明 symbols at the fixed 2% admission |
| `docs/renderers/web/assets/shared/lcd/`, `shared/buttons/` | no matching slot (no key-combination table) |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| battery ring, F8 | reuse JE-1000F JP shared-lcd bytes | same glyphs (as JE-240A US, JE-1000D JP) | transparent |
| 88H energy saving | reuse JE-240A US bytes | same-model glyph; native export unusable, JE-1000D 88H differs | transparent |
| low battery, high / low temperature | reuse JE-1000D JP native vectors | ≤1.2% admission-metric error against the JP paths | transparent |
| Li-ion 32 recycling mark | new native vector | JE-1000D mark sets the label bold | transparent |
| six 絵表示の説明 symbols | reuse shared variants (`native/je1000d-jp-00c43a89-01/02/03/05/06`, `mandatory/h1-jp-native`) | pass the fixed 2% admission | transparent |
| overview, LCD map, AC / solar / car charging, four in-box cards, App badges, App screenshots, App button map | new complete crops at 3× | Japanese labels or captions, JP-only cards, different badge crop; the LCD map is the same art as US but not byte-identical | complete panel; App phone frames kept; in-box ordinals cropped out |

No new shared symbol is needed. No body text or table is an image: all copy is native HTML from `transcription.json`.
