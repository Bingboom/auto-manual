---
name: bitable-translation-memory
description: Query Feishu/Lark Base phase2 multilingual snapshot content as translation memory for OpenClaw or Codex translation tasks. Use for direct sentence or paragraph translation asks, terminology lookup, and as the lookup layer beneath `manual-rewrite-with-tm` batch rewrite jobs in this repo, including plain requests like "把这句翻成法语" even when the user does not explicitly mention terminology or Translation_Memory.
---

# Bitable Translation Memory

Use this skill when the task is "translate with repo terminology", not generic free translation.
The preferred source is the dedicated Feishu sentence-pair table `Translation_Memory`, and the repo `data/phase2` snapshot is the fallback context layer.

## Skill boundary in this repo

Use this skill when the task is a one-shot translation reply, a sentence or paragraph lookup, or terminology grounding for another tool.

If the user wants a whole Markdown page or manual rewritten, wants headings and tables preserved, wants unmatched source text kept in `==...==`, or wants translation-memory sentence patterns reused across a structured document, load `manual-rewrite-with-tm` after this skill and let that skill own the output document.

## Default workflow

1. Query the live sentence-pair table first:
   `python3 .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "<phrase>" --source-lang en --target-lang <target-lang> --limit 8`
2. For OpenClaw prompt construction, prefer prompt output:
   `python3 .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "<paragraph>" --source-lang en --target-lang <target-lang> --format prompt`
   The script auto-splits multi-sentence input unless `--no-split` is passed.
   Run the command in the foreground and wait for completion. Do not background it and do not use `process poll` for a normal lookup; this query is expected to finish quickly.
   The script keeps a short local cache of the live table to speed up repeated chat lookups. Use `--no-cache` or `--cache-ttl-seconds 0` only when you need a forced refresh.
3. If the live table does not contain enough context, or the task needs model/page/row metadata, query the repo snapshot:
   `python3 build.py translation-memory --config <config> --model <model> --region <region> --query-text "<phrase>" --lang <target-lang> --limit 8`
4. If the user asks for the latest Base content for the repo snapshot layer, or `data/phase2` may be stale, refresh it first:
   `python3 build.py sync-data --config <config> --data-root data/phase2`
5. Narrow snapshot matches with one or more of:
   `--table spec-master`
   `--page operation_guide`
   `--section "OUTPUT PORTS"`
   `--row-key usb_c_high_power_port`
6. Feed only the compact result into OpenClaw. Do not paste raw table dumps or CSV rows unless the user explicitly asks for them.

## Output rules

- Prefer exact multilingual matches over paraphrases.
- When a live `Translation_Memory` row directly matches the requested sentence, return that matched target-language sentence as the default final translation.
- Do not produce a freer re-translation when a direct sentence-pair match already exists, unless the user explicitly asks for adaptation, polishing, or alternate tone.
- For a normal one-shot sentence translation, do not narrate the lookup, do not send interim progress text, and do not split the answer into multiple messages.
- If the preferred target language field is blank, say that the snapshot has no direct translation and fall back to the source-language wording instead of inventing a new term.
- Treat the live sentence-pair table as the highest-priority wording memory because it is purpose-built for aligned translation pairs.
- Keep row/page metadata when repeated terms need disambiguation.
- For larger translation jobs, run multiple focused queries instead of one huge catch-all search.
- If the task expands into a full Markdown or manual rewrite, use this skill as the lookup layer and hand the document rewrite flow to `manual-rewrite-with-tm`.
- Use `--json` when another tool or prompt-construction step needs structured output.

## Good queries

- Live sentence-pair lookup:
  `python3 .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "Always follow these basic precautions when using this product." --source-lang en --target-lang fr --limit 5`
- OpenClaw-ready paragraph prompt:
  `python3 .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "Always follow these basic precautions when using this product. Read all the instructions before using the product." --source-lang en --target-lang fr --format prompt`
- Exact term lookup:
  `python3 build.py translation-memory --config config.us.yaml --model JE-1000F --region US --query-text "USB-C 100W Port" --lang fr --table spec-master`
- Section context:
  `python3 build.py translation-memory --config config.us.yaml --model JE-1000F --region US --query-text "charging power" --lang es --page operation_guide --section "OUTPUT PORTS"`
- Symbol copy:
  `python3 build.py translation-memory --config config.us.yaml --model JE-1000F --region US --query-text "Warning and Caution Symbols" --lang fr --table symbols-blocks`
