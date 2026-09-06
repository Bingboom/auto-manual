# Web P2 shared contracts: variable Inbox and declared entry page

Status: implemented and locally verified. This record covers only the shared P2
contracts required by the first solar-panel and charger Web manuals; it does
not claim that either target is built or published.

Baseline: `ef45a0df` (`origin/main`, 2026-09-06).

## Discovery

- `HB-SPECIAL-INBOX` currently accepts exactly three cards in
  `tools/component_specs/inbox.py`, repeats that assumption in the HTML parser,
  retained-carrier validation and public-IR payload validation, and renders a
  fixed three-column Web grid.
- Existing three-card public IR uses `three-card-responsive` plus the three
  asset roles `card_1_art` through `card_3_art`. That shape is a compatibility
  contract and must remain readable.
- The component registry currently declares renderer capability only at the
  component level. A new Web-only variant would therefore falsely inherit the
  existing LaTeX, IDML and Word `rendered` claims unless variant-specific
  bindings are introduced.
- `tools/word_bundle_html.py` checks the first included Web page through
  `is_web_entry_page`. Existing governed JE-1000F prefaces remain protected,
  while unlisted targets implicitly accept any first included page. Short
  category manuals need an explicit, fail-closed declaration instead of relying
  on that fallback.

## Implementation plan

1. Add characterization tests for the existing three-card IR and governed
   preface behavior.
2. Add a `responsive-card-grid` Inbox variant that owns an ordered repeated
   `card_art` asset role. Keep the existing variant and serialized shape intact.
3. Add variant-specific renderer capability declarations. Web is `rendered`;
   LaTeX, IDML and Word are `not-applicable` for the new variant and their
   adapters must reject it explicitly.
4. Generalize the governed HTML carrier and IR validators to the declared card
   count, then add responsive five-card Web styling without changing the legacy
   three-card selectors.
5. Add `build.web_entry_source_patterns` as the category/target declaration
   consumed by the real Web bundle entrypoint. An empty or mismatching
   declaration fails closed; omitted declarations preserve current targets.
6. Document the contracts and validate targeted tests, Ruff, the full unit
   suite, maintainability guardrails, documentation links and the JE-1000F
   EU/en Web regression.

## Verification

- 102 focused component, Web, registry, stylesheet and bundle tests passed.
- Full repository Ruff passed.
- Full `python -m unittest` passed (3,781 tests; 22 skipped).
- Maintainability guardrails passed without raising either touched-file limit:
  `tools/web_inbox_component.py` remains at 120 lines and
  `web_inbox_components.css` remains at 180 lines.
- Documentation link integrity passed: 158 Markdown files, 1,710 links, zero
  broken.
- `JE-1000F / EU / en` passed both `build.py check` and a Web-profile `md`
  build from the committed phase2 fixture into isolated `/tmp` staging.

## Non-goals

- No JS-100I or JA-AD01A target data, templates, assets or configuration in
  this shared PR.
- No five-card print, LaTeX, IDML or Word layout implementation.
- No phase2 schema or live Base writes.
- No Hello-Docs publish snapshot, merge or production deployment.
