---
name: manual-revision-backport
description: Back-port a human reviewer's tracked-changes revision of a BUILT manual (.docx) into this repo's source of truth — the RST templates AND the Feishu phase2 source tables. Use whenever someone hands you a revised "…修订.docx" / reviewed Word manual (e.g. `JE-2000F-EU-fr-修订.docx`, several languages) and wants those edits reflected in the repo so the next build matches. This is reverse-sync of reviewer edits from an exported manual back into source — NOT new Markdown intake (use markdown-rst-template-intake) and NOT free translation/rewrite (use bitable-translation-memory / manual-rewrite-with-tm). Trigger even when the user only says "改回模版" / "把修订同步回去" / "update the template from this revised doc".
---

# Manual Revision Back-port

A reviewer opens a *built* manual in Word, turns on Track Changes, edits, and hands back
one `.docx` per language. Your job is to reflect those edits in the repo's **source of
truth** so the next `build.py` run reproduces them — without clobbering anything or
inventing work.

This skill owns the **analysis, source-mapping, and convergence-verification** that make
that safe and complete. It does **not** auto-execute writes: applying each change is
human-gated, because almost every revision raises scope questions only the operator can
answer (which model/region, which sibling targets, which "changes" are intentional).

Read `references/source-map.md` for the content→source map, the Feishu access recipe,
the apply techniques, and the decision checklist. Keep it open while you work.

## Core principles (internalize these — they are why the skill exists)

1. **Never transcribe the .docx blindly.** The reviewer edited a manual that was built
   from an *older* data/template snapshot, so a large fraction of its "changes" are
   already applied upstream, or are placeholder-resolved values, or are reviewer
   artifacts (e.g. a working version label). Treat the tracked changes as a *diff against
   a stale baseline*, then re-diff against the **current** source and only act on what is
   genuinely outstanding.
2. **Two-track source of truth — and NO `data/phase2/*.csv` is ever a source.** Manual
   content lives partly in repo **RST templates / recipes / configs** (editable here,
   normal branch/PR) and partly in **Feishu bitable tables**. Everything under
   `data/phase2/` is a *sync artifact* that `build.py sync-data` regenerates from the
   online tables — the online table is the single source of truth, so a hand-edit to any
   `data/phase2/*.csv` is silently clobbered on the next sync and the durable fix is always
   the Feishu source row. Note some CSVs are **derived, not 1:1 mirrors**:
   `spec_titles.csv` (also `Localized_Manual_Copy`, status words) is built from the
   `manual_copy_source` table (en source rows) joined to **Translation_Memory** for the
   localized columns — so the source of a section *title* is the TM row (per language,
   matched on the en source string), never the CSV.
3. **`sync-data` is operator-gated.** Its preflight needs `FEISHU_PHASE2_*` secrets that
   only exist in the operator's environment, so you cannot run a real sync or rebuild
   JE-2000F-style targets yourself. You CAN read/write the source rows directly with
   `lark-cli --as bot` (see references). Building a fresh baseline is the operator's step.
4. **Surface scope decisions; do not over-apply.** Model scope, region scope, sibling
   models, and "is this change intentional" are the operator's calls. Lay them out and
   wait. (Real examples that came up: AC-output count, whether to drop a cover line,
   whether to renumber app steps, whether to touch sibling EU models, whether a term is
   region-specific locale wording.)
5. **Verify convergence before saying "done."** It is very easy to miss scattered changes
   (the same terminology fix may live in 4 different tables + templates). Run
   `scripts/scan_residuals.py` for the OLD terms that should be gone; "done" means zero
   residuals *in scope*, with out-of-scope survivors explicitly explained.

## Default workflow

1. **Extract** the tracked changes per language:
   `python3 .agents/skills/manual-revision-backport/scripts/extract_docx_changes.py REVISED.docx [...] --out /tmp/revdiff`
   This emits, per file, a document outline + every changed paragraph as OLD→NEW with a
   heading breadcrumb. The breadcrumb is how you locate each change's manual section.
2. **Categorize** the changes. Typical buckets: spec values; symbol meanings; product
   part labels; body terminology; accents/diacritics; new content blocks; **cross-language
   data contamination** (one language's text sitting in another's column — a real bug
   worth flagging); headings. Note categories repeat across languages.
3. **Map each change to its source** using `references/source-map.md` (content type →
   template file OR Feishu table + the table's keying). Many tables key differently
   (`document_key` vs `Model`+`Region` vs `symbol_key`; per-model vs shared rows).
4. **Diff against current source, not the docx.** For each candidate change, read the
   *current* template / Feishu row. If it already matches the reviewer's NEW value, drop
   it. Only outstanding deltas survive.
5. **Surface the decisions** (principle 4) and wait for the operator before applying
   anything broad or model/region-scoped.
6. **Apply** the confirmed, in-scope deltas — human-gated, one logical group at a time:
   - repo templates: edit on a branch; for body copy use the apply techniques in
     references (word-boundary accent regex, ordered context-dependent term replaces,
     heading+underline pairs, placeholder-vs-literal awareness).
   - Feishu rows: `lark-cli --as bot` PUT, always **fetch → substring-replace → PUT →
     GET-verify** (never retype long fields). Report exactly what you set.
7. **Verify convergence** with `scripts/scan_residuals.py` (principle 5).
8. **Validate, commit, PR** (see below).

## Two-track source — quick orientation

- Repo templates (editable source): `docs/templates/page_<region-lang>/*.rst`,
  `docs/templates/page_shared/<lang>/*.rst`, `docs/templates/recipes/*/*.yaml`,
  `configs/config.*.yaml`.
- Feishu tables (the source for everything under `data/phase2/`; read/write with
  `lark-cli --as bot`): Spec_Master, page_placeholders, symbols_blocks, lcd_icons_blocks,
  troubleshooting_blocks, Spec_Footnotes, Spec_Notes, `manual_copy_source`, and
  **Translation_Memory** (a *separate base* — it backs derived CSVs like `spec_titles.csv`).
- `data/phase2/*.csv` are sync artifacts — never hand-edited.
- Full map (table ids, keying, which content lives where) is in `references/source-map.md`.

## Validate, commit, PR

- After template edits: `python build.py check --config configs/config.<region>.yaml --model <MODEL> --region <REGION>`
  (a buildable model whose data exists locally — it assembles all languages and catches
  RST/heading-underline errors). Revert any `docs/index.rst` the build regenerates.
- One topic per branch (`fix/<area>-<topic>` etc.); commit per logical unit; fill the PR
  template; do **not** self-merge. Feishu source edits are not in the repo — record them
  in the PR body / hand the operator the change-list so they re-sync.
- Honor AGENTS.md working-tree and concurrency rules.

## Use bundled resources

- `scripts/extract_docx_changes.py` — Word tracked-changes extractor (step 1).
- `scripts/scan_residuals.py` — convergence/residual checker (step 7); exits non-zero when
  residuals remain, so it can gate "done".
- `references/source-map.md` — content→source map, table keying, Feishu `lark-cli` read/write
  recipe, apply techniques, and the decision checklist. Read it before mapping changes.
