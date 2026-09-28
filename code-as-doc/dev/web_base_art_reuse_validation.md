# Base-art Web reuse: bounded flow option

Date: 2026-09-27. Engineering baseline:
`bd201fc237825acf49ea15471ca5c63bf3d90b85` (auto-manual main).

## Scope and interface

The existing US sample is six slots per language, not a whole-book conversion:
`operation.main-power`, `operation.ac-output`, `operation.dc-usb-output`,
`operation.energy-saving`, `operation.led-light`, and `reference.charging-car`
in EN/FR/ES. Their art identities and original anchors are in
[the US contract record](je1000f_us_base_art_web.md).

A second target must keep the exact coverage grant and frozen-art hash checks.
Neither an attachment filename nor the US sample approves another market's
sockets, model drawing, source text, or language. The new option is Web-only;
no shared ComponentSpec, IDML, source table or target grant changes here.

For the main-power, AC and DC/USB `status-right` figures, container-free art can
use this existing mode with a bounded layout option:

```json
{
  "layout": "status-right",
  "presentation_mode": "base-art-live-copy",
  "base_art_layout": {
    "art_sha256": "<64 lowercase hex characters of the approved frozen art>",
    "copy_layout": "flow"
  }
}
```

`copy_layout` accepts only `flow`, on `status-right`. The layout must contain
exactly `art_sha256` and `copy_layout`: step anchors, prerequisite rectangles,
widths, duration anchors and all other fixed geometry are rejected. Omitting
`copy_layout` retains the existing anchored behavior. The exact
`figure_coverage.slot_status_overrides` grant and `required_slots` remain
mandatory; mismatching packaged art bytes still fail assembly/replay.

The existing source fields remain authoritative:

- `step_ids` identifies the ordered steps; each has one summary or a label and
  instruction pair. No wording is copied into CSS or layout JSON.
- `capture_prerequisite` captures the preceding source paragraph once.
- `capture_following_lines` captures only the declared supporting lines. For
  JE-1000F main power this is three; the following energy-saving line remains
  outside the figure. Other targets must use their own actual source structure.
- Reading order is prerequisite, artwork/steps, supporting copy. Art and steps
  share a grid row on desktop and stack at 760 px and below. Text height is
  content-driven, without clipping, line clamps or an art-relative text box.
- The flow art must exclude the old fixed text containers, step brackets and
  clock. Preserve market-correct product details and necessary operation lines
  through the target's extraction/review process.

The existing CSS clock glyph is reused. Its shorthand is derived from each
step's numeric seconds value, including German `Sekunden`; a `7 s` instruction
produces `7s`, not `3s`. The original instruction remains unchanged, and the
clock/value are `aria-hidden` to avoid reading the same duration twice.
This is a bounded seconds recognizer, not a general time parser.

The actual German energy-saving source says
`Halten Sie beide Tasten länger als 3 Sekunden gedrückt.` Previously its footer
lost the shorthand, while using the same wording with a duration anchor failed.
The regression test reproduces both failures before the compatibility fix.
Main-power's existing `3 s lang gedrückt halten.` already worked.

## Current US publication audit

GitHub API inspection pinned Hello-Docs main to
`45a085eccf3d68dca27573c257eebfc3ffeeba65`. Its US publication metadata reports
version 2.5, built 2026-09-24. Each locale's source Markdown contains exactly the
six base-art figures above. The six unique art files were fetched by Git blob
identity and their bytes rehashed against the full art SHA-256 in the frozen
path; all six match the US record.

| Locale | Frozen source Markdown SHA-256 |
| --- | --- |
| EN | `b623dee0d8d057f43c29be5768241ac17e30369ef0f9ceb43557e99ebb55075d` |
| FR | `843efbe3b8c9ab24401c04760e8d046a43ce762acfae1c5ea2c0d7a634d1ebf8` |
| ES | `9a8524bc97127d1c9b50ea82522ba54a3a8fe04067bf71890063e20dd7b203c6` |

Operation and Charging fragments for all three US languages are byte-identical
before/after this change (six pages, eighteen base-art figures), using the same
review RST, composite fixture and Python environment on both sides.

Earlier in this task, local Playwright sampled the live US pages at 1280 px and
375 px. The first load missed some FR/ES assets/styles. One reload with image
`decode()` yielded six nonbroken base-art images per locale at both widths and
no document horizontal overflow; remaining failed requests were RTD adverts.
Screenshots were retained as auxiliary evidence. These are existing US pages,
not a deployment of the new flow option, and this was not CUA verification or
whole-book visual acceptance. Subsequent CUA in-app and Chrome entry attempts
each timed out; no further browser fallback was used. New flow layout visual
acceptance remains separate from DOM/source-copy tests.

## Verification and boundaries

Validation uses an isolated Python 3.12 environment installed from the existing
`requirements.lock`; no repository dependency pins or other worktree environment
were modified. An initial run against the old shared virtualenv failed because
it carried PyMuPDF 1.28.2 instead of the recipe pin 1.28.0, plus a flow-output
smoke-test failure. All affected modules pass in the matched environment.

The targeted suite covers flow layout rejection, German wording, source-value
clock derivation, long supporting copy preserved once, component replay with
residual lines, hash mismatches, and unchanged US output. Required gates are
recorded with the PR; fixture validation does not approve target artwork.
The final flow implementation passes 166 targeted tests and the full 4,680-test
suite (22 skips) in that locked environment. Ruff, maintainability guardrails
and documentation links pass. Guardrails retain six existing stale baseline
entries; no threshold or baseline was changed.
The US build check reads the existing JE-1000F/US phase2 snapshot through
`--data-root` and writes only isolated staging. Fourteen CSV hashes are retained;
this is local snapshot validation, not a fresh live-Base read or write.

Task evidence is retained under `.tmp/base-art-reuse/` in the A-line worktree:
`discovery.md`, `us-parity.json`, `remote-audit.json`, `remote-art-hashes.json`,
`snapshot-hashes.json`, browser logs/screenshots, and validation logs. These
local artifacts are not published assets.

`preview/index.html` is a self-contained local layout review with its candidate
PNG beside it. It labels the EN JE-2000F candidate separately from the DE
long-copy stress example, which deliberately borrows the EN art and is not a
DE target proof. Source parameters remain placeholders; test-only additional
text is marked. The preview has not passed browser visual acceptance.

EU en/de target entries, candidate art approval and target visual acceptance
belong to the separate target changes. JE-2000F candidate extraction is also
separate. This shared change does not merge, publish, promote nine-language
attachments, retire composites, or claim that either EU target is live.
