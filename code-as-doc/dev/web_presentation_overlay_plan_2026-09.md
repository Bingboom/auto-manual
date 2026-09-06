# Web Presentation 分层继承与目标 Overlay 计划（第 6 刀）

日期：2026-09-05
分支：`feat/web-presentation-overlays`
基线：`4da3121a`（JE-1000F/EU 五语含字整图 5B 已合入）

## 目标

把当前单体 `web_manual.json` 拆为三个有明确所有权的层：

1. shared base：跨产品复用的 Web profile 与原生语义组件合同；
2. skeleton profile：同一页面骨架的 Overview、Operation、App、Reference Figure
   识别和组版参数；
3. target overlay：只声明 `(model, region)`、选用的 skeleton、能力授权、必需图
   coverage 与真正的目标差异。

生产整本 IR 必须冻结已经按目标解析的最终合同。冷重放只消费 IR 内合同和打包
资产，不重新读取分层配置。新目标若沿用骨架，只需增加一个小型 overlay；若只改
一个带稳定 `id` 的组件项，只提交该项差异，不复制整张 figures/views 列表。

这里同时登记并封口一项资产技术债：Overview、Operation、Charging 的最终网页图，
不得以“无字底图 + 本地化 HTML 文字/引线”冒充完成态。需要原图文字或引线的槽位
统一使用含完整文字与引线的 `finished-panel` / `approved-composite` 成品整图；
`editable-fallback` 只允许留在 LCD Mode 等明确排除在成品图清单外的原生语义组件。
JE-1000F/EU 的 `it` 与另外四种语言受同一 11 槽位覆盖闸门约束。

## 成品图债务台账

`web_figure_coverage` 对四个真实代表包的复核结果如下。这里的“债务”只统计
Overview、Operation、Charging 中本应保留源文档文字与引线的图示；LCD Mode 的
原生 HTML 表格不在这笔债内。

| 目标 | 已完成 | 待清零债务 |
| --- | --- | --- |
| `JE-1000F/EU`（EN/FR/ES/DE/IT） | 55 `approved-composite` | 0；另有 5 个 LCD Mode 原生组件，明确排除 |
| `JE-1000F/US`（本次真实 EN 包） | 8 `approved-composite` | 3 个 Charging 槽位仍为 `editable-fallback`：AC wall、solar direct、solar adapter |
| `JE-3000C/KR` | 0 | 9 个 `missing`：Overview 2、Operation 4、Charging 3 |
| `JBP-2000B/JP` | 当前骨架不声明这三类图槽位 | 不能据此声称已有成品图能力；后续若开启 figures，必须先声明并通过 coverage |

统一收口规则：任何目标一旦开启 Overview、Operation 或 Charging 成品图能力，
target overlay 必须声明其 locale 与完整 required slots，最终只接受
`finished-panel` / `approved-composite`。第 7 刀增加新目标反回退入口闸门，并将上表
做成只能下降、不能新增的债务 ratchet；现有 US/KR 条目需在取得各自权威源图后用
含完整文字与引线的整图清零，不能用 HTML 文字/引线重绘销账。

## 发现与基线

- 当前 `docs/renderers/contracts/web_manual.json` 同时保存 shared profile、通用表格
  组件、JE-1000F 五面板 Operation 几何、App/Charging 规则、目标白名单和 EU 必需
  图闸门。文件规范化 JSON SHA-256 为
  `6684e62c3637c60d728b7779b2b36062626899f8e19bc5c502901662f3c250d7`。
- `load_web_manual_contract()` 只读这一文件；`load_web_document()` 将整个全局合同
  写进每本 IR，尚未冻结“该目标实际生效的层”。
- `overview_component_instances.json` 已有目标实例和 `extends`。其 resolver 已支持
  递归字典合并、稳定 `id` 列表局部覆盖和循环拒绝；Web 当前没有再写死
  `product_overview.instance_id`，但 `_transform_product_overview()` 仍保留读取该旧
  字段的兼容口，允许未来误把实例重新固定到全局合同。
- `figure_targets` 与 `preface.targets` 仍是单体合同中的能力白名单。它们不是可复用
  组件本身，而是目标是否可启用高级图文/旧兼容 adapter 的授权。
- 基线聚焦测试：
  `python -m unittest tests.test_web_presentation tests.test_component_spec_overview tests.test_web_document_ir tests.test_web_figure_coverage`
  共 82 项通过。

## 分层合同

入口 `web_manual.json` 只保留栈描述：shared base 文件、可选 skeleton profile
注册表、兼容 profile 和 target overlay 文件清单。每个 layer 有独立 schema 与稳定
ID；所有相对路径必须留在合同目录内。

解析顺序固定为：

`shared base → selected skeleton profile → target contract_overrides → derived grants`

覆盖规则固定为：

- mapping 递归合并；
- 两边均为含唯一稳定 `id` 的 mapping 列表时按 `id` 合并并保持基准顺序；
- 普通列表明确整表覆盖；
- 不允许重复 target、未知 skeleton、坏 schema、路径逃逸或歧义匹配。

目标 overlay 不复制 `figure_targets` / `preface.targets`。resolver 根据 capabilities
派生兼容字段，并把 coverage 声明绑定到 overlay 自己的 target，防止另一个目标借用。

## 实施阶段

### 1. 失败优先安全网

- 新增分层 loader 测试：真实 US/EU 共用同一 skeleton、目标授权隔离、未知目标不
  获得高级图授权、按 `id` 局部覆盖、普通列表整表覆盖，以及所有 fail-closed 条件。
- 固定默认兼容 materialization 与拆分前合同的语义摘要，证明纯拆分没有悄悄改变
  已批准参数。
- 增加 IR 测试，证明写入的是单一目标的 resolved contract，而不是全局目标目录。
- 增加 Overview 回归，证明 Web 始终按实际 `(model, region)` 解析实例，合同内陈旧
  `instance_id` 不能把另一个目标的几何套进来。

### 2. 分层解析器与合同机械拆分

- 新增聚焦的 `tools/web_presentation_contract.py`，让 `web_presentation.py` 继续作为
  兼容 facade，不扩大用户 CLI。
- 把通用组件移入 shared base，把 Overview/Operation/App/Reference 配置移入同一
  skeleton profile，把 US/EU 目标授权和 EU required-slot policy 移入小 overlay。
- 保留无 target 调用的兼容 materialization；实际生产路径始终传入 model/region。

### 3. 生产接线与文档

- `load_web_document()` 按 materialized target 加载最终合同，并在 IR metadata 中记录
  base/profile/overlay 的稳定 ID。
- `transform_web_fragment()` 在没有显式合同的独立调用中也按传入 target 加载；冷
  重放继续只使用 IR 内的 resolved contract。
- 更新组件定义、构建流程、orchestration map、优化日志和操作文档。

### 4. 验收梯

1. touched-file Ruff 与分层/Overview/IR 聚焦测试；
2. 完整 `python -m unittest`；
3. 全仓 Ruff、mypy `tools/utils`、62 个 maintainability guardrails、文档链接；
4. fixture-backed JE-1000F/US check；
5. JE-1000F/US、JE-1000F/EU、JE-3000C/KR、JBP-2000B/JP 代表包构建与禁读
   RST/CSV 冷重放；
6. US/EU 桌面与 390 px Web 回归，确认 5B 的 55 张整图、Warranty 数字组件和原生
   HTML 表格无变化。

## 第 6 刀验收记录

- 分层/IR/Overview 聚焦测试 95/95；全部 Web + ComponentSpec 测试 232/232；完整
  单元测试 3798 通过、22 跳过。
- 全仓 Ruff、mypy `tools/utils`、62 个 maintainability guardrails、1716 条文档链接
  和 fixture-backed JE-1000F/US `check` 均通过。
- US 17 页、EU 76 页、KR 16 页、JBP-JP 12 页均在禁止读取 `.rst/.csv` 后完成
  source-free 冷重放；四本 IR 分别冻结正确的 target overlay。
- US/EU 分别对同一 IR 使用拆分前单体合同与拆分后目标合同重放，17/17 与 76/76
  页面片段逐字节相同。
- EU 五语仍为 55 个 `approved-composite` + 5 个明确排除的 LCD Mode 原生组件；
  意大利语 11/11 成品整图。RTD 等价 Sphinx 构建以 `-W` 通过；IT AC Output 在
  1280 px 与 390 px 下均显示 1264 x 896 成品整图、隐藏 HTML fallback，页面横向
  overflow 为 0。

## 非目标

- 不改源 PDF/AI/55 张已批准整图，不重算 hash 以放行漂移；
- 不截图化 Specifications、Warranty、LCD、Troubleshooting 或 Symbols；
- 不改 review RST、线上 Base/F6、workflow、依赖、公开 CLI、Base schema 或 IDML
  approved reference layout；
- 不在本刀退役旧 DOM adapter；其删除与反型号专属 Python/CSS、四端整本验收属于
  第 7 刀。
