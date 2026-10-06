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

## car1 — Native car labels and CSS-only caption frame (2026-10-06)

The p24 car figure used text-stripped artwork but retained its empty white
capsule. Its source text was only represented approximately by ALT. The new
source uses the existing `HB-SPECIAL-REFERENCE-FIGURE` / `base-art-live-copy`
component with exact, selectable `Vehicle` and
`*The car charging cable is sold separately.` labels. The capsule is drawn by
shared `.hb-reference-live-pill`; the full native gray panel stays in the art.

The same-model and shared inventory remains in `source/asset_decisions.json`.
No available shared figure matches this US housing/port geometry. The corrected
asset is replayable through `manual_jhp3600c_us_car_framefree.json`, with the
original PDF hash, p24 crop, retained drawing indices and excluded caption
object 1068. Generic retained-path SVG export now preserves source clipping,
opacity and transforms; symbol reconstruction still requires every drawing
inside the glyph bounds. The old PNG is retained for traceability and marked
`superseded-do-not-reuse`; it fails the new caption-region check.

The shared artwork contract, Codex extraction skill, UI prompt and operator
playbook prohibit acquiring/reusing independent empty caption frames and require
bare-art review before CSS labels. Fresh frozen-Web sealing checks actual
ReferenceFigure specs, bound asset hashes and contrasting CSS fill rectangles.
A baked fill occupying >=85% of the inset rectangle fails. Same-tone,
outline-only and undeclared frames still require visual review; this check is
not OCR or an arbitrary image classifier. Historical receipt verification is
unchanged. No live asset registry promotion or online writes were performed.

Completed before source commit: 37 focused regressions, repository ruff,
maintainability guardrails, skill quick validation, document links, source line
coverage (zero unmatched), recipe pipeline byte parity, deterministic source
replay and strict standalone Sphinx. Bare SVG inspected in-browser at 12x;
standalone desktop, 390px and 320px show the exact labels, CSS capsule and no
page overflow. At 320px the CSS capsule grows to two lines.

Full-suite results, final aggregate browser checks and source-HEAD receipt are
recorded separately in the car1 evidence after completion. The generic
`build.py check --config configs/config.us-en.yaml --model JE-1000F --region US`
remains blocked by this worktree's missing local `data/phase2/Spec_Master.csv`;
no unrelated snapshot was fabricated or synchronized under Git-only scope.

car1 final acceptance: source commit `49c3d8ff47f6f663c977398992f9c369912ca851`,
version `git-20261005-31fd0692-car1`; full unittest **5,203 passed, 35 skipped,
837.624s**. Fresh receipt verified against the exact source commit. Strict
aggregate Sphinx passed after removing this turn's temporary preview symlink
from the output tree; the receipt's symlink rejection was kept intact. Aggregate
contains 106 targets and all 5,609 baseline source files remain byte-identical.
Final browser assertions passed at 1440/390/320: 84 heading roles, 28 bold LCD
status labels, seven availability pills, loaded shared key-combination artwork,
two live car labels, one CSS caption capsule, no old car PNG reference and no
page/label overflow. Primary checkout still has only its pre-existing `tmp/`.

Evidence: [validation](jhp3600c_us_en_web_evidence/validation-car1.json),
[browser DOM](jhp3600c_us_en_web_evidence/browser-car1.json),
[source-HEAD receipt](jhp3600c_us_en_web_evidence/language_projection_receipt-car1.json),
[desktop](jhp3600c_us_en_web_evidence/car-caption-desktop-car1.png),
[390px](jhp3600c_us_en_web_evidence/car-caption-mobile-car1.png),
[320px](jhp3600c_us_en_web_evidence/car-caption-320-car1.png),
[bare native art at 12x](jhp3600c_us_en_web_evidence/native-car-framefree-12x-car1.png),
[baseline parity](jhp3600c_us_en_web_evidence/baseline-source-parity-car1.json), and
[final user-window preview](jhp3600c_us_en_web_evidence/final-preview-car1.png).
Local commits only; no push/PR/merge/publication. The generic phase2 fixture
check limitation above remains explicit and is not counted as a passing check.

## App shared download and inline control correction (app1)

Physical p28 now uses the existing `HB-SPECIAL-APP/download` component with two artwork-over-copy columns. Store badges and the complete Jackery QR are byte-identical copies of `docs/renderers/contracts/assets/app/app_store_badges.png` and `app_download_qr.png`. Apple Vision independently decoded the shared QR, the retained source crop and the rendered native p28 to `https://download.jackery.com/app/jackery.html`. The old combined crop is retained for traceability with `superseded-do-not-reuse`; no generated document references it. Complete phone screenshots remain unchanged.

Step 2.1 uses the existing `HB-SPECIAL-APP/inline-control` and shared `.hb-inline-add-device-icon`; step 2.2 restores native bold `POWER` and `"Icon Flashed"`. The source-local coverage audit now assembles rich paragraph spans through the existing flow HTML API before matching native lines, so bold boundaries do not create false missing-text reports. No shared renderer or CSS logic changes.

The 26 relevant App component/IR tests passed (one skipped), ruff passed, source-native coverage has zero unmatched lines, strict standalone Sphinx passed, and frozen output replay is byte-identical. Final aggregate browser evidence is recorded separately after sealing the source commit. This remains a local Git-only candidate.

Final app1 acceptance: strict aggregate Sphinx passed for 106 targets; all 5,609 baseline source files remain byte-identical. Desktop 1440px, mobile 390px and narrow 320px show two artwork-over-copy columns, the shared circular plus, native bold spans and no document overflow. All 84 heading roles, 28 bold LCD status labels, seven SOLD pills and the key table passed regression checks; the CSS car caption still passes. See [App validation](jhp3600c_us_en_web_evidence/validation-app1.json), [browser evidence](jhp3600c_us_en_web_evidence/browser-app1.json), [desktop](jhp3600c_us_en_web_evidence/desktop-app1.png) and [mobile](jhp3600c_us_en_web_evidence/mobile-app1.png). Source commit: `6c72996742b72f226a8052dcab65627e89ca05d7`. No full-suite repeat was needed for the unchanged shared renderer; relevant App tests and the source-local rich-span audit negative control passed.

## App phone artwork size correction (app2)

The complete two-phone `app_add.png` source now declares the existing `hb-app-add-device-phone-art hb-app-phone-pair` shared classes, limiting its centered display to `min(100%, 22rem)`. The three-phone result uses the existing `hb-app-phone-trio` limit of `36.75rem`. These are source presentation bindings; shared CSS, phone artwork bytes, full frames and embedded native step numbers are unchanged. Strict source/aggregate builds and desktop/mobile evidence are recorded in the app2 validation artifact.

App2 accepted at 1440px, 390px and 320px: centered pair widths 352px / 352px / 288px and trio widths 588px / 358px / 288px match the unchanged shared CSS limits. Aspect ratios and original asset hashes are preserved, parent overflow remains visible, and document widths equal viewports. Source-native coverage is zero unmatched, 107 replay files are byte-identical, strict standalone/aggregate Sphinx passed, and all 5,609 baseline source files are unchanged. Prior 84 heading roles, bold status words and App emphasis remain correct. [Size validation](jhp3600c_us_en_web_evidence/validation-app2.json), [current preview](jhp3600c_us_en_web_evidence/preview-app2.png). Source commit: `c4e352ec0e80a552a21a7816b04a5ae4d52af663`.

## Shared reference screenshot reuse (app3)

The user explicitly marked the cropped three-phone result image “用共用图啊 边缘不完整”. The candidate now reuses `docs/renderers/contracts/assets/app/app_connect_result_steps.png` byte-identically, with SHA-256 `17ccfa065009948c9e6e661017fab0b261adac03d880c025178d207e2f47ffe3`. All phone corners, status bars, bottom controls and steps 2.3/2.4/2.5 are present. The original crop is retained only for traceability and marked `superseded-do-not-reuse`. The unchanged shared `hb-app-phone-trio` size rule remains in use.

This is an explicit reference-UI exception: the shared demonstration displays Explorer 1000 / 80% / 25°C / DC and AC, whereas the native screenshot displays HomePower 3600 Pro Max / 100% / 33°C / USB, AC and DC. The native functional instructions, product specifications and identity elsewhere remain authoritative; the source sentence “The above screenshots are for reference only.” is now selectable Web copy after the image. The image alt identifies it as a generic Explorer 1000 example. No screenshot was cropped or edited, and no shared renderer/CSS logic changed.

App3 accepted at 1440px, 390px and 320px: the complete shared image loads at the existing trio limit, centered with unchanged aspect ratio and no clipping/overflow. Exactly one selectable reference-only paragraph follows it. There are zero references to the retired cropped result. Native-source line coverage is zero unmatched, 108 frozen replay files are byte-identical, strict standalone/aggregate Sphinx passed, and 5,609 baseline files remain unchanged. [Shared-art validation](jhp3600c_us_en_web_evidence/validation-app3.json), [preview](jhp3600c_us_en_web_evidence/preview-app3.png). Source commit: `e12ab22b09c4d9f715a61816858961009c659f88`.

## ESS source labels, model strips and warning correction (ess1)

The unchanged `ess_connection.png` is now bound to existing ReferenceFigure `base-art-live-copy` with all three native p30 captions inside their source rectangles: the ATS power cable, expansion cable and installation-reference footnote. Full panel edges are preserved; the three former image-following paragraphs are removed from display. No bitmap is edited or extracted.

The p30 ESS title and p31 SPECIFICATIONS title carry their original `Model:` labels inside the same navigable H1 using shared `hb-heading-model`. The invented “— SMART HOME BACKUP SYSTEM” suffix is removed from the visible p31 title; its distinct source anchor remains. The warning uses the existing callout component and shared dark transparent triangle, restoring a white outlined whole-row warning with bold native body via `hb-source-warning-lockup`. Shared CSS owns these declarations and mobile stacking.

Narrow-screen follow-up (ess2): the heading permalink is absolutely positioned within the model strip, preserving keyboard access without adding a blank flex row at 320px. The source/artwork and native text remain unchanged.

Final ESS acceptance (ess2): source commit `5be6bdf2a3d6d5dfe22ec57d57e08e5ddf1f706f`. Strict standalone and 106-target aggregate builds passed. All 108 replay files and all 5,609 baseline source files are byte-identical. The 17 focused ReferenceFigure/callout regressions passed; native-source coverage is zero unmatched. Final 1440px/390px/320px browser assertions confirm three contained selectable captions, two model labels inside their H1 strips, white/dark-outline warning with loaded shared triangle and 700-weight body, no broken images or document overflow. Previous 84 heading roles, 28 bold status labels, seven availability pills and key artwork pass. No full-suite repeat is needed for this source/CSS repair without shared Python logic changes.

Evidence: [validation](jhp3600c_us_en_web_evidence/validation-ess2.json), [browser](jhp3600c_us_en_web_evidence/browser-ess2.json), [source receipt](jhp3600c_us_en_web_evidence/language_projection_receipt-ess2.json), [desktop diagram](jhp3600c_us_en_web_evidence/desktop-ess2.png), [title and warning](jhp3600c_us_en_web_evidence/title-warning-desktop-ess2.png), [specifications](jhp3600c_us_en_web_evidence/specifications-desktop-ess2.png), [390px](jhp3600c_us_en_web_evidence/mobile-ess2.png), [320px diagram](jhp3600c_us_en_web_evidence/narrow-ess2.png), and [320px specifications](jhp3600c_us_en_web_evidence/specifications-narrow-ess2.png). Local Git only; no push/PR/merge/publication or online writes. The primary checkout remains untouched with its pre-existing `tmp/`.

## Product title availability recheck (sold2)

The operator highlighted the Battery Pack 3600 and Automatic Transfer Switch title availability labels against native pp32–33. Current ess2 source already splits both headings into `hb-heading-title` and the existing shared `hb-sold-separately` span. A fresh browser inspection confirms one white pill per dark product strip, dark 700-weight text, 999px radius, no visible dash, and contained labels without page overflow at 1440px, 390px and 320px. No source, artwork or CSS modification was required. [Current desktop evidence](jhp3600c_us_en_web_evidence/sold-product-desktop-sold2.png) and [DOM checks](jhp3600c_us_en_web_evidence/browser-sold2.json) record this acceptance. The preview was refreshed and positioned on the product section. Local evidence commit only.

## PACKAGE LIST reuse decisions before extraction (package1)

| Slot | Candidates checked | Identity/content | Decision and reason | Source | Boundary policy |
| --- | --- | --- | --- | --- | --- |
| Station items | Frozen `inbox_unit.png`, `inbox_ac.png`, `inbox_terminal.png`, common `manual_icon1.png` | Same JHP-3600C front silhouette, US charging plug, terminal and document icon | Reuse existing bytes; no extraction | Existing p6 assets and shared document icon | CSS whole-panel outline; editable labels |
| Battery items | `docs/renderers/web/assets/jbp3600a_eu_en/inbox_unit_clean.png`, `inbox_cable_clean.png`, shared document icon | Same JBP-3600A front silhouette and expansion cable; no region-specific ports exposed | Reuse existing bytes; generic document pictogram replaces English cover miniature for language-neutral illustration | Existing clean package art | CSS dashed outline and availability capsule |
| ATS items | Target panels, manual_sources, Web/LaTeX assets, template common assets and asset recipes | No complete matching JA-TS05A, marking template, power cable, neutral wire, gland or bonding jumper individual art | Extract six original illustrations because existing three-panel PNGs clip the upper outline and contain copy | Native PDF physical p34 | No baked frame/caption text; CSS panel outline and item labels |
| Availability label | Existing shared capsule rules and native p34 | Decorative cart and gray caption capsule | Draw both capsule and decorative cart with CSS; no new glyph asset | Native p34 visual reference | Native selectable Sold separately wording |

All document covers use the existing generic document icon, with native selectable labels distinguishing User Manual, Owner's Manual, Installation Manual and Quick Start Guide. Tiny cover text is illustrative detail and will be explicitly recorded as omitted, not counted as preserved copy. New art is a Git-only quarantined candidate; no online registry write is in scope.

Native SVG selection on p34 fails the existing fill/stroke mapping guard. The six needed illustrations therefore use the existing crop-only high-resolution PNG pipeline, preserving original clipping and opacity. No mapping guard is weakened and no paths are replayed into an unclipped drawing.

#### PACKAGE LIST editable groups — package1

- Physical p34 three groups now use shared package panel/list CSS, native captions, complete solid/dashed outlines and CSS availability capsules/cart. 4/3/9 item labels preserve native order; mobile uses two columns. No empty text frame or capsule remains in bound item art.
- Reused station unit/AC/terminal bytes are exposed under `jhp3600c_us_shared`; battery/cable reuse existing `jbp3600a_eu_en`; all document illustrations reuse `common_assets/in_the_box/manual_icon1.png`. Six ATS assets use the pinned crop-only quarantine recipe; native source 12x four-edge inspection and repeat pipeline bytes agree. Product/template fixed printed markings remain.
- Retired whole package panels remain traceable as `superseded-do-not-reuse`. Their bboxes are excluded from coverage. `illustrative_detail_omissions.json` explicitly records the four miniature covers; native item labels remain visible. The audit excludes image paths/CSS/anchors from the semantic corpus; removing the Neutral Wire caption is correctly rejected by a negative control.
- Source-local replay and audit also reject any rebinding of retired package art; a negative control for `ess_station_package.png` passed. This keeps old bytes for traceability without allowing future accidental reuse.
- Focused Manual Flow/render contract/Web presentation tests passed (89); Ruff, doc links, source-native coverage (zero unmatched), strict standalone Sphinx and 116-file byte-identical replay passed. Browser 1440/390/320 verified all images loaded, 16 editable item labels, complete CSS borders, two availability labels and no horizontal overflow.

Final local package1 source commit: `be3ad420f7fb7ea86c1bed54073cff3cd56c34ed`; technical version `git-20261005-31fd0692-package1`. [Sealed receipt](jhp3600c_us_en_web_evidence/language_projection_receipt-package1.json) pins this source, frozen MyST and strict standalone HTML. Aggregate strict Sphinx passed for 106 targets; all 5,609 baseline source files remain byte-identical ([fingerprint](jhp3600c_us_en_web_evidence/candidate-package1.json)). The canonical port8765 preview now serves these three editable package groups. [Final desktop](jhp3600c_us_en_web_evidence/package1-final-desktop.png) and [mobile](jhp3600c_us_en_web_evidence/package1-final-mobile.png) show the actual aggregated page. Desktop/390px/320px DOM audits verify no overflow, all art loaded, all native item labels present, and no retired package image bound. Existing 84 heading roles and 7 heading availability pills are preserved. Local-only: no push, PR, merge, publication or live-data write. Root `tmp/` and earlier sealed releases remain intact.

#### Charging introduction — charging1

Physical p21: restored native bold `Green energy first:` and split `Fully charge the product before its first use.` into its own selectable dark/white/bold prose capsule using shared `hb-prose-pill`. Native wording remains byte-identical after joining the two paragraphs with a space; all other chapters are identical to package1. No artwork, callout severity or title hierarchy changes.

Native font inspection confirms the first-charge capsule uses 6.6pt bold vs 6.0pt body. Shared prose capsule therefore uses 1.1em, preserving this ratio (charging2).

Final charging2 source commit: `169ee17e8f18c4372dad4d6689e89dc59788e7e2`. Strict standalone and 106-target aggregate Sphinx passed; 116 frozen files replay byte-identically, source-native coverage has zero unmatched lines, and all 5,609 baseline source files remain byte-identical. [Sealed receipt](jhp3600c_us_en_web_evidence/language_projection_receipt-charging2.json), [candidate](jhp3600c_us_en_web_evidence/candidate-charging2.json), [desktop](jhp3600c_us_en_web_evidence/charging2-final-desktop.png), [mobile](jhp3600c_us_en_web_evidence/charging2-final-mobile.png), [320px](jhp3600c_us_en_web_evidence/charging2-narrow.png) and [DOM audit](jhp3600c_us_en_web_evidence/charging2-final-audit.json) record bold 700, white text on brand-dark fill, separate paragraph, no overflow, and the unchanged 84 headings. Original local preview refreshed. Only local commits; root `tmp/`, all earlier releases and unrelated target sources are preserved.

#### 120V charging native inset caption — charge120

Physical p21: moved `Connect the AC charging cable to the AC input port of the product and a wall outlet.` into the existing ReferenceFigure base-art-live-copy component at the native lower-right rectangle. The current textless `charge120.png` is byte-identical (SHA-256 `378983dcedd288cc23b4752b949ca53ddf98dcf5a1334ce6b0319c59a0e3ecbb`); complete source edges retained. Removed separate visible paragraph; no copy rewording or duplicate text. Shared `hb-reference-contained-copy` keeps the component's readable mobile labels within the same gray frame. No new artwork extraction, registry, schema or renderer adapter.

The reused crop contains six white exterior page-bleed rows (309–314/315) below its complete gray frame (last border rows306–308). Source geometry declares `--hb-art-page-bleed-bottom:1.9%` so mobile CSS hides only this outside white strip against the panel tone. The gray frame/product drawing and asset bytes remain intact; no global color removal or asset recrop. Desktop uses the source 6pt/316pt caption ratio (1.9cqw) and mobile keeps 0.88rem text.
