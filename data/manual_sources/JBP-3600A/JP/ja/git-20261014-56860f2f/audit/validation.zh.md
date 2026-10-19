# JBP-3600A JP 日文 Git-only 发布版 —— 验证记录（2026-10-14）

环境：Python 3.13，`requirements.lock` 固定版本（PyMuPDF 1.28.0 / MuPDF 1.29.0、Sphinx 8.2.3）。

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| 源 PDF 身份 | `sha256sum source/pdf-archive/part-001.bin` | `56860f2f…eb9160e`，与飞书文件一致 |
| 美术复现 | `python3 $PKG/source/extract_assets.py --check` | 26/26 与记录哈希一致（含 7 幅 redact_text 无字底图） |
| 词覆盖门 | `python3 $PKG/source/intake.py` | 10 章，问题 0；整张图纸 588 词全部分类 |
| ruff | `python -m ruff check build.py integrations tools tests scripts` 与 `ruff check $PKG` | 通过 |
| 包测试 | `python -m unittest tests.test_jbp3600a_jp_ja_web` | 13 项通过（含 intake 复现、美术复现、冷重放、准入、篡改拒绝）；故障表改为共享组件、7 幅插图改为无字底图 + 活标签后复测通过（新增活标签测试，共 14 项） |
| 全量测试 | `python -m unittest` | 5472 项；本包测试在清单刷新后全部通过；唯一无关失败为 `test_bitable_schema_cli` 帮助文本 golden（本地 Python 3.13 的 argparse 换行，CI 为 3.12），与本改动无关 |
| 维护性守卫 | `python -m tools.check_maintainability_guardrails` | 通过 |
| 文档链接 | `python -m tools.check_doc_link_integrity` | 0 断链 |
| 严格 Sphinx | `python -m sphinx -n -W --keep-going -b html web/ja <out>` | 0 警告 |
| 冷重放字节一致 | `rebuild.py --output <新目录>` 与 `web/ja` 全文件哈希比较 | 一致 |
| 篡改拒绝 | 改动 content.json / 资产 / presentation.css / PDF 任一字节 | 均在写出前拒绝 |
| 准入 | component、symbol、caption-frame admission | 通过；操作员验收后 `require_publishable_manual_ir` 也通过（验收前按预期拒绝） |
| 浏览器宽度扫描 | 320–1920 px 共 14 档（`audit/browser-validation.json`） | 无页面溢出、无坏图、无脚本错误、表格无横向滚动 |

状态：`publication_status: operator-approved-git-only-release`。操作员已于 2026-10-14 验收上线（「合入了，上线授权你合入」），`source/approval.json` 绑定全部源输入，IR `publication_eligible: true`；合入和发布按 MA-303 执行。
