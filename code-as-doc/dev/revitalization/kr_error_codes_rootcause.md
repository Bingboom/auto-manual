# 根因报告：JE-2000E-KR 2026-09-05 re-seed 只生成 FC 一个错误码

- 核查时间（UTC）：2026-09-19T08:51:26Z（活表读取时刻，见 `live_read_utc.txt`）
- 全程只读：lark-cli 仅 `+record-list` / `+field-list`（profile `cli_aaa0db0d4b39dcca`，identity=user 唐夏冰）；git 仅 `git show` / `log` / `ls-remote`（主 checkout 未动，Hello-Docs 证据取自本 scratchpad 既有 blobless clone `rev_wave1/rev04/Hello-Docs`）。
- 原始证据文件：`live_troubleshooting_raw.json`（活表原样）、`live_troubleshooting_records.json`（字段对齐+record_id）。

## 结论：选 A（源表缺 JE-2000E 标注）——但成因是 #955 的语义变更把"当时合法的数据"变成了"欠标注的数据"

一句话：错误码源表里 F0–F9/FE 共 11 行是 `Model=ALL` 的通用行，FC 一行是 `Model=JE-2000E` 的专属行；**PR #955（2026-08-28 合入 main）把装配的型号筛选从"叠加"改成了"专属整组覆盖通用"（specific-or-fallback）**，于是 JE-2000E 只要存在任何一行专属行（FC），11 行 ALL 通用行就整组被遮蔽。09-05 re-seed 用的是新语义 → 只出 FC。数据本身自 08-22 快照以来在 Model/Region 维度**从未变过**（排除 C）；代码行为是**有意的且被测试钉死的**（不是"过滤逻辑丢了"，排除严格意义的 B）。在现行契约下，要让 JE-2000E_KR 出全 12 码，源表必须给 11 行通用行补 JE-2000E 标注 → **A**。

## 1. 源表与消费链路

| 项 | 值 |
| --- | --- |
| Base | 文档构建 `LD3lb4G1ua4GOVs1vxAc9W2enje`（业务面） |
| 表 | 内容源_TROUBLESHOOTING `tblOmJoAfU35brkb`（活表现有 65 行） |
| 适用型号表达 | `Model` 纯文本字段（`fldHVkhpQB`），逗号分享（`ALL` / `JE-2000E` / `JE-1000F, JE-1000H, …`）；**不是** link 列或市场标签 |
| 适用区域表达 | `Region` 纯文本字段（`flduZohon6`），逗号分享（`EU, AU, KR`） |
| 同步链 | sync-data 全量快照 → `data/phase2/troubleshooting_blocks.csv`（镜像 gitignored） |
| 装配消费方 | `tools/csv_pages/renderers_troubleshooting.py::_collect_rows`（origin/main），经 `render_troubleshooting_page` 进 seed/build |

筛选逻辑（origin/main 现行）：`Is_latest` → `_matches_region`（Region 含目标区域或 all/空）→ `_model_scope`（Model 含目标型号 = "specific"；含 all 或空 = "fallback"；否则剔除）→ **`selected = specific or fallback`**：只要有任意 specific 行，整组 fallback 行被丢弃。

## 2. 逐码矩阵（活表 2026-09-19，KR 相关 12 行 / 全表 65 行）

| 码 | 存在 | record_id | Model（有 JE-2000E？/ 有 JE-3000C？） | Region | 韩文列 | 现行语义下对 JE-2000E_KR 的 scope |
| --- | --- | --- | --- | --- | --- | --- |
| F0 | ✔ | recvkCEhrnyy9I | `ALL`（否 / 否） | `EU, AU, KR` | ✔（14 字） | fallback → 被 FC 遮蔽 |
| F1 | ✔ | recvkCEhrnfYRP | `ALL`（否 / 否） | `EU, AU, KR` | ✔（14） | fallback → 被遮蔽 |
| F2 | ✔ | recvkCEhrnQJsi | `ALL`（否 / 否） | `EU, AU, KR` | ✔（14） | fallback → 被遮蔽 |
| F3 | ✔ | recvkCEhrnCScJ | `ALL`（否 / 否） | `EU, AU, KR` | ✔（14） | fallback → 被遮蔽 |
| F4 | ✔ | recvkCEhrnB2pp | `ALL`（否 / 否） | `EU, AU, KR` | ✔（37） | fallback → 被遮蔽 |
| F5 | ✔ | recvkCEhrnTuRc | `ALL`（否 / 否） | `EU, AU, KR` | ✔（47） | fallback → 被遮蔽 |
| F6 | ✔ | recvkCEhrn6jor | `ALL`（否 / 否） | `EU, AU, KR` | ✔（232） | fallback → 被遮蔽 |
| F7 | ✔ | recvkCEhrnKqaX | `ALL`（否 / 否） | `EU, AU, KR` | ✔（137） | fallback → 被遮蔽 |
| F8 | ✔ | recvkCEhrnj0po | `ALL`（否 / 否） | `EU, AU, KR` | ✔（23） | fallback → 被遮蔽 |
| F9 | ✔ | recvkCEhrnpYJ8 | `ALL`（否 / 否） | `EU, AU, KR` | ✔（50） | fallback → 被遮蔽 |
| FE | ✔ | recvkCEhrnSjmV | `ALL`（否 / 否） | `EU, AU, KR` | ✔（23） | fallback → 被遮蔽 |
| FC | ✔ | recvsEBtlyMhcY | `JE-2000E`（**是** / 否） | `KR` | ✔（72） | **specific** → 唯一入选 |

全表除以上 12 行外无任何其它 KR 匹配行（Region 分布：JP×24、CN×11、`EU, AU, KR`×11、`US, pt-BR`×11、US×7、KR×1）。所有 12 行 `Is_latest=TRUE`。

## 3. 两个正交面交叉验证

- **活表**（上表，读取时刻 2026-09-19T08:51:26Z）。
- **本地 phase2 镜像** `data/phase2/troubleshooting_blocks.csv`（快照 2026-08-22T03:48:43Z，52 行）：12 行 KR 相关行的 `No./Model/Region/error_code/Is_latest` **与活表逐项一致**。唯一漂移 = FC 行 `corrective_measures_ko` 文本（镜像/两代 seed 均为旧文 "…Jackery Explorer 2000 Plus 리튬이차전지시스템…"，活表已是新文 "…본 제품…"）→ 该编辑发生在 09-05 之后、且不涉及 Model/Region，**不影响本结论**；镜像整体 52→65 的增量是 09 月新增的 13 行 JP 行，与 KR 无关。

## 4. 因果时间线（三次装配产物全部对得上，且被仿真复现）

| 时间（UTC） | 事件 | 产物 |
| --- | --- | --- |
| 2026-08-19T03:39 | JE-2000E-KR 首次 seed（`0ce2064`，旧血统） | **12 码**（F0–F9、FE、FC）——当时 main 上是旧筛选 `_matches_model`：ALL 行恒入选 + 专属行叠加 |
| 2026-08-28T01:38 | **PR #955（`ad14f261`）合入 main**：`_matches_model`（叠加）→ `_model_scope` + `selected = specific or fallback`（专属整组覆盖） | 动机 = JBP-2000B 电池包产线需要自带独立错误码表、不得继承主机码；行为被 `tests/test_csv_page_renderers.py::test_render_troubleshooting_page_prefers_model_specific_rows_over_all` 钉死（`assertNotIn("GENERIC", specific)`） |
| 2026-08-28T03:27 | JE-3000C-KR seed（`43d2030`，#955 后 1.8 小时） | **11 码**（F0–F9、FE；无 FC）——3000C 无专属行 → fallback 全组。⚠ 纠正 kr_fix/pr_body.md 的说法：3000C tip 是 **11** 个码不是 12 个，FC 从不适用于 3000C |
| 2026-09-05T07:57 | JE-2000E-KR re-seed（`f7b39579`） | **仅 FC** ——FC 行 specific，遮蔽 11 行 ALL fallback |

仿真验证（用与 origin/main 完全同构的筛选语义跑活表数据）：新逻辑 JE-2000E_KR=`[FC]`、JE-3000C_KR=11 码、旧逻辑 JE-2000E_KR=12 码 —— 三个历史产物全部复现。**排除 C**：08-22 镜像、08-28 3000C seed、09-05 2000E seed 三个时间点的产物都与今日活表的 Model/Region 值自洽，数据在关键维度没有被改过（活表修订历史 lark-cli 只读命令不可见，此为快照+产物推断，三点互证）。

**为什么不是严格的 B**：11 行通用行的标注（`Model=ALL`）一直都在、从未丢；管线也没有"丢"标注——它按 #955 有意引入、并有测试钉住的覆盖语义在工作。真正的缺口是：**#955 改契约时没有对存量数据做一次"哪些行还依赖旧叠加语义"的清点**，JE-2000E_KR 的 FC 行（拍在 08-19 之前、按叠加语义录入）是唯一踩中新旧语义差异的存量数据点。

## 5. 建议的 F6 修复清单（本任务不写，走审批）

**推荐（最小改动，11 个单元格）**：把 §2 表中 11 行（record_id recvkCEhrnyy9I / rnfYRP / rnQJsi / rnCScJ / rnB2pp / rnTuRc / rn6jor / rnKqaX / rnj0po / rnpYJ8 / rnSjmV）的 `Model`（文本字段 `fldHVkhpQB`）由 `ALL` 改为 **`ALL, JE-2000E`**。

- 效果：对 JE-2000E（EU/AU/KR 三区域）这 11 行升为 specific，与 FC 同组共存 → JE-2000E_KR 回到 12 码；`all` 令牌保留 → 其它所有型号仍按 fallback 拿到原 11 码。
- 已按现行语义对 10 个旁观 target 仿真回归（JE-3000C_KR、JE-1000H_KR、JE-2000E_EU、JE-3600A_EU、JBP-2000B_EU、JE-1000F_EU、JE-1000H_AU、JBP-2000B_US、JE-2000E_US）：**除 JE-2000E_KR 外全部输出不变**（含 JE-2000E_EU/AU——11 行从 fallback 变 specific 但选出的行集相同）。
- 写后必须：逐行回读 11 个 record 的 Model 值；重跑 sync-data；对 JE-2000E_KR 重新 seed 验证 12 码；再做基线重快照（与 kr_fix PR 的合并顺序由操作者定——先合恢复 PR 再修源表再 re-seed，或先修源表直接 re-seed，二选一，避免恢复内容再次被冲掉）。

**备选一（对齐美规先例，11 行新增）**：仿照 `US, pt-BR` 块的显式型号清单写法，克隆 11 行为 `Model=JE-2000E / Region=KR` 专属行。行数翻倍、维护两份韩文文案，不推荐，除非操作者想让 KR 的 JE-2000E 文案独立演化。

**备选二（改代码，工程决策，不属于 F6）**：把 `_collect_rows` 的覆盖粒度从"整组"改为"按 error_code 覆盖"。能不动数据修好本案，但会改动 #955 测试钉死的契约、且需重新论证 JBP 电池包整表替换场景——只作为议题上报，不作为本轮修法。

**护栏跟进建议**：给 check 阶段加一条"型号有专属行但专属码数 < 同区域通用码数"的告警（本案形态 = 1 条专属 vs 11 条通用），防止下一个"叠加式录入 + 覆盖式消费"的数据再静默丢行。

## 6. 附带纠错与观察

1. `kr_fix/pr_body.md` §1 佐证里"JE-3000C-KR tip 有全部 12 个错误码"**不准确**：实测 tip `c1550c5b` 是 11 码（F0–F9、FE），无 FC；"12"应是把表头行数进去了。该误差不影响其恢复内容，但影响"姊妹线正常"的推理——姊妹线其实同样在 #955 新语义下工作，只是它没有专属行、没踩坑。
2. FC 行韩文文案已在活表被改为「본 제품」表述（09-05 之后、本 scratchpad 各写入轮之外的编辑），当前 review 页（含 kr_fix 恢复稿）载的是旧文 —— 源表标注修复后的下一次 re-seed 会自然带上新文，无需另行处理，但验收时别把这处文本更新误判为回退。
