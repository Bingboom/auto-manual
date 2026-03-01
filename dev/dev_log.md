date：2026-03-01

1. 仓库清理（只保留 phase1 主路径）
   * 已清理/不存在：**demo_data**、**output**、**snapshots**、**latex_theme**、旧 **docs/safety*.rst**、**docs/overview.rst**。
   * 当前文档入口保留为 phase1 生成流（**docs/generated/...** + **docs/index.rst**）。
3. 新增并接入 **spec** 页面组件链路
   * 新增规格页组件文件：[components_spec.tex](app://-/index.html?hostId=local#)
   * 主题接入：[theme.tex](app://-/index.html?hostId=local#)
   * Sphinx 额外文件接入：[conf_base.py](app://-/index.html?hostId=local#)
   * 渲染器切换到组件化 spec 输出：[renderers.py](app://-/index.html?hostId=local#)
4. **layout_params.csv** 参数体系扩展与精调
   * 新增 spec 专属参数组（标题间距、bullet、表格比例/密度、notes/footnotes、spec 字体行距）。
   * 新增 FR/ES spec 覆盖参数（密度与字号行距）。
   * 调整列表/标题 bullet 的基线参数（含 safety 与 spec 解耦）。
   * 文件：[layout_params.csv](app://-/index.html?hostId=local#)
   * 同步生成文件：[params.tex](app://-/index.html?hostId=local#)
5. 排版细节修正（按你的截图迭代）
   * spec 表格改为单线风格、外框/内线层级、左列灰底、圆角框一致性。
   * 标题前后间距、bullet 大小/间距、行高和一页内收敛都做了多轮调参。
   * safety 列表 bullet 与 spec 标题 bullet 分离控制，避免互相影响。
6. 文档化（便于团队协作）
   * 新增参数说明手册：[layout_params_guide.md](app://-/index.html?hostId=local#)
   * 新增参数变更记录模板：[layout_params_change_log_template.md](app://-/index.html?hostId=local#)
   * README 增加入口：[README.md](app://-/index.html?hostId=local#)
7. 测试与报告
   * 测试目录已补齐当前问题覆盖（渲染、SKU 解析、参数校验等）。
   * 测试报告文件：[test_report-260301.md](app://-/index.html?hostId=local#)
   * 构建已多次回归，PDF 输出路径：**/Users/pika/Documents/cms-demos/manual_demo/docs/_build/latex/manual_demo.pdf**
