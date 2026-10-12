# 样式定义：逐层实例，原始 RST 怎么变成 Web 版面（§10）

属于[样式定义](../STYLE_DEFINITION.md)，其索引列出全部分页。章节编号与原文一致。
本主题的新说明写在本页，不要追加到总文件。

## 10. 逐层实例：原始 RST 怎么变成 Web 版面

本节服务一个具体动作：**批量把存量文档转成当前构建物的 Web 样式**。示例全部取自真实源文件（共享模板与 JE-1000F / US 的冻结 review 派生物 [`docs/_review/JE-1000F/US/page/`](../../../_review/JE-1000F/US/page/)），每个语义按「原始 RST → 中间态 → 最终 Web 标记」给出，末尾给出批量转换时的 md 等价写法。版面数值不在这里重复，见 §2–§7 各条。

### 10.1 两条到达同一版面的链路

生产 Web 构建物走四层：

```text
(1) 装配   phase2 源表 + docs/templates/*.rst
           占位符（|PRODUCT_NAME|）与 {{ … }} 槽位替换、语言/区域 only 分支定型
           → prepared RST bundle：docs/_build/<model>/<region>/rst/page/*.rst
             （冻结样例：docs/_review/JE-1000F/US/page/）

(2) 出片   docutils 逐页渲染 HTML fragment（tools/word/bundle_html.py），
           同时做结构归一（tools/word/bundle_html_rewrite.py）：
           无表头、单行两列、首格是登记信号词的 list-table
           → table.manual-callout-table 等

(3) 升级   Web 档案（AUTO_MANUAL_PRESENTATION_PROFILE=web → tools/web/presentation.py）
           先按实际 model/region 解析 shared base → skeleton → target overlay，
           再按 resolved contract 的 source_patterns 认页（按页名 pattern，如
           spec_* / troubleshooting_* / *11_warranty，不猜内容），
           把 docutils 结构升级为 figure.hb-*-composition 骨架；
           结构不满足契约 → WebPresentationError，fail-closed

(4) 成站   pandoc 导出 MyST md（figure / callout 先换 token 保护、再原样恢复）
           → furo Sphinx 站点 + web_manual.css = 最终版面
```

两点边界：figure 升级只对目标 overlay 明确授权的 `(model, region)`（当前
JE-1000F / US 与 EU）生效，未授权目标保持中立 flow / 基础排版；生产整本 IR 冻结
该目标已经解析完成的合同与 layer ID，冷重放不重读 layer registry。Web publish 的
入口仍是 `AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md …`（见
[`user-guide/hello_auto-doc.md`](../../../../user-guide/hello_auto-doc.md)）。

存量转换链（本分支）只有两层：

```text
存量 Markdown → tools/plain_markdown_site.py 转成中间 md（```{callout} 等围栏指令）
             → tools/manual_md_directives.py 的指令 run() 直接产出合同标记
             → 同一份 web_manual.css = 同一版面
```

**两条链的汇合点是「合同标记 + `web_manual.css`」。** 生产链靠"识别 RST 结构再升级"，存量链靠"指令直接产出"，落到页面上是同一套顶层 class。所以批量复刻**不需要**复刻 RST 那几层——RST 层的价值是看懂哪个源结构对应哪块版面、以及哪些版面只有流水线数据才长得出来；真正转换时写 md 指令即可。

### 10.2 逐语义速查

| 版面 | 原始 RST 源结构（生产链） | Web 挂点 | 批量转换写法 |
|---|---|---|---|
| H1 胶囊 | 页标题 `=====` 下划线；生成页直接 raw `<h1 class="hb-h1-pill">` | `h1` | `# 标题` |
| H2 圆点条 | 小节 `-----` 下划线 | `h2` | `## 标题` |
| 警示框 | 单行两列 `list-table :widths: 12 88`，首格 `**CAUTION**` | `table.manual-callout-table` | `` ```{callout} CAUTION `` |
| 竖式规格表 | 生成器写 raw `<table class="hb-spec-table">` | `figure.hb-spec-table-composition` | `` ```{spec-table} 分节名 `` |
| 故障排查表 | `list-table :widths: 14 86` + 表头行，行来自源表 | `figure.hb-troubleshooting-composition` | `` ```{troubleshooting} `` |
| LCD 图标表 | 四列 `list-table :widths: 8 12 28 52`，第 2 列是图 | `figure.hb-lcd-table-composition` | `` ```{lcd-icons} `` |
| 符号图标表 | 四列 `list-table :widths: 12 38 12 38`，左右两对 | `figure.hb-symbol-pair-composition` | `` ```{symbols} `` |
| 信号词表 | `list-table :widths: 22 78` + raw 徽标 span | `figure.hb-symbol-signal-composition` | 流水线专属，无 md 写法 |
| 对比表 | 操作页内两列带表头 `list-table`（条件列向上合并） | `figure.hb-auto-resume-composition` | `` ```{comparison} 左表头 \| 右表头 `` |
| 质保三件套 | `.. container:: warranty-*` + 50/50 `list-table` | `.hb-warranty-*` | 流水线专属，无 md 写法 |
| 开箱清单 | 三列 `list-table :widths: 33 33 34`（图 + 名） | `figure.hb-inbox-composition` | 流水线专属，无 md 写法 |
| 通用表 | 普通 `list-table` / grid 表 | `table.manual-table` | pipe 表 / `` ```{manual-table} `` |

下面逐条展开。每条的三层分别是：**L1 原始 RST**（占位符已合并的 prepared 形态）、**L2 中间态**（docutils 出什么、谁在哪一步识别）、**L3 最终 Web 标记**（`web_manual.css` 消费的骨架）。

### 10.3 标题与正文（`HB-TITLE-*`、`HB-TYPE-BODY/LIST`）

**L1 原始 RST**（[`troubleshooting_en.rst`](../../../_review/JE-1000F/US/page/troubleshooting_en.rst)、[`08_charging_methods.rst`](../../../templates/page_shared/en/08_charging_methods.rst)）：

```rst
TROUBLESHOOTING
========

If any of the following fault codes appear, follow the listed corrective actions...

CHARGING VIA SOLAR PANELS (SOLD SEPARATELY)
-------------------------------------------

- 列表项一
- 列表项二
```

**L2** docutils 原生类型化：页标题 → `<h1>`、`-----` 小节 → `<h2>`、`~~~~~` → `<h3>`、段落 → `<p>`、列表 → `<ul>/<ol>`，不需要任何识别步骤。生成页（规格页）跳过 RST 标题、直接 raw 写 `<h1 class="hb-h1-pill">`，两种来源到 L3 等价。

**L3** CSS 直接挂在裸标签上（`#furo-main-content h1/h2/h3/p/ul`），版面规则见 §2.2–§2.4。**md 等价**：`# ` / `## ` / `### ` 与原生段落列表；H1 的大写由 CSS `uppercase` 完成，源里不必写大写。

### 10.4 警示框（`HB-CALLOUT-STRIP`）

**L1 原始 RST**（[`08_charging_methods.rst`](../../../templates/page_shared/en/08_charging_methods.rst)，一框一表，正文格可带子列表）：

```rst
.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **CAUTION**
     - Ensure that the input voltage for both DC input ports is the same...

       - Use the same model of Jackery solar panels...
       - Do not charge the product using both a car charger and a solar panel...
```

**L2** 归一发生在链路第 (2) 层（[`word_bundle_html_rewrite.py`](../../../../tools/word/bundle_html_rewrite.py)）：判定条件是**无表头 + 恰好一行 + 恰好两格 + 首格文本是 [`signal_words.py`](../../../../tools/signal_words.py) 登记的信号词**，四项都满足才归一；差一项就按通用表处理。类型化入口随后生成同一个 `HB-CALLOUT-STRIP` ComponentSpec；五种 variant 是 `warning`、`danger`、`caution`、`note`、`tip`，标签、正文、列表、语言和 source ref 保持为实例数据。Web、LaTeX、IDML、Word 各自通过注册的 adapter 消费它，不再各自维护一份 variant 映射。

**L3 最终 Web 标记**：

```html
<table class="manual-callout-table"><tbody><tr>
  <td class="manual-callout-label"><p><strong>CAUTION</strong></p></td>
  <td class="manual-callout-body">…完整正文，可含列表…</td>
</tr></tbody></table>
```

版面规则见 §3.1。**md 等价**：`` ```{callout} CAUTION ``，正文按完整 Markdown 解析（[`manual_md_directives.py`](../../../../tools/manual_md_directives.py) 先校验 ComponentSpec，再由 Web adapter 产出上面这段标记）。Pandoc 前后由 [`web_presentation.py`](../../../../tools/web/presentation.py) 保护并原样恢复整张表；恢复前后会重新校验同一 component ID、variant 和 slot 内容，不能靠 Pandoc 重建一个近似表格。

### 10.5 竖式规格表（`HB-TABLE-SPEC`）

规格页整页由生成器产出，prepared RST 里已是 `.. only::` 双分支的 raw（LaTeX 分支走 `\specsectiontitle` + `spectable` 环境）。

**L1 原始 RST**（[`spec_en.rst`](../../../_review/JE-1000F/US/page/spec_en.rst) 的 HTML 分支）：

```rst
.. only:: html

   .. raw:: html

      <h1 class="hb-h1-pill">SPECIFICATIONS</h1>

   .. raw:: html

      <h2 class="hb-spec-section">…GENERAL INFO…</h2>
      <table class="hb-spec-table">
        <tbody>
          <tr>
            <th scope="row" class="hb-spec-label">Product Name</th>
            <td class="hb-spec-value">Jackery Explorer 1000</td>
          </tr>
          …
```

**L2** 源 adapter 先把每个分节投影为 `HB-TABLE-SPEC` ComponentSpec：
`section_title` 保留本地化标题，`rows` 按 label group 记录 `label_rowspan`、值列表和
圈号 reference。CSV/RST、MyST、IDML 和 Word 的旧入口是薄 facade，先经同一结构校验，
再交给各自 adapter；多行值在 Web 中仍可是一个 `<br>` 单元格，Word 可投影为带
rowspan 的多个物理行，因为物理标记不是共享合同。

网页链路第 (3) 层按页名 `spec_*` 认页，把每张 `hb-spec-table` 包进
`figure.hb-spec-table-composition` 外壳，并校验分节数与 ① 圈号脚注数
（`web_manual.json` 的 `specifications.section_count` / `circled_reference_count`）——
数不对整页报错。包装后还会从最终 DOM 反向校验一次 ComponentSpec，确保 Pandoc
保护/恢复的是同一张结构表，不是近似的通用表。

**L3**：`figure.hb-spec-table-composition > table.hb-spec-table`（外壳负责深色外框、圆角、横向滚动；内表只管格线），版面规则见 §4.2。**md 等价**：

````markdown
```{spec-table} GENERAL INFO
Product Name | Jackery Explorer 1000
Model No.    | JE-1000F /JE-1000F-SG
             | 标签留空 = 并入上一标签（rowspan）
```
````

### 10.6 故障排查表（`HB-TABLE-TROUBLESHOOTING`）

**L1 原始 RST**（[`troubleshooting_en.rst`](../../../_review/JE-1000F/US/page/troubleshooting_en.rst)；模板只有表头，行由源表经 `{{ troubleshooting_rows_rst }}` 灌入）：

```rst
.. list-table::
   :class: longtable
   :header-rows: 1
   :widths: 14 86

   * - Error Code
     - Corrective Measures
   * - F0
     - Restart the product.
   * - F4
     - Connect the product to loads to discharge its battery until the fault disappears.
```

**L2** 第 (3) 层按页名 `troubleshooting_*` 认页，要求**恰好一张**「1 表头行 + 错误码序列 F0…FE」的两列表；找到后注入 `colgroup`（`hb-troubleshooting-col-code/measures`）、给格子打 `hb-troubleshooting-code/measures` class，再包 `figure` 外壳。

**L3**：`figure.hb-troubleshooting-composition > table.hb-troubleshooting-table`，版面规则见 §4.3。**md 等价**：`` ```{troubleshooting} ``，行写 `F4 | 措施一 / 措施二`（` / ` 自动拆成分步行）；需要本地化表头时写 `:headers: Code | Corrective measures`，必须恰好两个非空格子。

### 10.7 LCD 图标表（`HB-TABLE-LCD-ICON`）

**L1 原始 RST**（[`lcd_icons_en.rst`](../../../_review/JE-1000F/US/page/lcd_icons_en.rst)；行含序号、源表附件图、名称、多步说明）：

```rst
.. only:: not latex

   .. list-table::
      :class: longtable
      :header-rows: 0
      :widths: 8 12 28 52

      * - 1
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/1_Wi-Fi_….png
             :alt: Wi-Fi
             :width: 42px
        - Wi-Fi
        - | **On:** Wi-Fi connected.
          | **Blink:** Ready to connect to Wi-Fi.
          | **Off:** Wi-Fi disconnected.
```

**L2** 第 (3) 层按页名 `lcd_icons_*` 认页，要求**全页恰好一张四列表**、每行第 2 格必须有 `img`；命中后注入 `colgroup`（`hb-lcd-col-number/icon/name/description`）、逐格打 class、图片清掉宽高改由 CSS 管，再包 `figure`。

**L3**：`figure.hb-lcd-table-composition > table.hb-lcd-icon-table`，版面规则见 §4.4。**md 等价**：`` ```{lcd-icons} ``，行写 `1 | 图.png | Wi-Fi | On: … / Blink: …`（图片格只认第 2 列）。

IDML 的可见 LCD 圆角外壳高度必须等于表格行高之和，最后一行直接闭合到底部
圆角线。InDesign 原生终止标记使用外壳之外、与主表框串接的透明载体；最终化脚本
只能按 `tf_terminal_carrier_group_*` 标签扩展该载体，禁止读取表格行高后改写主表框、
底部遮罩、底板或外框。EN/FR/ES 共用这一结构回归。

### 10.8 符号页两表（`HB-TABLE-SYMBOL-SIGNAL` / `-ICON`）

**L1 原始 RST**（[`symbols_en.rst`](../../../_review/JE-1000F/US/page/symbols_en.rst)；同一页两张表）——信号词表是 22/78 两列，徽标是流水线生成的 raw span：

```rst
.. list-table::
   :class: longtable
   :header-rows: 1
   :widths: 22 78

   * - Symbol
     - Meaning
   * - .. raw:: html

          <span class="hb-warning-lockup" …>⚠ WARNING</span>
     - Hazardous practices that may result in severe injury, death...
```

图标表是 12/38/12/38 四列（左右各一对「图 + 释义」）：

```rst
.. list-table::
   :header-rows: 0
   :widths: 12 38 12 38

   * - .. image:: …/symbols/1_warning_triangle_….png
     - Warning and Caution Symbols. Alerts individuals to...
     - .. image:: …/symbols/7_do_not_dismantle_….png
     - Do not dismantle the product.
```

**L2** 第 (3) 层按页名 `symbols_*` 认页：信号词表按登记行数校验后升级为 `.hb-symbol-signal-composition`；四列表拆成左右两块独立面板。

**L3**：`figure.hb-symbol-signal-composition` 与 `figure.hb-symbol-pair-composition`（双面板 grid，行高互不影响），版面规则见 §4.6。**md 等价**：图标表用 `` ```{symbols} ``（每行四格）；信号词表流水线专属，存量转换时用 `` ```{callout} `` 或通用表近似，无同款徽标。

### 10.9 质保三件套（`HB-WARRANTY-LEAD` / `-SECTION` / `-YEARS`）

**L1 原始 RST**（[`11_warranty.rst`](../../../templates/page_shared/en/11_warranty.rst)；语义靠**显式 container**，与标题措辞无关——§0.2 的第 2 条写入规则就是这里）：

```rst
.. container:: warranty-lead

   **This warranty applies only to customers who purchase from...**

.. container:: warranty-section warranty-years

   Warranty Period
   ---------------

   .. list-table::
      :header-rows: 0
      :widths: 50 50

      * - **3 YEARS**

          **Standard Warranty**

          The standard warranty period for |PRODUCT_NAME| is 36 months...

        - **2 YEARS**

          **Extended Warranty**
          ...
```

**L2** docutils 把 container 渲染成 `<div class="warranty-section …">`；第 (3) 层按页名 `*11_warranty` 认页，按登记的 `section_count` / `period_years` 校验后重组。

**L3**：引语 → `.hb-warranty-intro-composition`，条款 → `.hb-warranty-card`，年限 → `.hb-warranty-period-card > .hb-warranty-period-grid`（大数字徽章 + 单位 + 副本），版面规则见 §6。**md 无等价写法**：年限卡的「3 YEARS / 2 YEARS」拆解依赖登记结构，存量转换遇到质保页保持普通标题 + 段落即可。

### 10.10 开箱清单卡（`HB-SPECIAL-INBOX`）

**L1 原始 RST**（[`02_whats_in_the_box.rst`](../../../_review/JE-1000F/US/page/02_whats_in_the_box.rst)；区域分支 + 三列图文表 + TIP 框）：

```rst
.. only:: not latex and region_us

   .. raw:: html

      <h1>WHAT'S IN THE BOX</h1>

   .. list-table::
      :header-rows: 0
      :widths: 33 33 34

      * - .. image:: asset:in_the_box/main_unit1
             :width: 120px

          **Jackery Explorer 1000**
        - .. image:: asset:in_the_box/ac_charging_cable
             :width: 120px

          **AC Charging Cable**
        - …
```

**L2/L3** source projector 把 H1、单行非空图文表和紧随其后的 TIP/NOTE 表组合为一个 `HB-SPECIAL-INBOX` ComponentSpec；三列源表保持 `three-card-responsive` 与原 `card_1_art`–`card_3_art` 序列，其他项数进入 `responsive-card-grid` 与有序重复 `card_art`。Web adapter 再输出 `.hb-inbox-composition > .hb-inbox-grid`：有序圆角卡 + 数字角标 + 通栏提示条（版面见 §5）。projector 以显式 H1、非空卡片组和提示合同 fail-closed，不再从不完整列表或页面邻接形状补造实例。**md 无等价写法**（角标与卡片组版是流水线重组的产物）。

### 10.11 例外：模板自带双分支的页（安全页、FCC）

安全页不走「识别升级」：模板里 LaTeX 与 HTML 两个分支**并排手写**，Web 标记在源里就是成品（[`safety_en.rst`](../../../templates/page_us-en/safety_en.rst)）：

```rst
.. only:: latex

   .. raw:: latex

      \HBSafetyInstruction{INSTRUCTIONS PERTAINING TO RISK OF FIRE, ...}
      \HBWarningLeadBlock{WARNING}{Always follow these basic precautions...}

.. only:: html

   .. raw:: html

      <div class="hb-safety">
        <h1 class="hb-h1-pill">IMPORTANT SAFETY INFORMATION</h1>
        <div class="hb-warning-box">…</div>
        <div class="hb-two-col">
          <p class="hb-lead">Always follow these basic precautions...</p>
          <ul class="hb-list">…</ul>
        </div>
      </div>
```

改这类页 = 同时改两个分支；只改一个分支就是 Web/印刷分叉。批量转换存量文档遇到安全类内容时，用 `` ```{callout} WARNING `` 承载文案即可，不要手抄 `hb-safety` 结构（那是 §3.2 的流水线专属语义）。

FridgeGuard 的 EN/FR/ES 安全页沿用现有 `hb-symbol-signal-composition`，用 `hb-safety-instruction` / `hb-safety-lead` 显式声明风险提示与首段警告的 Web 版式。风险提示表必须放在受保护的 figure 内，避免 Pandoc/MyST 将它转为带空表头的普通表格；三角图标复用共用深色/白色 SVG，并声明尺寸。共用样式由 [`web_symbols_fcc_components.css`](../web_symbols_fcc_components.css) 维护，保留深色图标整格、加粗原文、紧凑双栏与深色操作标题条。双栏外侧不加 `border-spacing`，只由两格内侧 padding 保留栏距，使标题、风险提示与警告框左边缘对齐。640px 以下，外表、tbody、tr 与两格均转为全宽单栏；风险图标列保留固定宽度。其他语言继承这些声明、结构与图标，仅使用其原稿文案。纯 Web 排版修复不改印刷分支的原文或语义。
