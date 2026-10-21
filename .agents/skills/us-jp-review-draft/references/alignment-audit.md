# US ↔ JP content alignment audit

Answers "日规稿和美规内容对应吗" with per-unit evidence.

## 1. Units

- Download the US RTD HTML and run
  `extract_units.py us.html draft.html us_units.json jp_units.json --group-dir align/`.
- Add the US artwork labels that only exist inside images (front/right view
  port callouts) as extra US units with tag `image-label` (ids `USIMG01…`).
- Put US units that repeat elsewhere (the main spec table reprinted in an annex)
  into `align/duplicates.json`.
- Check the extraction before delegating: every visible text node of both pages
  must be inside some unit. A previous run missed JP safety-card headlines
  (`<strong>` in a `<div>`), box item names and LCD cells that hold Japanese plus
  an extra `<p>`, and US operation-panel `<div>` text — which made whole groups
  look "missing".

## 2. Per-group agents (parallel)

One agent per one or two groups (`g1_safety` … `g10_app`; add annex chapters to
a group or record them as out of scope). Brief each with exactly its input
files and this rubric:

```
For EVERY US unit decide one status:
- covered: the JP draft states the same content (wording may differ; JP template phrasing is fine; a green new-translation unit, English or first-pass Japanese, counts as covered).
- partial: covers the topic but drops or changes facts, conditions, numbers, presses or steps — say exactly what.
- missing: no counterpart.
- us_only: US-market/regulatory only (FCC, US address/phone, UL wording, EPO hardware the JP model lacks, 240V split-phase specifics). Use sparingly, explain.
Headings count as units. JP placeholders 【未入力】 where the US has a value → partial, note "JP 待填，美规值：…".
Then list every JP unit no US unit maps to as jp_only with a reason (do not list pure labels 注意/説明/警告).
Write <group>_result.json: {"group", "us":[{"id","status","jp_ids","note"}], "jp_only":[{"id","note"}]}
Every US id exactly once; notes in Simplified Chinese ≤60 chars; validate with python.
```

Give the JP model facts (ports, voltages, EPO yes/no, UPS ms, parallel) in the brief.

## 3. Aggregate

- Cross-group links and later fixes go to `align/overrides.json`
  (`{"US597": ["covered", ["JP064"], "附录装箱清单对应同梱品"]}`); typical cases:
  an annex package list that matches 同梱品, labels that are present inside the
  screenshot figures, sections added in a later draft version.
- `aggregate_align.py align/ us-jp-content-alignment.xlsx alignment.json`
  (exit 1 on missing/extra ids). Report: covered / partial / missing / us_only,
  coverage over applicable units, jp_only count, missing grouped by theme
  (annexes, 200V input, storage, safety clauses …), typical partial causes.
- Ship the xlsx (汇总 / 美规逐条对照 / 日规独有) and a short
  `us-jp-content-alignment.zh.md`; put the chapter table in the review appendix.
