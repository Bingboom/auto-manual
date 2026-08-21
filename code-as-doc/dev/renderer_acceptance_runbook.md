# 四渲染栈验收 runbook（S5）

Status: 可执行 · Owner: 夏冰 · 2026-08-21

骨架库纵向切片第 6 步的操作手册。工具是
[`../../tools/renderer_acceptance.py`](../../tools/renderer_acceptance.py)，
判据全部「一条命令 + 一个退出码/一次 grep」——切片方案不接受"看起来对"。

## 1. 一次完整跑法

S4 的数据与模板落地后，在**一个 worktree 里**构建再验收（见 §4 的两个坑）：

```bash
git worktree add /tmp/acc HEAD
cp -R data/phase2 /tmp/acc/data/            # phase2 是 gitignored 本地镜像
cd /tmp/acc
python build.py all --config configs/config.bp-us.yaml --model JBP-2000B --region US
python tools/renderer_acceptance.py \
    --config configs/config.bp-us.yaml --model JBP-2000B --region US \
    --block-pages 8
cd - && git worktree remove --force /tmp/acc
```

退出码 0 = 全部选中判据通过。加 `--json` 出机器可读报告。

主机线回归（贵，两次 worktree 构建，单独跑）：

```bash
python tools/renderer_acceptance.py \
    --config configs/config.bp-us.yaml --model JBP-2000B --region US \
    --renderers regression --base-ref origin/main \
    --regression-target configs/config.us.yaml:JE-1000F:US \
    --regression-target configs/config.ja.yaml:JE-1000F:JP
```

## 2. 判据与它们各自防的事

| 栈 | 判据 | 防什么 |
| --- | --- | --- |
| PDF | **页数等于公式** `F(L) + L·B + K` | 页数是印刷交付的硬预算。"差一页也行"不是可接受结果。公式已对 7 本出货书逐一命中（见 §3） |
| PDF | 全页同尺寸 | 混入异开本页 |
| PDF | xelatex 日志无 `Undefined control sequence` / `Missing $` | 宏缺失被静默吞掉 |
| HTML | **组合图类名零命中** | 这是**正向要求**不是容忍：新目标在 web 契约 `figure_targets` 白名单外，按设计只出朴素 HTML。有命中说明有人手工扩了白名单 |
| HTML | 存在手册样式表（并报出通道） | 两条通道产不同样式表（Sphinx 出 `hb_manual.css`、web_publish 出 `web_manual.css`），只断言一个名字会无故判红另一条通道 |
| Word | 产物存在 | Word 绑 config 层、与型号无关，是最省事的一栈 |
| IDML | **`layout_params.csv` 与已批准版式契约 git diff 为空** | 已批准的 JE-1000F/US 版式把**整份** CSV 进哈希——给别的目标加一行就静默脱钩（#720 事故形态）。评审纪律不是控制手段，空 diff 才是 |
| 回归 | 主机线双 worktree 逐字节相同 | LaTeX 组件库与版式参数表都是全局单例，切片不能在没证明"没伤到既有产线"的情况下宣称成功 |

## 3. 页数公式的边界（已实测，别外推）

`F(L) + L·B + K`，`K = 1`（共享封底）：

- **多语本** `F(L) = 1 + 2·⌈L/3⌉`（封面 + 前言页 + 目录页，三语共用一张）
- **单语本 `F = 2`**，**不是**上式的 L=1 情形——日规体例把前言并入封面。套多语公式会在每条单语线上多算一页

逐本验证（工具的单测把这张表钉住）：

| 本 | L | B | 出货书页数 |
| --- | --- | --- | --- |
| HTP017 美加规（切片目标） | 3 | 8 | 28 |
| HTP011 欧英规 | 5 | 8 | 46 |
| HTE153 美加规 | 3 | 18 | 58 |
| HTE159 欧英规 | 6 | 17 | 108 |
| HTE152 欧英规 | 6 | 19 | 120 |
| HTE157 美加规 Pro Max | 3 | 31 | 97 |
| HTE152 日规（单语） | 1 | 25 | 28 |

公式不适用时用 `--expect-pages N` 直接钉住（例如按出货书实测数）。

## 4. 两个会浪费时间的坑（本轮实测踩到）

1. **`--staging-root` 跑不了全量构建。** `build.py all` 的 HTML 步骤走 Sphinx，其扩展要求
   "owning repository tools package"，staging 根在仓库外时报
   `hb_latex_callouts requires the owning repository tools package`。构建要在
   worktree（完整 checkout）里做；`--staging-root` 只适合 `check`。
2. **新 worktree 没有 `data/phase2`**（gitignored 本地镜像），不拷进去每次构建都会在
   identity 解析处失败。回归判据的实现里已自动拷贝，手工跑要自己拷。

## 5. 一条待 S6 处理的既有分歧（本轮顺带测出）

`JE-1000F/US` 的**管线 PDF 是 66 页，出货书是 58 页**（同开本 368.79×524.69pt）。
即既有产线的管线产物与印刷交付物已有 8 页分歧。这不是切片引入的，也不在 S5 范围内，
但它是 S6 逐页对账的重要先验：**对账差异的基线不是零**。S6 报告应把这类差异归入
「管线缺口 / 手工层承担 / 数据缺口 / 接受的降级」四类之一，而不是默认管线应当逐页等于出货书。

## 6. 修订记录

- 2026-08-21：S5 交付；公式补单语情形；样式表判据改通道感知；记录两个构建坑与 66/58 分歧。
