# JE-1000H EU: shared symbol glyphs in nine languages

Status: active

## Request and scope (2026-10-26)

The operator marked four JE-1000H icons in the per-model symbol comparison:
「这个 JE-1000H的图标 改成共用图标」, then decided 「nl/pl/pt 也改，模板路径从 main 重建」.
In scope: read manual, do not dismantle, no open flame, keep away from children.
Warning triangle, Li-ion and WEEE are out of scope and unchanged. No copy changes.

## Where each language's icons came from

| Languages | Published build | Four icons before | Finding |
| --- | --- | --- | --- |
| en, es, fr, uk | `git-20260930-4e7df369-lcd-icons` (template route) | Template defaults `docs/templates/word_template/common_assets/symbols/{read_manual_operator,do_not_dismantle,no_open_flame,keep_away_from_children}.png`, because `image_path` was empty | Three carry an opaque gray backdrop and fail the transparency check; the screwdriver is a different template drawing. Not the shared library. |
| de, it | `git-20261010-6d851884-1465-lcd` (template route) | Same template defaults | Same as above. |
| nl, pl, pt | frozen `git-20261001-8bcb378f-temperature-web` | Native transparent PNG crops of HTE159 p.111/128/145 | Transparent, but not the shared library. |

No language already used the shared variants, so all nine change.

## Artwork reuse decisions (§3 web-artwork reuse order)

| Slot | Checked | Identity | Decision | New extraction | Final source and hash | Background |
| --- | --- | --- | --- | --- | --- | --- |
| read manual | `shared/symbols/manifest.json` read-manual variants; template PNG; package crops | Book with “i”; tint (68,67,69) equals the native crop | Reuse `read-manual/book-information` | Not applicable | `native-v1/symbol_read_manual.svg` `1d208706…` | Transparent glyph |
| do not dismantle | do-not-dismantle variants (generic, dark, tw, h1-jp) | Outlined screwdriver in prohibition circle, matching the native crop | Reuse `do-not-dismantle/screwdriver-prohibited` | Not applicable | `native-v1/symbol_do_not_dismantle.svg` `5ad4fa83…` | Transparent glyph |
| no open flame | no-open-flame variants (generic, 3e3a39, crossed, crossed-fire-je2000f, h1-jp) | Flame and match crossed in circle; same tint | Reuse `no-open-flame/fire-match-prohibited` | Not applicable | `native-v1/symbol_no_open_flame.svg` `4a82cdd8…` | Transparent glyph |
| keep away from children | keep-away-from-children variants (generic, 3e3a39, panel, h1-jp) | Adult and child crossed in circle; same tint | Reuse `keep-away-from-children/adult-child-prohibited` | Not applicable | `native-v1/symbol_keep_away_from_children.svg` `a58074f9…` | Transparent glyph |

No icon was drawn, cropped or added to the library.

## Implementation

- Template route: `manual_sources/JE-1000H/EU/en/2.0/phase2/symbols_blocks.csv` sets
  `image_path` on the four JE-1000H rows; `source_manifest.json` re-locks it under
  `shared_symbol_revision`. The six locales rebuild from main. A 4e7df369 rebuild
  reproduces the published Markdown bytes for en/es/fr/de/it; against it, main
  differs only by the decorative `⚠` signal glyph (aria-hidden) the shared
  renderer dropped since then, plus the shared CSS. de/it additionally carry the
  merged #1476 LCD copy that their published 1465 build already has.
  uk at 4e7df369 rebuilds to 100,493 bytes against a recorded 100,337; its text
  equals main apart from `⚠`, and the published file must be compared before sealing.
- nl/pl/pt: sibling package `git-20261026-8bcb378f-shared-symbols`, derived by its
  `derive_shared_symbols.py`; only the symbol assets and their IR references
  differ (four rows on 2026-10-26, all seven since 2026-10-27). The approved
  package is untouched.

## Validation so far

- `tests.test_je1000h_eu_shared_symbols`, `tests.test_je1000h_eu_en_web`.
- Strict Sphinx for 18 before/after sites; Chromium 1280 and 390 px: no broken
  image and no horizontal scroll in the symbol table.

## Release decision (2026-10-26)

The operator reviewed the nine-locale 1280/390 before/after renderings and
decided 「上线提交发布」. The six template locales record it in
`manual_sources/JE-1000H/EU/en/2.0/source_manifest.json`
(`shared_symbol_revision.operator_release_approval`); pt/nl/pl bind it in the
package `approval.json`, which makes each IR publication-eligible. The engineering
PR is merged by the operator (AGENTS.md §8.6).

## Three more rows in pt/nl/pl (2026-10-27)

The seal gate binds every symbol row, so the operator decided 「那三行也换成共用图标」.

| Slot | Checked | Identity | Decision | New extraction | Final source and hash | Background |
| --- | --- | --- | --- | --- | --- | --- |
| warning | warning variants (outline-tinted, filled gray, h1-jp, je2000e) | Outlined triangle with tinted fill; aspect 1.126 vs native 1.128; tint (68,68,69) | Reuse `warning/outline-triangle-tinted` | Not applicable | `native-v1/symbol_warning_triangle.svg` `0f41fe5e…` | Transparent glyph |
| Li-ion | li-ion variants (generic, dark, htp017, Li-ion32 gray, je2000e) | Recycle arrows over “Li-ion” without “32”; aspect 0.876 vs 0.878; same tint (dark variant differs) | Reuse `li-ion/recycle-li-ion` | Not applicable | `native-v1/symbol_li_ion.svg` `317b9e9f…` | Transparent glyph |
| WEEE | weee variants (crossed-bin-bar, no-bar, gray, h1-jp, je2000e) | Crossed bin with bar; aspect 0.681 equals native | Reuse `weee/crossed-bin-bar` | Not applicable | `native-v1/symbol_weee.png` `6883f899…` | Transparent glyph |

The earlier approval covers the four-row Markdown only. `derive_shared_symbols.py`
applies it while its Markdown hashes match, so the seven-row package is a candidate
again until the operator approves the new pt/nl/pl renderings.

For the six template locales the operator ruled 「图标 外观一样 就是共用的」: their
template warning, Li-ion 32 and WEEE images show the same glyph, tint and
proportions as `warning/outline-triangle-tinted`, `li-ion/recycle-li-ion-32-gray`
and `weee/crossed-bin-bar`, so they count as shared. The template `weee.png`,
however, carries an opaque white backdrop; the operator then decided
「weee.png 带不透明的白底== 处理成透明底 作为共用的」. Its bytes are already in the shared
manifest's `withdrawn` list, and the same glyph exists transparent as
`weee/crossed-bin-bar`, so the six locales' WEEE row now points at that variant
(no new art, no template change; text unchanged). This fifth row is a candidate
until the operator reviews its renderings. The template `warning_triangle.png` and
`li_ion.png` bytes are also on the `withdrawn` list; the operator decided
「那两个也换成共用透明的」, so those rows point at `warning/outline-triangle-tinted`
(`0f41fe5e…`) and `li-ion/recycle-li-ion-32-gray` (`native-li_ion_gray_jp.svg`).
All seven rows in all nine locales now reuse shared variants byte for byte. The
six-locale rows added on 2026-10-27 await the operator's rendering review.

## Authority AI and native admission (2026-10-27)

The operator pointed to the JE-1000H (HTE159) record in the `发布文档管理` Base. Its
attachment `JE-1000H_修正版.ai` (SHA-256 `ffbad263…`, 161 pages; the same-source
portrait PDF is `8133ff3d…`) was downloaded read-only and committed as the pt/nl/pl
symbol authority; the original 0928 AI `8bcb378f…` is recorded as superseded. Rows
are bound inside the intake `icon_bbox` because the JE-2000F rule-band heuristic
dropped the read-manual book outline. Eighteen rows pass within 0.004–0.015.
Li-ion matched no shared variant within 0.02 (closest `native-dark` 0.0218;
`recycle-li-ion` 0.079). The operator ruled 「要允许误差 这个误差 就是人工引入的
你需要处理成共用的」: the gate gained trusted glyph waivers (0.03 hard ceiling), and
three entries admit `li-ion/recycle-li-ion-native-dark` for pt/nl/pl.

uk byte question resolved: the live Hello-Docs uk Markdown differs from a
4e7df369 rebuild only in the column padding of one empty-header Markdown table;
visible text is identical. Live de/it also equal the main rebuild in visible text.

## Release decision for the seven-row version (2026-10-27)

The operator reviewed the nine-locale seven-row renderings and decided
「上线提交发布」. pt/nl/pl bind it in the package `approval.json` (Markdown
`a0ba3718…` / `91eec6f9…` / `f9e4d011…`) and are publication-eligible; the six
template locales record it in `shared_symbol_revision.operator_release_approval`.

## Pending

1. Operator review and merge of the engineering PR (AGENTS.md §8.6).
2. After merge: seal at the merged main commit and a Hello-Docs `docs/publish/**` PR.
