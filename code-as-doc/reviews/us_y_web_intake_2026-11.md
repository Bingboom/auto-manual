# 五份美规完整说明书：Git-only 发布记录（2026-11-12）

Status: active

## 本次发布范围

操作者指令：「已完成的先推送上去发布」。按 [MA-432](../dev/merge_authorizations.md) 执行，只发布下列五份完整 US/en 候选；其余五份未完成稿保留本地，不进入此次发布快照或生产站点。

## 来源与批准边界

原始英文附件及完整源包按 SHA-256 冻结，合计 28 个物理页。候选采用原生正文及共享组件；批准派生版只改变授权/发布元数据，正文、表格、图片和共享样式须保持一致。印刷版版本沿用原稿，未知值不推断。本次记录发布指令和候选哈希，不补造逐张人工像素签字。

采用 [项目定位 §5.1](../architecture/Hello_Docs_Positioning.md#51-网页说明书的三条路线) 的存量 PDF/AI 路线和 [Git-only 发布契约](../dev/web_publish_pipeline/input-paths.md#22-git-only-transaction)：工程源合入并正常镜像后，生成业务面仅 `docs/publish/**` 的发布 PR，再核验 RTD 构建提交及线上内容。本次不创建队列或写线上源表/链接表。

## 已有验证

五份均已逐页核对正文、表格及插图，通过共享样式、组件覆盖、caption/symbol applicability checks (zero applicable rows)、严格 Sphinx、冷回放、篡改拒绝及 1280/390 浏览器核对；213 个候选文件绑定回读一致。

原完整候选代码在 Python 3.12.13 / requirements.lock 环境通过 6257 项单测，0 失败、0 错误，92 项按条件跳过，1160.719 秒；共享样式/来源事实专项 14 项通过。Ruff、文档链接、维护门禁及 Gitleaks 通过。fixture 隔离 build.py check 只作原有美规流水线回归，不替代本批 PDF 正文核查。

附件资源 ID 采用独立字段行的精确规则；正例零发现，12 个凭据/长度/紧凑 JSON 反例产生预期 14 项发现，无目录豁免。

## 当前阶段

当前准备不可变批准发布版本和工程 PR，尚未声称工程合入、生产部署或线上验收。后续分别记录源合入 SHA、镜像 SHA、发布 PR、RTD 构建和线上核验结果。


## Committed candidate inputs

| Model | Material | Candidate | Source SHA-256 |
| --- | --- | --- | --- |
| JA-IB07A-SO | 16-0102-000156 | [source](../../manual_sources/JA-IB07A-SO/US/en/git-20261112-e1f2a5fa-m000156/README.md) | `e1f2a5fad81afdca636bfcf7f619389caf9d367712be208664aa5e85bf2a1ca0` |
| JS-38A | 38-0001-000913 | [source](../../manual_sources/JS-38A/US/en/git-20261112-8a76fee8-m000913/README.md) | `8a76fee8450bd436eabdaae9caa1df1319a13a5d281b4c9557dbc36c2575b518` |
| JS-45A | 38-0001-000912 | [source](../../manual_sources/JS-45A/US/en/git-20261112-2198a1b7-m000912/README.md) | `2198a1b781b9e62748d19e896e1032e3caeedb458b2556c06918ff0087dce7bf` |
| JS-CONNECTION-GUIDE | 38-0001-000716 | [source](../../manual_sources/JS-CONNECTION-GUIDE/US/en/git-20261112-899cb3dd-m000716/README.md) | `899cb3dd395903c4fa41ddbee282e70480e6ce39605107407cb1da295289bece` |
| JS-40A | 38-0001-000717 | [source](../../manual_sources/JS-40A/US/en/git-20261112-95e0f1c8-m000717/README.md) | `95e0f1c8f544920b6709403d5c6e9c82d5779de42a9cbc928d5164f0a80a6047` |

## Approved immutable release inputs

The five operator-authorized copies preserve native pages, original PDFs, all artwork, CSS and all 52 non-IR Web files byte-for-byte. Independent derivation audit verified all 223 frozen bindings; the original candidates remain unchanged. Fresh strict HTML and complete article-text parity passed for each target. No per-image human signature was fabricated.

| Model | Approved source |
| --- | --- |
| JA-IB07A-SO | [source](../../manual_sources/JA-IB07A-SO/US/en/git-20261112-e1f2a5fa-m000156-release/README.md) |
| JS-38A | [source](../../manual_sources/JS-38A/US/en/git-20261112-8a76fee8-m000913-release/README.md) |
| JS-45A | [source](../../manual_sources/JS-45A/US/en/git-20261112-2198a1b7-m000912-release/README.md) |
| JS-CONNECTION-GUIDE | [source](../../manual_sources/JS-CONNECTION-GUIDE/US/en/git-20261112-899cb3dd-m000716-release/README.md) |
| JS-40A | [source](../../manual_sources/JS-40A/US/en/git-20261112-95e0f1c8-m000717-release/README.md) |

Formal release receipts must bind the actual source merge SHA. CI, engineering merge, Hello-Docs release merge, RTD deployment and online verification remain separate facts. The approved package inventories and derivation records are committed here; post-publication receipt authority is the Hello-Docs publish manifest.

## Shipping packaging r2

The five immutable r2 versions below retain the original native pages, PDFs, tables, artwork, CSS and Markdown. Five non-serving shared-style audit JSON files are retained byte-identically in source evidence, outside the locale delivery roots. The current assembler copied all 52 serving files with an exact inventory match; no shared tool or receipt guard was weakened. The already committed v1 snapshots remain preserved. r2 has 228 frozen file bindings; the registry contains 240 packages with zero new shared-input drift.

| Model | Selected shipping source |
| --- | --- |
| JA-IB07A-SO | [source](../../manual_sources/JA-IB07A-SO/US/en/git-20261112-e1f2a5fa-m000156-release-r2/README.md) |
| JS-38A | [source](../../manual_sources/JS-38A/US/en/git-20261112-8a76fee8-m000913-release-r2/README.md) |
| JS-45A | [source](../../manual_sources/JS-45A/US/en/git-20261112-2198a1b7-m000912-release-r2/README.md) |
| JS-CONNECTION-GUIDE | [source](../../manual_sources/JS-CONNECTION-GUIDE/US/en/git-20261112-899cb3dd-m000716-release-r2/README.md) |
| JS-40A | [source](../../manual_sources/JS-40A/US/en/git-20261112-95e0f1c8-m000717-release-r2/README.md) |

Independent r2 packaging review verifies exact candidate/v1/r2 body and asset continuity and source-inventory closure. US regional fresh-component admission is not applicable in the current implementation; caption-frame and symbol-row applicable counts are zero. Shared styles and native component coverage are checked separately. Formal evidence still requires the actual merged engineering SHA.
