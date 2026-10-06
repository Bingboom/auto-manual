# JHP-3600C / US / en Git-only Web intake

Status: active

The current local English candidate includes the safety layout correction and checked shared symbol variants (symbols1). Visual confirmation of this revised candidate is pending.

## Source and scope

- User-selected authority: `Jackery HomePower3600 Pro Max Portable Power Station User Manual.pdf`.
- SHA-256: `31fd069216fb282968bf90ba8ef7da0e885a875140667e083bca5cbc9e0122c7`.
- Model: JHP-3600C. Product: Jackery HomePower 3600 Pro Max. Region: US; language: en.
- Source has 97 physical pages: English preface on p2, English body on p4–34 (printed 01–31); cover/contact metadata on p1/p97. FR/ES excluded.
- Printed manual revision: unknown. Technical Git snapshot only.
- Base: `ed4d4ec5071d000d590d5b53322aea6c12186f7c`.
- Root checkout and its foreign `tmp/` are preserved. Work is isolated on `feat/web-jhp3600c-us-en`.

## Plan and safety boundaries

1. Freeze PDF identity, positioned native extraction and asset reuse/extraction decisions in a source-local package under `data/manual_sources/JHP-3600C/US/en/`.
2. Use existing public ManualSource/Manual IR, registered components, shared Web renderer and MyST scaffold. Native paragraphs/lists/tables remain searchable. No whole-page screenshots or new model-specific build config.
3. Preserve source wording, technical values, warnings, fault codes and manufacturer/contact identity. Normalize only line wrapping, ligatures and page furniture. Record source anomalies rather than silently correcting them.
4. Run an existing US target `build.py check` as a repository regression gate; JHP-3600C is external frozen source, not an enrolled phase2/print target. Validate this new body independently against all included source regions.
5. Validate strict Sphinx, packaged-image hashes, cold IR replay, asset tamper rejection and browser at desktop/mobile widths. Commit source package and evidence only after local validation.

No live table, queue, source, asset, build or HTML_link writes. No merge/deployment authorization is inferred. No phase2 schemas, public flags, dependencies or workflows change.

## Asset inventory before extraction

Searched `manual_sources/`, `data/manual_sources/`, `docs/renderers/web/assets/`, `docs/renderers/latex/assets/`, `docs/templates/word_template/common_assets/`, asset recipes and registries. No JHP-3600C/HomePower 3600 Pro Max target binding exists on the verified base. JE-3600A/JBP-3600A and JE-1000F drawings are candidates only: model name is insufficient to establish matching US sockets, dual-voltage routing, cascade/EPO or ATS arrangement. Detailed per-slot decisions and hashes belong to `asset_decisions.json` in the frozen input.

Shared safety symbols/LCD semantics are checked first. Exact matching files are copied byte-for-byte with path/hash provenance. Dense annotated overview and declared finished operation panels retain complete source borders/labels with no duplicate visible transcription. App screenshots retain full phone frames. Ordinary connection drawings use textless art plus native instructions; tables always use native cells.


## Implemented source

The [frozen manifest](../../data/manual_sources/JHP-3600C/US/en/git-20261005-31fd0692/source_manifest.json) binds the unchanged original PDF, complete positioned extraction, 399 selected/recovered fields, semantic chapter data, 84 asset decisions, shared IR, MyST and scaffold. It also pins 204 repository renderer/component/style/asset inputs. `rebuild.py` verifies both inventories before compiling through the shared APIs. No new family config, phase2 enrollment, parallel renderer or public CLI is added.

The result has 20 chapters, 26 warning/note/tip components, a 33-row glossary covering LCD numbers 1–31 (18 and 28 have two subrows), 14 native specification groups, FCC/Inbox/auto-resume/LCD-mode/symbol/troubleshooting compositions and native 3+2-year warranty cards. Eight source-specific LCD symbols are stored with true alpha under the shared Web LCD asset directory; existing matching safety/button/LCD assets are reused byte-identically. Dense finished panels remain image-led with accessible native copy; no whole source page is used as a Web page.

Complete operation/charging panel borders, solar connector drawings and phone frames were checked against rendered PDF pages. The ATS App panel retains both phone screenshots and the complete adjacent product-connection drawing. Its instructions are removed from the artwork and retained as native copy. Text redaction retains the original vector background without a grey fill overlay. Source callout severity, F0–F9/FA/FC/FF measures, JHP-3600C ratings, JBP-3600A battery and JA-TS05A specifications, contact identity and native legal copy are preserved.

## Normalizations and source anomalies

- Restore positioned ® immediately after USB Type-C and USB-C; expand ligatures and normalize wrapping.
- Keep charging/ventilation subitems nested, separate four footnotes, and separate specification submodes into native lines. Existing spec components require an h2 carrier hook; explicit `aria-level=3/4` restores accessible hierarchy and a source-local class prevents those headings from becoming sibling chapter TOC entries.
- Printed p28 uses literal `1440W4`; expose its 4 as `1440W⁴`. Printed p23 uses circled ④. The two source forms remain distinct.
- Retain `energe flow` (physical p22), the `The area is completely waterproof.` installation-site requirement (p30), and native product/name variation. No inferred engineering corrections.
- Exclude FR/ES, covers as reading pages and page furniture. Cover/contact identity remains traceable.

## Verification

- Strict Sphinx passed with warnings treated as errors.
- `audit_source.py` passed: 1,128 positioned extractable English/contact lines covered by semantic copy (including image alt) or retained panels; zero unmatched. This is a coverage check, not proof of reading order or visual geometry. Outlined symbol text and panel/image glyphs were checked visually and have explicit recovery/provenance records.
- Deterministic rebuild: every frozen MyST/IR/scaffold/style/asset file is byte-identical. Cold replay used only IR, CSS and assets, with no PDF/RST/CSV/extraction JSON. Altered LCD asset bytes were rejected: `document asset missing or changed: assets/lcd_parallel.png`.
- 26 focused shared replay/table/evidence tests passed. Ruff passed. Documentation link/lifecycle check passed after assigning the required active status.
- Existing-target regression gate passed using US/en JE-1000F phase2 fixtures. This result does **not** validate the JHP-3600C body or enroll a print target.
- Desktop 1440×1000, mobile 390×844 and narrow 320×844 had equal viewport/document scroll widths. All 86 image references resolve locally; observed loaded images had no failures. Wide LCD/auto-resume/troubleshooting tables scroll within their own figures. [Browser/replay evidence](jhp3600c_us_en_web_evidence/browser.json), [desktop](jhp3600c_us_en_web_evidence/desktop-operations.jpg), [mobile specs](jhp3600c_us_en_web_evidence/mobile-specs.jpg), [App frames](jhp3600c_us_en_web_evidence/mobile-app.jpg).

The current local runtime warns that some installed package versions differ from `requirements.lock`; no dependency versions were changed. The stated checks passed in this runtime. The branch wrapper could not switch to main because main is owned by the root worktree; the clean isolated branch was created directly from the verified origin/main ref.

## Reproduce

From the engineering worktree, choose unused output directories:

```bash
python3 data/manual_sources/JHP-3600C/US/en/git-20261005-31fd0692/audit_source.py
python3 data/manual_sources/JHP-3600C/US/en/git-20261005-31fd0692/rebuild.py --output /tmp/jhp3600c-rebuilt
python3 -m sphinx -W -b html /tmp/jhp3600c-rebuilt /tmp/jhp3600c-html
python3 -m ruff check build.py integrations tools tests scripts data/manual_sources/JHP-3600C/US/en/git-20261005-31fd0692 --exclude conf.py
python3 -m unittest tests.test_frozen_ai_web tests.test_frozen_ai_table_components tests.test_web_frozen_source_evidence
python3 tools/check_doc_link_integrity.py
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off AUTO_MANUAL_PRESENTATION_PROFILE=web python3 build.py check --config configs/config.us-en.yaml --model JE-1000F --region US --lang en --data-root tests/fixtures/phase2 --staging-root /tmp/jhp3600c-us-regression --skip-root-index
```

Operator visual confirmation of this English baseline is pending. No remote branch push, PR, merge, production RTD deployment or online record write is part of the completed local intake boundary.


## Local publication candidate

Previous candidate (superseded by the revised candidate below). Source commit: `7bf6b36750532f891968c1b3064e8ca9b50dd0ac`. At this exact ref the existing US regression gate passed again, the frozen MyST passed strict Sphinx, and [language evidence](jhp3600c_us_en_web_evidence/language_projection_receipt.json) sealed source inventory, version, commit, MyST and verification HTML.

A read-only archive of Hello-Docs/main at `83cc003714a81a6d8fa1e89b9b38829b76ed598e` supplied the existing `docs/publish/**` base. The shared assembler produced a local-only 106-target candidate. All 5,609 pre-existing files under `docs/publish/sources/**` remain byte-identical to that base; no target was removed. [Candidate fingerprint](jhp3600c_us_en_web_evidence/candidate.json).

Aggregate preflight passed:

```bash
python3 -m tools.publish_branch_assembly --releases-root tmp/jhp3600c-releases --output-dir /tmp/jhp3600c-publish-base/docs/publish
python3 -m sphinx -W -b html -D extensions=myst_parser,tools.rtd.portal /tmp/jhp3600c-publish-base/docs/publish/web /tmp/jhp3600c-publish-html
```

The portal emitted its local query corpus/deployment receipt, and every aggregate HTML image points to a packaged local file. These are local preflight receipts, not an RTD production build receipt. The final local page is `http://127.0.0.1:8765/JHP-3600C/US/en/md/manual_jhp3600c_us_en.html`; its desktop/mobile DOM and packaged images were checked. The short local alias is `http://127.0.0.1:8765/manual_jhp3600c_us_en.html`.

The candidate is assembled at `/tmp/jhp3600c-publish-base/docs/publish`, with isolated versioned release evidence under this worktree's `tmp/jhp3600c-releases`. Source and permanent QC evidence are committed in the engineering branch. Candidate publication/PR/merge/deployment and human English-baseline confirmation remain pending.

Mobile LCD scrolling was exercised: the table's scroll position advanced to 286 px within its 354 px figure while the page stayed 390 px wide. [Scrolled description view](jhp3600c_us_en_web_evidence/mobile-lcd-scrolled.jpg).

Final aggregate [desktop screenshot](jhp3600c_us_en_web_evidence/final-desktop.jpg) and [mobile screenshot](jhp3600c_us_en_web_evidence/final-mobile.jpg) record the actual portal candidate, including its language selector.


## Operator safety layout correction (layout3)

The operator's annotated screenshots showed that the previous local candidate's product-title bar, bullet-style safety heading and single-column safety body did not match physical p4. The prior content/build/overflow checks did not establish visual fidelity for this page.

The visible product-title bar is now suppressed while its Sphinx document identity and chapter navigation remain available. Safety uses a white-on-dark full-width chapter bar, a reused filled warning triangle with bold source label/risk text, the original 6+5 safety list split, and the original 5+9 operating list split. Both bold leads and nested temperature/ventilation subitems remain native selectable text; grounding stays full width. Shared safety styles stack the columns in source order at 640px and below. Frozen source-local `presentation.css` supplies the title/bar geometry and warning-column sizing without changing shared rendering or other targets.

No wording, values, warning labels or reading order changed: semantic leaf comparison against the preceding commit passed, and all other chapters remain structurally identical. There are now 84 asset decisions; the added triangle is a byte-identical shared SVG with explicit p4 provenance. All 1,128 positioned English/contact lines remain covered with no unmatched lines.

Current source commit: `10b89f4343a001bc9b91d5ccb8c4503a69d5ce7a`. Technical candidate version: `git-20261005-31fd0692-layout3`. The preceding sealed release remains intact; the revised release has a separate versioned directory and [new source receipt](jhp3600c_us_en_web_evidence/language_projection_receipt-layout3.json). Deterministic rebuild, cold IR replay, strict target Sphinx, Ruff and 26 shared replay/table/evidence tests passed. [Revised candidate fingerprint](jhp3600c_us_en_web_evidence/candidate-layout3.json) records 106 targets and all 5,609 pre-existing source files byte-identical to the read-only Hello-Docs base.

The local preview URL remains `http://127.0.0.1:8765/JHP-3600C/US/en/md/manual_jhp3600c_us_en.html`. [Desktop safety](jhp3600c_us_en_web_evidence/safety-desktop-layout3.jpg), [mobile safety](jhp3600c_us_en_web_evidence/safety-mobile-layout3.jpg), [mobile operating subitems](jhp3600c_us_en_web_evidence/safety-mobile-operating-layout3.jpg), [320px](jhp3600c_us_en_web_evidence/safety-narrow-layout3.jpg), [top without product bar](jhp3600c_us_en_web_evidence/top-without-product-bar-layout3.jpg) and [DOM measurements](jhp3600c_us_en_web_evidence/browser-safety-layout3.json) verify the actual assembled portal page. Desktop cells are equal-width and top-aligned; 390px/320px stack left then right, with viewport/document widths equal. The warning icon loads and all aggregate HTML images resolve to packaged local files. No push, PR, production publication or live data write occurred. Root `tmp/` was preserved.


The intermediate layout2 standalone preview passed, but the aggregate's global stylesheet did not load source-local CSS. The shared frozen replay now accepts a package-contained, hash-bound `source_stylesheet` declaration and retains its style block in MyST, so the existing assembler carries it into each document. Historical packages without that declaration retain their existing replay. A regression test covers aggregate HTML preservation, style tampering, path escape and HTML closure rejection. Layout3 passed strict standalone and aggregate Sphinx, deterministic rebuild/cold IR+CSS replay, Ruff, maintainability, document links and the existing-target US fixture check. This remains a local candidate pending operator visual approval, with no remote push or publication.

## Shared symbol correction and recurrence prevention (symbols1)

The original name/meaning-only reuse decision was wrong. Several common PNGs
contained cell backgrounds; the read-manual glyph was a person instead of the
source's open book/information mark, and the Li-ion artwork included an extra
`32`. The legacy decisions remain explicitly marked as superseded provenance.

Selection now starts at the shared [Web symbol catalog](../../docs/renderers/web/assets/shared/symbols/manifest.json).
Two existing native SVGs were repaired once in that common library (warning,
book/information), WEEE reuses the pre-existing shared PNG unchanged, and eight
missing suitable transparent variants are supplied once through the existing
asset-intake recipe. No per-language or per-model second library is introduced.
Every consumed target copy matches the selected shared variant byte-for-byte.
The variant assets remain local review candidates; no live registry promotion.

The catalog withdraws the eleven legacy asset hashes for new Web symbol tables.
Renaming or copying a withdrawn file does not restore eligibility. The legacy
print/Word source files and previous sealed releases are preserved. New external
frozen Web sealing requires complete actual ComponentSpec row coverage, explicit
shared glyph keys, unchanged shared bytes, authoritative PDF page/objects/caption
bindings, real alpha and normalized native-glyph comparison. No candidate metadata
can disable these checks. Historical stored receipts retain their sealed rules;
ordinary complete panels do not enter this small-symbol gate.

The source symbol captions are outlined. Their reviewed transcription and row
coordinates are bound to independently rendered source caption pixels; this is
not OCR or automated approval. Desktop/mobile and source comparisons remain
required. [Before/after and source artwork](jhp3600c_us_en_web_evidence/symbols-shared-before-after.png)
shows all eleven symbols on a checkerboard alongside the legacy and PDF artwork.

Validation: 84 focused tests pass, including renamed withdrawn bytes, RGB gray
background, RGBA rectangle, inset rectangle with transparent borders, transparent
wrong glyph after rehash, row/meaning swap, source/caption tampering, traversal,
shared-byte mismatch, preservation of original group opacity, native SVG recipe
extraction, and seal rejection before evidence creation. Ruff, maintainability,
doc links, source line coverage, deterministic rebuild and strict standalone and
aggregate Sphinx pass. The US JE-1000F check is an existing-target regression only;
its missing local Spec_Master snapshot is reported by the command and is not a
JHP-3600C content check.

The preceding full run tested 5,180 cases with one existing macOS path-alias error
(`/var` versus `/private/var`) in identity provenance. The unchanged test passes
with canonical `TMPDIR=/private/tmp`; the complete suite passes with that setting for this change: **5,194 tests
in 745.862 seconds, 35 skipped**. No unrelated identity-path repair is included.

Local browser checks: 1440px uses two equal symbol panels; 390px and 320px stack
panels in native order with no page overflow. All eleven symbol images load and
all page images resolve. [Desktop](jhp3600c_us_en_web_evidence/symbols-desktop-symbols1.jpg),
[desktop lower](jhp3600c_us_en_web_evidence/symbols-desktop-lower-symbols1.jpg),
[mobile](jhp3600c_us_en_web_evidence/symbols-mobile-symbols1.jpg),
[mobile right panel](jhp3600c_us_en_web_evidence/symbols-mobile-right-symbols1.jpg),
[narrow](jhp3600c_us_en_web_evidence/symbols-narrow-symbols1.jpg).
Root `tmp/` is untouched; this remains an isolated Git-only local candidate.

Final source commit: `c6206a0a1dde99817aee3b324d267be5d883d18e`; candidate version:
`git-20261005-31fd0692-symbols1`. [Fresh source receipt](jhp3600c_us_en_web_evidence/language_projection_receipt-symbols1.json)
verifies at that commit. [Validation record](jhp3600c_us_en_web_evidence/validation-symbols1.json),
[withdrawn-byte record](jhp3600c_us_en_web_evidence/withdrawn-symbols1.json),
[browser measurements](jhp3600c_us_en_web_evidence/browser-symbols1.json) and
[final candidate fingerprint](jhp3600c_us_en_web_evidence/candidate-symbols1.json)
record the boundary. The final 106-target assembly preserves all 5,609 original
source files byte-for-byte and passes strict Sphinx. The final local preview was
reloaded and checked against the selected shared symbol pool. No push, PR, merge,
production deployment or online data/registry write occurred.


## Operator FCC heading correction (fcc1)

The annotated Web screenshot requests removal of the added visible “● FCC”
chapter heading. Native physical p6 starts directly with the compliance card.
Source-local `presentation.css` suppresses that heading, including its generated
bullet and layout box; the FCC chapter anchor, original compliance component,
copy and artwork are unchanged. The technical candidate version is
`git-20261005-31fd0692-fcc1`; previous sealed releases remain intact.

Deterministic rebuild and strict standalone Sphinx pass. The correction is
limited to this source package and stays in the isolated Git-only worktree.

Source commit: `2302c2580222def3d217e8dbe506f9527c3724f7`.
[Fresh receipt](jhp3600c_us_en_web_evidence/language_projection_receipt-fcc1.json),
[validation](jhp3600c_us_en_web_evidence/validation-fcc1.json) and
[browser measurements](jhp3600c_us_en_web_evidence/browser-fcc1.json) bind the result.
All 18 focused frozen replay/evidence tests pass, as do document links and
strict aggregate Sphinx. The 106-target assembly preserves all 5,609 original
Hello-Docs source files byte-for-byte. At 1440px the FCC card retains two equal
columns; at 390px it stacks in order, with no page overflow. The visible heading
has zero layout height on both. [Desktop](jhp3600c_us_en_web_evidence/fcc-desktop-fcc1.jpg),
[mobile](jhp3600c_us_en_web_evidence/fcc-mobile-fcc1.jpg) and
[restored user pane](jhp3600c_us_en_web_evidence/fcc-final-preview-fcc1.jpg) record
the local preview. This correction has not been pushed or published.


## Operator overview heading correction (overview1)

Native physical p7 (printed p04) has a full-width dark PRODUCT OVERVIEW bar
with white copy, followed by flush-left round FRONT VIEW / RIGHT SIDE VIEW
markers. The generic Web H2 marker style missed the bar, and theme H3 padding
added an 8px inset. Source-local CSS restores the bar with shared color/radius
tokens and removes that inset while using the native-sized round markers.
The existing complete labeled front/side artwork is reused without extraction
or byte changes; semantic copy is byte-identical to the previous source.

Technical version: `git-20261005-31fd0692-overview1`. Deterministic rebuild
and strict standalone Sphinx pass. The preceding releases remain sealed.

Source commit: `d89212af49cfbcb08a57b1f6e23e682a390d59d5`.
[Fresh receipt](jhp3600c_us_en_web_evidence/language_projection_receipt-overview1.json),
[validation](jhp3600c_us_en_web_evidence/validation-overview1.json) and
[browser measurements](jhp3600c_us_en_web_evidence/browser-overview1.json) record
the result. Strict aggregate Sphinx and document links pass. The assembly
retains 106 targets and preserves all 5,609 pre-existing source files byte-for-byte.
At 1440px and 390px the dark/white bar spans the artwork band; both view markers
have zero padding and share its left edge. Both original images load and the
page has no horizontal overflow. The FCC heading remains hidden.
[Desktop](jhp3600c_us_en_web_evidence/overview-desktop-overview1.jpg),
[mobile](jhp3600c_us_en_web_evidence/overview-mobile-overview1.jpg) and
[restored user pane](jhp3600c_us_en_web_evidence/overview-final-preview-overview1.jpg)
show the local candidate. Root `tmp/` stays untouched; no remote push or publication.


## Operator LCD status emphasis correction (lcdstatus1)

The LCD description table now marks all leading status words with explicit
`strong` emphasis in its existing ComponentSpec rich HTML: 12 `On:`, 4 `Blink:`
and 12 `Off:` labels across rows 1, 2, 3, 4, 6, 8, 9, 19, 22, 24, 25 and 27.
The rich-text input carries the correction through shared rendering and frozen
replay. Removing only those new tags reproduces the previous semantic source
exactly; wording, plain-text fields, icons and other rows are unchanged.

Technical version: `git-20261005-31fd0692-lcdstatus1`. Deterministic rebuild,
source line coverage and strict standalone Sphinx pass. Previous seals remain.

Source commit: `50db389f24bbb3fe98c3d9d300c2718e72a5c5a8`.
[Fresh receipt](jhp3600c_us_en_web_evidence/language_projection_receipt-lcdstatus1.json),
[validation](jhp3600c_us_en_web_evidence/validation-lcdstatus1.json) and
[browser measurements](jhp3600c_us_en_web_evidence/browser-lcdstatus1.json) bind
the result. Strict aggregate Sphinx passes. The 106-target assembly retains
all 5,609 existing source files unchanged. Browser checks at 1440px and 390px
confirm all 28 labels have computed weight 700 while their paragraph weight
stays 400; no leading status label is unmarked. The existing mobile LCD table
scrolls to its description column (286px), with no page overflow.
[Desktop](jhp3600c_us_en_web_evidence/lcdstatus-desktop-lcdstatus1.jpg),
[mobile description](jhp3600c_us_en_web_evidence/lcdstatus-mobile-lcdstatus1.jpg)
and [restored user pane](jhp3600c_us_en_web_evidence/lcdstatus-final-preview-lcdstatus1.jpg)
show the corrected local preview. Root `tmp/` remains untouched; no push or publication.


## Whole-manual shared heading correction (headings3)

The stylesheet was loaded, but the whole-book intake shifted native chapter
H1 to H2 and section H2 to H3 beneath a synthetic document title. Generic H2
round markers and theme H3 padding therefore replaced chapter bars and native
section markers. Earlier safety/overview CSS fixed individual symptoms only.

[Heading review inventory](../../data/manual_sources/JHP-3600C/US/en/git-20261005-31fd0692/source/heading_audit.json)
records all 84 flow and specification-carrier headings with original physical
pages and reviewed roles. Native chapter/product bars now use actual H1 and
native section markers use H2, directly consuming the existing shared
`web_manual.css`. The duplicate overview and major safety title CSS is removed.
No new renderer, family stylesheet, model-specific global rule or asset exists.

Original exceptions remain explicit: plain preface; hidden synthetic document,
FCC/contact and panel labels; safety subsection strips; six shared warranty card
tabs; numbered App steps; six small gray labels. The two accessory product bars
use native H1. Thirteen specification group headings carry accessible level 2;
the duplicate ATS component label is hidden beneath its source product bar.

Technical version: `git-20261005-31fd0692-headings3`. All 84 actual standalone
HTML headings match the reviewed source level in order. Removing only heading
metadata reproduces the previous semantic source exactly: body wording,
component semantics and artwork are unchanged. Deterministic rebuild,
source coverage, strict standalone Sphinx and document links pass.

The interim headings1 browser check found that Furo hides the TOC when the first
H1 has no child heading. The plain preface remains at level 2 under the hidden
document identity, while native chapter bars remain H1 siblings. Existing Furo
navigation is thus preserved without a template fork or extension. A stronger
source selector also hides the redundant ATS carrier against generic H2 rules.
Headings2 is a separately sealed candidate; the interim release stays intact.

A hash-target browser regression exposed Furo's transparent heading highlight
overriding the native safety subbar fill while retaining white copy. The source
exception now outranks that theme selector. Final version is headings3; both
interim sealed releases remain available for provenance.


## Key combinations and accessory labels (styles4)

The operator identified a generic table in place of the native key-combination
panel, and availability copy flattened into seven titles. The key table now
declares the existing `HB-TABLE-KEY-COMBINATIONS` ComponentSpec with its original
three-column copy and a native carrier. Shared CSS owns the gray first column,
white operation/function columns, paired button captions with POWER/USB/AC
emphasis, plus signs, and shared CSS clocks for 3s/3s/1s. The component scrolls
inside its frame on narrow screens. Seven `SOLD SEPARATELY` labels use the shared
dark rounded badge; inline heading spans survive MyST replay and navigation.

Visual inventory exposed a separate artwork mismatch: old shared POWER/AC marks
were above their switches, and DC/USB did not match native USB. Three original
PDF p13 lower-marking variants are added to the existing shared button directory
as Git review candidates. The new recipe retains every path inside each glyph,
including circular face, border, switch, indicator and outlined marking, while
excluding the table backdrop. No colors or strokes are changed. Existing assets
remain intact; prior target bindings record their superseded status. No online
registry promotion is performed in this Git-only task.

MuPDF emits filled-and-stroked objects as two SVG paths on this page. The shared
vector selector now accepts the verified paired mapping and retains both paths
and ancestor transforms/opacity; unsupported mappings still fail. A regression
checks transparent edges, a white face, and a black indicator. Source line
coverage still has zero unmatched lines. Final browser/build evidence follows.


Final source commit: `36a2629946ab01dbd40079a7c23552b0b98203f2`, including the
heading correction at `c12696732e1f5464564d373e4f02ec2c584a0d30`.
[Seal receipt](jhp3600c_us_en_web_evidence/language_projection_receipt-styles4.json),
[validation](jhp3600c_us_en_web_evidence/validation-styles4.json) and
[browser measurements](jhp3600c_us_en_web_evidence/browser-styles4.json) bind the
final `git-20261005-31fd0692-styles4` local candidate. All 84 heading roles, native
levels, hidden exceptions, bar colors and round-marker alignment pass at 1440px,
390px and 320px. Hash-targeted safety strips retain their dark/white treatment.
All 28 LCD status labels remain weight 700. Seven availability labels have
rounded source-appropriate contrast: dark/white on ordinary headings and
white/dark inside accessory chapter bars. No page overflows; narrow key tables
scroll inside their own frame. All six button image references load unchanged
from the three shared variants; POWER/USB/AC captions are weight 700.

Strict standalone and aggregate Sphinx, byte-identical replay, source coverage,
ruff, maintainability and doc links pass. Full unittest: 5,196 tests, 35 skipped;
final focused tests: 33 pass. The 106-target assembly preserves all 5,609 baseline
source files byte-for-byte. The generic JE-1000F US fixture check cannot complete
because this isolated checkout lacks its local phase2 snapshot; the failed
command and output are recorded in validation. No online synchronization was
performed, and no PR is opened with an incomplete generic fixture check.

Visual evidence: [headings desktop](jhp3600c_us_en_web_evidence/headings-desktop-styles4.jpg),
[headings mobile](jhp3600c_us_en_web_evidence/headings-mobile-styles4.jpg),
[key table desktop](jhp3600c_us_en_web_evidence/key-combinations-desktop-styles4.jpg),
[mobile buttons](jhp3600c_us_en_web_evidence/key-combinations-mobile-buttons-styles4.jpg),
[mobile operation column](jhp3600c_us_en_web_evidence/key-combinations-mobile-operation-styles4.jpg),
[availability desktop](jhp3600c_us_en_web_evidence/sold-separately-desktop-styles4.jpg),
[availability mobile](jhp3600c_us_en_web_evidence/sold-separately-mobile-styles4.jpg),
[12x original-vector variants](jhp3600c_us_en_web_evidence/native-buttons-12x-styles4.png),
and [restored user pane](jhp3600c_us_en_web_evidence/final-preview-styles4.jpg).
The browser viewport is restored to its default 641×770 pane. Root `tmp/` remains
untouched. This records local browser acceptance only; operator approval and
production publication remain separate.
