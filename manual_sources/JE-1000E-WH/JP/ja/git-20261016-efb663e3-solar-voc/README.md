# SlimPower H1 JP — solar-Voc correction edition

Operator instruction, 2026-10-15/16: replace the solar-panel Voc paragraph so it cites the Jackery DC Input Module's DC input voltage range (16V～60V) instead of the H1's own DC input range (“整段替换”), keeping the disclaimer (“不删免责句”); on 2026-10-16 the operator dropped the opening accessory warning, which contradicted the recommendation and the disclaimer (“删掉第①句”).
This edition applies that correction to the [approved Web edition](../git-20261008-efb663e3-no-cover-reviewed/README.md) (MA-277). The approved edition, its printed source and its release evidence remain immutable.

**Status: `operator-approved-git-only-release`.** Accepted by the operator on 2026-10-16 (「全部验收并发布上线」; 「验收记录 允许你写」, MA-312): `source/approval.json` binds the chapters, presentation, component requirements and every reviewed input, and the IR is publication-eligible. Release is the Git-only Web Publish sealed at the merged `main` commit.

## What changed

The first three sentences of one paragraph of `source/chapters.json`; see `source/differences.md`. Every other copied input is byte-identical to the approved edition, and the rendered Markdown is the approved Markdown with exactly that paragraph replaced (`tests/test_jp_solar_voc.py`). The printed PDF and `source/native-text.json` keep the printed wording.

## Reconstruction

`derive_solar_voc.py` copies the approved inputs, applies the correction (which must match exactly once) and writes `source_manifest.json`, inventorying every package file. `rebuild.py` is the approved replay with the release check replaced by candidate/accepted status; `verify.py` is the approved verifier with only the declared native block exempted from verbatim coverage.

```sh
PKG=manual_sources/JE-1000E-WH/JP/ja/git-20261016-efb663e3-solar-voc
python "$PKG/derive_solar_voc.py"
PYTHONPATH=. python "$PKG/rebuild.py" --output tmp/h1-voc-cold
python -m sphinx -W --keep-going -b html tmp/h1-voc-cold tmp/h1-voc-html
PYTHONPATH=. python "$PKG/verify.py" --html tmp/h1-voc-html/manual.html
python -m unittest tests.test_jp_solar_voc
```

Replace `web/ja` with a fresh cold replay after any source change, then re-run the derivation.
