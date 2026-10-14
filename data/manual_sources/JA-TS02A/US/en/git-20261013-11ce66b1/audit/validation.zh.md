# 本地验证

- 原稿：JA-TS02A、US/en、JAK-UM-V1.0；共 92 页，只转换英文部分（PDF 3–24，印刷 01–22）。完整原稿拆成三个有序二进制分片无损保存，重组后的 SHA-256 与原文件一致。intake.py 和 rebuild.py 运行前都会先校验这一点。
- 共用 Manual IR：
  - source/intake.py 从存档 PDF 生成 source/en/content.json；rebuild.py 用共用的流渲染和共用组件重放。
  - 组件数：HB-CALLOUT-STRIP 5、HB-SPECIAL-APP 1、HB-SPECIAL-REFERENCE-FIGURE 30、HB-WARRANTY-LEAD 1、HB-WARRANTY-SECTION 6。
  - 原 build_web.py、source/web_presentation.css、source/native-pages.json 已删除。
- 全文覆盖：PDF 3–24 的 4410 个词都已归类，记录在 source/en/coverage.json。
  - 类别：正文、图内文字、印刷符号、页眉角标、页码。
  - 没有未归类的词，正文也没有重复。
  - 文本层缺失的 5 行按 source/text-recovery.json 补回，全部用上。
  - 跨行拆开的 2 个词（consump-/tion、approxi/mately）已合并。
- 印刷断行：判定规则是“下一个词仍放得下，印刷却换了行”，共 37 处，逐条记在 coverage.json。
- 表格：5 张都是原生 HTML。
  - 符号表、17 行规格表（无表头）。
  - 线缆表：表头跨列；分组名和电流各跨 4 行；颜色旁有线色示意。
  - 11 行 LED 状态表：指示灯名称跨行合并。
  - 4 行扭矩表：居中，数值不折行。
- 图：32 张完整插图／App 图，不显示图注，没有折叠文字栏。
  - p12、p13 的灰色提示条按插图规范留在完整面板内，提示句写进替代文字。
  - 符号：3 个共用 native-v1 SVG、1 个共用 PNG（接地）、2 个从源 PDF 提取的矢量（黄色警告三角、误吞警示）。
  - App 内联控件：7 个。
- 冷重放：web/en 与新重放的输出逐字节一致。
- 篡改测试：改动 source/presentation.css 后，重放在写出任何文件之前就报错；恢复后哈希与清单一致。
- 严格 Sphinx：python -m sphinx -n -W --keep-going -b html，成功。
- 发布准入（本地）：组件、符号资产、图框三项准入通过。require_publishable_manual_ir 因待审（pending source review）按预期拒绝。
- 浏览器（结果记在 browser-validation.json）：
  - 1280：表格都在版心内。
  - 768：没有横向滚动。
  - 390：只有 6 列的扭矩表在自己的框内横向滚动。
  - 320：线缆、LED、扭矩表各在自己的框内滚动。
  - 各宽度下页面本身都不溢出，没有缺图，没有脚本错误。
- 测试：tests/test_ja_ts02a_us_en_web.py。
- 改动范围：只改 data/manual_sources/JA-TS02A/US/en/git-20261013-11ce66b1/** 和本包的测试。
  - 没有改共用代码、CLI、配置、schema 或工作流。
  - 没有写在线表、队列、资产或链接字段。

本候选未合入、未发布。发布前需要操作员验收这些输入（source/approval.json），并另行授权合入和发布。
