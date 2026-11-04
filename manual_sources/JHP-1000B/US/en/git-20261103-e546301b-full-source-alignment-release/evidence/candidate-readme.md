# JHP-1000B / US / en — complete source alignment candidate

Record `reczz28SlRGJi0KB`, original single-language attachment SHA-256 `e546301b5cba7a6774418544a74c689f69712fd0fac6189df016f8020c0d98b1`. Earlier frozen editions are unchanged. This edition restores source safety columns, warning artwork and native copy, panel copy coordinates, source clock/triangle marks, merged LCD/USB-C cells, F7 voltage subscript, title hierarchy, and back contact/address/QR. All source transcription/model values remain unchanged.

The operator explicitly excludes the front cover and paper TOC. Local build plus full content/layout review is sufficient for the review checkbox. This is a **candidate**, with `publication_eligible: false`; integration and release are separate. No new release approval is inferred from the old package.

From the repository root, using the repository Python environment:

```sh
python manual_sources/JHP-1000B/US/en/git-20261103-e546301b-full-source-alignment/build_content.py
python manual_sources/JHP-1000B/US/en/git-20261103-e546301b-full-source-alignment/refresh_manifest.py
python manual_sources/JHP-1000B/US/en/git-20261103-e546301b-full-source-alignment/rebuild.py --output /tmp/jhp1000b-new-web
python -m sphinx -n -W --keep-going -b html /tmp/jhp1000b-new-web /tmp/jhp1000b-new-html
```

`derive_assets.py` and `derive_restored_assets.py` reproduce artwork only from the bound PDF or verified byte-identical registered assets. `source_layout.py` places editable native text at the source geometry. No shared templates, parser, CSS, phase2, or live data are changed. `source/differences-audit.json` resolves every previous layout declaration; `evidence/review.json` links the full source/page, bidirectional text, browser, and cold-replay checks. The original manuscript's source concerns remain recorded in `source_manifest.json`; they are not silently corrected.
