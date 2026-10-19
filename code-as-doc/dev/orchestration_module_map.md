# Orchestration Module Map

Status: active

Updated: 2026-10-13

This file records the current module boundaries for the repo's main workflow entrypoints.
Use it as the living map for "where should this logic go?" after the build, quality, release, and queue decomposition waves.

This is not the user workflow guide.
For day-to-day commands, use:

- [`code-as-doc/build_doc_guide.md`](../build_doc_guide.md)
- [`user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)

For external table and queue-state contracts, use:

- [`code-as-doc/dev/external_table_contracts.md`](external_table_contracts.md)
- [`code-as-doc/dev/queue_state_model.md`](queue_state_model.md)

## How to use this map

This file keeps the entrypoint rule (§1), the maintenance rules (§8) and this index.
Each module family is on its own page with its original section number: open only the
page your task needs, and update it in the same PR that moves a boundary. Add a row here
only for a new page.

| Section | Page | Read it when |
| --- | --- | --- |
| §2 | [`build-entrypoint.md`](orchestration_module_map/build-entrypoint.md) | you add or move logic behind a `build.py` action: command dispatch, build orchestration, runtime adapters |
| §3 | [`bundle-and-export.md`](orchestration_module_map/bundle-and-export.md) | you change bundle materialization or the Word, IDML, LaTeX or Web export modules |
| §4 | [`quality-and-release.md`](orchestration_module_map/quality-and-release.md) | you change quality gates, maintainability guardrails, diff/release reporting or review-preview packaging |
| §5 | [`build-queue.md`](orchestration_module_map/build-queue.md) | you change the Feishu build or review queue modules: routing, execution, writeback, adapters |
| §6, §7 | [`backport-and-intake.md`](orchestration_module_map/backport-and-intake.md) | you change the cloud-doc backport or source intake modules |
| §9 | [`decomposition-candidates.md`](orchestration_module_map/decomposition-candidates.md) | you look for the next decomposition candidate, or need the whole-document Web boundary or RTD product-knowledge module notes |

## 1. Entrypoint Rule

Keep these files orchestration-first:

- [`build.py`](../../build.py)
- [`tools/build/docs.py`](../../tools/build/docs.py)
- [`tools/build_queue/process_build_queue.py`](../../tools/build_queue/process_build_queue.py)

That means:

- parse and validate high-level entry arguments
- call stable helper modules
- keep compatibility wrappers when tests or external callers depend on existing names

Do not move new low-level implementation back into these files unless the behavior is truly entrypoint-specific.

工作台数据更新由 [`tools/workspace_snapshot.py`](../../tools/workspace_snapshot.py) 负责
完整读取与安全快照；`workspace_refresh_trigger` 在队列／TM 批次完成后发请求，
`workspace_refresh` 复用现有导出器，`workspace_refresh_publish` 只提交业务内容 PR，
`workspace_refresh_verify` 独立核验线上版本，`workspace_freshness` 仅提供冻结读取模型。
失败提醒复用 GitHub issue；模块不合入、不生产说明书、不推断历史活动。
见 [工作台数据持续更新](workspace_data_refresh.md)。

Read-only intake work packets and shared-art review live in
[`tools/manual_intake_assist/`](../../tools/manual_intake_assist/). The package
facade owns the unchanged `python -m tools.manual_intake_assist` command;
`packet.py` owns copy/evidence enumeration and checks, `art_review.py` owns
byte inventory and operator annotations. It does not assemble or approve manuals.

## 8. Maintenance Rules

When adding or moving logic in this area:

1. Prefer adding to an existing helper module before expanding an orchestration file.
2. If a new helper module is introduced, update this file in the same change.
3. If a major boundary changes, also update:
   - [`code-as-doc/code_optimization_log.md`](../code_optimization_log.md)
   - [`optimization_project.md`](../optimization_project.md)
4. Keep wrapper names stable in entry files when tests or external scripts patch them directly.
5. If a wrapper stops being needed, remove it only after tests and call sites are updated together.
6. When encoded field names are normalized, prefer unicode-escaped canonical constants in helper modules before deleting old literals from entry files.
