# Research & Intelligence 项目章程

Status: active · Owner: 夏冰 · Created: 2026-10-22
孵化分支：Bingboom/auto-manual 的 `feat/product-intelligence-demo`

## 定位

Research & Intelligence 是从 Hello-Docs 仓库中孵化的独立研究平台项目。当前分支仅作为
原型开发与迁移过渡环境，最终交付目标是独立仓库。不得将完整研究平台合入
`auto-manual/main`；后续与 Hello-Docs 的集成通过明确的数据契约与适配器实现。

这里的 Hello-Docs 指说明书系统：工程面 Bingboom/auto-manual 和业务面
Bingboom/hello-docs，见[两面图](../../user-guide/two_plane_map.md)。本项目不是
Hello-Docs 的新功能。Hello-Docs 对它来说只是可选的数据来源和集成对象。

## 为什么独立

这个 Demo 最初从 Hello-Docs 的产品知识和 RTD 展示能力延伸出来，所以放在 auto-manual
里。几轮讨论后，它的定位已经变了：

- 不局限于自身产品或竞品分析；
- 以研究问题为中心，不以说明书数据为中心；
- 需要接入 WeKnora 等非结构化知识处理能力；
- 将来有独立的数据模型、研究工作台和业务闭环。

业务边界已经独立，就不再作为 Hello-Docs 的内部功能开发。这次调整不否定之前的工作：
[Bingboom/auto-manual#1585](https://github.com/Bingboom/auto-manual/pull/1585) 已经完成
模块解耦，接下来完成仓库和项目治理层面的解耦。

## 孵化期规则

- `feat/product-intelligence-demo` 不以合入 `auto-manual/main` 为目标。不创建把它
  整体合入 `main` 的 PR。
- 孵化期的 PR 以这个分支为目标，例如 #1585。合入这些 PR 不等于合入 `main`。
- auto-manual 的 `main` 不依赖孵化分支里的任何内容。
- 描述这项工作时，称它为 Research & Intelligence 孵化原型，不称“Hello-Docs 新功能”。
- 新仓库不从这个分支整体推送生成：分支带着 Hello-Docs 的大量代码和历史，整体迁过去
  就失去独立建仓的意义。只迁出下面清单里的独立部分。

## 现有成果的归属

| 部分 | 现在的位置 | 归属 |
| --- | --- | --- |
| 事件库、决策摘要、飞书同步与推送、待发恢复、Markdown 视图 | `tools/intel/`（只依赖标准库和包内模块） | 平台核心，迁出 |
| 核心测试与样例 | `tests/test_intel_*.py`、`tests/fixtures/external_intel/`、`tests/test_external_intel_boundary.py` 中的导入扫描和独立运行 | 迁出 |
| 数据契约 | `external-intel-events/v1`、`external-intel/v1`、决策摘要 `items`、Markdown 视图布局，见[契约](product-intelligence-contract.md) | 迁出，作为对外契约 |
| 运行说明与联调记录 | [操作说明](../../user-guide/hello_auto-doc/product-intelligence-demo.md)的飞书闭环和 Markdown 视图部分、[联调记录](../tests/external_intel_live_integration_2026-10.md) | 迁出 |
| 研究页、产品视角、RTD 接入 | `tools/rtd/` 的研究页文件、`tools/product_knowledge/`、`tools/rtd_portal_assets/` 的研究页资源及其测试 | Hello-Docs 一侧的集成，不属于平台核心；去留见待决策 |
| 与宿主读取器的一致性检查 | `tests/test_external_intel_boundary.py` 中对照 `workspace_snapshot`、`market_policy` 的部分 | 留在 Hello-Docs 一侧，迁出后改为契约测试 |

## 迁移路线

1. [x] 冻结方向：写入本章程。
2. [ ] 完成 #1585：按[联调手册](../tests/external_intel_live_integration_2026-10.md)
   实测读表、人工判断回写、推送和 Wiki，通过后合入孵化分支。
3. [ ] 提取独立模块：新建独立仓库（暂名 `research-intelligence`），迁入上表中“迁出”的
   部分和本章程。只迁文件，不迁本仓库历史；包名和默认状态目录
   `~/.cache/auto-manual/external-intel` 随新仓库改名。
4. [ ] 重新建立接口：需要时，Hello-Docs 通过独立适配器接入平台，只读平台导出的契约
   数据；平台不导入 Hello-Docs 的代码。
5. [ ] 结束孵化：旧分支保留一段时间用于核对，确认迁移完整后归档。

## 待决策

- **数据存放。** 之前定的“事件和判断全部进 Hello-Docs”与新定位冲突。建议事件库和人工
  判断归平台自己的仓库或存储，Hello-Docs 的市场政策记录、产品知识只作可选输入。确认
  之前，孵化期的试运行数据不提交到任何仓库。
- **新仓库。** 名称、可见性、许可证和所有者。
- **研究页和产品视角。** 是作为 Hello-Docs 一侧的适配器保留，还是由平台自己的研究
  工作台取代。
- **WeKnora 等非结构化知识处理。** 接入方式和数据边界，在新仓库里单独设计。
