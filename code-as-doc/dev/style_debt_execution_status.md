# 样式契约欠账清算 — 执行状态

> **历史记录（冻结）。** 本页只保存 2026-08-05 完成的上一轮样式债清算、批准
> reference-layout 与 production 复建证据，不再承担当前欠账或 PR 进度账本。当前
> Workstream X 的范围、串行 PR 1–9、Submitted/Complete checklist 和最终验收统一
> 维护在
> [`style_component_contract_v2_plan.md`](style_component_contract_v2_plan.md)。
> 新增组件、状态定义和四端视觉规则只更新
> [`STYLE_DEFINITION.md`](../../docs/renderers/contracts/STYLE_DEFINITION.md)。

集成分支 `fix/idml-style-contract-debt`（接力基线 `789ae3e4`）。原始权威清单来自提交 `1242be91` 的 `docs/renderers/contracts/STYLE_DEBT.md`：26 个记录项，其中 16 条进入本轮，10 条归口长期维护。

**原始排期的 16 条已全部完成实现，并在 `manual_style.yaml` 中改为 `status: aligned`、`debt: []`。** 当前仍保留原清单中的十条长期项：9 条 `partial`，以及 `HB-TABLE-LCD-ICON` 的一条已批准参考档说明。31 条语义的正式四渲染器定义见 [`STYLE_DEFINITION.md`](../../docs/renderers/contracts/STYLE_DEFINITION.md)；最终全量验证、production IDML 复建和 reference pin 重绑结果记录在本页第 7 节。

---

## 1. 本轮完成范围

| 分组 | 已完成的语义 | 验收合同 |
|---|---|---|
| 显式语义 | `HB-SAFETY-DANGER`、`HB-WARRANTY-LEAD`、`HB-WARRANTY-SECTION`、`HB-WARRANTY-YEARS`、`HB-TABLE-AUTO-RESUME` | danger 保留独立 variant；Warranty 共享模板带显式 container 语义；Auto Resume 输出独立 table role |
| 标题与列表 | `HB-TITLE-L1`、`HB-TITLE-L2`、`HB-TITLE-L3`、`HB-TYPE-LIST` | H1 使用共享高度；L2/L3 keep-with-next 由 needspace token 推导；FR/ES list/sublist 使用语言 typed style |
| 表格与 callout | `HB-TABLE-TROUBLESHOOTING`、`HB-TABLE-SPEC`、`HB-CALLOUT-STRIP`、`HB-SAFETY-WARNING` | 行高、线宽、面板下限、bullet 悬挂结构、安全图标列均由共享 token 控制 |
| Symbols 与 LCD Mode | `HB-TABLE-SYMBOL-SIGNAL`、`HB-TABLE-SYMBOL-ICON`、`HB-TABLE-LCD-MODE` | Symbols 页面可见常量进入 token；LCD Mode 的批准 EN/FR/ES 几何、动态语言几何和 fallback 全部走 `layout_params.csv` |

`HB-SAFETY-DANGER` 的美术资产边界不变：LaTeX 与 IDML 仍共用现有 warning lockup 资产；本轮修复的是语义降级，不伪造新的 DANGER 美术。

## 2. #885 结论：不能按当前方向合入

| PR | 内容 | 当前结论 |
|---|---|---|
| [#885](https://github.com/Bingboom/auto-manual/pull/885) | 向共享 manifest 补回目录页与封底 | 不是批准版式的装配路径；`manifest-regenerate-diff` 与 `unit` 当前失败，不应直接合入 |

8/1 批准的 52 页结构已经保存在冻结 review derivative：`docs/_review/JE-1000F/US/index.rst`。它同时满足：

- `00_toc.rst` 在前言之后；
- 法语段仍从 `p20_...` 开始；
- `99_back_cover.rst` 位于末尾。

实际用批准装配路由复现：

```bash
python3 build.py idml \
  --config configs/config.us.yaml \
  --model JE-1000F \
  --region US \
  --source review-asis \
  --idml-mode flow \
  --no-clean
```

结果为 `pages=52`、`blocks=570`、`skipped_raw=0`；`manual.ir.json` 的 52 个页面 ordinal 与批准 reference plan 逐项一致。最终内容哈希为 `ced5ae20…`，并已通过显式 content-approval 路由重新批准；页面集合、ordinal、语言映射、物理 composition 和 reference PDF 均未改变。

因此问题不是“向共享 manifest 补两页”，而是 production IDML 必须明确使用冻结 review source（或建立等价的批准装配路由）。#885 应关闭或按这个路由结论重做，不能把共享 manifest 当作 8/1 基线来源。

## 3. reference pin 处理

`tools/check_reference_layout_pins.py` 校验两个合同 pin，任一漂移即红：

| pin | 来源 | 谁会碰 |
|---|---|---|
| `style_contract_sha256` | `docs/renderers/contracts/manual_style.yaml` | **每条债的销账**（改 `debt` / `status` 字段） |
| `layout_params_sha256` | `data/layout_params.csv` | P1/P2 token 化与 LCD Mode 专属几何 |

操作者已经批准“重新批准/重绑 content hash”。本轮先用最终 `manual.ir.json` 证明 source refs、语言映射、composition map、物理页数和 `skipped_raw` 不漂移，再通过 `tools/reference_layout_rebind.py --approve-content-change ... --write` 原子重绑。普通 rebind 仍默认拒绝 content hash 改变；显式批准要求批准人、RFC3339 时间和审查方法三项 metadata 齐全。

最终批准 identity 已迁移为 v2 分层结构：

- content（硬门禁）：`ced5ae20f48a0dc438d638ad10e0ae37c0574b00409e790ac2df1db1fcd66fc0`；
- assembly（硬门禁）：`1217da8e34c3317196ec7f1e288106dd7728d82fe97aa896ea8bcda670ba6a05`；
- style contract（硬门禁）：`885b936fa2569bf018d495e5af0527f9928bbf79e2ae47c9eaaae3bee7f94da7`；
- layout params（硬门禁）：`912db2f5da32326993cb00fffedfbddba1b44abd33098582fc584e51916c2d2d`；
- snapshot provenance（仅追溯）：`2d77eff60a95633f9b828aea62d788d38d514f8825773c1e5be1286dc1512d33`。

v2 的 assembly hash 覆盖 source 顺序、语言、页面角色和 composition map；
`allowed_unclassified_source_refs=[]`，因此批准装配不会静默退回普通 prose。

批准记录为 `approved_by: 唐夏冰`、`approved_at: 2026-08-05T15:43:17Z`，method 明确记录了 52-source / 58-page parity 验证和 composition map unchanged。`tools/check_reference_layout_pins.py` 已通过。

## 4. production 装配路由

操作者选择“建立等价批准装配路由”。实现后的规则是：

- 已有批准 reference target 的 `build.py idml --source auto` 自动解析为 `review-asis`；
- 显式 `--source runtime`、`review`、`review-asis` 保持调用者选择；
- 没有批准 reference 的 target 继续使用 runtime；
- `--source auto` 的行为已同步到 README 和操作指南，并有 dispatch 回归测试。

因此 production 不需要操作者每次手写 `--source review-asis`，同时不会把该规则扩散到未批准 target。

## 5. 继续归口的十条

- 版式专题 3 条：`HB-SPECIAL-FCC`、`HB-SPECIAL-INBOX`、`HB-SPECIAL-OVERVIEW`；
- 样式借用 3 条：`HB-TYPE-LEAD`、`HB-TYPE-FOOTER`、`HB-TYPE-PAGE-NUMBER`；
- 共享页计划 3 条：`HB-PAGE-STANDARD`、`HB-PAGE-NO-FOOTER`、`HB-PAGE-COVER`；
- 记录项 1 条：`HB-TABLE-LCD-ICON` 继续说明“批准 reference profile 拥有型号特定行高”，其 `status` 仍为 `aligned`，不是本轮缺陷。

## 6. 明确非目标

- 不修改或合入 PR #885；
- 不修改 reference PDF 或 composition map；
- 不处理上述十条长期项；
- 不删除 `docs/_review`、phase2 附件或用户构建产物；
- `sync-data` 0 行覆盖风险仍是独立 follow-up，不夹带进本分支。

## 7. 最终验证与 production 复建

验证梯全部通过：

| 验证 | 结果 |
|---|---|
| `python3 -m ruff check build.py integrations tools tests scripts` | 通过 |
| 直接改动覆盖的定向 unittest | 320 项通过，5 项跳过 |
| `python3 -m unittest` | 2716 项通过，5 项跳过 |
| `python3 tools/check_maintainability_guardrails.py` | 44 个热点全部通过；0 个新增语言常量 |
| `python3 tools/check_doc_link_integrity.py` | 116 份 Markdown、1497 条链接、0 断链 |
| `python3 tools/check_reference_layout_pins.py` | 1 份批准合同通过 |

最终 production 入口使用 fixture snapshot 运行：

```bash
python3 build.py idml \
  --config configs/config.us.yaml \
  --model JE-1000F \
  --region US \
  --source auto \
  --data-root tests/fixtures/phase2 \
  --idml-mode both \
  --no-clean
```

`auto` 实际解析为 `review-asis`；flow 与 production IDML 均成功。批准 page plan 为 physical `58`、matched `52/52`，最终 IR 为 `pages=52`、`blocks=570`、`skipped_raw=0`。HEAD 旧 plan 与重绑后 plan 的 source refs、语言、composition map、reference PDF 和 `idml_contract` 块逐项相同，当前 plan 的四个 source identity 与最终 IR 全部匹配。

构建仍报告两个 Product Overview placeholder 使用 unclassified prose fallback（法语、西班牙语各一页）；这是非阻断分类警告，批准 page plan 仍为 52/52、没有 raw block 被跳过，也不属于本轮 16 条样式契约欠账。

## 8. 顺带发现的两个缺陷（未修）

- **`sync-data` 会把非空镜像覆盖成 0 行**。实测把 `FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID` 指到 `02_主数据_产品信息表`（只有一个「是否支持加电包」字段）时，输出 `model_capabilities: rows=0 changed=yes`，`data/model_capabilities.csv` 被写成只剩表头。能力门的数据源一旦被清空，下一次构建会把所有带 `capability:` 条件的小节全裁掉，而且不报错。建议：拒绝把非空镜像覆盖成 0 行。正确坐标是 `02_主数据_Document_key`（`tbltnkDIdwiDOP7d` / `vewi97AFwi`），九个 checkbox 对应 CSV 九列。
- **`tools/idml/flow_idml.py:617` 的 `_fence_style()` 全仓库无调用者**，是死代码，里面还有第二处 `danger → warning` 别名。

## 9. 已核实、不构成问题的三件事

调查过程中我曾误判，这里记下结论以免重复：

- **能力门裁掉 `07_extra_battery.rst` 是正确的。** manifest 里三条都带 `capability: 加电包扩容`，JE-1000F 该项为 FALSE，产品本身不支持加电包，手册从未有这一页。pin 里也没有它。
- **`加电包扩容` / `并机/扩展` 两列全型号 FALSE 是权威事实，不是镜像漂移。** sync 下来的 `model_capabilities.csv` 与仓库那份 sha 完全一致（`cdf29b10…`，30 行）。
- **参考版式 pin 不是过期。** `approval` 字段：`approved_by: 唐夏冰`、`approved_at: 2026-07-31`、`method: 按现网内容重批契约; includes the merge-splice guard and p26 grid repair`——即 8/1 那次 1.7 publish 的基线。页面装配来自冻结 review derivative；当前剩余差异是 content hash，不是共享 manifest 缺页，也不是 pin 陈旧。
