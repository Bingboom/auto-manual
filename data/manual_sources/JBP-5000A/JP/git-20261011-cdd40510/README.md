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

The 12 ReferenceFigures use complete native artwork and 27 editable labels.
Lock/unlock stages plus the hookup remain one original panel; the two stacking
examples remain one original row. Dense figures scroll within their own mobile
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
