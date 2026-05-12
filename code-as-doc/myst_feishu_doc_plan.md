# MyST MD 与飞书云文档发布链路实施计划

## Summary

在现有 Word 构建链路上增加一个并行输出：`myst`。这个产物是为后续
Read the Docs / Sphinx 托管做准备的 canonical MyST-compatible Markdown，
不混入飞书专用语法。它复用当前 `build.py` 的目标解析、review 同步、
phase2 数据、page manifest、materialized bundle 和 Word HTML fragment，
不另起一套模板解析。Publish 阶段再从这个 Markdown 产物派生飞书导入内容，
通过 `lark-cli docs +create` 创建飞书云文档，并写回新增字段 `飞书云文档`。

## Key Changes

- `build.py` 增加 `myst` 动作，内部映射为 `build_docs --formats myst`。
- 新增 MD 输出目录：`docs/_build/<model>/<region>/myst/`。
- 默认文件名从 `build.myst_output` 读取，未配置时由 `word_output` 改后缀得到 `.md`。
- `build.py all` 暂不包含 `myst`，避免改变现有 HTML/Word/PDF 行为。
- 新增 `tools/myst_bundle.py`，复用 `materialize_bundle` 与 Word HTML fragment 转换，再导出 RTD/Sphinx 友好的 MyST-compatible Markdown。
- 新增飞书云文档发布模块，用当前 `lark-cli docs +create --api-version v2 --markdown @<md>` 从 MyST 产物创建云文档。
- 队列保留现有 `Document link` 主产物写回；新增 `飞书云文档` 字段写回云文档 URL。

## Queue Flow

- Draft：
  - 现有 `check -> word` 保持不变。
  - 不默认创建飞书云文档，避免加重 review 阶段队列。
  - 如需人工预览，可手动运行 `build.py myst --source review`。
- Publish：
  - 现有 `publish -> html --source review` 保持不变。
  - 追加 `myst --source review --no-clean`。
  - 上传 PDF 后，创建飞书云文档并写回 `飞书云文档`。
- `构建结果` 增加状态片段：`feishu_doc=ok|failed|skipped`。
- 飞书云文档创建失败时，不覆盖已有 `Document link`；主产物成功仍按现有逻辑写回，失败原因写入 `构建结果`。

## Feishu Details

- 默认父节点复用当前 `FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN` / queue wiki destination。
- `lark-cli docs +create` 使用 user 身份，沿用现有 phase2 identity 解析。
- canonical `myst` 产物保持 RTD 友好：标准标题、段落、列表、Markdown 表格、图片语法和相对资源路径。
- 飞书导入只作为 publish 阶段的派生投递；如飞书 CLI 对本地图片或复杂表格有限制，转换逻辑在临时导入内容里降级处理，不污染 canonical MyST 文件。

## Test Plan

- `python -m unittest`
- `python build.py myst --config config.us.yaml --model JE-1000F --region US`
- `lark-cli docs +create --api-version v2 --markdown @<generated.md> --wiki-node <token> --dry-run`
- `python build.py process-build-queue --config config.us.yaml --record-id <publish_record_id> --dry-run`
- 单测覆盖：
  - `myst` action/format 映射
  - MD 输出路径解析
  - RST/HTML fragment 到 Markdown 转换
  - Publish 阶段飞书创建命令拼装与返回解析
  - `飞书云文档` 写回不影响 `Document link`

## Assumptions

- 新增 Base 字段名准确为 `飞书云文档`。
- `Document link` 继续作为当前 PDF/DOCX 主产物链接。
- 第一版目标是生成 RTD/Sphinx 友好的 MyST-compatible Markdown；飞书云文档是 publish 阶段的下游投递结果。
- 文档同步更新 `README.md`、`code-as-doc/build_doc_guide.md`、`user-guide/hello_auto-doc.md`。
