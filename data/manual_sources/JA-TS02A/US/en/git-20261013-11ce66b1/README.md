# JA-TS02A / US / English — Git-only PDF intake

This package freezes the supplied Jackery Smart Transfer Switch PDF (model JA-TS02A, printed version JAK-UM-V1.0) and converts only printed English pages 01–22, physical PDF pages 3–24. The printed cover, global contents, non-English bodies and back cover are archived in the original PDF, not repeated in the Web body.

Text, specification/indicator/cable/torque/symbol tables remain selectable. Figures preserve complete same-model US panels and App screenshot frames. The asset decisions precede extraction; four standard safety symbols reuse shared bytes. Five visible lines absent from both native PDF text extractors are transcribed in source/text-recovery.json with source coordinates; no technical value or wording is rewritten. App inline controls are rendered from their exact source faces.

Replay from the repository root:

```sh
PYTHONPATH=. python3 data/manual_sources/JA-TS02A/US/en/git-20261013-11ce66b1/build_web.py --output /tmp/ja-ts02a-fresh-replay
python3 -m sphinx -W --keep-going -b html /tmp/ja-ts02a-fresh-replay /tmp/ja-ts02a-fresh-html
```

The shared MyST/Furo scaffold and Web stylesheet are reused. This source-local adapter follows the external frozen-MyST exception in the Web Publish Git-only contract; it does not register a new phase2 or print-build target. The existing build.py JE-1000F/US check is a repository regression gate only, and does not validate this manual's body. Source hashes, all 22 English pages, native table rows, artwork closure, cold replay, strict Sphinx and browser checks validate this new body.

Git-only boundary: no Feishu/Base/source table, queue, online asset, build/link or HTML_link writes. This is a source candidate for review, not a production publication. Original source filename and SHA-256 remain in source_manifest.json.

The unchanged 94,486,777-byte original PDF is archived losslessly as three ordered binary parts (each ≤32 MiB), matching the frozen-source per-file budget. Concatenating the parts restores the exact supplied PDF SHA-256. The adapter verifies the reassembled digest before every build. The user’s original file is preserved in Downloads.
