# 存量 Markdown → 手册样式网页

把已有的 `.md`（手写的、云文档导出的、流水线产出的）渲染成和线上 web 手册同一套样式的自包含静态站。

在仓库里跑，不需要额外准备：样式直接取自 [`docs/renderers/contracts/`](../docs/renderers/contracts/) 的三份契约 CSS（经 [`tools/web_stylesheets.py`](../tools/web_stylesheets.py) 拼接），渲染栈用仓库 `.venv`（sphinx / myst-parser / furo，与线上构建同版本）。

**这不是发布通道。** 线上 Read the Docs 只渲染 `docs/publish/web` 的冻结快照；本工具拒绝写入 `docs/_build`、`reports/releases`、`docs/publish`。

## 两步

```bash
.venv/bin/python tools/plain_markdown_site.py --source <存量目录> --to-intermediate <中间态目录> --download-images
```

产出**中间态 md**：脚本把云导出压坏的表格还原成语义指令（警示框、规格表、LCD 表…），认不准的原样留成管道表格并加一行注释。这是普通 md，`git diff` 得动，该改就改。

```bash
.venv/bin/python tools/plain_markdown_site.py --source <中间态目录> --output-dir <站点目录> --title "文档标题" --strict
```

产出站点，`index.html` 就是效果。这一段没有猜测：指令由 [`tools/manual_md_directives.py`](../tools/manual_md_directives.py) 编译成契约组件标记。

常用开关：`--download-images` 把远程图拉到本地（唯一联网的开关）；`--keep-tables` 不做表格升级；`--manifest inventory.csv` 批量（列 `source,title,section,order`）；`--strict` 警告即错误，出包时带着。

## 中间态能写的标记

除下面 8 个围栏指令外全是标准 CommonMark/MyST。写法：

````
```{指令名} 参数
数据行 | 数据行
```
````

| 指令 | 参数 | 行格式 | 空格子合并 |
|---|---|---|---|
| `callout` | 信号词，自动转大写，默认 `NOTE` | 正文按**完整 Markdown** 解析 | — |
| `spec-table` | 分节名 | `标签 \| 值` | 标签留空 → 并入上一个标签（**只看第一列**） |
| `troubleshooting` | 分节名 | `代码 \| 措施` | 不合并 |
| `lcd-icons` | 分节名 | `序号 \| 图 \| 名称 \| 说明`（固定 4 列） | 不合并 |
| `symbols` | 分节名 | `图 \| 含义`，自动对半分左右两栏 | 不合并 |
| `comparison` | `左表头 \| 右表头` | `左 \| 右`（固定 2 列） | 每列独立 |
| `lcd-mode` | 一张图（标准图片语法） | `状态 \| 动作 \| 说明`（固定 3 列） | 每列独立 |
| `manual-table` | 分节名 | 任意列数，可选 `:headers: A \| B \| C` | 每列独立 |

信号词：`WARNING` `CAUTION` `NOTE` `TIP` `DANGER` `IMPORTANT` `NOTICE` `ATTENTION`。

`troubleshooting` 的措施列、`lcd-icons` 的说明列里用 ` / `（前后各一空格）分隔 → 渲染成竖排步骤。

图片格只有三处：`lcd-icons` 第 2 列、`symbols` 第 1 列、`lcd-mode` 的参数位；别处写图片会被当成纯文字。

例：

````
```{callout} CAUTION
- **USB-C 100W** is a high-power output port.
- Only connect devices that comply with IEC/EN/UL 62368-1.
```

```{spec-table} INPUT PORTS
1 × AC Input | Charge Mode: 100V-120V~60Hz, 15A max.
 | Bypass Mode<sup>①</sup>: 100V-120V~60Hz, 12A max.
2 × DC8020 Ports | 11V-16V⎓8A Max
```
````

## 单元格里能写什么

**只有 `callout` 的正文是完整 Markdown。** 其余 7 个指令的单元格只认四种行内标记：

`**粗体**`、`^上标^`、`~下标~`，以及标准 Markdown 图片语法（仅图片格）。

斜体、链接、行内代码、列表、裸 HTML 都不行——会原样打印，`< > & "` 还会被转义。需要这些就用 `callout`，或把内容留在指令外面的正文里。

## 三个坑

- **单元格里的 `|` 转不了义。** 第一段会写成 `\|`，但第三段是直接 `split("|")`，不认转义：`A \| B | v` 被切成三格且残留反斜杠。正文里改用全角 `｜` 或 `/`；非要竖线就放 `callout`。
- **`troubleshooting` 的表头改不了**，固定 `Error Code` / `Corrective Measures`（`:headers:` 只有 `manual-table` 支持，写在别处会报未知选项）。要自定义表头就换 `manual-table`。
- **`:class:` 写了不生效**，8 个指令都声明了这个选项但渲染时忽略。

## 排错

| 现象 | 原因 |
|---|---|
| `Unknown directive type` | 用了别的解释器/没走本脚本；照上面的命令跑 |
| 表格顶上有灰色空条 | 那是管道表格，说明这张表还没改成指令 |
| 该合并的地方是空白框 | `spec-table` 只按第一列合并；要按其它列合并换 `manual-table` |
| 单元格被切成两半 + 残留 `\` | 内容里有 `|`，见上一节 |
| 图片不显示 | 忘了 `--download-images`，或图片写在了非图片格 |

看到中间态里这行注释，就是脚本没认出这张表，按提示改成对应指令后删掉它：

```
<!-- md-site: unclassified table; consider {lcd-icons}, {symbols}, {troubleshooting} or {comparison} -->
```

## 边界

带引线标注的操作图、前视图靠逐图百分比坐标，是流水线独有的，这里只能退化成"图 + 标签表"。字体 Gilroy 是商业授权不随站分发，网页回退到 Avenir Next 一档。

流水线产出的手册 `.md` 原样喂进来即可（带 `hb-*` 组件标记，样式完整）；**不要**先用 `pandoc -t gfm-raw_html` 降级成纯 md——实测在 `JE-1000F / US` 上会静默丢掉约三分之一正文、26 张图、38 个表格。
