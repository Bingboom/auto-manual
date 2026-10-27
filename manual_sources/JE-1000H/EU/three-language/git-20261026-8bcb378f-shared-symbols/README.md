# JE-1000H EU pt/nl/pl: shared symbol glyphs

Sibling of the approved `git-20261001-8bcb378f-temperature-web` package, which
stays unchanged. Operator request 2026-10-26:「这个 JE-1000H的图标 改成共用图标」,
then「nl/pl/pt 也改」.

Only the symbol-table assets differ per language. On 2026-10-26 the four marked
native crops (read manual, do not disassemble, keep away from fire, keep away from
children) were replaced byte for byte by the shared Web variants
`read-manual/book-information`, `do-not-dismantle/screwdriver-prohibited`,
`no-open-flame/fire-match-prohibited` and
`keep-away-from-children/adult-child-prohibited`. On 2026-10-27 the operator
decided「那三行也换成共用图标」: warning, Li-ion and WEEE now use
`warning/outline-triangle-tinted`, `li-ion/recycle-li-ion` and
`weee/crossed-bin-bar`, whose glyph, tint and aspect match the native crops.
Li-ion uses `li-ion/recycle-li-ion-native-dark`: no shared variant matches the
revised source glyph within 0.02, and the operator ruled「要允许误差 这个误差 就是人工引入的
你需要处理成共用的」, recorded as trusted waivers in
`docs/renderers/contracts/symbol_glyph_waivers.json` (measured 0.0218).
Captions and all other copy are unchanged (visible text checked); the MyST is
replayed from the IR by `tools.web.frozen_ai_web.replay_package`.

`derive_shared_symbols.py` applies this idempotently and refreshes
`source_manifest.json`. The symbol authority is the batch-1465 revised AI
`source/JE-1000H_修正版.ai` (SHA-256 `ffbad263…`, 161 pages) from the JE-1000H
(HTE159) record of the `发布文档管理` Base; the original 0928 AI (`8bcb378f…`) is kept
as `superseded_original_source`. Every symbol row of pt (p.111), nl (p.128) and pl
(p.145) is bound to its native glyph drawings within the intake `icon_bbox` and its
caption pixels, and passes `require_symbol_asset_admission` (results in
`symbol_asset_admission`). Status: `operator-approved-git-only-release`. On
2026-10-27 the operator reviewed the seven-row 1280/390 renderings and decided
「上线提交发布」; `approval.json` binds those Markdown hashes (the 2026-10-26 four-row
review is kept as `superseded_review`) and makes each IR publication-eligible. No
Feishu write, queue row or asset-register promotion is part of this package.
`tests/test_je1000h_eu_shared_symbols.py` checks the bindings, text and cold replay.
Review record: [je1000h_eu_shared_symbols_2026-10](../../../../../code-as-doc/reviews/je1000h_eu_shared_symbols_2026-10.md).
