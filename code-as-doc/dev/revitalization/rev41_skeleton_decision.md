# REV-41：骨架库设计的操作者决定（修改 + 暂缓）

Status: active · Owner: 夏冰 · Created: 2026-10-12

决定：**修改 + 暂缓**。已建成的骨架单元保留并维护；骨架的作用从"扩大网页覆盖"收窄为原生转换做不到的几类场景；
新一轮骨架拓展（REV-42、REV-43、Milestone M 的 R4a–R6）暂缓，满足 §4 任一重启条件后由操作者复评。

来源：2026-10-12 会话中，Claude 就"何时开始新一轮骨架模板拓展、现在做还有没有意义"做了评估（§2–§3），
操作者原话「好，写成 REV-41 决定记录开 PR」。本文随实施 PR 合入即决定在册；
[台账 REV-41](../manual_revitalization_execution.md#rev-41) 合入前为 verifying，合入后翻 done。
本决定不改代码、配置、源表、资产或已发布产物。

## 1. 决定内容

| 对象 | 决定 |
|---|---|
| [骨架库设计](../../architecture/Product_Skeleton_Library_Design.md)（Phase B，2026-08-20 起待批） | 修改：三层模型（Blueprint / Product Manual Plan / Resolved Manifest）、稳定 `slot_id` 和 generate-then-verify 作为现行机制保留；"用骨架扩大覆盖、语料 58/58 重建、`page_registry` 成为唯一组合权威"不再是当前目标，改为满足 §4 条件后的候选目标 |
| [需求文档](../../architecture/product_skeleton_library_requirements.md) | 不再推进定稿；剩余退出目标随本决定暂缓 |
| 已建成的骨架单元 `bp-intl`、`bp-jp`、`charger-intl`、`solar-intl` | 保留：在用目标照常构建、修订和维护，相关测试继续作为回归护栏 |
| REV-42：便携电源 MAIN@INTL 骨架（[PR #1101](https://github.com/Bingboom/auto-manual/pull/1101)） | 暂缓；PR 已于 2026-10-13 关闭（§5），分支 `feat/main-intl-web-skeleton` 保留，作为 T1 的参考 |
| REV-43：按清单扩大骨架覆盖 | 暂缓 |
| Milestone M R4a–R6（原 M0–M9 铺开积压） | 暂缓，期间不开工 |
| [Workstream M](../../optimization_project.md)（`page_registry` 唯一组合权威） | next → deferred |
| 系统建设页"骨架"线 | later → deferred（后置 · 按需），文案同步 |

## 2. 依据（2026-10-12 实测，主线 `024bb142`）

1. **网页覆盖已由原生转换路线承担。** RTD 部署回执（`https://ht-doc.readthedocs.io/manual-deployment.json`，
   workspace revision `a5f2952b`）列出 36 本（型号 × 区域）、138 个语言版。清单出自骨架家族的有 12 本：
   JBP-2000B 欧规、JBP-3600A 欧规、6 个充电器、4 个太阳能板，其中 8 本只有英文。19 本便携电源没有一本走骨架。
2. **已有骨架的电池包，新线也没有走骨架。** JBP-1000B-SIL 美规
   （[#1459](https://github.com/Bingboom/auto-manual/pull/1459)）、JBP-1000B-WH 日规
   （[#1462](https://github.com/Bingboom/auto-manual/pull/1462)、[#1466](https://github.com/Bingboom/auto-manual/pull/1466)）、
   JBP-5000A 日规（[#1487](https://github.com/Bingboom/auto-manual/pull/1487)）都是"已批准印刷 PDF → 冻结原生网页包"。
   三个包的 README 都写明不写 phase2、Base 或队列，内容基于共享的 Manual IR 与 ComponentSpec 生成。
   书已经印出来时，原生转换比"录结构化数据 + 写槽位模板"便宜，也更忠实于原书。
3. **网页侧的复用已下沉到组件层。** [`frozen_web_component_coverage.py`](../../../tools/web/frozen_web_component_coverage.py)
   按 9 个语义章节做共享组件准入（[Web 发布契约 · 共享组件准入](../web_publish_pipeline/shared-component-admission.md)），
   起到了轻量"语义骨架"的作用。
4. **剩余路线成本高，用户看不到收益。**
   - R4a 要冻结并可能改名已提交的评审派生物和已批准版式 pin，按 Milestone M 的 M-pre.3，每一项都要操作者确认；
   - R6 要改 Base schema，并以 T-K4 备份恢复证据为前提；
   - PR #1101 基于 `ff5e3556`，落后主线 380 个提交，与主线试合并有 8 个文件冲突（含 `tools/config_pages.py`
     和 3 个测试文件）。它的目标 JE-2000F/EU/en 已经上线，PR 承诺的正是"已验收的网页输出不变"。
5. **现有骨架健康，保留成本低。** 主线 `024bb142` 上，`manifest_family.py fold` 通过（54 个清单、6 个锚点、
   48 个折叠）；骨架相关的 14 个测试模块共 122 项全部通过（BP 美/欧/日、6 个充电器和 2 个太阳能板目标、
   JBP-3600A、resolver、family）。
6. **"每本复制一份"换了形态。** 冻结包里有 18 个目录带按包定制的脚本：`rebuild.py` 18 份（17 份内容不同），
   另有 `validate_layout.py`、`validate_source.py`、`refresh_manifest.py`、`native.py`，合计约 7,900 行。
   Web 发布契约同一节写明，共享组件修好后不会自动更新已冻结的书，要逐语言重建重发。
   这是 1.0 之后维护成本的主要来源，也是 §4 T3 要观察的对象。

## 3. Milestone M 进度索引

跟踪 PR [#974](https://github.com/Bingboom/auto-manual/pull/974)（draft）停在 2026-08-31，没有回填 R3c，
已于 2026-10-13 关闭；R0–R6 的分解原文留在分支 `docs/milestone-m-scale-proof-checklist` 上。
主线的 [Milestone M 页](../../next_optimization_checklist/milestone-m-skeleton-library.md)已改为 `deferred` 并指向本文，
其 M0–M9 积压本就全部 deferred。本表是主线上的进度索引，截至本决定：

| 项 | 状态 | 证据 |
|---|---|---|
| R0 覆盖重算 | 已合入 | [#975](https://github.com/Bingboom/auto-manual/pull/975) `0ed1871d`；[覆盖报告](../../reviews/skeleton_library_post_s6_coverage_2026-08.md) |
| R1a / R1b BP@INTL 复用契约 | 已合入 | [#976](https://github.com/Bingboom/auto-manual/pull/976) `bac8c980`；[#977](https://github.com/Bingboom/auto-manual/pull/977) `e59a8eb7`；[#978](https://github.com/Bingboom/auto-manual/pull/978) `a7812022` |
| R2 JBP-2000B 欧规六语 | 已合入 | [#981](https://github.com/Bingboom/auto-manual/pull/981) `c8fa6d00`；[原生验收](../../reviews/jbp2000b_eu_r2_native_validation_2026-08.md) |
| R3a / R3b BP@JP 单元 | 已合入 | [#982](https://github.com/Bingboom/auto-manual/pull/982) `76a98ac5`；[#983](https://github.com/Bingboom/auto-manual/pull/983) `57e94c25` |
| R3c JBP-2000B 日规 | 2026-09-05 合入；原生工程验收完成，产品/法务/资产放行仍记为显式债务，版式仍为 candidate | [#1029](https://github.com/Bingboom/auto-manual/pull/1029) `24a10e9f`；[原生验收](../../reviews/bp_jp_r3c_native_validation_2026-09.md) |
| R4a–R6 | 暂缓（本决定） | — |

## 4. 重启条件

任一条件满足时，由操作者复评；不按日期。

| 编号 | 条件 | 原生转换为什么不够 | 复评时先做什么 |
|---|---|---|---|
| T1 | 新品在没有已批准印刷稿时就需要说明书 | 原生转换必须以已批准 PDF 为权威源 | 在对应品类的骨架单元上起草；便携电源以 PR #1101 的设计为参考重做基线 |
| T2 | REV-26 决定扩大印刷排版（IDML）或多格式交付 | 原生包只出网页 | 按 REV-20/26 选定的代表产品族确定骨架范围 |
| T3 | 1.0 基线之后，修订数据显示同一处修正反复要改多本 | 共享组件更新不会自动进入已冻结的书 | 先抽共享内容模块（如 `battery_long_storage_advisory`）或收拢转换脚本，再判断是否需要页面骨架；数据取 REV-15 影响清单、REV-22 维护指标和知识台账的跨产品比较 |
| T4 | 用原生转换接入一条新线超过约 2 个操作日 | 这是 Milestone M 退出条件和平台路线 Phase 4 的单线成本线 | 对比"骨架 + 数据"的实测接入成本 |

另外，无论是否触发，[D23](../machine_readable_knowledge_governance.md) 的 1.0 基线重发完成后复评一次。

## 5. 后续事项

- PR #1101：已定。2026-10-13 按操作者原话「#1101 关掉」关闭；分支 `feat/main-intl-web-skeleton` 保留，作为 T1 的参考。
- PR #974：已定。2026-10-13 按操作者原话「#974 也关掉」关闭，以本文 §3 为主线上的进度索引；分支未删，R0–R6 分解原文可供重启时参考。
- [MA-023](../merge_authorizations.md)（待操作者定）：仍为"生效"，范围是 #974 的 R0–R6 清单，允许其中 PR 全绿即合。
  #974 已关闭、R4a–R6 暂缓，已没有可合入的对象；是否撤销，要有操作者原话后再改登记表。
- Milestone M 清单页：[PR #1509](https://github.com/Bingboom/auto-manual/pull/1509) 拆页合入后，本 PR 把
  [Milestone M 页](../../next_optimization_checklist/milestone-m-skeleton-library.md)的状态改为 `deferred` 并指向本文。

## 6. 同步改动与回退

本 PR 同步更新：台账 REV-41（verifying）、REV-42/43（deferred）、范围调整表和续接点；
系统建设页的骨架线和"产品骨架"条目；Milestone M 清单页和 `optimization_project.md` Workstream M 的状态；
设计和需求文档头；用户指南里系统建设页的重点顺序。

回退：revert 本 PR，REV-41–43 恢复 planned，各文档恢复原状。
