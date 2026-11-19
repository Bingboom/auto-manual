# lark-cli recipes and traps

Verified against lark-cli 1.0.78 (`/opt/homebrew/bin/lark-cli`). Base
subcommands carry a `+` prefix (`base +record-list`); the base is addressed
with `--base-token` (the old `--app-token` is gone). If a shape here fails,
check `lark-cli base --help` first — CLI upgrades have renamed commands before
(see "Version history").

## Identity

- The maintained business-plane lane is explicit: use `--profile prod --as bot`
  for both reads and approved writes (`FEISHU_APP_ID`/`FEISHU_APP_SECRET` are
  external; queue-side code uses `FEISHU_PHASE2_IDENTITY=bot`). Do not rely on
  the CLI's default profile or default user identity. A 91403 error on write
  usually means wrong identity/permission, not a payload bug.
- Secrets arrive via clipboard (`pbpaste`), never chat; mask them in any echo.

## Reading

```bash
lark-cli --profile prod base +field-list --as bot --base-token <BASE> --table-id <TBL> --limit 200
lark-cli --profile prod base +record-list --as bot --base-token <BASE> --table-id <TBL> \
  --format json [--filter-json '{"logic":"and","conditions":[["document_key","is","JE-1000F_EU"]]}'] \
  [--limit 200 --offset <n>]
```

- JSON result: `data.data` = rows as **positional arrays** aligned to
  `data.fields`, plus a parallel `data.record_id_list`. Default markdown output
  includes a `_record_id` column.
- **`record-list` caps at 200 rows** — an unfiltered read of a big table
  silently truncates, and a delete/verify built on a truncated read misses
  rows. Filter by key or paginate with `--limit 200 --offset`.
- `+record-get` also returns positional arrays (`data.fields` +
  `data.data[0]`), NOT a `record.fields` map.

## Writing

```bash
# CREATE (batch): one field map per record; maximum 200 records per call
lark-cli --profile prod base +record-batch-create --as bot \
  --base-token <BASE> --table-id <TBL> \
  --json '{"create_records":[{"Name":"Task A","Status":"Todo"}]}'

# For generated payloads, @file must be cwd-relative. @- is not stdin here.
lark-cli --profile prod base +record-batch-create --as bot \
  --base-token <BASE> --table-id <TBL> \
  --json @reports/source_intake/<run>/spec_intake_staging_payload.json

# UPDATE (batch): same patch applied to every id; null clears a cell
lark-cli --profile prod base +record-batch-update --as bot --base-token <BASE> --table-id <TBL> \
  --json '{"record_id_list":["recXXX","recYYY"],"patch":{"是否触发文档构建":["Y"]}}'

# UPDATE/CREATE (single): +record-upsert — there is NO +record-update
#   with --record-id → update; without → create. Payload is a BARE field map,
#   not wrapped in {"fields": ...}.
lark-cli --profile prod base +record-upsert --as bot --base-token <BASE> --table-id <TBL> \
  --record-id recXXX --json '{"Value_source":"..."}'

# DELETE: requires --yes
lark-cli --profile prod base +record-delete --as bot --base-token <BASE> --table-id <TBL> --record-id recXXX --yes
```

## Field-type traps (each cost a real round)

| Field type | Trap | What to do |
| --- | --- | --- |
| Formula (`document_key`, `source_row_key`, …) | not writable; recompute from inputs | write the inputs (links, order fields) and let it recompute |
| Lookup (`Row_key`, `Slot_key`) | not writable | set the corresponding **link** field (`Row_key_link`, `Slot_key_link`, `Document_key_link`) — cloning a sibling row that already carries links is the reliable CREATE path |
| Record-link (e.g. `Row_label_footnote_refs`) | write returns **ok but does not persist** (read-back stays null); clearing to null persists | verify by read-back; workaround = literal marker text in the value column, or set the link in the Feishu UI |
| Select | value must be an existing **option name** (else `not_found` + option list) | pass the option name; add options first if new |
| Multi-select | adding a new option = `+field-update` **full PUT** of the options array (carry existing options' hue/lightness or they're clobbered); duplicate same-name options block the update | dedupe by full PUT (Feishu merges by name; row references survive — verify after) then add the new option |
| Attachment | upload is `base +record-upload-attachment` (base group, ≥1.0.69) with `--field-id`; `--file` must be a **cwd-relative path** | upload, then read back and confirm the file token is non-empty |
| Text vs select case | sibling tables differ (footnotes `type` vs notes `Type`; Troubleshooting `Region` is plain text) | check `+field-list` before writing |

## Building tables, forms, views and dashboards

Verified 2026-11 on lark-cli 1.0.49 while building a new base from scratch.

**Destructive: removing a form question deletes the field.** `base
+form-questions-delete` drops the underlying **table field and all its
values**, not just the question. Removing a question in the new-style form UI
does the same (confirmed with an empty field). There is no "hide question"
call: `+form-questions-update` only changes `title` / `description` /
`required`. To keep an internal field out of a form, either create that field
**after** the form (fields added later do not join existing forms) or leave the
question and set its description to 「提交时留空」. Never use either delete path
on a field that holds data.

| Object | Shape / trap |
| --- | --- |
| Table | `+table-create --name <n> --fields '[...]'`; the first field becomes the primary field |
| Two-way link | `+field-create --json '{"name":"竞品","type":"link","link_table":"tbl…","bidirectional":true,"bidirectional_link_field_name":"文档"}'`; record values are `["rec…"]` and persisted on read-back in a fresh base |
| Auto fields | `{"type":"created_by"}`, `{"type":"created_at","style":{"format":"yyyy/MM/dd HH:mm"}}` |
| Select default | `"default_value":"<option>"` on `+field-create` sticks |
| URL text | `{"type":"text","style":{"type":"url"}}`; read-back renders the value as `[url](url)` |
| Form | `+form-create` adds **every** existing field as a question. Link fields cannot be added to a form through the API, and the new-style form UI cannot add an existing link field either |
| View | `+view-create` then `+view-set-filter` `{"logic":"or","conditions":[["状态","==","待审核"],["状态","empty"]]}`, `+view-set-sort`, `+view-set-group`; a new kanban groups by an arbitrary field until you set the group |
| Dashboard block | `data_config` SSOT is `dashboard-block-data-config.md` in the lark-base skill (not bundled with the CLI): counts use `count_all`, not a `COUNTA` rollup. Two `group_by` entries both in `enumerated` mode silently drop records carrying several values; split only one of them |
| Dashboard text | line breaks are stripped server-side, so keep text blocks to one line |
| Relative dates | UI-made cards store `"value":["Today"]` / `["CurrentWeek"]`; build relative-date cards in the UI rather than with a fixed timestamp that goes stale |
| Computed data | `+dashboard-block-get-data` may return `empty chart data` right after creation; retry after ~20 s before debugging |
| Table/view embed | the UI table component stores a hidden view (`<view> 副本`); its own filter is not readable through `+dashboard-block-get` |

Cloud containers: `FEISHU_APP_ID` / `FEISHU_APP_SECRET` in the environment are
not read automatically. Create the profile without echoing the secret:
`printf '%s' "$FEISHU_APP_SECRET" | lark-cli config init --app-id "$FEISHU_APP_ID" --app-secret-stdin --brand feishu --name prod`.

## Cloud docs / wiki (the shapes other skills borrow)

```bash
lark-cli wiki +node-get  --node-token <wiki-url-or-token>     # → obj_token of the doc
lark-cli wiki +node-copy ...                                  # baseline re-snapshot
lark-cli drive +export --token <obj_token> --doc-type docx \
  --file-extension markdown --output-dir <cwd-relative dir>   # doc → markdown export
```

## Version history (why remembered shapes rot)

- **1.0.51 → 1.0.69**: base subcommands gained the `+` prefix;
  `--app-token` → `--base-token`; `record-update` removed (use
  `+record-batch-update` / `+record-upsert`); `+record-upload-attachment`
  added; `record-list` `--limit` hard-capped at 200.
- **1.0.78**: `+record-batch-create` accepts
  `{"create_records":[{field:value}, ...]}`; the earlier `fields + rows`
  recipe is invalid. Generated `--json @file` inputs must use a cwd-relative
  path; `@-` is not a supported stdin shortcut.
- When the CLI updates, re-verify one read + one write shape before a batch
  job, and update this file in the same change.
