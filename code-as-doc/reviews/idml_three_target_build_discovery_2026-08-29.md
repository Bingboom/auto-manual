# IDML three-target final-assembly discovery — 2026-08-29

## Decision

Restore the real final-assembly build for all three currently exercised targets
without weakening an approved reference-layout gate and without adding a second
set of model-specific page logic.

The acceptance target is the public entrypoint, not a component shortcut:

```bash
python3 build.py idml --config configs/config.us.yaml \
  --model JE-1000F --region US --source review-asis \
  --data-root tests/fixtures/phase2 --idml-mode both

python3 build.py idml --config configs/config.kr.yaml \
  --model JE-3000C --region KR --source review-asis \
  --data-root tests/fixtures/phase2 --idml-mode both

python3 build.py idml --config configs/config.bp-us.yaml \
  --model JBP-2000B --region US --source runtime \
  --data-root tests/fixtures/phase2 --idml-mode both
```

All three commands must exit zero, report `skipped_raw=0`, emit both the final
assembly IDML and flow IDML, and produce ZIP-readable packages. Candidate status
is a separate governance decision: this repair does not promote JE-3000C/KR or
JBP-2000B/US to an approved production reference layout.

## Reproduced baseline

Base SHA: `2799ed3596126a7760e666ad4b8ff0a4f704ed2a`.

| Target | Final assembly | Flow-only control | Finding |
| --- | --- | --- | --- |
| JE-1000F/US | blocked by approved content, assembly, language, and per-page source pins | 52 pages, 573 blocks, `skipped_raw=0` | local `main` carries an older review derivative than the approved business-plane review branch |
| JE-3000C/KR | 18/18 physical pages, 143 blocks, `skipped_raw=0` | passes | preserve as the regression control |
| JBP-2000B/US | `compact SymbolsPanel cannot drop symbol rows` | 43 pages, 228 blocks, `skipped_raw=0` | standard-layout continuation metadata leaks into a compact one-page composition |

The IDML component tests passed at baseline, which proves that the JBP failure is
an end-to-end source-projection gap rather than a missing component primitive.

## Root cause 1 — JE-1000F approved source selection

The approved contract was rebound on 2026-08-14 against the frozen business-plane
review derivative. Its exact source is:

- repository: `Bingboom/Hello-Docs`
- branch: `review/JE-1000F-US`
- commit: `e06def5e49e107e1a9595c1f38bb11b1d5496f94`
- review root: `docs/_review/JE-1000F/US`

The engineering-plane `main` copy is older. Replacing it in a scratch worktree
with the 76 blobs from the exact review commit removed every source-page,
language, assembly, and editable-control-label mismatch. Only
`identity.content.manual_content_sha256` remained different.

That final content difference is expected: current Manual IR activates the
dedicated `idml` semantic branch so editable components replace opaque raw-LaTeX
artwork. An explicit rebind dry-run against the exact review derivative reported:

```text
identity=content.manual_content_sha256,provenance.snapshot_sha256
page_bindings=0
content_reapproved=yes
composition_map=unchanged
validation=passed
```

Therefore the safe repair is:

1. mechanically synchronize the exact 76-file review derivative into the
   engineering plane, without deleting or renaming review files;
2. reapprove only the Manual-IR content identity for the current editable IDML
   projection;
3. preserve the approved reference PDF, 52 source refs, 58-page composition,
   every page binding, language mapping, and the original live-snapshot
   provenance.

The operator directive in this task — restore final assembly to 3/3 — is the
approval record for the content-identity refresh. A fixture snapshot must not
replace the existing live provenance while rebinding.

## Root cause 2 — JBP compact Symbols composition

The shared RST symbol projection records the approved JE-US standard composition:
French and Spanish rows 5–6 and 11 carry `continuation=true`. The JBP target
reuses the same semantic rows but composes Safety + Symbols on one compact page.
`SymbolsPanel` currently respects the standard continuation flag for both
densities, so the compact page returns three overflow rows and the shared page
correctly refuses to drop them.

The component boundary owns this normalization. Compact density must render the
complete source row set in its explicit left/right columns; standard density must
continue to preserve continuation rows for the approved JE layout. The repair
belongs in the shared `SymbolsPanel` behavior and its integration tests, not in a
JBP model branch or target-specific page renderer.

## Planned files and safety nets

| Phase | Files | Safety net |
| --- | --- | --- |
| approved source repair | `docs/_review/JE-1000F/US/**`, `docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json` | exact remote commit inventory; rebind reports one enforced identity field, zero page bindings, unchanged composition map; reference-pin check |
| compact component repair | `tools/idml/components/symbols_panel.py`, targeted tests | explicit-column FR/ES continuation rows render 11/11 in compact density; standard continuation behavior unchanged |
| frozen Web fixture alignment | `tests/fixtures/phase2/web_composite_manifest.json`, Web presentation assertions | source-fragment pins and expected live copy match the exact approved review derivative; composite asset bytes and fail-closed checking stay unchanged |
| documentation | this report plus the owning component/build contract docs | documentation link integrity |
| final verification | no committed generated files | Ruff, targeted tests, full unit suite, guardrails, reference pins, doc links, then three isolated `--idml-mode both` builds and `unzip -t` |

## Non-goals

- No weakening, fallback, bypass, or automatic rebind of approved identity gates.
- No new model-specific renderer, page composition type, or layout-token family.
- No candidate-to-production promotion for JE-3000C/KR or JBP-2000B/US.
- No reference-PDF, physical-page-map, public CLI, dependency, schema, workflow,
  review-file name, or generated-artifact change.
- No cleanup of the operator's existing `_build` or release artifacts.

## Full-suite compatibility finding

The first clean-worktree full-suite run correctly failed after the approved
review derivative was restored: nine Web composite entries still pinned source
fragments from the older engineering-plane copy, and eight presentation literals
still expected its older live wording. The repair refreshes only those source
fragment hashes and literal expectations. It does not change composite asset
bytes, source matching, Web layout logic, or the review derivative itself.
