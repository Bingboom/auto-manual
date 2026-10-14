# 本地验证

- 原稿：JBP-3600A、US/en；28 页，只转换英文部分（PDF 4–11，印刷 01–08）。原 PDF 原样放在包根目录（7.2 MB，低于 32 MiB 单文件上限），intake.py、extract_assets.py、rebuild.py 运行前都先核对 SHA-256。
- 共用 Manual IR：source/intake.py 生成 source/en/content.json，rebuild.py 用共用流渲染和共用组件重放。
  - 组件数：HB-CALLOUT-STRIP 4、HB-SPECIAL-FCC 1、HB-SPECIAL-INBOX 1、HB-SPECIAL-REFERENCE-FIGURE 10、HB-TABLE-REFERENCE 1、HB-TABLE-SPEC 3、HB-TABLE-SYMBOL-ICON 1、HB-TABLE-SYMBOL-SIGNAL 1、HB-TABLE-TROUBLESHOOTING 1、HB-WARRANTY-LEAD 1、HB-WARRANTY-SECTION 5、HB-WARRANTY-YEARS 1。
- 全文覆盖：PDF 4–11 的 1144 个文本层词全部归类（正文、图内文字、印刷符号、包装序号、页码），没有未归类词，正文无重复；48 行轮廓文字全部用上。
- 印刷断行：判定规则是“下一个词仍放得下，印刷却换了行”；轮廓行按审定的句首断行。共 22 处，逐条记在 coverage.json。
- 准入（本地）：组件准入、符号资产准入（11 行，逐行重建原生字形并比对）、图框准入通过。候选状态下 publication_eligible 为 false，发布准入按预期不适用。
- 冷重放：web/en 与新重放输出逐字节一致。
- 篡改测试：改动 content.json、插图、presentation.css 或原 PDF，重放在写出任何文件之前就报错。
- 严格 Sphinx：python -m sphinx -n -W --keep-going -b html，成功。
- 浏览器（browser-validation.json）：320、390、768、1024、1280、1920 宽，页面都不横向溢出，没有表格内滚动，没有缺图，没有脚本错误。
- 测试：tests/test_jbp3600a_us_en_web.py（已登记到 tests/slow_modules.txt）。
- 改动范围：只新增 data/manual_sources/JBP-3600A/US/en/git-20261014-16ae12b0/**、本包测试和 slow_modules.txt 一行。没有改共用代码、CLI、配置、schema、工作流或产品矩阵；没有写在线表、队列、资产或链接字段。
