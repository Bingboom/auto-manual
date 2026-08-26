# 共享样式与完整组件应用指南

本文回答一个具体问题：**已有 JE-1000F 样式或完整组件时，新型号、新语言或新页面
怎样直接复用，而不是在页面里再画一遍。**

本文是操作指南，不是第二份样式规范：

- 视觉意图、四端绑定和不变量以
  [`STYLE_DEFINITION.md`](../../docs/renderers/contracts/STYLE_DEFINITION.md) 为准；
- 稳定语义与 renderer binding 以
  [`manual_style.yaml`](../../docs/renderers/contracts/manual_style.yaml) 为准；
- 数值以 [`data/layout_params.csv`](../../data/layout_params.csv) 为准；
- 本文只规定如何找到、调用、扩展和验收现有样式或组件。

## 1. 先判断这次改动属于哪一种

| 需求 | 应该改哪里 | 不应该做什么 |
|---|---|---|
| 新型号使用相同视觉块 | 复用现有完整组件，只提供新型号的数据和外部矩形 | 复制 JE 页面代码、重读内部 token、按型号新增 renderer |
| 新语言 | 补文案、语言 token 或内容容量回归 | 复制一套法语/西语绘制函数，按标题文字识别组件 |
| 已登记的 `standard` / `compact` 变体 | 由调用方选择 variant，组件内部解析其全部几何 | 在页面编排器里重新定义行高、列宽、底色或间距 |
| 真正的新视觉变体 | 先登记语义/variant/token，再扩展同一个组件和回归基准 | 用页码、型号、语言或标题字符串触发坐标补丁 |
| 修改共享视觉 | 按样式规范附录 A 修改权威源和所有适用投影 | 只改一个生成物或最终化脚本，把差异隐藏在后处理里 |

判断顺序固定为：

1. 在样式规范 §1 找到对应 `HB-*` 语义。
2. 在本表和 [`idml_module_map.md`](idml_module_map.md) 找到已有公共组件入口。
3. 确认需求是数据变化、语言容量变化、批准 variant，还是共享视觉变化。
4. 只有前三项都不能表达需求时，才设计新组件或新 variant。

## 2. 完整组件的硬边界

跨产线视觉块必须只有一个可见几何写入者：**完整组件**。

```text
页面编排器
  └─ 传入：语义数据、语言、批准的 density/variant、可用矩形、z-order
       └─ 完整组件
            ├─ 拥有：底色、圆角、列宽、行高、内边距、内部间距
            ├─ 拥有：内容 fitting、溢出/续页策略、原生载体空间
            └─ 调用：只执行既定几何的底层 primitive

最终化脚本
  └─ 只处理组件明确暴露的不可见载体；不得改可见内部对象
```

页面编排器可以决定组件的 `x / y / width / available_height`，也可以决定多个完整
组件在一页上的先后顺序。它不能读取组件内部 token，不能创建组件内部 story、cell、
plate、mask、outline，也不能按语言修改内部坐标。

“调用了同名函数”不等于完成复用。只要页面、primitive 或 InDesign 最终化还可以
二次修改行高、外壳或载体空间，这个视觉块就仍然有多份定义。

## 3. 已有组件怎样调用

| 视觉块 | 公共入口 | 调用方可传入 | 组件必须自己拥有 | 明确禁止 |
|---|---|---|---|---|
| Symbols | `SymbolsPanel` + `SymbolsPanelData` | 数据、语言、`standard` / `compact`、外部矩形 | 标题、两类表、底色、圆角、列宽、行高、表间距、续页、透明载体 | 页面调用 Symbols 私有表格函数或读取 `symbols_*` 内部几何 token；最终化改 shell/plate/mask/row |
| LCD 表 | `writer.add_lcd_story(...)`；页面入口 `add_lcd_operations_page(...)` | 行数据、语言、批准 profile、外部 story frame | 列、行、图标、可见 shell、透明终止载体 | 给主表框加“终止标记余量”；最终化读取表高后拉伸主框或圆角对象 |
| Troubleshooting | production block 流进入 `render_table_block(...)` | 两列表数据、语言、外部 flow/frame | 本地化行 minima、列宽、垂直居中、底色、圆角 shell、透明终止载体 | 页面直接调用 `_troubleshooting_*` 私有 helper；给末行或外壳补白；最终化改可见表框 |
| Storage | `StoragePanelData.from_blocks(...)` + `StoragePanel.render()` | H1/正文 blocks、语言、外部 story frame | 复用 JE 的 inline H1 + prose story；不创建独立卡片 | JBP 另建灰底正文卡、独立标题 story、圆角、inset 或基线补丁 |
| Specifications | `writer.add_spec_story(...)` | 规格 sections、annotations、语言、批准 layout variant、外部 frame | 分节标题、行高、AutoGrow 规则、列宽、圆角 shell、脚注与 portable symbol | 页面设置逐表固定 shell 高度、把余量塞进末行、按标题单独调圆点/基线 |
| Charging 尾部胶囊标题 | `add_charging_page(...)` → `HeadingPill` 的 `charging` variant | blocks、语言、语义 image role、批准 suffix 索引、外部 frame | 图→标题节奏、标题/胶囊字面宽度、两列间可见间距 | 叠加普通图后距和普通 H2 前距；右对齐胶囊；在页面重分两列 |
| H1 | 共享 `heading_text` + `h1_frame_opts`，通常由所属完整组件调用 | 标题语义和组件外部矩形 | 字面基线、标题框内部边界、共同字体/leading | 页面以 Y 偏移、型号分支或独立 text rectangle 重建内部基线 |

`render_table_block(...)` 是 Troubleshooting 在 block renderer 内的公共边界，不是
给页面编排器绕过生产流直接拼表的邀请。生产页应继续从准备好的 RST → block stream
→ prose/table renderer 进入它。

### 3.1 Symbols：页面只放置完整面板

```python
panel = SymbolsPanel(
    writer,
    sid=sid,
    data=SymbolsPanelData(...),
    bundle_root=bundle_root,
    language=language,
    density="compact",
).render(
    x=x,
    y=y,
    width=width,
    available_height=available_height,
)
```

调用完成后，页面只能使用返回的 story / continuation 结果继续编排；不得再拿
`panel_metrics()` 的行高给 shell、底板或遮罩做第二次调整。

### 3.2 Storage：使用 JE 的同一条 H1 + prose 内容流

```python
panel = StoragePanel(
    writer,
    sid=sid,
    data=StoragePanelData.from_blocks(storage_blocks),
    bundle_root=bundle_root,
    language=language,
).render()
writer.add_story_frames(panel.story_id, [(page_index, top, bottom)])
```

这里的 `top / bottom` 是完整 story 的外部矩形，不是允许调用方为标题和正文分别
定义坐标。Storage 适配器故意不提供 fill、radius、inset 或 title-frame 参数。

### 3.3 Charging：页面选择语义 variant，不传内部间距

`add_charging_page(...)` 从 target composition 读取 `image_role` 和
`h2_suffix_pill_indices`，把目标 H2 提升为 `HeadingPill(variant="charging")`。页面
不接收图后距、H2 前距、标题列宽或胶囊宽度；这些值属于共享组件。

## 4. 透明终止载体的统一模式

IDML 文本故事可能需要为原生终止标记保留极小空间。这个空间是**排版载体**，不是
视觉内容，必须与可见 shell 分离：

1. 组件先计算可见行高，并让主文本框、底色、遮罩和圆角外框精确结束在行高总和。
2. 组件通过 `terminal_carrier_height` 创建串接在主文本框之后的透明 frame。
3. 透明 frame 使用稳定标签 `tf_terminal_carrier_group_*`，且 fill/stroke 均为 None。
4. 最终化脚本如需容纳终止标记，只能扩展这个载体。
5. 最终化不得查询原生表高后修改主框、plate、mask、outline 或任何 row。

禁止用三种“看似快速”的办法：给最后一行加高、给可见 shell 加 1pt、在底部补一块
与底色相同的矩形。三者都会把内部排版问题伪装成视觉修补，并在下一语言或下一次
InDesign 重排时重新露白。

## 5. 新型号、新语言和新变体的接入方法

### 5.1 新型号，视觉相同

- 复用同一个公共入口；型号差异只进入数据、资产和批准 composition 配置。
- 搜索页面代码，确认没有新增型号名、标题文字或页码判断。
- 边界测试应拒绝页面读取组件内部 token 或私有 helper。
- 使用现有 EN/FR/ES fixture 运行同一组件路径；不得只截图英文。

### 5.2 新语言

- 先补稳定语义数据和真实本地化文案，再确认内容是否超过当前容量。
- 容量差异优先走 `lang_<code>_*` token 或内容测量，不复制 renderer。
- 同时检查字形、换行、行高、垂直居中、溢出和透明载体。
- 新语言通过后，把它加入同一组件回归矩阵；不要创建语言专属 golden 逻辑。

### 5.3 新 density / variant

- 先在机器合同登记 variant 的适用范围、理由和 token role。
- variant 只能选择完整组件内部的一组合同；不能把内部几何字段暴露给页面。
- standard 与新 variant 必须共享填色、对齐、载体和最终化边界等不变量。
- deliberate golden 变化要先审核可见差异，再更新基准，不能用重生成消除失败。

### 5.4 真正修改共享样式

按 [`STYLE_DEFINITION.md` 附录 A](../../docs/renderers/contracts/STYLE_DEFINITION.md#附录-a-组件与维护流程)
执行：先改权威语义/token，再改适用 renderer 和直接测试，最后同步规范与本指南。
不要先在输出 IDML、`docs/_build/` 或 JSX 最终化里调到“看起来对”。

## 6. 验收：完成的定义不是“构建成功”

每次复用或调整至少逐项确认：

- [ ] 调用的是完整组件公共入口，不是低层 primitive 或私有 helper。
- [ ] 页面只传数据、语言、批准 variant/density 和外部矩形。
- [ ] 页面没有读取内部行高、列宽、底色、圆角、inset、基线或间距 token。
- [ ] EN/FR/ES 走同一实现，并覆盖适用的 `standard` / `compact`。
- [ ] 可见 shell 精确包住可见内容；最后一行无白带、无补色块、无异常增高。
- [ ] 行内容原生垂直居中；不是靠逐行 `BaselineShift` 补齐。
- [ ] 透明终止载体与可见对象分离，最终化只处理载体。
- [ ] 无 overset、缺字、缺图和坏链接。
- [ ] 与批准 JE/reference 页面做了同页截图或渲染对比，而不是只看新产线自身。
- [ ] deliberate 视觉变化有明确差异记录；ownership-only 重构不随意刷新 golden。

常用验证梯度：

```bash
python -m unittest \
  tests.test_idml_symbols_panel \
  tests.test_idml_troubleshooting_table \
  tests.test_idml_fixed_panel_golden \
  tests.test_export_idml \
  tests.test_indesign_finalize
python tools/check_doc_link_integrity.py
```

涉及可见 IDML 几何或最终化行为时，直接测试之后还必须用真实 InDesign 导出
EN/FR/ES，并检查 PDF 页面与 preflight；XML 结构通过不能替代视觉验收。

## 7. 代码评审时直接拒绝的形态

- `if model == ...`、`if page_number == ...` 或按本地化标题决定样式。
- 页面编排器 import 组件私有 helper、metrics 或内部 token。
- 同一组件在 `standard` / `compact` 下分别复制渲染实现。
- 用末行增高、底部补色或额外可见矩形掩盖白带。
- 最终化脚本遍历并拉伸可见 table frame、plate、mask 或 outline。
- 只做英文截图，或只证明“无报错”而不做批准模板对比。
- 已有 JE 完整组件，却为 JBP 再建标题 story、灰底卡或独立基线。

发现以上任一项，应回到完整组件边界解决，而不是接受“先把这一页调好”的补丁。
