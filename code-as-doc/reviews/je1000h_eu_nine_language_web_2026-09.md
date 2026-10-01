# JE-1000H EU: add Portuguese, Dutch and Polish

Status: active

## Discovery (2026-09-30)

- Worktree: `/Users/pika/.codex/worktrees/6985/auto-manual2`; branch:
  `feat/web-je1000h-eu-nine-languages`. The initial detached checkout was clean.
- Current remote engineering main commit:
  `40123121575198c2eb1cf9e02ac084941858c796`. Ordinary Git HTTPS fetch failed
  after 75 seconds (github.com:443). Exact Git objects were verified locally.
  The start-branch wrapper switches shared local main, already checked out in
  another window, so this isolated branch was created directly from the verified
  remote commit without changing another checkout or its branch.
- Source: `HTE159-EU-9国说明书-0928(1).ai`, SHA-256
  `8bcb378fd0505237d91d5aa201d8bc0e84ee392963bfa6a73d32b8ed90b68feb`;
  161 PDF-compatible pages with selectable native text. Cover: JE-1000H,
  Jackery Explorer 1000 Plus, `Version: JAK-UM-V1.0`.
- Body page ranges: en 8–24, fr 25–41, es 42–58, de 59–75, it 76–92,
  uk 93–109, pt 110–126, nl 127–143, pl 144–160. `uk` means Ukrainian.
  Prefaces are on pages 2–4; print contents 5–7 are excluded; page 161 is
  the common manufacturer/declaration tail.
- Published Hello-Docs manifest currently contains six JE-1000H/EU targets
  (en/fr/es/de/it/uk), version `git-20260930-4e7df369-lcd-icons`.
  The existing engineering frozen source is the different EUUK V2.0-2026-08-03
  PDF (SHA-256 `07e9ac4b9faabd0852f61702df06f2837caa952c2fa28151b599ad930b1c0bcc`).
  No approval or content is transferred between those revisions.
- Reusable path: `tools.frozen_pdf_web` → native geometry intake →
  `manual-ir/v2` with registered ComponentSpec → public Web renderer →
  strict Sphinx. Target-local geometry allows 14 chapters including battery
  expansion. Existing JE-1000H LCD icon provenance is available for comparison.
- Product-specific requirements: AC1 and AC2, separate left and right views,
  battery expansion, 26 LCD rows including connected batteries. This is not
  a JE-1000F/JE-2000F geometry or artwork substitution.

## Scope correction and implementation plan

The operator clarified: “已经有现成的网页文档里啊，补充语言而已” and
“不要全新处理啊”. Only **pt/nl/pl** are now in scope. Existing
**en/fr/es/de/it/uk** remain byte-identical. The earlier nine-language/English
rebuild plan is superseded before any production source edits.

1. Pin the six published sources and existing English HTML/IR as the layout,
   semantic component and asset baseline. Do not rebuild those editions.
2. Reuse the current native PDF intake, manual-ir/v2, ComponentSpec and common
   Web renderer. Author only source-local geometry and bindings for pt/nl/pl,
   taking native text from physical pages 110–126, 127–143 and 144–160.
3. Reuse verified JE-1000H/EU artwork and shared buttons/icons. Extract only
   necessary locale-specific or changed illustrations; record provenance,
   transparency and before/after evidence. Do not re-extract matching base art.
4. Build one complete new-language candidate, verify it against native source
   and existing English layout, inspect desktop/narrow browser layouts, then
   complete the other two using the same existing intake path.
5. Validate source coverage, tables, battery chapter, AC1/AC2, locale-specific
   warnings/legal subjects and all figure bindings. Record source defects
   without unapproved corrections. Deliver three complete previews and evidence
   that the six existing editions are unchanged; open an engineering PR only
   after applicable checks pass.

The JAK-UM-V1.0 versus EUUK V2.0 source difference is a review item; it never
justifies upgrading or replacing an existing language. There is no new parallel
renderer, HTML generator or complete book pipeline.

Non-goals: production source-table writes, approval-state promotion, schema or
workflow changes, other worktrees, merge, Hello-Docs code PR, or publication.
Candidate geometry/source work does not require editing shared CSS. Any necessary
shared adapter fix must be a minimal separate commit and report its conflict
surface with JS-100I. The asset skill's registry confirmation applies only to
promotion; this request authorizes local candidates and explicitly defers it.

Checks: source SHA/page inventory; native line/table coverage; missing/foreign
assets; source-matched parameters; public IR validation and cold replay; strict
Sphinx; desktop and narrow browser inspection and overflow/missing-image checks;
`git diff --check`; documentation links. Any shared logic change also requires
Ruff, focused and full unittest, maintainability guardrails and relevant build
checks. Static checks are never reported as browser acceptance.

## Status

The complete local candidate is `reports/je1000h-eu-nine-language/candidate-23`
and its strict Sphinx output is `preview-23`. Each locale contains 16 chapters:
the preface, 14 body sections, and the verbatim common declaration/manufacturer
tail. Only pt/nl/pl were added. No candidate is approved for publication.

The source package and reproduction instructions are in
[the three-language package](../../manual_sources/JE-1000H/EU/three-language/git-20260930-8bcb378f-intake/README.md).
The [local acceptance report](../../reports/je1000h-eu-nine-language/README.md)
links previews, component mapping, source coverage, browser screenshots,
asset QA, cold replay, and the six-language unchanged evidence.

## Review fixes and retained source issues

- Source geometry now excludes adjacent LCD descenders and preserves App 2.5
  prose whose number appears only below its screenshot. Two explicit optional
  adapter fields retain old defaults; no shared renderer or CSS was changed.
- All three locales bind AC1/AC2 separately and include the expansion-battery
  chapter. Native solar warnings, warranty columns and full accessory drawings
  survive the shared components without extra headings or duplicate captions.
- The energy-saving panel now retains its complete native frame, top gray
  note, clock and close label spacing. It uses the existing ReferenceFigure
  component with semantic copy; no extra live clock is drawn. This supersedes
  the earlier stripped-art/footer fix. Main-power retains its native clock
  and adds only the live duration.
- AC/DC prerequisite extraction rectangles were initially reused as display
  widths, obscuring button circles. Narrower pills still covered leaders on
  phones. The final geometry leaves each prerequisite in native paragraph flow
  immediately before its operation card, preserving the text exactly once and
  keeping the illustration clear at both widths. Other operation/App labels
  retain the shared responsive presentation.
- PT `12 V⎓10 A máx.` was recovered from native Illustrator textFrames[1332]
  and matching artboard coordinates; the scoped recovery ledger preserves the
  original raw PDF inventory. Its finished overview bitmap retains the PDF
  font rendering limitation; no guessed redraw was made.
- Source defects retained for review: PT `ON` / Spanish `Apagado`, PT specs
  listing three AC outlets while the operation text describes two pairs, and
  some trademark superscripts positioned after the extracted paragraph.
  The source version differs from the six published editions.
- The connected-battery LCD icon has been re-extracted from native page 114
  at the operator's request: 261×142 RGBA replaces the blurred 43×34 RGB image
  and removes the neighboring table edge. The old six-language assets remain
  unchanged. Standalone extracted PNGs have alpha; the restored complete panels
  retain their native backgrounds as explicitly requested. No artificial
  upscaling is claimed.

## Whole-panel correction (2026-10-01)

The operator explicitly rejected background removal for large diagrams. Six
reference figures per locale (UPS, battery stack, accessories, wall/solar/car
charging) now use their own native complete panel, retaining gray backgrounds,
white caption bands, rounded/dashed frames and the cart badge. All 18 entries
use a crop-only corrective recipe. The existing ReferenceFigure component
carries semantic native copy without duplicate visible captions. A minimal
opt-in adapter change checks locale/page for `captions_embedded: true`; all
other assets retain their previous caption behavior. No renderer or CSS change.

36 browser checks cover all panels at desktop/mobile widths. Excluding only
these six figures, each locale's main HTML is identical to candidate-09; all 46
existing six-language source files still match their pinned hashes. See the
[final comparison evidence](../../reports/je1000h-eu-nine-language/evidence/panels-15/unchanged-body.json).
The final packages replay with source/AI reads blocked and identical Markdown.
This preserves print text within each panel; those labels are not separately
editable HTML, and mobile readers may need to zoom.

Current validation: eight reference tests, three native builds plus strict
Sphinx, formal 18-panel intake, Ruff, maintainability, docs links and the
fixture-backed US check pass. Full unittest passed 4,958 tests in 697.121s
(19 skipped); the prior external-fixture failure below did not recur. Final
opt-in compatibility was rechecked by the reference tests. No external fixture
was changed. There is no PR, remote write, merge, Bitable write or publication.

## Energy-saving panel follow-up (2026-10-01)

The operator explicitly requires the gray outer frame for this operation panel.
PT/NL/PL now use crop-only native panels from pages 117/134/151, preserving
the top gray note, bracket, single clock and original close label spacing.
The existing ReferenceFigure component keeps the extracted semantic copy.
No shared renderer, CSS or Python logic changes were needed. The style contract
now names the energy-saving combination panel explicitly.

Three native imports and strict Sphinx builds, source/asset hash checks,
component coverage and guarded cold replay pass. Nine browser checks cover
1280/840/390 widths with the energy image loaded, no extra footer and no page
overflow. Three offscreen App images remain normally lazy-loaded. Excluding
only the energy figure, each locale's main HTML and CSS match preview-15;
all 46 existing six-language files are unchanged. See
[follow-up evidence](../../reports/je1000h-eu-nine-language/evidence/energy-panel-18/validation.json).
The full suite was not repeated for this source-only follow-up. No publication.

## Connected-battery LCD icon follow-up (2026-10-01)

The later LCD row 21 re-extraction (candidate-19) also passes three strict builds,
all 39 native PDF pins, guarded cold replays and nine browser width/locale checks.
Only the connected-battery image URL changes versus preview-18; all other main
HTML/CSS and the 46 previous-language source files remain identical. The export
is taken from the current master, not an enlargement of the old raster.
See [LCD re-extraction evidence](../../reports/je1000h-eu-nine-language/evidence/lcd21-19/validation.json).

## Left-side overview crop follow-up (2026-10-01)

The three left-side overview images now start at 266pt rather than 269pt,
retaining the complete handle, top outline and upper right corner below the
native heading. Other crop edges and source annotations remain unchanged.
Three strict builds, source/artwork hash checks, guarded cold replays and six
840/390 browser checks pass. Only this image URL differs from preview-19;
the LCD/energy fixes and all 46 existing six-language sources are preserved.
See [crop evidence](../../reports/je1000h-eu-nine-language/evidence/left-view-21/validation.json).

## App background and shared screenshot follow-up (2026-10-01)

Restored the native gray rounded App control panel and aligned its four live
labels to locale text bounds. Steps 2.3–2.5 now reuse the complete existing
JE-1000H EU App screenshot unchanged, including phone tops and status bars.
Three strict builds, 60 native PDF hashes, source pins, guarded cold replays and
six desktop/mobile browser checks pass. Outside the two App figures, main HTML
and CSS match preview-21; all 46 existing six-language sources remain unchanged.
No shared code or CSS changes, publication or remote writes were made.
See [App validation](../../reports/je1000h-eu-nine-language/evidence/app-panel-23/validation.json).

## Earlier validation and PR boundary (historical)

All three native imports, strict Sphinx builds, component coverage gates,
native-line presence audits, guarded cold replays, formal asset intake,
focused regressions, Ruff and maintainability checks passed. Existing
JE-1000H source files and shared renderer/CSS are unchanged. The fixture-backed
US build check passed; the ordinary command could not find local ignored
`data/phase2/Spec_Master.csv`. This says nothing about the live Base.

The full `python3 -m unittest` run executed 4,957 tests in 939.912 seconds,
with 2 failures, 20 errors and 22 skips. All failures/errors hit the optional
JE-1000F external native-source fixture: `sibling AI original disagrees with
source provenance`. The same call using the unmodified starting commit
reproduces this error. The other task's temporary originals were preserved;
hash validation was not weakened. Root AGENTS.md §8.5 therefore blocks opening
the engineering PR. There was no merge, publication or live Bitable write.

The build check's generated `docs/index.rst` change (KR entry replaced with a
US entry) and generated build artifacts remain unstaged and preserved. They
are validation side effects, not part of either task commit.
