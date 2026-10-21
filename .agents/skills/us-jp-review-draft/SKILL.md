---
name: us-jp-review-draft
description: "Produce or continue a JP (日规) review draft (审核稿/审阅稿) of a manual whose source is the published US English manual: US structure as the master, existing Japanese reused wherever the corpus has it (whole sentences or sentence halves), the rest as green new translation (first-pass Japanese, US English kept for the count), JP spec-sheet and R&D values in purple, US↔JP content alignment audit, JP web-manual styling, versioned zip and optional Feishu wiki upload. Use for 基于美规输出日规说明书, 日规审核稿/审阅稿, 继续改日规草稿 (Feishu wiki zip), 统计需新增翻译量, 日规与美规内容是否对应, 研发答复回填. US→JP only; not for building a pipeline review branch (Start Review) or back-porting reviewer edits."
---

# US → JP Review Draft

Turn a published US English manual into a Japan-market review draft that
reviewers can read in one HTML page: Japanese from the existing corpus in black,
new translation in green, spec-sheet and R&D values in purple, pending values in
magenta, Chinese glosses in blue, review notes in orange. Proven on JHP-3600C
(v0.14 → v0.69); see `references/jhp3600c-case.md`.

This is an off-pipeline review artifact. It never writes `docs/templates`,
`docs/_review`, `data/phase2` or live source tables, and it never enters the
public repositories (auto-manual, Hello-Docs). Published drafts live only in
the private `Bingboom/Hello-Docs-Review` mirror; the other live write is the
operator-requested Feishu wiki upload.

## Inputs (ask for what is missing)

- US source: the RTD page (e.g. `https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/<MODEL>/US/en/md/...html`)
  or its frozen package under `data/manual_sources/<MODEL>/US/`. The US manual
  is the master: chapter order, sections and callouts follow it.
- Existing draft, if continuing: a Feishu wiki link to the draft zip, or the
  last zip the operator received.
- JP spec sheet (规格书, often screenshots or an A0 PDF) and R&D answers
  (研发答复, often chat screenshots): ratings, ports, limits, switching times.
- Operator decisions as they come up (chapters to add, product naming, wording,
  layout). Record each one in the draft's review notes, change log and
  `review.zh.md`.

## Workflow

1. **Load the draft.** Resolve the wiki node and download the zip into an empty
   scratch directory (`scripts/feishu_api.py node|download`; lark-cli may be
   unconfigured, the API helper only needs `FEISHU_APP_ID/SECRET`). Read the
   zip's `README.md`/`review.zh.md`, outline the HTML headings, render it once.
2. **Build the corpus** (read-only), in this order — see `references/corpus-and-color-rules.md`:
   JP RST templates → `Translation_Memory` terms + sentence pairs → live
   规格参数明细 / LCD tables → every published JP web manual (`scripts/jp_corpus.py pool`).
   Sibling JP models with the same hardware (e.g. JE-5000A for 100V/200V
   L14-30R/6-20R ports, JE-1000F for spec-table and safety wording) are the
   best source. Check `data/terminology_rules.csv` before choosing a term
   (e.g. Bypass → 「パススルー」, 「バイパス」 is retired).
3. **Fill the JP spec sheet.** Labels and row wording from the sibling JP spec
   table, not a word-for-word US label (no 「充電モード」/「パススルーモード」;
   add 「シガーソケット: 」「PV: 」). Values only from the JP spec sheet or R&D,
   in purple with their source. US values never enter Japanese text — they go
   into the orange review note.
4. **Replace with Japanese wherever it exists.** Reuse a corpus sentence when
   it says the same thing with only a value/name/port slot changed. When only
   half a sentence matches, split the unit: green new half + black corpus half.
   Everything else is a green unit with `data-needs-translation`, a first-pass
   Japanese draft and the US English in `data-previous-english`.
5. **Add operator-requested US sections** (connections, 200V UPS/charging …)
   and JP-only additions (e.g. a 電気工事士 installation caution): adapt to
   the JP spec, corpus Japanese for labels/frames; US figures via
   `scripts/rtd_figures.cjs` with an orange "美规原图…需重绘" caption.
6. **Fill R&D answers** as they arrive: write only what R&D stated, never a
   derived number; purple with `data-spec-source="研发答复 <date>"`. Keep open
   questions in the appendix; a question list for R&D is plain Chinese.
7. **Count the translation volume:** `scripts/count_translation.py --previous <last version dir>`
   → `new-translation-needed.xlsx/.csv` + summary; mirror the totals in the
   review appendix (units, words, chars, by chapter/type).
8. **Audit US↔JP coverage** when asked or before a big hand-off —
   `references/alignment-audit.md` (unit extraction, parallel per-chapter
   agents, overrides, `scripts/aggregate_align.py`).
9. **Style like the published JP web manual** (JE-1000F JP) —
   `references/jp-style-mapping.md`; overlay `assets/review-overlay.css`.
10. **Verify** with `scripts/render_check.cjs` at 1280 and 390 px (no broken
    images, no page-level horizontal scroll, expected colors) and look at the
    screenshot of every section you changed.
11. **Deliver** a versioned zip (`<MODEL>-JP-Review-Draft-vX.YY.zip`) with
    HTML, assets, registers, xlsx and an updated `README.md`/`review.zh.md`;
    send it to the operator. Upload to the Feishu wiki only when asked
    (`references/feishu-io.md`), next to the original, then read back.
12. **Write in the private repository.** A draft line in
    `Bingboom/Hello-Docs-Review` is one working directory,
    `docs/review-drafts/<MODEL>/<REGION>/` (its `draft.json` names the current
    version), plus frozen `milestones/<version>/` copies. Never add a version
    directory there: the site build refuses a `draft.json` anywhere else. Copy the
    working directory (without `milestones/`) to the scratchpad as the previous
    version, build the next one from it as above, put the new files back in place
    (keep `milestones/`), update `draft.json` (version, date, status, summary,
    `rd_open`), commit `<MODEL> <REGION> vX.YY: <summary>` to its `main` and push.
    Freeze a milestone only when the operator names one: copy the working directory
    (without `milestones/`) to `milestones/<version>/` and set its `milestone`. The
    private RTD project (<https://ht-docs-review-doc-lib.readthedocs-hosted.com/>)
    rebuilds the overview and the line page. Touch nothing outside
    `docs/review-drafts/` there (the mirror sync owns the rest). A zip goes to the
    operator only when asked. Rules:
    [`review-drafts-site.md`](../../../code-as-doc/dev/rtd_manual_portal/review-drafts-site.md).

One operator instruction = one version: a `make_vNNN.py` that copies the last
version directory, applies exact-count replacements, bumps every version
string and prepends the change log (`references/examples/jhp3600c/`).

## Color contract (operator-confirmed)

| Color | Markup | Meaning |
| --- | --- | --- |
| black | `.jp-original` | existing Japanese (template, TM, JP web manual) |
| green | `.en-new` (+ `data-needs-translation`) | new translation, counted; first-pass Japanese, US English in `data-previous-english` |
| green | `.en-new.jp-draft-insert` | small new insert (heading words, connector) or JP-only addition; not counted |
| purple | `.jp-spec-updated` / `.jp-spec-filled` | spec-sheet or R&D value, with source and date; not translation |
| magenta | `.us-difference.jp-parameter` | pending value 【要確認】/TBC |
| amber | `.jp-name-ref` | product-name reference 「本製品」 |
| blue small | `.zh-translation` | Chinese gloss of every unit |
| orange | `.jp-review` | Chinese review note, source and reasoning |

## Rules that bite

- Never claim "no Japanese exists" from one source: check all corpus layers,
  including short labels (「認証：」) and sentence halves.
- Wording decisions the operator already made (別売り vs 市販の, product-name
  reference, spec labels, full-width katakana, LCD 点灯時／消灯時) are in
  `references/corpus-and-color-rules.md`; apply them to new copy too.
- A question from the operator (为啥／是什么／…吗) gets an answer, not an
  edit. Change the draft only when asked; offer the change in one line.
- Keep every version's decisions in `review.zh.md` (newest first) and bump
  the version in the toolbar, title, banner, print note and change log.
- Live Feishu writes need the operator's request in this conversation and a
  read-back (node + SHA-256). The repo's lark/Bitable discipline still applies:
  `.agents/skills/lark-cli-bitable-ops/SKILL.md`.
- Known pitfalls and their fixes: `references/pitfalls.md`.
- Source-data errors found while drafting (fix the draft, record the debt,
  never write the live Base unasked): `references/source-data-debt.md`.

## Resources

- `scripts/feishu_api.py` — wiki node, download, Bitable dump, upload-to-wiki with read-back.
- `scripts/jp_corpus.py` — JP sentence pool from RTD JP manuals + templates; TM grep/fuzzy match.
- `scripts/extract_units.py`, `scripts/aggregate_align.py` — coverage audit.
- `scripts/count_translation.py` — translation volume (`--previous` carries counts forward).
- `scripts/fetch_jp_style.py`, `assets/review-overlay.css` — JP styling and review colors.
- `scripts/render_check.cjs`, `scripts/rtd_figures.cjs` — Chromium checks and US figure screenshots.
- `references/examples/jhp3600c/make_v0NN.py` — JHP-3600C transformations to adapt, not to run as-is (index in `references/jhp3600c-case.md`).
