---
name: pdf-web-sideload
description: Bypass intake for a book whose structured intake (spec extraction, templating) is not done yet but that must go live now. Convert the shipped PDF to MyST Markdown, land it with `build.py web-sideload` (stages it under reports/releases/ with a mandatory pdf_sideload marker and an automatic 整本未结构化 debt entry, no pipeline evidence), then collect it exactly like a pipeline book with `build.py web-assemble`. Use when the trigger is "this book needs to ship before it's structurally sourced" — not for a book that already has a review branch or phase2 data (use web-release), and not for standing up a brand-new model/region/lang target (use new-region-line first).
---

# PDF Web Sideload

`build.py web-release` publishes a book by running this repo's real
RST -> Web-profile pipeline and sealing per-language projection evidence for
it. Some books need to be live before that pipeline has anything to run on —
the spec extraction and templating (`spec-sheet-structured-intake`) is not
done yet, but the printed PDF already exists and the business need is now.
`build.py web-sideload` is the bypass intake for exactly that gap: it takes
an externally converted MyST Markdown source and stages it with the same
staging/metadata functions `web-release` uses, so `web-assemble` collects it
with equal standing — but it is marked `source_kind: "pdf_sideload"` and
carries **no** projection evidence, and it forces a debt entry every time.

This is not a way to skip structured intake permanently. It is a shipped-now,
paid-back-later bypass, and the payoff is mechanical: once
`spec-sheet-structured-intake` lands real phase2 data for the target, an
ordinary `build.py web-release` run for the same model/region/lang
overwrites this target's `latest/web/publish_meta.json` in place (same
identity), superseding the sideload build with zero extra steps.

## Before you start

The target (model, region, lang) must already be **declared** in a family
config — `build.languages` must list the language, and the model/region must
resolve through that config. Sideload bypasses missing *content*, not a
missing *target registration*. If the model/region/lang does not exist in
any `configs/config.*.yaml` yet, that is `new-region-line`'s job first, not
this skill's.

If the book already has a review branch, or phase2 source data exists for
it, use `build.py web-release` instead — sideloading a book the pipeline can
already build only creates a debt entry for something that is not actually
debt.

## The spine

```
1. Extract  — PyMuPDF (fitz) on the shipped PDF, page by page
2. Arrange  — one MyST md/ bundle, named to the config's output template
3. Sideload — build.py web-sideload --md-dir <bundle> ...   (stage + debt)
4. Collect  — build.py web-assemble                          (same as any book)
5. Receipt  — build.py web-receipt --write                   (after PR merge)
```

### 1. Extract with PyMuPDF, never `pdftotext`

Use PyMuPDF (`fitz`) to pull text and layout from the shipped PDF, page by
page. **Do not use `pdftotext`** on a double-column manual page: it reads
across columns instead of down each one and silently interleaves lines from
the left and right column into one garbled sentence order — a repo-recorded
trap (see `verify-before-asserting-absence` memory notes on this exact
failure). Re-flow each page into ordered prose/table blocks before moving to
step 2; do not hand a raw column-interleaved dump to the next step.

### 2. Arrange one MyST `md/` bundle

Build a directory shaped exactly like a staged `md/` output — the same shape
`tools.queue_bound_outputs.stage_web_publish_assets_to_host_repo` validates:

- `manual_<stem>.md` — the converted manual body. The filename **must**
  equal what `build.py`'s config-derived output-naming template would
  produce for this exact model/region/lang (the same template `web-release`
  uses via `resolve_md_output_path_for_target`). Guessing the name wrong is
  the single most common failure here — `web-sideload` refuses with the
  exact expected filename when it does not match, so run once with
  `--dry-run` to confirm the name before finishing the conversion.
- `index.md` — a MyST `{toctree}` page whose single entry is that manual
  stem (mirrors what `build.py md` itself generates).
- `conf.py` — a minimal Sphinx conf (`extensions = ["myst_parser"]` is
  enough; copy one from an existing staged `reports/releases/**/web/md/`
  bundle if unsure).
- `assets/` — optional, any images the converted manual references with
  relative paths.

Do not point `--md-dir` at anything under `docs/publish/` or hand-edit
anything there directly — `docs/publish/**` is assembler-owned generated
output (see `code-as-doc/dev/web_publish_pipeline.md` §3); this bundle is a
local, disposable staging input only.

### 3. Land it

```
python build.py web-sideload \
  --config <config> --model <M> --region <R> --lang <L> --version <V> \
  --md-dir <path to the md/ bundle> \
  [--debt "category:location:payoff action"]... \
  [--dry-run]
```

- `--version` follows the same convention as `web-release`: if the printed
  manual's version is unknown, use a Git-flavored technical snapshot version
  (`git-<date>-<source-sha-prefix>` style), not a guessed paper-manual
  version.
- `--dry-run` (default off) runs the collision precheck and the `--md-dir`
  shape/filename check only — no staging, no debt write. Always run it once
  before the real thing.
- The real run also does a strict local `sphinx -W -b html` build of the
  sideloaded source before staging (same rigor as `web-release`'s
  verification, just against your bundle instead of a pipeline build); a
  Sphinx/MyST error in the bundle fails here, before anything is staged.
- One `整本未结构化` debt entry is recorded **unconditionally**, every run,
  regardless of `--debt` — its payoff action is literally "run
  `spec-sheet-structured-intake` then re-run `web-release` for this target".
  Any `--debt` flags you pass are recorded in addition, not instead.
- The written `publish_meta.json` carries `source_kind: "pdf_sideload"` and
  `language_scope: "single"`, with no `language_projection_evidence_*`
  fields. That marker is the only thing that exempts a target from
  `publish_branch_assembly`'s otherwise-mandatory evidence gate — every
  pipeline-built target stays exactly as fail-closed as before this command
  existed (see `tools/web_language_release_evidence.py` and
  `tests/test_publish_branch_assembly.py`'s `pdf_sideload`/`pipeline`
  control-pair tests if you need to verify that yourself).

### 4-5. Collect and receipt like any other book

From here it is indistinguishable from a pipeline-built book:
`build.py web-assemble` (then `--push` once verified) collects it into
`docs/publish/**` alongside every other target, and — only after the release
PR is reviewed, merged, and production is verified — `build.py web-receipt
--write` writes `Document_link.HTML_link` and the published-manual catalog
row. Follow `code-as-doc/dev/web_publish_pipeline.md` §2.2 steps 4-7
unchanged; sideload only replaces step 1-3's pipeline build with an external
conversion.

## Red lines

- Never hand-edit anything under `docs/publish/**` to land a sideloaded book
  — that tree is assembler-generated only; go through `web-sideload` +
  `web-assemble`.
- Never fork a template or CSS to make a sideloaded manual "look right" —
  the MyST source is opaque prose/tables to the assembler; template changes
  belong to the pipeline, not to a bypass for content that has not entered
  the pipeline yet.
- Never suppress or skip the automatic `整本未结构化` debt entry — it is the
  only durable record that this book still needs structured intake. If you
  find yourself wanting to avoid recording it, the actual fix is running
  `spec-sheet-structured-intake` first and using `web-release` instead.
- The payoff path is exactly one command: a real `build.py web-release` run
  for the same model/region/lang/version-family, once phase2 data exists.
  Do not write a second, different metadata path or manual withdrawal step
  to "replace" a sideloaded target — same identity means the pipeline run
  overwrites it in place.

## Boundaries

- Structured intake itself (the actual payoff action) →
  `spec-sheet-structured-intake`.
- Standing up a brand-new model/region/lang target that does not exist in
  any config yet → `new-region-line`.
- A book that already has a review branch or phase2 data → `build.py
  web-release`, not this skill.
- Collecting staged targets into `docs/publish/**` and the release PR, and
  the post-merge receipt step → both unchanged from
  `code-as-doc/dev/web_publish_pipeline.md` §2.2; this skill only covers the
  bypass intake in front of them.
