# JE-1000F EU uk/pt/nl/pl: shared symbols and the battery row

Version: git-20261102-30bcad90-shared-symbols

Sibling of the approved `git-20260930-c38415f5-shared-keys` package, which stays
unchanged. Operator request 2026-11-02:「先用修正版.ai 把荷波葡乌的电池图标补上」.
The revised AI has no battery row in any of its nine languages, so the operator
chose「网页版单独补（同英法）」: the Web adds the row, as en/fr/de/es/it already do.

Only the symbol table changes. Its seven printed rows now reuse the shared Web
variants byte for byte. The previous native crops are not shared-library bytes, and
the WEEE crop is withdrawn. The eighth row is the Web-only
`battery-weee/crossed-bin-no-bar`. All other copy, images and IR blocks are
unchanged; visible text differs only by the added caption.

`derive_shared_symbols.py` applies this idempotently and refreshes
`source_manifest.json`. Symbol authority is the batch-1465 revised AI
`source/JE-1000F_修正版.ai` (SHA-256 `30bcad90…`, 161 pages) from the JE-1000F
record of the `发布文档管理` Base. The 0923 AI (`c38415f5…`) is kept as
`superseded_original_source`.

Each printed row of uk (p.94), pt (p.111), nl (p.128) and pl (p.145) is bound to
its native glyph drawings and caption pixels, and passes
`require_symbol_asset_admission`. Li-ion measures 0.0233, the batch-1465 design
variation already waived for JE-1000H. The operator ruled「同 JE-1000H，允许」,
recorded as trusted waivers in `docs/renderers/contracts/symbol_glyph_waivers.json`.

The battery row reuses a printed row from a sibling EU Explorer manual: JE-2000F
`修正版.ai` for pt/nl/pl, and the JE-3600A 0924 AI p.94 for uk, whose wording
matches the published JE-3600A uk Web page. Those rows are bound through
`docs/renderers/contracts/symbol_web_only_rows.json`, and the gate checks the
donor glyph, caption text and caption pixels.

Status: `operator-approved-git-only-release`. The operator reviewed the eight-row
1280/390 renderings and decided「上线提交发布」. `approval.json` binds those
Markdown hashes and makes each IR publication-eligible. No Feishu write, queue row
or asset-register promotion is part of this package. `tests/test_je1000f_eu_shared_symbols.py`
checks the bindings, the added text and cold replay.
Review record: [je1000f_eu_shared_symbols_battery_2026-11](../../../../../../code-as-doc/reviews/je1000f_eu_shared_symbols_battery_2026-11.md).
