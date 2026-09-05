# External Table Contracts

Updated: 2026-06-29

This file records the first repo-owned contract for external Feishu/Lark Base tables.
It is the stability boundary between external content governance and the local build,
queue, review, and release code.

Machine-readable phase2 source-table contract:

- [`../../data/source_table_contracts/phase2_source_tables.json`](../../data/source_table_contracts/phase2_source_tables.json)
- Loader/validator: [`../../tools/source_table_contract.py`](../../tools/source_table_contract.py)
- Drift-facing tests: [`../../tests/test_source_table_contract.py`](../../tests/test_source_table_contract.py)

Use the JSON contract as the durable index when changing online source-table
structure. This document explains the human workflow; the JSON records the
table-by-table keys, snapshot file, intake target, writable fields, source-record
index mapping, and guarded writer boundary used by automation.

Keep this document aligned when changing:

- [`tools/data_snapshot.py`](../../tools/data_snapshot.py)
- [`tools/source_table_contract.py`](../../tools/source_table_contract.py)
- [`data/source_table_contracts/phase2_source_tables.json`](../../data/source_table_contracts/phase2_source_tables.json)
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
| `symbols_blocks` | `symbols_blocks.csv` | symbol-block source rows |
| `troubleshooting` | `troubleshooting_blocks.csv` | troubleshooting error-code rows |
| `lcd_icons` | `lcd_icons_blocks.csv` | LCD icon row content, images, and variable markers |
| `variable_defaults` | `Variable_Defaults.csv` | default values for LCD description variables |
| `variable_lang_overrides` | `Variable_Lang_Overrides.csv` | language-specific LCD variable overrides |
| `manual_copy_source` | `Manual_Copy_Source.csv` | single-language source rows for page titles, headers, labels, and spec titles |
| Translation Memory rows tagged `manual_copy` | `Localized_Copy.csv` | generated multilingual short-copy runtime file |
| Translation Memory rows with `是否为 status word=Y` | `Status_Words.csv` | LCD status-word matching snapshot for bolding description prefixes |

The source-table contract additionally records whether each source table is:

- an intake target (`Spec_Master`, `Page_Placeholders_Source`,
  `Manual_Copy_Source`, `Spec_Footnotes`, `Spec_Notes`);
- update-capable through `source-table-change-request/v1`
  (`Spec_Master`, `Page_Placeholders_Source`, `Manual_Copy_Source`);
- indexed by `source_record_index.json` for exact live `record_id` resolution;
- a generated snapshot/read model only.

Required derived files:

| Derived file | Purpose |
| --- | --- |
| `row_key_mapping.csv` | stable mapping from source rows to generated-page row keys |
| `spec_titles.csv` | generated spec title labels and default section ordering |
| `Localized_Copy.csv` | generated multilingual short copy for `{{ copy:<copy_key> }}` |
| `Status_Words.csv` | generated LCD status-word matching terms |

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

### Localized columns in frozen snapshots

[`tools/lang_registry.py`](../../tools/lang_registry.py) owns language identity,
input aliases, historical snapshot suffixes, and table-specific column names.
[`tools/utils/csv_fields.py`](../../tools/utils/csv_fields.py) owns the shared
column spelling and cell/header selection primitives, with no business-reader
or language-registry dependency. [`tools/localized_copy.py`](../../tools/localized_copy.py)
keeps compatible exports of the same functions, the registry-aware helpers and
the strict copy-key resolver. The primitives do not choose a table's fallback policy:

- `snapshot_language_suffixes` / `localized_cell` use exact snapshot suffixes
  in registry order, testing each cell for nonempty stripped text.
- `localized_columns` expands caller-supplied suffixes into legacy CSV case and
  underscore spellings. `table_localized_columns` restricts candidates to the
  registered table/field. Neither adds English or source columns. The default
  case folding is unchanged; Spec_Master uses `casefold=False` to retain its
  historical `lower()` spelling even for unknown language tokens.
- `first_existing_column` tests headers, regardless of cell content;
  `first_text` tests cell values. Missing keys, `None`, and empty strings are
  unavailable to `first_text`; whitespace is unavailable with its default
  `strip=True`. With `strip=False`, whitespace is a value and can stop the
  search. `fallback_columns` is explicit and ordered in both APIs.
- `LocalizedCopyResolver` retains its strict copy-key contract: missing target
  language text is an error. The permissive primitives do not change it.

Canonical identity and column spelling are separate:

| Canonical language | Input aliases | Exact snapshot suffix order | Table-specific examples |
| --- | --- | --- | --- |
| `ja` | `ja`, `jp` | `jp`, `ja` | LCD/trouble use `jp`; footnotes use `Text_ja` |
| `uk` | `uk`, `ukr` | `uk`, `ukr` | LCD/trouble use `ukr`; footnotes use `Text_uk` |
| `pt-BR` | `pt-BR`, `pt_br`, `br` | `pt-BR`, `br` | LCD/trouble declare both; footnotes also declare bare `pt-BR` |
| `zh` | `zh` | `zh`, `cn` | Current table schemas use `zh`; `cn` is only a historical suffix, not a registered input alias |

Input-alias searches retain the requested alias first; exact snapshot searches
retain registry suffix order. Unknown nonempty language tokens keep the legacy
literal-column lookup. Empty language input adds no shared-helper candidates;
IDML's public `normalize_lang` compatibility façade still supplies its existing
`en` default and historical first suffix.

The migrated consumers deliberately retain different policies:

| Reader / fields | Candidate and fallback policy |
| --- | --- |
| IDML `load_spec_sections` | Exact snapshot suffixes per cell, then the corresponding `Row_label_source`, `Param_source`, or `Value_source`; no added English fallback |
| IDML LCD / troubleshooting / annotations | Exact snapshot suffixes per cell, then the explicitly named `*_en` / `Text_en` cell |
| IDML Symbols | Only the first historical suffix, then the matching English field per cell; it does not gain the other loaders' alias scan |
| CSV LCD / troubleshooting | Select a column from table metadata by header presence, with explicit English column fallback. For each row, an empty selected cell uses English; whitespace stops selection before stripping. A blank primary alias never advances to another alias in that row |
| CSV Symbols icon rows | Select from first-row headers using input alias order, then the legacy raw spelling, source-language spelling, and `text_en`. An empty selected cell remains an error; English is a missing-column fallback only |
| CSV builder footnote/note normalization | Registered `spec_footnotes` columns first (including the historical bare Portuguese field), then input aliases and legacy spellings. Preserve raw whitespace and do not add English fallback |
| CSV spec parser | For `Row_label` / `Param` / `Value`, English or the row's source language uses source fields first and bypasses localized columns. Other requests try input aliases, then source fields/base, then the caller's explicit default keys |
| Spec_Master utility lookup | For `Row_label` / `Param` / `Value`, English or the normalized source language bypasses localized fields. Otherwise try input spelling, lower, upper, underscore and lower underscore, followed only by literal br-family fallbacks; then source fields, bare base and `Spec_Value`. Other bases have no implicit source fields |

Spec_Master keeps its narrower policy in
[`tools/utils/spec_master_row_helpers.py`](../../tools/utils/spec_master_row_helpers.py),
shared by the product-name and template-substitution lookups. Only requests
`br`, `pt-br` or `pt_br` (case-insensitive) append the literal fallbacks
`br`, `pt-BR`, `pt-br`, `pt_BR`, `pt_br`; those fallbacks are not expanded again.
For example a `br` request does not gain `Value_PT-BR`, and `ja` does not gain
`Value_jp`. No registry alias search or silent English fallback is added.
`Source_lang` normalization is unchanged and separate from requested-language
spelling: a source `JP` normalizes to `ja`, but a request `jp` still looks for
`*_jp`. Unknown source languages keep the existing unrecognized-source behavior.

Source fields retain canonical-before-lowercase order. A source write selects
the first **present header**, including an empty cell, or the canonical source
header if neither exists. Page-label preference still rejects translation
notes and source-equivalent labels before falling back to `Value`; the lookup's
existing lowercasing of the requested label language, row ranking and filtering
are unchanged.

Old-path exit scope: IDML's `_SUFFIX_CANDIDATES`, `_lang_suffixes`, and
`_localized_cell`, the LCD/trouble `_lang_suffix` / `_lang_suffix_candidates` /
`_first_existing` copies, and the builder/Symbols/spec-parser candidate loops
are removed. Thin wrappers remain where they own table policy or RST text
normalization. The IDML loaders are public compatibility readers exported by
`tools/export_idml.py`; production IDML consumes the prepared-bundle IR.

The second slice removes Spec_Master's `_first_non_empty` implementation,
`_first_existing_key`, `_lang_suffix_candidates` and the lookup's duplicated
`_pick_lang_specific_value` loop. Row helpers and lookups now call the shared
primitives; the old `_first_non_empty` import is a direct compatibility alias
for unchanged audit/mapping readers. The remaining `_spec_lang_columns` and
`_pick_lang_value` wrappers own only Spec_Master candidate/source policy.

This leaves spec-master source normalization and row ranking/filtering, IDML's
legacy spec-title mapping, status-word matching, paths, caches, and
target selection with their existing owners. It does not alter snapshot data,
schema, online Base access, or the JP native-validation debt/eligibility state.
Consumer boundary cases and real JP/French page builds are covered in
[`tests/test_snapshot_localization.py`](../../tests/test_snapshot_localization.py);
primitive selection cases are in
[`tests/test_localized_copy.py`](../../tests/test_localized_copy.py). Spec_Master
source/candidate policy, public product/substitution behavior, and fresh-process
import permutations are covered in
[`tests/test_spec_master_read_policy.py`](../../tests/test_spec_master_read_policy.py).

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
| `构建结果` | claim/running/success/failure | `RUNNING` includes `claim_token` and UTC `claim_expires_at`; final values are prefixed by `SUCCESS` or `FAILED` |
| `Document directory` | success/failure with latest local artifact | absolute local path |
| `飞书云文档` | successful Draft | editable Feishu cloud document URL produced from the built Markdown |
| `基线文档` | successful Draft | frozen R0 cloud document used as backport comparison evidence |
| `idml_file` | successful Publish | uploaded designer handoff ZIP URL |
| `Document link_dd` | optional DingTalk writeback | DingTalk URL or empty string |
| `HTML_link` | successful `Web Publish` | deterministic Read the Docs manual URL |
| `data_sync` | queue build attempt | `refreshed`, `skipped`, or `failed` |
| `是否触发文档构建` | success | `已构建` |
| `是否立即构建` | success/failure | `false` |
| `是否强制刷新数据` | success/failure | `false` |

The RUNNING claim uses the existing `构建结果` field; it does not require a new
Base column. Its lease duration is two hours. Queue reads ignore a valid active
lease, while an expired or malformed legacy RUNNING value is eligible for a
new claim. Claim verification refetches without the configured pending view so
a view filter cannot hide the just-updated row.

GitHub workflow concurrency complements that table lease without adding Base
fields. Build Draft Package and print Publish share a per-Document_link record
group; their batch runs share one conservative batch group. Start Review uses
its own review-init record group. Web Publish serializes its complete aggregate
`Hello-Docs/publish` candidate update, `docs/publish/**`-only PR maintenance,
and `HTML_link` writeback under one global mutex. Every group queues rather
than cancels in-progress work, so workflow
scheduling cannot invalidate a live row lease.

Draft rows must produce Markdown and import both an editable `飞书云文档` and a
frozen `基线文档`. Import failure is a queue failure. Publish rows instead
deliver the designer handoff ZIP through `idml_file`; Web Publish writes
`HTML_link`. Any phase-specific remote artifact already obtained is preserved
in failure writeback.

The former `Document link` field is retired. Consumers must select the active
field by phase, or use the normalized agent contract
`delivery_kind` / `delivery_url` / `delivery_ready`. A blank retired field is
not evidence that an upload failed. The similarly named `Document_link`
table/view binding is historical infrastructure naming and remains in use.

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
- Phase2 content-source table changes must also update
  [`../../data/source_table_contracts/phase2_source_tables.json`](../../data/source_table_contracts/phase2_source_tables.json).
  Treat that file as the source-table structure index for Agent/Skill routing.
- Config validation should reject unsupported phase2 table keys before a live
  queue run can depend on them.
- Schema drift checks should run against fixed fixtures or dry-run payloads
  before depending on real Feishu network state.
- First offline gate: `python3 tools/schema_drift.py --payload tests/fixtures/schema_drift/passing_payload.json`
  validates required phase2 logical tables, required CSV headers, required queue
  writeback fields, and the source-table contract without contacting Feishu.
- Source-table contract gate: `python3 -m unittest tests.test_source_table_contract`
  validates the contract shape and checks it against source-intake, source-record
  index, and phase2 snapshot constants.
- External table names are product contracts. Prefer adding compatibility aliases
  before renaming a live field.
