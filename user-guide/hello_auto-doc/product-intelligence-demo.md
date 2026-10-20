# 产品情报关联 Demo

这是产品知识的下游研究入口。它消费冻结的已发布说明书、产品矩阵分类、
能力登记表和外部事件，生成可追溯的候选关联、研究假设及待核实问题。
结果需要人工判断，不能作为产品参数、兼容性、合规或商业收益结论。

## 打开和阅读

在启用实验模式的私有分支预览中，从知识库的“产品与市场”进入
“产品情报研究 · Demo”，或打开 `research/product-intelligence.html`。
普通构建默认关闭，公开说明书站点始终不生成研究页面及其 JSON。
构建开始时只清理本 Demo 自有的研究 HTML 和两份 JSON，避免复用输出目录时
把上一次实验结果带到关闭实验或公开说明书的构建中。
RTD 配置仅在私有项目 `ht-docs-ht-manuals` 的
`preview/product-intelligence-1579` 分支自动启用实验；`latest` 不启用。

按“研究问题 → 外部事件 → 候选产品 → 证据 → 假设与缺口 → 修订”阅读。
页面区分四类依据：

| 依据 | 能说明什么 |
| --- | --- |
| 已发布说明书 | 当前型号、地区、语言和版本明确记载的事实 |
| 人工分类配置 | 产品线和研究范围的维护判断 |
| 能力登记表 | 同型号、同地区的已登记开关；不等同于手册原文 |
| 规则推导 | 满足哪些关联条件；不等同于已验证的产品适用性 |

“候选关联”表示值得继续研究；“未知”列出所缺证据；“排除”保留不匹配原因。
未知与不支持是不同状态。欧规资料不能自动证明某个欧盟国家在售、并网合规
或补贴资格。旧版资料的语言范围若未核验，页面和数据会保留这一限制。

荷兰净计量案例通过 ID 复用现有市场政策快照；该快照缺失时显示缺失，
不会改用一份悄悄维护的政策副本。另一类美国停电事件用于展示不同研究问题。
来源状态、证据发布时间、研究录入时间和人工复核状态分别保留。

## 本地运行

在工程分支和已安装仓库依赖的 Python 环境中，指向一份独立的冻结发布源，
以及经审核的业务知识目录。路径替换为本机实际路径：

```sh
RTD_PRODUCT_INTELLIGENCE_DEMO=1 RTD_SITE_ROLE=combined \
  python -m sphinx -b html \
  -D extensions=myst_parser,tools.rtd.portal \
  -D rtd_knowledge_dir=/path/to/frozen/docs/knowledge \
  /path/to/frozen/docs/publish/web /tmp/product-intelligence-html
python -m http.server 8765 --directory /tmp/product-intelligence-html
```

打开本机服务下的 `/research/product-intelligence.html`。发布清单应位于
Web 源目录上一级的 `publish_manifest.json`；没有清单时不会从任意 HTML
或未发布的评审稿补造产品事实。构建读取冻结输入，不访问飞书，不写回源表。

同一次构建还生成两个可供 Agent 或独立应用读取的版本化 JSON：

- `_static/product-knowledge.v1.json`：逐发布变体的产品知识及证据指纹。
- `_static/product-intelligence.v1.json`：外部事件、关联、假设和研究历史。

两份 JSON 的知识快照指纹必须一致。JSON 是派生消费格式，不是新的产品主数据。

## 更新与人工判断

新手册通过正常审核发布后，下一次构建重新读取冻结资料。外部政策在已有业务
快照维护；其他研究事件和规则在工程侧研究案例配置维护。研究输入、来源和规则
变化会产生新的指纹，不能沿用旧的候选判断冒充新的审核。

保留前一次 JSON，再用 `compare_research_snapshots(previous, current)` 比较
事件和关联变化；历史输入与结果保留原指纹。人工判断通过案例的 review/history
记录进入下一次构建，Demo 不提供自动批准或产品源数据修改入口。
标为已复核时必须填写判断、复核人和 ISO 日期；后续修订重新待复核时，
前次人工判断仍保留在历史中。默认案例没有人工批准记录。

详细字段、所有权、复现测试与预览边界见
[实现契约](../../code-as-doc/dev/product-intelligence-contract.md)。
