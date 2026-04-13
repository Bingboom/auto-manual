---
name: bitable-translation-memory
description: Query Feishu/Lark Base phase2 multilingual snapshot content as translation memory for OpenClaw or Codex translation tasks. Use when translating manual content and you want terminology grounded in Spec_Master, spec_titles, Spec_Notes, Spec_Footnotes, or symbols_blocks instead of freeform wording.
---

# Bitable Translation Memory

Use this skill when the task is "translate with repo terminology", not generic free translation.
The preferred source is the dedicated Feishu sentence-pair table `Translation_Memory`, and the repo `data/phase2` snapshot is the fallback context layer.

## Default workflow

1. Query the live sentence-pair table first:
   `python .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "<phrase>" --source-lang en --target-lang <target-lang> --limit 8`
2. For OpenClaw prompt construction, prefer prompt output:
   `python .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "<paragraph>" --source-lang en --target-lang <target-lang> --format prompt`
   The script auto-splits multi-sentence input unless `--no-split` is passed.
3. If the live table does not contain enough context, or the task needs model/page/row metadata, query the repo snapshot:
   `python build.py translation-memory --config <config> --model <model> --region <region> --query-text "<phrase>" --lang <target-lang> --limit 8`
4. If the user asks for the latest Base content for the repo snapshot layer, or `data/phase2` may be stale, refresh it first:
   `python build.py sync-data --config <config> --data-root data/phase2`
5. Narrow snapshot matches with one or more of:
   `--table spec-master`
   `--page operation_guide`
   `--section "OUTPUT PORTS"`
   `--row-key usb_c_high_power_port`
6. Feed only the compact result into OpenClaw. Do not paste raw table dumps or CSV rows unless the user explicitly asks for them.

## Output rules

- Prefer exact multilingual matches over paraphrases.
- If the preferred target language field is blank, say that the snapshot has no direct translation and fall back to the source-language wording instead of inventing a new term.
- Treat the live sentence-pair table as the highest-priority wording memory because it is purpose-built for aligned translation pairs.
- Keep row/page metadata when repeated terms need disambiguation.
- For larger translation jobs, run multiple focused queries instead of one huge catch-all search.
- Use `--json` when another tool or prompt-construction step needs structured output.

## Good queries

- Live sentence-pair lookup:
  `python .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "Always follow these basic precautions when using this product." --source-lang en --target-lang fr --limit 5`
- OpenClaw-ready paragraph prompt:
  `python .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "Always follow these basic precautions when using this product. Read all the instructions before using the product." --source-lang en --target-lang fr --format prompt`
- Exact term lookup:
  `python build.py translation-memory --config config.us.yaml --model JE-1000F --region US --query-text "USB-C 100W Port" --lang fr --table spec-master`
- Section context:
  `python build.py translation-memory --config config.us.yaml --model JE-1000F --region US --query-text "charging power" --lang es --page operation_guide --section "OUTPUT PORTS"`
- Symbol copy:
  `python build.py translation-memory --config config.us.yaml --model JE-1000F --region US --query-text "Warning and Caution Symbols" --lang fr --table symbols-blocks`
