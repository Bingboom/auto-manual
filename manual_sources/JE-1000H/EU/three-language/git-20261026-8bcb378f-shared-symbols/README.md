# JE-1000H EU pt/nl/pl: shared symbol glyphs

Sibling of the approved `git-20261001-8bcb378f-temperature-web` package, which
stays unchanged. Operator request 2026-10-26:「这个 JE-1000H的图标 改成共用图标」,
then「nl/pl/pt 也改」.

Only four symbol-table assets differ per language. The native PNG crops for
read manual, do not disassemble, keep away from fire and keep away from children
are replaced byte for byte by the shared Web variants
`read-manual/book-information`, `do-not-dismantle/screwdriver-prohibited`,
`no-open-flame/fire-match-prohibited` and
`keep-away-from-children/adult-child-prohibited`. Warning, Li-ion and WEEE keep
their bytes. Captions and all other copy are unchanged (visible text checked);
the MyST is replayed from the IR by `tools.web.frozen_ai_web.replay_package`.

`derive_shared_symbols.py` applies this idempotently and refreshes
`source_manifest.json`. Status: `operator-approved-git-only-release`. The
operator reviewed the 1280/390 renderings and decided「上线提交发布」on
2026-10-26; `approval.json` binds the reviewed candidate and makes each IR
publication-eligible. The seal still requires source-bound symbol admission
against the HTE159 authority AI (SHA-256 `8bcb378f…`), which is not committed,
and that gate binds every symbol row, including the unchanged warning, Li-ion
and WEEE crops, to a shared variant. No Feishu write, queue row or
asset-register promotion is part of this package.
`tests/test_je1000h_eu_shared_symbols.py` checks the bindings, text and cold replay.
Review record: [je1000h_eu_shared_symbols_2026-10](../../../../../code-as-doc/reviews/je1000h_eu_shared_symbols_2026-10.md).
