---
name: manual-rewrite-with-tm
description: "Rewrite or translate full manuals and other structured markdown/doc-style content with translation-memory-first behavior. Use when the user asks to translate or rewrite documentation by memory rules such as: prefer translation-memory matches, keep unmatched source text in place and highlight it with ==...==, unify terminology, preserve markdown structure, or reuse a matched sentence pattern while replacing only parameters like wattage, voltage, model names, temperatures, units, ports, or counts."
---

# Manual Rewrite With TM

## Overview

Use this skill for manual-style content where wording must follow repo terminology and translation-memory patterns instead of free translation.

Preserve document structure, keep markdown stable, and apply deterministic rewrite rules before introducing any freer wording.

## Skill boundary in this repo

Use `bitable-translation-memory` for one-shot sentence translation, terminology lookup, or prompt-ready live TM context.

Use this skill for whole files, long sections, or structured Markdown/manual content where headings, lists, tables, images, and unmatched-source fallback must stay stable.

When both skills are relevant, load `bitable-translation-memory` first for live sentence-pair lookup and terminology grounding, then use this skill to execute the rewrite.

## Core workflow

1. Read the source content and preserve its structure.
2. Query translation memory for the target language using focused chunks, not one giant document query.
3. Apply the best exact match first.
4. If no exact match exists, check whether the sentence matches a memory pattern with only parameter changes.
5. If a safe pattern reuse exists, keep the translation-memory sentence skeleton and replace only the parameters.
6. If neither an exact match nor a safe pattern reuse exists, keep the original source text and highlight it with `==...==`.
7. Keep terminology consistent across the whole document.
8. Return the final content as markdown unless the user explicitly requests another format.

## Non-negotiable rules

- Prefer translation-memory wording over fresh translation.
- Preserve headings, tables, lists, emphasis, image links, and inline markup.
- Do not silently paraphrase unmatched text.
- When the rule is to preserve unmatched source text, keep the original source language and wrap it in `==...==`.
- Keep product names, model names, units, symbols, and parameter formatting consistent with the source unless memory clearly shows the localized form.
- For repeated terms, use one consistent target-language rendering everywhere in the file.

## Match priority

Apply matches in this order:

1. Exact sentence match from live translation memory
2. Exact term or phrase match from translation memory
3. Parameterized sentence-pattern reuse from translation memory
4. Source-text preservation with highlight

Do not skip to freer translation when rule 4 is required by the user.

## Parameterized sentence-pattern reuse

Treat a sentence as reusable from translation memory when the sentence structure and meaning are the same and only variable fields change.

Typical variable fields include:

- wattage, voltage, current, frequency, capacity, dimensions, temperature ranges
- model names and product names
- port names, button names, connector names
- counts, time durations, thresholds, SOC values
- standards or clause numbers

### Reuse rule

If a translation-memory sentence and the source sentence share the same semantic frame, reuse the translation-memory target sentence as the skeleton and replace only the variable fields.

### Examples

- `USB-C 100W Output` -> `USB-C 100-W-Ausgang`
- New source: `USB-C 140W Output`
- Output: `USB-C 140-W-Ausgang`

- Memory: `Charge Temperature: -20°C to 45°C`
- New source: `Charge Temperature: -10°C to 45°C`
- Reuse the translated sentence pattern and replace only the temperature parameter.

### Do not reuse by pattern when

- the safety meaning changes
- polarity, prohibition, or requirement changes
- a condition is added or removed
- the source sentence combines multiple clauses not present in memory
- parameter replacement would create ambiguity or ungrammatical output

In those cases, preserve the original source text with `==...==` when the user requested unmatched highlighting.

## Chunking guidance

For long manuals, work section by section.

Recommended chunk boundaries:

- title page / notices
- safety section
- symbols
- box contents
- product overview
- LCD / UI tables
- operations
- charging
- storage
- troubleshooting
- specifications
- warranty
- app setup

Prefer smaller focused translation-memory queries for paragraphs, warnings, tables, and labels instead of sending the whole document in one query.

## Markdown preservation rules

- Keep heading levels unchanged.
- Preserve table shape and cell boundaries.
- Preserve image markdown and URLs unchanged.
- Preserve inline bold, italic, code, superscripts, subscripts, and line breaks where possible.
- If only part of a table cell is unmatched, highlight only the unmatched source span when practical.
- Do not translate URLs, product codes, or standards unless memory explicitly shows a localized convention.

## Output rules

- Default output is the rewritten markdown only.
- Do not include process narration in the final content.
- If delivering the result in chat instead of a file, keep any short preface outside the markdown body.
- If writing a file, use a filename that clearly indicates the target language and memory-guided status.

## Using translation memory in this repo

This skill uses `bitable-translation-memory` as its live lookup layer. Query the live translation-memory source first via that existing repo skill.

Preferred query pattern:

`python3 .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "<text>" --source-lang en --target-lang <target-lang> --format prompt`

For larger work, run multiple focused queries on representative paragraphs, labels, or table rows.

## Batch markdown script

Use `scripts/rewrite_markdown_with_tm.py` when the task is a full markdown file or a long manual.

Example:

`python3 .agents/skills/manual-rewrite-with-tm/scripts/rewrite_markdown_with_tm.py input.md --target-lang de -o output.de.md`

Use bound Feishu terminology source first:

`python3 .agents/skills/manual-rewrite-with-tm/scripts/rewrite_markdown_with_tm.py input.md --target-lang de --use-feishu-term-source -o output.de.md`

Current script behavior:

- splits markdown into headings, text blocks, lists, tables, and images
- applies a term-priority table before paragraph translation
- splits normal text more finely by sentence to reduce whole-paragraph fallback highlighting
- queries translation memory block by block
- prefers exact sentence matches
- reuses translation-memory sentence skeletons when only parameters differ
- preserves unmatched source text and highlights it with `==...==`
- keeps markdown tables and image links in place

Term-priority table:

- bound terminology source record: `references/term-source.md`
- local fallback example file: `references/term-priority.example.tsv`
- format: tab-separated with `source` and `target` columns
- use it for button names, port names, warning labels, UI strings, and other repeated terms that should be normalized before sentence-level processing
- use `--use-feishu-term-source` to read the bound Feishu terminology table in a `master_spec`-style live-table flow
- when the live Feishu terminology source is reachable, treat it as the preferred term source; otherwise fall back to the local TSV table and cached term snapshot when available

Use this script as the default batch path, then spot-check the output for terminology consistency and any missed structural edge cases.

## Quality check before returning

Verify all of the following:

- memory matches were preferred where available
- unmatched source text is highlighted with `==...==`
- parameter-only differences reused the memory sentence pattern where safe
- markdown structure is intact
- terminology is consistent across repeated labels and headings
- no free translation was introduced for unmatched spans when the user asked to preserve source text
