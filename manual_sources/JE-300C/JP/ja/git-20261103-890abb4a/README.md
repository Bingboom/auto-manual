# JE-300C / JP / Japanese — Git-only Web release

Operator decision, 2026-11-03 (「继续 转日语说明书」): convert the JP single-language manuals that have a
customer model and a single-language PDF and are not yet on the Web. This package converts the Japanese
manual of the Jackery ポータブル電源 300 New (model JE-300C) from the 发布文档管理 Base row `reczz28SfbsHdirt`
(material 16-0102-000066, project HTE142). Route `JE-300C/JP/ja/md`, `legacy_default`.

**Status: `operator-approved-git-only-release`.** On 2026-11-04 the operator reviewed the 1280/390 renders beside the shared reference edition (PR #1657, reviewed commit `76fe0a13`) and said 「上线提交发布：JE-300B、JE-300C、JE-300D、JE-500A」 in the engineering session. `source/approval.json` binds that acceptance to these exact source inputs and the IR is publication-eligible. Source copy is published verbatim; `source_concerns` go to the source owner. The PR is merged only on the operator's own authorization (AGENTS.md §8.6).

## Source authority

- `original.pdf`: the row's Japanese PDF `【Jackery ポータブル電源 300 New】说明书-JP.pdf`, byte-exact
  (SHA-256 `890abb4ae5ba63f966853417afe67616abd8314a357eab67b8eea6e51b022838`, 23 pages, 130 × 185 mm).
  Outlined, no text layer. The Japanese original governs all copy.
- Print master: `16-0102-000066 HTE142300A-JP-JAK 说明书 RoHS REACH-Q.pdf` (SHA-256 `e9c89d75…cef9926`,
  25 pages); recorded in `source_manifest.json:print_master` for traceability, not archived here and not an
  extraction source.
- Identity (record id, material number, project, SKUs) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

The outlined-PDF method of the released US/en packages (worked example: the same model's
`manual_sources/JE-300C/US/en/git-20261027-a1128b25`). `source/intake.py` holds the line-by-line
transcription from 300 dpi renders (500–600 dpi clips for small or ambiguous glyphs), built from shared flow
and shared components only (`source_manifest.json:component_map`; no declared exceptions). Pages 3–23
(printed 01–20 plus the back cover) are Web content; the cover (p1) and contents (p2) are not. Source slips
stay as printed (`source_manifest.json:source_concerns`). The pictogram warning grids become one shared
warning/caution callout per printed row (JE-1000D JP V2 precedent). Shared reference edition for review:
the same model's released US English Web.

## Artwork

- **Panels** (`source/figures.json`, each with a `reuse_review`): 18 cut from `original.pdf` at 4x just inside
  the print panel frame (Japanese words in the art stay in the art and the alt text). `charging-usbc` reuses
  the US package's panel unchanged (pixel comparison: only anti-aliased edges differ).
- **LCD glyphs** (`source/glyphs.json`): 17 rows, each compared with the US package glyph by the fixed
  comparison; 9 reuse it (UPS, output voltage, AC wall charging, battery ring, thermometer ×3, 6H inline ×2),
  8 are this print's native vector paths (AC power, input/output power, car/solar charging, battery
  percentage, fault code, energy saving).
- **Symbols** (`source/symbols.json`): 12 rows; 10 reuse a shared symbol byte for byte. The `unplug/` row (p3,
  `unplug/h1-jp-native`) and the Li-ion 32 row (p4, `native/je3000c-kr-78316033-06`) bind the operator-confirmed canonical of its shared symbol group (PR #1659, decision SCG-20261103): no variant passes the fixed comparison, and the release admission releases the group canonical because the printed caption is a source-verified caption of that group.
  Nothing was added to the shared library.

## Rebuild

```sh
PKG=manual_sources/JE-300C/JP/ja/git-20261103-890abb4a
python3 -W ignore "$PKG/source/extract_assets.py"
python3 -W ignore "$PKG/source/intake.py"
python3 -W ignore "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 -W ignore "$PKG/rebuild.py" --output tmp/je300c-jp/ja
python3 -m sphinx -n -W --keep-going -b html tmp/je300c-jp/ja tmp/je300c-jp-site
```

A fresh rebuild is byte-identical to `web/ja`; the prepared-document shared-style admission reports no issues.

## Boundaries

Git-only release: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; no
phase2 or print target is registered and no shared renderer, component, contract, symbol library or workflow
changed. Release needs the operator's acceptance of the renders and a
separate merge/release authorization.
