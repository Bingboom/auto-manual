# JHP-3600C / US / en Git-only Web intake

Status: active

Local English candidate implemented and verified; operator visual confirmation is pending.

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

The [frozen manifest](../../data/manual_sources/JHP-3600C/US/en/git-20261005-31fd0692/source_manifest.json) binds the unchanged original PDF, complete positioned extraction, 399 selected/recovered fields, semantic chapter data, 83 asset decisions, shared IR, MyST and scaffold. It also pins 169 repository renderer/component/style inputs. `rebuild.py` verifies both inventories before compiling through the shared APIs. No new family config, phase2 enrollment, parallel renderer or public CLI is added.

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
