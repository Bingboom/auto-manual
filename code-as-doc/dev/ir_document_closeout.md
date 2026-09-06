# 整本公共 IR → Web 收口执行目标

## 目标与边界

以 JBP-2000B / JP / ja 实际构建为验收目标：有序源页只读取、解析一次，
形成 `manual-ir/v1` 整本文档；Web 从该 IR 消费正文、表格、语言和素材引用。
保存 IR 后断开 RST 来源，仍能重放网页。Web 插图使用 PDF 带字整图，
图内日语标注与产品外观文字保留；正文、规格、警告仍是结构化内容。

不延伸至 JE-1000F 原生 IDML 排版、线上 Base 写入、线上发布或其他输出端重构。
公共契约闭环与所有输出端迁移完成分别报告，不把组件投影冒充整本入口。

## 发现与基线

- 起点 `5788b59f`（#1056 已合入）；此前 Web 逐页调用
  `word_bundle_html._convert_rst_fragment_to_html`，没有整本 IR 消费边界。
- 目标由现有 `configs/config.bp-jp.yaml` 和 BP@JP manifest 决定，不新增型号配置。
- 参考为 HTP017 日规《Jackery Battery Pack 2000取扱説明書V2.0-2026-05-28.pdf》，
  12 页，SHA-256 `f7830bf9fb96d9a3e36737bad5196bbfac2d262eaef642f3406fe77eecd02b0b`。
- 2026-09-05 使用仓库 phase2 fixture 跑真实 `build.py md`，失败于 LCD 表：
  加电包有文字定义但不提供独立图标，现契约错误地要求每行恰好一张图。
- 现有 JP 连接/充电素材 recipe 为 IDML 去除标注；Web 需独立的带字导出，
  不能直接复用去字图，也不能重做图内标注布局。

## 执行顺序与退出条件

1. 冻结以上基线；确认 PDF 页面与裁切范围，复用资产提取工具生成带字图。
2. 建立整本源适配器、公共内容树及 Web 消费边界，实际入口迁移到该边界；
   RST 只在源适配阶段读取，输出 `manual.ir.json` 并校验内容/素材哈希。
3. 将 PDF 插图绑定到目标网页；修复本次实际构建暴露的契约问题。
4. 验证序列化重放、缺失/损坏素材及无图标 LCD；保留 JE-1000F US 回归。
5. 完成 lint、完整单测、边界和文档检查、实际 BP JP 与 US 构建；浏览器检查
   日语章节、规格表、带字插图和链接完整性，交付本地可打开网页和可评审 PR。

完成记录必须给出实际输出路径、测试结果、迁移退出的旧路径和剩余解析债务。
不能用“构建成功”替代视觉检查，也不能用 HTML 容器打包宣称所有中立富文本已完成。

## 完成记录（2026-09-05）

本轮整本 Web 消费边界完成，等待 PR 审核。实际路径：

`有序 prepared RST → web_document_source → ManualSource → 公共 assembler →
manual.ir.json → web_document_ir → 既有组件投影 → MyST → Sphinx 网页`。

- Web 的实际页面循环不再调用 `_convert_rst_fragment_to_html`；该兼容函数继续
  服务 Word 与独立片段测试。源页字节只在适配阶段读一次。
- 正文、列表、表格、强调与插图是可遍历的有序内容树，非整页 HTML 字符串。
  页面语言来自已有 assembly planner；不存在按型号硬编码的解析分支。
- 素材解析/复制从重型 Word 入口机械迁到 `document_assets`，两端复用。
  新进程导入 Web 消费者并禁止一切 RST/CSV 文件读取，仍成功重放实际 BP 整本。
- LCD 源生成器在全部独立图标为空时显式声明 `lcd-text-only`；空名称/说明和
  未声明的缺图仍失败，不用虚假占位图补齐。
- 实测 12 个源页、19 张图片，其中 9 组为 PDF 带字整图；浏览器全部加载成功。
  IR 素材位于现有 `assets/` 打包边界，RTD 静态路径可解析。
- JE-1000F US 使用原有 `review-asis` 回归：正文文本与合入前一致，图片 210→210。
- 完整单测 3721 项通过（22 skipped）；Ruff、maintainability、
  BP JP / US `build.py check` 通过。Guardrail 的 6 个 stale baseline 为已有提示。
- 实际输出位于本任务工作树 `.tmp/bp-web-whole/`：`html/` 为网站，
  `docs/_build/JBP-2000B/JP/md/manual.ir.json` 为 IR，`replay/body.html` 为独立重放，
  `acceptance.json` 为机器可读验收记录，`JBP-2000B-JP-web-preview.zip` 为离线站点包。
- 最终 IR 内容 SHA-256：
  `d4439b945c3475db43a3f52349fb047141677a0a014048cbb714f788ac488c40`。

### 已确认的参考 PDF 错误

操作者明确确认结构源正确：**开机按一次，关机长按三秒**。
参考 PDF 第 6 页图内标注相反。Web 的 power 保留完整插图，在提取 recipe 中通过
`swap_pdf_regions` 交换两处原生 PDF 开/关标题，原有时长、产品线稿、引线和机身文字保留。
该操作只适用于白底、等尺寸、不相交且位于裁切内部的区域，冻结源和输出哈希；
最终 PNG 经视觉核验，不修改原 PDF 或结构源。

### 整图与共享组件的边界

- 包装清单复用 `HB-SPECIAL-INBOX`：`box_contents_*` 源页接入既有公共组件，
  编号、卡片、名称及注意事项由组件生成；使用现有单品插图，不使用 PDF 整卡截图。
  recipe 中保留的三张早期整卡候选不再绑定到网页。
- 产品总览、开关机、锁定和充电图由整图承载图内标注。
  manifest 的 `covered_annotations` 以选择器和完整规范化文字绑定覆盖范围；
  构建只移除七块准确匹配的冗余标注，缺失、重复或源文变化均失败。
  同一份正确结构文字保留在图片 alt 与 IR provenance 中，避免失去无障碍说明。
- LCD 功能解释表、注意事项、警告、规格和正文继续是结构内容；
  不因插图带字而移除解释性正文，也不把整个文档栅格化。
- 浏览器已核验共享包装组件 1 个、卡片 3 张、图片 19/19、重复标注退出；
  安全、符号解释、LCD 定义、故障排除、规格、保修的正文与前版一致。

### 剩余边界（不能宣称已完成）

1. 后续第 1 刀已让新整本 Web IR 改用 `manual-ir/v2` 中立 flow/rich-text
   节点；HTML tag 不再是序列化语义权威，历史 `manual-ir/v1` 仍可原样读取和重放。
   为保持 Web 输出稳定，CSS class/style/data 属性暂存于可删除的
   `presentation.html.attributes`。后续第 2 刀又把已注册的 Callout、Spec、FCC、
   Inbox、Overview ComponentSpec 写进整本 IR；其余复杂组件以及 Word、print、
   IDML 全部从整本 IR 消费同一语义实例，仍由第 3–5 刀完成。
2. 源 RST 中仅面向 LaTeX 的宏仍由既有前置选择器排除；原始指令解析/严格诊断
   及旧 prepared-RST→IDML 适配器不是本轮的退出路径。
3. 本地 PDF 裁切已提交 recipe、绑定和图片，但没有登记到线上 Base 或发布站点；
   使用的是已有 fixture 快照，不能把本地试构建标记为线上交付。
4. US `runtime + fixture` 的旧 composite 源哈希已有不匹配；用旧转换器对同一源页
   重放得到完全相同错误（`product-overview.front`），未改冻结哈希来放行。
   本轮回归使用已经冻结的 review-asis 输入，该路径通过。

以上是显式后续边界，不继续追加无结束条件的 Web 小组件批次。

## 后续第 1 刀：ManualIR v2 中立 flow（2026-09-05）

新整本 Web 生产路径现在写出 `manual-ir/v2` 和
`whole-document-flow/v1`。标题层级、段落、列表顺序、链接目标、图片来源与
alt、表格表头及跨行/跨列、锚点和隐藏状态均为中立字段；Web 专属 class、style
和 `data-*` 只在可选 presentation hints 中。删除全部 hints 后仍可重建结构化
HTML，且空页面以空文本 flow root 保持页面/块身份而不产生可见标签。

读取端双版本兼容：已有 v1 文件不升级、不重写、不重算哈希，整本 Web consumer
在内存中适配旧 `document_content`；新生产文件只写 v2 `flow`。素材仍由
`image.source` 汇总并受打包 SHA-256 闸门保护。第 2 刀才会把现有五类
ComponentSpec 直接嵌入整本 IR，因此本节不宣称四端已经共享组件实例。

设计、非目标、逐刀依赖和验收命令见
[`manual_ir_v2_neutral_flow_plan.md`](manual_ir_v2_neutral_flow_plan.md)。
本地验收为聚焦测试 90 项、完整单测 3756 项（19 skipped）、49 页/353 个
flow block/57 个冻结素材；v1/v2 片段、修改前片段和禁读 RST/CSV 的冷重放均
逐字一致（仅比较修改前包时规范化包根 file URI），最终仍为 210 张网页图片。

## 后续第 2 刀：现有 ComponentSpec 嵌入整本 IR（2026-09-05）

新生产路径现在写出 `whole-document-components/v1`，并在 `manual-flow/v2`
中按原始页面、区段和节点顺序嵌入 `component` leaf。ComponentSpec 是组件身份、
variant、本地化 slot、asset role 和 token role 的语义权威；可选 `carrier_flow`
只保留链接、强调、图片属性等尚未完全进入 slot 的中立富文本。未知组件、重复
`source_ref`、嵌套 component carrier、语义与 carrier 不一致均在渲染前失败。

整本 Web replay 直接按 `component_id` 分发五类已注册 adapter，不再重跑
Overview、FCC、Inbox、Spec、Callout 的 DOM source projector；旧 v1 和第 1 刀的
v2 包仍走兼容路径。Inbox 先于 Callout 认领内部 TIP，避免一个源节点生成两个
实例。ComponentSpec asset 与 carrier image 共同进入有序 `asset_refs` 并受包内
SHA-256 闸门保护。其他 renderer 已能按文档顺序取得同一批 ComponentSpec，
但剩余组件及整本消费迁移仍属于第 3–5 刀。

真实冻结语料验收覆盖 JE-1000F/US 49 页 66 个组件、JE-1000F/EU 76 页
99 个组件、JBP-2000B/JP 12 页 9 个组件。将五类旧 source projector 全部替换为
抛错桩后，三目标仍可脱离 RST/CSV 冷重放；与第 1 刀代码对同源重建的逐页 HTML
比较均为零差异（仅规范化包根 file URI）。JBP-JP 仍使用含日文标注的 Overview
整图，没有退回两张无字图。完整设计与验收见
[`manual_ir_embedded_components_plan.md`](manual_ir_embedded_components_plan.md)。

## 后续第 3 刀：Operation、Warranty 与 LCD Mode（2026-09-05）

整本 `whole-document-components/v1` 现在再嵌入五种 ComponentSpec：
`HB-SPECIAL-OPERATION`、`HB-TABLE-LCD-MODE`、`HB-WARRANTY-LEAD`、
`HB-WARRANTY-SECTION` 和 `HB-WARRANTY-YEARS`。Operation 的步骤、前置条件、
附加说明和 artwork role 属于中立语义；Web 坐标及 composite locale 仍由 Web
presentation contract 管理。US 已批准 composite 继续以原
`source_fragment_sha256` 闸门校验，没有重算 golden 来放行变化。

LCD Mode 明确保留为“市场图 + 两组状态 + 六行可编辑表格”，没有截成整表图片。
Warranty 的引导、五个正文卡片和 3/2 年限卡分别拥有独立语义实例；德语
`JAHRE`、意大利语 `ANNI` 与英语 `YEARS` 进入同一个数字徽章 adapter。回放时旧
Warranty/LCD DOM projector 不再运行；Operation 在本刀内复用既有、哈希稳定的
Web composition transform 作为兼容层，第 7 刀才移除这层。

真实入口验收包括 JE-1000F/US review-asis，以及从
`origin/review/JE-1000F-EU@7d764e22` 隔离 worktree 物化的 DE/IT 审稿页。US
输出 5 个 Operation、5 个既有 approved composite、1 个可编辑 LCD Mode 和
`3/2 YEARS`；DE/IT 各输出 5 个 Operation、1 个可编辑 LCD Mode，年限分别为
`3/2 JAHRE`、`3/2 ANNI`。完整边界、非目标与验收梯见
[`manual_ir_operation_warranty_lcd_plan.md`](manual_ir_operation_warranty_lcd_plan.md)。

新增 `HB-SPECIAL-OPERATION` 后，共享 style contract 的 hash 发生预期变化。
正式 rebind 工具只刷新 JE-1000F/US 批准合同的
`identity.style.style_contract_sha256`：52 个 page binding 无变化、content 未重批、
58 页 composition map 无变化。3767 项全量测试（19 skipped）、reference pin、
Ruff、62 个 maintainability hotspot、1708 条文档链接和隔离 target check 均通过。

## 后续第 4 刀：LCD、Troubleshooting 与 Symbols（2026-09-05）

整本 IR 再纳入四种既有样式语义：`HB-TABLE-LCD-ICON`、
`HB-TABLE-TROUBLESHOOTING`、`HB-TABLE-SYMBOL-SIGNAL` 和
`HB-TABLE-SYMBOL-ICON`。它们的行、表头、本地化富文本和图标引用进入共享
ComponentSpec；Web 从冻结 IR 直接绘制原生表格，不再在回放时扫描 DOM，也没有把
任何表格改成截图。

Component registry 新增显式 `multiple: true` 资产合同。LCD 与 Symbol 图标共用一个
有序 `icons` role，行内 `asset_index` 指向最终打包资产；未声明的重复 role、数量
不匹配、空图片或语义/源结构不一致都会失败。Troubleshooting 与 LCD 的重命名 CSV
slot 由 assembly planner 的 page declaration 识别，不靠文件名或译文表头。

符号图标不再固化 JE-1000F/US 的 6+5 行：同一严格双面板 parser 同时接受真实
US 6+5 与 JE-3000C/KR 5+2，仍拒绝 rowspan/colspan、半对图文、空资产和歧义表。
四类组件均登记 Web/LaTeX/IDML/Word adapter；App/reference figures、presentation
overlay 分层与旧兼容路径最终退役继续留给第 5–7 刀。

全语料构建还补上两项第 3 刀的跨语言安全网：Operation 重放会把 ComponentSpec
中的 supporting copy 放回步骤 block 的语义位置，再交给兼容 Web transform，因而
法语多出的普通说明不会截断三条待机说明；未列入 `figure_targets` 的不同产品骨架
不会被强套 JE-1000F 五面板合同，仍保留为 neutral flow。Warranty 年限 parser 同时
接受 `3 YEARS` 一类空格单位和韩语 `3년` 一类紧邻单位。

## 后续第 5 刀：App 与 Reference Figure（2026-09-05）

整本 IR 新增 `HB-SPECIAL-APP` 与 `HB-SPECIAL-REFERENCE-FIGURE`，注册组件总数
由十四种增至十六种。App 的 download、inline-control、add-device 三个 variant
保留本地化 rich copy、可访问标签和 role-bound 共享 artwork；Reference Figure 的
semantic-fallback 与 approved-composite variant 则把完整 carrier flow、asset role、
locale policy 和 composite provenance 一起写入 ComponentSpec。

批准整图不再只是 Web 端的路径覆盖。实例同时记录稳定 replace key、locale、
`content_sha256` 和 `source_fragment_sha256`，回放时与包内 asset union 逐项核对。
`exact` locale 不会回退到另一语言，只有显式 `shared` 资产允许共享；没有批准整图
的目标继续使用“无字底图 + 本地化 HTML 文字/引线”的完整 semantic fallback，
不会借用 JE-1000F/US 图像。Web 冷重放直接消费组件声明的 carrier，不再扫描整页
DOM 重新识别 App 或 Reference Figure。

真实入口验收覆盖 JE-1000F/US EN/FR/ES 合订本、隔离审稿分支中的 JE-1000F/EU
DE/IT，以及未获 JE-1000F figure contract 的 JE-3000C/KR。US 合订本得到 9 个 App、
15 个 Reference Figure（其中 6 个 approved composite）；EU DE/IT 各得到完整 App/
Reference semantic composition；KR 保持普通 flow，证明目标合同没有串用。五个包
均可在禁止读取 RST/CSV 后从冻结 IR 重放，包内图片路径与哈希全部闭合。桌面和
390 px 移动验收确认 Operation 的 On/Off 文字、App 三步、Charging 整图与 Warranty
3/2 年数字徽章均可见且组件无横向溢出；滚动触发全部 210 张 US 图片后无破图。

本刀不修改或重新批准 PDF/AI/composite artwork，也不把规格、LCD、Symbols、
Troubleshooting 或 Warranty 转成截图。presentation base/profile/target overlay 分层
仍属于第 6 刀；反型号专属代码闸门、四端整本入口验收和旧 DOM 兼容路径退役仍属于
第 7 刀。完整设计与验证命令见
[`manual_ir_app_reference_plan.md`](manual_ir_app_reference_plan.md)。

### 已清零的 5B 资产债

JE-1000F/EU 的 EN/FR/ES/DE/IT 已从操作者指定的 EU/UK 源 PDF 抽取并登记
55/55 张完整面板：每语两张 Overview、五张 Operation、四张 Charging。每张图都
保留该语言的文字与原生引线，并绑定 source page/crop、locale、content SHA-256 与
source-fragment SHA-256。意大利语是 11/11 `approved-composite`；过去的“无字底图
+ HTML/SVG 本地化文字/引线”只是历史 fallback，不能作为最终交付，也不能销账。

目标覆盖闸门只接受 `finished-panel` / `approved-composite`。任何
`editable-fallback` / `missing`、重复槽位或缺槽都失败。该要求不适用于本应保持
原生 HTML 的规格、Warranty、LCD、Troubleshooting 与 Symbols 表格。

## 后续第 6 刀：分层 Web presentation 合同（2026-09-05）

单体 Web presentation 合同已拆为 shared base、skeleton profile 和 `(model, region)`
target overlay。映射递归合并、带稳定 `id` 的列表按项覆盖、普通列表整表替换；未知
骨架、重复目标、越界路径和歧义目标均失败。新目标只提交能力、覆盖策略和真实差异，
不能复制共享组件或整套骨架。

整本生产路径只解析一次实际目标，将 resolved contract 与 layer identity 冻结进 IR；
冷重放不再打开 layer registry。Overview 实例按实际目标解析，不再使用全局固定
instance。JE-1000F/EU 保持 55/55 本地化成品整图，其中 IT 11/11；US 的 Charging
fallback 与 KR 的缺图继续显式计债，不能被本次配置分层掩盖。

## 后续第 7 刀：最终入口闸门与旧 DOM 退役（2026-09-05）

新 `whole-document-components/v1` 包已把 ComponentSpec registry、manual theme、
resolved Overview instance 及其 SHA-256 一起冻结进 `manual.ir.json`。figure-capable
目标必须声明完整 locale/slot 集，且允许状态只能是 `finished-panel` 与
`approved-composite`。既有 US 9 项 `editable-fallback` 和 KR 9 项 `missing` 放在
独立版本化债务 baseline；新增或变差的债务失败，债务变成成品后未同步删除旧记录也
失败。EU 没有债务例外，因此意大利语一旦退回无字底图加 HTML 文字/引线会立即失败。

新生产 IR 已在 source adapter 阶段完成 Preface inventory 与 Auto Resume 的 Web
normalization。冷重放只做 ComponentSpec dispatch、资产 rebasing 与 hash 校验，不再
调用旧 `transform_web_fragment()`；历史 `manual-ir/v1` 与
`whole-document-flow/v1` 仍通过显式兼容路径读取。

共享 Web/ManualIR/ComponentSpec Python 与 Web CSS 还受反型号字面量 guardrail
保护，目标差异只能进入 overlay、资产、实例和数据。四个代表包在禁读 RST、CSV、
renderer contract 并禁用旧 DOM projector 后完成冷重放；共 401 个 ComponentSpec
逐实例验证 Web、LaTeX、IDML、Word 四个 adapter binding，共 1604 个绑定。这里证明
的是共享语义实例和四端 adapter 入口，不宣称 Web 与固定页输出逐像素或逐分页相同。

完整设计、非目标和验收梯见
[`manual_ir_final_gates_plan_2026-09.md`](manual_ir_final_gates_plan_2026-09.md)。
