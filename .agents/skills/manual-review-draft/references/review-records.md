# 审核记录：问题清单、决定与 tools_sha

私有审核仓库每条稿线的 `draft.json` 及其指向的两份记录。字段规则以
[review-drafts-site.md](../../../../code-as-doc/dev/rtd_manual_portal/review-drafts-site.md)
为准，站点构建（`tools/rtd/review_site.py`）会逐项校验；本页只给写稿时的要点和合成示例。

## draft.json

- `tools_sha`（工作稿必填）：写稿所用 auto-manual 提交，`git -C <auto-manual> rev-parse --short HEAD`。
- `issues`、`decisions`（可选）：稿线目录内的相对路径，不能是绝对路径、`..` 或符号链接。
- 有 `issues` 时不写 `rd_open`（它由问题清单派生）；保留时必须与派生结果完全一致。

## 问题清单 issues.json

```json
{"schema": "review-issues/1", "issues": [
  {"id": "R04", "title": "太阳能输入范围", "kind": "rd", "status": "open", "topic": "solar-input",
   "question": "上一代 12–60 V 范围是否适用？",
   "adoption": {"decision": "正文沿用上一代句子", "by": "操作者", "date": "2026-10-24"}},
  {"id": "R05", "title": "车充输入", "kind": "rd", "status": "confirmed",
   "resolution": {"by": "研发", "date": "2026-10-24", "evidence": "研发答复第 2 轮"}},
  {"id": "R06", "title": "短路电流", "kind": "rd", "status": "open", "topic": "short-circuit",
   "question": "目标规格未给最大短路电流及持续时间",
   "adoption": {"decision": "按一代主机 JE-1000E-SIL 写 1600A/1.25ms，绿色 一代数据", "by": "操作者", "date": "2026-10-27"}},
  {"id": "L01", "title": "警示标签措辞", "kind": "language", "status": "open"}
]}
```

- `kind`：`rd` 研发、`language` 语言审校、`compliance` 合规、`design` 设计、`content` 内容——由谁答复。
- `status`：`open` / `confirmed` / `dropped`；非 `open` 必须有 `resolution {by, date, evidence}`。
- `adoption` 记录正文采用了什么、谁决定；它不改 `status`。上例 R04 正文已采用上一代句子，但研发尚未确认适用性，仍是 `open`，继续计入待研发确认。R06 是缺数据时的一代补写，同样只记 `adoption`。
- `topic`：同型号多条稿线问同一问题时用同一小写短名（`solar-input`），站点据此提示跨稿线不一致。
- 允许附加字段（单元位置、参考原文、来源类型等）。
- 派生的待研发确认行：`R04 太阳能输入范围：上一代 12–60 V 范围是否适用？`。

## 决定文件 decisions.json

```json
[{"id": "D01", "title": "太阳能输入段落", "adopted": "沿用上一代句子，适用性待研发确认",
  "date": "2026-10-24", "status": "已采用", "source_type": "操作者决定", "request": "先按上一代写"}]
```

- 必填 `id`（`D01` 起，唯一）、`title`、`adopted`、`date`、`status`；只追加，不改写旧条目，被替代时写 `superseded_by`。

## 每轮检查

1. 站点构建通过；`WARNING … topic …` 已处理或写入审核意见。
2. 推送后 `python -m tools.rtd.review_table_sync <克隆目录>/docs/review-drafts --line <MODEL>/<REGION>`，确认计划后加 `--write`，报告回读。
3. 公开字段（飞书行会进入公开 Hello-Docs）不出现 `nameplate_model`、`sales_model` 等未发布型号；同步工具发现即拒写。
