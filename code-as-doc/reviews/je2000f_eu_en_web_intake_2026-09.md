# JE-2000F EU/en Web intake and implementation record

Date: 2026-09-08

Implementation baseline: `d1b12bf8686941b5e79d9b507d7cc991da3427b9`

Target: `JE-2000F / EU / en` (`HTE154`, Jackery Explorer 2000)

Status: implementation complete and ready for engineering review. Repository,
target-build, semantic-IR, asset-provenance, image-reference, strict-Sphinx, and
localhost desktop-browser checks pass. The operator approved all eleven
corrective full-frame crops at 12x. Mobile layout remains a publication-stage
real-browser check rather than evidence of formal publication.

## Authority and source inventory

| Source | Role | Revision / hash |
| --- | --- | --- |
| Current published PDF, DingTalk node `20eMKjyp81Rg14l4FebQL1ZwWxAZB1Gv` | Visible content and artwork authority | `Jackery Explorer 2000 User Manual (JE-2000F) EUUK V2.0-2026-08-04.pdf`; SHA-256 `6b4af85236ccfee0f4d24ad55ee8b24684d023982b5da216023d4f716f183f3d` |
| `origin/review/JE-2000F-EU` | Existing built-document source for the complete reviewed body | commit `6333df933820c5ed9058d7ad6e4140517e9111de` |
| Target-scoped phase2 snapshot | Reproducible Git build input, frozen from the existing data lane and audited against the two sources above | `manual_sources/JE-2000F/EU/en/2.0/phase2/` |

The review branch is 543 commits behind and 3 commits ahead of the implementation
baseline. It contains the complete generated English page set but still renders
`6000 cycles to 70%+ capacity` and a `10 A max.` bypass output. The current
published PDF visibly states `4000 cycles to 70%+ capacity` and
`220 V-240 V ~ 50 Hz, 2200 W max.`; the published PDF wins those conflicts.

A read-only bare-model query of the published-manual catalog on 2026-09-08
returned current US and JP rows but no EU row. That observation is not treated
as proof that the EU source does not exist. The verified Git read path for this
engineering target is the review branch and commit above; no replacement source
row or duplicate phase2 source was created.

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
| LCD | LCD component | complete screen map from PDF page 9 plus corrected numbered rows; the mode section keeps its device-only crop beside the semantic CSS/HTML table and never uses a rasterized table |
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
3. Kept the original 14 deterministic exports and added a corrective recipe for
   11 operator-approved, 12x full-frame crops. These retain the complete grey
   frame and image-owned text boxes while exact-bound duplicate live copy is
   consumed. The LCD mode panel is deliberately excluded from this rule.
4. Added a reusable EU regulatory page with target substitutions instead of a
   per-model config or page fork.
5. Froze the audited phase2 input and source manifest under
   `manual_sources/JE-2000F/EU/en/2.0/` so the Git branch builds without a live
   Bitable dependency. The manifest locks the PDF revision/name/hash, review
   branch commit, original recipe, corrective recipe, and final illustration
   manifest.

## Acceptance results

| Gate | Result |
| --- | --- |
| Approved-state asset recipe replay | Pass: the original 14 exports and corrective 11 full-frame exports reproduce from the 102-page source; every locked output hash matched |
| Source-manifest external locks | Pass: the original recipe, corrective recipe, and final illustration manifest hashes are verified by the target test |
| Real `build.py md` Web build | Pass: 17 public-IR pages, 14 finished illustrations, 12/12 governed figure slots (`11` finished-panel, `1` editable-fallback LCD), and no unresolved placeholder token |
| Content assertions | Pass: 4000-cycle life, 2200 W bypass, AC/DC Output Resume, 10 ms UPS, DC8020, 16 V-60 V, `F0`-`FE`, and the EU declaration are present; `Jackery Explorer 2000` is retained and `2000 Plus` / `AC1/2` are absent |
| Strict Sphinx | Pass: `python -m sphinx -W --keep-going -b html` |
| Generated-site references | Pass: 54 image references, zero missing files, 14 finished panels, and responsive-media CSS present |
| Target check | Pass: `python build.py check --config configs/config.eu-en.yaml --model JE-2000F --region EU --lang en --data-root manual_sources/JE-2000F/EU/en/2.0/phase2` |
| CI shared-fixture target check | Pass after adding the target's specification, note, footnote, and symbol rows to `tests/fixtures/phase2`; the all-target lane no longer classifies JE-2000F EU/en as a new skip |
| Existing-target regression | Pass with `tests/fixtures/phase2`: JE-1000F EU/en check; the repository's default `data/phase2` snapshot does not contain `Spec_Master.csv` |
| Python lint | Pass: `python -m ruff check build.py integrations tools tests scripts` |
| Unit tests | Pass: 3,868 tests, 22 skipped after the full-frame correction |
| Maintainability guardrails | Pass: zero new violations |
| Documentation links | Pass: 169 documents, 1,745 links, zero broken |

The local Web artifact is structurally reviewable and has no broken media. It
was served over localhost and inspected in the in-app browser. The operator
confirmed all eleven corrective crops; the Operations, LCD, App control-panel,
and charging sections were re-opened after the final build. This local review is
engineering evidence only. A real public route and publication-stage mobile
check still require the centralized Hello-Docs publication flow.

## Closeout checklist

- [x] Verified `origin/review/JE-2000F-EU` and pinned commit `6333df933820c5ed9058d7ad6e4140517e9111de`.
- [x] Re-read the formal PDF and pinned revision, filename, 102-page count, and SHA-256.
- [x] Locked the original and corrective recipes plus the final illustration manifest in `source_manifest.json`.
- [x] Reproduced and hash-checked all 11 corrective 12x outputs.
- [x] Recorded operator approval for all 11 full-frame crops.
- [x] Kept LCD as device art plus semantic CSS/HTML table; no full-frame LCD table image is bound.
- [x] Consumed only exact-bound duplicate live copy covered by finished images.
- [x] Confirmed `Jackery Explorer 2000`; rejected `2000 Plus` and `AC1/2` for this target.
- [x] Ran target build/tests, public-IR cold replay, asset-tamper rejection, strict Sphinx, image-reference, lint, maintainability, documentation-link, and full-unit checks.
- [x] Confirmed the branch is based on current `origin/main` at `d1b12bf8686941b5e79d9b507d7cc991da3427b9`.
- [ ] Live asset/source registry write-back: deliberately not performed; requires separate operator authorization and exact read-back.
- [ ] Merge and formal Web publication: outside this task; PR review/CI and centralized Hello-Docs publication remain separate gates.

## Non-goals

- No live Bitable write, queue-row mutation, review reseed, OSS upload, or
  archive-credential use.
- No JP changes, IDML pagination work, public URL claim, Hello-Docs code edit,
  publish-branch mutation, or PR merge.
- No whole-page screenshot rendering. Source panels remain illustrations inside
  shared semantic sections and components.
