# JE-1000F EU: four new Web languages

This directory is the frozen Git-only Web input for Ukrainian (`uk`),
Portuguese (`pt`), Dutch (`nl`) and Polish (`pl`). It does not replace the
published `en/fr/es/de/it` v2.7 books.

The designated Illustrator source is `HTE153-EU-9国语言-0923.ai`, SHA-256
`c38415f5c2d96832119105d963737a10901e470f70c5e7518ef6404f83625eb2`.
Its PDF-compatible layer has 161 physical pages. This package contains the
exact source text extraction, source-page geometry, locale-specific cropped
illustrations, structured table reconstructions, the pinned section index and
Web stylesheet, and a deterministic MyST formatter. The source binary remains
in the operator's original archive; its
67.8 MB bytes are not placed in the Web tree.

The source pages for each Web language are:

| Web language | Illustrator body pages | Printed body pages |
| --- | --- | --- |
| `uk` (source uses `UA`) | 93–109 | 86–102 |
| `pt` | 110–126 | 103–119 |
| `nl` | 127–143 | 120–136 |
| `pl` | 144–160 | 137–153 |

All four also use the cover on physical page 1, their own preface on page 3 or
4, and the shared English EU declaration/manufacturer page 161. Each target
has 13 chapters. Body text and safety instructions are selectable HTML; the
troubleshooting, specification, LCD, symbol, warranty, App and operating
tables/lists are assembled from the source's positioned text objects. The
illustrations are independent crops from the corresponding language pages.
The published portal supplies the language selector; the frozen MyST keeps
only the chapter navigation to avoid a duplicate selector on phones.
`source/source_completeness.json`, `source/figure_qa.json` and the eight
contact sheets under `source/qa/` preserve the source extraction and crop
review results; they are included in the input hash inventory.

To regenerate the MyST candidate from this committed input:

```bash
python3 manual_sources/JE-1000F/EU/nine-language/git-20260927-c38415f5/four-language/build_web.py \
  --output-root /tmp/je1000f-four-web
```

Build each `/tmp/je1000f-four-web/JE-1000F/EU/<lang>/md` directory with
`python3 -m sphinx -W -b html`. The local `conf.py` copies raw-HTML image
assets into the verification HTML directory. The publish assembler has its own
asset-copy and path-rewrite step; verify all referenced images again after
assembly.

The existing `build.py check` for JE-1000F/EU, using the committed
`manual_sources/JE-1000F/EU/en-fr/2.0/phase2` snapshot, is a regression check
for the prior merged-language target. It does not validate the four new AI
bodies. Their release gates are the designated-source hash, input inventory,
page/section/figure mapping, text/table comparison, strict Sphinx build and
desktop/mobile browser review. No phase2 or print target is registered here.

The renderer normalizes layout-only line breaks, reconnects the split
`support.jackery.com` URL, places source `®` marks next to both USB names,
recovers the vector `+` App button as selectable text, and removes literal
backslash quoting around Dutch `"Jackery"`. It reconnects the Portuguese
print-wrapped `continuamente` in the LCD mode table. The raw extraction files are
retained unchanged. The operator approved the Ukrainian USB-C sentence and
Dutch AC labels on 2026-09-28. `source/errata.json` records physical/printed
pages, original and corrected wording, evidence, the confirmation quote,
source PR #1315 and publication version `git-20260927-c38415f5`.
The original Dutch front-view and App crops remain in `figures/nl/`;
`corrections/nl/p129_front_view_AC.png` and
`corrections/nl/p142_app_control_AC.png` are separate corrected Web assets.
Both hashes and the image correction evidence are retained. The source
manifest inventories both raw and corrected inputs, and the final release
receipt binds them to the remote engineering Git commit.
