# JA-AD500A-SIL / US / en — solar-Voc correction edition

Operator instruction, 2026-10-15: replace the solar-panel Voc paragraph so it cites the Jackery DC Input Module's DC input voltage range (16V–60V) instead of the downstream FridgeGuard / Battery Pack ranges (“整段替换”), keeping the third-party-panel disclaimer (“不删免责句”).
This edition applies that correction to the [approved package](../git-20261006-a6d1659e-reviewed/README.md) (MA-259). The approved package, its printed source and its release evidence remain immutable.

**Status: `operator-approved-git-only-release`.** Accepted by the operator on 2026-10-16 (「全部验收并发布上线」; 「验收记录 允许你写」, MA-312): `source/approval.json` binds every reviewed `source/` and `assets/` input, and the IR is publication-eligible. Release is the Git-only Web Publish sealed at the merged `main` commit.

## What changed

One paragraph in `source/page/charging_en.rst`; see `source/differences.md`. Every other `source/` and `assets/` file is a byte-for-byte copy of the approved package, and the rendered Markdown is the approved Markdown with exactly that paragraph replaced (`tests/test_jaad500a_sil_us_solar_voc.py`). The printed source `source/original.ai` keeps the old wording.

## Reconstruction

`derive_solar_voc.py` copies the approved inputs, applies the correction (which must match the approved text exactly once) and refreshes `source_manifest.json`, plus `frozen_source_manifest.json` once `web/en` exists. A second run leaves the tree unchanged. `render.py` checks every input hash and the release status, then runs the existing prepared RST → manual-ir/v2 → shared Web/MyST pipeline.

```sh
PKG=manual_sources/JA-AD500A-SIL/US/en/git-20261016-a6d1659e-solar-voc
python "$PKG/derive_solar_voc.py"
python "$PKG/render.py" tmp/jaad500a-us-en-voc
python -m sphinx -n -W --keep-going -b html tmp/jaad500a-us-en-voc tmp/jaad500a-us-en-voc-html
python -m unittest tests.test_jaad500a_sil_us_solar_voc
```

Replace `web/en` with a fresh render after any source change, then re-run the derivation.
