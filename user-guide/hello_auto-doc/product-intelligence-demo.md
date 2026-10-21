# 外部情报 Demo

外部情报的重点是先收集、再推送用于决策，不受内部产品牵制。每条外部事件只需写清
发生了什么、来源和核实状态、需要什么决策、由谁决定、何时决定，就能被收集、展示
和推送；产品关联只是事件可选的附录。研究假设、产品关联都需要人工判断，不能作为
产品参数、兼容性、合规或商业收益结论。

## 录入外部事件

事件属于业务数据，放在业务知识目录（Hello-Docs `docs/knowledge/`，即构建的
`rtd_knowledge_dir`）的 `external-intel/events.json`，与 `market-policy/records.json`
并列，不在工程仓库维护。格式为 `schema_version: external-intel-events/v1` 的
`events` 列表，完整示例见
[`tests/fixtures/external_intel/events.json`](../../tests/fixtures/external_intel/events.json)。

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
