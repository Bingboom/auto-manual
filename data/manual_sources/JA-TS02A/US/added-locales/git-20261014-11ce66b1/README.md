# JA-TS02A / US / French · Spanish — Git-only Web release

This package adds the French and Spanish Web editions of the Jackery Smart Transfer Switch manual (model JA-TS02A, printed version JAK-UM-V1.0) from the same supplied booklet as the accepted English edition. It converts the printed French and Spanish bodies only:

| Language | Printed pages | PDF pages | Web root |
| --- | --- | --- | --- |
| French | 23–44 | 25–46 | `web/fr` |
| Spanish | 45–66 | 47–69 (PDF 65 repeats PDF 64) | `web/es` |

The cover, global contents, English and Portuguese bodies and back cover stay in the archived PDF (「封面和目录 不用体现在web版面上」).

**Status: operator-accepted Git-only release.** The operator reviewed the layout review page (print beside the desktop and phone Web per chapter, French and Spanish tabs) for candidate `d35efce`, which was merged as PR #1530 (`9ca45d81`) with decisions D1–D6 at their defaults. On 2026-10-14 the operator accepted both editions for release (「授权你合入」, in reply to the go-live prompt). `source/approval.json` binds that acceptance to these exact source inputs, and both replayed IRs are `publication_eligible: true`. Release runs under MA-307 in `code-as-doc/dev/merge_authorizations.md`.

## Package shape

This is an add-on package (`US/added-locales/`, like `JHP-3600C/US/added-locales`). The English edition `../../en/git-20261013-11ce66b1` is live and operator-accepted (MA-302). Its `source/approval.json` binds the acceptance to that package's exact inputs, and its README, test and route `JA-TS02A/US/en/md` name that package. A single US-level package (the JBP-3600A shape) would have meant moving or re-inventorying the accepted English package and voiding its acceptance. This package leaves the English package byte-for-byte untouched; the test checks that.

The source identity is still one: `source_manifest.json` names the same 94,486,777-byte PDF (SHA-256 `11ce66b135c5a1b1141c33e4368552124f24757db78d0890a0cdfe3e4f14bff3`). It holds no copy of it. The English package's three archive parts are pinned repository inputs, and `intake.py`, `extract_assets.py` and `rebuild.py` reassemble them and verify the SHA-256 before they run. The English records and artwork that the extraction reuses are pinned the same way.

## Layout reference and method

The layout follows the accepted English edition (fixes R1–R9): the same 11 chapters in the same order, the same shared components, figures, callouts and tables. Wording is as printed in each language. The method follows JBP-3600A US: a per-language region table (`GEOMETRY` in `source/intake.py`), print line breaks and hyphen joins logged per language, outlined text restored from source pixels with glyph-path boxes, symbols admitted per locale, and FR/ES panels sharing an English file only when the crop matches it within antialiasing.

| Print feature | Web |
| --- | --- |
| Line breaks | A line the print ends while the next word would still have fitted is a print break; every other line end is a wrap. Logged in `source/<lang>/coverage.json` (36 per language). |
| Hyphen splits | Rejoined and logged: FR domes-/tique, automatique-/ment, immédi-/atement, alimenta/tion (no hyphen); ES concesion-/ario, recomien-/da, instruc-/ciones. |
| Outlined text | Two French Dashboard lines (p42) are vector outlines with no text layer. `source/text-recovery.json` restores them from source pixels with their glyph-path boxes (straight apostrophe as printed). Spanish has none. |
| Repeated page | The Spanish print repeats its p62 (PDF 64 and 65 are word- and pixel-identical). The repeat is classified `duplicate-print-page` and left out. |
| Weights, headings | Bold print runs are `strong`; headings keep print case. Table header cells that the French and Spanish prints set in regular weight stay regular. |
| Callouts | Print labels as printed: AVERTISSEMENT / PRECAUCIÓN (shaded strips; English CAUTION), Avertissement / Advertencia (warning lockups with the print's yellow triangle). |
| Tables | Native row and column spans, as in English. Spanish torque values (pulgadas-libra) wrap on desktop; phones scroll the torque table, as in English. |

Shared components per language: HB-CALLOUT-STRIP 4, HB-SPECIAL-APP 1, HB-SPECIAL-REFERENCE-FIGURE 30, HB-WARRANTY-LEAD 1, HB-WARRANTY-SECTION 6. English has five callout strips. The French and Spanish prints set the "Installing the Deadfront Cover" warning as a plain line with no triangle, so it stays a body line.

## Artwork reuse

Inventory first, per the Web artwork reuse order. Decisions are recorded in `source/figures.json`, `source/inline-controls.json` and `source/symbols.json`.

- **Panels.** Each FR/ES panel was compared with the accepted English crop at the offset where its page prints the same art. Three match within antialiasing and share the English file: FR deadfront installation, FR IoT pairing and ES store badges. The other 61 are cut from their own pages as complete panels at the English 3x scale, because their labels are translated or the art sits at a sub-point offset. Two crops leave one area blank: the FR system overview leaves the printed folio under its last label, and the ES cable-entry panel leaves the "Conexiones Eléctricas" heading that shares its print band (the heading stays live copy).
- **Inline App controls.** All 14 are vector-identical to the English drawings (≤ 1.5e-5 pt) and share the English files.
- **Symbols.** Each symbol is checked with the fixed shared glyph gate against that language's own page. The English yellow triangle and the shared read-manual symbol pass and are reused. The shared grounding, caution and electric-shock assets reused by the English edition, and its ingestion-hazard glyph, miss the gate against this print. The print draws white-filled thin outlines; the shared assets are grey-tinted, thick-outlined tiles. FR/ES therefore use the print's own vectors (`assets/*-print.svg`, one file for both languages).

## Print-source issues kept as printed

These were noticed during review and are kept, not corrected; the list is not exhaustive. FR: "Symbol" table header in English, untranslated "Feed-In Type" and "100A Grid/ 60A Power Station", "Panel de distribution", "Connecter à la Panneau", "l'Smart Transfer Switch", "à le Smart Transfer Switch", "Briseurs recommandés", "disjoncteurs 20A, disjoncteurs; pas de…" (30A missing), and "one désignée" in the cable-entry art. ES: heading "Opcionale", "lCES-003", the stray asterisk in "*Plan de carga y descarga", "período de descargar", "5000 Plus(Máx.", Portuguese "botão de parada de emergência" in the emergency-stop art, and the repeated page.

## Reconstruction

Run from the repository root (PyMuPDF 1.28.0 / MuPDF 1.29.0, `requirements.lock`):

```sh
PKG=data/manual_sources/JA-TS02A/US/added-locales/git-20261014-11ce66b1
python3 "$PKG/source/extract_assets.py"
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
for lang in fr es; do
  PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --language "$lang" --output "tmp/ja-ts02a/$lang"
  python3 -m sphinx -n -W --keep-going -b html "tmp/ja-ts02a/$lang" "tmp/ja-ts02a-site/$lang"
done
```

To re-freeze: remove `web/`, run `source/refresh_manifest.py`, rebuild each language into `web/<lang>`, and run `source/refresh_manifest.py` again. `tests/test_ja_ts02a_us_fr_es_web.py` covers identity, the operator acceptance, coverage, intake reproduction, cold replay, admissions and the English package being untouched. `audit/browser-validation.json` records the Chromium sweep from 320 to 1920 px.

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes. No phase2 or print-build target, and no change to shared renderers, templates, workflows, dependencies, CLI or schema.
