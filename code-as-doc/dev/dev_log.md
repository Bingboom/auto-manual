date：2026-03-01

1. 仓库清理（只保留 phase1 主路径）
   * 已清理/不存在：**demo_data**、**output**、**snapshots**、**latex_theme**、旧 **docs/safety*.rst**、**docs/overview.rst**。
   * 当前文档入口保留为 phase1 生成流（**docs/generated/...** + **docs/index.rst**）。
2. 新增并接入 **spec** 页面组件链路
   * 新增规格页组件文件：[components_spec.tex](app://-/index.html?hostId=local#)
   * 主题接入：[theme.tex](app://-/index.html?hostId=local#)
   * Sphinx 额外文件接入：[conf_base.py](app://-/index.html?hostId=local#)
   * 渲染器切换到组件化 spec 输出：[renderers.py](app://-/index.html?hostId=local#)
3. **layout_params.csv** 参数体系扩展与精调
   * 新增 spec 专属参数组（标题间距、bullet、表格比例/密度、notes/footnotes、spec 字体行距）。
   * 新增 FR/ES spec 覆盖参数（密度与字号行距）。
   * 调整列表/标题 bullet 的基线参数（含 safety 与 spec 解耦）。
   * 文件：[layout_params.csv](app://-/index.html?hostId=local#)
   * 同步生成文件：[params.tex](app://-/index.html?hostId=local#)
4. 排版细节修正（按你的截图迭代）
   * spec 表格改为单线风格、外框/内线层级、左列灰底、圆角框一致性。
   * 标题前后间距、bullet 大小/间距、行高和一页内收敛都做了多轮调参。
   * safety 列表 bullet 与 spec 标题 bullet 分离控制，避免互相影响。
5. 文档化（便于团队协作）
   * 新增参数说明手册：[layout_params_guide.md](app://-/index.html?hostId=local#)
   * 新增参数变更记录模板：[layout_params_change_log_template.md](app://-/index.html?hostId=local#)
   * README 增加入口：[README.md](app://-/index.html?hostId=local#)
6. 测试与报告
   * 测试目录已补齐当前问题覆盖（渲染、SKU 解析、参数校验等）。
   * 测试报告文件：[test_report-260301.md](app://-/index.html?hostId=local#)
   * 构建已多次回归，PDF 输出路径：**/Users/pika/Documents/cms-demos/manual_demo/docs/_build/latex/manual_demo.pdf**


date：2026-03-05。 分支：auto-draft-v0.1

截至今天（2026-03-05）这轮在仓库里落盘的完整改动，我按“功能链路”整理如下。

1. 仓库结构清理到 `phase1` 主路径

- 清掉了旧 demo/旧产物目录和非 phase1 旧源（如 `output/`、`snapshots/`、`demo_data/`、旧 `docs/safety*.rst` 等）。
- 当前入口集中到 `phase1 -> docs/generated -> sphinx/latex` 主流程。

2. 构建链路修复与稳定化

- 修了 `builder.py` 直接运行时的相对导入问题（支持脚本直跑 fallback）。
- 修了多 SKU 场景下 `gen_index_bundle` 的 `--sku` 解析/失败前置检查（对应测试已补）。
- 相关文件：
  [tools/phase1/builder.py](/Users/pika/Documents/cms-demos/manual_demo/tools/phase1/builder.py)
  [tools/build_docs.py](/Users/pika/Documents/cms-demos/manual_demo/tools/build_docs.py)
  [tests/test_build_sku_resolution.py](/Users/pika/Documents/cms-demos/manual_demo/tests/test_build_sku_resolution.py)

3. `spec` 页面正式接入 phase1 渲染体系

- 增加并稳定了 spec 页面的 renderer 解析和输出（含 section/table/notes/footnotes）。
- 相关文件：
  [tools/phase1/renderers.py:447](/Users/pika/Documents/cms-demos/manual_demo/tools/phase1/renderers.py:447)
  [tools/phase1/renderers.py:697](/Users/pika/Documents/cms-demos/manual_demo/tools/phase1/renderers.py:697)
  [docs/templates/spec_template.rst](/Users/pika/Documents/cms-demos/manual_demo/docs/templates/spec_template.rst)
  [docs/renderers/latex/components_spec.tex](/Users/pika/Documents/cms-demos/manual_demo/docs/renderers/latex/components_spec.tex)

4. `Spec_Master.csv -> RST -> PDF` 链路接入

- Draft 数据源已切主：spec 页面优先读 `tools/Draft-tool/data/Spec_Master.csv`。
- 相关文件：
  [tools/phase1/builder.py:265](/Users/pika/Documents/cms-demos/manual_demo/tools/phase1/builder.py:265)
  [tools/Draft-tool/data/Spec_Master.csv](/Users/pika/Documents/cms-demos/manual_demo/tools/Draft-tool/data/Spec_Master.csv)
  [tools/Draft-tool/csv_to_spec_page_rst.py:367](/Users/pika/Documents/cms-demos/manual_demo/tools/Draft-tool/csv_to_spec_page_rst.py:367)

5. `Spec_Master.csv` 法语字段补齐并参与构建

- 在主表中增加并填充了 FR 列：`Row_label_fr/Param_fr/Value_fr/page_title_fr/section_title_fr`。
- 相关文件：
  [tools/Draft-tool/data/Spec_Master.csv:1](/Users/pika/Documents/cms-demos/manual_demo/tools/Draft-tool/data/Spec_Master.csv:1)

6. 新增脚注独立 CSV 并接入主流程

- 新增脚注数据表 `Spec_Footnotes.csv`。
- `builder` 在加载 `Spec_Master` 后自动合并脚注表。
- 相关文件：
  [tools/Draft-tool/data/Spec_Footnotes.csv:1](/Users/pika/Documents/cms-demos/manual_demo/tools/Draft-tool/data/Spec_Footnotes.csv:1)
  [tools/phase1/builder.py:268](/Users/pika/Documents/cms-demos/manual_demo/tools/phase1/builder.py:268)

7. spec 排版样式按你给的图持续迭代

- 表格线条层级、左列底色、圆角一致性、标题与表格间距、bullet 大小/对齐、单页收敛都做了多轮调整。
- 相关文件：
  [docs/renderers/latex/components_spec.tex](/Users/pika/Documents/cms-demos/manual_demo/docs/renderers/latex/components_spec.tex)
  [docs/renderers/latex/layout_core.tex](/Users/pika/Documents/cms-demos/manual_demo/docs/renderers/latex/layout_core.tex)
  [data/layout_params.csv](/Users/pika/Documents/cms-demos/manual_demo/data/layout_params.csv)

8. 字体与平台构建兼容（Mac 预览 + Win 主环境）

- 调整了字体注入与补丁流程，确保 `fonts.tex` 在 latex 主 tex 中稳定生效。
- 相关文件：
  [docs/renderers/latex/fonts.tex](/Users/pika/Documents/cms-demos/manual_demo/docs/renderers/latex/fonts.tex)
  [tools/patch_latex_fonts.py](/Users/pika/Documents/cms-demos/manual_demo/tools/patch_latex_fonts.py)
  [docs/conf_base.py](/Users/pika/Documents/cms-demos/manual_demo/docs/conf_base.py)

9. 测试体系与报告

- 补了针对当前问题的测试目录与用例（builder/renderers/sku/layout 参数）。
- 新增/更新测试报告。
- 相关文件：
  [tests/test_phase1_builder.py](/Users/pika/Documents/cms-demos/manual_demo/tests/test_phase1_builder.py)
  [tests/test_phase1_renderers.py](/Users/pika/Documents/cms-demos/manual_demo/tests/test_phase1_renderers.py)
  [code-as-doc/tests/test_report-260301.md](/Users/pika/Documents/cms-demos/manual_demo/code-as-doc/tests/test_report-260301.md)

10. 文档化补充（供团队协作）

- 新增了 `layout_params` 参数说明和“参数变更记录模板”。
- 相关文件：
  [code-as-doc/dev/layout_params_guide.md](/Users/pika/Documents/cms-demos/manual_demo/code-as-doc/dev/layout_params_guide.md)
  [code-as-doc/dev/layout_params_change_log_template.md](/Users/pika/Documents/cms-demos/manual_demo/code-as-doc/dev/layout_params_change_log_template.md)
  [README.md](/Users/pika/Documents/cms-demos/manual_demo/README.md)

11. 构建验证结果

- 已多次跑通 `phase1_build`、`build_docs`，并产出 PDF：[docs/_build/latex/manual_demo.pdf](/Users/pika/Documents/cms-demos/manual_demo/docs/_build/latex/manual_demo.pdf)
- 全量单测通过（当前 18/18）
