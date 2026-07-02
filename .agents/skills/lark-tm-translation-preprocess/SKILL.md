---
name: lark-tm-translation-preprocess
description: Preprocess Feishu/Lark DOCX or Wiki manual links with live Translation_Memory sentence pairs, configurable source and target languages, parameter-fuzzy matching, yellow-highlighted replacements, and upload back beside the source file. Use when a Feishu natural-language/OpenClaw request asks to "预处理", "翻译预处理", "用记忆库处理", "基于源语言结合语料库", "上传到原路径/同路径", or to turn a Lark/Feishu document link into a target-language TM-preprocessed DOCX for language pairs such as en→ko, en→fr, en→es, fr→en, etc.
---

# Lark TM Translation Preprocess

Use this skill for the repeatable Feishu/OpenClaw workflow:

1. Accept a Feishu/Lark Wiki, file, doc, or docx URL.
2. Download or export the source as `.docx`.
3. Read live `Translation_Memory` sentence pairs.
4. Replace only source text that has a safe exact, parameter-only, or high-confidence fuzzy match in the requested target language.
5. Highlight every replacement with yellow by default.
6. **Re-open the packed DOCX and verify the translation actually landed** (open-state gate — see Verification).
7. Upload to the same Wiki parent path as the source — only when verification passed.
8. Return the uploaded document link.

This is a translation preprocessing pass, not a full free-translation pass. Unmatched source text stays unchanged unless the user explicitly asks for a human/LLM completion step after preprocessing.

> **Never hand-edit the `.docx` zip.** Always run the script below. It rebuilds the archive
> cleanly (every part written exactly once, so a duplicate `word/document.xml` cannot
> happen) and self-verifies before uploading. Appending to / patching the zip in place is
> exactly what produced the "looks translated but the opened file is still the original"
> failure — do not do it. **Done = the script returned `ok: true` AND `verified: true`.**
> Treat `verified: false` (or `ok: false`) as a hard failure: report it, do not upload, do
> not tell the user it is done.

## Dependencies

It shells out to `lark-cli` directly (there is no `lark-drive` / `lark-wiki` / `lark-shared` skill in this repo) and reads the TM Base through the `bitable-translation-memory` helper:

- `lark-cli` (must be on `PATH`): resolves the URL (`drive +inspect`), downloads/exports the source (`drive +download` / `docx +export`), reads the source node (`wiki +node-get`), and uploads the result (`drive +upload`). Reads use `--as bot`. On a permission/scope error, surface it and ask the operator to grant the bot read access to the source node and write access to its parent.
- live `Translation_Memory` Base: loaded via the `bitable-translation-memory` helper (`tools/translation_memory.py` + cached live table). See `bitable-translation-memory/SKILL.md` for sentence-pair and terminology rules.

Optional follow-ons (not part of the preprocessing pass):

- `manual-rewrite-with-tm`: free/LLM-translate the text this pass leaves unmatched.
- `docx-highlight-changes`: recolour or add highlight spans in the produced DOCX.

## Language Handling

Always identify or ask for:

- `source-lang`: the language currently present in the source document.
- `target-lang`: the language to preprocess into.

The script accepts common codes and aliases: `en`, `fr`, `es`, `de`, `it`, `uk`, `ja`/`jp`, `ko`/`kr`, `pt-BR`, `zh`/`cn`.

Do not hardcode English or Korean. Any source/target combination is valid if both columns exist in live `Translation_Memory` and the target cell is non-empty for a matched row.

## Main Script

> **Uploads by default.** A normal run uploads the processed DOCX back beside the source on Feishu. For a local, no-side-effect trial, pass `--no-upload` (add `--input-docx <local.docx>` to skip the download too).

Run from the repo root:

```bash
python3 .agents/skills/lark-tm-translation-preprocess/scripts/preprocess_lark_docx_with_tm.py \
  --url "<Feishu or Lark URL>" \
  --source-lang en \
  --target-lang ko \
  --collapse-leading-multilingual-notice \
  --json
```

Useful variants:

```bash
# English source to French target, default yellow highlighting, upload beside source
python3 .agents/skills/lark-tm-translation-preprocess/scripts/preprocess_lark_docx_with_tm.py \
  --url "<Feishu URL>" --source-lang en --target-lang fr --json

# Local dry-run without uploading
python3 .agents/skills/lark-tm-translation-preprocess/scripts/preprocess_lark_docx_with_tm.py \
  --input-docx ./sample.docx --source-lang en --target-lang es --no-upload --json

# Upload to a known Drive folder when the source URL has no resolvable Wiki parent
python3 .agents/skills/lark-tm-translation-preprocess/scripts/preprocess_lark_docx_with_tm.py \
  --url "<Feishu file URL>" --source-lang en --target-lang de --folder-token "<folder_token>" --json
```

The JSON result includes:

- `output_docx`: local processed file.
- `report_json`: replacement report with match source, score, and row key.
- `change_count`: replacement count.
- `units_total` / `units_matched` / `hit_rate`: sentence-level TM hit-rate
  counters for this run.
- `hit_rate_ledger`: where the run was appended in the cumulative hit-rate
  ledger (`reports/tm_hit_rate/ledger.jsonl`, via `tools/tm_hit_rate.py`), or
  the append-failure note. The ledger append is best-effort and never fails
  the run; query the trend with `python3 -m tools.tm_hit_rate stats`.
- `highlighted_runs`: highlighted run count in `word/document.xml`.
- `upload.url`: Feishu uploaded file URL when upload succeeds.
- `source_wiki_node.parent_node_token`: evidence for same-path upload.

## Leading Multilingual Notice

Use `--collapse-leading-multilingual-notice` when the source starts with a multi-language `IMPORTANT` / `IMPORTANTE` notice and the user says only one target language should remain.

Behavior:

- Keep the first source-language notice block.
- Delete later leading language blocks before `IMPORTANT SAFETY INFORMATION`.
- Localize the leading language label and `IMPORTANT` heading when possible.
- Then run normal TM preprocessing over the kept block.

If the document uses a different first heading after the notice, pass:

```bash
--front-matter-end-text "<first heading after the multilingual notice>"
```

## Matching Rules

The preprocessing script applies matches in this order:

1. Exact source-language paragraph/cell match.
2. Parameter-only match after normalizing model names, wattage, voltage, time, counts, URLs, and similar variables.
3. High-confidence fuzzy match with token coverage and sequence similarity.
4. Sentence-unit split matching for multi-sentence paragraphs.

For parameter-only differences, reuse the target sentence skeleton and replace only variable fields. Do not use this process to introduce a free translation for unmatched text.

## Verification

The script runs an **open-state acceptance gate** itself (`verify_output`): after repacking and *before* uploading, it re-opens the packed DOCX and checks that

- the archive is a sound zip with **exactly one** `word/document.xml` and a `[Content_Types].xml`,
- when `change_count > 0`, the reopened body actually carries highlighted runs, and
- a sample of the written target strings is genuinely present in the reopened body.

If any check fails the script sets `verified: false` / `ok: false`, **skips the upload**, and exits non-zero — so a write-back that did not land can never be uploaded or called done. The specific failures are listed under `verification.problems`.

Before replying that a task is done, confirm from the script's JSON:

1. `ok: true` **and** `verified: true` (with `verification.problems` empty).
2. `change_count > 0` unless the user only wanted a dry run or audit.
3. If uploaded, the uploaded file's Wiki parent equals the source parent:

   ```bash
   lark-cli wiki +node-get --node-token <uploaded_file_token> --obj-type file --as user --json
   ```

   Compare `parent_node_token` to the source node's `parent_node_token`.

4. Optional visual QA (needs a renderer): if LibreOffice / `soffice` is available, convert the DOCX to PDF/images and eyeball representative pages. Skip when no renderer is installed — a confidence check, not a gate.

If `verified: false`, do **not** upload and do **not** report success — surface `verification.problems` and fix the cause (most often a bad write-back or zero matches).

## Natural-Language Trigger Examples

These should map to this skill:

- `把这个飞书文档按英韩记忆库预处理，黄色高亮，上传同路径`
- `这个源语言是英文，目标法语，用语料库匹配翻译，处理完发我链接`
- `源语言 fr，目标 es，参数可以模糊匹配，上传到原路径`
- `预处理这个 wiki 文档，只保留目标语言的 IMPORTANTE 开头部分`

The OpenClaw/Feishu adapter should extract the URL and language pair from the message, then invoke this skill's script with the resolved arguments.
