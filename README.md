## 项目是什么

这是一个“CSV 驱动的安全手册生成器”。内容与版式都尽量参数化，通过 CSV 配置 + LaTeX 模版，生成固定版式的 PDF。

## 工作流程（pipeline）

1. **内容生成（RST）**

   * 输入：`data/safety_items.csv`
   * `tools/csv_to_rst.py` 会把 CSV 里的内容按 `part`（top/bottom/lead_top/save_title）分块，渲染到 `docs/templates/safety_template.rst` 中。
   * 输出：`docs/safety.rst`（作为 Sphinx/LaTeX 的主体内容）
2. **版式参数生成（TeX macros）**

   * 输入：`data/layout_params.csv`
   * `tools/csv_to_tex_params.py` 会把布局参数转成 `docs/latex_theme/params.tex`，定义形如 `\csname HB<key>\endcsname` 的 TeX 宏。
   * LaTeX 主题在 `docs/latex_theme/`（`components*.tex`、`layout.tex`、`theme.tex`）里大量使用这些宏来控制纸张、边距、字号、组件盒子形状（pill/warning box/两栏 list/table/note 等）。
3. **构建 PDF**

   * 用 Sphinx + 自定义 LaTeX 主题构建最终 PDF（典型输出路径在 `docs/_build/latex/` 下面）。

「CSV 中 TeX 值的转义约定」：

* **TeX 命令请用单反斜杠**
* **只有想输出 TeX 的换行 `\\` 时才写双反斜杠**
* 不要按“Python 字符串”思维去写 CSV（CSV 不是 Python 字符串字面量）
