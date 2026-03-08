# Auto-Manual Tool

基于 CSV + RST 的说明书构建仓库。  
当前主流程是：`phase1 -> 生成 index.rst -> Sphinx LaTeX -> XeLaTeX PDF`，并支持多种 DOCX 导出。

## 1. 先看结论（当前真实逻辑）

- 主入口：`tools/build_docs.py`
- `docs/index.rst` 不建议手改；每次构建会由 `tools/gen_index_bundle.py` 覆盖生成
- `config.yaml` 的 `pages` 决定整本页面顺序
- `pages` 已有 dataclass schema（`tools/config_pages.py`），构建入口不再直接裸读字典
- `csv_page` 目前只支持 `source: phase1`
- 默认 `doc_type` 只支持 `manual_bundle`
- 构建目标解析（model/region/token）已统一收敛到 `tools/utils/targets.py`
- `spec` 页 `product_name` 按 `Model + Region + Language` 从 `Spec_Master.csv` 解析
- `renderers` 与 `word_bundle` 已拆分为多模块（P1）

---

## 2. 快速开始

### 2.1 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

系统依赖：

- PDF 必需：`xelatex`（TeX Live / MiKTeX）
- DOCX 需要：
  - `word_source=latex` 或 `word_source=html`：必需 `pandoc`
  - `word_source=bundle`：
    - Windows：走 Word COM（可不依赖 pandoc）
    - macOS/Linux：走 pandoc

如果你要显式构建 HTML（`build.build_html: true`），请确保安装 `furo` 主题：

```bash
pip install furo
```

### 2.2 生成 LaTeX 参数（首次构建前建议执行）

```bash
python3 tools/csv_to_tex_params.py
```

说明：

- 输入：`data/layout_params.csv`
- 输出：`docs/renderers/latex/params.tex`
- `tools/build_docs.py` **不会**自动重建 `params.tex`
- `make clean` 会删除 `docs/renderers/latex/params.tex`

### 2.3 构建整本（推荐）

```bash
python3 tools/build_docs.py --model JHP-2000A --region US --clean --no-open
```

或：

```bash
make build-noview MODEL=JHP-2000A
```

---

## 3. build_docs 实际执行顺序

`tools/build_docs.py` 真实顺序如下：

1. 读取并校验 `config.yaml`
2. 校验 `paths.layout_params_csv`（默认 `data/layout_params.csv`）
3. 按 `Model + Region + Language` 从 `Spec_Master.csv` 解析 `Row_key=product_name`（即 `Product Name` 对应值）
4. 将 `|PRODUCT_NAME|` / `|PRODUCT_NAME_BOLD|` 注入 `rst_epilog`
5. 收集 `pages` 中的 `csv_page`，调用 `tools/phase1_build.py`
6. 调用 `tools/gen_index_bundle.py` 生成 `docs/index.rst`
7. 按配置决定是否构建 HTML
8. 固定构建 LaTeX（`sphinx-build -b latex`）
9. 调用 `tools/patch_latex_fonts.py` 注入 `fonts.tex`
10. 多轮运行 `xelatex`
11. 按 `build.word_source` 导出 DOCX（可选）

补充：`build_docs.py` 调用 `validate_config` 时使用的是 `strict_files=False`，  
所以像 `cover_pdf/rst_include` 的文件存在性不会在这一步强校验，而是在后续阶段暴露问题。

可视化：

```mermaid
flowchart TD
  A[config.yaml] --> B[tools/build_docs.py]
  B --> C[validate_config]
  B --> D[validate_layout_params]
  B --> E[tools/phase1_build.py]
  E --> F[docs/generated/<model>/*.rst]
  B --> G[tools/gen_index_bundle.py]
  G --> H[docs/index.rst]
  H --> I[sphinx-build -b latex]
  F --> I
  I --> J[docs/_build/latex/*.tex]
  B --> K[tools/patch_latex_fonts.py]
  J --> K
  K --> L[xelatex x N]
  L --> M[docs/_build/latex/<main_tex_stem>.pdf]
  B --> N[DOCX export (optional)]
```

---

## 4. 配置关键项（`config.yaml`）

`build_docs.py` 直接依赖的关键字段：

- `build.default_model`（推荐）
- `build.default_region`（推荐）
- `build.main_tex`
- `build.output_pdf`
- `build.xelatex_runs`
- `build.build_word`
- `build.word_source`：`latex | html | bundle`
- `build.word_output`
- `build.word_reference_doc`（主要用于 bundle）
- `build.build_html`
- `build.open_pdf / build.open_word / build.open_html`
- `paths.layout_params_csv`
- `paths.spec_master_csv`
- `paths.spec_footnotes_csv`（可空字符串，表示不加载脚注补充 CSV）
- `tools.patch_fonts`
- `pages`（页面顺序与来源）

注意：

- `--no-open` 会覆盖 `open_pdf/open_word/open_html`
- `doc_type` 当前仅支持 `manual_bundle`，其他值会报错

---

## 5. 构建目标解析逻辑（build_docs 与 gen_index_bundle 一致）

优先级：

1. 命令行 `--model` / `--region`
2. 若命令行未传，则使用 `build.default_model` / `build.default_region`

说明：

- 构建目标仅由 `model` / `region` 决定
- `product_name` 由 `Spec_Master.csv` 中 `Row_key=product_name` 的行解析（通常该行 `Row_label` 为 `Product Name`）

实现说明（P0 已完成）：

- `build_docs.py`、`gen_index_bundle.py`、`word_bundle.py` 都复用 `tools/utils/targets.py`
- token 检测与 `build.default_model/default_region` 解析语义已统一
- 结论：三个入口脚本对 target 选择策略保持一致，减少分叉行为

---

## 6. 页面类型与约束（pages DSL）

支持类型：

- `cover_pdf`
- `csv_page`
- `pdf_insert`
- `rst_include`

当前约束：

- `csv_page.source` 仅支持 `phase1`
- `rst_include` 直接 include 指定 rst
- `docs/index.rst` 每次由 `gen_index_bundle.py` 重写
- `pages` 解析统一走 `tools/config_pages.py`（`CoverPdfPage/CsvPage/PdfInsertPage/RstIncludePage`）

---

## 7. Phase1 真实数据来源

默认路径：

- 页面定义：`data/phase1/page_registry.csv`
- 默认块：`data/phase1/content_blocks.csv`
- 每页块覆盖：`data/phase1/<page_id>_blocks.csv`（如存在则优先）

当前说明：

- `phase1` 不再读取 `product_variables.csv`
- 渲染变量来源为构建参数（`--model/--region`）与 `Spec_Master.csv` 解析出的 `product_name`
- `docs/templates/*.rst`（除 `safety_template.rst/spec_template.rst`）若需要产品名，统一使用：
  - `|PRODUCT_NAME|`
  - `|PRODUCT_NAME_BOLD|`

每页块数据优先级：

1. 若存在 `data/phase1/<page_id>_blocks.csv`，优先使用该页文件
2. 否则回退到 `content_blocks.csv` 里 `page_id=<page_id>` 的块

`spec` 页特殊逻辑（当前已改为单一来源）：

1. 主数据仅使用 `paths.spec_master_csv`
2. 脚注补充仅使用 `paths.spec_footnotes_csv`（可为空禁用）

渲染器限制：

- 当前注册渲染器只有：`safety`、`spec`、`symbols`
- 若 `csv_page` 指向未注册渲染器，默认会直接报错

---

## 8. DOCX 导出模式（`build.word_source`）

### 8.1 `word_source=latex`

- 输入：`docs/_build/latex/<main_tex>`
- 工具：pandoc
- 优点：接近 LaTeX 排版结果

### 8.2 `word_source=html`

- 输入：`docs/_build/html/index.html`
- 工具：pandoc
- 若 `build_html=false` 但选择 html 导出，脚本会临时用 `alabaster` 最小主题构建 HTML（避免对 `furo` 强依赖）

### 8.3 `word_source=bundle`

- 输入：`pages` 重新拼接生成的 `docs/_build/word/manual_bundle.html`
- `csv_page`：先走 phase1 生成 `docs/generated/<model>/<page>_<lang>.rst`，再读取该 RST 转 HTML
- `rst_include`：读取配置中的 RST 文件转 HTML
- 结论：`html / pdf / word(bundle)` 都基于同一份 `csv_page -> generated rst` 内容源
- 不支持：`pdf_insert`
- 参考模板：`build.word_reference_doc`
  - 支持通配符路径（取排序后的第一个匹配）
- 额外后处理：
  - 导出后会强制补齐 Word 大纲级别（`Heading1/Heading2` 对应 `outlineLvl 0/1`），确保导航层级稳定

---

## 9. 输出文件

- LaTeX 主文件：`docs/_build/latex/<main_tex>`
- PDF：`docs/_build/latex/<output_pdf>`
- DOCX：`docs/_build/word/<word_output>`
- Word bundle HTML：`docs/_build/word/manual_bundle.html`

---

## 10. 命令速查

校验：

```bash
make validate
```

等价：

```bash
python3 tools/validate_config.py --config config.yaml
python3 tools/validate_layout_params.py --csv data/layout_params.csv
```

仅跑 phase1：

```bash
python3 tools/phase1_build.py
python3 tools/phase1_build.py --model JHP-2000A --region US --page safety,spec --lang en --spec-master-csv data/phase1/Spec_Master.csv --spec-footnotes-csv data/phase1/Spec_Footnotes.csv
```

仅重建 index：

```bash
python3 tools/gen_index_bundle.py --config config.yaml --model JHP-2000A --region US
```

单独导出 Word bundle：

```bash
python3 tools/word_bundle.py --config config.yaml --model JHP-2000A --region US --output manual_demo_en.docx
```

---

## 11. 常见失败点与排查

- `xelatex not found`  
  安装 TeX Live/MiKTeX，并保证 `xelatex` 在 PATH 中

- `config uses unsupported '{sku}' token`  
  把配置中的 `{sku}` 改为 `{model}` 或 `{region}`

- `Word reference doc not found`  
  检查 `build.word_reference_doc` 路径或通配符是否匹配到文件

- `No content blocks for page_id=...`  
  检查 `content_blocks.csv` 或 `<page_id>_blocks.csv`

- `missing renderer for page_id=...`  
  该 `csv_page` 没有注册渲染器（当前只保证 `safety/spec/symbols`）

- `File params.tex not found`  
  先执行 `python3 tools/csv_to_tex_params.py`

- `build_html=true` 时提示主题不存在（如 `furo`）  
  安装主题，或改用 `word_source=html + build_html=false` 的最小主题路径

- `PDF not found: docs/_build/latex/<output_pdf>`  
  `output_pdf` 需与 `main_tex` 对应产物一致（例如 `main_tex: manual_demo.tex` 时默认产物是 `manual_demo.pdf`）

---

## 12. 当前仓库默认配置（供快速对照）

以当前 `config.yaml` 为准：

- `build.default_model: JHP-2000A`
- `build.default_region: US`
- `build.main_tex: manual_demo.tex`
- `build.output_pdf: manual_demo.pdf`
- `build.xelatex_runs: 3`
- `build.build_word: true`
- `build.word_source: bundle`
- `build.word_output: manual_demo_en.docx`
- `build.build_html: false`
- `paths.spec_master_csv: data/phase1/Spec_Master.csv`
- `paths.spec_footnotes_csv: data/phase1/Spec_Footnotes.csv`

如果你改了这些值，请以你的 `config.yaml` 为最终事实来源。

---

## 13. 维护规范与仓库卫生（P0/P1）

规范文档：

- 代码规范主文档：`code-as-doc/code_style_guide.md`
- 本次 P0 优化记录：`code-as-doc/code_optimization_log.md`
- 文档维护规范：`code-as-doc/code-as-doc.md`

P1 结构优化（已完成）：

- `tools/phase1/renderers.py` 已拆分为：
  - `tools/phase1/renderers_common.py`
  - `tools/phase1/renderers_safety.py`
  - `tools/phase1/renderers_spec.py`
  - `tools/phase1/renderers_spec_parser.py`
  - `tools/phase1/renderers_symbols.py`
- `tools/word_bundle.py` 已拆分为：
  - `tools/word_bundle_common.py`
  - `tools/word_bundle_html.py`
  - `tools/word_bundle_docx.py`
- `config/pages` schema 已 dataclass 化：`tools/config_pages.py`

仓库卫生规则：

- `docs/_build/`、`docs/generated/`、`__pycache__/`、`.DS_Store` 已加入 `.gitignore`
- 这些目录/文件属于构建产物或缓存，不应进入版本库
- 如果后续发现再次被追踪，先检查 `.gitignore`，再执行 `git rm --cached <path>`
