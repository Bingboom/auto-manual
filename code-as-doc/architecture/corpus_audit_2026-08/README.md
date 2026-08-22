# corpus_audit_2026-08 — 语料盘点可复算数据集

**本目录是《manual_ia_audit_2026-08.md》（及骨架库设计文档引用其数字处）全部核心数字的唯一可复算来源。**
报告正文与本目录冲突时，以 `python3 stats.py` 的输出为准，并回改报告。

运行方式（纯 stdlib，无依赖）：

```bash
python3 stats.py   # exit 0 = 全部一致性断言通过；exit 1 = 数据集自相矛盾
```

## 1. 三个分母（何时用哪个）

| 分母 | 值 | 定义 | 何时用 |
| --- | --- | --- | --- |
| 磁盘文件 | **59** | `manuals.csv` 的 `file_seq` 去重数。物理 PDF 计数 | 语料获取/覆盖账、转曲件比例（8/59）、下载与登记核对 |
| 独立内容 | **58** | `independent_content=Y` 的行数。结构/内容层的去重本 | 一切结构统计：槽位、覆盖率、五格成员、重构通过率 |
| (SKU, 区规) 组合 | **57** | 全部登记行（含别名行）的 `(sku, region)` 去重数 | 产线目标对齐、区规覆盖缺口（§6 类账目） |

三者关系：登记行 60 = 文件 59 + 1（墨西哥规槽位别名行共享文件）；
独立内容 58 = 文件 59 − 1（HTE152 错档件与 HTE154 日规正名件为同一内容的两份文件）；
(SKU,区规) 57 = 60 行去重（HTE140 日规三变体共 1 组合，HTE154 日规两文件共 1 组合）。

## 2. 两组折叠对的编码（口径在此写死）

1. **HTE153 墨西哥规 = 美加规**：同一份 58 页 EN/FR/ES 文件服务两个区规槽位（**1 文件 2 槽位**）。
   编码为**两行**：墨西哥规行 `independent_content=N`、`alias_of=美加规行的 slug`（两行 slug 相同，
   以 region 区分）、**与美加规行共用同一个 `file_seq`**。结构统计（topics/reconstruction）只有美加规行参与。
2. **HTE152 错档件 = HTE154 日规排版变体**：原挂 HTE152/日规 的文件实为 HTE154 平台
   （文件名自证 HTE1542000A；与正名件抽取文本逐字节相同，text-md5 51d26e771b74），
   **2 文件 1 独立内容**。编码为独立 `file_seq` 的一行，`sku` 改登记为 HTE154、
   `independent_content=N`、`alias_of=HTE154 日规正名件`。腾出的 (HTE152, 日规) 槽位由
   journal 3 分解的真本（JE-2000E《…2000PlusV2 电子版取扱説明書》）填充。

## 3. 各 CSV 的来源与字段约定

| 文件 | 内容 | 来源 |
| --- | --- | --- |
| `manuals.csv` | 60 登记行（59 文件 + 墨规别名行） | journal 1（55 条分解记录）、journal 3（HTE152 日规真本 + 错档裁决）、journal 4（HTE153 AU/KR/BR）、audit §7.4（HTE140 No-225 重建行） |
| `topics.csv` | 每个独立内容一组行；`order` 为书内槽位序（印刷页序分解产物的原始顺序），`topic_id_raw` 为分解原值，`topic_id_normalized` 为归一后 id；**normalized 为空 = 该原始槽位在归一时被删除/吸收/收敛**（共 7 处） | 章节序列：journal 1/3/4 的 `chapters`；归一规则：journal 2 `normalize:topic-ledger` 的 8 条 merge |
| `topic_ledger.csv` | 归一后 30 id 词表 + 三档 tier + 合并谱系 | journal 2（词表 39→30、三档 15/4/11）；`first_seen_slug` 为按 `file_seq` 序的确定性推导值（journal 未直接给出） |
| `reconstruction.csv` | 58 独立内容的重构判定 | journal 1 r19（Phase A 判定与 outlier）、journal 2 r00/r01（印刷页序口径重测：A1 假分叉 3 本、A3 同页平局 3 本）、journal 2 r02（日规加电包归 BP、A5 撤销为 JP@v1 体例版本）、journal 3（真本纯通过）、journal 4（AU/KR/BR 纯通过） |

journal 路径（只读原始证据，不随仓库分发）：
`~/.claude/projects/-Users-hello-tech-team-Documents-GitHub-auto-manual/a8174933-fac0-457b-a22c-ff34a22e6e25/subagents/workflows/{wf_1d8d06c3-a3a, wf_23177ec3-b4c, wf_bdeee803-3c6, wf_64a76562-1f6}/journal.jsonl`

## 4. 槽位与重构的口径

- **槽位两层**：原始槽位 983（分解忠实层，含同书多实例与后被吸收的提级条目）；
  归一槽位 976（骨架统计口径 = 三档表、覆盖率、核心 19 id 份额一律用它）。
  差 7 = HTE156 中规重复封底 1 + W7 层级吸收 3（screen_operation / energy_saving_mode /
  vertical_stand_mounting）+ 同书多实例收敛 3（HTP015 日规 symbol×2、HTE110 日规
  app_user_manual、HTE110 欧英规 app_setup×2）。
- **重构口径**：印刷页序（journal 2 采纳、journal 3/4 沿用）——同页两章不计先后；
  fcc / regulatory_compliance 按浮动合规片段豁免；storage↔spec、connections↔troubleshooting
  等 T5 类槽位对参数豁免。overlay 封闭集：T1 symbol↔UMI 互换、T2 storage↔troubleshooting
  真分叉、T3 storage 后移至 spec 后、T4 troubleshooting 前置至 lcd 后、T6 storage 前移至
  spec 前、T7 usage_precautions 后置至 warranty 后。
- **五格**：二维键（骨架家族 × 体例族）。HTE119 日规与 HTP007 日规按 journal 2 r02 落
  JP@v1 体例版本行（分属 MAIN@JP / BP@JP），HTE110 日规仍为 outlier。**MAIN@JP = 14**
  由此闭合：12 现役日规主机（含 HTE152 真本）+ HTE140 No-225 补记 + HTE119（JP@v1）；
  13/14 纯通过与设计文档 §4.4 的 92.9% 一致。BP@JP 的格自有规范序列在设计文档中仍标
  pending，两本 JP@v2 加电包的纯通过判定沿用 phaseA 的 JP 序列测量。

## 5. 与报告已发布数字的已知差异（重算修正，报告应回改）

| 数字 | 报告/journal 曾发布 | 本数据集重算 | 差因 |
| --- | --- | --- | --- |
| 总槽位 | §2 头 981 / §3 表 926 | 原始 983 / 归一 976 | 981=926+55 的底数 926 本身少算 2（journal 2 已实测 55 本原始=928）；981/926 均未叠加 错档−16/真本+18/No-225+16/墨规去重−18 的净账 |
| 纯删除 | 46/58 = 79.3% | **47/58 = 81.0%** | 发布值沿用台账（墨规幽灵行占一个 overlay 名额、No-225 无判定行）；补记 No-225（纯通过）并剔除墨规行后 +1 |
| 需 overlay | 9 本 | **8 本** | 墨规行（T1）非独立内容，去重后 T1 由 4 本变 3 本 |
| ≤1 overlay | 55/58 = 94.8% | 55/58 = 94.8%（一致） | 上两条相抵 |
| MAIN@INTL 成员 | 25→28 | **27** | 28 含墨规幽灵成员 |
| MAIN@JP 成员 | 12 vs 13/14 混用 | **14**（13 纯通过） | 见 §4 |
| troubleshooting 覆盖 | 52/58 | **53/58** | 台账曾把 HTE162 中规记为命中又另行扣减；序列层从未含它，直接按序列计数 |
| storage 覆盖 | 39/58 | **38/58** | 39 未剔除墨规幽灵行 |
| preface 覆盖 | 32/58 | **31/58** | 同上 |
| back_cover 覆盖 | 48/58 | **43/58** | 发布值为原始 id 口径；归一后中规合格证页不再计 back_cover（journal 2 merge#2） |
| 核心 19 id 份额 | 895/981≈91.2%（归一后≈92.3%） | **898/976 = 92.0%** | 见总槽位行；本值即"归一后重扫"的落数 |

## 6. 已知提取缺口

见 stats 输出与 `manuals.csv` notes；汇总：

1. **HTE140 日规 No-225（沙金色/SG 件）行为重建行**：分解任务输出已清理，章级序列按姊妹
   WH 件复制（audit §7.4 已证两件章级同构、14 组实质差异全在子章/表格/条款层），
   `provenance=reconstructed-from-sibling+audit§7.4`。子章层差异不在本数据集内。
2. **HTE153 美加规文件的寄生 FCC 块未入槽位台账**：journal 4 证实该块实在
   （EN p6 / FR p24 / ES p42，原分解漏检并撤销了"无 FCC"结论），但没有任何 journal
   重发含 fcc 槽的修订序列，按"不编造"原则不补行——这是台账债，补测后应在 topics.csv
   增行并重跑 stats。
3. **HTE153 AU/KR/BR 与 HTE152 日规真本的磁盘文件名**未随 journal 提供，slug 为构造值，
   notes 记录了已知的实物特征（页数、MD5 线索、文档控制号）。
4. journal 4 曾提及 AU 有一份重复下载件（MD5 0935d5e0 与主件相同），按 W1 口径不入册。
