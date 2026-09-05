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

1. 内容树仍保留 HTML 元素/属性等适配提示，原有组件 payload 也有 HTML 片段；
   中立富文本语法以及 Word、print、IDML 全部消费同一语义树尚未完成。
   当前交付明确是公共 envelope + 整本 Web 入口闭环。
2. 源 RST 中仅面向 LaTeX 的宏仍由既有前置选择器排除；原始指令解析/严格诊断
   及旧 prepared-RST→IDML 适配器不是本轮的退出路径。
3. 本地 PDF 裁切已提交 recipe、绑定和图片，但没有登记到线上 Base 或发布站点；
   使用的是已有 fixture 快照，不能把本地试构建标记为线上交付。
4. US `runtime + fixture` 的旧 composite 源哈希已有不匹配；用旧转换器对同一源页
   重放得到完全相同错误（`product-overview.front`），未改冻结哈希来放行。
   本轮回归使用已经冻结的 review-asis 输入，该路径通过。

以上是显式后续边界，不继续追加无结束条件的 Web 小组件批次。

