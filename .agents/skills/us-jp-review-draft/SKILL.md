---
name: us-jp-review-draft
description: "Produce or continue a JP (日规) review draft (审核稿/审阅稿) of a manual whose source is the published US English manual: JP template frame, existing Japanese reused wherever the corpus has it, missing copy kept in English (green) and counted as new translation, JP spec-sheet values filled, US↔JP content alignment audit, JP web-manual styling, versioned zip and optional Feishu wiki upload. Use for 基于美规输出日规说明书, 日规审核稿/审阅稿, 继续改日规草稿 (Feishu wiki zip), 统计需新增翻译量, 日规与美规内容是否对应. US→JP only; not for building a pipeline review branch (Start Review) or back-porting reviewer edits."
---

# US → JP Review Draft

Turn a published US English manual into a Japan-market review draft that
reviewers can read in one HTML page: Japanese from the existing corpus in black,
still-missing copy in green English (the translation workload), Chinese glosses
in blue, pending values in magenta, review notes in orange. Proven on
JHP-3600C (v0.14 → v0.19); see `references/jhp3600c-case.md`.

This is an off-pipeline review artifact. It never writes `docs/templates`,
`docs/_review`, `data/phase2` or live source tables, and it is not committed to
the repo. The only live write is the operator-requested Feishu wiki upload.

## Inputs (ask for what is missing)

- US source: the RTD page (e.g. `https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/<MODEL>/US/en/md/...html`)
  or its frozen package under `data/manual_sources/<MODEL>/US/`.
- Existing draft, if continuing: a Feishu wiki link to the draft zip.
- JP spec sheet (规格书, often screenshots): ratings, ports, box contents, options, notes.
- Operator decisions as they come up: which US chapters to add (connections,
  200V, annexes), product naming, color rules. Record each one in the draft's
  review appendix and in `review.zh.md`.

## Workflow

1. **Load the draft.** Resolve the wiki node and download the zip into an empty
   scratch directory (`scripts/feishu_api.py node|download`; lark-cli may be
   unconfigured, the API helper only needs `FEISHU_APP_ID/SECRET`). Read the
   zip's `README.md`/`review.zh.md`, outline the HTML headings, render it once.
2. **Build the corpus** (read-only), in this order — see `references/corpus-and-color-rules.md`:
   JP RST templates → `Translation_Memory` terms + sentence pairs → live
   规格参数明细 / LCD tables → every published JP web manual (`scripts/jp_corpus.py pool`).
   Sibling JP models with the same hardware (e.g. JE-5000A for 100V/200V
   L14-30R/6-20 ports) are the best source for port and spec wording.
3. **Fill the JP spec sheet.** Labels and sentence frames from sibling JP
   rows; values only from the JP spec sheet. US values never enter Japanese
   text — they go into the orange review note. Flag spec-vs-US conflicts
   (weight, inverter vs rated output, port current) in the appendix.
4. **Replace with Japanese wherever it exists.** Reuse a corpus sentence when
   it says the same thing with only a value/name/port slot changed. Otherwise
   keep the US English in green with `data-needs-translation` and, if a close
   Japanese sentence exists, record it as `data-reference-jp`. New Japanese
   terms are never invented: no corpus term → English (e.g. `AC Expansion Port`).
5. **Add operator-requested US sections** (connections, 200V UPS/charging …):
   adapt to the JP spec (voltages, ports, cable names marked TBC), keep corpus
   Japanese for labels/frames, English otherwise; US figures via
   `scripts/rtd_figures.cjs` with an orange "美规原图…需重绘" caption.
6. **Count the translation volume:** `scripts/count_translation.py` →
   `new-translation-needed.xlsx/.csv` + summary; mirror the totals in the
   review appendix.
7. **Audit US↔JP coverage** when asked or before a big hand-off —
   `references/alignment-audit.md` (unit extraction, parallel per-chapter
   agents, overrides, `scripts/aggregate_align.py`).
8. **Style like the published JP web manual** (JE-1000F JP) —
   `references/jp-style-mapping.md`; overlay `assets/review-overlay.css`.
9. **Verify** with `scripts/render_check.cjs` at 1280 and 390 px: no broken
   images, no page-level horizontal scroll, expected colors; read the section
   screenshots, compare with the reference manual.
10. **Deliver** a versioned zip (`JHP-xxxx-JP-Review-Draft-vX.YY.zip`) with
    HTML, assets, registers, xlsx and an updated `README.md`/`review.zh.md`;
    send it to the operator. Upload to the Feishu wiki only when asked
    (`references/feishu-io.md`), next to the original, then read back.

## Color contract (operator-confirmed)

| Color | Meaning |
| --- | --- |
| black | existing Japanese (template, TM, JP web manual); spec values inside Japanese |
| green `.en-new` | no Japanese corpus → English, counted as new translation |
| blue small `.zh-translation` | Chinese gloss of every unit |
| magenta `.jp-parameter` | pending value / TBC (not translation) |
| orange `.jp-review` | Chinese review note, source and reasoning |

## Rules that bite

- Never claim "no Japanese exists" from one source: check all corpus layers,
  including short labels (「認証：」) that sentence filters drop.
- Keep every version's decisions in `review.zh.md` (newest first) and bump
  the version in the toolbar, title, banner and change log.
- Live Feishu writes need the operator's request in this conversation and a
  read-back (node + SHA-256). The repo's lark/Bitable discipline still applies:
  `.agents/skills/lark-cli-bitable-ops/SKILL.md`.
- Known pitfalls and their fixes: `references/pitfalls.md`.

## Resources

- `scripts/feishu_api.py` — wiki node, download, Bitable dump, upload-to-wiki with read-back.
- `scripts/jp_corpus.py` — JP sentence pool from RTD JP manuals + templates; TM grep/fuzzy match.
- `scripts/extract_units.py`, `scripts/aggregate_align.py` — coverage audit.
- `scripts/count_translation.py` — translation volume.
- `scripts/fetch_jp_style.py`, `assets/review-overlay.css` — JP styling.
- `scripts/render_check.cjs`, `scripts/rtd_figures.cjs` — Chromium checks and US figure screenshots.
- `references/examples/jhp3600c/make_v015…019.py` — the JHP-3600C transformations (spec fill, connections, color/count, restyle, 200V) to adapt, not to run as-is.
