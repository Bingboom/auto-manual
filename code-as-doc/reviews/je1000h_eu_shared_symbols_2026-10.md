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
  `derive_shared_symbols.py`; only the four assets and their IR references differ.
  The approved package is untouched.

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

## Pending

1. pt/nl/pl seal: `seal_frozen_web_evidence` runs `require_symbol_asset_admission`,
   which needs the HTE159 AI (`8bcb378f…`, not committed) and binds **every**
   symbol row to a shared variant. The unchanged warning, Li-ion and WEEE rows
   are native crops, so the seal cannot pass until the operator decides on those
   three rows and supplies the AI.
2. en/fr/es/de/it/uk: the template route's release evidence does not run the
   symbol gate; they can be sealed from the merged main commit. uk must first be
   compared with the live Hello-Docs file (the 100,493 vs 100,337 byte question).
3. After merge: seal at the merged main commit and a Hello-Docs `docs/publish/**`
   PR. Hello-Docs access for this session is still missing.
