# 生产素材入飞书多维表：表结构与 dry-run

Status: proposed

Updated: 2026-10-12

2026-10-12 已执行，都已回读核对（见 §9）：
- §4 的表结构变更；
- 205 个已有导出物行的补字段；
- 操作者说「入库」后的第一批写入：53 个母版、281 个定义、1069 个导出物连同附件。

下一步是 §9 第 3 步的同步命令。

dry-run 已实现：[`tools/asset_pipeline/base_inventory.py`](../../tools/asset_pipeline/base_inventory.py) 负责盘点，[`base_reconcile.py`](../../tools/asset_pipeline/base_reconcile.py) 负责和线上表对账。两者都只读工作区和事先保存的线上快照，不调用飞书。Base 结构变更和线上写入，都要等操作者确认后才做。

## 1. 目标

**日常只在多维表一个地方管图；仓库里那份是同步命令生成的副本。**（操作者 2026-10-12 确认的方向。）

- 仓库里有四个目录的生产素材，共 1274 个文件。它们都要进 `文档构建` Base：每个文件一行，附件就是这份文件本身。
- 不新建表，沿用 [AI 母版入库](asset_ai_master_intake_plan.md)建好的三张 `04_资产*` 表。旧插图表 `tblxFBWaDG4OYhqu` 照旧不读不写。
- 新图、换图只在 Base 里上传和审批。审批通过后，由同步命令下载、校验哈希，再开 PR 写进仓库。仓库里的图不再手工改。
- 构建、CI 和 Read the Docs 仍然读仓库里的副本，不依赖飞书在线。这样构建可重复，PR 审查和回退也照旧可用。

## 2. 以谁为准

| 内容 | 以谁为准 | 说明 |
|---|---|---|
| 图片本身（新增、替换） | `04_资产导出物.export_file` | 唯一的维护入口；一行一个文件 |
| 仓库里的图 | 同步命令 | Base 的副本，只经同步 PR 更新；构建、CI、RTD 都读它 |
| 这张图是什么、能不能构建：类别、语言维度、状态、待无字化、适用机型/区域、语言变体 | `04_资产定义` | 现有规则不变：`sync-data` 把这几列镜像进 `data/asset_registry.csv`（[`tools/sync_asset_registry.py`](../../tools/sync_asset_registry.py)），只覆盖、不删行 |
| 注册表里的导出物路径和内容哈希 | 同步命令 | 按导出物行的 `repo_path` 和 `content_sha256` 写入；`sync-data` 不碰这两列 |
| 附件和仓库是否一致 | 对账 | 每次同步都核对 SHA-256，结果写进 `对账结果` |

过渡期：同步命令上线之前，仓库里的图仍可能经 PR 直接改。每次改完要重跑 dry-run 对账，把变化补进 Base。同步命令上线后，方向固定为只从 Base 到仓库。

## 3. 三张表各放什么

以下是第一批写入前、对照 2026-10-12 线上快照得出的数字。写入后的行数见 §9。

**`04_资产源文件`**：一个设计母版（`.ai`/PDF）一行。
- 线上已有 4 行，保留不动。
- 要新建 53 行：
  - `data/asset_sources.csv` 已登记、但表里还没有的母版；
  - 配方或插图清单引用了、却没有登记的 42 个，标 `needs_review`。
- 母版文件不在 Git 里，这里只登记元数据。附件归档仍按 AI 母版入库流程逐个做。

**`04_资产定义`**：一个稳定的 `asset_key` 一行。线上已有 223 行。
- 注册表的 479 个 key 里，198 个已在表里，保留不动；另外 281 个要新建，拼写与注册表完全一致（见 §8）。
- 表里另有 25 个注册表没有的定义：13 个 JS-100I 插图和 12 张太阳能图。其中 20 个已经是仓库文件的身份，dry-run 直接沿用（见 §6）。
- 其余 688 个是 dry-run 的建议定义，要走注册表晋级，不在第一批上传：
  - 插图清单绑定的 462 个；
  - 只能按目录推出 key 的 161 个；
  - 符号清单 62 个；
  - 按键清单 3 个。

**`04_资产导出物`**：一个实际文件一行，`export_file` 附件里只放这一份文件。线上已有 461 行。
- 仓库文件的行，`export_key` 统一写成 `registry::<仓库路径>`。这是线上已有的写法，与入库行（`<source_key>::artifacts/...`）、网页组合图行（`web-composite/...`）各占一个命名空间。
- 205 个仓库文件 2026-09-08 已经传过，附件齐全，字节与仓库完全一致。它们空着的 `artifact_kind`、`gate_status`、`size_bytes` 等字段，2026-10-12 已经补齐（见 §9）。
- 其余 1069 个要新建。

暂存 CSV 的列按以下顺序排：
1. 表里已有的字段；
2. 建议新增的字段；
3. 只供审阅、不上传的列，如 `registered_in`、`key_origin`、`needs_review`、`action`。

## 4. 表结构变更

操作者 2026-10-12 同意后已在线上执行，每个字段都回读核对过。新字段的 ID：

| 表 | 字段 | 类型 | ID |
|---|---|---|---|
| `04_资产导出物` | `像素尺寸` | 文本 | `fldg6efQBd` |
| `04_资产导出物` | `透明通道` | 复选框 | `fldu9VGDQJ` |
| `04_资产导出物` | `对账结果` | 文本 | `fldNqYriGQ` |
| `04_资产定义` | `中文说明` | 文本 | `flddo4JMAj` |

单选字段只追加选项，原有选项和颜色都保留；字段 ID 不变，改前改后各选项的行数完全一致。逐项如下：

`04_资产导出物`：
- `artifact_kind` 加四个选项：`web-shared`、`web-target`、`print`、`word`，分别对应四个目录。现有的 `archive-page`、`preview`、`semantic-export`、`web-composite` 不动。
- `gate_status` 原有 `approved`、`archive`、`quarantine`，加了 `temporary` 和 `pending`：
  - `temporary` 沿用定义表现成的值，给 🔧临时替代 的文件用；
  - `pending` 给还没人定状态的文件用。
- `format` 原有 pdf、png、jpg、jpeg、svg，加了 `webp`，有 24 个文件是 WebP。
- 新增三个字段：
  - `像素尺寸`：文本，如 `2131x491`；SVG 填 viewBox 尺寸，PDF 不填；
  - `透明通道`：复选框；
  - `对账结果`：文本，记录附件哈希与仓库是否一致。
- 语言写进现有的自由文本字段 `locale`。`web_locale` 是 web-composite 门禁读的单选（en/fr/es/shared），不加选项。

`04_资产定义`：
- 新增 `中文说明`（文本，写含义和用法）。由操作者逐步补，dry-run 不填。
- `gate_status` 已有 `approved`、`temporary`、`missing`、`quarantine`、`archive`，够用。
- 线上已有 `override_for` 和 `preview` 两个字段；它们的 ID 现在也冻结进了 [`data/asset_base_bindings.json`](../../data/asset_base_bindings.json)。dry-run 会原样带上注册表的 `override_for`。`preview` 是供画廊视图浏览的预览图，不是构建输入。

`04_资产源文件`：不改。新建的元数据行，`archive_status` 填现有的「待校验」。

新字段 ID，连同线上已有、但之前没冻结的 `override_for`（`fldJp29f3p`）和 `preview`（`fldGtEpu8Y`），已经写进 `data/asset_base_bindings.json`。业务 Base 结构清单 [`bitable_schema/business_base_manifest.json`](../../bitable_schema/business_base_manifest.json) 里，三张资产表也已同步；其他表的结构漂移见 §13。

与最初方案相比有三处改动：
- **不加 `withdrawn` 门禁选项。** 符号清单撤回的 11 张旧位图都在 Word 目录里，只是网页不再用；改用撤回门禁，会把 Word 和印刷也一起挡住。它们按各自的注册表行定门禁（目前都是 `approved`），备注里写明「网页符号清单已撤回这份位图」。
- **不加 `渲染面`。** 目录归属已经由 `artifact_kind` 表达。要逐个文件说清哪个渲染器真的在用，得先做一次引用普查。
- **门禁沿用定义表的词汇**：🔧临时替代 用 `temporary`，❌缺失 用 `missing`，不再统一写成 `pending`。

## 5. 四个目录怎么进表

数据来自 main `1fcac3d` 和 2026-10-12 的线上快照。

| 目录 | `artifact_kind` | 文件数 | 线上已有 | 门禁 |
|---|---|---|---|---|
| `docs/renderers/web/assets/shared/` | `web-shared` | 77 | 0 | approved 4，pending 73 |
| `docs/renderers/web/assets/<机型_区域_语言>/` | `web-target` | 941 | 18 | approved 318，pending 623 |
| `docs/renderers/latex/assets/` | `print` | 196 | 133 | approved 185，quarantine 6，temporary 4，pending 1 |
| `docs/templates/word_template/common_assets/` | `word` | 60 | 54 | approved 59，pending 1 |

- 合计 1274 个文件，234 MB；最大的一个 4.0 MB，可以逐个作为附件上传。
- 格式：PNG 1016、SVG 130、PDF 101、WebP 24、JPG 3。

## 6. 文件的身份怎么定

按以下顺序，取第一个命中的规则：

1. **共享清单按路径列出的文件**：用清单里的 key，如 `warning/outline-triangle-tinted`、`button/power`。
2. **注册表某行按路径列出的文件**：用那一行的 `asset_key`。
   - 路径用注册表自己的解析函数 [`registered_exports`](../../tools/asset_registry.py) 求出，与 `asset-check` 校验的是同一批文件；
   - 其中包括 `v2-` 标签投影到 LaTeX 目录的规则。
3. **注册表没列出这个文件名，但字节与某行的导出物相同**，而且文件在那一行用到的目录里：算作这一行的副本。Word 和 LaTeX 会各用自己的文件名存一份。照样用那一行的 key，同时报 `registry-copy`，并标 `needs_review`。
4. **机型插图清单绑定的文件**：
   - 目录里已有登记的文件时，按它们的拼法推出 key。注册表里两种拼法并存，如 `web/je1000h/eu/de/charging_ac` 和 JA 系列的 `web/ja-ad01a/eu/en/inbox-charger`；同一目录内拼法一致，所以新文件跟着邻居走。
   - 目录里没有登记文件时，用注册表的多数拼法：`web/<去掉连字符的机型>/<区域>/<语言>/<文件名>`；多种语言共用一个文件时，语言段写 `shared`。
5. **以上都没有命中**：按目录推出 key（`lcd/shared/<名称>`、`print/<路径>`、`word/<路径>`、`web/<目录>/<文件名>`），并报 `unregistered-file`。

第 4、5 步推出的 key 都是建议值，标 `needs_review`。

**有线上快照时**，第 4、5 步的建议要让位给 Base 已有的写法：
- 文件在 Base 里已有行，就用那一行的 key。例如 `js100i_eu_en` 的 13 个文件，Base 用的是 `web/js-100i/eu/en/...`，报 `live-key`。
- 建议的 key 和 Base 里某个定义重合，也用 Base 的定义。
- 两种情况下，门禁都取 Base 定义的状态。
- 例外：建议的 key 如果是注册表某一行的 key，就不沿用那一行的状态。
  - 注册表行只批准它按路径和哈希列出的文件。这个文件不在其中，否则第 2 步就已经命中。
  - 这样的文件保持 `pending`，报 `registry-key-elsewhere`。
  - 例如 `je2000f_eu_en/charging_ac.png`：它的建议 key 与注册表行 `web/je2000f/eu/en/charging_ac` 相同，但那一行批准的是 `je2000f_eu_en_full_frames/` 里的另一份字节。
- 注册表命名的文件不让位；如果 Base 那一行用了别的 key，报 `live-key-differs`，交操作者判断。

## 7. 门禁（gate）

只有有人定过的状态能放行：注册表行的状态，或者 Base 里已有定义的状态。

| 状态 | `gate_status` |
|---|---|
| ✅成品 | `approved` |
| ⛔隔离 | `quarantine` |
| 🔧临时替代 | `temporary` |
| ❌缺失 | `missing` |
| 还没人定 | `pending`，等操作者在定义表定了状态再放行 |

`build_eligible` 只在 `approved` 时为 TRUE。`visual_review_required` 在非 `approved` 时为 TRUE，与 intake 的做法一致。

几个具体情况：
- 共享符号清单的 62 个条目，清单里自己写着「registry promotion pending」或「publication pending」，所以都是 `pending`；清单状态写进备注。
- 按键清单有 7 个 SVG：
  - `button/power`、`button/ac`、`button/dc_usb`、`button/led` 是注册表里的 ✅成品行，所以是 `approved`；
  - JHP-3600C 的 3 个底部按键不在注册表里，是 `pending`。
- 撤回的 11 张旧位图见 §4。

## 8. 与 sync-data 的关系

`sync-data` 读取线上的 `04_资产定义` 后会做三件事：
1. 把 Base 管的几列覆盖到注册表里同一 key 的行；
2. 注册表里没有的 key，追加成新行；
3. 用注册表的加载器重新解析整张表，解析失败则整个同步失败。

dry-run 用同一个合并函数做了两次预演，结果写在 `summary.json` 的 `registry_sync_preview` 里。

**只看仓库**（`registered_definitions`）：注册表的 479 个定义按原样上传后，与现在的 `data/asset_registry.csv` 逐字节相同。

**加上线上快照**（`next_sync_after_upload`），也就是第一批上传后下次 `sync-data` 看到的样子：
- 加载器检查通过，同步不会失败。
- 会改 6 行，都是 Base 和注册表已经不一致的地方，与这次上传无关：
  - `page/jbp2000b_eu/cover`：Base 是按语言、en，注册表是中立。
  - 5 张太阳能图：Base 是「太阳能板与连接图 / 中立」，注册表是「插图 / 按语言 / en」。涉及 `web/je1000h/eu/en/charging_solar`、`web/je2000f/eu/en/charging_solar_adapter`、`web/je2000f/eu/en/charging_solar_direct`、`web/je3000c/eu/en/charging_solar`、`web/je300d/eu/en/charging_solar`。
- 会追加 25 行，是 Base 里已有、注册表没有的定义（13 个 JS-100I 插图，12 张太阳能图）。

由此有四条约束：

- **这 6 处不一致要先定以哪边为准。** 不管这次传不传，下次 `sync-data` 都会把 Base 的值写进注册表。注册表对的话，先改 Base；Base 对的话，让同步去改注册表。
- **上传之后，479 行由 Base 说了算，维护方式要跟着变。**
  - 类别、状态、适用范围等列以后要在 Base 里改；直接改 CSV 的话，下次 `sync-data` 会被覆盖回去。
  - 注册表里有 224 行的备注写着「未写线上 Base」，说明目前很多行是直接在 CSV 里维护的。
- **688 个建议定义现在不能上传。**
  - 下次 `sync-data` 会把它们全部追加进注册表；而它们的状态都是空的，加载器会拒绝（`unknown status ''`），`sync-data` 会直接失败。
  - 它们要走注册表晋级：
    1. 操作者按目录或机型分批确认 key、类别和状态；
    2. 一个仓库 PR 把这些行连同导出物路径和哈希加进注册表；
    3. 合并后再上传对应的 Base 定义，这样又是一次无变化的往返。
- **不能出现重复的 `asset_key`。**
  - [`tools/sync_web_composites.py`](../../tools/sync_web_composites.py) 遇到重复的 key 会直接报错。
  - 所以上传只新建快照里没有的 key；已有的 key 只读对比，不覆盖。

导出物行不受影响：`sync-data` 只读 `artifact_kind=web-composite` 的导出物行，新加的四种类型不会进入构建。

## 9. 入库流程

**第 0 步：dry-run 和线上快照（本 PR）。** 先只读保存线上快照（§11），再带上 `--live-snapshot` 跑 dry-run。每行都会得到一个动作，交操作者核对，重点看 §12。

**第 1 步：结构变更（2026-10-12 已完成）。** 见 §4。

**第 2 步：第一批写入（2026-10-12 已完成）。** 只在操作者明确说「入库」后才做。
- 写之前重新保存一次快照、重跑 dry-run，确保动作是按最新线上状态算的。
- 按动作执行：
  - `create`：新建 53 个母版元数据行、281 个注册表定义、1069 个导出物行；导出物的附件取自 `repo_path`。
  - `fill`：只补已有导出物行里空着的字段，列在 `fill_fields` 里。这是改现有行，要操作者单独同意。2026-10-12 已对 205 行执行，见下方记录。
  - `keep`：不动。
  - `propose`：等第 3 步晋级。
- 导出物能关联到定义的就关联；定义还在建议阶段的，先只填 `asset_key` 文本，晋级后再关联。
- 每写一行都回读，核对 `record_id`、`export_key`、`content_sha256`，并确认附件的 `file_token` 不为空。
- 写完后把附件全部下载下来比对 SHA-256，结果写进 `对账结果`。
- 上传和下载都用 lark-cli 1.0.49 的 `+record-upload-attachment` 和 `+record-download-attachment`。云环境现有的网络设置就够用，不需要另外放行域名。
- 不删行；已有的定义、入库行和网页组合图行一律不改。

2026-10-12 补字段记录：
- 操作者同意后，按当天的快照和 dry-run，逐行 PATCH 了 205 个 `registry::` 行。只写 `fill_fields` 列出的字段，共 1005 个值：
  - `artifact_kind`：print 133、word 54、web-target 18；
  - `gate_status`：approved 201、temporary 4；
  - 另有 `size_bytes`、`build_eligible`、`visual_review_required`、`source_key`、`source_page`、`像素尺寸`、`透明通道`。
- 写完重新保存快照，逐行核对：
  - 1005 个值全部与计划一致；
  - 这 205 行的其他字段一个没变，附件都在；
  - 计划外的 256 行没有任何变化，总行数仍是 461。
- 用写后的快照重跑 dry-run，这 205 行都变成 `keep`。

2026-10-12 第一批写入记录：
- 操作者说「入库」后，先重新保存快照。它与 dry-run 用的快照逐行相同：母版 4 行、定义 223 行、导出物 461 行。
- 用 `+record-batch-create` 新建，每批最多 200 行：
  - 母版 53 行，`archive_status` 都是「待校验」。
  - 定义 281 行，拼写与注册表一致。有 `source_key` 的 266 行同时关联了 `source_record`。
  - 导出物 1069 行，`export_key` 都是 `registry::<仓库路径>`：
    - 定义已在 Base 里的 379 行关联了 `asset_record`；其余 690 行的定义还在建议阶段，只填 `asset_key` 文本；
    - 有 `source_key` 的 757 行关联了 `source_record`。
- 附件按 main `623d163` 的文件逐行上传，共 192.9 MB。每行上传前先读一次单元格，已经有附件就跳过，所以重试不会传出第二份。
- 回读：每张表写完都重新保存快照，逐格核对：
  - 新行与写入用的数据逐格一致，关联也一致（这份数据有 8 行偏离了计划，见下文）；
  - 每个新导出物行恰好一个附件，`file_token` 与上传返回的相同，文件名和大小也对；
  - 原有的行一个没变；
  - 写完后三张表分别是 57、504、1530 行。
- 下载比对：1274 个 `registry::` 行的附件全部下载，包括新建的 1069 行和原有的 205 行。
  - SHA-256 都与 `content_sha256` 和仓库文件相同。
  - `对账结果` 统一写成「一致：附件 SHA-256 与 content_sha256、仓库文件相同（2026-10-12 下载核对，main 623d163）」。
  - 写后的快照显示只有这一列变了；256 个入库行和网页组合图行没动。
- 用写后的快照重跑 dry-run（规则修正之前）：
  - 母版 57 行、导出物 1274 行全部是 `keep`；定义 `keep` 499，待晋级 688；修正规则后的结果见 §12；
  - 下次 `sync-data` 仍然只改原有的 6 处不一致，并追加 25 个 Base 独有定义；这批新定义不改注册表，加载器检查通过。
- 原有的 205 个 `registry::` 行里只有 1 行关联了 `asset_record`。补关联要改现有行，留给操作者决定。
- 写完后逐行对照计划，发现 `je2000f_eu_en/` 下有 8 个文件按 `approved` 建了行，而计划里它们是 `pending`。
  - 原因：建导出物用的是定义写入之后的 dry-run。这 8 个文件的建议 key 与刚写进 Base 的注册表定义同名，dry-run 就沿用了那几条定义的 ✅成品。
  - 但那几行注册表批准的是 `je2000f_eu_en_full_frames/` 里的另一份字节。规则已在 §6 修正，加了测试。
  - 这 8 行已改回计划里的值：`gate_status` 为 `pending`，`build_eligible` 取消，`visual_review_required` 勾选。回读核对过，其他行都没变。
  - 改完后，线上 1274 个 `registry::` 行的门禁和 `asset_key`，与批准的计划逐行一致：approved 566、pending 698、quarantine 6、temporary 4。
- 同一目录下还有 2 个太阳能裁图：`charging_solar_adapter.png` 和 `charging_solar_direct.png`。
  - 它们的建议 key 与上传前就在 Base 里的定义同名，所以计划里本来就是 `approved`。
  - 按修正后的规则，它们应为 `pending`。操作者确认后，这两行也已同样改为 `pending`，回读核对过，其他行都没变。
- 现在线上 1274 个 `registry::` 行的门禁，与修正后的 dry-run 逐行一致：approved 564、pending 700、quarantine 6、temporary 4。

**第 3 步：同步命令（Base → 仓库）。** 这是日常流程的核心，参照 `sync_web_composites` 实现：
- 只取 `approved`、`build_eligible`、恰好一个附件，且附件 SHA-256 等于 `content_sha256` 的行。
- 下载到 `repo_path`，校验哈希；同时更新注册表里的导出物路径和内容哈希。
- 结果以 PR 的形式提交，不直接推送；PR 里列出新增、替换和对账结果。
- 不自动删文件：Base 里不再可用的行只列出来，由人确认后再删。

**第 4 步：后续批次。** 按 §8 分批晋级 688 个建议定义。

**日常：**
- 新图、换图只在 Base 里做，同步命令把结果带进仓库。
- 过渡期仓库里的图如果直接改了，重跑 dry-run，按动作补进 Base：字节变了用 `update-file`，Base 那一行的旧哈希留在备注里；文件删了会报 `orphan-export`，只在备注里标记，不删行。

写入用 lark-cli，按仓库约定的 `--profile prod --as bot`，步骤按 [`lark-cli-bitable-ops`](../../.agents/skills/lark-cli-bitable-ops/SKILL.md) 来。

## 10. 不放进表的内容

- **已发布说明书的冻结包**：`manual_sources/` 下 9319 个图片/PDF，`data/manual_sources/` 下 2245 个。它们是封存的字节副本，哈希已记在发布清单里。
- **验收截图和证据、构建产物、测试夹具**：`code-as-doc/`、`reports/`、`docs/_build/`、`data/asset_evidence/`、`tests/fixtures/`。web-composite 的冻结附件也在夹具里，它们本来就是 Base 里的行。
- **`.ai` 母版**：不在 Git 里，按 AI 母版入库流程归档到 `04_资产源文件.source_file`。
- **RTD 门户的产品图**：`tools/rtd_portal_assets/_static/`，门户用图，不是说明书素材。

待定：`docs/renderers/contracts/assets/` 下还有 32 张图，注册表没有登记。其中少数被 Web 呈现契约和 FridgeGuard 的 App 页直接引用，比如 `app_store_badges.png`、`app_add_device_steps.png`。要不要把它作为第五个目录纳入，由操作者决定；纳入的话，`artifact_kind` 需要再加一个选项。

## 11. dry-run 用法

先只读保存线上快照。表 ID 来自 `data/asset_base_bindings.json`，每页最多 200 行：

```bash
SNAP=<新的快照目录>; BASE=LD3lb4G1ua4GOVs1vxAc9W2enje; mkdir -p "$SNAP"
for pair in sources:tblsXlZx61Ff5pQC definitions:tblWilXeN5FXPraC exports:tblavT0dcjZGK9DR; do
  table=${pair%%:*}; id=${pair#*:}; offset=0; page=0
  while :; do
    out="$SNAP/${table}_records_${page}.json"
    lark-cli --profile prod base +record-list --as bot --base-token "$BASE" --table-id "$id" \
      --limit 200 --offset "$offset" --format json > "$out" || break
    rows=$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["data"]["record_id_list"]))' "$out")
    [ "$rows" -lt 200 ] && break
    offset=$((offset + 200)); page=$((page + 1))
  done
done
```

然后跑 dry-run：

```bash
python -m tools.asset_pipeline.base_inventory --output-dir <新的或空的目录> [--live-snapshot "$SNAP"]
```

- dry-run 只读以下输入，不调用飞书：
  - `git ls-files` 列出的四个目录；
  - 注册表、共享清单和机型插图清单；
  - 配方和 `data/asset_sources.csv`；
  - 给了 `--live-snapshot` 时，再加上快照里的 `<表>_records_<n>.json`。
- 输出目录必须是新的或空的，并且不能位于 `docs/`、`data/`、`tools/` 下面。
- 输入或快照读不了时，退出码为 2。
- 处理 1274 个文件约 2 秒。

输出文件：

| 文件 | 内容 |
|---|---|
| `asset_sources.csv` | `04_资产源文件` 的待入库行 |
| `asset_definitions.csv` | `04_资产定义` 的待入库行：注册表原样的行、Base 已有的行、建议定义 |
| `asset_exports.csv` | `04_资产导出物` 的待入库行，含仓库路径、字节数、SHA-256、像素尺寸和透明通道 |
| `findings.csv` | 问题清单：类型、对象、说明 |
| `summary.json` | 行数、各类计数、`registry_sync_preview` 和 `live_actions` |

有快照时，每行多三列：
- `action`：`create`、`keep`、`fill`、`update-file` 或 `propose`；
- `live_record_id`：对应的线上记录；
- `fill_fields`：只在导出物行上有，列出要补的字段。

CSV 带 UTF-8 BOM，Excel 和飞书导入都能直接认出中文。多值字段沿用注册表的逗号分隔；只供审阅的列表列用分号分隔。

问题类型：

| 类型 | 含义 |
|---|---|
| `unregistered-file` | 没有任何清单或注册表行列出这个文件 |
| `unregistered-master` | 配方或插图清单引用的母版，`data/asset_sources.csv` 里没有登记 |
| `source-key-alias` | 配方用了另一个 `source_key`，但哈希与某个已登记的母版相同 |
| `ambiguous-registry` | 多个注册表行按路径列出了同一个文件 |
| `registry-copy` | 文件名没有登记，但字节与某行的导出物相同（见 §6 第 3 条） |
| `hash-mismatch` | 清单或注册表声明的哈希与文件不符 |
| `duplicate-bytes` | 多个路径存着相同的字节 |
| `withdrawn-copy` | 撤回的旧位图在别处还有一份 |
| `missing-file` | 清单列出的文件不在工作区里 |
| `mixed-key-prefix` | 同一目录里已登记的 key 用了不同的前缀 |
| `illustration-without-path` | 插图清单的条目没有可用的路径 |
| `live-key` | 采用了 Base 已有的 key，而不是 dry-run 的建议 |
| `live-key-differs` | 注册表命名的文件，Base 那一行用了别的 key |
| `registry-key-elsewhere` | 建议的 key 是注册表某一行的 key，但那一行列出的是别的文件；这个文件保持 `pending`（见 §6） |
| `stale-attachment` | Base 里这个仓库文件的附件已经过时，要 `update-file` |
| `stale-intake-export` | 入库行指向的仓库文件后来改过，入库附件是旧字节 |
| `orphan-export` | Base 里有行，但仓库四个目录里已经没有这个文件 |
| `base-drift` | Base 和注册表对同一定义的类别、语言等不一致，下次 `sync-data` 以 Base 为准 |
| `base-only-definition` | 只在 Base 里有的定义，下次 `sync-data` 会追加进注册表 |
| `duplicate-live-row` | 线上表里同一个 key 有多行 |

## 12. 当前盘点结果

数据来自 main `1fcac3d` 和 2026-10-12 第一批写入前的线上快照。

第一批写入后，用修正后的规则（§6）在写后快照上重跑：
- 母版都是 `keep`，定义只剩 688 个待晋级。
- 导出物 1274 个全部 `keep`。
- 新增 `registry-key-elsewhere` 10 个，所以需要复核的导出物是 705 个。
- 暂存的门禁是 approved 564、pending 700、quarantine 6、temporary 4，与线上逐行一致。
- 其余问题的数量都没有变。

**总量**
- 57 个母版、1187 个定义、1274 个导出物。
- 门禁：approved 566、pending 698、quarantine 6、temporary 4。
- 需要复核：母版 42、定义 688、导出物 703。

**对照线上的动作**
- 母版：新建 53，保留 4。
- 定义：新建 281，保留 218，待晋级 688。
- 导出物：
  - 新建 1069；
  - 补字段 205，其中 `artifact_kind`、`gate_status`、`size_bytes` 每行都要补。2026-10-12 补完后，这 205 行变为 `keep`；
  - 没有附件过时的行，也没有孤儿行。

**线上已有的问题**
- `base-drift` 6 个，`base-only-definition` 25 个，见 §8。
- `stale-intake-export` 10 个：AI 母版入库行指向的仓库文件后来重新导出过，入库附件是旧字节。入库行是历史记录，不改；当前字节以新的仓库文件行为准。
- `live-key` 13 个：`js100i_eu_en` 的文件沿用 Base 的 `web/js-100i/eu/en/...`。

**仓库这边的问题**
- `unregistered-file` 179 个。最大的几组：
  - `je1000e_sil_us_en`（FridgeGuard，55）
  - `je100c_eu_shared`（26）
  - `js100i_eu_shared`（16）
  - `je2000f_eu_en`（10）
  - `jbp3600a_eu_en`（9）
  - `js100i_eu_added`（8）
  - `shared/lcd`（8）

  另有两个单独的文件：`latex/assets/lcd_display_hero.png` 和 `common_assets/operation/led_light_complete.png`。
- `unregistered-master` 42 个：37 个是配方引用的 `source_key`，5 个只在插图清单里留了母版哈希，记为 `source/unregistered-<哈希前 12 位>`。
- `ambiguous-registry` 1 个：`je1000h_eu_en/battery_pack.png` 同时被 `charging/battery_pack` 和 `web/je1000h/eu/en/battery_pack` 列出。暂存时取字母序靠前的 key，另一个写进备注。
- `registry-copy` 4 个：`common_assets/operation/` 下 3 张，与 LaTeX 目录里的 `op_*.png` 字节相同；以及 `latex/assets/right_side_ports.png`。
- `duplicate-bytes` 38 组：21 组全在网页目录内，3 组在 Word 或 LaTeX 目录内，14 组跨目录。

## 13. 后续工作

1. 实现第 3 步的 Base→仓库同步命令。这是"只在 Base 管图"真正生效的前提。
2. 同步命令上线后，加一项 CI 检查：仓库里每个生产素材文件，都要在 Base 里有字节一致的 `approved` 行。这样直接改仓库的图会被拦下。
3. 按 §8 分批晋级建议定义，先从没有登记的文件最多的目录开始。
4. 如果需要按文件标出渲染面，先对模板和渲染器做一次引用普查。
5. 业务 Base 结构清单要整库重导一次。2026-10-12 的整库导出显示，7 月 20 日以来其他表也有结构变化，例如 KO 列、钉钉字段、`Workflow_action` 的 `Web Publish` 选项。lark-cli 1.0.49 导出的公式明细改成按字段名书写，很多表的字段顺序也变了。这些不属于本次范围，本次只更新了三张资产表。
6. 更正 [`lark-cli-bitable-ops`](../../.agents/skills/lark-cli-bitable-ops/SKILL.md) 命令参考里的版本说明。那里写上传附件要 1.0.69 或更新版本，但 CI 固定的 1.0.49 已经有 `+record-upload-attachment` 和 `+record-download-attachment`，2026-10-12 的第一批写入就是用它完成的。
