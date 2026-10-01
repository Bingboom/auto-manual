# Textless-extraction operator playbook

Distilled from the Milestone J rounds (2026-07-13 → 07-28: master榨取 ×3, the
JP-burned-text escape, PR #734's leader-hole repair). Operator names below are
the literal `transforms[].op` values accepted by
`data/asset_recipes/asset-extraction-recipe-v1.schema.json` and implemented in
`tools/asset_pipeline/extract.py` — verify against the code when in doubt.

## Reuse and classification before text removal

Complete the selection table in the shared
[Web artwork contract](../../../../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)
first: record searched manifests/candidates, identity/content checks, reuse or
extraction decision, concrete reason for new extraction, source/hash and
background policy. Reuse a matching asset unchanged; changing the manual's
language or receiving a new PDF does not justify recropping.

Only small standalone icons, such as LCD/status icons and individual button
symbols, use transparency. Classify by semantic role, not rendered pixel size;
a reduced full diagram is still a full diagram. Inspect vector
paths to distinguish peripheral page/cell backdrops from product material,
button faces, shadows and screen/App content. Complete panels retain gray
backgrounds, white caption bands, borders, badges and leader geometry, even
when their text becomes native HTML. App screenshots retain complete phone
frames, status bars and bottom UI; reuse matching screenshots before extraction.

Do not remove every gray/white path by color, paint the backdrop white, or rely
on CSS blending to disguise it. This rule does not introduce a new pipeline
operator: tune the supported extraction/export in the scratchpad, preserve any
pinned approved recipe, and record which objects were retained or excluded.
For new extractions, compare all four edges with the source at 12x; for these small
icons also verify SVG transparency/PNG alpha on white and checkerboard surfaces.

## 1. Operator decision tree

Use this tree only after reuse has been ruled out and text removal is needed;
complete finished panels use crop only. Work top-down; stop at the first fit.
Every escalation needs evidence from
the drawing's actual structure (`page.get_drawings()`, span dumps), never
habit.

| # | Structure observed | Operator | Why / real case |
| --- | --- | --- | --- |
| 1 | Plain burned labels; graphics must survive | `redact_text` (graphics `preserve` → `PDF_REDACT_LINE_ART_NONE`) | The proven default. Six rounds of graphic-level deletion attempts (2026-07-15) all regressed and were rolled back to this. |
| 2 | Callout leader lines that TOUCH label text bboxes | `redact_text` with graphics `remove_if_touched` | The cascade-kill becomes the weapon: leaders die with the labels they touch (led_light / right_side_ports / front_controls, 2026-07-16). |
| 3 | Paired leaders drawn OVER artwork: white halo (≈1.8pt) + black stroke (≈0.3pt), axis-aligned | `drop_leader_strokes` (`tools/asset_pipeline/leaders.py`) | The halo already erased the art it crossed, so any patching shows; flipping the strokes' paint operator to `n` leaves geometry bytes intact and the art beneath shows through (PR #734). Identification is STRUCTURAL (paired widths, axis-aligned) — never hardcoded coordinates; a suppression-count mismatch must raise, not pass. |
| 4 | Residual stray strokes not touching any text, on a PURE WHITE area | `whiteout` | White rects on light-gray panels / heat grills / shading show as patches — that is exactly the #734 defect. Pure-white background only. |
| 5 | Structure fits none of the above | **leave the asset alone** | `main_power` / `overview/right_side_ports` got WORSE under #3 (non-paired leaders; removing white patches revealed occluded gray triangles). Scope down and report, don't force. |

Precision facts that decide between rows:

- Product engravings are vector outlines — redaction does NOT touch them;
  callout labels are true text spans — redaction kills them. Check with a
  span dump before assuming.
- Circles + knob + rays are often ONE path object whose bbox far exceeds the
  visible circle — that is why `remove_if_touched` cascade-kills dials when
  leaders don't actually touch text.
- Crop margin 0.6pt; 1.5pt sweeps neighboring table lines into the clip.

## 2. Tuning environment

- Iterate in the session scratchpad with a small script that mirrors the
  pipeline semantics (open the archived page PDF, apply the candidate
  transform, render). A full intake run (~1.5 min) is for final packaging,
  not parameter search.
- Final packaging: `python tools/asset_intake.py --asset-source-key <key>
  --asset-source-file <master> --asset-recipe data/asset_recipes/<r>.json
  --asset-output-root <out>` — intake is **package-only and never edits the
  worktree**; promotion into the repo is a separate, deliberate step.
- Verify renders at **12x zoom** (4x hides capsule nicks and thin-line
  damage). Look specifically for: white patches on non-white areas, nicked
  capsules/rings, severed body outlines, leftover leader stubs.

## 3. Known traps (each cost a round)

1. **Zero-area bbox**: a perfectly horizontal/vertical line has a
   zero-height/width rect and `fitz.Rect.intersects()` returns False —
   3 of 13 leader strokes were missed this way. Write an explicit
   overlap test for degenerate rects.
2. **CTM stack**: content-stream coordinates live under `cm` transforms —
   track the full CTM stack to compare geometry in page space, or every
   bbox comparison silently lies.
3. **Whiteout coordinate offset**: patch coordinates have a subtle mapping
   offset history; verify patch placement in the render, not the math.
4. **Gate semantics**: recipe gates are `quarantine` (first run, forces
   visual review) → `approved` with `expected_sha256` (locks bytes). App
   UI / QR / URL / localized content MUST be quarantined (schema enforces).
5. **Frozen promotion contracts**: `tools/app_ui_promotion.py` pins
   `EXPECTED_RECIPE_SHA256`; editing a pinned recipe raises
   `promotion recipe binding is not immutable`. The fix is a SEPARATE
   corrective recipe (e.g. `manual_je1000f_us_front_controls.json`) + a test
   pinning the main recipe unchanged — never rebind an approved decision.

## 4. Confirmation protocol (before any registry write)

1. Build a PIL left/right pair (old | new) per asset, at review-friendly
   scale, and send it to the operator with: asset_key, source (master page),
   new sha256, and what changed.
2. Wait for explicit confirmation per asset (numbered picks count).
3. Only then touch the registry — and follow the write-readback discipline
   from `lark-cli-bitable-ops` (attachment token non-empty on read-back).

## 5. Closing checklist (a round is not done until all boxes tick)

- [ ] **Reuse decision recorded**: searched candidates and specific reason for
      extraction are recorded; reused assets keep original bytes/source hashes.
- [ ] **Background and boundaries match the declared type**: small LCD/status/button icons
      have true transparency; complete panels keep their gray background and
      frames; App screenshots keep phone tops/status bars and all four edges.
      Product shading, markings and leaders are intact; new crops have source
      comparisons at 12x and do not include neighboring panels.
- [ ] **Web verification**: desktop/mobile show the selected asset with complete
      bounds, correctly anchored labels and no duplicated captions/step numbers.
- [ ] **Hash three-place sync**: recipe `expected_sha256` · registry 内容哈希
      12-hex prefix (`data/asset_registry.csv`) · pinned test censuses
      (`tests/test_asset_registry.py` ×2, `tests/test_asset_recipe.py`
      contract). One place stale = CI red or, worse, silent drift.
- [ ] **Registry enrollment both sides**: CSV mirror row + Feishu 插图资产表
      (`tblxFBWaDG4OYhqu`) row/attachment, read back (row id + non-empty file
      token reported). Naming contract `<asset_key>[-<lang>].{pdf,png}`;
      `overview/` prefix has no filename_prefix; a missing `v2-` file falls
      back to `renderers/latex/assets`.
- [ ] **Never delete registry rows** — debts and superseded assets get status
      flips/notes, not deletion (the J1 merge rule).
- [ ] **Consumers verified, not assumed** (grep template `asset:` refs; e.g.
      front_controls → JP/ZH app-setup only).
- [ ] **Integration swap deferred**: templates/IDML pointing at the new asset
      is a separate PR with its golden/parity rebaseline.
- [ ] **Want-list re-audit**: after any new master delivery, re-check the
      missing-asset debt rows — old debts may already be payable (the KR-8图
      lesson: all 8 keys resolved from the master; the row was fossil debt).
