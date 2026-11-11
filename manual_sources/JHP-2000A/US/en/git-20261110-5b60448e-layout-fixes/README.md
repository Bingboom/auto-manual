# JHP-2000A US English LED and contact-frame layout correction candidate

Derived from `../git-20261103-5b60448e-full-source-alignment-release`; the published package and its approval/evidence stay byte-identical. The authoritative PDF, all wording and all other artwork stay unchanged. This is a review candidate, not a publication authorization.

## Discovery and correction plan

The operator marked the LED steps for alignment and reported “二维码缺了上边框” on the published US English page on 2026-11-10. The old LED overlay spaces an ordered list by flowing text height, so each label drifts above its printed numbered circle. The contact crop begins at y=460 pt, below the QR frame's top stroke (459.60983 pt with 0.25 pt width).

1. Keep the original LED bitmap unchanged. Center each native list item independently on the three numbered-circle centers measured from PDF p13: y=418.44202, 442.18858 and 467.22688 pt. The list remains semantic and selectable; labels share one left edge.
2. Reuse the contact panel's existing derivation and stripping rectangles. Expand only its crop top from 460 to 459 pt so the complete original QR border is included. Rebase native contact-text percentages to preserve their source-coordinate positions. Preserve every QR pixel.
3. Rebuild through the existing package `build_content.py`, `refresh_manifest.py` and `rebuild.py --output <unused directory>` entrypoints; strict Sphinx, source-copy/asset parity, cold replay, desktop and narrow viewport checks.

No shared component, template, live Base, release approval, active publication mapping or deployed page is changed. Existing historical source concerns and layout decisions remain in `source/differences.md`. Current verification is recorded separately under `evidence/layout-fixes/`.

## Asset replay boundary

Unchanged assets are byte copies of the parent release, not newly extracted. Only `source-contact-frame.png` is rerendered with the existing `render_panel` operation at its original 5x resolution. Cold replay consumes the hash-locked `assets/` inventory; it does not rerun the historical bulk `derive_assets.py` intake.
