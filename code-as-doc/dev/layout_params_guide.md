# Layout Params 调参说明（Phase1）

本文档基于 `data/layout_params.csv`，用于说明当前版面参数怎么调、先调哪些、如何避免误调。

适用范围：
- `phase1` 安全页（safety）与规格页（spec）排版
- 多语言（EN/FR/ES）当前实现

不适用范围：
- 非 `layout_params.csv` 管控的硬编码样式（见本文“非 CSV 参数”一节）

---

## 1. 参数生效链路

`data/layout_params.csv`  
-> `tools/csv_to_tex_params.py`  
-> `docs/renderers/latex/params.tex`（自动生成，禁止手改）  
-> `docs/renderers/latex/*.tex` 组件读取 `\csname HB<key>\endcsname`  
-> `tools/build_docs.py` 输出 PDF

关键原则：
- 改版面只改 `data/layout_params.csv`
- 不直接改 `docs/renderers/latex/params.tex`

---

## 2. 命名规范与单位规则

### 2.1 Key 前缀

- `page_`: 纸张、页边距、页脚
- `type_`: 字号、行距、大小写、颜色
- `comp_`: 组件结构参数（间距、圆角、边框、表格、列表）
- `brand_color_`: 颜色定义（CMYK）
- `lang_fr_` / `lang_es_`: 语言覆盖参数（FR/ES）

### 2.2 Unit（由 `tools/validate_layout_params.py` 校验）

允许值：
- `mm`, `pt`, `em`, `ex`, `ratio`, `int`, `none`, `cmyk`

解释：
- `ratio`/`int`/`none`/`cmyk` 会原样写入 TeX 宏（不自动拼单位）
- `mm`/`pt`/`em`/`ex` 会按长度单位参与排版

---

## 3. 参数分区速查（按“先调哪组”）

### 3.1 页面框架（全页）

优先看：
- `page_margin_*`, `page_footskip`
- `section_after_fix`（用于抵消 Sphinx 默认段后胶水）
- `page_footer_*`

适用场景：
- 整页内容上移/下移
- 页码位置、页脚大小不一致

### 3.2 文本系统（全局字面密度）

优先看：
- `type_body_*`
- `type_list_*`
- `type_warning_text_*`

适用场景：
- 内容“看起来挤/松”
- 列表过长导致跨页

### 3.3 Safety 页组件

优先看：
- 标题条：`comp_h1_pill_*`
- 副标题条：`comp_subbar_*`
- 警示框：`comp_warning_box_*`, `comp_lockup_*`
- 双栏块：`comp_twocol_sep`, `comp_twocol_tighten`, `comp_twocol_after`
- lead 行：`comp_lead_after`

适用场景：
- 警示框尺寸不对
- 双栏块和上文黏连/间隔过大
- 一页塞不下

### 3.4 列表圆点（Safety item）

优先看：
- `comp_list_bullet_symbol`
- `comp_list_bullet_raise`
- `comp_list_leftmargin`, `comp_list_labelsep`, `comp_list_itemsep`

适用场景：
- 圆点和文字不在一条视觉基线上
- 圆点太大/太小
- 列表层级缩进不对

### 3.5 Spec 页标题与表格

优先看：
- 小节标题：`comp_spec_section_before`, `comp_spec_section_after`
- 小节 bullet：`comp_spec_section_bullet_symbol`, `comp_spec_section_bullet_raise`, `comp_spec_section_bullet_gap`
- 表格结构：`comp_spec_table_left_ratio`, `comp_spec_table_tabcolsep`, `comp_spec_table_row_stretch`
- 表格线框：`comp_table_outer_rule`, `comp_table_inner_rule`, `comp_table_outer_arc`
- 注释区：`comp_spec_notes_before`, `comp_spec_footnotes_before`
- 规格页字号：`type_spec_*`

适用场景：
- 标题离上块太近/太远
- 表格太高导致分页
- 左右列比例不对、文字过于拥挤

---

## 4. 多语言覆盖规则（FR/ES）

规则：
- EN 走基础参数
- FR/ES 优先取 `lang_fr_*`/`lang_es_*`
- 若某覆盖 key 缺失，自动回退到基础 key

建议：
- 先把 EN 调到目标样式，再只为 FR/ES 加“密度类参数”
- FR/ES 优先调行距、段后距、表格行高，不要先动结构

当前覆盖重点：
- `lang_fr_*` / `lang_es_*` 已覆盖了 spec 标题间距、表格密度、spec 字号行距

---

## 5. 非 CSV 参数（避免误判）

以下样式当前不在 `layout_params.csv`：
- spec 表格左列底色深浅：在 `docs/renderers/latex/components_spec.tex` 的 `SpecLeftBg`（目前硬编码）
- 某些组件内部绘制细节（例如复杂 `tcolorbox` 画法）仍在 `.tex` 组件文件

含义：
- 若你只改 CSV，却发现某些视觉不变，先确认该项是否已参数化

---

## 6. 常见问题 -> 推荐先调参数

1. 标题下方空隙太大/太小（spec）
- 先调 `comp_spec_section_after`

2. 小节标题离上一块太近（spec）
- 先调 `comp_spec_section_before`

3. safety 列表圆点看起来“上浮/下沉”
- 先调 `comp_list_bullet_raise`（小步：`0.02ex`）

4. spec 小节 bullet 与标题不齐
- 先调 `comp_spec_section_bullet_raise`（小步：`0.02ex`）

5. 表格太“高”（一页塞不下）
- 先调 `comp_spec_table_row_stretch`
- 再调 `type_spec_*_font_leading`
- 最后调 `comp_spec_table_tabcolsep`

6. 表格边框视觉不对（粗细层级）
- 外框：`comp_table_outer_rule`（应大于内线）
- 内线：`comp_table_inner_rule`

7. FR/ES 版本容易分页
- 先加/调 `lang_fr_*` / `lang_es_*` 对应密度键，不要直接动 EN 基础值

---

## 7. 标准调参流程（建议团队统一）

1. 修改参数：
```bash
vi data/layout_params.csv
```

2. 参数校验：
```bash
python3 tools/validate_layout_params.py
```

3. 生成 TeX 参数：
```bash
python3 tools/csv_to_tex_params.py
```

4. 构建 PDF：
```bash
python3 tools/build_docs.py --no-open
```

5. 若怀疑旧产物干扰，清理后重建：
```bash
rm -rf docs/_build/latex
python3 tools/build_docs.py --no-open
```

---

## 8. 调参纪律（减少返工）

- 一次只改一组参数（如“spec 标题间距组”）
- 每次改动保留“参数名 + 原值 + 新值 + 目的”记录
- 视觉回归至少对比：
  - safety_en
  - safety_fr
  - spec_en
  - spec_fr
- 若同一问题需要改 `.tex`，先确认是否值得抽成新参数，再决定是否参数化

