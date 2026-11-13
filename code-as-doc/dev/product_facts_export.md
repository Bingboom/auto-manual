# 自有产品事实导出（product facts export）

Status: active · Owner: 夏冰 · Created: 2026-11-13

把已发布网页说明书里的自有产品规格，整理成一份带出处、带版本、可重复生成的机读文件
（`hello-docs-product-facts/v1`），供说明书站以外的系统直接读取，第一个使用方是
竞情分析工作台（私有仓库 Bingboom/Demo--auto）。产品矩阵页面和这份导出用同一套
读表规则，导出不另建事实来源。

定位依据：[Hello-Docs 定位](../architecture/Hello_Docs_Positioning.md) §4（面向查询、关联、比较
与复用，保留原文与出处，核验前只是派生候选）与 §6（已发布内容形成的派生视图）。

## 1. 内容

一条记录是一个型号在一个市场：

| 字段 | 内容 |
| --- | --- |
| `id`、`model`、`market` | `JE-1000D/US`、型号、市场 |
| `product` | 产品分类快照里的商品简称、所属产品（去掉颜色款词，如 `E1000V2沙金色` → `E1000V2`）、颜色款、产品类别、产品系列、容量档；快照未列出时为 `null`，并记一条 problem |
| `manual` | 读取的语言版本（英文优先，再按 `product_matrix.json` 的 `language_order`）、该版本的 `version`、发布时间、页面相对路径与完整网址、源文件路径与 SHA-256 |
| `editions` | 该市场所有语言版本的页面与版本 |
| `facts` | 规格表写到的数值：`value`、`unit`、`quote`（读出该值的那一行，`标签: 原文`） |
| `unknown` | 适用于该产品类别、但所读版本规格表没有写（或规则读不出）的属性 |
| `capabilities` | 能力表（`data/model_capabilities.csv`）里该型号该市场的开关；没有该行时为 `null`。项目号列不导出 |

文件还带 `attributes`（属性字典全文）、`guides`（通用指南、快速指南及其适用产品与页面，
它们不是产品，不进 `records`）、`differences`、`problems`、`summary` 和 `inputs`（发布清单、
产品分类快照、能力表、属性字典各自的哈希或日期）。文件里没有生成时间：输入不变，字节不变。

## 2. 属性字典

[`tools/product_facts/attributes.json`](../../tools/product_facts/attributes.json)
（`hello-docs-product-attributes/v1`）为每个数值定义一次键、中文名、英文名、单位、类型、维度、
所依据的产品矩阵读数（`field`）和适用的产品类别（`applies_to`）。现有 9 项：标称容量、
AC 额定输出、AC 峰值输出、重量、循环寿命、太阳能板 STC 功率、防护等级、输出功率、扩展电池接口。

使用方把自己的字段映射到这些键，不要按名字猜。已知容易混的：

- 竞情工作台的 `rated_w`（额定输出）对应 `ac_rated_w`；`capacity_wh`、`weight_kg` 同名同义。
- 竞情工作台的 `solar_w` 是储能电源的太阳能**输入上限**；`panel_power_w` 是太阳能板自己的
  STC 功率，两者不能对应。规格表的太阳能输入上限目前没有读数。
- 扩展电池接口只有“规格表写了”才记 `true`；没写算未知，不算没有。

## 3. 出处、差异与边界

- 每个数值都是说明书所写，按产品矩阵规则读出，**未经人工核实**（文件 `basis` 字段写明）。
  核实与否由使用方记录，不回写这里。
- 一个市场的数值不会搬到另一个市场。同一产品不同记录写法不一的数值列在 `differences`，
  由人判断是区域规格本来不同，还是说明书写错；导出不替人挑一个。
- 规格表规则只认英文、中文、日文标签，所以每个市场读最靠前的这几种语言版本；只有其他语言
  版本的市场会多出 `unknown`。
- 只含已发布内容，不含项目号、SKU、竞品、拆机或内部规格资料；后者只放在使用方自己的存储里，
  不回流到 auto-manual 或 Hello-Docs。

## 4. 运行

在持有发布目录的仓库（Hello-Docs）根目录运行，只读，不联网：

```bash
python -m tools.product_facts                              # 只打印汇总和 problems
python -m tools.product_facts --out product_facts.json     # 写出导出文件
python -m tools.product_facts --check product_facts.json   # 文件不是当前导出时退出 1
```

`--root` 指向另一个检出，`--assets` 指向另一份 portal 资源目录（设置、产品矩阵配置、
产品分类快照）。代码在 [`tools/product_facts/`](../../tools/product_facts/)，测试在
`tests/test_product_facts.py`。

## 5. 分发与使用方

- **待定：** 导出文件放在哪里供使用方读取（每日数据刷新提交进 Hello-Docs，或使用方在本机
  检出上运行命令），确定后补在这里。现在只能在检出上运行命令得到文件。
- **竞情工作台（Demo--auto）：** 计划新增资料类型「说明书」，由工作台自己拉取这份导出、写进
  它的「资料」「证据」表，与官网采集值并排；不一致时按它自己的规则标「来源说法不一」。
  这部分在工作台仓库里实现。
