# JS-100I / JP / ja — spec-table edition (Jackery SolarSaga 100 Air)

Operator review of the live page, 2026-10-27: 「这个表格样式不对吧」. The 電気データ table was
published as a plain table without the shared spec-table frame that 基本情報 and 多機能アダプタ have.
After reviewing the 1280/390 renders of the fix the operator chose a new edition: 「按新版本包发布」.
This edition applies that layout fix to the released [base package](../git-20261026-cc8b3421/README.md)
(#1611). The base package, its printed source and its release evidence remain immutable.

**Status: `operator-approved-git-only-release`.** `source/approval.json` binds every reviewed
`source/` and `assets/` input; the IR is publication-eligible. The base release's decisions carry
over: every source concern stays verbatim for the source owner (「全部照录…保留疑点后续纠正」).

## What changed

- `source/page/spec_ja.rst`: the 電気データ table is drawn as the shared `hb-spec-table-composition`
  with the shared `hb-spec-label` / `hb-spec-value` cell classes, as the two HB-TABLE-SPEC tables are.
  It stays a declared three-column table in `shared_component_exceptions` (HB-TABLE-SPEC has two
  columns and no header); its text hash is unchanged.
- `source/presentation.css`: the narrow-screen scroll rule gives way to two geometry/typography rules:
  the STC/BNPI header is bold as printed and the three columns fit 390 px without scrolling.

No copy changes: the visible copy equals the base edition's (`tests/test_js100i_jp_web.py`). Every
other copied `source/` and `assets/` file, and `render.py`, is a byte-for-byte copy of the base;
see `source/differences.md`.

## Rebuild

From the repository root (same toolchain as the base package):

```sh
PKG=manual_sources/JS-100I/JP/ja/git-20261027-cc8b3421-spec-table
python "$PKG/derive_spec_table.py"
python "$PKG/render.py" tmp/js100i-jp-spec
python -m sphinx -n -W --keep-going -b html tmp/js100i-jp-spec tmp/js100i-jp-spec-html
python -m unittest tests.test_js100i_jp_web
```

Replace `web/ja` with a fresh render after any source change, then re-run the derivation, which also
writes `frozen_source_manifest.json` once `web/ja` exists.

## Release boundary

As for the base package: after the engineering PR merges, seal at the merged `main` commit, assemble
from Hello-Docs `main`, open a `docs/publish/**`-only PR, then verify RTD
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction)).

Not touched: live Base, queue, source tables, HTML_link, asset registry, workflows, dependencies, the
base package and the JS-100I EU packages.
