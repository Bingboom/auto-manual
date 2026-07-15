# 闭环运营手册（操作者版）

Updated: 2026-07-15

这是 Milestone G（G0–G7，PR #514–#521）交付的闭环机制的**操作者视角**说明：
日常要跑什么命令、什么时候跑、看到什么算正常。实现细节和字段含义在
[`../code-as-doc/dev/revision_ledger.md`](../code-as-doc/dev/revision_ledger.md)（维护者向），
本文只讲"人怎么用"。

一句话背景：从 Milestone G 起，**评审者对文档的每一条修改都会自动记账、
自动结清，被采纳的翻译修正可以一键收割进语料库**。系统自动做大部分事，
留给人的只有"过目并批准"这一类不该自动的决定。

---

## 1. 修订回灌账本（revision ledger）

### 1.1 哪些是全自动的（不用管）

- **记账**：每次跑 `cloud_doc_backport.py run-review-branch`，评审者的每条修改
  （机器原文 → 评审者改文，带型号/区域/文件出处）自动追加到
  `reports/revision_ledger/ledger.jsonl`。
- **结清**：下一轮跑 backport（或手动跑 `reconcile`）时，系统自动回看之前
  的账：评审者的改法最终留在文档里了吗？自动打上判决——
  `accepted_as_proposed`（采纳）/ `rejected`（被拒）/ `edited_further`（又被改了），
  并从 git 查出合并 PR、时间、作者一并记录。标点/换行级别的差异不会误判
  （相似度匹配，阈值 0.90）。

> 账本是**本机文件**，不进 git、CI 也看不到。它跟着跑 backport 的那台机器走。

### 1.2 三个人工命令

**① 看健康度（想看就看，建议每月至少一次）**

```bash
python3 -m tools.revision_ledger stats
```

看三个数字：

- `reflow_rate` **回灌率**：多少账已经结清。健康线 > 0.9；长期偏低说明
  评审分支合并后没有下一轮 backport 去结账（跑一次
  `python3 -m tools.revision_ledger reconcile --auto` 即可手动结清）。
- `acceptance_rate` **采纳率**：结清的账里，评审者的修正有多少原样留住了。
- `top_corrected_sources` **被改最多的文件**：同一个文件反复被改，是
  "模板本身该改了"的信号（这是未来"语料驱动模板优化"的输入）。

**② 收割语料候选（每轮评审收尾后跑一次）**

```bash
python3 -m tools.revision_ledger tm-candidates
```

把所有"被采纳的翻译修正"投射成候选清单，写到
`reports/revision_ledger/tm_candidates.jsonl`。每行一对句子：

- `old_text`：机器/旧的译文
- `new_text`：评审者改后的译文
- `lang`：目标语言；`provenance`：出处（哪个型号/区域/文件/PR）
- `delta_hash`：这条候选的编号，批准时用它

**③ 批准并写入语料库（人批门——只有这一步会写飞书）**

过目候选清单，把要采纳的 `delta_hash` 交给 `tm-apply`：

```bash
# 先空跑看计划（不带 --write，什么都不会动）：
python3 -m tools.revision_ledger tm-apply --approve <delta_hash>

# 确认后真写（B 库 = $FEISHU_TRANSLATION_MEMORY_BASE_TOKEN 指向的规范库）：
python3 -m tools.revision_ledger tm-apply \
  --approve-file approved.txt \
  --tm-binding "$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN:<Translation_Memory表id>" --write
```

规则（都是系统强制的，列出来是让你放心）：

- 没批准的哈希**一律不写**；重复批准是幂等的（已写过的显示 `already`）。
- 写入按"旧译文精确匹配 TM 行"定位，找不到就**弃权**（`unresolved`），
  绝不猜行乱写。弃权的候选留在清单里，走人工的
  `bilingual-tm-maintenance` 流程补录。
- 每条写入后 GET 回读校验。

**走一遍完整例子**：KR 手册评审 → 评审者把某句韩文改得更地道 → backport
收回（自动入账）→ 下轮自动结清为"采纳" → `tm-candidates` 列出这对句子 →
你过目说 OK → `tm-apply --write` 写进 TM → **下次韩文预翻译直接命中新译法**。
评审者的智慧从此不再流失。

---

## 2. TM 命中率台账

每次跑 docx 预翻译（`lark-tm-translation-preprocess` skill），运行结果里
自动多了三个数字：`units_total`（尝试翻译的句子数）、`units_matched`
（命中语料库的句子数）、`hit_rate`（命中率），并自动累计到
`reports/tm_hit_rate/ledger.jsonl`。

看趋势：

```bash
python3 -m tools.tm_hit_rate stats
```

按语言对分桶（如 `en->ko`）。**第一次真实预翻译跑完就有基线数字**；
之后每次语料入库（上面的 ③），都应该在这条曲线上看到回报。
命中率不涨 = 入库的语料没用在刀刃上，值得回头看候选的筛选标准。

---

## 3. 回收提醒哨兵（不用记得跑 backport 了）

每天 02:00 UTC，`backport-reminder.yml` 自动比对每个**评审中**云文档的
现文本和它上次回收的基线：

- 有没回收的编辑 → 仓库里自动开/更新一个
  **`[backport-reminder]`** issue，列出哪些文档、哪个分支、云文档链接。
- **你要做的**：看到 issue，对着列出的文档跑
  `python tools/cloud_doc_backport.py run-review-branch --doc-name <名> --cloud-doc <链接>`。
  回收完成后，下一次哨兵运行会自动把 issue 关掉——不用手动关。
- 从没回收过的评审文档会标 `no_baseline`（评审开始后一次 backport 都没跑），
  处理方式相同。

> 哨兵只报不动手，也不写任何飞书数据。首次启用建议在 GitHub Actions 页面
> 手动 `Run workflow` 跑一遍验证凭据（见 §5）。

---

## 4. 给审核人出带批注的 PDF

当审核方只看 PDF 时，把 QC 结果直接印在 PDF 上：

```bash
# ① 先出 QC 结果（已有流程）：
python tools/content_lint.py --data-root data/phase2 --json --write-report

# ② 渲染到构建好的 PDF 上：
python tools/pdf_annotate.py \
  --pdf docs/_build/<model>/<region>/pdf/<manual>.pdf \
  --findings reports/content_qc/<run-id>/findings.json
```

得到 `<manual>_annotated.pdf`（原 PDF 一个字节都不动）。每个高亮带批注：
什么问题、**源头在哪张表哪个字段**、建议动作。定位不到的问题会汇总在
第 1 页的批注里，不会错标。

**铁律：批注只是给人看的呈现。改错永远回到源头**（云文档/修订 docx →
backport），不要在 PDF 上改。

---

## 4.5 模板更新 × 在飞评审（跨面协作的唯一日常场景）

模板只能在 **auto-manual** 改（PR 合入 main 后由镜像自动带到 Hello-Docs
main，分钟级、零手工）；但**在飞的评审分支不会自动吃到新模板**。按改动
性质二选一：

**情况 A：不急着进本轮评审（默认，适合措辞/错别字级改动）**
什么都不用做——本轮按旧模板走完，下一次 Start Review / 构建自然用新模板。
评审中途换底会给评审者制造困惑，小改动一律走这条。

**情况 B：必须进在飞评审（模板有实质错误）**，严格按序：

1. **先收干净**：对该评审跑一次 backport，把云文档未回收的修订收进
   账本/源表（回收哨兵 issue 就是检查单）。
2. 合模板 PR → 自动镜像到 Hello-Docs main。
3. **重触发该行 Start Review**（重新勾"是否进入Review"）——语义是
   force restart：评审分支从最新模板+数据状态强制重播种。
4. 评审继续。安全性由分工保证：已进**源表**的修正重播种会带回来；
   评审者的文字修订不丢——**云文档才是评审者的真身**，重播种后
   backport 会拿新渲染重新 diff 云文档、把修订重新收集归位。
   跳过第 1 步的代价：修订仍在云文档里能重收，但账本少一轮记录。

背景：评审中发现"这句该改模板"（Class T）时，backport 不直接写模板，
而是产出 `template_sync_proposal` → 模板修改回 auto-manual 走 PR——
本节描述的就是这条回路的下半程。

## 4.6 三流转双面仪表（一条命令看全局）

```bash
python tools/flow_dashboard.py report
```

只读聚合既有台账/报告，输出 `reports/flow_dashboard/dashboard.md`（同目录还有
`dashboard.json` 和可直接双击打开的可视化 `dashboard.html`——卡片+仪表条+
月度趋势柱，零外部依赖，适合直接发给干系人看），分两张脸：

- **运营面**（给自己看健康）：回灌率、TM 命中率、二次修订率、模板复发修正率、
  模板句语料覆盖率
- **价值面**（给别人看产出）：已审计 PDF 数、覆盖面（型号/区域/语言）、机器发
  现数、回收 delta 数、TM 候选句对数、省时叙事

原则：**从零起步、无数据不造数**——数据源还不存在的指标显示"暂无数据"+原因，
这一行空格本身就是趋势的起点。常用参数：

- `--revision-ledger <path>` 可重复：合并多个 checkout 的修订台账（每个
  checkout 各攒各的账，跨仓合并去重按 delta_hash）
- `--baseline-hours-per-manual <小时>`：省时叙事的操作者基准数
  （= 以前手工做一本要多久），不给就显示"待基准数"。
  **操作者基准（2026-07-03 夏冰口径）：首版 ≥10 个工作日 ≈ 80 小时**——
  获取规格书后文案 3 天、设计排版+评审约 1 周；产品阶段 EVT→DVT→PVT
  每轮规格变更都触发同流程的修订（文案→设计→评审→发布），PVT 变更较少
  但仍有。月度例行跑法：
  `python tools/flow_dashboard.py report --baseline-hours-per-manual 80`。
  修订轮的省时暂未单独计价（可数轮数在修订台账里，等 H2 一起做每轮基准）
- 已审计 PDF 数的数据源是 `reports/pdf_annotate/ledger.jsonl`——
  `pdf_annotate` 每次运行自动记账（`--no-ledger` 关闭）；
  历史审计用 `pdf_annotate --backfill-summary <run-summary.json>` 补账

## 4.7 base 重建演练（灾备，季度一次）

**为什么**：飞书 base 是数据单一真相，公式字段/选项/关联是不受 git 版本控制的
"程序逻辑"。删一行构建表就曾连坐 52 行悬空——真灾难时能不能重建、要多久，
必须演练过才算数。

**演练步骤**（全部只用仓库内工件，不碰生产 base）：

```bash
# 1. 建演练用 scratch base（用完由操作者删除；命名带"演练-"前缀）
lark-cli base +base-create --name "演练-base重建-<日期>"
# 2. 从 schema 镜像重建表结构（幂等，dry-run 默认，--write 执行）
# 完整重建用整库镜像（21 表）；promote 流程的 2 表小 manifest 仍是 manifest.json
python tools/bitable_schema.py apply --manifest bitable_schema/business_base_manifest.json \
  --base-token <scratch> --identity user --write --yes
# 复杂字段（公式/lookup/link）apply 会列跳过清单——按 manifest 里的 detail 手工重建
# 3. 从种子/快照灌数据
python tools/bitable_schema.py seed-import --base-token <scratch> \
  --table 规格书字段映射规则 --seed bitable_schema/seed/规格书字段映射规则.csv \
  --key 规格书字段 --identity user --write --yes
# 4. 回读核对行数/字段数，记录耗时到本节
```

**演练记录**：

| 日期 | 范围 | 耗时 | 发现 |
| --- | --- | --- | --- |
| 2026-07-13 | scratch base + 2 表结构 + 25 种子行（首演） | **86 秒**，回读 25 行/10 字段 ✓ | **schema 镜像只覆盖 2/20 张表**——其余 18 张表的字段结构只存在于飞书里，真灾难时无法从仓库重建；值快照（sync-data CSV）覆盖 phase2 子集但没有字段定义。跟进：把 `bitable_schema export` 扩到全部业务表并纳入例行同步（**已闭口，见下行**） |
| 2026-07-13 | schema 镜像扩全表（缺口闭合） | 业务 base **21 表/366 字段** + TM base 2 表/58 字段整库导出入库（`bitable_schema/business_base_manifest.json` / `tm_base_manifest.json`）；44+10 个复杂字段（公式/lookup/link）带**重建细节**（lookup 源表、link 目标表等，apply 不自动建、按细节手工重建） | 例行：**每次表结构变更后（至少季度演练前）重跑整库 export 并提交 diff**；全表 parity 哨兵可作后续 |

**底线**：季度一次；每次把耗时和新发现追加到上表。演练不达标（重建不出来/
耗时不可接受）= 灾备欠账，进 checklist。

## 4.8 印刷外链清单（月度）

印在纸上的 URL/QR 印出去就改不了。`data/printed_url_inventory.csv` 是唯一
清单（模板/渲染器/配置/phase2 镜像全扫描；QR 图片目标扫不出来，手工登记进
`data/printed_url_manual_entries.csv` 会自动并入）。月度两条命令：
`check`（清单是否跟上源的变化）+ `liveness`（HEAD 探活，403/405 视为
反爬不算死链）。首扫结果：6 个目标（4 个 warranty 邮箱 + jackery.jp 官网
+ jp 邮箱），2026-07-13 探活全通。

## 4.9 插图资产登记（资产环 P0，维护者代登记）

业务控制面使用 `文档构建` Base 中三张独立表：`04_资产源文件`（一个母版
修订一行）、`04_资产定义`（一个稳定 `asset_key` 一行）和 `04_资产导出物`
（一个物理文件一行）。旧插图表只保留历史数据，新链路不读取或写入它。
仓库侧 `data/asset_sources.csv` 与 `data/asset_registry.csv` 是可审查、可冻结的
构建快照。操作者已定的四条规则：

1. **.ai 源文件放 `04_资产源文件.source_file` 附件列**，git 只存获批的
   构建导出物 + 登记哈希（大文件不进仓库）
2. **现存带字插图排期无字化**（`待无字化` 勾选；范本=LCD hero 纯数字标注
   一图通三语）；新图一律无字底图 + 文字走数据层
3. **临时替代图显式记债**：状态 `🔧临时替代` 的资产构建可用；publish 门
   （P1）上线后拦截，登记为例外的除外
4. **维护者代登记**：设计师交付文件（.ai + 导出物），维护者挂表并更新哈希

导出命名契约：`<asset_key>[-<lang>].{pdf,png}`（成品页 PDF 的 -en/-es/-fr
已是先例）。当前仓库镜像统计：**71 项 = 64 成品 / 3 临时替代 /
4 缺失**；缺失清单即向设计侧的要图清单。后续：P1 资产解析器+publish 门，
P2 .ai 入附件列+导出自动化，P3 release manifest 加 assets 段。

### 4.9.1 构建链路与母版 intake 入口（已接入）

仓库把注册表变成可调用的构建入口：

```bash
python build.py asset-check --json
python build.py asset-check --asset-key operation/ac_output --asset-format png --json
python build.py asset-check --asset-key hero/lcd_display --asset-format png --allow-temporary
python build.py asset-check --publish --asset-key operation/ac_output --asset-format png
python build.py asset-intake \
  --asset-source-key source/manual_je1000f_us_master \
  --asset-source-file '<local-master.ai>' \
  --asset-recipe data/asset_recipes/manual_je1000f_us_master.json \
  --asset-output-root .tmp/asset-intake/manual_je1000f_us_master/run-01
```

含义分别是：盘点注册表、解析一个成品导出、仅在草稿中显式解析临时替代、
以及执行发布态的成品门。`asset-check` 会校验导出文件存在且哈希前缀一致；
不会把桌面 `.ai` 路径写进构建结果。PR #662 的无字矢量试点仍兼容其过渡目录，
解析结果会落到 `docs/renderers/latex/assets/`。

`asset-intake` 是独立的 package-only 入口。它先把源复制到权限受限的临时目录并
核对完整 SHA，再只从这个快照拆分；完成后再次核对外部源，输出 59 个清理后的
单页 PDF、页面预览、recipe 导出物、`manifest.json`、`artifacts.csv` 和固定顺序/
时间戳的 ZIP。源、工作树、注册表和 Base 都不会被命令改写。输出目录必须不存在；
运行时版本、完整哈希、路径、像素预算或 raw/decoded PDF 私有标记任一不合约即整批
失败且不发布半成品目录。

Recipe 的文字契约按可本地化风险区分：`textless` 必须零可见字符，
`numeric-only` 只允许数字，`fixed-product-markings` 只允许设备实物上不会随手册语言
变化的丝印/按钮标记，`localized-full-page` 必须按语言与区域隔离。设备上的 POWER、
AC、DC/USB 等固定丝印不能被误记成“零文字”，也不能借该策略放入可本地化说明正文。

后续生图工具只读取 [`data/asset_generation_candidates.csv`](../data/asset_generation_candidates.csv)：
`generator_allowed=TRUE` 才能生成候选图；产品结构、LCD、按钮、端口、二维码、
警示图和带精确文字的操作图必须走设计重绘或源文件导出。生成结果先登记为候选，
经过人工确认、导出和哈希登记后，才可转为 `✅成品`。

源文件元数据见 [`data/asset_sources.csv`](../data/asset_sources.csv)：它记录完整
`.ai` SHA-256、页数、版面尺寸、适用范围和已验证的 Feishu 附件指针；归档未完成
时指针保持为空，不记录本地桌面路径，也不回退到旧表。

### 4.9.2 `.ai` 交付与登记一页流程

设计师只需交付 `.ai` 和约定导出物；维护者负责登记。业务面单一真相是
`文档构建` Base（`LD3lb4G1ua4GOVs1vxAc9W2enje`）中的三张 `04_资产*` 表。
下列 `<source_table_id>` 必须来自新建表的真实返回；禁止替换成旧插图表 ID。
大文件不进入 Git。

1. 在文件所在目录计算完整 SHA-256，核对文件名与字节数，并把页数/画板数、成品尺寸、
   Illustrator 版本、修订信息和完整哈希记入 `data/asset_sources.csv`。对 PDF-compatible AI，
   可用 `pdfinfo <file.ai>` 读取页数和生成器；修订表与印刷标题栏不一致时分别记录，
   不擅自合并成一个版本号。
2. 对 PDF-compatible AI 先运行 `asset-intake`。使用 recipe 声明的 source key，
   `--asset-output-root` 指向一个不存在的新目录；至少重跑两次并比较整树，确认
   manifest/CSV/ZIP/全部 PDF/PNG 逐字节相同、所有获批导出命中完整预期哈希、输出 PDF
   不含 `AIPrivateData` / `PieceInfo` / `AIMetaData`，且源文件前后 SHA 不变。隔离页和
   `visual_review_required=true` 的资产不得借此自动放行。
3. 先在 `04_资产源文件` 按 `source_key` 查记录及 `source_file`，下载已有附件
   并比较哈希。哈希相同就停止，
   不重复上传：

   ```bash
   lark-cli base +record-search --as user \
     --base-token LD3lb4G1ua4GOVs1vxAc9W2enje \
     --table-id <source_table_id> \
     --keyword 'source/<master-key>' --search-field source_key \
     --field-id source_key --field-id source_file --field-id source_sha256 --format json

   lark-cli base +record-download-attachment --as user \
     --base-token LD3lb4G1ua4GOVs1vxAc9W2enje \
     --table-id <source_table_id> --record-id <record_id> \
     --file-token <file_token> --output ./downloaded-master.ai
   shasum -a 256 ./downloaded-master.ai
   ```

4. 仅当附件为空或哈希不同且本次确为新修订时上传。`source_file` 放原始 AI，
   `asset_package` 放确定性 ZIP，`manifest_file` 放匹配的 manifest；`--file` 必须是
   当前目录下的相对路径。附件命令会向单元格追加文件，不能用它制造同版本副本：

   ```bash
   lark-cli base +record-upload-attachment --as user \
     --base-token LD3lb4G1ua4GOVs1vxAc9W2enje \
     --table-id <source_table_id> --record-id <record_id> \
     --field-id source_file --file ./master.ai
   ```

5. 分别回下载 AI、ZIP 和 manifest 的新 `file_token`，再次比较完整 SHA-256；三者
   一致后才更新飞书 `source_sha256` / `package_sha256` / `manifest_sha256`、Git 中的
   `data/asset_sources.csv` 精确记录指针，以及 `04_资产定义` / `04_资产导出物` 的
   recipe 资产、物理文件、scope、gate、repo path 和完整内容哈希。旧修订是否移除由
   维护者在确认新修订可打开、可导出后单独决定。

当前仍不引入 ExtendScript。PDF-compatible AI 走上述确定性 PDF 拆分；非 PDF-compatible
文件、Illustrator 原生图层/画板语义和需要设计重绘的资产仍由设计工具处理。累计至少
两个主文件并固化原生画板命名后，再按 `indesign_finalize.jsx` 的模式评估独立、可重跑
的 Illustrator 批量导出脚本。

## 5. 首跑清单（一次性，做完划掉）

- [ ] **命中率基线**：跑一次真实的 docx 预翻译，`tm_hit_rate stats` 出现
      第一个基线数字
- [ ] **哨兵首跑**：GitHub Actions → Backport Reminder → Run workflow，
      确认凭据链路通（未配置时它会在 Summary 里列出缺哪个 secret）
- [ ] **A 库迁移**：把旧 A/wiki 归档库（`X3O8…`）里 B 库没有的句对迁到
      B 库（可用 `bilingual-tm-maintenance` 流程）。迁移完成前，
      **不要放量跑 ③ 语料写入**——新语料写进分裂的库会变烂账

## 6. 运营节奏（建议）

| 频率 | 做什么 |
| --- | --- |
| 每轮评审收尾 | `tm-candidates` → 过目 → `tm-apply`（§1.2 ②③） |
| 有 `[backport-reminder]` issue 时 | 对着清单跑回收（§3） |
| 每月 | `python tools/flow_dashboard.py report`（§4.6，一条命令出两面）；`python tools/printed_url_inventory.py check && python tools/printed_url_inventory.py liveness`（§4.8 印刷外链）；`top_corrected_sources` 里反复出现的文件记下来（模板优化候选） |

跑了 2–3 轮、流程顺手之后，这套程序会固化成 skill（届时本文档仍是底层参考）。
