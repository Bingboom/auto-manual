# Build guide: IDML flow mode, InDesign finalize and parity

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

`idml` defaults to the production exporter. The separate design-template flow
mode writes semantic Markdown, a continuous-story editable IDML, a style map,
and trace files under `docs/_build/<model>/<region>/<lang>/idml/flow/`:

```bash
python3 build.py idml --model JE-1000F --region US --idml-mode flow
python3 build.py idml --model JE-1000F --region US --idml-mode both
```

When `--source auto` is used, a target with an approved reference-layout plan
is assembled from its committed review bundle exactly as `review-asis`; this
keeps the approved source order, including review-owned TOC/back-cover pages.
An explicit source selection is never rewritten. Targets without an approved
plan retain the runtime default and historical fallback pagination.

The flow artifacts remain generated handoff files, not a new content source.
Registered components become editable objects, images become linked frames,
and Markdown tables become native tables; raw serialized JSON must not become
visible document content.

On a provisioned macOS design host, close any older copy of the target INDD,
then create the native INDD, export with the frozen print contract, and write
the runtime preflight:

```bash
python3 -m tools.indesign_finalize \
  --idml docs/_build/JE-1000F/US/idml/manual_je1000f_us.idml \
  --indd output/indesign/JE-1000F_US_same_source.indd \
  --pdf output/pdf/JE-1000F_US_indesign.pdf \
  --report output/indesign/JE-1000F_US_preflight.json \
  --pdf-preset '[PDF/X-4:2008 (Japan)]' \
  --output-intent 'Japan Color 2001 Coated' \
  --output-condition JC200103 \
  --pdfx PDF/X-4
```

Keep the generated `Document fonts/` directory beside the output INDD.  The
finalizer now saves the INDD, closes it, reopens that saved file, recomposes it,
and repeats the overset/font/link preflight before exporting the PDF.  Reports
use `indesign-preflight/v2` and record this second pass under `post_reopen`.
The job fails when the saved document changes page/story count, reopens with a
`NOT_AVAILABLE`/substituted font, or gains an overset/bad link.  This catches
document-font failures that are invisible during the first IDML import.

For a design host processing more than one target, use an explicit
`indesign-finalize-jobs/v1` manifest. Every job must declare its PDF preset,
output intent, output condition, and PDF/X level; batch mode deliberately has
no print-contract defaults, so a missing ICC or preset cannot silently inherit
the wrong host setting:

```json
{
  "schema_version": "indesign-finalize-jobs/v1",
  "aggregate_report": "finalize.aggregate.json",
  "jobs": [
    {
      "id": "je1000f-us-en",
      "idml": "je1000f-us-en/manual_je1000f_us_en.idml",
      "indd": "je1000f-us-en/manual_je1000f_us_en.indd",
      "pdf": "je1000f-us-en/manual_je1000f_us_en_indesign.pdf",
      "report": "je1000f-us-en/finalize_report.json",
      "pdf_preset": "[PDF/X-4:2008 (Japan)]",
      "output_intent": "Japan Color 2001 Coated",
      "output_condition": "JC200103",
      "pdfx": "PDF/X-4",
      "application": "Adobe InDesign 2026"
    }
  ]
}
```

Run it with:

```bash
python3 -m tools.indesign_finalize --jobs /path/to/finalize.jobs.json
```

The batch validates the full manifest before opening InDesign, checks the
version pin once, isolates each job's failure, and writes one aggregate JSON
with per-job preflight summaries. It also scans each job's IDML directory
before and after the run and groups `indesign_package.complete=FALSE` results
for handoff follow-up. Jobs are grouped by their explicit `application` value.
Each group is dispatched to InDesign once, then an ExtendScript outer loop
finalizes the documents sequentially with a per-document try/catch and report.
One document can therefore fail without preventing the remaining documents in
that application group from running. Different InDesign application names use
separate dispatches, and single-job mode remains unchanged.

After PDF export, the Python wrapper also scans every retained text trace in
the final PDF. A visible replacement character (`U+FFFD`) or `.notdef` glyph
(`glyph_id=0`) fails the job even when InDesign reports every font as
installed. Because the scan runs on the assembled PDF, it covers native
InDesign stories and text retained inside placed PDF graphics. Findings are
recorded in `missing_glyphs` and `pdf_glyph_validation`; rasterized or outlined
art still requires visual review because it no longer contains inspectable PDF
glyphs.

Compare that InDesign export to the supplied approved PDF, not to the newly
built LaTeX PDF. `--latex-pdf` is retained as a legacy CLI flag name; its value
for this workflow is the approved reference PDF:

```bash
python3 -m tools.idml_pdf_parity \
  --latex-pdf <approved-reference.pdf> \
  --indesign-pdf output/pdf/JE-1000F_US_indesign.pdf \
  --preflight output/indesign/JE-1000F_US_preflight.json \
  --manual-ir docs/_build/JE-1000F/US/idml/manual.ir.json \
  --reference-layout-plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --idml docs/_build/JE-1000F/US/idml/manual_je1000f_us.idml \
  --indd output/indesign/JE-1000F_US_same_source.indd \
  --pages all \
  --out output/comparison/JE-1000F_US_same_source_parity.json
```

The approved contract supplies a visual hard gate; CLI overrides may not
loosen it:

| Render/check setting | Required value |
| --- | ---: |
| Rasterization | 300 dpi, RGB |
| Raster size | `1537 × 2187 px` on every page |
| Display ICC SHA-256 | `2b3aa1645779a9e634744faf9b01e9102b0c9b88fd6deced7934df86b949af7e` |
| Gaussian blur | 1 px |
| Per-page RGB MAD | `≤ 0.008` |
| Per-page changed-pixel ratio | `≤ 0.040` |
| Changed-channel threshold | `16` |

All 58 pages must be compared. A failure on any page fails the complete run;
mean RGB MAD or mean changed-pixel ratio cannot hide an out-of-tolerance page.
The blank-page/content-occupancy check is additional, not a replacement for
the visual hard gate.

The latest deliverable is acceptable only when all of these are true:

- exactly 58 pages, with every page inside the approved geometry tolerance;
- zero overset stories/table cells, zero missing fonts, zero missing glyphs,
  and zero bad links;
- PDF/X-4 and the required Output Intent/Condition are present in the exported
  PDF;
- all 52/52 source identities and the reference PDF match the approved plan;
- every one of the 58 page-level visual comparisons passes both thresholds;
- no visible body/back-cover whole-page PDF shortcut is present;
- every actually used asset is approved, scope-matched, current, and
  hash-correct, with the three bundle trace files retained;
- the parity JSON reports `accepted=true`.

Writing this workflow or generating an IDML/INDD/PDF does not prove parity.
Only reports from the latest actual InDesign export can satisfy the gate; do
not deliver an artifact while any item above is unknown or failing.

`--idml-mode both` also writes a compact design handoff package beside the
legacy production IDML:

```text
docs/_build/<model>/<region>/<lang>/idml/
  manual.ir.json
  latex_page_plan.json
  production/manual.production.idml
  production/source_trace.json
  production/asset_manifest.csv
  flow/manual.flow.md
  flow/manual.flow.idml
  missing_assets_report.md
  designer_checklist.md
  layout_feedback.md
```

The production `source_trace.json` records `skipped_raw_blocks` from the
production `manual.ir.json` sidecar. Ordinary targets without an approved
reference plan keep this as an observation field. An approved-reference plan
must freeze `idml_contract.max_skipped_raw`; production export fails closed
when the current total exceeds that baseline. `manual_ir_cli.py --strict`
remains the explicit zero-tolerance diagnostic independent of plan activation.
The same strict command also rejects unregistered Manual IR languages at the
top-level target, frozen manifest declaration, or page level. Approved-reference
production applies that language gate automatically before composition;
ordinary/fallback exports preserve their compatibility behavior. Language
aliases are resolved only through `tools/lang_registry.py`, while non-content
page roles `cover` and `toc` are exempt.

Japanese, Korean, and Chinese characters in editable IDML are serialized as
explicit script-aware character runs. Korean Hangul uses the committed
SIL-OFL `NanumGothic` face. Japanese uses the committed static TrueType
`HBManualSansJP-Regular.ttf` (`HB Manual Sans JP (OTF)` in InDesign,
OpenTypeTT) in both IDML and LaTeX. It is the Noto Sans JP Regular outline under
a project-unique family and PostScript identity, so a host-installed
`Noto Sans JP (OTF)` cannot shadow the document font after close/reopen. The
IDML token uses InDesign's normalized `(OTF)` family spelling while the TTF
name table and PostScript identity stay project-unique. The file is
hash-verified and packaged with the document. Chinese
continues through `CJK_FONT_FAMILY_TOKEN` (the renderer token
`idml_font_family_cjk`). Font-family routing intentionally stays outside
`data/layout_params.csv`: changing font delivery is not page geometry and does
not by itself require a reference-layout rebind.
Latin-market editable symbols are governed separately: the U+203B reference
mark is an inline native IDML vector with deterministic story-local object IDs,
so it has no font dependency after an INDD save/reopen cycle. Warranty-year
badges likewise use a native black circle plus an editable white ASCII digit;
do not replace the approved badge with either `❷` / `❸` or bare `2` / `3`.
The native badge renderer positions the localized year unit with a fixed tab
stop and reuses that exact x anchor for the warranty subtitle below it;
font-space advance must not separate `YEARS` from `Standard Warranty` or
`Extended Warranty` horizontally.
`Noto Sans` owns
ordinals and subscript digits; `Noto Sans Symbols` owns the
DC glyph and circled labels 1-20; `Noto Sans Symbols2` owns the filled-circle
fallback. LCD labels 21-27 are normalized to `(21)`-`(27)`, and both final
assembly modes enable native vector structure markers. Every declared
redistributable face is hash-verified from
`docs/templates/word_template/common_assets/fonts/idml_portable/` and copied
beside the IDML under `Document fonts/`; generated packages therefore do not
depend on `Segoe UI Symbol`, `Yu Gothic`, or `Noto Sans KR` on the host.
Line and coarse text-width budgeting is governed by
`tools/idml/line_metrics.py`: the existing per-component narrow-glyph ratios
remain stable, East Asian Width `W`/`F` characters consume one em, combining
marks consume no width, and ambiguous-width characters remain narrow for
cross-host determinism. The estimator does not load local font files and does
not replace native InDesign finalize/parity checks. Heading/suffix-pill sizing
also reserves a full em for wide/fullwidth glyphs while preserving the approved
Latin advances. Single-column contents use native tab leaders; multicolumn
contents retain the reference line geometry. An explicitly empty specification
group omits its heading and marker. Warranty lists retain their source numbering
or nested dash once, using the existing hanging-tab layout.

Japanese native finalization preserves each character's face when rebinding the
portable font, and fails if that requested face is unavailable. The report's
`portable_font_rebinds[].style_counts` exposes the result. Archive frozen inputs
and native reports outside the target build directory before another `idml` or
`check` run: preparation cleans that target. See the
[JP native acceptance ledger](../reviews/bp_jp_r3c_native_validation_2026-09.md)
for an actual twelve-page run and its retained debt.

On the publish queue path (`Workflow_action = Publish`), the worker runs the
idml step with `--idml-mode both` and then packages the export into one
designer delivery zip via `tools/idml/delivery.py`:
`manual_<model>_<region>[_<lang>]_publish_<version>_handoff.zip` containing the
production and flow IDML with every `LinkResourceURI` rewritten to
`file:Links/<name>`, the linked images collected under `Links/`, the flow outputs, the handoff
reports, `source_trace.json` stamped with the queue row's real version, a
fonts manifest, the declared SIL-OFL faces under `Document fonts/`, optional
licensed Gilroy files when `AUTO_MANUAL_LOCAL_GILROY_DIR` is provisioned on the
build machine, and the versioned reference PDF. The zip is
the designer-facing package: its checklist points to the versioned root IDML,
`missing_assets_report.md` reports package-time link portability, and the
separate `source_asset_resolution_report.md` preserves unresolved semantic
source/flow diagnostics without presenting them as broken packaged links. The
zip is staged under `reports/releases/<model>/<region>/<lang>/versions/<version>/`,
uploaded to the knowledge base, and its link is written to the queue row's
`idml_file` field. The bare `.idml` is no longer uploaded: its image links are
absolute build-machine paths that die with the build worktree, so only the
packaged zip is a usable designer deliverable.

The remote Publish workflow reads its XeLaTeX/CJK apt package set from
`.github/texlive-apt-packages.txt` and binds the apt-archive cache key to that
file plus runner OS/architecture. Each run writes cache hit/miss and install
duration to the Actions summary. For cache acceptance without touching
`Document_link`, dispatch `feishu-build-queue.yml` with
`texlive_smoke_only=true`; that path compiles a deterministic smoke PDF,
reports its SHA-256, and skips `process-build-queue` entirely.

For approved reference figures, the package-time link set must include every
referenced file under `_generated/idml_reference_assets/` plus the pairing-panel
PDF, and `missing_assets_report.md` must report zero missing links. For release
acceptance, extract the final ZIP and run `indesign_finalize.py` against its
versioned root IDML. `check_idml`, ZIP integrity, or preflight of an earlier raw
IDML does not prove the delivered `Links/` package.

For queue rows with `Git_ref`, the build worktree is based on the current
`origin/main`; only the active `docs/_review/<model>/<region>` target is
overlaid from the row's review ref. The worker does not replace sibling target
directories. For a versioned Publish, the worker carries the resolved review
commit into the subprocess; the clean gate accepts the target only when its
complete file set and blob hashes match that commit, then writes the composite
provenance into the release manifest. The manifest consumes the tree SHA proof
frozen by that entry gate rather than re-reading the working subtree after the
build has staged target assets. Approved-reference targets do not run the
parameter-sync mutation at all: every print renderer consumes the same
`review-asis` bytes that the contract pins. This prevents both a stale local
`main` branch from silently running an older renderer and fresh Base values
from bypassing review on their way into a release.

The default flow style map lives at
`docs/templates/idml_template/style_mapping/flow_style_map.json` and is copied
to each flow output folder as `flow_style_map.json` so design can map the story
to an InDesign template without changing production styles.

`configs/config.eu.yaml` now represents the live `EU` region-family row as `eu-merged`, routes blank-`Lang` queue rows to the merged EU manual, and keeps `sync.phase2.tables.spec_master` pinned to the live Base view that contains `JE-1000F_EU` rows. `configs/config.eu-en.yaml`, `configs/config.eu-fr.yaml`, and `configs/config.eu-es.yaml` are the explicit English, French, and Spanish single-language EU surfaces when you need one language family at a time.

### Prepared RST inline content in IDML

The prepared-RST adapter slices grid tables by display columns, including wide
CJK characters and partial horizontal borders. Local `replace`/`image`
substitutions expand after cell boundaries are parsed. Table images and inline
icons use portable Markdown image references in the existing string payload;
Manual IR and flow manifests record these asset references. Both IDML writers
resolve them through the shared render context and fail on missing inline
assets instead of printing directive syntax. Native icon geometry is owned by
the renderer; these parser checks do not certify final page composition.

JP IDML uses its manifest-declared Japanese TOC payload with dynamically
collected headings; the TOC is excluded from non-IDML builders. Its
`front_matter_roles: ["cover", "toc"]` declaration controls both the TOC slot
and fallback folios, so the first body page is 01. An explicit renderer page
plan still owns its physical folios. Front-matter metadata alone does not
create a reference-layout sidecar. Final story reflow and TOC page accuracy
must be checked in InDesign screenshots of the identified candidate package.

The six approved JE-1000F/JP illustrations resolve through scoped registry
overrides. Product engravings and logos remain; added manual annotations are
removed. Other targets retain their existing asset resolution. Local approved
files are usable for review while dedicated asset-Base archival remains
pending write permission; local hash checks do not prove online archival.

Under the measured-LaTeX fallback plan a story's spread chain is the anchor
distance to the next matched source. An *unmatched* source between them owns
physical pages of its own and is emitted as its own spread, so charging that
distance to the preceding story threads it through trailing blank linked
frames. Such an unanchored gap now falls back to the height estimate instead;
an explicit assembly contract is unaffected. Warranty and App Setup are also
treated as dedicated sections that never share one linked chain, and a
dedicated section under a fallback plan is never allocated below its own
estimate. `[export-idml] STORY SPANS` reports each story's allocated pages and,
where they differ, the height estimate, so an over- or under-allocated section
is named in the build log instead of only in a native screenshot.

A measured fallback span may also be *longer* than the section the IDML writer
composes, because it measures a different engine: LaTeX spread JE-1000F/JP's
symbols section over four physical pages where the writer fills three, and the
surplus linked frame printed as blank folio 04. The exception the preface
already carried — a physical gap in a fallback plan is not a request to thread
a story through blank frames — now covers every fallback story: the plan may
shorten a chain but never lengthen it past what the story needs, counted as its
height estimate or one frame per authored page break, whichever is larger. An
approved-reference or target-assembly contract stays authoritative in both
directions, since a human mapped it page by page.

Because that cap sizes a fallback chain from the height estimate, the estimate
also counts the frame foot an unbreakable figure leaves. A figure line cannot
break: when a single-column story's figure does not fit the space left in a
frame, InDesign moves it to the next frame and the foot stays empty.
JE-1000F/JP's charging methods estimated 929 pt (two pages) with full-width
figures, but its solar-adapter and car figures each moved on, leaving 186 pt
and 80 pt feet; the section needed about two and a half pages and overset.
Counting those feet allocates three pages. Two-column stories and
approved-reference or target-assembly contracts keep the linear estimate.
Prepared-source integrity: a declared page include that is missing or is not a
file now stops source discovery with the index and source path. Registered
prose macros need complete arguments; unsupported content around recognized
macros increments `skipped_raw` and fails strict Manual IR validation. A valid
macro no longer hides adjacent unsupported copy. Existing language/tag
selection and successful payload formats remain unchanged.

IDML handoff validates the source `manual.ir.json` before copying artifacts or
writing reports. Missing IR is explicitly unavailable; corrupt IR is an error,
not a zero-skipped report. This IDML integrity path remains on its existing v1
producer and does not by itself consume the new whole-document v2 flow or
certify native JP layout. See the
[shared-source plan](../dev/latex_indesign_same_source_plan.md) for remaining consumer and parser boundaries.
