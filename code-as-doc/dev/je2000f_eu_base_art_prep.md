# JE-2000F/EU Operation base-art candidate, EN and DE

Status: six **quarantined candidate illustrations** for a three-slot Web pilot.
They are not registered assets, published figures, or an approval of a new AI
master. The first pilot covers only main power, AC output, and DC/USB output.

## Source and comparison

The source for these candidates is the currently published 102-page V2.0
EU/UK PDF, DingTalk file node `20eMKjyp81Rg14l4FebQL1ZwWxAZB1Gv`, named
`Jackery Explorer 2000 User Manual (JE-2000F) EUUK V2.0-2026-08-04.pdf`.
Its downloaded SHA-256 is
`6b4af85236ccfee0f4d24ad55ee8b24684d023982b5da216023d4f716f183f3d`,
matching `manual_sources/JE-2000F/EU/en/2.0/source_manifest.json` and the
existing extraction recipe. The candidate extraction is reproducible with
[`manual_je2000f_eu_base_art_candidate.json`](../../data/asset_recipes/manual_je2000f_eu_base_art_candidate.json)
and `tools/asset_intake.py`; that recipe remains `quarantine` and
`build_eligible=false`.

The DingTalk `Ai文件（源）` row for JE-2000F has an additional 170-page,
42,495,585-byte `HTE154-EU-9国语言-0924.ai` attachment (downloaded SHA-256
`eb899f4407517869e1a0405ce2b2ed6daa76196f23197ad03fb0e295d39d84e6`).
It is marked `最新` in that table. Its EN Operation pages 13–14 have the same
extracted text as published PDF pages 11–12; DE pages 67–68 differ in their
printed page numbers from PDF pages 59–60. The figure crops also show small
pixel differences at 4×. Neither the row label nor these four-page comparisons
establish a whole-book approval or that newer specification fixes are present.
The AI attachment was not used to make these candidates and must not overwrite
the frozen published source.

## Candidate evidence

All output PNGs are 12× native PDF crops from the verified V2.0 source. Each
`art_sha256` below is the exact candidate byte hash, for a future target-scoped
binding. The relative paths are evidence files, not production Web paths.

| Language / slot | PDF page | Crop pt | Candidate SHA-256 |
| --- | ---: | --- | --- |
| [EN main power](../../data/asset_evidence/je2000f_eu_base_art/en_power.png) | 11 | `[34,82,250,175]` | `3dcd31b33a077179fb5f0fa452a2d2d07178c974611be89a3c4e3affe944be12` |
| [EN AC](../../data/asset_evidence/je2000f_eu_base_art/en_ac.png) | 11 | `[34,290,340,450]` | `e605d4e1634666ec9e0dd0b7719809160584b92c193f92b9509ed126fc98e6f9` |
| [EN DC/USB](../../data/asset_evidence/je2000f_eu_base_art/en_dc.png) | 12 | `[34,50,340,211]` | `503a5f9a81cf4e8a4223134793147d9ddabbd033490ac5f6eb7c249351c7b8fa` |
| [DE main power](../../data/asset_evidence/je2000f_eu_base_art/de_power.png) | 59 | `[34,82,250,175]` | `4307b2bbcda7f933d35713a1c66e0dda1d4ebbd69bdfe6a9d33fe366ee7fc3db` |
| [DE AC](../../data/asset_evidence/je2000f_eu_base_art/de_ac.png) | 59 | `[34,290,340,450]` | `68ebc82bf7234f0060bb650c2bb503853abee26331655e250224ed11cc1a32c4` |
| [DE DC/USB](../../data/asset_evidence/je2000f_eu_base_art/de_dc.png) | 60 | `[34,50,340,211]` | `d82b7582b8b9b0fe392f7a2903e5babb5239dd397667624bf563a4d41aaa8fa4` |

The main-power crop keeps the product, the POWER button magnifier, the hand,
and the product-to-button leader. It excludes the outer panel. Whiteouts remove
the grey standby box, its separate triangle, and the right-side bracket/leader;
the clock is outside the crop. EN and DE need different whiteout coordinates
because the DE box and bracket are lower and farther left. The AC and DC/USB
crops retain the relevant output port, regional socket, hand, and equipment
connections. Text spans are redacted with graphics preserved. Whiteouts remove
the right step bracket and its outgoing horizontal line, plus the DC/USB
prerequisite pill; the AC pill is outside
its crop. Device markings such as `Jackery`, `POWER`, `AC`, and `DC/USB` remain
part of the product drawing, not the translated instructions.

The source EN figure draws UK sockets and the DE figure draws Schuko. Both have
one AC power button. Reusing JE-1000F/US art or its measured anchors would
depict the wrong target. The two languages also need separate assets even after
the editable text is removed.

## Copy and binding requirements

The current EN/DE source templates already contain the live text. Each figure
has two steps. Main power is `On: Press once` / `Off: Press and hold for 3s`
in EN and `Ein: Einmal drücken` / `Aus: 3 s lang gedrückt halten` in DE.
AC and DC/USB are each on/off by one press in both languages; each has a
prerequisite sentence. Main power has **four non-empty** following source
lines: default standby time, automatic shutdown, Jackery App setting, and the
Energy Saving Mode shutdown. The source also has an empty `|` separator before
these four lines. AC and DC/USB each have an empty `|` before their paired
steps. The Web transform must skip the separators when counting steps and
supporting copy; all four main-power lines must appear once as ordinary HTML
after the figure. The shared portable-power-station contract currently
captures only three supporting lines; this target needs four.
The printed clock/`3s` is decoration; the Web component can draw its existing
CSS clock next to a duration derived from the step text.

The scoped `base-art-live-copy` binding should use the Web flow layout with
only `art_sha256` and `copy_layout: flow` in `base_art_layout`, plus exact
per-slot coverage grants. The candidate PNGs must first be promoted to
target-scoped Web asset paths and the EN/DE illustration manifests must stop
substituting the old full-frame panels. The current EN formal source manifest
pins its illustration manifest hash and must be re-locked with any approved
binding. The shared contract and `target_overlays.json` are owned by the other
pilot windows; no shared renderer, CSS, schema, source table, review derivative,
or live Base is changed here.

The first isolated preview against the real EN template found a parser
misalignment: AC and DC/USB treated the leading empty lines as steps, and
main power counted its separator as supporting copy, omitting the Energy
Saving sentence. This preview is **not accepted**. The shared Web component
owner is correcting the flow-only parser; the next preview must check every
source sentence exactly once in EN and DE.

Full-target figure coverage also needs a JE-2000F/EU Overview instance.
`overview_component_instances.json` currently has none, although both
languages already have finished `overview_front.png` and `overview_side.png`
in their Web illustration manifests. Loading a figure-capable JE-2000F/EU
contract with its current Overview source pattern fails with `expected one
overview instance for 'JE-2000F'/'EU'; found 0`. A preview-only empty Overview
source pattern can isolate the three Operation figures, but it cannot support
a production coverage claim. A correctly bound Overview instance and its
derived coverage slots require separate review before the full-target gate
can pass.

## Verification and acceptance boundary

The asset pipeline packaged all six images from the hash-verified source with
the recipe's `quarantine` gate. Visual inspection at 12× found the product
outlines, fingers, leaders, and socket types intact; no translated instruction,
step bracket, printed clock, or fixed standby text box remains in the candidate
art. [Six source/candidate pairs](../../data/asset_evidence/je2000f_eu_base_art/review_pairs.html)
show the actual V2.0 PDF crop beside each candidate.

An isolated Web preview with the shared renderer at commit `d6b65465` now uses
the real EN/DE Operation templates and these candidate images. The preview
replaces two placeholder durations with the published PDF values (EN `2 hours`
/ `12 hours`; DE `2 Stunden` / `12 Stunden`) for readability. The renderer
extracts both steps in each figure, the AC/DC prerequisite once per figure,
the main-power duration as a CSS clock plus live `3s`, and all four supporting
lines in order inside the main-power figure. The neighboring IEC/EN/UL
62368-1 caution appears once after the DC/USB figure in each delivered HTML
preview and zero times inside the three figures.

Review the [EN flow preview](../../data/asset_evidence/je2000f_eu_base_art/flow_preview_en.html)
and [DE flow preview](../../data/asset_evidence/je2000f_eu_base_art/flow_preview_de.html).
Auxiliary screenshots made with local headless Playwright Chromium are available
for
[EN desktop](../../data/asset_evidence/je2000f_eu_base_art/flow_preview_en_desktop.png),
[EN mobile](../../data/asset_evidence/je2000f_eu_base_art/flow_preview_en_mobile.png),
[DE desktop](../../data/asset_evidence/je2000f_eu_base_art/flow_preview_de_desktop.png),
and [DE mobile](../../data/asset_evidence/je2000f_eu_base_art/flow_preview_de_mobile.png).
At 1280 px and 390 px, these three-figure screenshots had no horizontal
overflow. They were captured before the neighboring caution was appended to
the delivered HTML; they are auxiliary layout evidence, not the agreed CUA
browser acceptance. CUA visual acceptance remains pending. The isolated HTML
and screenshots do not pass the formal full-target figure gate, review an
entire manual page, or approve the candidate assets for production. Explicit
visual approval remains required before registry enrollment or production
binding.
