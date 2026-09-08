# JE-2000F EU/en Web intake and implementation record

Date: 2026-09-08

Implementation baseline: `d1b12bf8686941b5e79d9b507d7cc991da3427b9`

Target: `JE-2000F / EU / en` (`HTE154`, Jackery Explorer 2000)

Status: implementation complete and ready for engineering review. Repository,
target-build, semantic-IR, asset-provenance, image-reference, and strict-Sphinx
checks pass. A human desktop/mobile viewport review remains required because the
Codex browser security policy blocked local `file://` navigation.

## Authority and source inventory

| Source | Role | Revision / hash |
| --- | --- | --- |
| Current published PDF, DingTalk node `20eMKjyp81Rg14l4FebQL1ZwWxAZB1Gv` | Visible content and artwork authority | `V2.0-2026-08-04`; SHA-256 `6b4af85236ccfee0f4d24ad55ee8b24684d023982b5da216023d4f716f183f3d` |
| `origin/review/JE-2000F-EU` | Existing built-document source for the complete reviewed body | commit `6333df933820c5ed9058d7ad6e4140517e9111de` |
| Target-scoped phase2 snapshot | Reproducible Git build input, frozen from the existing data lane and audited against the two sources above | `manual_sources/JE-2000F/EU/en/2.0/phase2/` |

The review branch is 543 commits behind and 3 commits ahead of the implementation
baseline. It contains the complete generated English page set but still renders
`6000 cycles to 70%+ capacity` and a `10 A max.` bypass output. The current
published PDF visibly states `4000 cycles to 70%+ capacity` and
`220 V-240 V ~ 50 Hz, 2200 W max.`; the published PDF wins those conflicts.

The PDF text layer is used only to locate content. The English body is physical
PDF pages 6-21 (printed pages 01-16), and physical page 102 carries the English
EU declaration/manufacturer tail. Those pages are rendered for visual checks.

## Confirmed pre-edit findings

- `JE-2000F_EU` supports the AC/DC Output Resume Function. The published
  operations page says that it is disabled by default and can be enabled in the
  App. `data/model_capabilities.csv` currently marks the capability `FALSE`, so
  the shared marked section is wrongly removed.
- The published LCD uses numbers 1-25. Number 22 spans separate high- and
  low-temperature rows, so the table has 26 descriptive rows. The frozen data
  has the correct descriptions but the tail is misnumbered and misordered:
  Battery Power Indicator must be 17, Low Battery Indicator 18, Remaining
  Battery Percentage 19, Discharge Timer 20, Energy Saving Mode 21, both
  temperature rows 22, Fault code 23, Output Power 24, and Remaining Discharge
  Time 25.
- The frozen troubleshooting data already contains the full published set:
  `F0 F1 F2 F3 F4 F5 F6 F7 F8 F9 FE`. No new live row is required.
- The current Web baseline builds through `build.py md` and emits 16 public-IR
  pages, but all 12 governed Overview, Operation, and Charging figure slots are
  reported `missing`. It is not an acceptable Web preview.
- The single-language EU family config has no target-aware Web illustration
  selector. The current scalar `paths.web_illustration_manifest` cannot safely
  serve several models from one shared family config.

## Source-to-structure mapping

| Published content | Shared carrier / component | Target evidence to bind |
| --- | --- | --- |
| safety and symbols | existing EU/en safety and Symbols component | reviewed copy plus frozen Symbols rows |
| three package items | shared Inbox component | product, AC cable, and manual figures from PDF page 7 |
| front and right-side overview | generated Overview component | complete source panels from PDF page 8 |
| LCD | LCD component | complete screen map from PDF page 9 plus corrected numbered rows |
| operations | shared generated Operations carrier | source panels from PDF pages 11-13; AC/DC resume section enabled by capability |
| UPS | shared UPS carrier | complete bypass diagram from PDF page 14 |
| charging | shared charging carriers | AC, direct solar, four-panel solar, and car diagrams from PDF pages 15-16 |
| troubleshooting | Troubleshooting component | frozen `F0`-`FE` rows matching PDF page 17 |
| specifications | Spec component | frozen V2.0 values matching PDF page 18 |
| warranty | shared Warranty component | published 3-year standard plus 2-year extension |
| App setup | shared App component | download, add-device/button, and result panels from PDF pages 20-21 |
| EU declaration and manufacturer | reusable EU regulatory carrier | product/model substitutions and published page-102 wording |

Finished source panels replace the target's placeholder files through the
public semantic IR. Text that remains owned by shared components is not repeated
below a full-panel image; any consumed annotation must use an exact selector and
exact normalized text binding.

## Implemented changes

1. Corrected the target capability and LCD numbering/order while retaining the
   complete troubleshooting set and V2.0 specification values.
2. Added a target-aware Web illustration-manifest resolver to the shared family
   config contract. The existing scalar form remains supported; the plural form
   resolves case-insensitive document keys and rejects ambiguous duplicates.
3. Extracted 14 deterministic source panels, locked their source page, bounding
   box, and SHA-256 provenance, and bound all 12 governed figure slots.
4. Added a reusable EU regulatory page with target substitutions instead of a
   per-model config or page fork.
5. Froze the audited phase2 input and source manifest under
   `manual_sources/JE-2000F/EU/en/2.0/` so the Git branch builds without a live
   Bitable dependency.

## Acceptance results

| Gate | Result |
| --- | --- |
| Approved-state asset recipe replay | Pass: 102 archive pages, 102 previews, and 14 target exports; every locked output hash matched |
| Real `build.py md` Web build | Pass: 17 public-IR pages, 14 finished illustrations, 12/12 governed figure slots, and no unresolved placeholder token |
| Content assertions | Pass: 4000-cycle life, 2200 W bypass, AC/DC Output Resume, 10 ms UPS, DC8020, 16 V-60 V, `F0`-`FE`, and the EU declaration are present |
| Strict Sphinx | Pass: `python -m sphinx -W --keep-going -b html` |
| Generated-site references | Pass: 54 image references, zero missing files, 14 finished panels, and responsive-media CSS present |
| Target check | Pass: `python build.py check --config configs/config.eu-en.yaml --model JE-2000F --region EU --lang en --data-root manual_sources/JE-2000F/EU/en/2.0/phase2` |
| CI shared-fixture target check | Pass after adding the target's specification, note, footnote, and symbol rows to `tests/fixtures/phase2`; the all-target lane no longer classifies JE-2000F EU/en as a new skip |
| Existing-target regression | Pass with `tests/fixtures/phase2`: JE-1000F EU/en check; the repository's default `data/phase2` snapshot does not contain `Spec_Master.csv` |
| Python lint | Pass: `python -m ruff check build.py integrations tools tests scripts` |
| Unit tests | Pass: 3,865 tests, 22 skipped |
| Maintainability guardrails | Pass: zero new violations |
| Documentation links | Pass: 169 documents, 1,745 links, zero broken |

The local Web artifact is structurally reviewable and has no broken media. The
attempted automated desktop/mobile viewport review could not open the generated
`file://` URL because of the Codex browser's local-file security policy. This is
an environment limitation, not a passing browser-acceptance result; reviewers
must still open the generated HTML in a normal browser at desktop width and at
375 px before merge or publication.

## Non-goals

- No live Bitable write, queue-row mutation, review reseed, OSS upload, or
  archive-credential use.
- No JP changes, IDML pagination work, public URL claim, Hello-Docs code edit,
  publish-branch mutation, or PR merge.
- No whole-page screenshot rendering. Source panels remain illustrations inside
  shared semantic sections and components.
