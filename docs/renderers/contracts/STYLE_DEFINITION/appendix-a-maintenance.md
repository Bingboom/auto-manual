# 样式定义：附录 A 组件与维护流程

属于[样式定义](../STYLE_DEFINITION.md)，其索引列出全部分页。章节编号与原文一致。
本主题的新说明写在本页，不要追加到总文件。

## 附录 A 组件与维护流程

### A.1 一个组件由什么构成

| 层 | 内容 | 落在哪 |
|---|---|---|
| 语义 | 语义 ID、`semantic_source_kinds`、`theme_token_roles`、token refs、四端 capability/binding、`conformance` / `constraints` / `approved_variants` | [`manual_style.yaml`](../manual_style.yaml) |
| 主题角色 | 组件 token role 消费的 surface / border / radius / type / width 角色及四端 binding | [`manual_theme.yaml`](../manual_theme.yaml) |
| 源写法 | MyST 围栏指令，或 RST 模板 / 源表字段 | [`tools/manual_md_directives.py`](../../../../tools/manual_md_directives.py)、`docs/templates/` |
| 标记 | `figure.hb-*-composition` 外壳 + 表格/网格骨架 + 每列一个 `col.hb-*-col-*` | 指令的 `run()` 或流水线渲染器 |
| 样式 | 顶层 class 上的规则；分列宽度写在 `col` class 上 | [`web_manual.css`](../web_manual.css) 及两个分模块 |
| 印刷 | LaTeX 入口宏 + IDML 渲染器 | `docs/renderers/latex/`、`tools/idml/` |

外壳与骨架分离是硬约定：**外壳负责外框、圆角、横向滚动、外宽契约；内表只负责格线与排字**。规格表、故障排查表、对比表、LCD 模式表都遵循这一层划分，所以窄屏时是外壳滚动而不是表格压字。

### A.2 围栏指令的构造契约

八个指令共用基类 `_ManualDirective`（`has_content`、一个可选参数、默认不接受任意 option）：

| 环节 | 约定 |
|---|---|
| 参数 | `self.label`。多数指令 → `aria-label`；`comparison` 拆成两个表头；`lcd-mode` 当作图片 |
| 行解析 | `rows()`：按未转义的 `|` 分列并 `strip`，奇数个连续反斜杠转义紧随其后的竖线（`\|` → 字面 `|`），偶数个反斜杠保留一半并仍把竖线作为分隔符；**空行直接丢弃** |
| 类型化 option | `callout` 只接受 `:variant:`，值限 `warning` / `danger` / `caution` / `note` / `tip`；`troubleshooting` 接受恰好两个非空格子的 `:headers:`；`manual-table` 接受 `:headers:`。其它 option、任意 `:class:` 和未知 variant 均 fail-closed |
| 行内子集 | `_inline_html()`：转义 `& < > "` 后只还原 `**粗体**`、`^上标^`、`~下标~`。`callout` 例外，走 `nested_parse` 完整 Markdown |
| 图片格 | `_image_html()`：只在 `lcd-icons` 第 2 列、`symbols` 第 1 列、`lcd-mode` 参数位 |
| 多步文本 | `_line_block()`：` / ` 分隔 → `.line-block` > `.line`；少于两段退化为 `<p>` |
| 合并语义 | `_merged_row()`：空格子并入上方（每列独立）。`spec-table` 用自己的实现，**只看第一列** |
| 输出 | `nodes.raw(format="html")`，即样式契约要的确切标记 |

### A.3 复用一个已有样式或完整组件

复用不是复制现有页面后再调到相似，而是让新调用方进入同一个公共组件边界：

1. 在 §1 找到 `HB-*` 语义，在所属视觉章节确认不变量与批准 variant。
2. 找到现有完整组件公共入口；调用方只传语义数据、语言、登记在册的
   density/variant、可用矩形和 z-order。
3. 组件独占底色、圆角、列宽、行高、内边距、内部间距、内容 fitting、溢出策略与
   原生载体空间。页面不得 import 私有 helper、metrics 或内部 token。
4. 最终化只能处理组件显式暴露的不可见载体；不得修改可见 story frame、plate、
   mask、outline 或 row。
5. 用 EN/FR/ES 的同一组件 fixture 验证适用密度，并与批准 JE/reference 页面做真实
   视觉对比。构建成功、XML 无错或只看英文都不构成视觉验收。

各现有 IDML 组件的公共入口、允许输入、禁区和验证清单统一维护在
[`共享样式与完整组件应用指南`](../../../../code-as-doc/dev/style_component_usage_guide.md)。
页面接入前先按该表审查；不能表达需求时再进入下一节的新组件流程。

### A.4 新增一个组件

1. **定义稳定语义。** 在 `manual_style.yaml` 加 `role`、
   `semantic_source_kinds`、`theme_token_roles`、token refs、四端 capability/binding，
   并诚实填写 `conformance`、`constraints` 和 `approved_variants`。先有语义，再有
   渲染器。
2. **提供稳定源结构。** 在模板、生成器或源表 schema 中加与本地化文案无关的
   标识；同步扩展 extractor、Manual IR 类型与 projector。不能从英文标题反推。
3. **实现四端投影。** Web 加顶层 composition/class，LaTeX 加稳定公共宏，IDML
   加可编辑组件/样式，Word 加结构归一规则。通栏 Web 组件加入 §8.1 的共享外宽
   selector。
4. **只在需要时提供 Markdown 指令。** 面向存量 Markdown 时，在
   [`manual_md_directives.py`](../../../../tools/manual_md_directives.py) 实现指令并注册；
   启发式 detector 只生成可审阅中间态，不直接决定 production 语义。
5. **补机器合同和本文。** 每端至少一个直接测试；§1 增加唯一对照行，相关视觉章节
   写清不变量、响应式/固定页差异和 source → output 示例。
6. **验证批准目标。** token 或合同变化要检查 reference pin；若 content/assembly
   发生变化，必须走显式批准，不能把 style rebind 当内容批准。

样式模块的规模边界由
[`tools/check_maintainability_guardrails.py`](../../../../tools/check_maintainability_guardrails.py)
看守。不要在本文复制阈值数字；阈值属于代码门禁，调整时要解释模块为什么不能继续
拆分，而不是只把上限调大。

### A.5 改样式的顺序

1. 在 `manual_style.yaml` 找语义 ID，确认 `semantic_source_kinds`、四端 binding、
   token 和当前 `conformance.debt` / 边界记录。
2. 在 §1 和所属视觉章节确认四端投影；判断本次是共享值变化，还是有理由的
   renderer-specific 投影。
3. 先改权威源：数值进 `layout_params.csv`，Web 响应式值进 CSS，结构语义进
   模板/extractor/IR。不要先改生成的 `params.tex` 或输出 HTML/IDML。
4. 更新所有受影响 renderer 和直接测试；新增差异必须登记，不能靠注释解释本地常量。
5. 更新本文，保证 §1、视觉定义、示例和维护规则不互相矛盾。
6. 按影响面验证；生成副作用只提交应提交的源文件。

最低验证矩阵：

| 影响面 | 至少运行 |
|---|---|
| 本文、导航或链接 | `python tools/check_doc_link_integrity.py` |
| `manual_style.yaml` / renderer 合同 | render-contract 定向测试 + `python -m unittest` |
| Python renderer / tests | Ruff + `python -m unittest` + maintainability guardrails |
| `layout_params.csv` | `python tools/csv_to_tex_params.py`，再审计 `params.tex` 差异 |
| Web 样式 | plain-Markdown 组件测试 + 一个真实 Web build |
| PDF/IDML 共享样式 | US check/build + reference pin；视觉变化另做真实 PDF/IDML 比对 |

规格表的 Web / PDF / IDML / Word 列宽就是已登记投影差异的例子。**只改 CSS 可能
让四端悄悄分叉**；只改 IDML 则可能让 token 名存实亡。不能手改批准 hash 绕过
reference gate。
