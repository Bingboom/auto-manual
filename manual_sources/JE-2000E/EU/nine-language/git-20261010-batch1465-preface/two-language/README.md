# JE-2000E / EU batch 1465 preface candidate

This immutable candidate adds the delivered European Portuguese preface wording and Dutch paragraph 2. EU legal subject remains **Jackery**, confirmed by the operator on 2026-10-10. Polish and the six older routes are unchanged.

`approved_copy_corrections.json` pins the exact before/after strings, original frozen release manifest, delivered PDF SHA-256 and physical page 4. Copy corrections are represented as native manual-ir/v2 paragraph nodes and recorded source errata. All later pages, semantic components and artwork remain byte-equivalent to the prior package. The older immutable packages are preserved.

This is a prepared native source candidate, not an online deployment. Replay with the public `tools.web.frozen_ai_web.replay_package` against a copied locale package, then build with Sphinx `-W --keep-going`. Re-seal release evidence through `tools.web.frozen_source_evidence.seal_frozen_web_evidence`; fresh admission requirements apply. Do not change generated `docs/publish` directly. Engineering PR approval and the generated Hello-Docs publish PR remain separate gates.

## Current validation and remaining gate

PT/NL native IR validation, fresh component admission, cold replay and Sphinx warnings-as-errors builds pass. The 40 existing frozen component/evidence, symbol admission and caption-frame tests pass. Source-bound symbol admission and release sealing pass for both languages.

The operator-provided `JE-2000E_修正版_竖版.pdf` is the authority witness for physical pages 123 (PT) and 142 (NL). Sixteen native SVG variants preserve source drawing paths, have real transparent margins, reuse explicitly registered shared variants and match independently reconstructed source glyphs with zero normalized pixel error. `symbol_caption_recovery.json` records the Portuguese period and closing-parenthesis recovery from source text. This witness does not replace the earlier body intake provenance: the historical authority identity is retained in `baseline_original_source`, and the prior recipe remains pinned.

Engineering PR review/merge, business-plane sync, generated publish PR and live RTD acceptance remain pending. No merge or deployment is represented by this source candidate.

The sixteen shared symbol variants are stored under the existing `native-v1/` asset folder, with `je2000e-eu-batch1465-` filenames. Their semantic keys and glyph bytes are unchanged. The 63 design-system, portal, deployment-receipt and symbol-admission regression tests pass after catalog integration.
