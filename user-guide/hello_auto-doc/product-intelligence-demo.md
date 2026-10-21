# 外部情报 Demo

本页是 Research & Intelligence 孵化原型的试运行说明。它是从 Hello-Docs 仓库中孵化的
独立研究平台项目，不是 Hello-Docs 的新功能；所在分支不合入 `main`，核心最终迁到
独立仓库，见[项目章程](../../code-as-doc/dev/research-intelligence-charter.md)。

外部情报的重点是先收集、再推送用于决策，不受内部产品牵制。每条外部事件只需写清
发生了什么、来源和核实状态、需要什么决策、由谁决定、何时决定，就能被收集、展示
和推送；产品关联只是事件可选的附录。研究假设、产品关联都需要人工判断，不能作为
产品参数、兼容性、合规或商业收益结论。

## 录入外部事件

事件属于业务数据，放在业务知识目录（Hello-Docs `docs/knowledge/`，即构建的
`rtd_knowledge_dir`）的 `external-intel/events.json`，与 `market-policy/records.json`
并列，不在工程仓库维护。孵化期沿用这个位置；迁出后事件存放在哪里，是章程里的待决策项。格式为 `schema_version: external-intel-events/v1` 的
`events` 列表，完整示例见
[`tests/fixtures/external_intel/events.json`](../../tests/fixtures/external_intel/events.json)。
也可以在飞书「外部情报」表里维护，由同步命令写入这个文件，见下文
[飞书表格闭环](#飞书表格闭环手动试运行)。

- 政策事件（`source_kind: market_policy`）用 `source_record_id` 复用市场政策记录；
  政策事实只从该记录读取，记录缺失时显示“来源资料缺失”。
- 其他外部事件（`external_event`）在修订里写 `status`、`summary`、`boundary` 和
  `sources`；标为 verified 必须有官方 HTTPS 来源，未核实线索可以先不附来源。
- 每次修订写 `decision_question`；`decision_owner`（角色或团队）、`decide_by`、
  `hypotheses`、`unknowns` 可选，未填时页面和摘要显示“待指派”“未设定”。
- 需要产品视角时才加 `product_lens`（目录市场、市场映射说明、分类/能力/数值事实
  规则）。规则词必须是产品知识快照里存在的分类、能力登记列或数值事实，写错会在
  附录列出问题，而不是悄悄匹配不到产品。

新增或修改事件时追加一条修订，不改写旧修订。标为已复核时必须填写判断、复核人和
ISO 日期；后续修订重新待判断时，前次人工判断仍保留在历史中。

## 打开和阅读

在启用实验模式的私有分支预览中，从知识库进入“外部情报 · Demo”，或打开
`research/product-intelligence.html`。普通构建默认关闭，公开说明书站点始终不生成
研究页面及其导出。

页面是一张外部事件索引：每个事件一行，列出市场、类型、标题、需要决策的问题、决策人、
截止日期、来源状态和决策状态，顺序与决策摘要一致（待人工判断在前，再按截止日期）。
顶部的“全部事件 / 待人工判断 / 已人工判断 / 来源已核实”可一键筛选，也可按市场、来源
状态、决策状态和关键词筛选。点开一行查看外部发生了什么、来源、可能影响与待核实、人工
判断和修订记录；其中折叠的“附录 · 产品关联视角”说明它未配置、暂不可用、规则需修正或
已计算，已计算时候选产品展开依据，证据不足和暂不关联的变体只列未满足的条件。

## 推送决策摘要

同一次构建生成决策摘要：`_static/external-intel-digest.v1.json`（逐事件结构化
字段和单条消息文本）与 `_static/external-intel-digest.v1.md`（可直接转发的整份
CommonMark 文本）。待人工判断的事件排在前面，再按截止日期排序；每条带页面锚点，
站点有规范 URL 时带绝对链接。摘要不含内部产品数据，构建本身不发送任何消息；接入
飞书等渠道时应由渠道适配器读取 `items` 自行组装，而不是直接转发 `text`。

## 飞书表格闭环（手动试运行）

闭环是：在飞书表格里收集事件 → 同步成 `events.json` 的修订 → 把待决策摘要推送到
飞书群 → 决策人回到表格填写判断 → 下一次同步记录判断。目前只能手动运行，还没有
工作流定时执行；同步只读表格，从不写回。

### 建表

在任一多维表中新建「外部情报」表，一行一个事件，列名必须与下表一致（缺列时同步
直接停止并列出缺少的列）。单选列也可以用文本列，按下表的选项名填写。

| 列 | 类型 | 填写 |
| --- | --- | --- |
| 事件ID | 文本 | 可空，自动生成；自填时以小写字母开头，只含小写字母、数字和连字符。同步后不能修改 |
| 标题、市场 | 文本 | 必填；市场如 `NL`、`US` |
| 类型 | 单选：政策／市场／竞品 | 必填 |
| 发生日期 | 日期 | 必填，事件发生或生效的日期 |
| 来源类型 | 单选：外部事件／市场政策记录 | 必填，同步后不能修改 |
| 政策记录ID | 文本 | 仅市场政策记录必填（`market-policy` 记录 ID），同步后不能修改 |
| 来源状态 | 单选：已核实／未核实／需求 | 外部事件必填 |
| 发生了什么、适用边界 | 多行文本 | 外部事件必填 |
| 来源 | 多行文本 | 每行一条：`官方 \| 标题 \| https://… \| 说明 \| 核实日期`，可再加 `\| 发布日期`；类型为官方或二手，已核实至少要一条官方来源 |
| 需要决策 | 多行文本 | 必填 |
| 决策人 | 文本或人员 | 可空，显示“待指派” |
| 截止日期 | 日期 | 可空，显示“未设定” |
| 可能影响、待核实 | 多行文本 | 可空，每行一条 |
| 人工判断、复核人、复核日期 | 多行文本、文本或人员、日期 | 三项一起填，或都不填 |
| 变更说明 | 文本 | 可空；改动后写入下一条修订的原因，未改时用默认说明 |

市场政策记录的事实来自政策快照，这一行的来源状态、发生了什么、适用边界和来源要
留空。产品视角（`product_lens`）不在表格里维护，仓库中已有的配置原样保留。

### 同步规则

- 只有表格行的事实或判断变了才追加一条修订，旧修订不改写；修订日期是同步当天
  （北京时间）。只改标题、类型、市场或发生日期时更新事件本身，不加修订。
- 人工判断只在复核日期不早于最近一次事实修订日期时计入。只录入判断的同步不会让已
  接受的判断在下一轮失效。事实变化后，未修改的旧判断保留在历史中，事件回到待判断，
  同一天也一样；重新确认时更新判断内容、复核人或复核日期，日期仍须满足上述条件。
  同日结论不变时，可在判断中加上重新核对的说明，或先清空三项并同步，再重新填写。
- 填错的行不会被采用，该事件保持上次状态，并在推送中列为“需处理的表格行”；表格中
  删掉的行也会列出，事件保留在 `events.json` 里，需要移除时在 Hello-Docs 单独提内容 PR。
- 已有手写事件，或某事件的行已被删掉时，新建一行并填同一个事件ID即可接管，历史
  修订原样保留。

### 运行

lark-cli 使用的机器人应用要能读取这张多维表，并已加入要推送的群。令牌只放在环境
变量里，不写进任何仓库文件：

```sh
export FEISHU_EXTERNAL_INTEL_BASE_TOKEN=...   # 多维表 token
export FEISHU_EXTERNAL_INTEL_TABLE_ID=tbl...
export FEISHU_EXTERNAL_INTEL_CHAT_ID=oc_...
# 可选：表格行链接，打开任一行复制链接，把其中 rec 开头的记录 ID 换成 {record_id}
export FEISHU_EXTERNAL_INTEL_RECORD_URL='https://...&record={record_id}'
# 可选：研究页面所在站点，用于“查看详情”链接
export EXTERNAL_INTEL_SITE_URL=https://...

KNOWLEDGE=/path/to/Hello-Docs/docs/knowledge
python -m tools.intel sync --knowledge-dir "$KNOWLEDGE" --push          # 试运行
python -m tools.intel sync --knowledge-dir "$KNOWLEDGE" --write --push  # 写入并推送
```

试运行不写文件、不发消息，只打印每行的变化和将要发送的消息。`--write` 写入
`external-intel/events.json`，`--push` 随后发送；写入后在 Hello-Docs 提交该文件的
内容 PR。`python -m tools.intel push --knowledge-dir "$KNOWLEDGE" [--dry-run]` 只推送文件的
现状。读表或发送失败时只打印 lark-cli 的退出状态和它给出的飞书返回码（例如 91403 通常是没有权限），
不会打印令牌或消息内容。

消息按“已逾期”“7 天内到期”“待决策”分组，列出需要决策的问题、决策人、截止日期和
来源状态，附“去填写判断”（表格行）和“查看详情”（站点页面）链接；本次同步录入的
判断和需处理的表格行也会列出。没有待决策事件、同步也无事可报时不发送。同一天、
同一内容一小时内重复发送只会发出一条。

推送前，命令会先在本机 `~/.cache/auto-manual/external-intel/` 下保存待发消息和候选
写入（可用 `EXTERNAL_INTEL_STATE_DIR` 指定缓存根目录），不把运行状态放进 Hello-Docs。
文件只保存业务消息、事件候选、原日期和幂等键，以及目标配置的哈希；不保存原始群 ID
或 CLI 配置。缓存中的消息链接仍可能包含业务表格地址，不要提交或公开缓存。

发送失败时，重新执行同一个 `sync --write --push`，或使用同一群、CLI profile 和身份
运行 `push`，会先发送原待发消息，成功后才清除缓存；随后再运行一次 sync 才读取新行。
`push --dry-run` 可以查看待发消息。恢复时，若候选尚未写入且原文件仍匹配，会先补写；
若事件文件已被另行修改，命令停止并保留现场，请先核对候选与人工改动。超过飞书一小时
幂等窗口再重试，若上次实际已发送但回执丢失，可能产生重复消息，应先核对群记录。

## Markdown 知识视图

借鉴 [llm_wiki](https://github.com/nashsu/llm_wiki) 的知识库结构（只借鉴结构，不使用它的代码），
把 `events.json` 生成一组相互链接的 Markdown 页面：可以直接用 Obsidian 或 llm_wiki 打开，
AI 助手也能先读索引再回答问题。

```sh
python -m tools.intel wiki --knowledge-dir "$KNOWLEDGE"           # 预览：列出要写入和删除的页面
python -m tools.intel wiki --knowledge-dir "$KNOWLEDGE" --write   # 写入
python -m tools.intel wiki --knowledge-dir "$KNOWLEDGE" --check   # 视图过期时退出码为 1
```

页面生成在 `external-intel/` 下：

- `wiki/index.md` 按类型列出全部事件和市场，`wiki/overview.md` 列出待决策、人工判断和各市场
  数量，`wiki/log.md` 每条修订一项、按记录日倒序，另有每个事件一页
  `wiki/events/<事件ID>.md`、每个市场一页 `wiki/markets/market-<市场>.md`。
- `purpose.md`（目的、关键问题、范围、决策人）和 `schema.md`（页面约定）只在缺少时按模板
  创建，之后由人维护，不会被覆盖。

`wiki/` 下这些页面每次都从 `events.json` 重新生成，手改会被覆盖：事实在飞书表格里改，同步
后再生成。生成只写这些页面，并删除已不存在事件的旧页面；`wiki/` 下的其他文件（例如 llm_wiki
保存的问答）不动。页面不含产品数据，也不带生成时间，数据不变时重新生成没有差异。

同步写入 `events.json` 后运行 `--write`，把 `events.json`、`wiki/`、`purpose.md` 和
`schema.md` 放进同一个 Hello-Docs 内容 PR。用 Obsidian 打开 `external-intel/` 文件夹即可
浏览页面和关系图；用 llm_wiki 把同一文件夹作为项目打开即可问答。两个应用会在该文件夹里建
`.obsidian/`、`.llm-wiki/`，不要提交。

## 本地运行

在工程分支和已安装仓库依赖的 Python 环境中，指向一份独立的冻结发布源，以及包含
`external-intel/events.json` 的业务知识目录。路径替换为本机实际路径：

```sh
RTD_PRODUCT_INTELLIGENCE_DEMO=1 RTD_SITE_ROLE=combined \
  python -m sphinx -b html \
  -D extensions=myst_parser,tools.rtd.portal \
  -D rtd_knowledge_dir=/path/to/frozen/docs/knowledge \
  /path/to/frozen/docs/publish/web /tmp/product-intelligence-html
python -m http.server 8765 --directory /tmp/product-intelligence-html
```

打开本机服务下的 `/research/product-intelligence.html`。开关接受 true/false、1/0、
yes/no、on/off（不区分大小写），其他写法会在构建开始时直接报错。构建读取冻结输入，
不访问飞书，不写回源表。

每次构建生成外部事件 JSON 和两份决策摘要；只有事件配置了产品视角且产品输入可读时，
才额外生成 `_static/product-knowledge.v1.json` 与 `_static/product-intelligence.v1.json`。
发布清单缺失或产品资料读不出时，只有产品视角附录显示“暂不可用”，事件和摘要照常
生成；事件文件本身格式错误时只跳过本页面并给出警告。构建开始时只清理本 Demo 自有的
页面和这五份导出，避免复用输出目录时把上一次结果带到关闭实验或公开说明书的构建中。

## 预览部署与比较

RTD 配置只在 `preview/*` 分支启用实验，其他版本（包括 `latest`）一律强制关闭。预览
载体需要在 Hello-Docs 预览分支的 `docs/knowledge/external-intel/events.json` 放入事件
文件，否则页面显示空状态。

保留前一次 JSON，再用 `compare_event_snapshots(previous, current)` 比较事件变化，用
`compare_lens_snapshots(previous, current)` 比较产品视角变化；历史输入与结果保留原
指纹，比较结果的人工复核状态始终为待复核。

详细字段、所有权、复现测试与预览边界见
[实现契约](../../code-as-doc/dev/product-intelligence-contract.md)。
