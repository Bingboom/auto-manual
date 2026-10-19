# 本地验证

- 原稿：JBP-3600A、US；28 页，转换英文、法文、西文三部分正文（EN PDF 4–11、FR 12–19、ES 20–27）。原 PDF 原样放在包根目录（7.2 MB，低于 32 MiB 单文件上限），intake.py、extract_assets.py、rebuild.py 运行前都先核对 SHA-256。
- 包形态：一个 US 级包，web_roots 为 en/fr/es（同 JHP-5000C、JHP-3000D）；包路径已在本 PR 内从 US/en/ 移到 US/。
- 共用 Manual IR：source/intake.py 按语言生成 source/<lang>/content.json，rebuild.py --language 用共用流渲染和共用组件重放。三种语言组件数相同：HB-CALLOUT-STRIP 4、HB-SPECIAL-FCC 1、HB-SPECIAL-INBOX 1、HB-SPECIAL-REFERENCE-FIGURE 10、HB-TABLE-REFERENCE 1、HB-TABLE-SPEC 3、HB-TABLE-SYMBOL-ICON 1、HB-TABLE-SYMBOL-SIGNAL 1、HB-TABLE-TROUBLESHOOTING 1、HB-WARRANTY-LEAD 1、HB-WARRANTY-SECTION 5、HB-WARRANTY-YEARS 1。
- 全文覆盖（按语言）：EN 1144、FR 1249、ES 1252 个文本层词全部归类，无未归类词，正文无重复。轮廓文字补回 EN 48、FR 59、ES 61 行，全部用上。跨行连字符拆词合并：FR 1 处、ES 3 处。
- 印刷断行：规则同英文；逐条记在各语言 coverage.json（EN 22、FR 24、ES 23 处）。
- 准入（本地，三种语言）：组件准入、符号资产准入（每种语言 11 行，逐行重建原生字形并比对）、图框准入通过。操作员已于 2026-10-14 验收上线（「合入了，上线授权你合入」）：source/approval.json 绑定全部源输入，三种语言的 publication_eligible 均为 true，require_publishable_manual_ir 通过；合入和发布按 MA-303 执行。
- 冷重放：web/en、web/fr、web/es 与新重放输出逐字节一致；web/en 与移包前英文版逐字节一致。
- 篡改测试：改动法文 content.json、西文插图、presentation.css 或原 PDF，重放在写出任何文件之前就报错。
- 严格 Sphinx：三个 web 根分别执行 python -m sphinx -n -W --keep-going -b html，均成功。
- 浏览器（browser-validation.json）：三种语言各在 320、390、768、1024、1280、1920 宽检查，页面都不横向溢出，没有表格内滚动，没有缺图，没有脚本错误。
- 测试：tests/test_jbp3600a_us_web.py（含章节顺序固定为印刷顺序），登记在 tests/slow_modules.txt。
- 改动范围：只新增 data/manual_sources/JBP-3600A/US/git-20261014-16ae12b0/**、本包测试和 slow_modules.txt 一行。没有改共用代码、模板、CLI、配置、schema、工作流或产品矩阵；没有写在线表、队列、资产或链接字段。
