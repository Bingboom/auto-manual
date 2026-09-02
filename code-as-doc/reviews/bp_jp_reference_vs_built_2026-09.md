# BP@JP reference-versus-built ledger (R3c Phase 6)

Date: 2026-09-01

Reference: `Jackery Battery Pack 2000取扱説明書V2.0-2026-05-28.pdf`, the shipped
HTP017 Japanese book, 12 pages, supplied by the operator for this comparison.
Built: `docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp.idml`, 12 spreads,
produced by `build.py idml` against the live-synced `data/phase2` mirror.

This is the pipeline-side half of Phase 6's twelve-page visual acceptance. It is
measured, not eyeballed: text, fonts and sizes are extracted from both artefacts
and compared. It does not replace the native round — overset and true visual
fidelity still need InDesign — but it narrows what that round has to look for.

## 1. What matches

**Page count**: 12 = 12.

**Page geometry**: reference 368.754 x 524.659 pt; built 368.787 x 524.693 pt.
The 0.033 pt difference is mm-to-point rounding (both are 130.1 x 185.1 mm) and
is not a deviation.

**Content**: 6,879 characters of live text in the reference against 6,644 in the
build, and every per-page difference is explained rather than outstanding:

| Page | Role | ref | built | Reading |
| ---: | --- | ---: | ---: | --- |
| 01 | cover | 276 | 0 | cover is a placed approved asset; the reference sets it as live text. Delivery-method difference, same as the US precedent. |
| 02 | toc | 1,324 | 98 | dot leaders only — see below |
| 03 | safety | 884 | 790 | within tolerance |
| 04 | symbols | 370 | 363 | within tolerance |
| 05 | inbox | 208 | 190 | within tolerance |
| 06 | product_overview | 505 | 438 | within tolerance |
| 07 | lcd | 252 | 241 | within tolerance |
| 08 | operation_guide | 317 | 292 | within tolerance |
| 09 | connections | 276 | 264 | within tolerance |
| 10 | charging | 839 | 750 | within tolerance |
| 11–12 | troubleshooting + spec | 1,628 | — | one composition spans both spreads, so a per-spread character count double-counts it; not comparable this way |

The table of contents is **content-identical**. All ten entries match in label
and page number (`使用上のご注意 01`, `同梱品 03`, `各部の名称 03`, `液晶画面 04`,
`製品の使用方法について 04`, `ポータブル電源との併用 05`, `充電方法 07`,
`トラブルシューティング 08`, `主な仕様 08`, `保証について 09`), as does the
`01-10` range marker. The 1,226-character gap is entirely dot leaders: the
reference sets them as literal `.` characters, the build uses a leader tab, so
the dots are a style property rather than content. That is the better encoding,
not a shortfall.

## 2. The deviation that matters: Japanese weight

The shipped book sets Japanese text in **four weights**. The build uses one.

| Face | Reference characters |
| --- | ---: |
| NotoSansJP-Regular | 2,926 |
| NotoSansJP-DemiLight | 2,004 |
| NotoSansJP-Medium | 1,509 |
| NotoSansJP-Bold | 356 |
| NotoSansCJKjp-Bold | 77 |

**3,946 of 6,872 Japanese characters — 57% — are set in a non-Regular weight.**

The build emits `HB Manual Sans JP (OTF)` for all 255 Japanese runs, and every
one of them resolves to Regular. This is not a case of a style asking for a
weight the package cannot supply: measured, zero Japanese runs request Bold or
Medium. The pipeline never varies Japanese weight in the first place, and
`Document fonts/` ships exactly one Japanese face,
`HBManualSansJP-Regular.ttf`.

The consequence is systematic rather than local: every Japanese heading,
emphasis, table header and lead that the shipped book sets in Medium or Bold
renders at body weight. Weight is doing real typographic work in the reference —
`保証期間` at Bold 7.6 pt, `主電源ボタン` at Bold 7.0 pt, the running body at
DemiLight 7.0 pt — so a single-weight rendering reads as flat at every level of
the hierarchy at once.

This is a pipeline gap, not a finishing-layer item. Closing it needs the other
Noto Sans JP weights provisioned under the `HB Manual Sans JP` family and the
paragraph styles selecting them; it cannot be repaired by hand at layout time
without abandoning the shared component styles.

## 3. Secondary deviation: the Latin and numeral face

In the shipped book Gilroy is an accent, not a workhorse: **43 characters in the
whole 12-page book** (Medium 25, Regular 11, Bold 7). Page numbers are Japanese
face — `01` is NotoSansJP-Regular 6.0 pt.

In the build, 293 runs inherit Gilroy from the paragraph styles: `Jackery` (30),
the bullet `•` (24), `2000 Plus` (12), page numbers, `AC` / `DC` / `LCD`,
`36.8V-57.6V`, and list ordinals. All 72 style definitions declare Gilroy as
their base font.

Two consequences follow. Against the reference this is a face mismatch on
numerals and page numbers. Independently, Gilroy is commercially licensed
(Radomir Tinkov) and deliberately not shipped in the package, so a host without
it substitutes silently — the signature being Japanese text correct while brand,
product name, bullets, page numbers and units all change typeface.

## 4. What this does not settle

One question the next native round can answer in a glance, and nothing outside
InDesign can. `HB Warranty Body` is declared with its leading equal to its size
(6.00/6.00, `type_warranty_body_font_size` and `idml_warranty_body_font_leading`),
so its 599 characters of prose depend entirely on a `Leading="7"` override --
and that override is emitted on the `ParagraphStyleRange`, thirteen times, in
`components/warranty.py::_variant_body_format`. In the whole package that is
the only character-model attribute sitting on a paragraph range: `PointSize`
appears there zero times against 248 on `CharacterStyleRange`, `HorizontalScale`
zero against 355, and the same function puts `HorizontalScale` on the character
range two lines later. But the form is not an accident either -- `lcdmode` emits
it the same way and `tests/test_idml_lcdmode_editable.py:302` pins it -- so
whether InDesign honours it is a question about InDesign, not about this repo.

**So look at the warranty body on pages 11-12 and say whether the lines have
interline space.** If they are set solid, the override is being dropped and the
attribute belongs on the character range; if they breathe, the form is fine and
this note can go away.


Overset stories and overset table cells cannot be measured outside InDesign:
`tools/indesign_finalize.py::_overset_pages` reads a report the JSX writes inside
the application. The previous Phase 6 status quoted zeros for those, but they
predate #985, #989 and #992 and describe bytes that no longer exist.

The next native round should keep its finalize report inside
`docs/_build/JBP-2000B/JP/` so the findings are readable here instead of being
transcribed.

## 4a. Charging page: figure measure, suffix pill, and the redacted labels

Reference page 09 resolved three findings that read as one, all in the target
contract rather than the renderer.

The illustrations printed at 58 percent of the reference measure — 181.0 pt
against 311.6 pt — because BP@JP's `charging` page declared no
`composition_data` at all and fell through to the `charging_diagram` role's
0.58 ratio. BP@US and BP@EU both declare `reference_measure` for the same page
role, so BP@JP was the outlier. Declaring it puts both figures at the shipped
size to a tenth of a point: AC 312.1 x 152.4 pt against the reference panel's
311.6 x 151.1, solar 312.1 x 179.7 against 311.6 x 179.5. The heights land
because both assets are full-measure crops of that page — the same 3772 px
width — which is also what proves the next finding.

`ソーラー充電（別売）` printed as plain running heading copy. The reference sets
`（別売）` as white type on a dark rounded pill, brackets included, which is the
`h2_suffix_pill_indices` treatment the siblings already declare. It could not
be declared here: `split_trailing_parenthetical` matched only ASCII brackets
preceded by a space, and Japanese writes full-width brackets with no space.
The detector now carries the two forms as separate alternatives, so the Latin
branch matches exactly what it matched before, and the full-width branch keeps
its brackets in the pill because that is what the book prints. The pill's
remaining width gap (28.1 pt against 35.7) is horizontal padding in the shared
pill component and was left alone.

The four cable labels were printed as a two-cell table under each figure. The
reference sets them as live 6 pt Regular text inside the artwork, at
`拡張ケーブル` (50.5, 242.9), `ACケーブル` (199.6, 243.7), `SolarSaga 200`
(285.6, 427.2) and `拡張ケーブル` (37.6, 463.4) — a pair on a shared baseline
under the AC art, and a pair 36 pt apart beside their own parts in the solar
panel, which no table row can express. The asset registry says why those
coordinates are available: both assets are this page's artwork with
「电缆活字标签」 redacted, so each figure already carries the white band the
labels came out of, and the leader arrows are still drawn in.

So the labels now sit back in that band. The copy stays in
`docs/templates/page_bp/ja/08_charging_methods.rst`, where translation, review
and cloud-doc backport reach it; the contract carries only where each label
sits, as fractions of the figure's own box, bound by cell ordinal the way the
LCD hero callouts bind to their parts rows. All four land within 0.0 pt of the
reference positions. The source no longer bolds them, because the reference
does not.

Blast radius: `figure_callouts` is optional in the plan gate and defaults to
empty through `plan_figure_callouts`, `add_prose_story` and
`render_image_block`, so a figure with nothing declared keeps its table under
the art. No other contract declares it — `tests/test_idml_figure_callouts.py`
pins that — and all four IDML goldens regenerate byte-identical, which is also
why those tests exist: the goldens do not reach this path.

## 4b. Corner treatment: what matches, what does not, and why none of it was scopable

An audit of every box-like shape in both books, measured three independent
ways, settled this. Two of those ways disagreed at first and the disagreement
was the most useful result: a pixel arc fit on the rendered page measures the
outer edge of the **ink**, which for a stroked box sits half a stroke width
outside the **path**, and the IDML stores a path radius. Card 5.80 path +
0.94/2 stroke = 6.27 ink; note strip 7.89 + 1.05/2 = 8.41. Every number below
is a path radius. Taking the ink numbers would have declared six values half a
stroke too round.

Already matching, and left alone: the H1 chapter tab, the most repeated chrome
in the book at eleven instances -- 5.6693 pt built (`comp_h1_pill_arc`, 2.0 mm)
against 5.70-5.80 measured, sharp on top and rounded south in both. Its
parameter comment says it was measured from the master, and it was. So were
`comp_subbar_arc` (2.45 mm = 6.94, against the reference's 6.957 stadium bar)
and `comp_table_outer_arc`.

The radii that differ are, without exception, the ones nobody measured:
hardcoded literals (`page_objects.py` 5.5, `page_toc.py` 4.753, nine separate
values in `oppanel.py`) and one derived sum (`comp_tip_arc` + `comp_callout_rule`
= 6.10 for every notice panel). The deltas run both ways -- the warranty frames
and the operation panels are **rounder** in the build than in the book -- so
there is no single global correction.

Nothing here could be scoped to Japanese. Every radius sink reads its key
language-neutrally through `param_pt` / `component_param_pt`;
`localized_param_pt` and `localized_component_param_pt` have four call sites in
the repo and not one of them is a radius. A `lang_jp_comp_*_arc` row is a dead
row that changes nothing, silently -- the same trap as #985. Four declared rows
(`comp_subbar_arc`, `comp_fcc_arc`, `comp_inbox_card_arc`, `comp_note_arc`) are
not read by the IDML renderer at all, so editing them would also do nothing.

So the radius lives in the target contract, which is the tightest scope
available: the file belongs to one target and nothing else reads it. A
composition may declare `corner_radii`, a map from a named piece of chrome to
its radius in points; declaring nothing keeps the shared default, which is what
every other contract does. Delivered for the two compositions whose data
already reaches the chrome:

| Chrome | built before | reference | built now |
| --- | ---: | ---: | ---: |
| inbox card (x3) | 5.50 | 5.80 | 5.80 |
| inbox note strip | 6.10 | 7.89 | 7.89 |
| warranty section frame (x6) | 6.80 | 4.80 | 4.80 |
| warranty 免責事項 panel | 6.80 | 11.08 | 11.08 |
| warranty lead panel | 9.07 | 7.72 | 7.72 |

The disclaimer is why a chrome name may be suffixed with a structural index.
Declaring one `section` value for all seven frames moved the disclaimer from
6.80 to 4.80 against a master that sets it at 11.08 -- the six real frames got
better and that one got worse, which an adversarial pass over the rebuilt
artefact caught. It is addressed as `section:7`, the ordinal its component spec
already carries, and never by its title: routing on printed copy is what
silently degraded seven languages in #979. Its fill, stroke and title chip
still differ from the master -- the book sets a flat unstroked grey panel with
the heading as plain bold text inside -- and that is a component variant, not a
radius.

Still on the shared defaults, with the reason:

| Chrome | built | reference | why not yet |
| --- | ---: | ---: | --- |
| notice panel (x5) + label plates | 6.10 / 5.48 | 8.06 / 7.31 | inline prose component; `_render_component` receives no composition data |
| TOC segment bar | 4.75 | 6.31 | the TOC renders outside the composition dispatch |
| signal-words + symbol-legend frames | 5.50 | 6.31 / 4.61 | the safety and symbols pages carry no `composition_data` |
| operation panel (x2) | 10.00 | 8.15 | no `composition_data`, and nine hardcoded literals |
| spec table shell | 6.80 | 5.78 | radius is a literal argument in `data_stories.py` |

Beyond radii, the audit found chrome the book prints that the pipeline does not
emit at all: the dark stadium section bar (the `emphasispill`
`full_width_subbar` component exists and its radius already matches, but it is
promoted only for the maintenance page), a rounded shell around the
troubleshooting table (spec and LCD tables get one; `add_trouble_story` wraps
its table in a bare `ParagraphStyleRange`), grey stadium capsules behind
warranty lines, the back-page contact rows, and the connections step chips. One
divergence runs the other way: the note strip is filled and carries a 注意
label plate that the reference does not print.

The operator's ruling was to build the contract scoping first and, of the
missing chrome, to take the troubleshooting shell. That shell needs the table
segmented -- the shell is a fixed-height anchored group and the table flows
across two spreads, which is why the spec table is segmented by section -- so
it is its own change. The section bar is entangled with the page 02/03 heading
structure still open in §7.

## 4c. Type scale: the specification row pitch, and why the rest is not a type change

The type-scale gap is real and measured. The master sets every PROSE role at
7.00 pt -- TOC entries, warranty items, symbol captions, specification values,
running body, the disclaimer -- and a second tier at 6.00 pt for in-panel and
in-table secondary copy. The build sets the prose roles at 5.50-6.50 and the
6.00 pt tier at roughly the right size already, so the figure callouts and the
troubleshooting cells need nothing. Body leading is 9.00 pt against the master's
7.00/9.00 measured over 22 samples, where the build runs 6.00/7.20.

But raising type does not work as a token change, and this is the finding that
stopped one. **56.6 percent of this book's text sits in anchored frames with
`AutoSizingType="Off"` whose heights are data tokens that do not move with type
size.** Every one of the ten ordinary specification rows was a 7.00 pt line box
holding a 6.60 pt line -- 0.40 pt of slack, `AutoGrow="false"`, no terminal
carrier -- so a 7.7 pt leading oversets all twenty cells. Five of the seven
pinned warranty panels carry the largest 6.00 pt population on 2.94-6.11 pt of
slack. The LCD panel and the four notice bodies have 1.00-8.00 pt each. None of
that is visible from the build: nothing compares `add_prose_story`'s estimated
height against the frame it flows into, so an overset would have surfaced only
when the book was opened.

So the containers move first. The specification shell was the largest single
geometry gap in the book, and its pitch was measurable rather than inferred:
the master draws a hairline between every pair of rows, and reference page 9
carries two stroked panels -- the upper one is the troubleshooting table
(fourteen bands at about 10.89 pt, left column reading F1...FF), and the lower
one is the specification table (eleven bands, ten at 14.95 pt and a final one at
38.35 pt, left column reading 認証 / 型番 / 定格容量 / バッテリータイプ /
サイクル寿命 / サイズ&重量 / DC拡張ポート(入力) / (出力) / 充電温度 / 動作温度 /
保存温度). Pairing those two panels the other way round would have put the
troubleshooting pitch into the specification table.

| | built before | master | built now |
| --- | ---: | ---: | ---: |
| specification shell | 133.80 | 188.34 | **187.80** |
| as a share of the master | 71.0% | 100% | **99.7%** |

Declared as `lang_jp_idml_compact_spec_table_row_height` and
`..._multiline_min_height`. `spec_tables.py` already reads both per language
with the shared value as the fallback, and
`lang_ko_idml_compact_spec_table_row_height` has been in the Korean overlay for
a while, so this is a data change on an established path. The shell fits: the
frame is 245.8 pt and carries the 20.1 pt H1 pill besides.

### What the audit established about scoping the sizes themselves

Every corner of this was checked against the code rather than assumed, because
the obvious mechanism is a trap. Making the paragraph-style table's size helper
language-aware -- `sz()` in `tools/idml/styles.py` reads one literal key -- would
silently activate rows that already exist for other languages:

| key | already declared by | so language-scoping it would |
| --- | --- | --- |
| `type_spec_label_font_size` | de 5.6, it 5.7, fr/es 5.9 | move four shipped books |
| `type_spec_value_font_size` | fr/es 5.9 | move two |
| `type_body_font_size` | nobody | be inert |
| `type_warranty_body_font_size` | nobody | be inert |
| `type_symbol_body_font_size` | nobody | be inert |

Those de/it rows are half-live today: `data_stories.py` reads them to size the
portable symbol markers inside spec cells, while the paragraph style still
prints at the shared 6.00. So the specification type size is the one role that
cannot be scoped this way, and the row pitch delivered here is what its geometry
needs regardless.

The safety-page bullet list was going to be part of this change and was dropped:
the reference role that looked like a bullet list at 7.00/11.50 turns out, on
page 2 at x 29.9 and x 100.6, to be the page intro and the four signal-word
legend definitions. The master's page 2 has no bullet list at all, so our
fifteen bullets are a content-structure difference belonging with §7 rather than
a type delta.

## 4d. Safety bullets, and two corrections the adversarial pass forced

The master sets the eleven 「使用上のご注意」 bullets at 7.00 pt on an 11.50 pt
pitch, full measure; the build set the same eleven items at 5.50/6.30. Declared
as `lang_jp_idml_compact_safety_list_font_size` / `..._leading`, which
`safety_story.py` already reads per language with the shared value as the
fallback -- en/fr/es/de/it/uk each declare their own, so Japanese was simply
missing from a table every other language is in.

This item was twice withheld on reasoning that turned out to be wrong, and both
errors came from reading a sample instead of the whole:

1. "The master's page 2 has no bullet list." It has eleven, at x 28.34. The
   first six of the page's twenty-six 7.00 pt spans happen to be the intro and
   the legend definitions, and the reading stopped there.
2. "The build sets them in two columns, so it needs a layout change." It does
   not. `column_measure` in `safety_story.py` feeds the components inside the
   story; the bullets run the full 312.09 pt measure, and the built frame spans
   page x 28.35-340.44 exactly as the master's do.

The verification that settled it proved the pairing four independent ways --
folio ('01' on both sides), all eleven items verbatim in the same order followed
by 「絵表示について」, frame x-extent against the master's 42 x 7.00 pt wrap
capacity, and the whole y-stack reconciling to 0.01 pt against
`idml_shared_page_top` 27.7 and `idml_safety_signals_table_top` 350.0 -- and
showed the reference size is not a text-matrix artefact on either axis (glyph
bbox height 19.992 = 7.0 x 2.856; full-width advance exactly 7.00).

Reflow is contained to that one frame: 113.45 -> 223.20 pt of 294.673, or
38% -> 76%, leaving 71.47 pt. The legend below starts at page y 350.00 and the
body frame ends at 346.00, a gap the growth never reaches.

### Two corrections to §4c

**The build is not blind to overset.** §4c said nothing compares a story's
height against its frame, so an overset would surface only on opening the book.
That is true of the Python leg only: `tools/idml/indesign_finalize.jsx` collects
both `overset_stories` and `overset_table_cells` with page attribution, so the
finalize report catches it.

**The specification-cell overset numbers describe the state before the row
pitch changed.** The reflow model that produced "ten 7.00 pt line boxes holding
6.60 pt lines, 0.40 pt of slack" was computed at the shared 11.0 pt row height
-- it called the estimator with a language key that is not `jp`, the same
normalization trap as #985, so it modelled a table the shipped file no longer
has. At the master's 14.95 pt pitch those cells have roughly 3.3 pt of slack at
a 7.7 pt leading. The conclusion that containers must move first still stands,
and the row pitch is what moved them; but the specification type size is no
longer blocked by cell overset. What still blocks it is the key collision:
de/it/fr/es already declare `type_spec_label_font_size` and
`type_spec_value_font_size`.

### What the completeness critic found that the audit could not see

The audit's lens is XML text, so it is blind to type baked into placed artwork,
and four "absent" findings are that blindness rather than gaps: the cover is not
missing -- `Spread_sp_0` places `cover_jbp2000b-ja.pdf`, whose twelve spans match
the master to 0.01 pt, making it the one page already at type parity -- and the
Li-ion lettering, the ①/② step numerals and the product silkscreen are all
present inside their assets. A fifth, the master's live 「3s」 duration mark, is a
text-to-icon substitution in our artwork rather than a dropped element.

Two findings survive as real and are not yet acted on: the safety bullet marker
is '•' U+2022 where the master sets '・' U+30FB, and the two notice bodies judged
"not reader-visible" on a -0.2 pt size delta carry `HorizontalScale="106.9"`,
so their set width differs by more than the vertical axis alone shows.

## 5. Method

Reference typography via PyMuPDF span extraction (font, size, character counts
per page). Built typography by parsing the IDML: spreads to stories through
`ParentStory`, then transitively to anchored sub-stories, which hold the table
content — a first pass that skipped that step lost 39 of 84 stories and 2,886
characters and produced per-page gaps that were artefacts rather than findings.
Scripts are scratch and not committed; every number above is reproducible from
the two artefacts named at the top.
