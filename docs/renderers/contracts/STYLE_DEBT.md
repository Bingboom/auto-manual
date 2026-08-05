# 样式契约欠账清单

[`manual_style.yaml`](manual_style.yaml) 的 31 条语义里，**25 条 `partial` 全部带 `debt`**，另有 1 条 `aligned` 也留了一条说明性 `debt`（`HB-TABLE-LCD-ICON`）。本文把它们排成可执行的优先级。定义与四渲染器对照见 [`STYLE_DEFINITION.md`](STYLE_DEFINITION.md)。

几乎所有欠账都落在 **IDML 一侧**：Web 与 LaTeX 由 token 驱动，InDesign 渲染器则仍持有本地常量、或靠文本形状猜语义。

排序依据，按权重从高到低：**会不会静默出错**（错了没人报警）＞ **换语言/换型号会不会放大** ＞ **改版式要不要动代码** ＞ **是否只是记录**。

## 总览

| # | 优先级 | 语义 | 欠账 | 症状 |
|---|---|---|---|---|
| 1 | **P0** | `HB-SAFETY-DANGER` | IDML 把 danger 降级成通用 warnbox 渲染器 | 安全等级在印刷件里被抹平 |
| 2 | **P0** | `HB-WARRANTY-YEARS` | 识别基于文本形状启发式 | 文案一改就可能认不出，卡片静默丢失 |
| 3 | **P0** | `HB-WARRANTY-SECTION` | 生产 IDML 没有显式的质保-section 组件类型 | 同上，且无处挂 token |
| 4 | **P0** | `HB-WARRANTY-LEAD` | IDML 只显式识别年限文本模式 | 引语段落靠邻接关系存活 |
| 5 | **P0** | `HB-TABLE-AUTO-RESUME` | 生产 IDML 没有显式的 auto-resume 表角色 | 退化成普通表，对比语义丢失 |
| 6 | **P1** | `HB-TITLE-L2` | 未强制共享的 keep-with-next 策略 | 标题与正文跨页分离 |
| 7 | **P1** | `HB-TITLE-L3` | 同上 | 同上 |
| 8 | **P1** | `HB-TYPE-LIST` | 语言密度列表覆盖未走类型化级联 | 长语种列表行距失准 |
| 9 | **P1** | `HB-TABLE-TROUBLESHOOTING` | 行下限、光学偏移、0.25pt 内线、0.57pt 外线、240pt 英文下限、导入余量共 6 项留作渲染器校准；`comp_trouble_step_indent`、`comp_trouble_section_needspace` 仅 LaTeX 生效 | 换语言重排时印刷侧与网页侧分叉 |
| 10 | **P1** | `HB-TABLE-SPEC` | IDML 行高与多行行为未完全 token 驱动 | 多行值撑格不一致；列宽已有 31%/0.315/33% 三值分叉 |
| 11 | **P2** | `HB-TITLE-L1` | IDML 自行推导 band 高度，未用 `comp_h1_pill_height` | 调胶囊高度改 token 不生效 |
| 12 | **P2** | `HB-CALLOUT-STRIP` | 变体几何与排版未完全 token 驱动 | 四种信号词的差异要改代码 |
| 13 | **P2** | `HB-SAFETY-WARNING` | IDML 可见几何仍含渲染器本地常量 | 同上 |
| 14 | **P2** | `HB-TABLE-SYMBOL-SIGNAL` | IDML 页面构成持有可见常量 | 版式调整要改代码 |
| 15 | **P2** | `HB-TABLE-SYMBOL-ICON` | 同上 | 同上 |
| 16 | **P2** | `HB-TABLE-LCD-MODE` | 专属几何仍在渲染器本地兜底里 | 同上 |
| 17 | **P2** | `HB-SPECIAL-OVERVIEW` | 目标特定的绝对几何未 token 化 | 每个型号手调坐标 |
| 18 | **P2** | `HB-SPECIAL-FCC` | IDML 用专门的绝对定位页面合成器 | 换页面结构要改合成器 |
| 19 | **P2** | `HB-SPECIAL-INBOX` | 同上 | 同上 |
| 20 | **P3** | `HB-TYPE-LEAD` | IDML 借正文或标题样式，没有独立 lead 样式 | 语义在印刷侧不可寻址 |
| 21 | **P3** | `HB-TYPE-FOOTER` | IDML 页脚借用规格注释样式 | 同上 |
| 22 | **P3** | `HB-TYPE-PAGE-NUMBER` | 专属 token 与 IDML 样式尚未共享 | 同上 |
| 23 | **P3** | `HB-PAGE-STANDARD` | 页码抑制仍用语义页角色，未进共享页计划 | 页计划不可单点审计 |
| 24 | **P3** | `HB-PAGE-NO-FOOTER` | IDML 页模板选择未体现在共享页计划里 | 同上 |
| 25 | **P3** | `HB-PAGE-COVER` | 封面是置入的成品美术；封底几何 InDesign 原生，文案来自共享 IR | 已知边界，非缺陷 |
| 26 | 记录 | `HB-TABLE-LCD-ICON` | 已批准的参考档拥有型号特定行高，共享排版与位置仍 token 驱动 | 状态 `aligned`，不是债 |

## P0 — 五条靠猜的语义（先修这批）

共同病根：**IDML 侧没有显式的组件类型，靠文本形状/邻接关系反推语义**。这类失败是静默的——认错时不报错，直接排成普通段落或普通表，只有人眼看成品才发现。目前没有任何护栏拦得住。

其中 `HB-SAFETY-DANGER` 排第一：它把最高安全等级降级成通用警告框，是合规面的问题，不只是版式问题。

建议做法一致：给这五个语义在 IDML 渲染器里建显式组件类型（对齐 `semantic_source_kinds`），识别从"猜文本"改成"读 IR 类型"。质保三条（2/3/4）应该一起做，它们共用同一段识别逻辑。

验收：改一次源文案（不改结构），重新生成 IDML，五个组件全部仍被识别；再刻意改文案措辞，仍被识别。

## P1 — 换语言就放大的五条

`HB-TITLE-L2` / `-L3` 的 keep-with-next 缺失，会在任意一次语言重排后产生孤立标题；`HB-TYPE-LIST` 的语言密度覆盖没有走类型化级联，长语种（FR/ES）行距会失准。这三条的共同点是：EN 下看不出问题，多语种一上就出现。

`HB-TABLE-TROUBLESHOOTING` 的六项校准常量与 `HB-TABLE-SPEC` 的行高，是印刷侧与网页侧最容易分叉的地方——规格表列宽已经分成 Web 31% / PDF 0.315 / Word 33% 三个值，就是这类欠账长出来的结果。

验收：拿 FR 或 ES 的目标各出一次 PDF 与 IDML，对同一页比对标题落位与列表行距。

## P2 — 九条"改版式必须改代码"

不会出错，但会拖慢每一次版式调整：token 改了不生效，得进渲染器改常量。`HB-SPECIAL-FCC` / `-INBOX` 用的是绝对定位页面合成器，`HB-SPECIAL-OVERVIEW` 每个型号手调坐标，这三条成本最高。

建议按"下次要动这块版式时顺手做"的节奏推，不单独立项。

## P3 — 六条结构性长期项

样式借用三条（`LEAD` / `FOOTER` / `PAGE-NUMBER`）与页计划三条（`PAGE-*`）。它们不影响当前成品，影响的是可审计性：语义在 IDML 里没有独立地址，就无法单点校验。等页计划这件事本身立项时一起做。

## 顺带：一处数据缺陷

`HB-TABLE-TROUBLESHOOTING` 的 `debt` 在 YAML 里是 flow 列表，而那句话本身含半角逗号，于是被切成了六个碎片项（`0.25pt inner rule`、`240pt English floor`…）。语义没错，但按条目统计会把一条债算成六条。

修它要注意：`manual_style.yaml` 的内容进 `style_contract_sha256`，改动后必须跑 `python tools/reference_layout_rebind.py` 重绑参考版式 pin，否则 `tools/check_reference_layout_pins.py` 会红。**不要顺手改**——把它并进下一次真正修这条债的改动里。
