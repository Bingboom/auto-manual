# JE-1000F US base art on the Web

Status: implemented for Web; IDML follows in a separate change.

## 1. Scope

Three JE-1000F/US Operation figures render as `base-art-live-copy` on the Web in
EN, FR and ES:

| Figure | Logical art | Frozen art SHA-256 |
| --- | --- | --- |
| `operation.main-power` | `operation/main_power` | `74004806e6c0996fb77b2260c046e055194855a96bed97c519bb58c292e3b5e2` |
| `operation.ac-output` | `operation/ac_output` | `43a46a51a98773dd307ff35dd1ac684790109b2b8c437f87ceacbc3636bc1d75` |
| `operation.energy-saving` | `operation/je1000f_us/energy_saving` | `9dd943d3063031c0795ff8c4b2b6aac266bfb2bff78e2250e445f27352c23a07` |

The frozen, registry-approved art is the figure's only image. Visible copy stays
owned by the source templates and renders as live, searchable HTML. DC/USB and
LED keep their approved composites; every other target is unchanged. The IDML
counterpart (the same art in the production IDML) and the single-language IDML
component routing were split out of #1220 and are not part of this change; the
IDML output for JE-1000F/US is byte-identical with and without it.

The AC figure keeps the approved art with its drawn, empty prerequisite pill.
The textless AC candidate is not registered; approving it changes the art hash
and therefore requires new anchors (section 3).

## 2. Contract

`docs/renderers/contracts/web_presentation/target_overlays.json` (`je1000f-us-v1`)
declares, per figure:

- `presentation_mode: base-art-live-copy`;
- `base_art_layout` with the measured anchors, as percentages of the art box:
  - `art_sha256` — the art version the anchors were measured on;
  - `step_anchors` — one `[x, y]` per step: `y` is the drawn bracket arm, the
    label sits on it and the instruction hangs below;
  - `step_width`, optional `duration_anchor` (beside a drawn clock),
    `prerequisite_rect` (the drawn pill) and `prerequisite_max_width` (blank art a
    narrow-screen pill may grow into), or `footer_x` for footer figures;
- the matching `figure_coverage.slot_status_overrides` grant.

| Figure | Anchors (x, y) | Other |
| --- | --- | --- |
| Main power | (76.5, 15.42), (76.5, 34.17); width 22.5 | duration (81.4, 48.1) beside the drawn clock |
| AC output | (84.0, 26.51), (84.0, 36.98); width 15.5 | pill `[1.14, 1.98, 42.83, 6.05]`, narrow max width 55 |
| Energy saving | — | footer text starts at x 72 under the drawn bracket line (x 76.27) |

The anchors were measured once from the frozen PNGs (bracket arms, clock and
pill bounding boxes). Renderers never infer geometry from pixels.

## 3. Fail-closed rules

Contract loading rejects an unknown `presentation_mode`, a mode without its exact
coverage grant (including overlays with no coverage policy), a grant outside
`required_slots`, and a `base_art_layout` with unknown keys, a malformed art hash,
missing prerequisite geometry, or a step/anchor count mismatch. Coverage binds each
base-art slot to its packaged `assets/…` path and SHA and rejects a layout whose
`art_sha256` differs from the frozen art. Document validation rejects base-art
evidence that disagrees with the package asset manifest, and cold replay then
re-hashes the packaged bytes.

Coverage summaries emit a `base-art-live-copy` count only when it is non-zero, so
every report without such a slot keeps the exact v1 shape: the eight stored
Hello-Docs Web packages validate unchanged.

## 4. Rendering

`tools/web_base_art_operation.py` runs only for base-art figures. The art and its
overlays share one canvas; the overlays are transparent so no drawn line, pill or
clock is covered. Summary steps such as `On: Press once.` split at the first colon
into label and instruction (the IDML row rule); nothing is dropped when no colon
exists. Main power adds the duration beside its drawn clock, taken from the step
copy (`3s`, `3 secondes`, `3 segundos`). Energy saving renders a footer under the
art with the duration, the source `mode_label` and the action.

`mode_label` lives in the source page's `.. raw:: manual-ir` `operation_panel_copy`
block, which HTML conversion drops. The Web loader reads it from the same
only-normalized RST and adds it as an optional `mode_label` slot for base-art
figures only, so other targets' frozen specs are unchanged.

The art is decorative for assistive technology (`alt=""`), as the approved
composite it replaces was; the instructions are live text in reading order and
the duration shorthand is `aria-hidden`. At 760 px and below the copy stacks under
the art, except the AC prerequisite, which stays on the drawn pill and fills it.

## 5. Verification

- Unit and cold-replay tests cover the contract grant/layout negatives, sparse
  coverage summaries, art-hash binding, replay evidence tampering, summary
  splitting, footer composition and `.. only::` handling of panel copy. Against
  the #1220 code, the missing-grant and unknown-mode contract cases and the
  replay-evidence tamper case are not rejected, and all eight stored Hello-Docs
  packages fail summary validation; here they are rejected or pass as intended.
- Production-equivalent build (live phase2 sync, business review branch, Web
  profile): the EN page differs from the published 2.4 page only in these three
  figures.
- Browser check at 814 px and 375 px in EN, FR and ES: labels sit on the measured
  arms, no copy crosses the art edge, the prerequisite is centred in the pill, and
  the longest FR/ES Off instruction ends 3.7 px above the drawn clock.

## 6. Open items

- The EN source alt text reads "… operation placeholder."; Web no longer exposes
  it, but the templates and review pages still carry it for other outputs.
- The FR/ES Off instruction wraps to two lines above a clock placed for one EN
  line, so instruction type is set smaller than in the approved composites; the
  ES source copy is also longer than the copy baked into the approved ES composite.
- Whole-manual visual acceptance of the published Web page remains with the
  operator.
