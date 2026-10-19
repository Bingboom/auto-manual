# JHP-3600A / US approved Git-only Web source

This package preserves the authoritative PDF and selectable source text, source-local
artwork decisions, recipes, shared glyph copies, Manual IR and MyST Web sources.
Operator authorized this exact EN/FR/ES source for commit, push and publication on 2026-10-12 ("先提交发布推送"). The local candidate remains archived in its original worktree.
The PDF's printed revision is unconfirmed; the snapshot identifier is technical.

## Preview

- [en](http://127.0.0.1:8941/US/en/manual_jhp3600a_us_en.html)
- [fr](http://127.0.0.1:8941/US/fr/manual_jhp3600a_us_fr.html)
- [es](http://127.0.0.1:8941/US/es/manual_jhp3600a_us_es.html)

## Rebuild

From the repository root, use an unused output directory:

```sh
python3 data/manual_sources/JHP-3600A/US/git-20261012-541ca8a5-reviewed/rebuild.py --language en --output /tmp/jhp-3600a-us-candidate
python3 -m sphinx -b html -n -W --keep-going /tmp/jhp-3600a-us-candidate /tmp/jhp-3600a-us-preview
```

Other languages use the same adapter and their native source page selections.
Shared presentation styles own headings, tables and callouts; source-local CSS
only preserves original figure geometry and table group arrangements.
Small glyphs reuse verified transparent shared assets. Base art retains structural
panels, product markings and complete phone frames; external labels are editable.
Independent caption frames are removed from base art and redrawn with CSS.
`validation/local-checks.json` records local preflight, not user acceptance.

## Safety layout correction

The three native safety pages retain their risk banner, warning lead, explicit
source column breaks and semantic bullet lists. Full white warning panels use
`HB-CALLOUT-STRIP` with `hb-source-warning-lockup`, shared transparent triangle
SVGs and bold native copy; English and Spanish retain the danger variant.
The source-visible `※` marker is editable. Maintenance subbars retain their
level-two semantics, shared heading tokens and native rounded geometry.
`source/safety-layout-review.json` records the source-specific decisions;
`validation/safety-layout-browser.json` records checks at actual CSS widths.

## Symbol and FCC layout correction

Native EN/FR/ES symbol pages now use the registered `HB-TABLE-SYMBOL-SIGNAL`
and `HB-TABLE-SYMBOL-ICON` components. All four native badges retain their
white warning triangle, dark field and bold localized signal word. Source
gray label/icon columns and white meaning columns use shared theme tokens;
source panels stay side by side from 600 CSS px, in their original 6/5 row order.
The original pictograms reuse the previously verified transparent SVG files.

Native FCC panels use `HB-SPECIAL-FCC/two-column`, the shared transparent
nested-C FCC mark, source column breaks, four semantic bullet items and bold
native notice labels. CSS owns the gray rounded panel and logo text wrap.
No gray panel background or text is baked into the reused glyph.

`source/symbol-layout-review.json` and `source/fcc-layout-review.json` record
the source boundaries and asset decisions. `validation/symbols-fcc-browser.json`
records EN/FR/ES at measured 1280, 711 and 390 CSS px. The user's 180% browser
zoom was preserved. These checks do not replace operator layout acceptance.

## Inbox layout correction

The three native items retain their original unequal card widths, positions and
illustration scale. The existing product, cable and document SVG vectors are
reused unchanged. Six identified empty frame/badge paths are removed from a
source-local derivative; the historical clipped SVG is marked do-not-reuse.
Shared `hb-inbox-card` and `hb-inbox-marker` styles own complete gray rounded
frames, dark circles and centered white live numbers. Native captions remain
selectable in EN/FR/ES, with all coordinates bound to the same reused base art.
`source/inbox-layout-review.json` records the source geometry and reuse decision;
`validation/inbox-browser.json` records responsive browser evidence.

## LCD catalog correction

Both native LCD tables use shared `HB-TABLE-LCD-ICON` styling: gray first
three columns, centered circle numbers, dark rounded frame, and native 4/19
number rowspans. Status words and source setting/note paragraphs start separate
selectable lines. Original EN 8/16 and FR/ES 7/17 page row groups are preserved.
The complete icon census found ten mismatched prior glyphs. Nine missing
source variants are exported once as transparent native SVGs with their
original clipping. The battery x5 capsule reuses an existing exact file, and
fourteen other matching pictograms are reused unchanged. The capsule PNG
retains its original bytes; CSS clips only its transparent padding to preserve
native display size. Historical mismatched files are marked do-not-reuse.
`source/lcd-layout-review.json` records candidates, hashes and native paths.
`validation/lcd-browser.json` records responsive browser verification.

## Power callout alignment

The two gray power-on/off callouts center their editable paragraphs horizontally
and vertically in EN/FR/ES. The native line breaks, font sizes, frame geometry,
base artwork and other labels are preserved. `validation/power-callout-browser.json`
records responsive alignment and unchanged-geometry checks.

## Operation headings and prerequisite labels

The six native operation subtitles are semantic level-two headings and use
shared heading typography, round markers and spacing. EN/FR/ES preserve their
original copy and order. AC/USB prerequisite capsules center their editable
copy horizontally and vertically, retaining native size and position.
`validation/operation-layout-browser.json` records responsive verification.

The AC reset explanation is also centered horizontally and vertically in its
existing gray frame across EN/FR/ES. `validation/ac-reset-browser.json` records
alignment, unchanged geometry and regression checks for headings and prerequisites.

## USB caution list correction

The USB-output caution keeps three native semantic bullet items in EN/FR/ES,
with the original first-sentence bold spans and wording. The registered
`HB-CALLOUT-STRIP` and shared list styles own the presentation; no artwork or
CSS changes are introduced. `validation/usb-caution-browser.json` records
1280/711/390 CSS px checks and preserved prior figure geometry.
`validation/usb-caution-closure.json` checks each native marker against its
semantic list item while retaining the full-text and asset-closure checks.

## Energy-saving explanation and note correction

The existing illustration preserves its size, frame, leaders and labels. The
live gray explanation uses the native EN/FR/ES baseline spacing and left inset,
with the paragraph vertically centered. The following existing note retains
its shared callout component and native line breaks. A nonvisual container
keeps the note text at the source figure scale and restores the compact gap.
Phones retain the shared stacked callout and a readable 14 px body.
`validation/energy-saving-browser.json` records measured 1280/711/390 CSS px
checks; `validation/energy-saving-closure.json` records unchanged artwork,
full-text coverage and resource closure.

## LCD screen composition correction

The native left illustration and right six-row mode table now use registered
`HB-TABLE-LCD-MODE`. Existing SVGs are reused unchanged. Source-measured
EN/FR/ES panel, table, row and column proportions retain the complete original
frame, gray first two columns, white copy column, native line breaks and two
three-row state spans. Narrow screens scroll this complete panel horizontally.
`validation/lcd-screen-browser.json` records 1280/711/390 CSS px checks, native
proportions, unclipped selectable text and preserved prior layout corrections.
`validation/lcd-screen-closure.json` records full-text and resource closure.

## Key combination table correction

The three native button combinations now use registered `HB-TABLE-KEY-COMBINATIONS`,
shared button-pair, plus, CSS clock, gray first column and dark table frame styles.
Independent selectable captions are grouped beneath their corresponding buttons.
Source-measured EN/FR/ES columns, rows, fonts and line breaks keep the complete
original table; phones scroll it horizontally. The admitted horizontal shared
variants do not match this source and are marked do-not-reuse for this table.
Three native vertical variants were extracted once from physical page 12 through
the committed asset pipeline and are shared by all three languages. Original
artwork bytes remain intact. The recipe, candidate audit, 12x source/export pairs,
alpha checks, strict builds, responsive browser evidence and full-text/resource
closure are retained under `source/` and `validation/`. Operator layout acceptance
and all publication remain pending.

## UPS caution list correction

The UPS caution restores native semantic bullets: three in English and Spanish,
four in French, preserving each original wording and grouping. The registered
`HB-CALLOUT-STRIP` and existing shared list styles own the presentation, with
no CSS or artwork changes. `validation/ups-caution-browser.json` records
1280/711/390 CSS px checks and preserved previous USB, energy-saving, LCD and
key-combination geometry. `validation/ups-caution-closure.json` verifies
all native text, specific semantic bullet markers and local resources.

## Native specification, troubleshooting, storage and reminder list repairs

Four registered `HB-TABLE-SPEC` groups restore native headings, gray labels,
grid, rounded frame, AC input rowspan and source line breaks. The registered
`HB-TABLE-TROUBLESHOOTING` restores centered error codes and separate hanging
steps; the English source's F6 sequence 1,2,2,3,4 is retained. Storage keeps its
CSS gray panel, opening and closing paragraphs, and three semantic bullets.

Seven additional reminder tables per language now use semantic lists under
`HB-CALLOUT-STRIP`: 21 tables and 45 items across EN/FR/ES. Original text and bold
spans remain selectable, and misplaced French/Spanish callout labels return to
their source label cells. Existing USB and UPS lists are preserved. No table
contains unstructured literal bullet characters. Artwork bytes are unchanged.

`source/*-layout-review.json` records native geometry and copy. The final
`validation/tables-item-list-browser.json` records 1280/711/390 CSS px checks and
unchanged prior USB, energy-saving, LCD, key and UPS geometry. Its closure
sidecar verifies full native text, specific bullet markers against semantic
list items, local dependencies including CSS URLs, and narrow source/MD/IR scope.
These are local checks; operator acceptance and publication remain pending.

## Native heading and availability pairs

Battery connection, solar charging and car charging restore their nine native
EN/FR/ES level-two titles, circle markers and dark rounded availability labels.
The labels stay selectable inside their headings using shared
`hb-heading-title` and `hb-sold-separately` styles. Source-only alignment centers
the title and badge; bounded title width keeps the circle with long Spanish
copy on phones. Text, body paragraphs and artwork remain unchanged.
`validation/availability-browser.json` records 1280/711/390 CSS px checks and
prior layout regression. Its closure sidecar verifies full native text, local
resources, narrow source/Markdown/IR scope and fresh 109-file replay per language.

## Native caption centering and prose item lists

EN/FR/ES battery accessory captions center in both directions. The availability
capsule is drawn in CSS with white live text and a byte-identical existing
transparent shopping-cart glyph. All five native vector paths match the reused
icon under translation; the base artwork stays unchanged. All native notice titles
remain centered when mobile cells stack. Parallel connection restores
its native level-two title and circle marker. Four numbered steps and the
remaining result, warranty and Wi-Fi/Bluetooth bullets use semantic lists while
preserving wording and emphasis. Existing repaired table lists remain intact.
`validation/centered-copy-browser.json` records 1280/711/390 CSS px checks;
its closure sidecar verifies text/resources, five-node source scope, unchanged
artwork and previous USB/energy/LCD/key/UPS layout geometry. This remains a local
candidate pending the operator's combined layout acceptance.

## Compact native parallel instructions

The four numbered parallel-connection steps and two result bullets keep their
semantic lists with compact native spacing in EN/FR/ES. Source-local CSS removes
the inherited paragraph and item margins within these two lists, preserving a
small gap between them. Wording, emphasis, other lists and artwork stay unchanged.
`validation/parallel-list-browser.json` records 1280/711/390 CSS px checks;
`validation/parallel-list-closure.json` covers the full text and local resources.
The candidate remains local pending combined operator layout acceptance.

## Parallel figure labels and caution

Remove the extra `Jackery Explorer 2000 Plus` live label from the EN/FR/ES parallel
figures as explicitly marked by the operator. Keep the native connector/AC-port
labels and byte-identical base artwork. Original source text and bbox remain in
the text ledger, with the three operator omissions explicitly classified and
counted. The two semantic caution items preserve wording and hanging indentation;
source-local CSS removes their inter-item gap. Other body copy and lists stay
unchanged. `validation/parallel-figure-browser.json` records 1280/711/390 CSS px
checks; its closure records all required text/resources and the scoped omission.
Publication remains pending combined operator layout acceptance.

## Charging intro and AC title native layout

Restore the EN/FR/ES first-use charging sentence as bold white selectable text
inside the shared `hb-prose-pill` dark capsule. Convert each AC wall charging
paragraph into the native semantic H2 with the shared circle marker. Keep all
original wording and bold spans. The two charging-temperature notice items retain
semantic LI and hanging indentation; source-local CSS removes their inter-item
gap. The centered notice title and existing charging artwork remain unchanged.
`validation/charging-browser.json` records 1280/711/390 CSS px checks. Dense AC
artwork keeps its existing horizontal scroll container on narrow screens.
`validation/charging-closure.json` verifies all required source text/resources,
the three previously authorized extra-label omissions, unchanged artwork, and
110 byte-identical cold-replay source files per locale. Strict Sphinx builds pass.
Publication remains pending combined operator layout acceptance.

## Whole-document level-two title and availability audit

Audit all 28 native H2 titles per language and three heading availability capsules
per language against the original PDF. Restore the missing exit-parallel H2 and
six white-on-dark warranty subtitle labels; preserve numbered App headings in
native title case without circle markers. The contact telephone returns to
emphasized body copy. The French App timeout `Remarque` is a centered notice
label, not a section title; its exact source body spans remain unchanged.
Safety subbars, 16 circle titles per language, three dark `SOLD SEPARATELY`
equivalents and the existing gray accessory/cart label retain their native roles.
`validation/headings-browser.json` records font/marker/color, 1280/711/390 CSS px
wrapping, all-title clipping and badge overlap checks. The closure verifies full
required copy/resource coverage, exact source/Markdown/IR scope, unchanged art
and 110 byte-identical cold-replay source files per locale. No warranty body
panels or new artwork were added. Publication awaits combined layout acceptance.

Follow-up: the existing warranty-years figure has a residual top border and
dark live year numerals over dark circles in the desktop screenshot. This audit
preserves that figure byte-for-byte; repair its artwork/caption composition in a
separate layout change.

## Specification trademark and circled footnotes

EN/FR/ES restore the two native registered marks as selectable SUP immediately
after `USB Type-C` and `USB-C`. The trademark words, including the English line
printed in the French source, stay unchanged. Native circled ①/②/③ remain live
text in three semantic ordered-list items, with suppressed generated counters,
compact spacing and hanging continuation lines. Shared `manual-spec-note` and
`manual-spec-footnote` styles own the note typography. Table reference markers
and all existing heading/artwork/layout repairs remain unchanged.
`validation/spec-footnotes-browser.json` records desktop/mobile bounds and real
SUP visibility; expected ink above a line box is not itself clipping. Its closure
verifies the native trademark line through the paragraph minus only the two SUP
marks, then separately verifies those two source marks at their native terms.
No ledger text is omitted or rewritten for this repair. All required source text
and resources pass, with 110 byte-identical cold-replay files per locale.
Publication remains pending combined layout acceptance.

## Complete native warranty-page restoration

Restore the EN/FR/ES gray lead panel, six native rounded warranty panels, dark
white-text headings crossing their top borders, and 3/2 white numerals centered
in CSS circles. Existing registered `HB-WARRANTY-LEAD`, `HB-WARRANTY-SECTION`
and `HB-WARRANTY-YEARS` components own the editable copy and year-card typography.
The original 36-month paragraph sits in the left period column; the exact native
extension paragraph returns to the right column. Native exclusions keep all four
semantic items. Desktop columns stack on narrow screens with no title/body
collision. Only the warranty chapter and scoped composition CSS change. Every
old body/lead/note/list rich-text fragment is reused without rewriting copy.
The former year-art files remain archived byte-identically; the visible year card
uses semantic text and CSS shapes and has no leftover empty raster border.
This resolves the earlier warranty-year numeral/border follow-up.
`validation/warranty-browser.json` records 1280/711/390 CSS px checks. The closure
verifies all required source text/resources, previous trademark SUP matching,
prior authorized extra-label omissions, narrow source/Markdown/IR scope, and
110 byte-identical cold-replay files per locale. Existing warranty API modules
are explicitly hash-pinned in `source_manifest.json`. Publication remains
pending combined layout acceptance.

## Native App download and phone-layout repair

EN/FR/ES download copy uses the existing `HB-SPECIAL-APP/download` component:
complete shared App Store/Google Play artwork and the source-matching dense QR
frame sit above their original selectable instructions. All reused files are
byte-identical and retain origin paths and SHA-256. The missing circular plus
uses the shared transparent SVG in the original step2.1 gap, preserving native
words and punctuation. The two-phone figure scales to the reading column with
live2.1/2.2 captions and no unnecessary640px scroll canvas. A separate gray-strip
artifact was traced to the neighboring control panel overlapping the old crops.
The shared native SVG extractor preserves the original phone images, frame
paths, clipping, transforms and opacity, while excluding that adjacent panel.
All old assets and original recipes remain archived byte-identically. Native
locale geometry and copy are preserved, with only y percentages rebased to the
phone-only height. The control panel and all later App instructions remain intact.

`source/app-layout-review.json` records pre-edit reuse decisions; the three
phone recipes and hashes are in `source/app-phone-artwork-recipes.json`.
`validation/app-phone-edge-qc.json` compares all24 phone edges at12px per source
point against the PDF, with source/candidate top/bottom pairs. Strict builds,
1280/711/390 CSS px browser checks, full required text/resource closure and
byte-identical fresh replay pass for all locales. Scope is proven in source,
Markdown and Manual IR. Shared framework files are hash-pinned and unchanged.
Local-only candidate; combined operator layout acceptance remains pending.

## Native App connection trio: neighboring-border repair

Remove the thin neighboring CAUTION border accidentally included at the bottom
of the EN/FR/ES2.3–2.5 artwork. Reuse each original target SVG and remove only
1/3/1 native paths, identified by native PDF drawing index, exact path geometry,
fill/stroke and source-to-crop matrix. Every other SVG byte remains unchanged,
including native overprinted interface titles, bitmap UI, frame paths, clip
groups, definitions, transforms and opacity. Crop geometry and all live labels
remain exactly as before. Ordinary responsive figure sizing replaces the dense
640px minimum, keeping the trio in one row without a horizontal scroll strip.
Original assets and original intake recipes stay archived byte-identically.

`source/app-connect-layout-review.json` records rejected shared assets and the
native reuse decision; `source/app-connect-artwork-recipes.json` records the
removed source-bound paths and final hashes. All36 phone image edges pass the
12x source/browser comparison, and all three final bottom strips are pure white.
Strict EN/FR/ES builds,1280/711/390 CSS px browser checks, full native text and
resource closure, precise source/Markdown/IR scope, and119-file fresh replay
pass. Shared styles, framework code and all earlier repairs remain unchanged.
This is a local-only Git candidate pending combined operator layout acceptance.

## Native contact footer restored

Physical page64 now uses its native plain company heading, address and one
horizontal contact panel with large telephone, circular phone icon, email and
website icons, and a separate complete QR frame. All copy remains selectable;
the existing company heading and telephone anchor are preserved. At390 CSS px,
telephone and email/website stack inside the same panel with the square QR on
the right. No extra cards or changes to body headings are introduced.

The three shared icons are byte-identical to inventoried JHP-5000C assets and
match native PDF path geometry. Existing QR candidates have different matrices;
the reviewed native glyph retains all18 source paths and matches all441 module
cells at12px per source point. Provenance and reuse decisions are frozen in
`source/contact-footer-layout-review.json` and `source/contact-footer-qr-recipe.json`.

Strict EN/FR/ES builds, nine1280/711/390 CSS px browser cases, native text and
resource closure, precise source/Markdown/IR scope, and123-file fresh replay
pass. Telephone and link text fit their own boxes and remain vertically centered.
Existing assets, prior repairs and shared framework code are preserved. This is
a local-only Git candidate pending combined operator layout acceptance.

## Publication source acceptance

`source/approval.json` binds the operator grant, reviewed input hashes and merge authorization. Only artwork referenced by each locale is carried in its Web tree; the full original source pool and all earlier evidence remain archived unchanged. The shared build.py check is a fixture-backed family regression gate, not acceptance of these native language bodies. Publication and online receipt are verified separately.

Native publication admission binds all33 pictogram rows to PDF5/25/45. The existing shared crossed-bin-bar PNG replaces the prior gray-JP bin variant in all three symbol tables; its bytes remain unchanged. Explosive-triangle reference crops retain1pt transparent source padding, matching the existing vector exactly. No native captions or table arrangement changed.
