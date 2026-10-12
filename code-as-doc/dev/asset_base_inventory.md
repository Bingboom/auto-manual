# 生产素材入飞书多维表：表结构与 dry-run

Status: proposed

Updated: 2026-10-12

方案待操作者确认。dry-run 已实现（[`tools/asset_pipeline/base_inventory.py`](../../tools/asset_pipeline/base_inventory.py)），只读工作区，不调用飞书。Base 结构变更和线上写入，都要等操作者确认后才做。

## 1. 目标

仓库里有四个目录的生产素材，共 1273 个文件。目标是让它们在 `文档构建` Base 里都能查看、审阅和下载：每个文件一行，附件就是这份文件本身。

- 不新建表，沿用 [AI 母版入库](asset_ai_master_intake_plan.md)建好的三张 `04_资产*` 表。旧插图表 `tblxFBWaDG4OYhqu` 照旧不读不写。
- 构建仍然只读仓库里的字节。Base 用来登记、审阅和下载；附件和仓库文件按 SHA-256 对账。
- 第一步是只读 dry-run：从工作区生成待入库的行和问题清单，交操作者核对。

## 2. 以谁为准

| 内容 | 以谁为准 | 说明 |
|---|---|---|
| 文件字节和路径 | Git | 构建只读仓库；Base 附件是同一份字节的副本 |
| 这张图是什么、能不能构建：类别、语言维度、状态、待无字化、适用机型/区域、语言变体 | `04_资产定义` | 现有规则不变：`sync-data` 把这几列镜像进 `data/asset_registry.csv`（[`tools/sync_asset_registry.py`](../../tools/sync_asset_registry.py)），只覆盖、不删行 |
| 导出物路径、内容哈希、仓库备注 | 仓库 | 注册表里属于仓库的列，`sync-data` 不改 |
| 附件和仓库是否一致 | 对账 | 每次上传后下载附件、比对 SHA-256，结果写进 `对账结果` |
| 新图 | 先进 Base，再进仓库 | 在 Base 上传、审批通过后，经 PR 同步进仓库。做法同现在的 `web-composite`：只取已审批、恰好有一个附件的行，下载后校验哈希再落盘 |

## 3. 三张表各放什么

**`04_资产源文件`**：一个设计母版（`.ai`/PDF）一行。dry-run 给出 57 行：
- `data/asset_sources.csv` 已登记的 15 个母版；
- 配方或插图清单引用了、却没有登记的 42 个，标 `needs_review`。

母版文件不在 Git 里，这里只登记元数据。附件归档仍按 AI 母版入库流程逐个做。

**`04_资产定义`**：一个稳定的 `asset_key` 一行，共 1186 行：
- 注册表已有的 479 行，拼写与注册表完全一致（见 §8）；
- 其余 707 行是建议定义：插图清单绑定的 475 个，只能按目录推出 key 的 168 个，符号清单 61 个，按键清单 3 个。类别、语言维度和适用范围都是建议值，状态留空，由操作者定。

**`04_资产导出物`**：一个实际文件一行，`export_file` 附件里只放这一份文件。
- 共 1273 行，`export_key` 统一写成 `git:<仓库路径>`。
- 不会跟现有的导出物行撞键：首次归档的 142 行（`archive-page`、`preview`、`semantic-export`）和 `web-composite` 行。

暂存 CSV 的列按以下顺序排：
1. 表里已有的字段；
2. 建议新增的字段；
3. 只供审阅、不上传的列，如 `registered_in`、`key_origin`、`needs_review`。

## 4. 需要确认的结构变更

`04_资产导出物`：
- `artifact_kind` 加四个选项：`web-shared`、`web-target`、`print`、`word`，分别对应四个目录。现有的 `archive-page`、`preview`、`semantic-export`、`web-composite` 不动。
- `gate_status` 加 `pending`（线上还没有的话）。现有的 `approved`、`archive`、`quarantine` 不动。
- 新增三个字段：
  - `像素尺寸`：文本，如 `2131x491`；SVG 填 viewBox 尺寸，PDF 不填；
  - `透明通道`：复选框；
  - `对账结果`：文本，记录上传后附件哈希与仓库是否一致。
- 语言写进现有的自由文本字段 `locale`。`web_locale` 是 web-composite 门禁读的单选（en/fr/es/shared），不加选项。

`04_资产定义`：新增 `中文说明`（文本，写含义和用法）。由操作者逐步补，dry-run 不填。

`04_资产源文件`：不改。

确认后先在线上改结构，再用一个单独的 PR 把新字段 ID 冻结进 [`data/asset_base_bindings.json`](../../data/asset_base_bindings.json)。

与最初方案相比有两处改动：
- **不加 `withdrawn` 门禁选项。** 符号清单撤回的 11 张旧位图都在 Word 目录里，只是网页不再用；改用撤回门禁，会把 Word 和印刷也一起挡住。它们按各自的注册表行定门禁（目前都是 `approved`），备注里写明「网页符号清单已撤回这份位图」。
- **不加 `渲染面`。** 目录归属已经由 `artifact_kind` 表达。要逐个文件说清哪个渲染器真的在用，得先做一次引用普查。

## 5. 四个目录怎么进表

数据来自 main `e863459`（2026-10-12）。

| 目录 | `artifact_kind` | 文件数 | 已由谁登记 | 门禁 |
|---|---|---|---|---|
| `docs/renderers/web/assets/shared/` | `web-shared` | 76 | 符号清单 61，按键清单 7；`lcd/` 下 8 个没有登记 | approved 4，pending 72 |
| `docs/renderers/web/assets/<机型_区域_语言>/` | `web-target` | 941 | 注册表 296，机型插图清单 476，没有登记 169 | approved 296，pending 645 |
| `docs/renderers/latex/assets/` | `print` | 196 | 注册表 195（含 1 个字节副本），没有登记 1 | approved 185，quarantine 6，pending 5 |
| `docs/templates/word_template/common_assets/` | `word` | 60 | 注册表 59（含 3 个字节副本），没有登记 1 | approved 59，pending 1 |

- 合计 1273 个文件，234 MB；最大的一个 4.0 MB，可以逐个作为附件上传。
- 格式：PNG 1016、SVG 129、PDF 101、WebP 24、JPG 3。

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

## 7. 门禁（gate）

只有注册表行的状态能放行：

| 注册表状态 | `gate_status` |
|---|---|
| ✅成品 | `approved` |
| ⛔隔离 | `quarantine` |
| 🔧临时替代、❌缺失 | `pending` |
| 不在注册表里 | `pending`，等操作者在定义表定了状态再放行 |

`build_eligible` 只在 `approved` 时为 TRUE。`visual_review_required` 在非 `approved` 时为 TRUE，与 intake 的做法一致。

几个具体情况：
- 共享符号清单的 61 个条目，清单里自己写着「registry promotion pending」或「publication pending」，所以都是 `pending`；清单状态写进备注。
- 按键清单有 7 个 SVG：
  - `button/power`、`button/ac`、`button/dc_usb`、`button/led` 是注册表里的 ✅成品行，所以是 `approved`；
  - JHP-3600C 的 3 个底部按键不在注册表里，是 `pending`。
- 撤回的 11 张旧位图见 §4。

## 8. 与 sync-data 的关系：定义为什么要分批进表

`sync-data` 读取线上的 `04_资产定义` 后会做三件事：
1. 把 Base 管的几列覆盖到注册表里同一 key 的行；
2. 注册表里没有的 key，追加成新行；
3. 用注册表的加载器重新解析整张表，解析失败则整个同步失败。

由此有四条约束：

- **注册表已有的 479 个定义，要按注册表原样上传。**
  - dry-run 用同一个合并函数模拟了一次，结果与现在的 `data/asset_registry.csv` 逐字节相同（见 `summary.json` 的 `registry_sync_preview.registered_definitions`）。
  - 这一批上传后，下次 `sync-data` 不会改动注册表。
- **上传之后，这 479 行由 Base 说了算，维护方式要跟着变。**
  - 类别、状态、适用范围等列以后要在 Base 里改；直接改 CSV 的话，下次 `sync-data` 会被覆盖回去。
  - 注册表里有 224 行的备注写着「未写线上 Base」，说明目前很多行是直接在 CSV 里维护的。
  - 这一条需要操作者明确同意。
- **707 个建议定义现在不能上传。**
  - 下次 `sync-data` 会把它们全部追加进注册表；而它们的状态都是空的，加载器会拒绝（`unknown status ''`），`sync-data` 会直接失败。
  - 它们要走注册表晋级：
    1. 操作者按目录或机型分批确认 key、类别和状态；
    2. 一个仓库 PR 把这些行连同导出物路径和哈希加进注册表；
    3. 合并后再上传对应的 Base 定义，这样又是一次无变化的往返。
- **不能出现重复的 `asset_key`。**
  - [`tools/sync_web_composites.py`](../../tools/sync_web_composites.py) 遇到重复的 key 会直接报错。
  - 所以上传前先读线上表：已有的 key 跳过；值不一致的列出来交操作者，不覆盖。

导出物行不受影响：`sync-data` 只读 `artifact_kind=web-composite` 的导出物行，新加的四种类型不会进入构建。

## 9. 入库流程

**第 0 步：dry-run（本 PR）。** 生成暂存 CSV 和问题清单，交操作者核对，重点看 §12。

**第 1 步：结构变更。** 操作者确认 §4 和 §8 后，在线上改结构，并把新字段 ID 冻结进 `data/asset_base_bindings.json`。

**第 2 步：第一批写入。** 只在操作者明确说「入库」后才做。
- 先只读拉取三张表，按 `source_key`、`asset_key`、`export_key` 算出需要新增的行。
- 只追加以下三类行：
  - 还没进表的母版元数据；
  - 注册表已有、Base 还没有的定义；
  - 全部 1273 个导出物行，附件取自 `repo_path`。能关联到定义的就关联；定义还在建议阶段的，先只填 `asset_key` 文本，晋级后再关联。
- 每写一行都回读，核对 `record_id`、`export_key`、`content_sha256`，并确认附件的 `file_token` 不为空。
- 写完后把附件全部下载下来比对 SHA-256，结果写进 `对账结果`。
- 不删行，不改现有的导出物行和已有的定义。

**第 3 步：后续批次。** 按 §8 分批晋级 707 个建议定义。

**第 4 步：日常维护。**
- 仓库里的素材变了：重跑 dry-run，按 `export_key` 和 `content_sha256` 与线上表比对。
  - 新文件：追加一行。
  - 字节变了：更新同一行的附件和哈希，备注里留下旧哈希。
  - 文件从仓库删掉了：只在备注里标记，不删行。
- 新图从 Base 进来：审批通过后经 PR 同步进仓库，做法同 `web-composite`。这需要一个新的同步命令，属于后续工作。

写入要用 lark-cli 和飞书凭证，步骤按 [`lark-cli-bitable-ops`](../../.agents/skills/lark-cli-bitable-ops/SKILL.md) 来。当前的云端容器里两者都没有。

## 10. 不放进表的内容

- **已发布说明书的冻结包**：`manual_sources/` 下 9319 个图片/PDF，`data/manual_sources/` 下 2245 个。它们是封存的字节副本，哈希已记在发布清单里。
- **验收截图和证据、构建产物、测试夹具**：`code-as-doc/`、`reports/`、`docs/_build/`、`data/asset_evidence/`、`tests/fixtures/`。web-composite 的冻结附件也在夹具里，它们本来就是 Base 里的行。
- **`.ai` 母版**：不在 Git 里，按 AI 母版入库流程归档到 `04_资产源文件.source_file`。
- **RTD 门户的产品图**：`tools/rtd_portal_assets/_static/`，门户用图，不是说明书素材。

待定：`docs/renderers/contracts/assets/` 下还有 32 张图，注册表没有登记。其中少数被 Web 呈现契约和 FridgeGuard 的 App 页直接引用，比如 `app_store_badges.png`、`app_add_device_steps.png`。要不要把它作为第五个目录纳入，由操作者决定；纳入的话，`artifact_kind` 需要再加一个选项。

## 11. dry-run 用法

```bash
python -m tools.asset_pipeline.base_inventory --output-dir <新的或空的目录>
```

- 只读以下输入，不调用飞书：
  - `git ls-files` 列出的四个目录；
  - 注册表、共享清单和机型插图清单；
  - 配方和 `data/asset_sources.csv`。
- 输出目录必须是新的或空的，并且不能位于 `docs/`、`data/`、`tools/` 下面。
- 输入读不了时，退出码为 2。
- 处理 1273 个文件约 2 秒。

输出文件：

| 文件 | 内容 |
|---|---|
| `asset_sources.csv` | `04_资产源文件` 的待入库行 |
| `asset_definitions.csv` | `04_资产定义` 的待入库行：注册表原样的行，加上建议定义 |
| `asset_exports.csv` | `04_资产导出物` 的待入库行，含仓库路径、字节数、SHA-256、像素尺寸和透明通道 |
| `findings.csv` | 问题清单：类型、对象、说明 |
| `summary.json` | 行数、各类计数和 `registry_sync_preview` |

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

## 12. 当前盘点结果

数据来自 main `e863459`。

**总量**
- 57 个母版、1186 个定义、1273 个导出物。
- 门禁：approved 544、pending 723、quarantine 6。
- 需要复核：母版 42、定义 707、导出物 728。

**`unregistered-file`，共 179 个**
- 最大的几组：
  - `je1000e_sil_us_en`（FridgeGuard，55）
  - `je100c_eu_shared`（26）
  - `js100i_eu_shared`（16）
  - `je2000f_eu_en`（10）
  - `jbp3600a_eu_en`（9）
  - `js100i_eu_added`（8）
  - `shared/lcd`（8）
- 另有两个单独的文件：`latex/assets/lcd_display_hero.png` 和 `common_assets/operation/led_light_complete.png`。

**`unregistered-master`，共 42 个**
- 37 个是配方引用的 `source_key`。
- 5 个只在插图清单里留了母版哈希，记为 `source/unregistered-<哈希前 12 位>`。

**`ambiguous-registry`，共 1 个**
- `je1000h_eu_en/battery_pack.png` 同时被 `charging/battery_pack` 和 `web/je1000h/eu/en/battery_pack` 列出。
- 暂存时取字母序靠前的 key，另一个写进备注。

**`registry-copy`，共 4 个**
- `common_assets/operation/` 下 3 张，与 LaTeX 目录里的 `op_*.png` 字节相同。
- `latex/assets/right_side_ports.png`。

**`duplicate-bytes`，共 38 组**
- 21 组全在网页目录内，3 组在 Word 或 LaTeX 目录内，14 组跨目录。

**在这四个目录里没有文件的定义，共 26 个**
- web-composite 21 个，文件已经在 Base 里；
- 飞书附件列 2 个；
- ❌缺失 2 个；
- 上面那个重复登记的 key。

## 13. 后续工作

- 按 §8 分批晋级建议定义，先从没有登记的文件最多的目录开始。
- 参照 `sync_web_composites`，新增一个 Base→仓库同步命令，处理 `web-shared`、`web-target`、`print`、`word` 的新图。
- 如果需要按文件标出渲染面，先对模板和渲染器做一次引用普查。
