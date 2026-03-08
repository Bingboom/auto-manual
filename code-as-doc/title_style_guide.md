# Title Style Guide

更新时间：2026-03-08

本文定义当前仓库中 `HTML / Word / LaTeX` 三条输出链路的标题样式来源、层级规则与维护方式。

## 1. 目标与原则

- 标题层级必须来自模板/内容语义，不允许在脚本里按标题文案硬编码分级。
- 三条链路（html/word/pdf）使用同一份 rst/csv 内容源，标题语义一致。
- LaTeX 样式由 `components_base.tex` 统一接管，页面组件仅做必要特化。

## 2. 标题层级规范

- 一级标题（H1）
  - 普通页面：RST `=` 标题（对应 `\section`）
  - safety/spec 模板页面：模板中显式 `h1`（HTML）和 `\section`（LaTeX）
- 二级标题（H2）
  - 普通页面：RST `-` 标题（对应 `\subsection`）
  - safety 子条：`OPERATING INSTRUCTIONS`（模板 `h2`）
  - spec 分节：`● GENERAL INFO` 等（模板 `h2` / LaTeX `\specsectiontitle`）
- 三级标题（H3）
  - RST rubric（LaTeX 对应 `\subsubsection`，由 `components_base.tex` 统一定义）

## 3. 样式来源矩阵

### 3.1 LaTeX（PDF 主链路）

核心文件：

- `docs/renderers/latex/components_base.tex`
  - 统一定义 `\section / \subsection / \subsubsection` 样式
  - H1 暗底胶囊（`\hbsectiontitle`）
- `docs/renderers/latex/components_safety.tex`
  - safety 专属组件（warning box、subbar、twocol）
  - 不再负责全局 section patch
- `docs/renderers/latex/components_spec.tex`
  - spec 专属分节标题与表格组件（`\specsectiontitle`）
- `data/layout_params.csv` -> `docs/renderers/latex/params.tex`
  - 控制字号、间距、颜色等参数（通过 `tools/csv_to_tex_params.py` 生成）

### 3.2 HTML（Sphinx HTML 与 Word bundle HTML）

核心文件：

- `docs/templates/*.rst`
  - 标题语义来源（普通页面 rst 标题 + safety/spec 模板内 `h1/h2`）
- `docs/_static/hb_manual.css`
  - 页面样式（`.hb-h1-pill`, `.hb-subbar`, `.hb-spec-section`）

### 3.3 Word（bundle 导出）

核心文件：

- `tools/word_bundle_html.py`
  - RST -> HTML 片段转换
  - 对普通 rst 顶层标题补回 `h1`
  - 内置一套 Word bundle CSS（需与 `hb_manual.css` 同步）
- `tools/word_bundle_docx.py`
  - 仅做通用 Heading outline 规范化（Heading1=>outline0, Heading2=>outline1）
  - 不允许根据标题文本做硬编码升级/降级

## 4. Spec 标题多语言维护

### 4.1 数据源

- `data/phase1/spec_titles.csv`（标题字典）

字段规范：

- `title_en`：主键 + 默认值
- `title_zh`：中文映射
- `title_jp`：日文映射
- 可扩展：`title_fr`, `title_es` ...

### 4.2 运行逻辑

- 解析器：`tools/phase1/renderers_spec_parser.py`
- 按 `title_en` 匹配页面标题与分节标题并映射到目标语言列
- 区域/语言选择逻辑：
  - JP 区域默认用 `title_jp`
  - CN/zh 默认用 `title_zh`
  - 其他默认 `title_en`
- 映射缺失时回退 `title_en`

## 5. 修改标题样式的标准流程

1. 先改语义（模板/rst）
- 确认标题层级由 rst 标题或模板 `h1/h2` 正确表达
- 禁止先改脚本后处理

2. 再改视觉（CSS/LaTeX 组件）
- HTML：改 `docs/_static/hb_manual.css`
- Word bundle：同步改 `tools/word_bundle_html.py` 内嵌 CSS
- LaTeX：优先改 `components_base.tex`（全局）；页面特化改 `components_safety.tex` / `components_spec.tex`

3. 最后改语言映射（如 spec）
- 在 `data/phase1/spec_titles.csv` 更新 `title_en -> title_xx`

## 6. 验证清单

### 6.1 单测

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

### 6.2 Spec 渲染

```bash
python3 tools/phase1_build.py --page spec --lang en --model JE-2000F --region US
python3 tools/phase1_build.py --page spec --lang en --model JE-2000F --region JP
```

检查：`docs/generated/JE-2000F/spec_en.rst` 中 `\section` 与 `\specsectiontitle` 是否符合预期。

### 6.3 Word 导航层级

```bash
python3 tools/gen_index_bundle.py --config config.ja.yaml --model JE-2000F --region JP
python3 tools/word_bundle.py --config config.ja.yaml --model JE-2000F --region JP --output docs/_build/word/manual_demo_ja.docx
```

检查 Word 导航窗格：

- H1：章节标题
- H2：章节子标题 / spec 分节

### 6.4 日语模板 Word 构建流程（`page_ja`）

输入源：
- RST 模板：`docs/templates/page_ja/*.rst`（含 `cover_jp.rst`）
- CSV 页面：`data/phase1/Spec_Master.csv` + `data/phase1/Spec_Footnotes.csv` + `data/phase1/spec_titles.csv`
- 页面编排：`config.ja.yaml -> pages`

执行顺序：
1. `tools/gen_index_bundle.py` 读取 `config.ja.yaml`，按 `pages` 生成 `docs/index.rst`。
2. `tools/word_bundle.py` 调用 `word_bundle_html.py`，解析 `rst_include/csv_page` 页面。
3. 遇到 `csv_page` 时触发 `phase1`，生成 `docs/generated/{model}/spec_ja.rst`。
4. `word_bundle_common.py` 从 `Spec_Master.csv` 按 `model + region + lang` 解析产品名，注入 `|PRODUCT_NAME|` 与 `|PRODUCT_NAME_BOLD|`。
5. `word_bundle_docx.py` 将 bundle HTML 转为 DOCX，并做通用 heading outline 规范化。

标准命令：

```bash
python3 tools/word_bundle.py --config config.ja.yaml --model JE-2000F --region JP --output manual_demo_ja.docx
```

产物：
- `docs/_build/word/manual_demo_ja.docx`

维护约束：
- 禁止在脚本里按标题文案硬编码层级；标题层级仅由 RST/模板语义决定。
- `page_ja` 与 `page_en` 仅做语言内容差异，样式继承同一套 `components_base.tex` 与 Word/HTML 样式体系。

## 7. 禁止事项

- 禁止在 `word_bundle_docx.py` 按具体标题文案做 if/else 强制分级。
- 禁止在不同链路使用不同内容源导致标题不一致。
- 禁止只改 Word 视觉而不改 HTML/LaTeX 对应样式，造成跨格式漂移。

## 8. 变更影响面提醒

标题相关改动通常会影响以下文件：

- `docs/templates/*.rst`
- `docs/_static/hb_manual.css`
- `tools/word_bundle_html.py`
- `docs/renderers/latex/components_base.tex`
- `docs/renderers/latex/components_safety.tex`
- `docs/renderers/latex/components_spec.tex`
- `data/phase1/spec_titles.csv`（spec 多语言标题）

提交前必须至少完成：

- 单测通过
- 至少一个 `US` 与一个 `JP` 的 Word/Spec 产物验证
