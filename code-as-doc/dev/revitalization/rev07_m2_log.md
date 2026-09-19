# REV-07 / M2+M1 实跑日志 — ops_catalog_sync 首轮

- 任务：REV-07（[台账](../manual_revitalization_execution.md#rev-07)，方案 §5.3 M1/M2）。工具=
  [`tools/ops_catalog_sync.py`](../../../tools/ops_catalog_sync.py)，契约=
  [`web_publish_pipeline.md`](../web_publish_pipeline.md) §2.3。
- 授权：操作者夏冰 2026-09-18 批 M2 镜像化（「其它按你建议批」）；本轮唯一活表写=运营表 1 行机器列刷新。
- 身份：lark-cli 1.0.69，profile `cli_aaa0db0d4b39dcca`，`--as bot`。执行窗口（UTC）：2026-09-19T15:37Z–15:48Z。
- 原始输出（dry-run/写/回读/reconcile 全套 JSON+stdout）存于执行会话 scratchpad `rev_wave1/rev07_m2/raw/`；
  关键值全部内联在下。

## 1. 命令形状实测（只读探针，写前）

| 探针 | 结果 |
| --- | --- |
| `sheets +workbook-info`（运营表 K13JsXoUjhd75sth7eec1sKpnKd） | sheet `15c75c`「说明书目录」row_count=200，revision=27，`row_count` 平铺在 sheet 项上（工具兼容 grid_properties 回退形） |
| `sheets +csv-get --range A1:O3` | 表头与 15 列契约逐字相等；`[row=N]` 前缀、`has_more` 字段在位（工具对 has_more=true 拒绝出计划） |
| `base +record-list`（构建表 LD3lb4G1ua4GOVs1vxAc9W2enje/tblbnRHjpJeCVTtj） | 33 行；fields 为字符串数组；HTML_link 渲染形为「方括号 URL + 圆括号 URL」的 markdown 链接串（extract_link 已覆盖）；非空 3 行=US 2.3 + EU en/fr，全嵌套形 |

## 2. sync dry-run（存档后才写）

- manifest 源：Hello-Docs main pinned SHA `6b0d565e9a6d12da58a488b70a0101b72f7d8063`（manifest built_at 2026-09-17T07:23:17+00:00），52 targets。
- 运营表：52 数据行，revision 27。
- 计划：**in_sync=51 / updates=1 / appends=0 / orphans=0 / duplicates=0**。
- 唯一 update = row 20 `JE-1000H/EU/en`（正是 rev_wave1 writes_log 记过的漂移行）：
  - 当前版本 `2.0-20260913` → `2.0`
  - 目标构建时间UTC `2026-09-13T22:55:51+00:00` → `2026-09-16T09:54:02+00:00`
  - 内容提交 `505c484a838740a12823fa4ba78af1fb4c04d81c` → `c99b7169e3a16381d235d6cf5bf171962b0ad90b`

## 3. sync --write（授权写，1 行）

- 写形：`sheets +cells-set --range A20:K20`（仅机器列，仅 value，不带样式）；15:46:23Z。
- 回读（同行 A20:O20）：机器列与 manifest 逐格相等 ✓；人工列 L..O = `['', '待评估', '', '']`
  与写前一致（该行 L/N/O 本为空、M=待评估）✓。
- revision 27 → **28**；行数 52 → **52**（未增删行）✓；failures=0。
- 幂等复跑（写后第二次 dry-run）：**in_sync=52 / updates=0 / appends=0**，零写调用 ✓。

## 4. reconcile（M1，只读）

- 种子轮（占位白名单）：new=50 = 49×`target_unregistered` + 1×`ops_stale_row`（row 20，即 §2 的待修行），exit 1
  —— 与 rev06 基线（构建表 web 登记 3/52）完全一致；49 个 key 清单直接生成白名单
  [`data/ops_catalog_reconcile_whitelist.json`](../../../data/ops_catalog_reconcile_whitelist.json)。
- 终轮（写后 + 已提交白名单）：**exit 0**，known=49（全部 M0-05 Git-only 无回执基线命中并列出）、new=0；
  receipts=33 行读齐，3 条非空 HTML_link 全部命中 manifest 嵌套正式页（无 flat 形、无 unmatched）。

## 5. 结论与遗留

- M2 幂等同步、人工列保护、失败行隔离重试、M1 三面核对+白名单分类全部实证跑通；
  运营表回到与 manifest@6b0d565e 完全一致。
- 遗留（不在本轮授权）：① 49 个存量 target 是否补录队列回执（M0-05 附属，操作者 M2 决策；白名单已把
  它们压为已知差异）；② reconcile 的定时化（挂 cron/workflow）归 REV-16/后续切片；③ HTML_link
  写回后移（发布验证成功后再写）为姊妹 PR 范围。
