# JE-1000F US visual parity PR2 plan (2026-07-26)

## Outcome

Bring the native, editable JE-1000F US InDesign export into final visual
alignment with `Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf`, while
preserving the frozen review copy protected by PR #711.

The reference PDF is SHA-256
`e72b1ba01882062e261b17d5ba54a2f7c3099e5ba531a6428be13888641083f2`.

## Discovery

- PR #711 is merged at `8fad02be`; its target-local `sync_preserve_paths`
  contract remains the copy boundary for the JE-1000F US safety pages.
- The current LCD renderer already fills columns 1-3 with `HB Bg K05`; the
  remaining requested change is a small target-scoped icon reduction. The
  present outer panel height is close to the reference and must be re-measured
  after the icon change before any height adjustment.
- The editable back cover has only a narrow contact bar and no QR. Two
  hash-bound QR-only candidates exist. Because this PR's named visual authority
  is the frozen reference PDF, the reference candidate (page 58, decoded payload
  `160102000161`) is the target-local selection; the conflicting AI-master
  candidate stays quarantined.
- The three What's in the Box cards use shared fixed widths, dark K40/0.75 pt
  rules, and artwork widths that are visibly larger than the reference. These
  need governed reference-layout metrics, not source-copy changes.
- Native PR1 preflight has two real overset stories: Spanish operation flow and
  Spanish warranty. Their fixes must use language/layout geometry only.

## Non-goals

- No edits to shared RST copy or `data/phase2` source copy.
- No model-name branches in shared Python behavior.
- No finished-art page screenshots in production IDML.
- No PR1 merge-history rewrite and no PR2 self-merge.
- No committed INDD, IDML, PDF, package ZIP, `_build`, `output`, `reports`, or
  `tmp` artifacts.

## Implementation phases

1. Add a validated `icon_size_pt_by_language` LCD reference-profile token,
   project it into each target row, cap icon frames in the native table, and add
   fail-closed tests.
2. Promote only the frozen-reference QR candidate for JE-1000F US and compose
   the back cover from editable company/contact stories plus governed icon,
   divider, QR, and frame geometry.
3. Add target-scoped reference metrics for inbox artwork widths and card rule
   weight/color; keep the existing semantic assets and frozen text.
4. Correct the Spanish operation and warranty oversets using language-specific
   layout parameters/component geometry.
5. Export in an isolated build tree, finalize in Adobe InDesign 2026, compare
   affected pages against the reference, and iterate until the native gate is
   58 pages, 0 overset, 0 missing fonts, and 0 bad links.

## Safety net and verification ladder

1. `python -m ruff check build.py integrations tools tests scripts`
2. Targeted LCD, back-cover, asset-registry, inbox, and IDML export tests
3. `python -m unittest`
4. `python tools/check_maintainability_guardrails.py`
5. `python tools/check_doc_link_integrity.py`
6. `python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US`
7. Native InDesign finalization and rendered-page comparison to the frozen PDF

Production edits begin only after this plan is committed to the branch diff.

## Completion record

- LCD icons are governed at 14.2 pt for English, French, and Spanish; columns
  1-3 remain light gray and the existing approved row-height contract remains
  unchanged.
- The inbox cards retain editable labels and semantic artwork. Cable/document
  artwork is reduced to 40/38 pt and the card outline uses the light K10 rule.
- The frozen-reference page-58 QR (`160102000161`) is promoted only for
  JE-1000F US. The editable back cover now carries the reference geometry,
  contact copy, divider, native line icons, and QR; the conflicting AI-master QR
  remains quarantined.
- Native InDesign finalization passed with 58 pages, 0 overset stories, 0
  missing fonts, and 0 bad links. The previous Spanish operation/warranty
  oversets do not reproduce in the final contract-bound build.
- Rendered pages 6, 8, 9, 24, 42, 45, 55, and 58 were visually inspected
  against the frozen reference. The review ZIP and portable linked-IDML ZIP
  both pass archive integrity checks.
