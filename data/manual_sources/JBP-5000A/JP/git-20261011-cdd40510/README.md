# JBP-5000A / JP / ja — native Web candidate

Authoritative source: `Jackery Battery Pack 5000 Plus 取扱説明書.pdf`.
The physical cover identifies JBP-5000A and Japan-only use. It has 10 pages;
SHA-256 is `cdd40510647f7d45a80f58eccddba32754346edeaede760c993ca6670af6bfc8`.
Printed version is unknown. Illustrator metadata is retained as evidence,
without treating its timestamps or the product name as a printed version.

The Web body follows physical pages 2–10 in their printed order. Page 1 is
archived in `source/print-cover.json`, outside the Web body. All 213 native body
lines are classified once; 137 live source selections remain selectable HTML.
The 9 printed chapters include specifications, inbox, overview, LCD, operations,
battery combinations, charging, warranty and precautions. The final App
download block remains within precautions, without an invented App chapter.

Shared Manual IR and Web components own the headings, 12-row specification
table, 2-row LCD table, 3-card inbox and 5 authored-label callouts. A source
warranty note without an authored signal word retains its native gray block.
No per-model configuration, renderer, phase2 enrollment or print target is added.
Native source statements and units are preserved, including the printed
stacking wording. This conversion does not correct technical source copy.
The specification group title retains the printed mixed case and has no
ordinary H2 circle. Its font, size, weight and spacing still use shared styles;
the source stylesheet only suppresses the generic uppercase/marker treatment.
The two live LCD map numerals are centered inside the complete circle bounds
from native page 4 drawings 2032/2034, rather than positioned by text metrics.
The four lock/unlock step numbers likewise use the full circle bounds from
native page 5 drawings 3793/3794/3791/3792; original artwork is unchanged.
The native recycling notice uses a single shared bordered panel: the existing
transparent Li-ion symbol has a fixed column, with its heading and three real
bullet statements beside it. The preceding bold specification notice retains
its square CSS marker. All source copy and symbol artwork are unchanged.
The safety list removes paragraph tail gaps inside its 11 original bullets;
shared typography and item spacing remain in effect.
The accessory-support notice below the inbox cards retains its native single
disc bullet through the shared unordered-list style.
The LCD table numbers 1/2 use paragraph carriers for the existing shared
circle style; the numerals remain selectable text and centered within each ring.
Warranty preserves the physical pages 8–9 grouping: a shared gray introduction,
bordered clause groups 1–7 and 8–11, thin row separators, seven exclusions
within clause 5, and the second paragraph within clause 2. Shared panels own
the fill, border and radius; source-local styles set row padding and spacing.
Browser admission verifies these boundaries, clause order and visible text
containment at all three widths. Every word and original artwork is retained.

The 12 ReferenceFigures use complete native artwork and 27 editable labels.
Lock/unlock stages plus the hookup remain one original panel; the two stacking
examples remain one original row. The stacking SVG keeps every existing vector
object and expands its viewport to contain the complete original bottom borders.
The stacking notice uses the shared shaded-label/white-body treatment with four
real bullets, the original two-line label and natural body wrapping. Dense figures scroll within their own mobile
container. Their letters are not reduced to unreadable dimensions or split
into new cards. The original horizontal App Store/Google Play badges and full
vector QR frame remain together in the final download block.

`source/asset_decisions.json` records the search, concrete differences, rejected
variants, exact hashes and background policy before acquisition. Five assets
are reused byte-identically: the JE-5000A combination panel, service lockup,
connected-battery badge, shared Li-ion symbol and existing clean expansion
cable. Native 100 and battery-with-bolt LCD glyphs are genuinely transparent;
80%, 188 and bolt-only variants were rejected by actual contour comparison.
Complete panel shading, product surfaces, borders and leader lines are retained.
No independent empty caption frame is acquired; such frames belong in shared
CSS. Only fixed physical-book/store/device lettering stays in the artwork.

`source/native_export_compatibility.json` documents exact implicit/explicit
closure equivalence in this PDF's compound fill/stroke paths. Both original
SVG elements and their ancestor transforms/clip groups are retained. No shared
exporter behavior, source path colors or opacity is changed.

Replay from the repository root, with unused output directories:

```sh
python3 data/manual_sources/JBP-5000A/JP/git-20261011-cdd40510/rebuild.py --output tmp/jbp5000a-replay/ja
python3 -m sphinx -n -W --keep-going -b html tmp/jbp5000a-replay/ja tmp/jbp5000a-html/ja
python3 data/manual_sources/JBP-5000A/JP/git-20261011-cdd40510/validate_source.py --output tmp/jbp5000a-html/ja
python3 -m http.server 8936 --bind 127.0.0.1 --directory tmp/jbp5000a-html
python3 data/manual_sources/JBP-5000A/JP/git-20261011-cdd40510/validate_layout.py --base-url http://127.0.0.1:8936 --evidence-dir tmp/jbp5000a-browser-qc
```

This is an operator-review candidate, not a publication authorization. It remains
Git-only: no live Base, source table, queue, online asset registry or HTML_link
writes. The original PDF, candidate and evidence are retained independently of
the JE-5000A host release.
