# OpenClaw Phase 2 Bootstrap

Use this repo as a natural-language operator surface for the manual workflow.

Operator boundary:

- Feishu phase2 tables remain the source of truth.
- `Document link` remains the only required artifact link field in V1/V1.5.
- Do not invent or require `Document link_dd` unless the task is explicitly about V2 DingTalk dual-write.

When a user asks to operate the workflow in natural language:

1. For query-only asks, resolve the target queue row with:
   - `python3 build.py queue-query --config config.us.yaml --query-text "<user request>" --json`
2. For execution asks like build / publish / start-review, prefer:
   - `python3 build.py queue-execute --config config.us.yaml --query-text "<user request>"`
   This deterministic entrypoint resolves one queue row, dispatches the matching GitHub worker, waits for completion, then re-reads the Feishu row and prints the final record fields.
3. Prefer the deterministic `--query-text` parser for natural-language asks.
   Only fall back to manual flags when the user is explicitly debugging filters.
4. Prefer exact filters from the user request:
   - `--document-id`
   - `--document-key`
   - `--build-family`
   - `--lang`
   - `--document-version`
   - `--query-workflow-action`
   If the user gives a full token like `JE-1000F_US_0.3`, treat it as exact `Document_ID` first.
   The parser also accepts spaced asks like `JE-1000F US 0.3`, `JE-1000F US en 0.3`, and `开始 review JE-1000F us-merged`.
   Do not decompose it into guessed `Build_family`, `Lang`, or `Version` unless the user explicitly asks for a broader search.
5. If multiple rows match, stop and tell the user which rows are ambiguous.
6. Only fall back to the manual two-step path when debugging or when a human explicitly asks for the separate record_id first:
   - Resolve row:
     `python3 build.py queue-query --config config.us.yaml --query-text "<user request>" --json`
   - Then dispatch:
   - Start Review:
     `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch start-review <record_id>`
   - Build Draft Package:
     `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch build-draft <record_id>`
   - Publish:
     `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch publish <record_id>`
7. If the user wants status:
   - Prefer `python3 build.py queue-query ... --json` for Feishu table truth
   - Use `node integrations/openclaw/auto-manual-control-layer/cli.mjs status last` for the latest tracked GitHub run
8. When reporting results, prefer:
   - `record_id`
   - `Workflow_action`
   - `Git_ref`
   - `构建结果`
   - `Document link`
   - `PR_url`

Natural-language intent mapping:

- "生成草稿", "重出草稿", "build draft", "draft package" -> `build-draft-package`
- "发布", "正式发布", "publish" -> `publish`
- "进入 review", "拉进 review", "start review" -> `start-review`
- "查链接", "最新文档链接", "document link" -> queue query only
- "查失败原因", "为什么失败" -> queue query first, then summarize `构建结果`

Examples:

- User says `查 JE-1000F_US_0.3 的 Build Draft Package`
  First query:
  `python3 build.py queue-query --config config.us.yaml --query-text "查 JE-1000F_US_0.3 的 Build Draft Package" --json`

- User says `请帮我构建 JE-1000F_US_en_0.3，并返回 Build Draft Package 记录`
  Execute directly:
  `python3 build.py queue-execute --config config.us.yaml --query-text "请帮我构建 JE-1000F_US_en_0.3，并返回 Build Draft Package 记录。只返回 record_id、Git_ref、构建结果、Document link。"`

- User says `为什么 JE-1000F US 0.3 构建失败`
  First query:
  `python3 build.py queue-query --config config.us.yaml --query-text "为什么 JE-1000F US 0.3 构建失败" --json`

Safety rules:

- Do not dispatch workflows on any branch other than `main`.
- Do not bypass Feishu row resolution by inventing a `record_id`.
- For `Build Draft Package` and `Publish`, treat `Document_link.Git_ref` as the real content source.
