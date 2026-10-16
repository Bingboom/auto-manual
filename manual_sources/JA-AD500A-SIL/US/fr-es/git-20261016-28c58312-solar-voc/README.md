# JA-AD500A-SIL / US / fr + es — solar-Voc correction edition

Operator instruction, 2026-10-15: replace the solar-panel Voc paragraph so it cites the Jackery DC Input Module's DC input voltage range (16V–60V) instead of the downstream FridgeGuard / Battery Pack ranges (“整段替换”), keeping the third-party-panel disclaimer (“不删免责句”); French and Spanish follow the operator-approved translations.
This edition applies that correction to the [approved package](../git-20261007-28c58312-reviewed/README.md) (MA-262). The approved package, its printed source and its release evidence remain immutable.

**Status: `operator-approved-git-only-release`.** Accepted by the operator on 2026-10-16 (「全部验收并发布上线」; 「验收记录 允许你写」, MA-312): `source/approval.json` binds every reviewed `source/` and `assets/` input, and the IR is publication-eligible. Release is the Git-only Web Publish sealed at the merged `main` commit.

## What changed

One paragraph in each of `source/page/charging_fr.rst` and `source/page/charging_es.rst`; see `source/differences.md`. Every other `source/` and `assets/` file is a byte-for-byte copy of the approved package, and each rendered Markdown is the approved Markdown with exactly that paragraph replaced (`tests/test_jaad500a_sil_us_solar_voc.py`). `source/native_copy.json` and the printed `source/original.pdf` keep the printed wording; the PV Voc source concern in `source_manifest.json` records the correction.

## Reconstruction

`derive_solar_voc.py` copies the approved inputs, applies the corrections (each must match the approved text exactly once) and refreshes `source_manifest.json`, plus `frozen_source_manifest.json` once `web/fr` and `web/es` exist. A second run leaves the tree unchanged.

```sh
PKG=manual_sources/JA-AD500A-SIL/US/fr-es/git-20261016-28c58312-solar-voc
python "$PKG/derive_solar_voc.py"
python "$PKG/render.py" fr tmp/jaad500a-us-fr-voc
python "$PKG/render.py" es tmp/jaad500a-us-es-voc
python -m sphinx -n -W --keep-going -b html tmp/jaad500a-us-fr-voc tmp/jaad500a-us-fr-voc-html
python -m unittest tests.test_jaad500a_sil_us_solar_voc
```

Replace `web/fr` and `web/es` with fresh renders after any source change, then re-run the derivation.
