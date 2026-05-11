# MyST Markdown And Feishu Cloud Doc Publish Plan

Updated: 2026-05-11

## 1. Purpose

This plan defines the architecture for adding a MyST Markdown publish lane next
to the existing Word / PDF publish lane, then importing that Markdown into
Feishu cloud documents through `lark-cli`.

The goal is to support three related outcomes:

- publish-stage generation of MyST-compatible Markdown for each target manual
- Read the Docs hosting of electronic manual editions
- batch migration of existing Markdown manuals into a MyST-hosted manual library,
  so they can be progressively converted into the structured template/data model

This is an architecture and implementation plan. It does not replace the current
Word / PDF release flow.

## 2. Current Baseline

The current manual pipeline is centered on the runtime manual bundle:

1. `build.py` resolves config, model, region, language, data snapshot, and review
   source.
2. The manual bundle is materialized under `docs/_build/<model>/<region>/.../rst/`.
3. Word export consumes the same bundle through the Word bundle HTML path.
4. Publish builds review-sourced Word and PDF artifacts, then writes release
   traceability through `release-manifest`.
5. The Feishu `Document_link` queue uploads the primary release artifact:
   Draft rows use DOCX, Publish rows use PDF.

The MyST lane should reuse this bundle boundary. It should not introduce a
second page assembly system and should not make model-specific config files just
because a different output format is requested.

## 3. Target Architecture

### 3.1 Output lanes

The build system should treat Markdown as a first-class output format:

- `html`: reading preview / hosted HTML output
- `word`: review and handoff DOCX output
- `pdf`: publish release output
- `md`: MyST-compatible Markdown output

`md` should be a sibling of `word`, not a replacement for `rst`.

The generated Markdown path should stay target-scoped:

```text
docs/_build/<model>/<region>/<lang>/md/<manual>.md
```

For merged-language targets that do not include `<lang>` in the output path,
the existing target output rules should continue to apply.

### 3.2 Conversion source

The Markdown exporter should reuse the Word bundle HTML path:

```text
manual bundle -> Word bundle HTML -> Pandoc -> MyST-compatible Markdown
```

This keeps Word and Markdown aligned with the same assembled manual content,
review overlays, generated pages, image paths, and target metadata.

Pandoc writer selection should be:

1. prefer native `myst` when the installed Pandoc supports it
2. otherwise use MyST-compatible CommonMark with pipe tables
3. only fall back to generic Markdown when neither preferred writer exists

The fallback must be documented as "MyST-compatible Markdown", not full native
MyST feature parity.

### 3.3 Publish flow

Publish should include Markdown generation after PDF generation:

```text
check -> diff-report -> word -> pdf -> md -> release-manifest
```

Release traceability should record the Markdown artifact alongside Word and PDF:

- local path
- exists flag
- SHA-256
- release/version location when queue-driven publish stages artifacts

The primary `Document link` contract should not change:

- Draft writes the DOCX link
- Publish writes the PDF link
- Markdown is supplementary and feeds Read the Docs / Feishu cloud docs

### 3.4 Feishu cloud document import

When the `Document_link` table exposes the `飞书云文档` field, queue processing
should import the generated Markdown as a Feishu cloud document after the primary
artifact upload succeeds.

The CLI command shape is:

```bash
lark-cli drive +import \
  --as <user|bot> \
  --file ./path/to/manual.md \
  --name <manual-name-without-extension> \
  --type docx
```

The importer should parse the returned payload for a cloud document URL and write
that URL back to `飞书云文档`.

Failure semantics:

- If the field does not exist, skip cloud-doc import.
- If the field exists but Markdown was not generated, fail the queue row.
- If import fails after the primary artifact was uploaded, mark the row failed
  while preserving the latest primary artifact link in writeback.
- On success, append `cloud_doc=ok` to `构建结果`.

This makes missing cloud docs visible instead of silently reporting a successful
publish with an empty `飞书云文档` field.

## 4. Read The Docs Hosting Model

Read the Docs should become the stable electronic-manual host. The hosting model
has two lanes that converge over time.

### 4.1 Generated manual lane

For structured manuals, the RTD build should generate Markdown from the same
target bundle used by publish:

```text
RTD build job -> build.py md -> generated MyST source tree -> Sphinx/MyST HTML
```

The initial hosted target can stay narrow, such as the default US English runtime
manual, while the source tree and navigation model should allow more model /
region / language targets later.

The RTD source should be assembled as a Sphinx + MyST project, with generated
manual entries included in a normal toctree. This keeps RTD independent from
Feishu and keeps Feishu import as a delivery integration, not the canonical web
host.

### 4.2 Existing Markdown manual lane

Existing Markdown manuals should be migrated into a committed MyST source area
before they are fully structured:

```text
existing Markdown manuals -> batch normalizer -> MyST source tree -> RTD
```

The first migration pass should be conservative:

- preserve the original chapter order and wording
- normalize heading levels only where required for valid MyST navigation
- copy or rewrite image paths so assets render on RTD
- add stable slugs and index pages
- keep provenance metadata so each migrated page can be traced back to its source

This creates a complete electronic manual library quickly, while allowing each
manual to be converted into reusable templates and structured data over time.

### 4.3 Progressive structural conversion

After a legacy Markdown manual is hosted, convert it chapter by chapter:

1. identify stable reusable sections
2. move reusable prose into `docs/templates/`
3. move specs, symbols, product attributes, and repeated tables into `data/phase2`
4. replace the hosted legacy page with generated MyST from the structured manual
5. keep old URLs redirected or represented by stable index entries where possible

The hosted electronic edition becomes the continuity layer during this migration.

## 5. Implementation Phases

### Phase 1: Build and publish Markdown

- Add or confirm `build.py md` and `--formats md`.
- Add Markdown artifact planning next to Word and PDF output planning.
- Export Markdown through the Word bundle HTML path.
- Include `md` in `all` output formats.
- Include `md` in publish before `release-manifest`.
- Add Markdown artifact data to release manifests.
- Add focused unit tests for writer selection, command routing, output path
  resolution, publish order, and release manifest metadata.

Exit criteria:

- `python3 build.py md --config config.us.yaml --model JE-1000F --region US`
  writes a target-scoped Markdown file.
- `python3 build.py publish --config config.ja.yaml --model JE-1000F --region JP`
  produces Word, PDF, Markdown, and release manifest metadata.

### Phase 2: Queue import to Feishu cloud docs

- Add `飞书云文档` as an optional queue writeback field.
- Generate Markdown for Draft and Publish queue builds.
- Import Markdown through `lark-cli drive +import --type docx`.
- Write the returned cloud document URL to `飞书云文档`.
- Preserve the existing `Document link` semantics.
- Add queue tests for field-present, field-absent, success, and failure cases.

Exit criteria:

- A Draft queue row writes DOCX to `Document link` and cloud doc URL to
  `飞书云文档`.
- A Publish queue row writes PDF to `Document link` and cloud doc URL to
  `飞书云文档`.
- Cloud-doc import failure is visible in `构建结果` and does not erase the latest
  primary artifact link.

### Phase 3: Read the Docs MyST site

- Add a MyST-capable RTD source layout.
- Add `myst-parser` to Python documentation dependencies.
- Add an RTD build step that generates or assembles the MyST manual tree before
  Sphinx builds HTML.
- Keep the existing RTD baseline stable while the MyST tree is introduced.
- Add a smoke build for the default hosted target.

Exit criteria:

- RTD can build the default generated manual from MyST Markdown.
- The site navigation can include generated manuals and migrated Markdown manuals.

### Phase 4: Batch migration of existing Markdown manuals

- Add a batch conversion tool for existing Markdown manuals.
- Normalize each manual into the MyST source tree with copied assets and stable
  navigation.
- Emit a migration report listing source file, output file, copied assets, and
  any unresolved links.
- Do not force structural data extraction during the first migration pass.

Exit criteria:

- Existing Markdown manuals can be hosted as electronic manuals on RTD.
- Each migrated manual has a clear path for later conversion into templates and
  structured data.

## 6. Validation Matrix

Required validation for implementation work:

```bash
python3 -m unittest
python3 build.py check --config config.us.yaml --model JE-1000F --region US
python3 build.py md --config config.us.yaml --model JE-1000F --region US
python3 build.py publish --config config.ja.yaml --model JE-1000F --region JP
```

Queue validation should cover one Draft row and one Publish row with the
`飞书云文档` field present.

RTD validation should include a local Sphinx build of the MyST source tree before
changing the hosted RTD configuration.

## 7. Non-Goals

- Do not replace RST as the internal generated bundle format in this phase.
- Do not replace Word or PDF release artifacts.
- Do not make `飞书云文档` the primary release link.
- Do not require every historical Markdown manual to be fully structured before
  it can be hosted.
- Do not create one config per model or per output format.

## 8. Open Follow-Up Decisions

These decisions should be made when Phase 3 begins:

- whether the MyST RTD source tree lives under `docs/myst/` or another dedicated
  documentation root
- whether generated publish Markdown should be hosted as one page per manual or
  split into one page per chapter
- how many model / region / language targets should appear in the first public
  RTD navigation
- whether legacy Markdown migration should preserve original file names or use
  normalized slugs immediately

The Phase 1 and Phase 2 work does not depend on these decisions.
