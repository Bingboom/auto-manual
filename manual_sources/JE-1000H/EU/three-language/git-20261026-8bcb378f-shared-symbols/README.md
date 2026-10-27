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
Captions and all other copy are unchanged (visible text checked); the MyST is
replayed from the IR by `tools.web.frozen_ai_web.replay_package`.

`derive_shared_symbols.py` applies this idempotently and refreshes
`source_manifest.json`. `approval.json` records the operator's「上线提交发布」for
the four-row candidate; it applies only while its Markdown hashes match, so the
seven-row package is a candidate again until the operator approves the new
1280/390 renderings. The seal also requires source-bound symbol admission against
the HTE159 authority AI (SHA-256 `8bcb378f…`), which is not committed. No Feishu
write, queue row or asset-register promotion is part of this package.
`tests/test_je1000h_eu_shared_symbols.py` checks the bindings, text and cold replay.
Review record: [je1000h_eu_shared_symbols_2026-10](../../../../../code-as-doc/reviews/je1000h_eu_shared_symbols_2026-10.md).
