# lark-cli recipes and traps

Verified against lark-cli ≥ 1.0.69 (`/opt/homebrew/bin/lark-cli`). Base
subcommands carry a `+` prefix (`base +record-list`); the base is addressed
with `--base-token` (the old `--app-token` is gone). If a shape here fails,
check `lark-cli base --help` first — CLI upgrades have renamed commands before
(see "Version history").

## Identity

- Default identity is **user**; source-table writes run as **bot** (`--as bot`,
  with `FEISHU_APP_ID`/`FEISHU_APP_SECRET` set; queue-side code uses
  `FEISHU_PHASE2_IDENTITY=bot`). Some bases are read-only to one identity
  (a 91403 error on write usually means wrong identity/permission, not a bug).
- Secrets arrive via clipboard (`pbpaste`), never chat; mask them in any echo.

## Reading

```bash
lark-cli base +field-list --base-token <BASE> --table-id <TBL>          # fields in data.fields
lark-cli base +record-list --base-token <BASE> --table-id <TBL> \
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
# CREATE (batch): fields + rows-of-arrays — not records/fields objects
lark-cli base +record-batch-create --base-token <BASE> --table-id <TBL> \
  --json '{"fields":["Row_key","Value_source"],"rows":[["ac_output","230 V~ 50 Hz, ..."]]}'

# UPDATE (batch): same patch applied to every id; null clears a cell
lark-cli base +record-batch-update --base-token <BASE> --table-id <TBL> \
  --json '{"record_id_list":["recXXX","recYYY"],"patch":{"是否触发文档构建":["Y"]}}'

# UPDATE/CREATE (single): +record-upsert — there is NO +record-update
#   with --record-id → update; without → create. Payload is a BARE field map,
#   not wrapped in {"fields": ...}.
lark-cli base +record-upsert --base-token <BASE> --table-id <TBL> \
  --record-id recXXX --json '{"Value_source":"..."}'

# DELETE: requires --yes
lark-cli base +record-delete --base-token <BASE> --table-id <TBL> --record-id recXXX --yes
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
- When the CLI updates, re-verify one read + one write shape before a batch
  job, and update this file in the same change.
