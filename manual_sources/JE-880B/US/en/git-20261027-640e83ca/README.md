# JE-880B / US / English — Git-only Web candidate

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」.
This package converts the English single-language manual of the Jackery Explorer 880 Pro (model JE-880B,
printed version JAK-UM-V1.0) from the 发布文档管理 Base row `reczz28SPRx9mkQB` (material 38-0001-000399,
project HTE104). Route `JE-880B/US/en/md`, `legacy_default` (no US Web edition exists for this model).

**Status: `operator-approved-git-only-release`.** On 2026-10-28 the operator confirmed 「上线提交发布：JE-300C、
JE-300E、JE-300E-SG、JE-880B；授权合入 #1631 及其 Hello-Docs 发布 PR」 under MA-365
(「授权全部合入上线 上线之后 我再一个个核对版面」). `source/approval.json` binds that acceptance to these exact
source inputs and the IR is publication-eligible; the operator checks the layout on the live page after
release. The default layout decisions are listed in [`audit/review.zh.md`](audit/review.zh.md).

## Source authority

- `original.pdf`: the row's English PDF, byte-exact (SHA-256 `640e83ca…`, 11 pages). Outlined, no text layer.
- Print master: `38-0001-000399 说明书 HTE104880A-US-JAK  RoHS REACH-q.pdf` (one artboard); name, size and
  SHA-256 in `source_manifest.json:print_master`, not archived here.
- Identity (record id, material number, project, SKU) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

The same outlined-PDF method as `manual_sources/JE-300E/US/en/git-20261027-04bd8b90`: `source/intake.py`
holds the line-by-line transcription of every English line in PDF order (cover p1 excluded), built from
shared flow and shared components only (`source_manifest.json:component_map`); source slips are kept as
printed and listed in `source_manifest.json:source_concerns`. The print has no symbol table. Figures are
cut from `original.pdf` at 4x; the six LCD pictograms set inline in run-in subheadings are this print's
own pixels as transparent PNGs (the shared native-SVG mapper does not support their paths; recorded in
`source/glyphs.json`). No released Explorer US English Web edition exists; the layout reference is the
released JE-3600A EU English Web edition (`manual_sources/JE-3600A/EU/en/git-20261005-47a346dc`).

## Rebuild

```sh
PKG=manual_sources/JE-880B/US/en/git-20261027-640e83ca
python3 "$PKG/source/extract_assets.py"
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output tmp/je880b-us/en
python3 -m sphinx -n -W --keep-going -b html tmp/je880b-us/en tmp/je880b-us-site
python3 -m unittest tests.test_explorer300_us_en_web
```

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; the only
Feishu calls were read-only downloads. No phase2 or print target is registered and no shared renderer,
component, contract or workflow changed. Release follows the Git-only transaction
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction))
only after the operator accepts the renders and says 「上线提交发布」.
