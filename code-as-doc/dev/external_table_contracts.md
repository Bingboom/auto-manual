# External Table Contracts

Updated: 2026-05-07

This file records the first repo-owned contract for external Feishu/Lark Base tables.
It is the stability boundary between external content governance and the local build,
queue, review, and release code.

Keep this document aligned when changing:

- [`tools/data_snapshot.py`](../../tools/data_snapshot.py)
- [`tools/validate_config.py`](../../tools/validate_config.py)
- [`tools/queue_contract.py`](../../tools/queue_contract.py)
- [`tools/process_review_start_queue_records.py`](../../tools/process_review_start_queue_records.py)
- [`tools/sync_data.py`](../../tools/sync_data.py)

## 1. Phase2 Snapshot Tables

The phase2 snapshot is frozen under `data/phase2/` by default. A valid snapshot
must contain a readable `snapshot_manifest.json`, all required CSV exports, and
all required derived files.

Required synced tables:

| Logical table | Snapshot file | Purpose |
| --- | --- | --- |
| `spec_master` | `Spec_Master.csv` | canonical spec values used by generated pages |
| `spec_footnotes` | `Spec_Footnotes.csv` | footnote text and selectors |
| `spec_notes` | `Spec_Notes.csv` | note text and selectors |
| `spec_titles` | `spec_titles.csv` | localized spec title labels |
| `symbols_blocks` | `symbols_blocks.csv` | symbol-block source rows |

Required derived files:

| Derived file | Purpose |
| --- | --- |
| `row_key_mapping.csv` | stable mapping from source rows to generated-page row keys |

Optional synced tables currently accepted by config validation:

| Logical table | Purpose |
| --- | --- |
| `lcd_icons` | icon/image metadata for LCD-related output |
| `variable_defaults` | default variable values |
| `variable_lang_overrides` | language-specific variable overrides |

Snapshot compatibility rules:

- `snapshot_manifest.json` must be valid JSON with table entries that include
  the logical names for required tables.
- A required table is valid only when the manifest says it was synced/requested
  and the corresponding CSV exists.
- Required tables must not be silently skipped. If an upstream table is
  intentionally removed, update the code contract, fixtures, and this document
  in the same change.
- `page_registry.csv` and `data/layout_params.csv` remain repo-maintained inputs
  outside the phase2 sync flow.

## 2. Document_link

`Document_link` is the queue table for Build Draft Package and Publish. Start
Review may reuse the same table/view binding, but the build queue consumes only
rows whose `Workflow_action` maps to Build Draft Package or Publish.

Read fields:

| Field | Required | Type expectation | Notes |
| --- | --- | --- | --- |
| `Document_ID` | yes for build/publish | scalar/link-like text | versioned document identity |
| `Document_Key` | yes | scalar/link-like text | expected `<MODEL>_<REGION>` for grouped routing |
| `Version` | yes for versioned outputs | scalar/list text | preserved in result strings and artifact names |
| `Lang` | yes | scalar/list text | normalized to lower-case where needed |
| `Build_family` | optional | scalar/list text | config-routing hint, for example `us-merged` |
| `Workflow_action` | yes | scalar/list text | canonical values: `Build Draft Package`, `Publish` |
| `Doc_phase` | deprecated | scalar/list text | compatibility fallback only; do not add new rows with it |
| `Git_ref` | required for Build Draft Package | scalar/link-like text | review branch source; Publish uses it when present |
| `是否触发文档构建` | yes | checkbox/list/text | canonical build trigger |
| `是否立即构建` | optional | checkbox | event-listener trigger, not enough by itself |
| `是否强制刷新数据` | optional | checkbox | controls whether queue runs `sync-data` before build |
| `是否上传钉钉` | optional | checkbox | switches artifact sink to DingTalk/Alidocs when enabled |
| `DingTalk_target_node_url` | optional | scalar text | explicit DingTalk destination |
| `operator_union_id` | optional | scalar text | DingTalk operator/session identity |

Writeback fields:

| Field | Written when | Value expectation |
| --- | --- | --- |
| `开始构建时间` | running | epoch milliseconds |
| `构建结果` | running/success/failure | string prefixed by `RUNNING`, `SUCCESS`, or `FAILED` |
| `Document directory` | success/failure with latest local artifact | absolute local path |
| `Document link` | success/failure with latest remote artifact | Feishu Drive/Wiki or DingTalk URL |
| `Document link_dd` | optional DingTalk writeback | DingTalk URL or empty string |
| `HTML_link` | publish HTML deploy workflow | deployed Vercel URL when field exists |
| `data_sync` | queue build attempt | `refreshed`, `skipped`, or `failed` |
| `是否触发文档构建` | success | `已构建` |
| `是否立即构建` | success/failure | `false` |
| `是否强制刷新数据` | success/failure | `false` |

Compatible aliases:

| Canonical field | Accepted alias |
| --- | --- |
| `是否触发文档构建` | `是否构建文档？` |
| `operator_union_id` | `DingTalk_session_key`, `钉钉会话键` |
| `DingTalk_target_node_url` | `钉钉上传节点`, `default_target_node_url` |

## 3. Review Init

Review Init starts or restarts review branches. The maintained implementation
currently reuses the `Document_link` table/view binding for GitHub-hosted worker
secrets, but it consumes only rows whose `Workflow_action` maps to Start Review.

Read fields:

| Field | Required | Type expectation | Notes |
| --- | --- | --- | --- |
| `Document_Key` | yes | scalar/link-like text | required `<MODEL>_<REGION>` target identity |
| `Workflow_action` | yes | scalar/list text | canonical value: `Start Review` |
| `是否进入Review` | yes | checkbox/text | true/checked means pending |
| `Document_ID` | optional | scalar/link-like text | Start Review does not require a versioned id |
| `Build_family` | optional | scalar/list text | config-routing hint |
| `Lang` | optional | scalar/list text | config-routing hint |
| `Version` | optional | scalar/list text | must agree within grouped rows when present |
| `Task_id` | optional | scalar text | stable selector when `Document_Key` is a linked field |
| `Review_status` | optional | scalar/list text | not a duplicate guard; `InReview` can be restarted |
| `Git_ref` | optional | scalar text | reused branch name if present |
| `PR_url` | optional | scalar text | reused or rewritten by the worker |

Writeback fields:

| Field | Written when | Value expectation |
| --- | --- | --- |
| `Git_ref` | success | review branch name |
| `PR_url` | success | created or reused GitHub PR URL |
| `Review_status` | success | `InReview` |
| `是否进入Review` | success | `false` |

## 4. Drift Rules

- Field additions, removals, aliases, or type changes must update this document
  and the relevant parser/writeback tests in the same change.
- Config validation should reject unsupported phase2 table keys before a live
  queue run can depend on them.
- Schema drift checks should run against fixed fixtures or dry-run payloads
  before depending on real Feishu network state.
- First offline gate: `python3 tools/schema_drift.py --payload tests/fixtures/schema_drift/passing_payload.json`
  validates required phase2 logical tables, required CSV headers, and required
  queue writeback fields without contacting Feishu.
- External table names are product contracts. Prefer adding compatibility aliases
  before renaming a live field.
