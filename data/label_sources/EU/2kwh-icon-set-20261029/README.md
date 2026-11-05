# EU label marks for the shared Web symbol library

Three product labels from the Feishu wiki page 「2度电以上图标整理」
(node `TrYWwb2rRiHOQ0kXlJ3c8EvUnHd`, 17 label PDFs for the ≥2 kWh EU/UK
products), downloaded 2026-10-29. They are the source of nine marks that no
manual or shared asset carried yet:

| File here | Feishu title | Wiki node | SHA-256 | Marks |
| --- | --- | --- | --- | --- |
| `HTE1563000A-EU-UK_rear-label.pdf` | 16-0101-000677 HTE1563000A-EU UK-JAK 后标贴 RoHS REACH-Q.pdf | `RH2mwjceiial7UkaqCkcqQuanqi` | `871367165ee5976422ef7736b546c16b464d32ef1af96624e5f22f629dbf5cbd` | CE, UKCA, Ukrainian conformity mark |
| `HTE1563000A-EU_box-info-label.pdf` | 16-0101-000387 HTE1563000A-EU-JAK 彩盒信息标贴 A1 RoHS REACH-Q.pdf | `POQdwLGduiuyd7kgkwccNKZWnHB` | `a4099ae690f1c065bb28444f53f750fc7177298a72d0133ebe9f44924ee6264c` | UN38.3, Triman + Info-tri (packaging, device) |
| `HTE1542000A-EU-UK_rep-label.pdf` | 16-0101-000873 HTE1542000A-EU UK-JAK 欧英代标贴 A0 RoHS REACH-Q.pdf | `HhoJwepB1idAP7kKAOccVY9Enud` | `5eb72dc0b8a01d46c1cb9241403fd947ef0a166bc7003784ec1435f30fcd96c9` | EC REP, UK REP, battery bin with Pb |

HTE1563000A is JE-3000C and HTE1542000A is JE-2000F (`data/model_languages.csv`).
The same CE, UKCA, UN38.3 and Triman artwork is printed on the other models'
labels; the folder keeps one source per mark, not every label.

## Selection and the ink exception

Each mark is the unchanged `native_symbol_svg` selection of every drawing inside
a reviewed glyph box on page 1. The selection, box and hashes live in the mark's
`provenance` in
[`shared/symbols/manifest.json`](../../../../docs/renderers/web/assets/shared/symbols/manifest.json).

The labels are reverse-printed: silver ink on a dark label, white ink on the
orange box. Kept as printed, the marks vanish on a white manual page. The
operator approved one exception to the no-recolour rule on 2026-11-02
(「形状照原稿，改深灰」): paths, transforms, clipping and opacity stay native; only
the label colours are mapped, per mark, by the recorded `ink_map`:

- silver or white label ink → `#454546`, the ink of the shared EU symbols;
- label-background colour drawn on top of that ink (orange inside the Triman
  blocks) → paper white, so figure and ground keep their roles;
- label-background colour drawn straight on the background, which the label
  never shows (`hidden_fill_ordinals`: a stray "s" after "cordon" in the Triman
  device block, a zero-area path in each REP frame) → `fill="none"`.

The library files are therefore inked candidates, not native glyphs. When a
manual's authoritative artwork later prints one of these marks, the symbol
admission still compares against that artwork; a different glyph or tint gets
its own variant.

## Replay

```bash
python data/label_sources/EU/2kwh-icon-set-20261029/extract_marks.py --check
python data/label_sources/EU/2kwh-icon-set-20261029/extract_marks.py --output <unused dir>
```

`--check` re-extracts all nine from these PDFs and compares the native and
inked hashes and the library files. The native bytes were recorded with
PyMuPDF 1.28.0 / MuPDF 1.29.0; another version may serialise the SVG
differently.
