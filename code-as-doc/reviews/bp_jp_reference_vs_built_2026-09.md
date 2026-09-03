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

## 5. Method

Reference typography via PyMuPDF span extraction (font, size, character counts
per page). Built typography by parsing the IDML: spreads to stories through
`ParentStory`, then transitively to anchored sub-stories, which hold the table
content — a first pass that skipped that step lost 39 of 84 stories and 2,886
characters and produced per-page gaps that were artefacts rather than findings.
Scripts are scratch and not committed; every number above is reproducible from
the two artefacts named at the top.
