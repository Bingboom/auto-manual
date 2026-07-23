# IDML render-contract regression discovery (2026-07-22)

## Outcome

The regression is a contract-selection failure, not a loss of source copy and
not a Read the Docs rendering change. `JE-1000F / US / en+fr+es` has an
approved 58-page reference-layout contract, but commit `75579a11` (PR #693)
removed its only registry entry while leaving the contract itself marked
`approved`. Production IDML therefore selected the measured-LaTeX fallback.

That fallback is intentionally approximate and is not a stable replica input:

- the 2026-07-22 review artifact emitted 61 IDML pages from a 63-page measured
  LaTeX PDF and native InDesign preflight found 7 overset stories;
- a clean reproduction from the identical `origin/main` tree and identical
  manual IR emitted 60 IDML pages from a 62-page measured LaTeX PDF;
- the accepted `JE-1000F_US_editable_v29` artifact used the approved plan,
  emitted 58 pages, and passed native preflight with 0 overset stories,
  0 missing fonts, and 0 bad links.

The fallback also changes component routing. Product Overview and operation
page boundaries use approved-plan composition metadata. Without it, operation
copy flows through estimated prose frames and the fallback inserts only one
operation break before Key Combinations. The four available operation frames
are already exhausted, so the Key Combinations component requires a fifth frame
that does not exist. Its native editable story XML is still present, but it is
overset and therefore not visible in the InDesign document.

Restoring the approved plan exposed a second, independent defect in the App
composition. The first editable-overlay implementation inferred App control
labels from whatever body block followed the screenshot. English and French
happened to carry three duplicate label lines there, while Spanish immediately
continued with step 2.3. That made the renderer consume ordinary Spanish prose
as a control label. The fixed-size French/Spanish overlay and notice frames also
did not remeasure after localized style overrides, producing eight native
overset stories. The other two overset entries displayed only `U+0016` because
InDesign represents an embedded table with that story placeholder: they were
the French and Spanish Troubleshooting tables, whose fixed 240 pt inner frames
clipped the final `FE` row after localized rows auto-grew. The resulting total
was 10. That 58-page report is a regression baseline only, not an accepted
artifact.

## Evidence

- At the affected `origin/main` revision,
  `docs/renderers/contracts/reference_layout_registry.json` contained
  `"plans": []`.
- `docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json`
  remains `approval.status=approved`, covers all 52 source pages and physical
  pages 1-58, and binds the approved PDF SHA-256
  `e72b1ba01882062e261b17d5ba54a2f7c3099e5ba531a6428be13888641083f2`.
- Current manual IR identity is:
  - content: `e38dad9c6e8d47ea2e1a3c5fe724786d22489861832beebd42cb5a4d953318b3`
  - snapshot: `7e5ebfa8713983d055210c00e22305e34f636a83d5c3bcab210bb39a5706f0c5`
  - style contract: `32a0167cb7915c0bcdeec1e4a4938b4fc023a65b0257bee8cc21cd546c082712`
  - layout params: `92498016e185dd6949171c4a5c435ac5ac76d53e9b535fe567ab59fe2270c139`
- The stale approved contract differs in snapshot SHA, layout-parameter SHA,
  and the Spanish troubleshooting page SHA. Its partial refresh was the reason
  cited by PR #693 for temporary deregistration.
- The previous Manual IR hashed `layout_params.csv` as raw bytes. An LF/CRLF
  conversion, blank row, or comment-column-only edit could therefore report
  layout drift even when the ordered layout tokens were unchanged. This false-
  drift path did not itself remove the registry row, but made contract refresh
  unnecessarily fragile and encouraged partial hash maintenance.
- The previously separate operation-alignment work is already present on
  `origin/main` through PR #692 plus the localized fixes in PRs #699 and #701;
  re-merging the old branch would instead discard newer RTD and IDML fixes.

## Root-cause chain

1. A source snapshot/layout change invalidated the hash-bound plan.
2. The refresh changed only part of the contract identity.
3. To unblock a build, PR #693 removed the registry entry.
4. Registry absence was interpreted as “ordinary unapproved target”, even
   though an approved matching contract still existed on disk.
5. The exporter silently selected fallback pagination and component routing.
6. The longer estimated operation stories overset; Key Combinations and other
   later editable content became invisible.
7. After contract restoration, App labels were still inferred positionally
   from adjacent prose rather than from a language-and-role source contract.
8. Spanish step 2.3 was therefore eligible to be consumed as overlay copy, and
   long French/Spanish labels and notices retained stale fixed measurements.
9. Troubleshooting used a 240 pt fixed frame even though its 12 row minima
   already consumed 235.86 pt; localized wrapping grew beyond the remaining
   4.14 pt and hid `FE` on the French and Spanish pages.
10. Native InDesign correctly reported all of those editable stories as
    overset.

## Source-level resolution

1. Approved-but-unregistered matching contracts now raise a hard error.
   Fallback is allowed only when no approved contract exists for the target.
2. `tools/reference_layout_rebind.py` performs a dry-run by default and, with
   `--write`, atomically refreshes all Manual IR identity fields and all 52 page
   hashes/languages together. It validates the complete candidate and refuses a
   changed source order or physical composition map.
3. Manual IR now hashes the ordered parsed layout-token `key`/`value`/`unit`
   semantics. Line endings, blank rows, and comment-column changes do not drift
   the contract; token value/unit/order changes still do.
4. Key Combinations now has one token-driven `KeyCombinationStyle` component.
   Shared geometry and typography live in `data/layout_params.csv`; governed
   French/Spanish differences are locale overrides, and all independent text
   frames are emitted last above linked assets and native shapes.
5. Product Overview is the localized App-label source of truth. Stable table
   slots are indexed as `language + semantic role` (`main_power`, `dc_usb`,
   `ac`); the approved plan binds those exact base labels to reviewed App-only
   display variants. Only an adjacent three-line block that exactly matches
   the base-label set is deduplicated, so ordinary prose and Spanish step 2.3
   remain in the story.
6. App overlays use one token-driven `AppFigureStyle`; labels and notices are
   remeasured after all locale/geometry overrides, and their unlocked text
   frames are emitted above artwork. Missing approved roles, variants, assets,
   or style tokens fail the build instead of falling back to guessed copy.
7. Troubleshooting uses one `TroubleshootingTableStyle` and a deterministic
   localized row-wrap estimate derived from measured EN/FR/ES row baselines,
   a 5.5 pt Regular corrective-measure style, a component-local Bold header,
   the governed code-column optical width, and locale heading/table rhythm
   tokens. Its editable panel remains fixed at the computed content-safe
   height; an invisible host-frame allowance contains the complete anchored
   group instead of relying on a finalizer to hide overflow. English retains
   the 240 pt floor while longer translations grow.
8. Rebind the approved contract to the current frozen review IR, restore its
   exact registry entry, then verify on the cheap-to-expensive ladder and
   finalize the emitted IDML in Adobe InDesign 2026 `21.0.1.6`.

## Files in scope

- `tools/idml/reference_layout_plan.py`
- `tools/reference_layout_rebind.py` (new, low-level maintainer command)
- `tools/idml/control_labels.py`
- `tools/idml/components/key_combinations.py`
- `tools/idml/components/reference_figure.py`
- `tools/idml/components/notice.py`
- `tools/idml/components/prose_table.py`
- `data/layout_params.csv`
- `docs/renderers/contracts/manual_style.yaml`
- `docs/renderers/contracts/reference_layout/*.json`
- `docs/renderers/contracts/reference_layout_registry.json`
- targeted tests and the owning workflow documentation

## Non-goals

- No content-source or phase2 schema edits.
- No changes to the approved 58-page composition map or reference PDF.
- No whole-page placed artwork as visible output.
- No hiding, deleting, or rasterizing operation copy to make preflight pass.
- No merge from the stale `fix/idml-operation-template-alignment` branch.

## Safety net and acceptance

Run, in order:

1. Ruff on changed Python.
2. Reference-plan and Key Combinations targeted tests.
3. Full `python3 -m unittest`.
4. Maintainability guardrails and documentation-link integrity.
5. `build.py idml` from `review-asis` with the frozen phase2 attachment root.
6. Native InDesign finalization and PDF/X validation.
7. Approved-PDF parity and focused page inspection.

Acceptance is exactly 58 pages and 52 source bindings, 0 overset stories,
0 missing fonts, 0 bad links, valid PDF/X-4 output intent, all editable Key
Combinations and App text frames present above the artwork, Spanish step 2.3
still present in its prose story, all 12 French/Spanish Troubleshooting rows
including `FE` visible, and no approved-plan fallback note.
