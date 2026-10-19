# JA-AD500A-SIL / US / fr — spec-label correction edition

Operator instruction, 2026-10-19: 「法语版规格表 Input/Output 写反了 == 这个改掉发布」. In the printed French specification table, the module's DC input rows (11V–16V and 16V–60V) are labelled *Sortie CC* (output) and its DC output row (42V–58V) is labelled *Entrée CC* (input). The English and Spanish editions and the module design have them the other way round. The original package recorded this as a source concern, "preserved as printed; requires operator/source-owner correction decision", and this edition carries out that decision.

This French-only edition is derived from the live [solar-Voc edition](../git-20261016-28c58312-solar-voc/README.md) (MA-312). That edition stays immutable and keeps serving Spanish. The base edition, its printed source and its release evidence stay unchanged.

**Status: `operator-approved-git-only-release`.** Accepted on 2026-10-19 (MA-319). `source/approval.json` binds every reviewed `source/` and `assets/` input, and the IR is publication-eligible. Release is the Git-only Web Publish sealed at the merged `main` commit.

## What changed

- **Copy:** the two labels in `source/page/spec_fr.rst` are swapped; see `source/differences.md`. The rendered visible copy is the base edition's French copy with exactly those two labels swapped (`tests/test_jaad500a_sil_us_fr_spec.py`). `source/native_copy.json` and `source/original.pdf` keep the printed labels.
- **Shared styles:** a re-frozen locale must pass the prepared-document shared-style gate (`tools/web/prepared_style_audit.py`), which the base edition predates (it stays in `prepared_style_baseline.json`). `derive_fr_spec.py` therefore moves the French pages onto shared theme classes, with no copy change:
  - Product overview: the `manual-overview-composition` wrapper and its inline width move to a geometry rule on the shared reference figure.
  - LED table: the inline-styled raw HTML table becomes a list table on the shared `hb-source-status` / `hb-source-status-table` classes. It is declared in `source_manifest.json` → `shared_component_exceptions`, because no shared LED-state component exists.
  - Contact block: the source-local `manual-contact-footer` / `contact-qr` classes and inline styles become one shared `hb-text-panel`; the QR size moves to a geometry rule.
  - `source/presentation.css` is new and holds geometry only; `render.py` passes it as the IR source stylesheet.

  The LED table and contact block now take the shared theme look (as in the JA-AD500A-SIL JP solar-Voc edition) instead of the page-drawn border.

Every other copied French `source/` and `assets/` file is a byte-for-byte copy of the base edition. The Spanish pages, `source/approval.json` and `source/differences.md` of the base edition are not copied.

## Reconstruction

```sh
PKG=manual_sources/JA-AD500A-SIL/US/fr-es/git-20261019-28c58312-fr-spec
python "$PKG/derive_fr_spec.py"
python "$PKG/render.py" fr tmp/jaad500a-us-fr-spec
python -m sphinx -n -W --keep-going -b html tmp/jaad500a-us-fr-spec tmp/jaad500a-us-fr-spec-html
python -m unittest tests.test_jaad500a_sil_us_fr_spec
```

After any source change, replace `web/fr` with a fresh render, then run the derivation again.
