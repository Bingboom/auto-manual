# Quick Start Guide

Updated: 2026-03-17

This guide describes the real working flow for `manual_je1000f_jp`.
It assumes the final editable manual lives under [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP) after review starts.

Target in this guide:

- product: `JE-1000F`
- region: `JP`
- config: [`config.ja.yaml`](../config.ja.yaml)
- final Word output: [`docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx`](../docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx)
- config rule: use the JP template-family config plus `--model` and `--region`

---

## 1. Environment Preparation

Before starting this JP example, complete the environment setup described in [`hello_auto-doc.md`](hello_auto-doc.md).

Minimum expected setup in the repository root:

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Also make sure the external tools required by your target export path are installed.
For the full environment notes, including `xelatex` and `pandoc`, use [`hello_auto-doc.md`](hello_auto-doc.md).

---

## 2. Three Layers in the Real Workflow

There are three different content layers. They are not used the same way.

1. Template and data seed layer
   - templates:
     - [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)
   - structured data:
     - [`data/phase1/Spec_Master.csv`](../data/phase1/Spec_Master.csv)
     - [`data/phase1/Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
     - [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)
     - [`data/phase1/content_blocks.csv`](../data/phase1/content_blocks.csv)
   - purpose:
     - create the first draft
     - maintain reusable structure shared by many products

2. Review working layer
   - [`docs/_review/JE-1000F/JP/index.rst`](../docs/_review/JE-1000F/JP/index.rst)
   - [`docs/_review/JE-1000F/JP/page/*.rst`](../docs/_review/JE-1000F/JP/page)
   - [`docs/_review/JE-1000F/JP/generated/JE-1000F/*.rst`](../docs/_review/JE-1000F/JP/generated/JE-1000F)
   - [`docs/_review/JE-1000F/JP/overrides/**`](../docs/_review/JE-1000F/JP/overrides)
   - purpose:
     - day-to-day review edits for this exact target
     - Git-tracked review history
     - final publish source after review starts

3. Runtime publish layer
   - [`docs/_build/JE-1000F/JP/rst/**`](../docs/_build/JE-1000F/JP/rst)
   - [`docs/_build/JE-1000F/JP/html/**`](../docs/_build/JE-1000F/JP)
   - [`docs/_build/JE-1000F/JP/word/**`](../docs/_build/JE-1000F/JP/word)
   - [`docs/_build/JE-1000F/JP/pdf/**`](../docs/_build/JE-1000F/JP)
   - purpose:
     - temporary runtime bundle
     - final HTML / Word / PDF outputs

Rule:

- before review starts, use template/data to create the first draft
- after review starts, edit [`docs/_review/JE-1000F/JP/**`](../docs/_review/JE-1000F/JP)
- do not use [`docs/_build/**`](../docs/_build) as the editing surface

---

## 3. What You Should Edit

### 3.1 Edit template/data only in these cases

Edit [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp) or CSV when the change should be reusable for other products too.

Typical examples:

- a generic JP page structure change
- a reusable heading or layout change
- a new placeholder family that should exist for many models
- a real product parameter update in [`Spec_Master.csv`](../data/phase1/Spec_Master.csv)

### 3.2 Edit `_review` in normal manual production

Once `JE-1000F / JP` has entered review, normal copy changes should happen here:

- [`docs/_review/JE-1000F/JP/page/*.rst`](../docs/_review/JE-1000F/JP/page)
- [`docs/_review/JE-1000F/JP/generated/JE-1000F/*.rst`](../docs/_review/JE-1000F/JP/generated/JE-1000F)

Use this for:

- target-specific wording adjustments
- reviewer comments
- temporary release-specific edits
- final release polishing

### 3.3 Asset overrides during review

If review needs a replacement image, put it under:

- [`docs/_review/JE-1000F/JP/overrides/_static/**`](../docs/_review/JE-1000F/JP/overrides/_static)

using the same relative path as the public asset.

Only these override subtrees are overlaid into the runtime bundle:

- [`docs/_review/JE-1000F/JP/overrides/_static/**`](../docs/_review/JE-1000F/JP/overrides/_static)
- [`docs/_review/JE-1000F/JP/overrides/_assets/**`](../docs/_review/JE-1000F/JP/overrides/_assets)
- [`docs/_review/JE-1000F/JP/overrides/renderers/**`](../docs/_review/JE-1000F/JP/overrides/renderers)

---

## 4. End-to-End Flow

For `manual_je1000f_jp`, the real flow is:

1. create or update the draft seed from template/data
2. initialize the review bundle once
3. edit the review bundle during the whole review cycle
4. run `check` against the review content
5. commit each review round
6. export the revision record table
7. publish from review
8. push

---

## 5. Stage A: Create the First Draft from Template/Data

Before the first real Word / PDF build on a machine, run environment self-check once:

```powershell
python build.py doctor --config config.ja.yaml --model JE-1000F --region JP
```

This tells you whether the current machine is ready for:

- Word export for the current `word_source`
- PDF export for the current `pdf.mode`
- required Python modules
- required system tools such as Word COM, `pandoc`, and `xelatex`

If this target has not entered review yet, prepare the runtime draft from template/data.

```powershell
python build.py rst --config config.ja.yaml --model JE-1000F --region JP --source runtime
```

What this does:

- reads [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)
- reads [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) and other CSV data
- generates CSV-backed pages
- materializes the runtime draft to:
  - [`docs/_build/JE-1000F/JP/rst/`](../docs/_build/JE-1000F/JP/rst)

Use `--source runtime` here on purpose:

- it guarantees the draft comes from the generic template/data seed
- it does not pull an older `_review` bundle back in

---

## 6. Stage B: Initialize Review Once

When the draft is ready to enter formal review, seed the review bundle.

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP
```

What this does:

1. creates a fresh runtime draft from template/data
2. copies the reviewable subset into:
   - [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP)

Important behavior:

- if [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP) does not exist, it is created
- if it already exists, `review` now keeps the existing review content by default
- this prevents accidental overwrite of reviewer edits

Use `--refresh-review` only when you intentionally want to throw away the current review text and reseed from template/data:

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP --refresh-review
```

---

## 7. Stage C: Edit the Review Bundle

After review starts, this becomes the normal editing surface:

- [`docs/_review/JE-1000F/JP/index.rst`](../docs/_review/JE-1000F/JP/index.rst)
- [`docs/_review/JE-1000F/JP/page/*.rst`](../docs/_review/JE-1000F/JP/page)
- [`docs/_review/JE-1000F/JP/generated/JE-1000F/*.rst`](../docs/_review/JE-1000F/JP/generated/JE-1000F)

This is the key workflow change:

- do not keep editing [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp) for daily JE-1000F JP review work
- do not keep editing [`docs/_build/JE-1000F/JP/rst/**`](../docs/_build/JE-1000F/JP/rst)
- do keep editing [`docs/_review/JE-1000F/JP/**`](../docs/_review/JE-1000F/JP)

If you later discover a change should actually be shared by many products, move that logic back into the template/data layer in a separate update.

---

## 8. Stage D: Run the Quality Gate Against Review Content

`check` now uses source `auto` by default.
That means:

- if a review bundle exists, `check` validates the review-edited content
- if no review bundle exists yet, `check` validates the runtime draft from template/data

Run:

```powershell
python build.py check --config config.ja.yaml --model JE-1000F --region JP
```

What it checks:

- target identity
- stale foreign model names
- unresolved placeholders
- missing include targets
- missing assets
- page contract missing placeholders, spec keys, `tpl_*` keys, and assets

---

## 9. Stage E: Build Preview Outputs from Review

After review starts, build actions use source `auto` by default.
If [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP) exists, the review content is overlaid onto the runtime bundle before export.

So these commands now build from review by default:

```powershell
python build.py rst --config config.ja.yaml --model JE-1000F --region JP
python build.py html --config config.ja.yaml --model JE-1000F --region JP
python build.py word --config config.ja.yaml --model JE-1000F --region JP
python build.py pdf --config config.ja.yaml --model JE-1000F --region JP
```

If you want to be explicit, you can force review mode:

```powershell
python build.py word --config config.ja.yaml --model JE-1000F --region JP --source review
```

If you want to temporarily ignore review and preview only template/data output:

```powershell
python build.py word --config config.ja.yaml --model JE-1000F --region JP --source runtime
```

If you want one isolated page preview without rewriting the standard runtime bundle:

```powershell
python build.py preview --config config.ja.yaml --model JE-1000F --region JP --page 03_product_overview_placeholder
```

This writes to:

- [`docs/_build/JE-1000F/JP/preview/03_product_overview_placeholder/rst/`](../docs/_build/JE-1000F/JP/preview/03_product_overview_placeholder/rst)

If you only want a fresh runtime draft for template or placeholder debugging:

```powershell
python build.py fast --config config.ja.yaml --model JE-1000F --region JP
```

---

## 10. Stage F: Commit Every Review Round

Each meaningful review round should be committed.

Recommended pattern:

```powershell
git add docs/_review/JE-1000F/JP
git commit -m "Update JE-1000F JP manual"
```

If the round also changed shared seed data or a generic template:

```powershell
git add data/phase1 docs/templates docs/_review/JE-1000F/JP
git commit -m "Update JE-1000F JP manual"
```

Rule:

- commit the real editing source for that round
- for target-only changes, that source is usually `_review`
- for shared changes, commit template/data and `_review` together

---

## 11. Stage G: When Parameters Change During Review

This is the important special case.

If you change:

- [`data/phase1/Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- [`data/phase1/Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
- [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)

after review has already started, do not use `--refresh-review` by default.

Use:

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP
```

What `sync-review` does by default:

- rebuilds the runtime draft from template/data
- syncs parameter-driven files into [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP)
- keeps ordinary manually edited review pages untouched

Default synced files:

- `generated/**/*.rst`
- `page/spec_*.rst`
- `page/safety_*.rst`
- any page whose source template contains placeholders such as `|PRODUCT_NAME|` or `|MAIN_POWER_BUTTON_LABEL|`
- cover pages generated from title/product identity

If you only want spec/safety generated files:

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --sync-scope generated
```

If one ordinary review page also needs to be replaced from runtime:

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --page-file 02_whats_in_the_box.rst
```

Use `review --refresh-review` only when you want to fully reseed the whole review bundle.

Batch refresh is supported too.
If a config contains multiple targets in `build.targets`, and multiple languages in `build.languages`, one command will refresh all of them:

```powershell
python build.py sync-review --config config.yaml
```

---

## 12. Stage H: Baseline and Normal Review Rounds

### 12.1 First baseline

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP
git add docs/_review/JE-1000F/JP
git commit -m "Add JE-1000F JP review baseline"
```

### 12.2 Normal follow-up round

```powershell
python build.py check --config config.ja.yaml --model JE-1000F --region JP
python build.py word --config config.ja.yaml --model JE-1000F --region JP
git add docs/_review/JE-1000F/JP
git commit -m "Update JE-1000F JP manual"
```

If you changed shared seed data and want to rebuild the review draft from scratch, use:

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP --refresh-review
```

Do this only intentionally.

---

## 13. Stage I: Export the Revision Record

After at least two review commits exist, export the revision report.

Recommended command:

```powershell
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP --from-ref HEAD~1 --to-ref HEAD
```

If this is the first baseline and you do not want one-time Added rows in the report:

```powershell
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP --from-ref HEAD~1 --to-ref HEAD --ignore-initial-adds
```

Main output directory:

- [`reports/version_tracking/JE-1000F/JP/`](../reports/version_tracking/JE-1000F/JP)

Recommended open order:

1. `*_index.html`
2. `*_fields.html`
3. `*_fields.csv`

For day-to-day revision sheets, `*_fields.csv` is usually the best table to send around.

---

## 14. Stage J: Publish the Final Release

Use `publish` as the formal release command.

```powershell
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
```

What `publish` does:

1. runs `check` against review content
2. exports the diff report from [`docs/_review/JE-1000F/JP`](../docs/_review/JE-1000F/JP)
3. builds the final Word document from review
4. writes a release manifest to [`reports/releases/JE-1000F/JP/`](../reports/releases/JE-1000F/JP)

Default diff output directory for publish:

- [`reports/version_tracking/JE-1000F/JP/`](../reports/version_tracking/JE-1000F/JP)

If the review bundle does not exist, `publish` fails.
This is intentional. Formal release should not silently fall back to template draft content.

If you need the traceability record without rerunning the whole publish sequence:

```powershell
python build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP
```

---

## 15. Stage K: Build the Final Word Document Directly

If you only need the Word file and do not want the full release sequence, you can still run:

After the review round is accepted, build the final JP Word document.

```powershell
python build.py word --config config.ja.yaml --model JE-1000F --region JP
```

This now uses the final review content by default, because:

- `word` uses `--source auto`
- `auto` prefers [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP) when it exists

If you want the command to state that explicitly:

```powershell
python build.py word --config config.ja.yaml --model JE-1000F --region JP --source review
```

Expected output:

- [`docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx`](../docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx)

---

## 16. Stage L: Archive and Push

Your review bundle itself is the archiveable editable source.

Recommended release close-out:

1. commit the final review content
2. export the revision record
3. build the final Word document from review
4. push

Command:

```powershell
git push
```

---

## 17. Full Example for `manual_je1000f_jp`

### 17.1 First-time setup

```powershell
python build.py rst --config config.ja.yaml --model JE-1000F --region JP --source runtime
python build.py review --config config.ja.yaml --model JE-1000F --region JP
git add docs/_review/JE-1000F/JP
git commit -m "Add JE-1000F JP review baseline"
```

### 17.2 Normal review loop

```powershell
python build.py check --config config.ja.yaml --model JE-1000F --region JP
git add docs/_review/JE-1000F/JP
git commit -m "Update JE-1000F JP manual"
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
git push
```

### 17.3 Parameter change during review

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP
git add data/phase1 docs/_review/JE-1000F/JP
git commit -m "Sync JE-1000F JP parameter updates"
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
```

### 17.4 Intentional reseed from template/data

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP --refresh-review
```

Use this only when you have decided to replace the current review text with a new draft from the shared seed layer.

---

## 18. Common Mistakes

- Editing [`docs/_build/JE-1000F/JP/rst/**`](../docs/_build/JE-1000F/JP/rst) and expecting the edits to survive
- Running `python build.py review` and assuming it always refreshes review content
- Running `python build.py review --refresh-review` without realizing it will replace the current review text
- Changing [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) during review and forgetting to run `sync-review`
- Continuing to edit [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp) for target-only review comments
- Exporting diff reports from `_build` instead of `_review`
- Forgetting that `word/html/pdf/check` now use review content by default after review exists
- Running `publish` before the first review baseline exists

---

## 19. One-Sentence Rule

For `manual_je1000f_jp`, the correct flow is:

seed from template/data once -> `review` once -> edit `_review` -> if parameters changed run `sync-review` -> commit -> `publish` -> `push`
