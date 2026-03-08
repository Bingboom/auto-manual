# Spec Master User Guide

本文说明 `Spec_Master.csv` 在当前仓库构建链路中的作用，并明确哪些字段是“构建 Word 时必备”的。

## 1. `Spec_Master.csv` 在构建链路中的作用

当前 `spec` 页数据来源是**单一配置源**（代码：`tools/phase1/builder.py`）：

- 主表：`config.yaml -> paths.spec_master_csv`
- 脚注补充（可选）：`config.yaml -> paths.spec_footnotes_csv`

当前仓库默认配置：

```yaml
paths:
  spec_master_csv: tools/Draft-tool/data/Spec_Master.csv
  spec_footnotes_csv: tools/Draft-tool/data/Spec_Footnotes.csv
```

整体链路：

1. `tools/build_docs.py` 调用 `tools/phase1_build.py`
2. `Phase1Builder._load_page_blocks(page_id="spec")` 读取 `Spec_Master.csv`
3. `tools/phase1/renderers.py::collect_spec_content()` 识别 Spec_Master schema 并解析
4. 生成 `docs/generated/<model>/spec_<lang>.rst`
5. 构建 PDF / DOCX
   - `word_source=latex/html`：间接使用这份 `spec_<lang>.rst`
   - `word_source=bundle`：`tools/word_bundle.py` 也先触发/复用 phase1 生成，再读取同一份 `spec_<lang>.rst`

结论：`paths.spec_master_csv` 指向的 `Spec_Master.csv` 是 `spec` 页面（含 Word 规格页）内容的单一事实来源。

## 2. 构建 Word 的必备字段

注意：这里说的“必备”是按当前代码真实规则定义，不是业务约定。

### 2.1 硬必备（表头级，缺失会导致无法按 Spec_Master 模式解析）

`Spec_Master.csv` 必须包含以下列名（大小写敏感）：

- `Section`
- `Row_key`
- `Line_order`

如果你启用了 `--model` / `build.default_model` 的按型号构建，建议在主表增加并填写：

- `Model`（例如 `JHP-2000A`）

原因：

- `Phase1Builder` 和 `renderers` 都用这 3 列判断是否属于 Spec_Master schema。
- 如果缺失，会退回其他 schema 路径，通常会导致 `spec` 页无有效内容或构建失败。

### 2.2 行级必备（没有就会被丢行；全丢会报错）

每一条要进入 Word 规格表格的“数据行”，至少要满足：

1. `Section` 非空
2. `Row_key` 非空
3. 能得到行左侧标签 `row_label`（三选一）
   - `Row_label_<lang>`（如 `Row_label_en`）
   - `Row_label_en`
   - `Row_key`（兜底）
4. 能得到行右侧内容 `line_text`（两种路径二选一）
   - 直接提供：`line_text_<lang>` / `line_text_en` / `line_text`
   - 或拼接提供：
     - `Param_<lang>` / `Param_en` / `Param_name`
     - `Value_<lang>` / `Value_en` / `Spec_Value`
     - 解析器会按 `Param + sep + Value` 或仅 `Value/Param` 组装

如果某行缺少 `row_label` 或 `line_text`，该行会被跳过。  
如果最终所有数据行都被跳过，会报错：

- `spec page has no usable Spec_Master rows for sku=... lang=... [model=...]`

### 2.3 推荐必填（不是硬必备，但强烈建议）

- `Section_order`：控制章节排序
- `row_order` / `Row_order`：控制行排序
- `Line_order`：控制同一行多行值顺序（虽然表头硬必备，但值也建议规范填写数值）
- `page_title_<lang>`：控制 `SPECIFICATIONS` 主标题（否则用默认）
- `section_title_<lang>`：控制章节显示名（否则回退到 `Section`）

## 3. 会影响“是否出现在 Word 里”的过滤字段（可选但高风险）

这些字段不是必填，但如果填错，行会被过滤掉：

- `Is_Latest` / `is_latest`：仅保留 truthy 行
- `enabled`：仅保留 truthy 行
- `sku_scope`、`sku_id`：按 SKU 过滤
- `project_code` / `项目代码`：与 `product_variables.csv` 的变量匹配
- `Region` / `region`：与变量匹配
- `Model` / `model`：当构建目标传入 model 时按 model 精确过滤（建议在主表显式填写）
- `Page` / `page`：若存在，必须是 `spec` 或 `specifications`
- `row_kind` / `Row_kind` / `kind`：
  - `data`（默认）进入规格表
  - `note` 进入 notes
  - `footnote` 进入 footnotes
  - `title` 不进数据表

## 4. `Spec_Footnotes.csv` 与 Word 的关系

`Spec_Footnotes.csv` 不是构建 Word 规格表格的硬必需。  
它用于补充 `notes/footnotes` 文本，最终显示在规格表后。

常见字段（建议）：

- `row_kind`：`note` 或 `footnote`
- `note_text_<lang>`（note 场景）
- `footnote_mark` + `footnote_text_<lang>`（footnote 场景）
- 可配合 `enabled` / `sku_scope` / `Is_Latest` 使用

## 5. 最小可用样例（可用于验证 Word 构建）

下面是一个最小可工作的 `Spec_Master.csv`（English）示例：

```csv
Section,Section_order,Row_key,Row_label_en,Line_order,Param_en,Value_en
GENERAL INFO,1,product_name,Product Name,1,,Jackery HomePower 2000 Plus v2
GENERAL INFO,1,model_no,Model No.,1,,JHP-2000A
```

说明：

- 这份样例满足硬必备表头（`Section, Row_key, Line_order`）
- 行级可用（`Row_label_en` + `Value_en`）
- `Param_en` 可留空

## 6. 快速自检命令

只验证 spec 页面渲染：

```bash
python3 tools/phase1_build.py --model JHP-2000A --page spec --lang en
```

查看产物：

```bash
ls docs/generated/JHP-2000A/spec_en.rst
```

完整构建（含 Word）：

```bash
python3 tools/build_docs.py --model JHP-2000A --clean --no-open
```

如果失败，优先检查：

1. `Spec_Master.csv` 是否包含硬必备表头
2. 数据行是否能生成 `row_label` 和 `line_text`
3. 过滤字段（`Is_Latest/enabled/sku_scope/Region/project_code/Model/Page`）是否把行全部过滤掉
