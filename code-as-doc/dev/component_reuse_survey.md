# 跨产线组件与样式复用 — 现状梳理

Date: 2026-08-25

Owner: renderer contract maintainers

主线承重数字在 `main` 上复核；Symbols 几何所有权案例在
`fix/bp-us-idml-components` 合入本页后复核，并在对应段落明确标出。

Canonical style definition: [`STYLE_DEFINITION.md`](../../docs/renderers/contracts/STYLE_DEFINITION.md)

Operational reuse guide: [`style_component_usage_guide.md`](style_component_usage_guide.md)

> **这不是第二份样式规范。** 语义定义、四端绑定、新增组件流程和视觉合同一律
> 以 [`STYLE_DEFINITION.md`](../../docs/renderers/contracts/STYLE_DEFINITION.md)
> 为准；欠账状态以 [`manual_style.yaml`](../../docs/renderers/contracts/manual_style.yaml)
> 的 `conformance` 为准。本页只做一件那两处都不做的事：**盘点"同一件事被定义了
> 几次"**，并给出下一条产线、下一种语言开工前应当先定义什么。
>
> 本页不复制规范条文、不保存 commit / hash / 页数。发现的可执行缺陷立即开单，
> 不在此页累积待办。
>
> 数字全部由脚本对 `main` 的树复核（方法见 §8），不是转述。每处 `file:line`
> 引用都自动核验过存在且行号在范围内。

---

## 1. 结论

**合同治投影，但此前既不治识别，也没有约束组件完成后的几何写权限。**

四端投影这一层治理得很好：31 条 `HB-*` 语义、四渲染器 capability/binding、
fail-closed 校验、令牌单源、Workstream X 把 9 条 `partial` 清算到
`debt: []`。加电包（JBP-2000B）整条产线落地时**零新增**产品专属 LaTeX 宏、
产品专属版式令牌和产品专属渲染器模块——复用层是真的成立。

但"语义有没有被识别出来"这一层没有合同。`HB-CALLOUT-STRIP` 的状态是
`state: aligned, debt: []`，同时模板语料里 **50% 的 callout 从未到达它**，
de / ko / uk / zh 四语是 **100% 到不了**。账本没说谎——它回答的是"语义到达之后
四端投影对不对"，schema 里没有任何字段问"这个语义在语言 X 里认不认得出来"。

主线调查确认的重复定义主要长在识别层，这也是本月两个窗口在同一张标签表上
撞车的原因（§3.1）。但 JBP Symbols 的后续验收补出了第二个盲区：**调用了同名
共享组件，不等于内部几何只有一个定义者。** 页面、组件、底层 primitive 和
InDesign 最终化脚本只要还能分别改行高、外壳或载体空间，就会重新落回逐页补丁
（§3.6）。

---

## 2. 复用层确实成立（不要重复解决已解决的问题）

加电包产线的实测结论，逐条可复验：

| 检查 | 结果 | 命令 |
|---|---|---|
| `page_bp/**` 新增 LaTeX 宏 | 0 | `grep -rn "newcommand\|providecommand\|HBOverrideParam" docs/templates/page_bp/` |
| `layout_params.csv` 里的 bp/jbp 产品专属令牌 | 0 | `grep -ci "jbp\|_bp_" data/layout_params.csv` |
| bp 专用 `.tex` 模块 | 0 | `ls docs/renderers/latex/ \| grep -ci "bp\|jbp"` |
| `tools/` 里的 bp 专用模块 | 0 | `find tools -iname "*bp*" -o -iname "*jbp*"` |
| 共享渲染器代码里的 `JBP-2000B` 分支 | 0（唯一一处是 `tools/renderer_acceptance.py:30` 的用法示例注释） | `grep -rln "JBP-2000B" tools/` |

因此下面这些机制**已经能承载新产线，不要另造**：

- 三层骨架：blueprint → region profile → resolved manifest（`tools/skeleton_resolve.py`，字节确定性由 `tests/test_skeleton_resolve.py` 钉住）
- ComponentSpec 四端 adapter（`tools/component_specs/`，未注册 key 直接 raise）
- 版式令牌单源 `data/layout_params.csv` → `params.tex` / IDML `param_pt`
- 组件密度变体 `standard` / `compact`（必须留在同一完整组件内，不是页面复制一套内部几何）
- 资产语义引用 `.. image:: asset:KEY` + `override_for`（模板里已无裸路径）
- 片段层 `{{snippet:<id>}}` + `docs/templates/snippets/registry.yaml`
- 语义容器 `.. container:: warranty-section`（§3.3）

---

## 3. 识别层的病灶：硬编码本地化字符串门

### 3.1 病灶形态

组件是否激活，取决于代码里一个**硬编码的本地化字符串集合**或**语言码集合**。
集合外的语言静默退化——不报错、不进日志、两个渲染器同时丢框。

全仓扫描（`tools/` + `docs/renderers/`，AST 级）命中 **59 处**这类字面集合。
其中每一处的语言覆盖各不相同：

| 门 | 站点 | 覆盖语言 |
|---|---|---|
| callout 标签 → variant | `tools/component_specs/callout.py:15`（26 键） | en / fr / es |
| 质保页标题 → 组件化 | `docs/renderers/latex/hb_latex_warranty.py:9` | **仅 en** |
| 质保标题 → 语言反推 | `tools/idml/stories.py:36`、`tools/idml/page_objects.py:574` | en / fr / es |
| 开关键文案 | `tools/idml/oppanel.py:24` | en / fr / es / ja / zh |
| 紧排/本地化几何 | `{"es","fr"}` 字面量 **13 处**（`tools/idml/symbols_page.py:217,436,621`、`character_metrics.py:24,114,158`、`safety_story.py:103,160`、`components/key_combinations.py:183`、`data_stories.py:784`、`page03.py:189`、`pages.py:125`、`csv_pages/renderers_symbols.py:662`） | fr / es |
| TOC 条目标题 | `tools/idml/page_toc.py:63`（39 键） | 多语混杂 |
| 注册在册的语言 | `tools/lang_registry.py` | **10 种** |

`tools/lang_registry.py` 已经是正确的单源（`governed_languages()`），
`symbols_page.py:93` 也确实在用它——但同一个文件的 `:217/:436/:621` 又写了字面
`{"es","fr"}`。**正确访问器与字面旁路并存于同一模块。**

### 3.2 callout：50% 静默丢框

按仓库自己的作者约定（`:widths: 12 88` 的单行双格表 + 粗体标签）统计
`docs/templates/**`：

| 语言 | callout 数 | 成框 | 丢框 | 未识别标签 |
|---|---:|---:|---:|---|
| de | 14 | 0 | **14** | VORSICHT×10, HINWEIS×4 |
| ko | 14 | 0 | **14** | 주의×10, 참고×4 |
| uk | 13 | 0 | **13** | УВАГА×9, ПРИМІТКА×4 |
| zh | 13 | 0 | **13** | 注意×8, 备注×3, 说明×1, 提示×1 |
| it | 14 | 4 | 10 | ATTENZIONE×10 |
| pt-BR | 14 | 4 | 10 | CUIDADO×10 |
| fr | 24 | 22 | 2 | REMARQUES×2 |
| en | 26 | 25 | 1 | NOTES×1 |
| es | 24 | 23 | 1 | OBSERVACIONES×1 |
| **合计** | **156** | **78** | **78（50%）** | |

**连「覆盖了」的三种语言也在丢框。** en / fr / es 各丢 1~2 个，全是**复数形式**
（`NOTES` / `REMARQUES` / `OBSERVACIONES`）。`tip` 一直带着 `TIPS` / `CONSEILS`
/ `CONSEJOS`，`note` 没有——同一张表里两个变体的处理不一致。这正是两个窗口各自
在分支上修过、至今都没合进 main 的那处缺口（§8）。

it / pt-BR 那 4 个成框的是 `NOTA`——**蹭西班牙语条目蹭到的**，两语真正的信号词
`ATTENZIONE` / `AVVERTENZA` / `CUIDADO` / `AVISO` / `PERICOLO` 全部返回 `None`。

最能说明问题的一对：意大利语 `ATTENZIONE` → `None`，法语 `ATTENTION` →
`caution`。**差一个字母，一个丢框一个不丢。**

同类陷阱在质保页的语言反推表里重演（`tools/idml/stories.py:36`）：西语
`GARANTÍA` 认得，葡语 `GARANTIA`（无重音）认不出——于是 pt-BR 质保页的语言只能
靠后面的兜底猜。

### 3.3 正确机制已存在，最新产线却没用

`STYLE_DEFINITION.md` §0.5 三处明文禁止靠文案识别：

- 层表：「源结构标识 …… **标识必须与本地化文案无关**」
- 规则 4：「页面角色 …… **不能从页面标题翻译文本推断**」
- 末段：「**不能静默退化成靠文案识别的普通段落**」

规则 2 还给出了质保语义的正确机制 `.. container:: warranty-section`，并注明
「当前显式 semantic container **只支持质保语义**」——质保恰恰是唯一有正确机制
的那个。

先看被禁的那条路还剩多少流量：`hb_latex_warranty.py:9` 的门是 `{"WARRANTY"}`，
**一个标题**。逐 `*warranty*.rst` 取首行比对：

| 页面标题 | 走到 `HBWarranty*` | 语言 |
|---|---|---|
| `WARRANTY` | ✅ | en |
| `GARANTIE` / `GARANTÍA` / `GARANZIA` / `GARANTIA` / `ГАРАНТІЯ` / `保修说明` / `保証について` / `보증` | ❌ 静默退化 | fr+de / es / it / pt-BR / uk / zh / ja / ko |

**1/9 个标题、1/10 个模板文件**走到组件。

而正确机制早已存在且已被采用：`page_shared/{en,de,es,fr,it,ko,pt-BR,uk}/11_warranty.rst`
八个语言全部用了 `.. container:: warranty-*`，**包括门外的 it/ko/pt-BR/uk**——
它们靠容器而非标题匹配到达组件。剩下 `page_jp`、`page_zh` 未迁。

所以标题门是这批页面的**退化回退路径**，不是主路径。真正的教训在下一条：
新产线容易漏掉容器这一步，而漏掉时没有任何东西提示。加电包产线（分支
`fix/bp-us-idml-components`，未合入 main）最初就是这样——质保页用 `**粗体**`
假标题而非容器，代价在 IDML 构建里当场报了出来：

```
tools/idml/oppanel.py:452: WarrantyGroupingWarning: warranty grouping skipped: missing h2
```

`oppanel.py:512-518` 告警后直接返回未分组的 blocks，`HB-WARRANTY-SECTION` 绑不上。
**构建当时就告诉我们了**，但没有闸门把这个告警变成失败。该产线随后已迁到容器，
IR 里现在是 1× `warranty_lead` + 5× `warranty_section` + 1× `warranty_years`。

---

### 3.4 反复出现的形态：已建未接

比"没建"更值钱也更危险的一类：**共享机制已经写好，却没有接上任何生产调用方**，
于是下一个人看不到它、又造一遍。三处实测：

| 已建的共享机制 | 生产调用方 | 后果 |
|---|---|---|
| `tools/render_contract.py:90 resolve_layout_tokens`（通用 `lang_<code>_<key>` 级联） | **0**（仅 `tests/test_render_contract.py:235-237`） | IDML 7 处各自重写级联，门还互不一致 |
| `tools/csv_pages/renderers_safety.py`（成套安全页生成器，配对发射 LaTeX + HTML 占位） | **0**（`PAGE_RENDERERS`（`renderers.py:47-52`）只注册 spec/symbols/lcd_icons/troubleshooting，无 safety；无外部 import） | 14 个安全页模板双通道手写两遍 |
| `tools/signal_words.py signal_label_entries`（十语数据驱动标签表） | **1**（只有 `tools/word_bundle_html_rewrite.py:13`） | 同一个日语 `警告` 表格：Word 有框，LaTeX / IDML 丢框 |

第三行是渲染器不对称的机制解释，在 import 层就看得见——不需要构建就能确认。

同一类形态还有一例反向的：`tools/audit_code_copy.py:40-75` 的 `ALERT_LABELS`
是一份**更宽**的字面集合（含 de/it/uk/ja/zh 的信号词），它不 import
`callout.py`。**审计工具认得的词，渲染时不认。**

### 3.5 同一个徽章，三种颜色

深色信号徽章是四端样式系统里唯一没有 `tools/component_specs/` 条目的组件。
同一个提交上它的底色有三个互不关联的值：

| 值 | 站点 | 出现在 |
|---|---|---|
| cmyk `0,0,0,0.90` | `data/layout_params.csv:1030 brand_color_branddark` | LaTeX / IDML |
| `#343031` | `docs/renderers/contracts/web_manual.css:10 --hb-brand-dark` | Web |
| `#4a4a4a` | `renderers_symbols.py:447` 与 `word_bundle_html_rewrite.py:95` 各写一遍 | 生成 RST / Word |

两个 Python 站点发射的内联样式串逐字符相同，`U+26A0` 字形也各写一遍。
`manual_style.yaml:208-217` 的 `HB-TABLE-SYMBOL-SIGNAL` 已经有 LaTeX/IDML 的
`comp_symbol_signal_*` 令牌，**缺的是底色令牌与非印刷端的盒模型令牌**。

### 3.6 同名组件，四个几何写入点：Symbols 为什么又修了一遍

这一例来自当前 `fix/bp-us-idml-components` 分支，不计入前述主线 59 处识别门。
JE-1000F 早已把信号徽标的表内居中和徽标内容基线做过一次；JBP 内容与它相同，
却仍出现 WARNING / CAUTION / NOTE / TIP 越往下越偏、Symbol 列底色铺不满、上下表
粘连。原因不是缺少 `VerticalJustification=CenterAlign`——生成的四个外层格本来就
有这个属性——而是同一视觉块仍有四处能写几何：

| 写入点 | 当时拥有的能力 | 重复后果 |
|---|---|---|
| compact 页面组合 | 自己解析 compact 行高、分栏和表间距 | 复用了表格函数，没有复用完整 JE 组件合同 |
| `components/symbols_panel.py` | 计算外壳、行、底板和载体余量 | 组件合并后仍原样保留 compact 尾部余量 |
| `page_objects.py` | 为余量补 K05 底板和分隔线尾巴 | 把空带遮住了，但空带仍存在 |
| `indesign_finalize.jsx` | 按重排后的表高反向拉伸文本框及同尺寸可见矩形 | 最终化阶段覆盖了组件自己声明的外壳几何 |

compact 英文信号表的三个普通行是 `21.317pt`，末行是 `25.15pt`，表尾另留
`11.5pt`；恰好 `3 × (25.15 - 21.317) = 11.499pt`。也就是说这 11.5pt 本应把
四个正文行补齐为等高，却被放到了整表底部。格内文字确实各自在自己的短行里居中，
但相对完整外壳和模板就逐行向上漂；继续补底色或调单个徽标坐标只能制造下一轮补丁。
法语和西语是同一结构，只是目标行高分别为 `23pt` 与 `23.25pt`。

本次收敛后的唯一所有权是：

- `SymbolsPanel` 同时服务 JE/JBP，只接收语言、数据、可用矩形与
  `standard` / `compact` 密度；
- standard 保留 JE 已批准行高，compact 在组件内部把大额载体余量吸收到可见正文行；
- InDesign 终止标记所需的 `4mm` 空间是独立透明文本框载体，不属于圆角外壳、
  K05 底板、遮罩、分隔线或表格行；
- 页面组合器只能放置组件；最终化脚本最多校准透明载体，不能再改任何可见几何；
- EN/FR/ES 的 standard/compact Story 与几何共同进入
  `idml_symbols_panel_golden.json`，最终化源码测试还明确拒绝遍历并改写可见矩形。

这条案例补全了本页的判断标准：**“没有型号分支”只是复用的必要条件，不是充分
条件。还必须证明完整组件是内部几何的唯一写入者，且导出后的后处理没有第二写权限。**

后续 JBP 验收又在 Troubleshooting 与 Charging 暴露了同一边界，而不是两个新的
页面特例：Troubleshooting 的可见行和外壳本来同为 `138.941pt`，最终化却把 `1pt`
终止标记余量加到可见外壳，首列因此露出白带；现在表格内容框严格止于 shell
底边，终止标记进入串接的第二个透明 `TextFrame`，并由
`tf_terminal_carrier_group_*` 稳定标签单独识别，最终化不再读取表高或改写内容框。
LCD 表也曾保留同一条二次写入路径：组件已经让行高之和等于可见外壳，最终化却
再次给主表框、圆角底板、外框和底部遮罩统一增加 `1pt`，于是末行下方重新露白。
现在 LCD 复用与 Troubleshooting 相同的透明终止载体和稳定标签，最终化只能扩展
载体；可见表格几何完全归 LCD 组件所有，EN/FR/ES 使用同一回归约束。
Charging 的 AboveLine 插图已自带
原生行盒，普通图后距 `4.25pt` 与尾部胶囊标题前距 `5.67pt` 又叠加，图→标题比模板
多出约 `9.5pt`；旧标题行还把第一列扩张到全部剩余宽度并给胶囊强制 `96pt`
最小宽度，导致英/法/西标题末字到胶囊首字分别被拉到约 `101.55/65.62/77.08pt`，
而批准模板仅为约 `10.94/11.73/9.98pt`。收敛规则仍是 D6：前者把 `1pt`
建模为独立透明载体；后者由共享 `HeadingPill` 按批准字体字面宽度确定两列，使用
`10.9pt` 可见文字间距，并由 `charging` 变体拥有图→标题的纵向过渡节奏。页面装配
计划只选择变体，不接收坐标、间距或列宽值。

Storage 随后确认了更直接的重复：compact JBP 页面曾另建标题故事、K05 圆角正文卡、
内边距和垂直边界，虽然外观接近参考，但 JE-1000F 已有批准的 inline H1 + prose
内容流。现统一让 Storage 适配器直接调用该故事渲染器；JBP 的
`storage_specifications` 编排只给 Storage 与 Specifications 分配两个外部矩形，
不再拥有标题基线、正文底色、圆角或 inset。EN/FR/ES golden 同时锁定 JE 的
`LeftIndent=4.74`、标题字面 `BaselineShift=0.5` 与无 JBP 专属灰底卡的结构。

随后发现 fixed/composed H1 仍存在一条隐蔽分叉：Safety、Symbols 与 Inbox 虽然
调用共享 `heading_text`，却使用 `BaselineShift=-1.5`；JE 的 flowed H1 则使用
`+0.5`，标准 Safety/Inbox 又靠文本框向上约 1.92pt 抵消，所以 JBP compact 页面
暴露为字面下沉。现在所有 H1 统一由 `heading_text` 输出 `+0.5pt`，固定标题框由
`h1_frame_opts` 自己生成与底条同高、同 Y 的文本矩形；Overview 实例也不再登记
独立 `title_text_rect`。页面编排器只放置外矩形，不能通过 Y 偏移重建内部基线。

同页 compact Specifications 也不能靠逐表外壳高度补齐版面。旧实现把
`81.7/28.5/28.5pt` 外壳减去等高单行后的余量全部加给末行，造成三张表的尾行
分别变成 `15.7/17.5/17.5pt`，其余单行仍为 `11pt`。现由规格表组件根据
单行/多行规则生成全部行高，圆角外壳直接取行高总和；compact 行关闭 AutoGrow，
页面编排器和最终化脚本都没有第二个行高写入点。

规格值里的直流符号也属于同一跨产线组件边界。JBP 曾把 U+2393 替换为固定
`7pt / 0.65pt` 的原生矢量，虽然规避了平台字体，却比 JE-1000F 批准稿的 6pt
Apple Symbols 字形明显更宽、更粗且上浮。现由共享 `portable_symbol_text` 按
Apple Symbols 的 em/advance/side-bearing/outline 指标生成原生路径，并随
`HB Spec Value` 的实际语言字号缩放；JE/JBP、standard/compact、EN/FR/ES 不再有
第二套直流符号几何。

这轮验收的复盘可压缩为一张因果表：

| 现象 | 当时的补丁式反应 | 真正根因 | 结构性收口 | 防复发证据 |
|---|---|---|---|---|
| Symbols 灰底铺不满、表粘连、徽标不居中 | 补底板、补分隔线、逐个调徽标 | compact 页面、组件、primitive、最终化四处都能写几何 | `SymbolsPanel` 独占标题、两类表、行列、底色、间距、续页与透明载体 | EN/FR/ES × standard/compact golden；边界测试禁止页面/最终化取得可见写权限 |
| Troubleshooting / LCD 末行下方白带 | 给末行或外壳加余量，再用底色遮盖 | InDesign 终止标记空间被算进可见 shell，最终化又拉伸主框 | 主框严格止于行高总和；终止标记进入串接的透明载体 | 三语行高/居中结构测试；finalizer 源码测试只允许 `tf_terminal_carrier_group_*` |
| Charging 图到 `SOLD SEPARATELY` 留白过大 | 单页缩间距、移动胶囊 | AboveLine 行盒与通用图后距/H2 前距叠加，标题两列又被拉满 | `HeadingPill(charging)` 独占图→标题节奏和两列字面宽度 | EN/FR/ES 同路径 package 回归；页面只选择 variant |
| Storage 多出灰底正文卡、标题基线不同 | 为 JBP 单独画近似卡片 | 没有调用 JE 已批准的 inline H1 + prose 完整故事 | `StoragePanel` 直接复用 JE story renderer，不暴露 fill/radius/inset | EN/FR/ES fixed-panel golden；页面只放置外部 story frame |
| Specifications 尾行偏高、圆点/直流符号突兀 | 给每张表固定 shell 高度、单独画符号 | shell、行高、H1/分节基线和 glyph 分别有第二写入点 | 组件按内容先算行高再定 shell；共享标题合同和 portable symbol | 单行等高、AutoGrow、基线与字形测试；页面无逐表几何参数 |

结论不是“以后小心一点”，而是把写权限变成机器可检查的接口边界。新型号、新语言
或新页面接入时，应直接按
[`共享样式与完整组件应用指南`](style_component_usage_guide.md) 的公共入口表和验收
清单执行；若调用方需要内部行高、底色、圆角、基线或载体参数，说明它还没有进入
完整组件，而不是“这个型号需要特殊调一下”。

---

## 4. 已验证的重复清单

78 条候选经对抗性验证（默认驳回，逐站点开文件核对）。下表是确认项；被驳回的
一并列出，避免下一个人重查。

| # | 重复的东西 | 独立定义站点 | 影响 |
|---:|---|---:|---|
| 1 | 本地化信号词（WARNING 一族） | 4 | pt-BR 同一本书印两个词（§5.1）|
| 2 | callout 标签 → variant 词汇表 | 4+ | 50% 丢框 |
| 3 | 警告三角图形解析 | 6 | 注册表 / 硬编码路径 / Unicode 字形并存 |
| 4 | `lang_<code>_<key>` 级联 | 7 | `render_contract.resolve_layout_tokens` **零生产调用方**，7 处各自重写 |
| 5 | 资产配方 key + 输出路径 + 哈希 | 2 组 | §5.2 |
| 6 | `05_operation_guide.yaml` 配方 | 8 | 字节相同仅差第 2 行，**而那行没有任何代码读** |
| 7 | 背板文案 + 几何 profile | 4 | `_JBP_US_BACK_COVER_PROFILE` 28 键中 27 键与合同 JSON 字节相同 |
| 8 | Word callout 标记 dict | 2 | `adapters.py:92` 与 `word_bundle_html_rewrite.py:474` 逐字符相同 |
| 9 | 信号词徽章 HTML | 2 | 两条 HTML 发射路径各写一遍内联样式串 |
| 10 | 长期存放建议文案 | 6 | snippet 层已建，`page_shared` 仍留副本 |
| 11 | Symbols 行高 / 外壳 / 载体空间 | 4 | 名义复用后仍连续出现底色、粘连、垂直居中补丁（§3.6） |

补一条清单外但同源的：**安全页内容按输出通道各写一遍**，14 个模板里
`.. only:: latex` 与 `.. only:: html` 两个分支手写同一批预防措施——接地说明、
130℃ 爆炸警告、充电温度上下限，在同一个文件里相隔约 90 行各打一遍
（`docs/templates/page_us-en/safety_en.rst:25-35/57-77` 对 `:110/:117`）。
`STYLE_DEFINITION.md` §10.11 确实把安全页列为"识别升级"路径的显式例外，
**但那个例外针对的是标记方式，不是内容要打两遍**——而能消除它的生成器已经写好
且没接上（§3.4）。这是本组里唯一"分叉后果属合规风险"而非观感问题的一条。

**被驳回**（列出来，省得下一个人重查）：

- 「188 处 `\providecommand` 回退值、54 处已漂移」——**方向搞反了**。
  `theme.tex:16` 先 `\input{params.tex}`，由 CSV 生成的 `\def` 已经落定，
  组件模块里的 `\providecommand` 对 CSV 覆盖的键**根本不生效**（`\def` 胜）。
  这些字面量是死默认值，不是活的双定义；`tests/test_latex_component_modules.py`
  已经钉住加载顺序。真正残留的只是 35 个只存在于 TeX、CSV 里没有的键。
- `comp_trouble_compact_*` 「CSV 与代码默认值重复」——代码侧站点不存在；CSV 那两行**无任何读取方**，是登记表腐烂，不是双定义。
- 「`page_bp/*/09_storage.rst` 重述了存放建议」——那三个文件正确地写了
  `{{snippet:battery_long_storage_advisory}}`，是消费者不是定义者。
- 「`components_symbols.tex` 重复解析三角图形」——它接的是 basename 参数，数据驱动；自己只画 TikZ 矢量填充（印刷需要 CMYK + 矢量，不应收敛）。

**已登记为分期债、不算意外重复**：`docs/templates/snippets/registry.yaml` 头部
自述该建议「以 10 份手工副本存在」，收敛列为后续 rollout。

---

## 5. 已开单的可执行缺陷

### 5.1 pt-BR 图例与被解释对象自相矛盾

`Localized_Copy.csv:26` pt-BR = **AVISO**（驱动符号页图例）；
`components_safety.tex:329` pt-BR = **ADVERTÊNCIA**（驱动安全页横幅）。
两页同在 `manual_pt-br.yaml`（`:8` 与 `:14`），`JE-1500D / pt-BR` 是活靶。

十种语言逐一比对，**九种完全一致，只有 pt-BR 漂移**——两份手工副本没有任何闸门
比对，于是在第十种语言上悄悄分叉。符号页本身就是解释信号词含义的图例。

> 已开单。词该用哪个属安全文案，需要操作者/母语者裁决，不能猜。

### 5.2 配方哈希冲突

`overview/je1000f_us/front_controls` 的 pdf 与 png 各被两个
`build_eligible: true` + `gate: approved` 的配方钉了**不同哈希**
（`manual_je1000f_us_front_controls.json` 对 `manual_je1000f_us_master.json`）。
加电包产线在分支上还有 4 组同形态的（`front_controls` / `left_side_ports`），
合入后共 6 组。

**今天出货的字节是对的**：逐个哈希核对，全部匹配较新那个配方，
`asset_registry.csv` 记的也是这个值。缺的是**退役元数据**——旧配方仍以
approved + build_eligible 声明着已被取代的哈希，
`tools/asset_pipeline/recipe.py` 只在单文件内查唯一性，跨配方无索引，
配方里也没有 `supersedes` 字段（意图只写在自由文本 `gate.reasons` 里）。

闸门与逃生口各一个，必须一起看：

- `check_registry`（`tools/asset_registry.py:704`）比对声明值与磁盘，
  不符即报 `hash_mismatch` → `asset-check` 失败。**闸门是真的。**
- `refresh_registry_csv`（同文件 `:232`、`:239-241`）按磁盘字节**重算**哈希并
  改写该行，分歧被当作刷新的正常理由，不报错。

所以"旧配方重跑 + 刷新登记表"这个很自然的组合，会把回退过的字节变成新的登记
真值，全程无红。`tools/asset_intake.py` 也不读登记表，只比对配方自带的 pin。

> 已开单。修的是配方层缺跨文件所有权索引与退役标记，不是重跑提取。
> 注意 `manual_je1000f_us_master.json` 被 `tools/app_ui_promotion.py:70` 按字节
> 钉死，改它必须同步更新那个 pin。

### 5.3 `missing_assets_report.md` 假阳性 18 条

见既有单据。14 条打包器正常收进 `Links/`，4 条是 LaTeX 专用（IDML 用
`warning_triangle_white.svg` 原生画徽章）。

---

## 6. 前期定义工作：开工前先定义这六件

这是本页的目的——下一条产线、下一种语言、下一个组件动手**之前**先把这六件事
定义下来，否则必然又造一遍轮子。

### D1 信号词词汇表反向索引（唯一真源）

现状：正向表已经齐全——`Localized_Copy.csv` 的 `symbols.signal.*.label`（十语）
优先，`symbols_blocks.csv` 的 `signal_row` / `label_<lang>` / `aliases_<lang>`
兜底，`tools/signal_words.py` 两个函数都能读。**缺的只是反向索引**
`label → signal_key`，以及让四端都去读它。

定义（建议形状）：`tools/signal_words.py` 增 `signal_label_index()`，
返回「全语言 + 全别名的归一化标签 → signal_key」；
`callout.py` 删掉 `_VARIANTS_BY_LABEL`，`variant_for_label()` 改为查该索引再过
现有的 `_VARIANT_ALIASES`；`audit_code_copy.py:40` 的 `ALERT_LABELS` 变成
`set(signal_label_index())`。别名（复数、近形词）作为数据列，不再是代码字面量。
`components_safety.tex` 加一条与 `\HBStoreBaseFromKey` 对等的文案注入通道，
TeX 里不再重打信号词。

收益：§3.2 的 78 处丢框、§5.1 的 pt-BR 分叉、§3.4 的渲染器不对称、
清单 #1/#2 一并消解。这是投入产出比最高的一件。

### D2 语言覆盖进合同

现状：`manual_style.yaml` 的 `conformance` 只描述四端投影，
一个组件可以 `aligned` 却在 7 种语言里是死的。

定义：给每条语义加一个语言覆盖字段（识别层，不是投影层），
声明该语义的**源结构识别**在哪些语言可用；由测试对模板语料取证。
`HB-CALLOUT-STRIP` 今天应当诚实地写成 en/fr/es，而不是无声的 `aligned`。

### D3 语言门一律走 `governed_languages()`

现状：13 处 `{"es","fr"}` 字面量与正确访问器并存，
`render_contract.resolve_layout_tokens` 建好了但**零生产调用方**。

定义：禁止字面语言集合（可加 lint 规则）；
`tools/idml/params.py` 暴露一个共享的本地化令牌访问器，
7 处各自实现的级联收敛到它——注意保留"仅治理语言级联"和"按组件严格性"两个
现有能力，`resolve_layout_tokens` 目前表达不了，需要先补。

### D4 识别层禁令要有闸门

现状：`STYLE_DEFINITION.md` §0.5 三处明文禁止靠本地化文案识别，
但没有任何检查执行它，于是有 59 处字面集合、3 处靠标题反推语言。

定义：把禁令做成检查——扫描 `tools/` + `docs/renderers/`，
本地化字符串集合参与路由判定即失败，例外需登记。
**扩展既有的 `tools/audit_code_copy.py`，不要另造工具**：它已经为
`signal_words.py` / `renderers_symbols.py` / `word_bundle_html_rewrite.py`
做了专项特判，说明早就知道这是热点区——但 `:171` 只扫 `*.py`，
所以 §5.1 那处分叉的两边（`.tex` 与 `.csv`）都在它视野之外。把扫描面扩到
`.tex` 与本地化 CSV 列即可。

### D5 新产线迁移清单要显式

现状：BP 拿到了骨架层的全部好处，却漏掉了语义容器（§3.3），
没有任何东西提示它漏了。

定义：新 `(型号, 区域)` 上线清单里显式列出"必须采用的识别层机制"，
逐项打勾——语义容器、`asset:` 引用、`{{snippet:}}`、`{{copy:}}`。
`.agents/skills/new-region-line/SKILL.md` 是这份清单的落点。

### D6 完整组件边界与后处理写权限

现状：JBP 最初复用了 Symbols 的底层表格函数，却在 compact 页面里重新解析一套
内部行高；后来虽然收敛为 `SymbolsPanel`，底板补线和最终化脚本仍能二次修改组件
几何。于是“共享组件已存在”与“共享组件是唯一真源”不是一回事。

定义：每个跨产线视觉块都必须有一个完整公共组件，其输入只包含语义数据、语言、
可用矩形和登记在册的密度/variant。组件合同明确拥有底色、圆角、列宽、行高、
内部间距、相邻子组件的过渡节奏、溢出策略和原生载体空间。页面组合器只决定放置与 z-order；底层
primitive 只执行组件传入的几何；导出/最终化脚本不得修改可见内部对象。

新密度或新产线接入前必须先做两项证明：

1. 调用的是完整组件 API，而不是组件私有表格函数或页面内复制的 token 解析；
2. 至少 EN/FR/ES 共用一份 standard/compact 几何与 Story 回归，并有源码级边界测试
   禁止页面和后处理重新取得内部写权限。

组件确实需要宿主软件承载余量时，必须把它建模成**透明、不可见、单独命名**的
载体；不得把余量混进可见外壳后再靠补底色、补线或最终脚本拉伸来掩盖。

---

## 7. 下一条产线开工前的自查

按顺序问，任一为"否"就先补：

0. **要造的东西是不是已经有了、只是没接上？** 先 grep 目标能力的函数名，
   再看它有几个生产调用方——§3.4 三例都是"建好了没人调"。
   零调用方不等于不存在，等于**等着你接**。
1. 新页面的语义，`manual_style.yaml` 里有 `HB-*` 吗？没有就先登记，别先写模板。
2. 结构化章节用了 `.. container::` 语义容器，还是 `**粗体**` 假标题？
3. 新语言的信号词进了 `Localized_Copy.csv` 吗？代码里是否还需要改字面量？（需要就说明 D1 没做）
4. 插图走 `.. image:: asset:KEY` 吗？新 key 的 `override_for` 留空了吗？（全新键必须留空）
5. 复用的文案是 `{{snippet:}}` / `{{copy:}}`，还是又粘了一份？
6. 版式数值进了 `layout_params.csv` 吗？还是留在 `.tex` / Python 字面量里？
7. 新产线调用的是完整组件 API，还是只复用了底层 primitive 又重写了内部几何？
8. 页面组合器或最终化脚本还能改组件的行高、列宽、底色、外壳和分隔线吗？
9. EN/FR/ES 是否共用同一份组件几何与 Story 回归基准？
10. 构建告警读了吗？`WarrantyGroupingWarning` 这类告警就是识别层在喊话。

多窗口并行时额外一条：**动共享词表/共享映射之前先 `git fetch` 看有没有人在改。**
§8 记的那次撞车，两个窗口在同一张标签表上相隔 10 小时各写了一遍同样的修复。

---

## 8. 方法与复验

九个面并行取证（ComponentSpec 层 / IDML 模块 / LaTeX 渲染器 / Word 管线 /
样式令牌 / RST 模板 / 骨架契约 / 资产层 / 既有治理文档），78 条重复候选逐条
对抗性验证（默认驳回、要求逐站点开文件、生成产物不计定义站点）。
Symbols 几何所有权作为合入后的第十个定向案例，另用 Story XML、InDesign
最终化报告和 PDF 坐标复核，不回写主线 78 条候选的历史统计。

承重数字由独立脚本复核，非 agent 转述：

| 数字 | 复验方式 |
|---|---|
| 156 / 78 / 78 callout | 按 `:widths: 12 88` 单行双格表统计，逐标签调 `variant_for_label()` |
| 10 种注册语言 | `tools.lang_registry.LANGUAGE_REGISTRY` |
| 59 处字面集合 | AST 扫描 `tools/` + `docs/renderers/` 的 Set/List/Tuple/frozenset/Dict 字面量 |
| 1 / 9 质保标题 | 逐 `*warranty*.rst` 取首行比对 `_WARRANTY_PAGE_TITLES` |
| 2 组哈希冲突 | 解析全部配方建 `(key, path)` 索引，再对 committed 文件取 sha256 |
| pt-BR 分叉 | 十语逐一比对 `Localized_Copy.csv` 与 `components_safety.tex` 分支 |
| Symbols 载体错配 | 对比 compact 行高和 frame allowance，复核最终 PDF 四个徽标中心间距及最终化脚本写入对象 |

两个窗口在同一张标签表上撞车的物证（本页 §1 所指）：共同基点 `efa4822b`，
`3a095ee8`（08-23 09:05）与 `2b6d00af`（08-23 19:18）各自独立加了
`NOTES`/`REMARQUES`/`NOTAS`，相隔 10 小时。
