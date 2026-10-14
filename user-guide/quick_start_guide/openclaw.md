# 快速开始：OpenClaw 入口（§2.1、§9.5）

属于[快速开始指南](../quick_start_guide.md)，其索引列出全部分页。章节编号与原文一致。
示例或流程变化时更新本页，不要把新内容追加到总文件。

## 2.1 OpenClaw Phase 2 自然语言入口怎么接

如果你要让 OpenClaw 在飞书里按自然语言去操作这套流程，推荐固定成两个确定性入口：

1. 查状态或查记录时，先查表定位唯一目标行：
   - `python build.py queue-query --config configs/config.us.yaml --query-text "查 JE-1000F_US_0.3 的 Build Draft Package" --json`
   - 如果要先让 OpenClaw 看结构化 dry-run 结果，再走下一步：`python build.py queue-resolve-action --config configs/config.us.yaml --query-text "发布 JE-1000F_US_0.3" --json`
   - 如果只是查发布文档管理表里的产品说明书链接或总览：`python build.py manual-index-query --config configs/config.us.yaml --query-text "查 JE-2000F 的说明书链接" --json`
2. 要真正执行时，直接走一条确定性命令：
   - `python build.py queue-execute --config configs/config.us.yaml --query-text "请帮我构建 JE-1000F_US_en_0.3，并返回 Build Draft Package 记录。只返回 record_id、Git_ref、构建结果和 delivery_url。"`
   - 如果这条命令最终会命中 `Workflow_action = Publish`，要额外带上 `--confirm-publish`
3. 只有在排查问题或需要人工拆步骤时，再手动触发控制层：
   - `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch <start-review|build-draft> <record_id>`
   - `node integrations/openclaw/auto-manual-control-layer/cli.mjs dispatch publish <record_id> confirm`
4. 如果要直接接飞书 IM 消息入口，而不是通过 OpenClaw 命令面板：
   - 本机直连、不要服务器中转时：启动 `python build.py listen-message-control --config configs/config.us.yaml`
   - 这种模式走的是 `lark-cli event +subscribe` 的长连接；飞书应用里要先把 `im.message.receive_v1` 事件加上并发布
   - 如果同一台机器还要保留旧 app 的本地 `lark-cli` 配置，先设置 `FEISHU_IM_LARK_CLI_HOME=单独目录`，再在那个目录下初始化新 app 的 `lark-cli` 配置
   - 它仍然只处理这套文档控制层支持的动作、状态和只读发布文档管理查询，例如 `开始 review ...`、`帮我生成 ... 草稿`、`发布 ...`、`为什么 ... 构建失败`、`查 JE-2000F 的说明书链接`、`获取说明书总览信息`
   - 云文档 backport **不是**飞书 IM / BlockClaw 的能力（LLM 对目标分支的判断不够确定）；已接受修订的回写请在 Claude Code / Codex / 终端里跑 `python -m tools.backport.cloud_doc run-review-branch ...`（见 AGENTS.md §3）
   - 如果你要的是公网 callback / 多实例 / 长期托管，再改用下面的 webhook adapter
   - 启动 `node integrations/openclaw/feishu-im-webhook-adapter/server.mjs`
   - 如果部署在长期运行的 ECS 上，改用 [`../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/`](../../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/) 里的 wrapper 和 `systemd` unit 模板，不要长期靠手工 `nohup`
   - 把 Feishu 事件订阅指向这个 adapter 的 callback URL
   - 如果飞书事件订阅启用了加密模式，给 adapter env 增加 `FEISHU_IM_ENCRYPT_KEY`

这样做的目的只有一个：

- 不让自然语言入口凭空猜 `record_id`
- 不让自然语言入口临场拼“查表 -> dispatch -> 等待 -> 回读”的步骤
- 仍然以 Feishu 队列表为唯一真源
- 如果一句话里已经给了完整 `Document_ID`，例如 `JE-1000F_US_0.3`，解析器会优先把它当成精确 `Document_ID`，而不是拆成猜测的 `Build_family` 或 `Lang`
- 解析器现在也支持空格写法，例如 `帮我生成 JE-1000F US 0.3 草稿`、`开始 review JE-1000F us-merged`、`为什么 JE-1000F US 0.3 构建失败`
- 只读说明书索引查询会先读 `发布文档管理` Base 视图：`查 JE-2000F 的说明书链接` 返回匹配行，`查询各产品的说明书` 返回清单，`获取说明书总览信息` 返回按区域、源语言、文档类型、分类等维度的总览
- Start Review 可以只给 `Document_Key`，例如 `review JE-1000F_EU`
- Build Draft Package 的市场文案请求按配置展开；`构建JE-1000F的欧规说明书文案` 或 `基于配置构建JE-1000F的欧规` 隐含“构建配置里的所有欧规语言行”，会解析成 `Task_id` 前缀 `JE-1000F_EU_`，并只执行 `是否触发文档构建 = Y` 的 `Build Draft Package` 行
- 如果没说市场，例如 `构建JE-1000F说明书文案`，市场也会通配；解析器会用 `Task_id` 前缀 `JE-1000F_`，拉起所有 `JE-1000F` 且 `是否触发文档构建 = Y` 的 `Build Draft Package` 行
- 如果要指定版本，可以说 `构建 JE-1000F_EU_1.0 的欧规说明书文案`；解析器会保留 `Task_id` 前缀并加上 `Version=1.0`，而不是去找不存在的单条 `JE-1000F_EU_1.0`

Phase 2 控制层使用阶段化交付契约：

- `Build Draft Package`：`delivery_kind=feishu_cloud_doc`，`delivery_url` 来自 `飞书云文档`
- `Publish`：`delivery_kind=idml_file`，`delivery_url` 来自 `idml_file`
- `Web Publish`：`delivery_kind=html`，`delivery_url` 来自 `HTML_link`

`delivery_ready` 是 Agent 的交付完成判据。`Document link` / `document_link` 已退役，绝不能用它或空的 `idml_file` 判断 Draft 云文档上传失败；`baseline_ready` 只表示 `基线文档`可用于 backport。

如果当前启用了 DingTalk mirror，worker 还会在表里额外写：

- `Document link_dd`

`Document link_dd` 只作为可选镜像回写，不参与 `delivery_ready` 判定。

## 9.5 OpenClaw Phase 1 操作入口

如果你们已经把 OpenClaw 作为统一控制层接到 Feishu，上面的三条自动化也可以直接换成 OpenClaw 命令入口：

- `/start-review <review_init_record_id>`
- `/build-draft <document_link_record_id>`
- `/publish <document_link_record_id> confirm`
- `/manual-status [run_id|last]`

注意：

- OpenClaw 只负责统一入口和状态查询，不直接执行仓库里的 `build.py`
- 真正的远端执行仍然是 `main` 上的 GitHub worker
- OpenClaw dispatch 现在会额外带一个 `openclaw_dispatch_nonce`，worker 完成后也会上传 `openclaw-run-metadata`，这样状态查询可以稳定追踪到同一次手动触发
- 如果同一批 `en / es / fr` Build Draft Package 行在很短时间内连续触发，OpenClaw 现在会复用一个共享 draft queue worker，而不是给每个语言各发一条会互相竞争的 GitHub queue run
- 类似 `构建JE-1000F的欧规说明书文案` 这种没有写“所有”的市场文案请求也按批量处理；OpenClaw 会用 `Task_id` 前缀匹配配置里的欧规语言行
- 类似 `构建JE-1000F说明书文案` 这种没有写市场的文案请求会进一步把市场也通配，按 `Task_id` 前缀 `JE-1000F_` 匹配所有已勾选构建的行
- 插件包路径是 [`../integrations/openclaw/auto-manual-control-layer/`](../../integrations/openclaw/auto-manual-control-layer)
