# F6 活表修复执行日志：错误码源表 11 行 Model 标注

- 授权：操作者原话「批」（2026-09-19），对象 = 根因报告 §5 推荐修法（11 个单元格，`ALL` → `ALL, JE-2000E`）
- 执行时间（UTC）：写前读 2026-09-19T09:00:55Z → 试写 09:02:36Z → 批量 09:03:05Z → 整表回读 09:03:51Z → sync 09:05:31Z
- 身份：lark-cli 1.0.69，profile `cli_aaa0db0d4b39dcca`（identity=user 唐夏冰，token valid）
- 目标：文档构建 base `LD3lb4G1ua4GOVs1vxAc9W2enje` / 表 内容源_TROUBLESHOOTING `tblOmJoAfU35brkb`
- 主 checkout 全程停在 `feat/sweep-terminology-crosscheck`，零 tracked 改动（见 §5 collateral 处理）
- 证据文件全部在本目录（`prewrite/`、`postwrite/`、`table_after.json`、`render_sim/`）

## 1. 写前确认（三问）

1. **目标存在**：11 行逐条 GET（`prewrite/<record_id>.json`），全部 `Model='ALL'`、`Region='EU, AU, KR'`、`Is_latest=['TRUE']`，error_code = F0–F9+FE，与根因报告 §2 逐项一致。
2. **表形**：`+field-list` 实测 `Model` = `fldHVkhpQB`，**plain text**（不是多选）→ 写形 = 字符串 `"ALL, JE-2000E"`。`Region`=`flduZohon6` text；共 18 字段。（`field_list.json`）
3. **加性/替换**：单字段 patch（upsert / batch-update），不建行不删行；FC 行 `recvsEBtlyMhcY` 不在写清单。

## 2. 逐笔写 + 回读（11/11 全部验证）

写形：试写 = `+record-upsert --record-id <id> --json '{"Model":"ALL, JE-2000E"}'`（裸字段 map）；成功后其余 10 行 = `+record-batch-update --json '{"record_id_list":[…10 ids…],"patch":{"Model":"ALL, JE-2000E"}}'`。每次写后 sleep 4s 再 GET。

| record_id | error_code | 前值 Model | 写后 Model（GET 回读） | 回读全字段 diff | 方式 |
| --- | --- | --- | --- | --- | --- |
| recvkCEhrnyy9I | F0 | `ALL` | `ALL, JE-2000E` | 仅 Model | 试写 upsert（09:02:36Z ok） |
| recvkCEhrnfYRP | F1 | `ALL` | `ALL, JE-2000E` | 仅 Model | batch（09:03:05Z ok） |
| recvkCEhrnQJsi | F2 | `ALL` | `ALL, JE-2000E` | 仅 Model | batch |
| recvkCEhrnCScJ | F3 | `ALL` | `ALL, JE-2000E` | 仅 Model | batch |
| recvkCEhrnB2pp | F4 | `ALL` | `ALL, JE-2000E` | 仅 Model | batch |
| recvkCEhrnTuRc | F5 | `ALL` | `ALL, JE-2000E` | 仅 Model | batch |
| recvkCEhrn6jor | F6 | `ALL` | `ALL, JE-2000E` | 仅 Model | batch |
| recvkCEhrnKqaX | F7 | `ALL` | `ALL, JE-2000E` | 仅 Model | batch |
| recvkCEhrnj0po | F8 | `ALL` | `ALL, JE-2000E` | 仅 Model | batch |
| recvkCEhrnpYJ8 | F9 | `ALL` | `ALL, JE-2000E` | 仅 Model | batch |
| recvkCEhrnSjmV | FE | `ALL` | `ALL, JE-2000E` | 仅 Model | batch |

回读判定：每行 postwrite GET 与 prewrite GET 全 18 字段逐项 diff，**唯一变化字段 = Model**（韩文/英文文案、Region、Is_latest 等原样）。

## 3. 整表零漂移验证

`+record-list --limit 200` 全表拉取（09:03:51Z，`table_after.json`）对比根因轮活表快照（`../kr_rootcause/live_troubleshooting_records.json`，08:51:26Z）：

- 行数 65 → 65，无增无删（record_id 集合完全一致）
- 全表逐格 diff：**变化单元格 = 11 个，全部是清单内行的 Model**；0 个意外变化
- FC 行 recvsEBtlyMhcY 未动 ✓

## 4. sync-data 镜像验证

- 跑前核对 `~/.openclaw/.env`（28 键）：`FEISHU_PHASE2_BASE_TOKEN=LD3lb4G1ua4GOVs1vxAc9W2enje` ✓、`FEISHU_PHASE2_TROUBLESHOOTING_TABLE_ID=tblOmJoAfU35brkb`（view `vewZne4CUk`）✓、**`FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID=tbltnkDIdwiDOP7d` 在正确位** ✓（能力表洗白前科的防线）
- 命令：`.venv/bin/python build.py sync-data --config configs/config.us.yaml --table troubleshooting`（按 TABLE_ORDER 只选 troubleshooting，其余 8 张内容表 SKIP）
- 结果：`troubleshooting: rows=65 changed=yes new_sha=4afe9830…`；镜像 `data/phase2/troubleshooting_blocks.csv` 52 行（08-22 旧快照）→ 65 行
- 镜像内容核对：11 行 `Model='ALL, JE-2000E'` / `Region='EU, AU, KR'`，码集 = F0–F9+FE ✓；其余分组（CN 11 / JP 11 / US,pt-BR 11 / JBP-2000B US 7 / JBP-2000B JP 13 / FC KR 1）与活表一致
- phase2 目录 md5 前后对照（`phase2_md5_before.txt` / `phase2_md5_after.txt`）：变化 = troubleshooting_blocks.csv + 三个 sync 簿记文件（snapshot_manifest / source_record_index / web_composite_manifest）+ 22 个**纯新增**的 web_composites 附件 PNG；**九张内容表 CSV（Spec_Master 等）零变化**

## 5. Collateral（sync 副作用）处理

`--table troubleshooting` 仍无条件刷新派生文件，动了两个 **git tracked** 文件：

- `data/model_capabilities.csv`（+1 行）与 `data/asset_registry.csv`（+96/-11，含引号抖动）
- 用 sync 日志的 old_sha 对 `git show HEAD:<file>` sha256 证明两文件**写前干净**（= 我的 sync 弄脏，非他窗工作）→ `git checkout --` 恢复，恢复后 sha256 与 HEAD 逐字节一致
- 同步出的新内容已存档备查：`collateral_model_capabilities.diff`、`collateral_asset_registry.diff`、`*_synced_20260919.csv`（Base 侧确有新数据，属后续正式 sync 轮，不属本任务）
- 残留（无害）：`data/phase2/snapshot_manifest.json`（gitignored）的 derived_files 记录的是 sync 后 sha，与恢复后的两文件不符；实测下游（data_snapshot / schema_drift）只校验 logical name 存在性、不校验 sha，下次全量 sync 自愈
- `data/.phase2.snapshot.lock`（?? 未跟踪）为 08-19 遗留物，非本轮产物，未动
- 最终 `git status`：本轮零新增足迹（现存脏项均为他窗遗留，mtime 08-19/08-21）

## 6. 渲染验证矩阵（真代码，非同构复写）

方法：`git archive origin/main`（2e4bda10）只读抽出 tools+configs+data 到 scratchpad（`render_sim/originmain_tree/`，主 checkout 未动），**直接 import 真 `tools.csv_pages.renderers_troubleshooting._collect_rows`**，喂刷新后的镜像 CSV；"before" = 同一数据集把 11 格在内存里回退为 `ALL`（§3 已证明这是唯一 delta）。比较含 error_code + measures 全文。

| target | lang | before 码数 | after 码数 | 判定 |
| --- | --- | --- | --- | --- |
| **JE-2000E_KR** | ko | 1（仅 FC，复现 09-05 坏产物） | **12（F0–F9, FE, FC）** | ✅ 修复生效 |
| JE-3000C_KR | ko | 11 | 11 | 逐字节不变 |
| JE-1000H_KR | ko | 11 | 11 | 逐字节不变 |
| JE-2000E_EU | en | 11 | 11 | 逐字节不变（fallback→specific 但行集相同） |
| JE-2000E_AU | en | 11 | 11 | 逐字节不变 |
| JE-1000F_EU | en | 11 | 11 | 逐字节不变 |
| JE-3600A_EU | en | 11 | 11 | 逐字节不变 |
| JBP-2000B_EU | en | 11 | 11 | 逐字节不变 |
| JE-1000H_AU | en | 11 | 11 | 逐字节不变 |
| JE-1000F_US | en | 11 | 11 | 逐字节不变 |
| JE-2000E_US | en | 11 | 11 | 逐字节不变 |
| JBP-2000B_US | en | 7（自有表） | 7 | 逐字节不变 |
| JE-900B_JP | jp | 11 | 11 | 逐字节不变 |

明细：`render_sim/before_after_matrix.json`、`render_sim/sim_after_fix.json`。

## 7. 未做（按任务边界）

- re-seed 实跑与基线重快照（#90 合并后基线收尾另有 agent 在做；re-seed 属后续轮次）
- 未改任何代码；未动 `docs/templates/`、`docs/_review/`、其它源表
- 注意事项（交接）：下次 JE-2000E_KR re-seed 会自然带上 FC 行活表新文（「본 제품」表述），验收时勿误判为回退（根因报告 §6.2）
