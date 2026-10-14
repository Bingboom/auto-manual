# JA-TS02A / US / English — Git-only PDF intake

This package freezes the supplied Jackery Smart Transfer Switch PDF (model JA-TS02A, printed version JAK-UM-V1.0) and converts only printed English pages 01–22, physical PDF pages 3–24. The printed cover, global contents, non-English bodies and back cover stay in the archived PDF and are not repeated in the Web body.

**Status: Git-only source candidate.** There is no `source/approval.json`. The replayed IR is `publication_eligible: false` and carries a pending source review. Publication needs the operator's acceptance of these exact inputs and a separate merge/release authorization.

## Layout review fixes

The operator asked for a layout review of this draft against the print (「上线发布。 你继续审核。 PR 1523。 版面」, 2026-10-13). The review found nine classes of defect, R1–R9, almost all from generic rules in the former `build_web.py`. On 2026-10-14 the operator chose to have them fixed on this branch. Standing instructions: 「全部修，一次做完」, 「封面和目录 不用体现在web版面上」 and reuse of the existing shared components (「线上有很多现成的」「不需要你重新另写」).

| Finding | Resolution |
| --- | --- |
| R1 print line breaks lost | A line the print ends while the next word would still have fitted is a print break; every other line end is a wrap. The 37 breaks are logged in `source/en/coverage.json`. |
| R2 print bold lost, table first columns bold | Bold and semibold print runs are `strong`; table first columns are plain cells. |
| R3 heading levels and case | Levels follow the print sizes; the four Working Modes entries sit one level lower. RECOMMENDED BREAKERS is a chapter. IC RF Statement, the p12 Warning line and Circuit priorities are body text; the p11 and p15 Warning words are callout labels. Headings keep print case. |
| R4 invented captions, "Figure labels" boxes | No visible captions or label boxes. The caption is the alt text; words printed in the art stay in the art. |
| R5 figure before its steps | Steps and their figure form one reading unit, text first: side by side on desktop, stacked on phones. |
| R6 table structure | Native row and column spans. The specification table has no header row; cable rows carry wire-colour swatches; the torque table is centred and its values do not wrap. |
| R7 callouts and warning glyphs | The p10 CAUTION boxes use the shared callout strip. The p11 and p15 warnings use the shared warning lockup with the print's yellow triangle. The p5 ingestion-hazard glyph is restored. The p12/p13 grey warning strips stay in their complete panels, as the artwork contract requires; their sentences are in the alt text. |
| R8 phone tables scroll | Two- and three-column tables fit the phone; only the six-column torque table scrolls at 390 px. |
| R9 bespoke styles | Removed: `build_web.py`, `source/web_presentation.css`, `source/native-pages.json`. The page replays through the shared Manual IR and components. `source/presentation.css` holds only this source's geometry. |

Component inventory: HB-CALLOUT-STRIP 5, HB-SPECIAL-APP 1, HB-SPECIAL-REFERENCE-FIGURE 30, HB-WARRANTY-LEAD 1, HB-WARRANTY-SECTION 6. The three grey-tile symbol PNGs are replaced by the shared native-v1 SVGs, which match the print's outline drawings. The yellow warning triangle and ingestion-hazard glyph are native vectors from the PDF; the shared libraries hold no yellow-filled variant. Decisions are recorded in `source/figures.json` and `audit/asset-decisions.json`.

Print-source issues are kept as printed (for example "home districution panel", "Connect the the", "Square D-HOM , Eaton-BR"); they are listed for the source owner in the review, not corrected here. The p22 priority list ("2.Nice to have") renders as a numbered list, so its missing space after the number does not show.

## Reconstruction

- `source/native.py` reads the archived PDF (word geometry, font weight, line junctions).
- `source/intake.py` maps each page region to shared flow nodes and components. It writes `source/en/content.json` and `source/en/coverage.json`.
- The coverage gate refuses any unclassified English body word, duplicate live copy, or unused text recovery or split word.
- Five visible lines absent from the PDF text layer are restored from `source/text-recovery.json`, with source coordinates.
- Seven App inline controls are the exact source faces (`source/inline-controls.json`).
- `rebuild.py` verifies the reassembled PDF, every inventoried input and the pinned shared repository inputs. It then replays through the shared Manual IR APIs. `assets/` in the output holds only the files that `content.json` and the source stylesheet reference.

Run from the repository root (PyMuPDF 1.28.0 / MuPDF 1.29.0, `requirements.lock`):

```sh
PKG=data/manual_sources/JA-TS02A/US/en/git-20261013-11ce66b1
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output tmp/ja-ts02a/en
python3 -m sphinx -n -W --keep-going -b html tmp/ja-ts02a/en tmp/ja-ts02a-site/en
```

To re-freeze: remove `web/en`, run `source/refresh_manifest.py`, rebuild into `web/en`, and run `source/refresh_manifest.py` again.

## Boundaries and source archive

Git-only boundary: no Feishu/Base/source table, queue, online asset, build/link or HTML_link writes. The package does not register a phase2 or print-build target. The build.py JE-1000F/US check is a repository regression gate only; it does not validate this manual's body.

The unchanged 94,486,777-byte original PDF is archived losslessly as three ordered binary parts (each ≤32 MiB), within the frozen-source per-file budget. Concatenating the parts restores the supplied PDF's SHA-256, and both `intake.py` and `rebuild.py` verify it before they run. Original filename and SHA-256 are in `source_manifest.json`.

The complete original PDF is also committed for direct download at [Jackery Smart Transfer Switch.pdf](../../../original/Jackery%20Smart%20Transfer%20Switch.pdf). This byte-identical copy sits outside the frozen Web package and is not a served Web asset. Its SHA-256 is `11ce66b135c5a1b1141c33e4368552124f24757db78d0890a0cdfe3e4f14bff3`.
