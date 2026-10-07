# JA-AD600A / EU / en Web acceptance

## 2026-10-07 source correction

The operator supplied `HTO814-EU-9国语言-0924 (1).ai` as the current authority.
SHA-256: `65297e68dbd6c811c5a34bb38a589ef8939b3a9eed6113ef305b60125cffb348`.
English physical pages 3–16 correspond to printed 01–14. The source manifest
retains the previous PDF authority separately.

- Nine IR pages produce the source's eight chapters; Dimensions remains in chapter 2.
- Chapter numbers 1–8, installation subsections 7.1–7.9 and FAQ Q1–Q8 are native text.
- Ten numbered installation steps pair full instructions with complete individual source frames. Wiring retains hand tightening, terminals ①/② and the electric screwdriver setting of 4 N·m.
- Three wiring precautions, source polarity emphasis, gray introductory/drilling notes, and the original connection instructions are retained.
- Inbox A–I and Anderson / OT / DC8020 connector labels are native text. Primary item A occupies its own row; subsequent objects retain source order.
- The lit-status device and four native green/red/blinking/off lamp states are present. Blinking uses a static halo.
- Three source warning triangles are visible. Only the two source installation strips carry the authored Warning label. The shared neutral-gray warning symbol is reused unchanged.
- The waterproof warning is between pre-installation checks 5 and 6; numbering continues through 9.
- The installation note already embedded in the diagram appears once. No added Vehicle installation overview heading remains.
- Warranty uses source prose and a 25/75 desktop period table, stacking at full width on mobile. The protected lead notice explicitly declares `hb-source-warranty-note`, preserving six title-case headings without decorative dots, compact paragraph spacing, and a white 2 inside a dark circular badge on white. No invented warranty section cards remain.
- Thirteen specification values and six compatible power-station rows remain unchanged.
- FAQ Q4's incomplete subject and the repeated Interpretation Rights paragraph remain documented source errata.

## Asset and coverage evidence

The original 16-export recipe and image bytes remain unchanged. Three aggregate
operation exports and the original English-labeled connection panel are
retained in `superseded_illustrations`; they no longer
bind into the page. Eleven new complete-frame exports use a separate current-AI
recipe. One shared warning SVG is hash-pinned and explicitly reusable.

The illustration manifest has 25 active unique assets and four retained
superseded assets. The page contains 27 image occurrences. Figure coverage
reports 14 installation occurrences: 13 `finished-panel` and one governed
`base-art-live-copy`, with zero editable fallback and zero missing slots. All 12 installation diagram/step slots remain
required. The two additional occurrences are reused warning icons.

## Reproduction commands

```bash
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off python3 build.py check \
  --config configs/config.charger-eu-en.yaml \
  --model JA-AD600A --region EU --lang en \
  --data-root data/manual_sources/ja_ad600a_eu_en

AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off \
AUTO_MANUAL_PRESENTATION_PROFILE=web \
python3 build.py md \
  --config configs/config.charger-eu-en.yaml \
  --model JA-AD600A --region EU --lang en \
  --data-root data/manual_sources/ja_ad600a_eu_en \
  --staging-root /tmp/ja-ad600a-web

sphinx-build -W -b html \
  /tmp/ja-ad600a-web/docs/_build/JA-AD600A/EU/en/md \
  /tmp/ja-ad600a-web/docs/_build/JA-AD600A/EU/en/html

python3 -m unittest \
  tests.test_ja_ad600a_eu_en_target \
  tests.test_ja_ad01a_eu_en_target
```

## Recorded local evidence

- Offline target quality check: passed.
- Real Pandoc Web build: passed.
- Sphinx 8.2.3 `-W`: passed with zero warnings.
- Target and sibling regressions: 16 tests passed, including source hashes, step ordering, warning position, native IR cold replay and packaged-asset tamper rejection.
- Repository unit suite: all 474 discovered test modules ran exactly once in four independent processes; 5,211 tests completed, 35 skipped, no failures or errors. A canonical `TMPDIR` avoids the existing macOS `/var` versus `/private/var` path discrepancy.
- Repository Ruff baseline, maintainability guardrails and documentation links: passed without raising limits.
- Browser QA at desktop 1280 × 900 and mobile 390 × 900: all 27 image occurrences decoded; no page errors or body overflow; all ten steps pair text/art side by side on desktop and stack within the same step on mobile.
- The status table has its own working horizontal scroll on mobile. Warranty badge and prose both occupy full width on mobile.
- Follow-up after the operator screenshot: the Warning rubric is excluded from paragraph grid rules. All three warning panels were checked for pairwise image/label/body overlap at 390, 640, 641, 800, 1280 and 1460 CSS pixels; all pass. The original desktop/mobile checks had missed the two rubric-bearing panels.
- A standalone delivery copy embeds the generated page's CSS, JavaScript and images. Its article text is identical to Sphinx output; it passes the same desktop/mobile assertions.

## Evidence boundary

This acceptance proves local source, build, IR replay, hashes and responsive
rendering. It does not prove merge, formal publication, a live page update,
or Base/queue writes. The online manual remains unchanged by this repair.

## Warranty screenshot follow-up

The operator's source screenshot requires a dark circular 2 with white text,
white period background, bold Standard Warranty, six title-case H2s without
decorative dots, and compact section/paragraph spacing. These are now driven
by the explicit protected source marker and shared CSS. Source warranty text
was compared in full with the previous generated chapter and is unchanged.
Actual Pandoc and strict Sphinx builds pass. Browser checks at 390, 640, 641,
800, 1280 and 1460 CSS pixels verify the circle geometry, colors, all six
headings, compact section margins and responsive period composition. Entire
desktop/mobile chapter screenshots were inspected. The installation-pair and
three-warning overlap checks continue to pass. Target/sibling regressions
remain 16/16; maintainability guardrails and documentation links pass.

## Connection artwork reuse decision

| Candidates | Identity/content review | Decision and reason | Source/background |
| --- | --- | --- | --- |
| Existing JA-AD600A English connection_diagram.png | Exact product, ACC/output/input connectors and complete cables; embeds three English cable labels | Preserve bytes for provenance; cannot supply a language-neutral base | Previous immutable AI recipe, hash1e32d063...0340; white complete panel |
| Same-model locale assets and shared/template candidates | No matching textless charger/cable composition exists in this checkout; other charger models have different connectors/hosts | Extract only the three source label regions from current authority | Current AI SHA25665297e68...b348, physical15; preserve original crop45,10,345,190 and white panel |

At12x, every pixel outside the three source label rectangles is unchanged.
No caption frame exists to remove. Fixed product/connector inscriptions remain.
The correction uses the existing ReferenceFigure component and a shared asset
path; no new renderer, registry write or live Base/queue action is required.

## Editable connection labels acceptance

English now consumes the shared connection_base.png and source-native labels
ACC Cable, Output Cable and Input Cable with Fuse through the existing
ReferenceFigure ComponentSpec. The artwork asset locale policy is `shared`;
localized labels stay in the source RST line block. The PNG SHA256 is
8fb3b2ca8692360087ac958ebbce9e766c34af3e49183107a8fbae3008f3e427.
The extraction recipe additionally delivers a vector PDF with no text spans.
The original recipe, registry row and labeled image remain unchanged.

The illustration replacement declares `consume_before_presentation`: its
frozen art attributes must be bound before the ComponentSpec source hash is
computed. The source basename differs from the replacement basename to avoid
reapplying the same binding. This reuses the existing pipeline behavior.

Real Pandoc and Sphinx `-W` pass. Forty-four target/sibling, ReferenceFigure,
ComponentSpec and presentation-contract tests pass, including cold IR replay.
At390,640,641,800,1280 and1460 CSS pixels, all three source labels are native
text, readable in their assigned rectangles, do not overlap, and stay inside
the complete art. The same base hash is used at every width. Desktop/mobile
images were visually reviewed; existing installation, warning and warranty
checks continue to pass. This is local English integration and a reusable
base, not evidence of eight other language pages or online publication.

## Number and prose alignment follow-up

The operator screenshot requires prose immediately to the right of its round
step number. The existing `hb-step-copy` source boundary now uses a fixed
number column and a flexible prose column; continuation paragraphs stay
indented, and each desktop text/art pair aligns at the top. Narrow layouts
retain the inline number/text lockup above the complete illustration.

All ten steps were checked at390,640,641,800,1280 and1460 CSS pixels for
first-line/number alignment, continuation-paragraph indentation, top alignment
or mobile stacking, and no whole-page overflow. Desktop/mobile modification
panel screenshots were visually compared with the operator source screenshot.
All step copy remains unchanged. Real Pandoc and strict Sphinx pass, and94
presentation/contract/target/sibling tests pass. Existing editable connection
labels, warranty, three warnings and complete-asset checks continue to pass.
