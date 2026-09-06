# ManualIR 最终入口闸门与旧 DOM 退役计划（第 7 刀）

日期：2026-09-05
分支：`refactor/web-ir-final-gates`
基线：`e67e9be3`（第 6 刀 target-layered Web presentation 已合入）

## 目标

完成七刀跨渲染器 IR 收口的最后一刀：把已经存在的复用原则变成新目标无法绕过
的入口闸门，并让新生成的 `whole-document-components/v1` 文档在冷重放时不再进入
旧 DOM 语义识别链。

Overview、Operation、Charging 的最终网页图统一只接受含完整文字与引线的
`finished-panel` / `approved-composite` 成品整图。无字底图加 HTML/SVG 本地化文字
或引线仍是 `editable-fallback`，不能销账。LCD Mode 的原生 HTML 表格是明确排除
项，不属于这笔成品图债务。

## Discovery 结论

1. `component_registry.yaml` 当前登记 16 个共享 ComponentSpec 类型，每个类型均声明
   Web、LaTeX、IDML、Word 四端 adapter；真实整本 v2 IR 已把这些实例按文档顺序
   冻结，冷重放可直接 dispatch。
2. 第 6 刀仅对 JE-1000F/EU 声明了严格 figure coverage。JE-1000F/US 的
   `capabilities.figures=true` 尚无 coverage 声明，JE-3000C/KR 则以
   `figures=false` 保留可见债务，因此新目标仍能绕开完整 locale/slot 声明。
3. 真实包覆盖账如下：
   - JE-1000F/EU：五语共 55 个 approved composites，成品图债务 0；另有五个
     LCD Mode 原生表格，不计债；意大利语为 11/11 成品整图。
   - JE-1000F/US：EN/FR/ES 各有 8 个 approved composites；每语 AC wall、
     solar direct、solar adapter 三个 Charging 槽位仍为 editable fallback，
     全目标共 9 个债务。当前单语代表包显示 8 成品 + 3 债务。
   - JE-3000C/KR：Overview 2、Operation 4、Charging 3，共 9 个 missing；
     LCD Mode 原生表格另计为排除项。
   - JBP-2000B/JP：当前 skeleton 未声明上述 figure 槽位，不能据此宣称成品图能力。
4. 共享 Web 实现面（`tools/web_*.py`、`tools/manual_ir/`、
   `tools/component_specs/` 和 Web CSS）当前没有目标型号字符串常量或型号 CSS
   selector，可从零基线直接设硬闸，不需要接受已有代码债。
5. 新整本 v2 replay 仍统一调用 `transform_web_fragment()`。16 类已嵌入组件靠
   `resolved_component_ids` / `embedded_components_complete` 跳过旧 projector，
   但这仍让生产重放依赖一条包含旧识别器的兼容入口；Preface inventory 清理和
   Auto Resume 表格装饰是仍需保留的非组件 Web source-normalization。

## 实施阶段

### A. Figure admission 与债务 ratchet

- `figures=true` 的 target overlay 必须声明非空 locale、完整 required slots，且
  `allowed_statuses` 必须恰为 `finished-panel` / `approved-composite`。
- 既有 US/KR 债务进入独立的版本化 baseline，按 target + locale + slot + status
  锁定。未登记的 missing/editable fallback 失败；登记项状态变化但未成为成品也失败。
- 某债务变成成品时，旧 baseline 项必须在同一变更中删除；过期债务登记也失败，
  防止债务清零后再次回退。
- baseline 只能引用已存在 overlay 的 coverage policy，且 locale/slot 必须完全一致。
  新 figure target 默认没有 baseline 例外，因此第一本构建就必须零债通过。
- resolved contract 冻结该目标的严格 policy 与既有债务条目；冷重放不读取 overlay
  或 baseline 文件。

### B. 反型号专属 Python/CSS

- 新增只读 AST/CSS 扫描器，从 target overlay 取得已登记型号，检查共享 Web
  renderer、ManualIR、ComponentSpec 和 Web stylesheet。
- Python 注释不算执行逻辑；字符串常量、分支值、模板常量与 CSS selector/value
  中的型号字面量均失败。
- 将检查接入 `check_maintainability_guardrails.py`，让 CI 真实执行，而不只停留在单测。

### C. 新 v2 replay 退出旧 DOM projector

- 在生产者读源阶段完成 Preface inventory 清理和 Auto Resume 的既有 Web
  normalization，再将结果序列化为 neutral flow/presentation hints。
- `whole-document-components/v1` replay 只做 ComponentSpec dispatch、资产 rebasing、
  hash 校验和静态资产 staging，不再调用 `transform_web_fragment()`。
- 历史 `manual-ir/v1` 与 cut-1 `whole-document-flow/v1` 继续走明确标记的兼容入口，
  不把兼容性删除伪装成架构收口。
- 以 failing double 证明新 v2 冷重放即使旧入口不可调用仍能完成，并保持页面片段
  与第 6 刀基线一致。

### D. 四端与代表语料验收

- 对四个代表包投影全部嵌入 ComponentSpec，逐实例验证 Web/LaTeX/IDML/Word
  adapter binding；组件专项测试执行四端 projection/payload。
- JE-1000F/US、JE-1000F/EU、JE-3000C/KR、JBP-2000B/JP 禁读 RST/CSV 冷重放。
- 对 US/EU 做第 6 刀前后页面片段逐页比较；EU IT 再查 11/11 成品整图、fallback
  隐藏、桌面和 390 px 无横向 overflow。

## 验证梯

1. touched-file Ruff 与 figure/contract/replay/anti-copy 聚焦测试；
2. 全部 Web + ComponentSpec 测试；
3. 完整 `python3 -m unittest`；
4. 全仓 Ruff、mypy `tools/utils`、maintainability 和文档链接；
5. fixture-backed JE-1000F/US `build.py check`；
6. 四个真实包四端 binding、冷重放与 US/EU byte parity；
7. EU RTD/Sphinx `-W`、IT 桌面/移动视觉与成品图覆盖。

## 非目标

- 不把 LCD、Specifications、Warranty、Troubleshooting、Symbols 或其他原生表格截图化；
- 不用 HTML/SVG 文案与引线冒充成品图；
- 不改 frozen artwork 内容，不代替产品/设计审批；
- 不写线上 Base/F6，不改 workflow、依赖、Base schema、公开 CLI 或 approved
  reference-layout；
- 不删除历史 IR 兼容读取，也不删除用户生成的 `_build`、review 或其他 worktree 产物。

## 完成状态（2026-09-05）

- A 已完成：US 9 项 Charging `editable-fallback` 与 KR 9 项 `missing` 写入独立
  ratchet baseline；EU 无例外，IT 的 11 个槽位全部为 `approved-composite`。测试明确
  证明无字底图加 HTML/SVG 文字或引线仍是债务。
- B 已完成：maintainability guardrail 扫描共享 Web/ManualIR/ComponentSpec Python
  的字符串常量和 Web CSS 非注释内容，禁止目标型号字面量。
- C 已完成：新 source-normalized `whole-document-components/v1` replay 不再调用旧
  `transform_web_fragment()`；历史 v1/cut-1 包继续走兼容入口。registry、theme、
  Overview target instance 与 hash 均随包冻结。
- D 已完成：JE-1000F/US、JE-1000F/EU、JE-3000C/KR、JBP-2000B/JP 共 401 个
  ComponentSpec 验证 1604 个 Web/LaTeX/IDML/Word adapter binding，并在禁读
  RST/CSV/renderer contracts、禁用旧 DOM projector 下冷重放。US 49 页与 EU 76 页
  最终 HTML 相对改造前逐字节一致（仅规范化输出目录 file URI）。EU Sphinx `-W`
  通过，IT 11/11 成品整图在桌面与 390 px 均加载、隐藏 fallback 且无横向溢出。
