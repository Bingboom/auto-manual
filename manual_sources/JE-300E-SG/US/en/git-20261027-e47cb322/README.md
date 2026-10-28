# JE-300E-SG / US / English — Git-only Web candidate

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」.
This package converts the English single-language manual of the Jackery Explorer 300 (model JE-300E-SG)
from the 发布文档管理 Base row `reczz28SPRx9oxZE` (material 16-0102-000184, project HTE147). Route
`JE-300E-SG/US/en/md`, `legacy_default` (no US Web edition exists for this model).

**Status: `operator-approved-git-only-release`.** On 2026-10-28 the operator confirmed 「上线提交发布：JE-300C、
JE-300E、JE-300E-SG、JE-880B；授权合入 #1631 及其 Hello-Docs 发布 PR」 under MA-365
(「授权全部合入上线 上线之后 我再一个个核对版面」). `source/approval.json` binds that acceptance to these exact
source inputs and the IR is publication-eligible; the operator checks the layout on the live page after
release. The default layout decisions are listed in [`audit/review.zh.md`](audit/review.zh.md).

## Source authority

- `original.pdf`: the row's 「单语言说明书」 English PDF, byte-exact (SHA-256 `e47cb322…`, 17 pages,
  130 × 185 mm). Every glyph is outlined, so the PDF has no text layer.
- Print master (「查找引用」): `16-0102-000184 HTE147300A-USCA-JAK 说明书 RoHS REACH_q.pdf` (44 pages: the full
  print artboard plus the booklet pages; title block HTE147300A-US-JAK 说明书 / V0.1 / 2026-3-13). Its name,
  size and SHA-256 are recorded in `source_manifest.json:print_master`; it is not archived here.
- Identity (record id, material number, project, SKUs) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

`source/intake.py` holds the English copy, transcribed line by line from 300 dpi renders of the named
physical pages and kept as printed (print markup: bold, subscript, line break). It builds shared flow and
shared components only (`source/kit.py`); `source_manifest.json:component_map` maps every printed block.
The cover (p1) and contents (p3) are not Web content. The body matches the JE-300E US candidate
(`manual_sources/JE-300E/US/en/git-20261027-04bd8b90`) except the model number and the fourth inbox card
("Doucuments", kept as printed). The layout reference is the released JE-300E EU English Web edition (`data/manual_sources/JE-300E/EU/en/git-20261016-50b910fd`), which has the same
chapter set and components.

## Artwork

Inventory first (Web artwork reuse order):

- **Symbols**: each of the 10 rows is compared with every shared variant of its semantic family using the
  symbol admission's fixed comparison, and all 10 reuse a shared symbol byte for byte. The plain warning
  triangle and do-not-dismantle rows use `warning/outline-triangle-dark-hte162` and
  `do-not-dismantle/screwdriver-prohibited-dark-hte147`, added by PR #1632 (operator 「同意」, 2026-10-28);
  the latter is this JE-300E print's own native paths.
- **LCD glyphs**: 11 of 12 reuse the JE-300E EU Web glyphs, which pass the fixed comparison against this
  print; the battery-percentage glyph is this print's native vector paths. The FCC mark reuses the
  shared `fcc_mark.svg`.
- **Panels**: the 18 figures are cut from this `original.pdf` at 4x just inside each print panel frame
  (`source/figures.json`); this print's own pixels are used rather than the JE-300E US crops so each
  figure binds to this source's hash.

## Rebuild

```sh
PKG=manual_sources/JE-300E-SG/US/en/git-20261027-e47cb322
python3 "$PKG/source/extract_assets.py"
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output tmp/je300esg-us/en
python3 -m sphinx -n -W --keep-going -b html tmp/je300esg-us/en tmp/je300esg-us-site
python3 -m unittest tests.test_explorer300_us_en_web
```

PyMuPDF 1.28.0 / MuPDF 1.29.0 (`requirements.lock`). To re-freeze: remove `web/en`, rebuild into
`web/en`, then run `source/refresh_manifest.py`.

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; the only
Feishu calls were read-only downloads. No phase2 or print target is registered and no shared renderer,
component, contract or workflow changed. Release follows the Git-only transaction
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction))
only after the operator accepts the renders and says 「上线提交发布」.
