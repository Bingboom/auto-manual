---
name: bilingual-tm-maintenance
description: "Maintain live Feishu/Lark Translation_Memory from bilingual source/target copy: update existing English-linked rows first, create missing pairs when requested, append the target-language maintenance log, audit the bilingual alignment, and append the target-language audit log. Use for requests like 给双语文案录入记忆库, 维护对应语言log, 校对双语, or 写校验log字段."
---

# Bilingual TM Maintenance

Use this skill when the user provides bilingual manual copy and wants it maintained in the live `Translation_Memory` table, with both maintenance logs and bilingual audit logs written back.

This is an evidence-first data maintenance workflow, not a free-translation workflow.

## Source Of Truth

- **Canonical write base (G4 convergence, 2026-07-02):** the Base that
  `$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN` names. Resolve the table **by name**
  inside it (`Translation_Memory` for sentence pairs, `Terms` for terminology):
  `lark-cli base +table-list --base-token "$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN"`.
- **Read-only archive (do NOT write):** the old A/wiki mirror — wiki node
  `X3O8wCpXPifqGKkP2sYccyxznQb`, Base `LUIcbxeKdaCY2rsEHwCcnVQSnUe`, table
  `tbl6gKPJPTvOcTWv`. It is kept for history only; every write goes to the
  canonical base above.

Before writing, run `lark-cli base +table-get` against the canonical base and
use the returned field IDs. Do not rely on guessed field names when writing.

## Language Field Pattern

The source field is usually `en`. The target field is the requested language field, such as `fr`, `es`, `de`, `it`, `uk`, `jp`, `ko`, or `pt-BR`. (Both tables use `ko` for Korean and `uk` for Ukrainian as of the 2026-06-01 column standardization; Japanese stays `jp` to match the phase2 build convention.)

For the target language, also locate:

- Maintenance log field: `<language>维护Log (AI)`
- Audit log field: `<language>校验Log (AI)` or the exact localized variant returned by `+table-get`

Use exact field IDs from `+table-get` in write payloads.

## Maintenance Workflow

1. Parse the bilingual material into explicit source-target pairs.
2. Keep only pairs where both sides are actually present in the provided source material.
3. If the source English already exists in `Translation_Memory`, update that row's target-language field in place.
4. If the source English does not exist, create a new record only when the user asked to add missing pairs.
5. Append the target-language maintenance log without overwriting existing log text.
6. Read the written records back from Base and confirm the target value and maintenance log are stored correctly.
7. Audit the bilingual pair against the provided source material.
8. Append the target-language audit log without overwriting existing audit log text.
9. Read the audited records back and confirm the audit log is stored correctly.

## Non-Negotiable Rules

- Do not maintain inferred translations that are not present in the target-language source material.
- Do not create generic header pairs just because they are useful if the target source does not explicitly contain that header.
- If the source file has `Symbol | Meaning` but the target file omits the corresponding target headers, do not create `Symbol -> <target>` or `Meaning -> <target>`.
- Prefer updating existing English-linked rows over creating duplicates.
- If a row exists and the target field is already populated with different text, treat the provided bilingual source as authoritative only when the user clearly asked to maintain from that source. Otherwise, report the conflict.
- Skip parameter-related rows when the user asks not to maintain parameter-related corpus.
- Preserve source-authoritative values when the user allows parameter-pattern reuse.
- Never use `record-list` display output alone as proof of Unicode write success. Always verify with `record-get` or projected JSON output.

## Matching Rules

Use a conservative match:

- Exact normalized English match: update the existing row.
- Markdown-only differences, such as bullets, bold, table cell boundaries, or line breaks: acceptable if the text is otherwise the same.
- Parameter differences: only maintain when the user allows parameter rows or parameter-pattern reuse.
- Target text missing from the provided target-language source: do not write it.
- Target text present but visibly dirty, such as stray letters, mojibake, or broken spacing: write an audit log as `review suggested`; fix only when the user asks for correction or the source evidence is unambiguous.

## Korean Number Formatting Rule

When maintaining the Korean (`ko`) target, apply thousands separators to ordinary numeric values: use an ASCII comma every three digits from the right, such as `1,000`, `1,024 Wh`, `1,800 W`, and `3,600 W`. Preserve decimal notation, units, signs, and the established spacing around units.

Do not insert separators into name-like or identifier-like digit strings, including model and product names, part numbers, error codes, serial/SKU/firmware identifiers, URLs, and dates or years. Examples that remain unchanged are `JE-1000H`, `Explorer 1000 Plus`, `Jackery Battery Pack 2000`, `F0`, and `2026`. In mixed text, normalize only eligible numeric quantities; never alter the digits inside an exempt identifier.

This is a Korean target-format normalization rule, not permission to invent a translation. Apply it when the bilingual source clearly identifies the same numeric value and the user has requested Korean corpus normalization. If an existing target differs in a way that could change the value or identifier, preserve it and classify the row as `review suggested` instead of silently rewriting it. Do not retroactively rewrite existing rows unless the user explicitly requests a corpus-wide cleanup.

## Log Rules

Use short, ASCII log lines to avoid Windows encoding issues in log fields.

Maintenance log examples:

- `2026-05-22 KR maintenance: Explorer 1500 Ultra manual QC passed`
- `2026-05-22 pt-BR maintenance: JE1000F manual QC passed`

Audit log examples:

- `2026-05-22 KR audit: source-aligned QC passed`
- `2026-05-22 KR audit: review suggested (target source typo near Output Power: 1000W)`

Append logs:

- If the field is empty, write the new line.
- If the field already has content, append the new line after a newline.
- If the exact log line already exists, do not duplicate it.

## Windows-Safe Base Writes

For localized text, avoid inline JSON in PowerShell.

Preferred write pattern:

1. Create a short repo-local JSON payload file.
2. Pass it with `--json @./<payload>.json`.
3. Keep the path relative to the repo root.
4. If typing non-ASCII literals inside a PowerShell here-string, use Unicode escapes or read the text from a UTF-8 source file inside Python before writing the JSON payload.
5. Immediately read the record back.

Do not trust dry-run output or CLI echo text as proof that Unicode stored correctly.

## Read/Write Command Shape

Field discovery:

```powershell
lark-cli base +table-get --base-token "$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN" --table-id <resolved Translation_Memory table id>
```

Projected read:

```powershell
lark-cli base +record-get --base-token "$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN" --table-id <resolved Translation_Memory table id> --record-id <record_id> --field-id <en_field_id> --field-id <target_field_id> --field-id <maintenance_log_field_id> --field-id <audit_log_field_id> --format json
```

Write one record:

```powershell
lark-cli base +record-upsert --base-token "$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN" --table-id <resolved Translation_Memory table id> --record-id <record_id> --json @./.tmp_tm_payload.json
```

Create one record:

```powershell
lark-cli base +record-upsert --base-token "$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN" --table-id <resolved Translation_Memory table id> --json @./.tmp_tm_payload.json
```

## Audit Outcome

After auditing, classify each touched row as one of:

- `passed`: source and target are aligned.
- `review suggested`: source-target alignment needs human review, the target source has a typo, or a source-specific parameter difference is unclear.
- `skipped`: pair was not maintained because one side was missing, parameter-related content was excluded, or the target text was inferred rather than source-backed.

Report counts in the final answer:

- records created
- existing records updated
- records skipped
- audit passed
- audit review suggested

If any row is `review suggested`, include the record ID and the English source so the user can inspect it quickly.
