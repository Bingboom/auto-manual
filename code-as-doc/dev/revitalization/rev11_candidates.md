# REV-11 调查半：翻译候选池核实与首批审核建议清单

- 调查时点（UTC）：2026-09-19T03:10:04Z 开始，全部数据抓取完成于 2026-09-19T03:17:12Z（同一时点口径，各抓取的逐条时间戳见 §6）
- 性质：**只读调查**。未写任何飞书表、未改仓库文件；所有产出在本目录。
- 裁决权声明：**本文所有"建议"仅是执行层建议，批准/拒绝/待定的裁决权在语言责任人（操作者）。**

## 1. 候选池的真实位置与现状

候选池不是一个地方，是**三层**（机制层 1 个 + 事实层 2 个）：

### 1.1 机制层：#538 设计的正式候选文件 —— 当前为 0 条

- PR #538（H3 双面仪表，main 提交 `e395e513`）的 `tools/flow_dashboard.py` 读
  `reports/revision_ledger/tm_candidates*.jsonl` 作为 "TM 候选句对数"。
- 候选文件由 `tools/revision_ledger.py tm-candidates` 生成，只收
  `final_status=accepted_as_proposed` 且 `route_class=repo_review_text` 的行；
  下游 `tm-apply --write --tm-binding` 走审批门写活表（回灌通道**已存在**，main 上齐全）。
- **正查（两个正交手段核实"不存在"）**：
  1. `find` 遍历全部 worktree 父目录（auto-manual 主 checkout、44 个 worktree、Hello-Docs）→ 无任何 `tm_candidates*.jsonl`；
  2. Spotlight `mdfind -name "tm_candidates"` 全盘 → 0 命中（2026-09-19T03:11Z）。
- **现算**：对两份现存 revision ledger 各跑一次 `tm-candidates`（输出指到本目录）→ **均为 0 条**
  （`tm_candidates_auto-manual.jsonl` / `tm_candidates_hello-docs.jsonl`，命令输出 `"candidates": 0`）。
  原因：两份台账 **100% pending、0 行 accepted**（见 1.2），候选生成的前置条件（裁决）从未发生。

### 1.2 事实层 A：revision ledger 待裁决行 —— 197 条（全 ko）

| 台账 | 行数 | 状态 | 时间范围 | mtime |
| --- | --- | --- | --- | --- |
| `/Users/hello-tech-team/Documents/GitHub/auto-manual/reports/revision_ledger/ledger.jsonl` | 129 | 全 pending | 2026-08-19 ~ 08-26 | 08-26 |
| `/Users/hello-tech-team/Documents/GitHub/Hello-Docs/reports/revision_ledger/ledger.jsonl` | 93 | 全 pending | 2026-09-05 | 09-04(文件系统) |

- 按 `delta_hash` 合并去重（flow_dashboard 同款口径）：**197 条唯一 delta**（重叠 25）。
- 全部 `lang=ko`，来自三个回写轮：`backport-review-JE-2000E-KR-20260819`（85）、`backport-review-JE-3000C-KR-20260826`（44）、`backport-review-JE-2000E-KR-20260905`（68）。
- 路由分布：`source_table_suggestion` 101 / `repo_review_text` 89 / `image_asset_delta` 4 / `needs_human_mapping` 3。
  其中 **repo_review_text 的 89 条**（含 machine+reviewer 双文本的 70 条）一旦裁决 accepted 即自动成为 TM 候选。

### 1.3 事实层 B：活表 Draft 待办 —— 431 Draft + 74 无状态（TM-B base，只读核实）

TM-B base `Ji1hb5ub1aUbewsTljGccvx5nhc`（表列表读取 2026-09-19T03:12:39Z）只有两张表，**没有独立的"待审核/candidate"表**；候选语义由 `Status` select 字段承载（选项 Draft/Approved/Deprecated，两表同构）：

| 表 | 总行数 | Approved | Draft | Deprecated | 无 Status |
| --- | --- | --- | --- | --- | --- |
| Translation_Memory `tblqtvNbgjDwR4ya` | 1358 | 949 | **314** | 21 | **74** |
| Terms `tblzerRpOEuDIkKA` | 232 | 115 | **117** | 0 | 0 |

- TM 的 314 条 Draft **全部**是 zh→zh-TW 完整句对（314/314 核实，无一缺格）；Terms 的 117 条 Draft 同为 zh→zh-TW 词条。即当前 Draft 池 ≈ 一整轮台规繁体预翻译入库待裁决。
- 74 条无 Status 行**全部**是 en→zh-TW 句对（74/74 核实）。数字对账：2026-08-19 状态回填时 TM 共 1284 行，现 1358 行，差值恰为 74 —— 即回填之后新增、**从未进入任何裁决状态**的行。
- 停滞证据：08-19 回填时 Approved 1085 / Draft 431（memory 在册）；今天 Approved 1064 (=949+115) + Deprecated 21、**Draft 仍是 431 (=314+117)**。一个月来的全部裁决动作 = 21 行 Approved→Deprecated，**Draft 零消化**。

### 1.4 当前真实候选数（一句话）

**正式候选（#538 机制口径）= 0；待裁决面 = 702 行** = ledger pending 197 + 活表 Draft 431 + TM 无状态 74。明细见 `rev11_pool.csv`（702 行，与此处口径逐行对应）。

## 2. 抽样评估（10 条，执行层建议）

| # | 池 | ID | 内容摘要 | 建议 | 一句理由 |
| --- | --- | --- | --- | --- | --- |
| 1 | TM Draft | recvqDrWUQmLTF | 300D 前言（zh→zh-TW） | 批准 | 转换正确且做了台湾用语本地化（用户指南→使用者指南），前言样板复用价值高 |
| 2 | TM Draft | recvqDsREXMqSv | 电池漏液安全句 | 批准 | 译文流畅、本地化到位（以清水沖洗、儘速諮詢醫師），安全样板高复用 |
| 3 | TM Draft | recvqDsREXqTNg | 130°C 爆炸警告 | 待定 | zh-TW 把「过高温度环境」弱化为「高溫環境」，安全文案的语义精度须语言责任人拍板 |
| 4 | TM Draft | recvqDsREXkAOE | 充电温度：32°F~113°F… | 拒绝 | 纯参数句（值随型号变化）复用价值低，且 zh-TW 端「～」两侧加空格与源格式分叉 |
| 5 | TM Draft | recvqDuMybDJFB + recvqDuMybVVag | 最大140W 参数句 ×2 | 拒绝其一 | 同 zh 同 zh-TW 的完全重复行（本轮唯一池内重复）；两行 Model 均空，去重前按惯例先核 Model 维度 |
| 6 | TM 无状态 | recvul0W7f8fEC | UPS 前言（en→zh-TW） | 批准（先补 Status） | 译文正确、与既有前言家族措辞一致；但行上无 Status/Source，须先补字段入池再裁决 |
| 7 | TM 无状态 | recvuqhHuVIgbY | 儿童安全句（en→zh-TW） | 批准（先补 Status） | 与既有 zh Draft（recvqDsREXF4TE）同族同措辞，无冲突 |
| 8 | Terms Draft | recvqDsXTFcNat | 请妥善保存本说明→請妥善保存本說明書 | 待定 | 整句进了术语表（scope 错位），且目标端多「書」字致键不对称；建议移句对表或统一键名 |
| 9 | Ledger pending | 8b0c737b5b71（JE-2000E KR 00_preface） | 을(를)→을 助词修正 | 批准 | 明确的机械性改进，与在册 KO-JOSA-DOUBLE 系统债一致（姊妹行 8ca59… 은(는)→는 同理） |
| 10 | Ledger pending | 4cf0cabb2e42（JE-2000E KR 05_operation） | 「AC 출력」→「AC1/2 출력」 | 批准（限 JE-2000E KR scope） | 型号事实修正（2000E 是 AC1/2 双口机），不可泛化到单 AC 口型号 |

另记一条反例供裁决界面参考：ledger `cdbdac11d039`（「우측 측면 뷰」→「왼쪽 측면도」）是**语义反转**（右视图→左视图），必须对着产品图核实后才可裁决——此类行建议默认"待定"。

## 3. 存量数字 118 / 151 的溯源

| 数字 | 含义 | 产出工具 | 报告/引用位置 | 当前值（本轮重跑） |
| --- | --- | --- | --- | --- |
| 118 | 全库实质分叉（英文键×语言） | `tools/lang_asset_sweep.py`（PR #924，main 提交 `c7f5e2f4`；#958 追加 --terminology） | 仓库内引用：`code-as-doc/architecture/product_skeleton_library_requirements.md:91`（origin/main）；数字演变 118(08-13)→116→114(08-18) 记录在用户 memory `language-assets-governance.md` | **110**（2026-09-19T03:17Z 重跑，报告在本目录 `fork_report_20260919.md`） |
| 151 | TM 空影重复行（同 en 一行有值一行空） | 同上（sweep 的 shadow 口径） | **仓库内无任何文档记录该数字**（两个正交核实：① `git grep` origin/main 全库 "151"+空影/shadow 语境 0 命中；② "空影" 一词仅出现在工具源码本身）。原始 2026-08 报告按 memory 在操作者桌面（scratch 版脚本+报告），但今天 `find ~/Desktop`（-iname 裁决/sweep/空影/分叉）与 `grep -rn 空影 ~/Desktop` 均 0 命中 → **原始报告位置待操作者提供**；数字演变 151(08-13)→150(08-18) 仅在 memory 在册 | **144**（同一次重跑，按语言 de:21/it:22/es:18/fr:18/zh:15/jp:15/uk:14/ko:10/pt-BR:10/zh-TW:1） |
| （附）39 | H3 首跑"落地无裁决"的候选 | `tools/flow_dashboard.py`（PR #538） | 仓库内记录：`code-as-doc/code_optimization_log.md:802`（origin/main）——"JE-2000F CN 轮的 39 条 delta 全部落进源表但从未在台账盖 accepted" | 该 39 条**已不在现存台账里**（两份 ledger 最早行均为 2026-08-19 之后；7 月台账状态本地不可复原，见 §5 caveat）。当下同类数字 = 197 条 pending |

本轮 sweep 重跑其余读数（同报告）：轻微差异 26、TM 同英文重复 32 组（矛盾 16）、Terms∩TM 重叠键 75、活表垃圾值 12、库内废弃术语 12（且 12 处均标着 Approved——门只扫构建产物扫不到库存，这批要单独裁决）。

## 4. 给语言责任人的裁决界面建议（下一步）

1. **Draft 即待办**（08-19 裁决已确立，取代空影发现法）：建议按三个批次裁决而非逐条 ——
   a) TM 314 条 zh→zh-TW（多数为机械繁化+台湾用语，可先立一条「句级 desc 类以印刷源表为准」式的批量规则，参照 08-18 memory 中已被提出的同类规则）；
   b) Terms 117 条（先清 scope 错位：整句词条移句对表）；
   c) 74 条无状态行先统一补 `Status=Draft`（+Asset_ID/Source 按 08-19 回填口径）再入池——这是一步**需审批的写操作**，本轮未做。
2. **Ledger 197 条的裁决动作是跑 `revision_ledger.py reconcile`（或 ingest 自带的 auto-reconcile），不是新工具**；三轮 KR 回写的 PR 早已合并，只是没人回来盖章。盖章后 `tm-candidates` → 人工 approve（delta_hash 清单）→ `tm-apply --write` 走既有审批门，链路在 main 上是通的。
3. 抽样显示三类高频裁决模式可做成快捷键：**纯参数句→拒绝**、**重复行→并一留一（先核 Model 维度）**、**josa/机械修正→批准**。
4. 分叉 110 处的逐条裁决清单已随本轮生成（`adjudication_20260919.md`），与候选池分开走，不要混在一个界面里。

## 5. 未能核实 / 口径限制（caveats）

- 2026-07 的 39 条候选所在的台账物理状态无法复原：现存两份 ledger 起始行均为 2026-08-19 后，7 月版 `ledger.jsonl` 去向未能确认（可能被重建；全盘 mdfind 无第三份 ledger）。不影响"当前候选数"的口径。
- 151 的原始报告文件未找到（桌面两种搜法均空），只能给出 memory 在册的数字与今天的重跑值 144；原始文件位置待操作者提供。
- TM 表 74 行无 Status 与 21 行 Deprecated 的变更人/时间未查（record 修订历史需另拉），只做了总量对账推断（1358−1284=74）。
- 本轮 sweep 用 origin/main 的工具与模板树（`git archive` 导出到本目录 `main-tree/`）+ 活表实时数据；主 checkout 停在 `feat/sweep-terminology-crosscheck`，其模板与 main 有 234 个 rst 差异，故**没有**用工作树跑。
- lark-cli 本机版本 1.0.69（skill 记 1.0.78 口径），`--profile prod` 不存在，实际用 `cli_aaa0db0d4b39dcca`；读操作不受影响。
- Hello-Docs ledger 属镜像仓库工作区，本轮只读取未改动。

## 6. 数据抓取台账（UTC + 来源命令）

| 时间 (UTC) | 动作 | 命令要点 |
| --- | --- | --- |
| 03:10:04Z | 建目录/开始 | `date -u` |
| 03:10:16Z | 仓库侧定位 | `git grep -l 回灌\|候选\|candidate origin/main -- tools/`；`git log origin/main --grep=H3` |
| 03:11:44Z | 两份 ledger 现算候选 | `.venv/bin/python tools/revision_ledger.py tm-candidates --ledger <各自> --out <本目录>` → 均 0 |
| 03:11–03:12Z | ledger 统计 | `tools/revision_ledger.py stats --ledger <各自>`（129/93 全 pending） |
| ~03:11Z | "候选文件不存在"双核实 | `find <全部 worktree 根>/reports/revision_ledger` + `mdfind -name tm_candidates` |
| 03:12:39Z | TM-B 表清单 | `lark-cli --profile cli_aaa0db0d4b39dcca base +table-list --as bot --base-token Ji1hb5…` |
| 03:12:57Z / 03:14:47Z | 两表字段+选项 | `base +field-list`（原始存 `tm_fields_raw.json` / `terms_fields_raw.json`） |
| 03:13:53Z | TM 全量 7 页 | `base +record-list --limit 200 --offset 0..1200`（原始存 `tm_page_*.json`，1358 行 1358 唯一 record_id） |
| 03:15:03Z | Terms 全量 2 页 | 同上（`terms_page_*.json`，232 行） |
| 03:17:12Z | P0 sweep 重跑（只读） | `python tools/lang_asset_sweep.py --out … --adjudication … --terminology --repo-root <main-tree>`（origin/main 树 + 活表） |

## 7. 本目录产出清单

- `rev11_candidates.md`（本文）
- `rev11_pool.csv` — 702 行待裁决面全量（pool / record_or_hash / status / pair / 双端文本 / 来源）
- `tm_candidates_auto-manual.jsonl`、`tm_candidates_hello-docs.jsonl` — 现算正式候选（均 0 行，空文件即证据）
- `tm_all_rows.json`、`terms_all_rows.json` — 两表归一化全量；`tm_page_*.json`、`terms_page_*.json`、`tm_fields_raw.json`、`terms_fields_raw.json` — 原始抓取
- `fork_report_20260919.md`、`adjudication_20260919.md` — 本轮 sweep 重跑报告与裁决清单
- `main-tree/` — origin/main 的 tools/data/docs/templates 只读导出（sweep 运行环境）
