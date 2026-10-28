# JE-300C / US / English — Git-only Web candidate

Operator instruction, 2026-10-27: 「把这个表中 未转网页版的说明书 走git only进行单语网页文档的转换」.
This package converts the English single-language manual of the Jackery Explorer 300 (model JE-300C)
from the 发布文档管理 Base row `reczz28SPRx9psWa` (material 16-0102-000099, project HTE142). The operator
decided that only 16-0102-000099 gets a Web edition (16-0102-000100 does not). Route `JE-300C/US/en/md`,
`legacy_default` (no US Web edition exists for this model).

**Status: `operator-approved-git-only-release`.** On 2026-10-28 the operator confirmed 「上线提交发布：JE-300C、
JE-300E、JE-300E-SG、JE-880B；授权合入 #1631 及其 Hello-Docs 发布 PR」 under MA-365
(「授权全部合入上线 上线之后 我再一个个核对版面」). `source/approval.json` binds that acceptance to these exact
source inputs and the IR is publication-eligible; the operator checks the layout on the live page after
release. The default layout decisions are listed in [`audit/review.zh.md`](audit/review.zh.md).

## Source authority

- `original.pdf`: the row's English PDF, byte-exact (SHA-256 `a1128b25…`, 18 pages). Outlined, no text layer.
- Print master: `16-0102-000099 说明书A1- HTE142300A-USCA-JAK RoHS REACH Q.pdf` (one artboard, EN/FR/ES);
  name, size and SHA-256 in `source_manifest.json:print_master`, not archived here.
- Identity (record id, material number, project, SKUs) is in `source_manifest.json:document_identity`.
  No Feishu file token is stored.

## Method

The same outlined-PDF method as `manual_sources/JE-300E/US/en/git-20261027-04bd8b90`: `source/intake.py`
holds the line-by-line transcription, built from shared flow and shared components only
(`source_manifest.json:component_map`, no declared exceptions). The cover (p1) and contents (p3) are not
Web content. Source slips are kept as printed (`source_manifest.json:source_concerns`). Layout reference:
the released JE-300E EU English Web edition (`data/manual_sources/JE-300E/EU/en/git-20261016-50b910fd`).

## Artwork

- **Symbols**: each of the 10 rows is compared with every shared variant of its semantic family using the
  symbol admission's fixed comparison, and all 10 reuse a shared symbol byte for byte. The plain warning
  triangle and do-not-dismantle rows use `warning/outline-triangle-dark-hte162` and
  `do-not-dismantle/screwdriver-prohibited-dark-hte147`, added by PR #1632 (operator 「同意」, 2026-10-28);
  the latter is this JE-300E print's own native paths.
- **LCD glyphs**: 10 of 14 reuse the JE-300E EU Web glyphs (fixed comparison against this print); UPS, AC
  wall charging, battery percentage and the two temperature glyphs are this print's native vector paths.
  The FCC mark reuses the shared `fcc_mark.svg`.
- **Panels**: cut from `original.pdf` at 4x just inside each print panel frame (`source/figures.json`).

## Rebuild

```sh
PKG=manual_sources/JE-300C/US/en/git-20261027-a1128b25
python3 "$PKG/source/extract_assets.py"
python3 "$PKG/source/intake.py"
python3 "$PKG/source/refresh_manifest.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$PKG/rebuild.py" --output tmp/je300c-us/en
python3 -m sphinx -n -W --keep-going -b html tmp/je300c-us/en tmp/je300c-us-site
python3 -m unittest tests.test_explorer300_us_en_web
```

## Boundaries

Git-only: no Feishu/Base/source-table, queue, asset-registry, build/link or HTML_link writes; the only
Feishu calls were read-only downloads. No phase2 or print target is registered and no shared renderer,
component, contract or workflow changed. Release follows the Git-only transaction
([web publish pipeline §2.2](../../../../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction))
only after the operator accepts the renders and says 「上线提交发布」.
