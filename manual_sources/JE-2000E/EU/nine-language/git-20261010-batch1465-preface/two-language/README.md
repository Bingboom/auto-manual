# JE-2000E / EU batch 1465 preface candidate

This immutable candidate adds the delivered European Portuguese preface wording and Dutch paragraph 2. EU legal subject remains **Jackery**, confirmed by the operator on 2026-10-10. Polish and the six older routes are unchanged.

`approved_copy_corrections.json` pins the exact before/after strings, original frozen release manifest, delivered PDF SHA-256 and physical page 4. Copy corrections are represented as native manual-ir/v2 paragraph nodes and recorded source errata. All later pages, semantic components and artwork remain byte-equivalent to the prior package. The older immutable packages are preserved.

This is a prepared native source candidate, not an online deployment. Replay with the public `tools.web.frozen_ai_web.replay_package` against a copied locale package, then build with Sphinx `-W --keep-going`. Re-seal release evidence through `tools.web.frozen_source_evidence.seal_frozen_web_evidence`; fresh admission requirements apply. Do not change generated `docs/publish` directly. Engineering PR approval and the generated Hello-Docs publish PR remain separate gates.

## Current validation and remaining gate

PT/NL native IR validation, fresh component admission, byte-identical cold replay and Sphinx warnings-as-errors builds pass. The 22 existing frozen component/evidence regression tests pass. Release sealing is blocked by `symbol asset admission failed: symbol table requires source-bound asset admission`; the unchanged historical PT/NL baseline reproduces the same failure. Source-bound symbol admission evidence must be supplied before release. No PR or publication has been created.
