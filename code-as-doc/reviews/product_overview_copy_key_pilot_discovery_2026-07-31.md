# Product Overview Copy-Key Pilot Discovery

Date: 2026-07-31

Scope: Workstream W / Stage 5 item 6

## Finding

The US Spanish, French, and Brazilian Portuguese Product Overview templates
still own seven pieces of localized chrome as literal RST text. The same seven
values already exist in both the committed phase2 fixture and the operator's
current phase2 snapshot under these `Localized_Copy` keys:

- `product_overview.page_title`
- `product_overview.front_view`
- `product_overview.right_side_view`
- `product_overview.part.handle`
- `product_overview.part.lcd`
- `product_overview.part.led_light_button`
- `product_overview.part.led_light`

The `text_fr`, `text_es`, and `text_pt-BR` values match the template literals
exactly. The shared resolver already fails closed when a referenced key or
language value is absent, so this slice needs no new runtime behavior or source
table write.

## Implementation

1. Add a characterization test that resolves the seven keys through the real
   RST substitution boundary and locks each rendered template to its pre-change
   SHA-256.
2. Replace only the matching literals in the three US templates with copy-key
   tokens.
3. Record the source-of-truth change in the maintainer and operator guides.

## Safety properties

- The rendered RST for all three templates remains byte-identical.
- Missing `Localized_Copy` data continues to fail closed.
- No Feishu/Base or `data/phase2` production row is written.
- No EU raw-LaTeX Product Overview page is changed.
- Existing descriptive image-alt prose remains literal; adding dedicated alt
  copy keys is outside this pilot.
- No page geometry, IDML composition, reference-layout contract, or asset is
  changed.

## Verification ladder

- Ruff.
- `tests.test_product_overview_copy_pilot` plus localized-copy/template tests.
- Full `unittest` suite.
- Maintainability guardrails and documentation link integrity.
- US and JP fixture-root `build.py check` baselines.
