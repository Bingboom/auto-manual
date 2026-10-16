# JA-AD500A-SIL / JP / ja — solar-Voc correction edition

Operator instruction, 2026-10-15/16: replace the solar-panel Voc paragraph so it cites the Jackery DC Input Module's DC input voltage range (16V～60V) instead of the downstream SlimPower H1 / Battery Pack ranges (“整段替换”), keeping the disclaimer (“不删免责句”) and the opening accessory warning (“保留这句”).
This edition applies that correction to the live [Web-layout edition](../git-20261009-ac3a1f82-web-layout/README.md) of the approved package (MA-272). The base edition, its printed source and its release evidence remain immutable.

**Status: `review-candidate-no-release-authorization`.** The edition renders but is not publication-eligible. Release needs the operator's acceptance in `source/approval.json` (binding every reviewed `source/` and `assets/` input), `publication_status` switched to `operator-approved-git-only-release` in `derive_solar_voc.py`, and a Git-only Web Publish.

## What changed

The middle sentences of one paragraph in `source/page/charging_ja.rst`; see `source/differences.md`. Every other copied `source/` and `assets/` file is a byte-for-byte copy of the base edition, including its page-local `source/presentation.css`. The rendered Markdown is the base edition's Markdown with exactly that paragraph replaced (`tests/test_jp_solar_voc.py`). `source/native_pages.json` and `source/original.pdf` keep the printed wording.

## Reconstruction

```sh
PKG=manual_sources/JA-AD500A-SIL/JP/ja/git-20261016-ac3a1f82-solar-voc
python "$PKG/derive_solar_voc.py"
python "$PKG/render.py" tmp/jaad500a-jp-voc
python -m sphinx -n -W --keep-going -b html tmp/jaad500a-jp-voc tmp/jaad500a-jp-voc-html
python -m unittest tests.test_jp_solar_voc
```

Replace `web/ja` with a fresh render after any source change, then re-run the derivation.
