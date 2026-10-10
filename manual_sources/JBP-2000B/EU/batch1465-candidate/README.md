# JBP-2000B EU batch 1465 source-review candidate

This new immutable Git-only source candidate applies 45 verified paragraph/note amendments to the current native semantic IR. It never edits `docs/publish/**`, historical sources, phase2 schema, live Base, or another model. English is already correct and is preserved at its published source revision.

Counts: fr 7, es 6, de 5, it 6, uk 10, pt 5, nl 3, pl 3. `corrections.json` records exact current → delivered text, physical PDF page and frame. Every proposed paragraph was matched against the delivered 80-page revised PDF; its SHA-256 is in `source_manifest.json`. `decisions.json` retains unchanged context and mapping decisions.

Web adjustments preserve the existing inline connection icon, omit print-only formatting and review colors, preserve the Italian web spelling `un'uscita` instead of reintroducing the delivered typo `ucita`, and retain the German three-pack stacking caution. 200 mm ventilation and anti-tip guidance remain intact. All 51 unique image files have been byte-verified against the baseline; no artwork was modified.

The eight `web/` packages contain corrected source IR plus generated MyST, existing asset bytes and original Sphinx scaffolds. Component carrier and semantic slots were synchronized, then checked by the existing renderer. Nine-language baseline/candidate IR checks, native render replay and strict Sphinx HTML compilation pass. These are review outputs, not a sealed release. The IR intentionally carries `publication_eligible=false` and pending review status; historical approval/evidence must not be reused as approval of the revised text.

Remaining gates: operator proofreading/source review; fresh component, source-bound symbol and caption-frame admission; source/IR provenance and language-release evidence reseal; reviewed Git-only handoff through the existing generated `publish -> main` Web lane; operator merge; RTD build and served-text readback. Do not re-seed the US review branch for this EU target. A live build-table read returned the US record `recvtchyLmtGv1` only; do not infer EU absence or fabricate a queue row.

The live source and existing package README confirm Git-only source ownership; no Feishu write is part of this candidate. Automated publication must continue to reject it until the pending evidence is completed.
