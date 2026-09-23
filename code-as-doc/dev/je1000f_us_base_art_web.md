# JE-1000F US base art on the Web

Status: implemented for Web. The IDML counterpart is described in
[`idml_component_targets.md`](idml_component_targets.md).

## 1. Scope

Four of the five JE-1000F/US Operation figures render as `base-art-live-copy` on
the Web in EN, FR and ES:

| Figure | Logical art | Frozen art SHA-256 |
| --- | --- | --- |
| `operation.main-power` | `operation/main_power` | `74004806e6c0996fb77b2260c046e055194855a96bed97c519bb58c292e3b5e2` |
| `operation.ac-output` | `operation/ac_output` | `43a46a51a98773dd307ff35dd1ac684790109b2b8c437f87ceacbc3636bc1d75` |
| `operation.dc-usb-output` | `operation/dc_usb_output` | `c46c92d6ee991a400208635802b5d2682f215cacaa748a3ca73068fdb18cdec3` |
| `operation.energy-saving` | `operation/je1000f_us/energy_saving` | `9dd943d3063031c0795ff8c4b2b6aac266bfb2bff78e2250e445f27352c23a07` |

The frozen, registry-approved art is the figure's only image. Visible copy stays
owned by the source templates and renders as live, searchable HTML.

LED light keeps its approved composite. Its registered art (`operation/led_light`,
`bf4fce34…`) lost the magnifier and the hand when the extraction's text
redaction removed every graphic touching the magnifier's LIGHT label, so a card
built on it would drop the hand the composite shows. The footer-panel card LED
needs is implemented and tested (section 4); the figure switches to it once a
fixed JE-1000F/US LED base art serves every output (section 6). Every other
target is unchanged. The IDML
counterpart (the same main-power art in the production IDML) belongs to the
single-language component target, which applies it only while its sources match
the approved contract; see [`idml_component_targets.md`](idml_component_targets.md).

The AC and DC/USB figures keep the approved art with its drawn, empty
prerequisite pill. The textless AC candidate is not registered; approving it
changes the art hash and therefore requires new anchors (section 3).

## 2. Contract

`docs/renderers/contracts/web_presentation/target_overlays.json` (`je1000f-us-v1`)
declares, per figure:

- `presentation_mode: base-art-live-copy`;
- `base_art_layout` with the measured anchors, as percentages of the art box:
  - `art_sha256` — the art version the anchors were measured on;
  - `step_anchors` — one `[x, y]` per step: `y` is the drawn bracket arm, the
    label sits on it and the instruction hangs below;
  - `step_width`, optional `duration_anchor` (beside a drawn clock),
    `prerequisite_rect` (the drawn pill), `prerequisite_fill` (the drawn pill's
    measured `#rrggbb` tone, required with the rect) and `prerequisite_max_width`
    (blank art a narrow-screen pill may grow into), `footer_x` for footer-overlay
    figures, or `art_width` (the art column of the card) and `step_markers` (one
    of `bulb-lit`, `sos`, `bulb-off` per step) for footer-panel cards;
- the matching `figure_coverage.slot_status_overrides` grant.

| Figure | Anchors (x, y) | Other |
| --- | --- | --- |
| Main power | (76.5, 15.42), (76.5, 34.17); width 22.5 | duration (81.4, 48.1) beside the drawn clock |
| AC output | (84.0, 26.51), (84.0, 36.98); width 15.5 | pill `[1.14, 1.98, 42.83, 6.05]` tone `#f8f8f8`, narrow max width 55 |
| DC/USB output | (86.0, 20.28), (86.0, 31.69); width 13.5 | pill `[1.63, 2.68, 43.49, 7.32]` tone `#e8e8e8`, narrow max width 55 |
| Energy saving | — | footer text starts at x 72 under the drawn bracket line (x 76.27) |

The anchors were measured once from the frozen PNGs (bracket arms, clock and
pill bounding boxes, pill tone); the same measurement reproduces the declared
main-power and AC arms exactly. Renderers never infer geometry from pixels.

## 3. Fail-closed rules

Contract loading rejects an unknown `presentation_mode`, a mode without its exact
coverage grant (including overlays with no coverage policy), a grant outside
`required_slots`, and a `base_art_layout` with unknown keys, a malformed art hash,
missing prerequisite geometry or tone, a step/anchor count mismatch, or a
footer-panel card without its art width or with markers that are unknown or do
not match its steps. A card that marks an SOS step fails to render when its
source page declares no `sos_label`. Coverage binds each
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

A footer-panel card (built for LED; declared once its base art is fixed) puts the
lead in its own soft panel above the art and bolds its phrase through the first
colon (the IDML card's rule); the art shares the row below with numbered steps.
The art carries no numbers or step glyphs, so the Web draws them (lit bulb, SOS
badge, unlit bulb) the way the IDML card draws them natively. A one-word step
label never splits mid-word; it may overhang its step box by a few pixels and
still ends inside the art.

`mode_label` (energy saving) and `sos_label` (the LED card) live in the source
page's `.. raw:: manual-ir` `operation_panel_copy` block, which HTML conversion
drops.
Both Web paths — the whole-document IR and the per-page fallback — read them from
the same only-normalized RST and ask one rule
(`component_specs.operation_html.base_art_panel_copy`) which apply; only base-art
figures carry them, so other targets' frozen specs are unchanged.

The art is decorative for assistive technology (`alt=""`), as the approved
composite it replaces was; the instructions are live text in reading order and
the duration shorthand, step numbers and step glyphs are `aria-hidden`. At 760 px
and below the copy stacks under the art, except the AC and DC/USB prerequisites,
which stay on the drawn pill and fill it with its measured tone.

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
- DC/USB (live phase2 sync 2026-09-23T02:07Z, business review content, Web
  profile), against `main`: the EN/FR/ES pages differ only in the DC/USB figure
  and in the AC prerequisite's declared tone variable (its look is unchanged);
  the LED figure is byte-identical (still its composite). IDML for every
  JE-1000F/US target is member-identical to `main`, production and flow,
  including the active en component target.
- Browser check at 814 px and 375 px in EN, FR and ES: the DC/USB labels sit on
  their arms (within 0.02 px) on one line (the Spanish "Encendido" had wrapped
  mid-word before labels stopped breaking), no copy leaves the art, and the
  narrow-screen DC/USB pill fills with `#e8e8e8`.

## 6. Open items

- The EN source alt text reads "… operation placeholder."; Web no longer exposes
  it, but the templates and review pages still carry it for other outputs.
- The FR/ES Off instruction wraps to two lines above a clock placed for one EN
  line, so instruction type is set smaller than in the approved composites; the
  ES source copy is also longer than the copy baked into the approved ES composite.
- LED base art. `operation/led_light` (`bf4fce34…`) lost the magnifier and the
  hand; the IDML LED card meanwhile substitutes an unregistered
  `led_light_complete.png` whose right edge crops the magnifier rim and the
  wrist. A JE-1000F/US replacement extracted from the V2.0 print PDF
  (2026-07-28, page 12; PNG `483c0dcf…`) keeps the product, the whole magnifier
  and hand, and the LIGHT product marking. Registered as the target's override
  it serves every output, so it lands in its own change: the Word/PDF image
  changes, and because the formal IDML entry measures pagination from the LaTeX
  PDF, IDML page 05 changes and the approved reference-layout plan needs a
  content-change rebind. The LED card then declares that art.
- The LED step glyphs (bulbs, SOS badge) are drawn by the Web component because
  the art has none; if a future art version draws them, drop the markers instead
  of drawing them twice.
- Whole-manual visual acceptance of the published Web page remains with the
  operator.
