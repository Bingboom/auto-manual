---
name: pdf-web-sideload
description: Bypass intake for a book whose structured intake (spec extraction, templating) is not done yet but that must go live now. Convert the shipped PDF to MyST Markdown declaring every component with its semantic directive (never hand-written component HTML), land it with `build.py web-sideload` (stages it under reports/releases/ with a mandatory pdf_sideload marker and an automatic 整本未结构化 debt entry, no pipeline evidence), then collect it exactly like a pipeline book with `build.py web-assemble`. Use when the trigger is "this book needs to ship before it's structurally sourced" — not for a book that already has a review branch or phase2 data (use web-release), and not for standing up a brand-new model/region/lang target (use new-region-line first).
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
the left and right column into one garbled sentence order — a trap this repo has been burned by
on real double-column spec pages. Re-flow each page into ordered
prose/table blocks before moving to
step 2; do not hand a raw column-interleaved dump to the next step.

### 2. Arrange one MyST `md/` bundle

#### Declare components — never hand-write their HTML

**This is the contract that matters.** Every manual component (callout box,
spec table, troubleshooting table, icon legend, symbol panel, …) is declared
with a semantic directive from
[`tools/manual_md_directives.py`](../../../tools/manual_md_directives.py).
The bundle you write is the **author plane**; `web-sideload` compiles it into
the **staged plane** by running the real directive layer.

**Never hand-write component HTML** — not `<table class="manual-callout-table">`,
not `<figure class="hb-spec-table-composition">`, not any `hb-*` class, and
not an inline `style=` attribute. `web-sideload` refuses a bundle containing
any of them, and names the directive you should have used.

That refusal is not pedantry. Hand-written markup produces an unstyled shell,
because the stylesheet keys off structure a human transcription always loses:
`<colgroup>` sizing, `scope="row"` on the label column, `rowspan` merging, and
per-cell `hb-*` classes. The directive emits all of it; a hand-written table
emits none of it and renders as bare text. Component markup has exactly one
source, and it is the directive layer.

Inline styles are refused for the same reason: on the web plane a component
binds **classes only** (`web_callout_classes` in
[`tools/component_specs/adapters.py`](../../../tools/component_specs/adapters.py)
— contrast `word_callout_markup`, which is the *print* plane and is where
inline styles legitimately live). The shared
[`web_manual.css`](../../../docs/renderers/contracts/web_manual.css) owns the
look. Never add styling of your own; the stylesheet and the emitters are
shared surfaces and are out of bounds for a sideload.

The vocabulary — the label argument becomes the composition's `aria-label`:

````markdown
```{callout} WARNING
Do not open the enclosure.

- the body is full Markdown, so bullets and links work
```

```{spec-table} INPUT PORTS
1 × AC Input | Charge Mode: 100-120 V~ 60 Hz, 15 A max.
             | Bypass Mode^①^: 12 A max.
2 × DC8020 Ports | 11 V-16 V⎓8 A max.
```

```{troubleshooting} Fault codes
:headers: Error Code | Corrective Measures

E01 | Cool the unit / Restart
```

```{lcd-icons} LCD legend
① | ![battery](assets/batt.png) | Battery | Shows charge / Blinks when low
```

```{symbols} Safety symbols
![weee](assets/weee.png) | Dispose separately
```

```{lcd-mode} ![screen](assets/screen.png)
Standby | Press POWER | Wakes the display
        | Hold POWER | Powers off
```

```{comparison} Resumes | Does not resume
AC output | USB output
```

```{manual-table} Key combinations
:headers: Keys | Action

Hold POWER | Power on
```
````

Three conventions run across the whole vocabulary:

- **A blank cell merges with the cell above.** This is how the source
  expresses one label spanning several values — a state covering three
  actions, an input covering two modes. It becomes a real `rowspan`. A pipe
  table cannot express it and renders an empty box instead, which is why
  `{manual-table}` exists as the escape hatch for any shape without a
  dedicated component. In `{spec-table}` a blank *label* continues the
  previous label.
- **Circled footnote references** are written `^①^` (and subscripts `~x~`),
  which the emitter turns into `<sup>`/`<sub>`. Cell content otherwise takes
  a deliberately small inline subset (`**bold**`, images) so column and
  row-span semantics stay deterministic.
- **` / ` splits a multi-step cell** into the manual's line block, in
  `{troubleshooting}` measures and `{lcd-icons}` descriptions.

A `{callout}` body is parsed as full Markdown, so it may contain its own code
fence — use a **longer** outer fence (` ````{callout} `) when it does, exactly
as MyST requires.

#### Bundle shape

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
  bundle if unsure). Do **not** add the directive extension yourself —
  `web-sideload` loads it for you on a private copy during compilation. Do
  set `language` to the bundle's language code: the callout, troubleshooting
  and LCD emitters read it.
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
- The real run verifies in **two stages** before staging anything, and what
  gets staged is the compiled output, not what you wrote:
  1. **Author plane** — the component-markup lint above, then a strict
     `sphinx -W -b html` build with `tools.manual_md_directives` loaded, so
     every directive must parse. Each directive is then compiled into its
     component markup. Your `--md-dir` is never modified; compilation runs on
     a copy.
  2. **Staged plane** — a second strict `sphinx -W -b html` over the compiled
     bundle under `extensions=myst_parser,tools.rtd_portal`, which is exactly
     what Read the Docs builds the published source with. Passing this stage
     is what proves the staged artifact will actually render live.

  Compilation is not optional and cannot be replaced by a `conf.py` setting:
  [`.readthedocs.yaml`](../../../.readthedocs.yaml) passes
  `-D extensions=myst_parser,tools.rtd_portal`, which **overrides** `conf.py`,
  and `readthedocs_source.assemble_rtd_source` strips the bundle's `conf.py`
  outright. A directive left unexpanded in a staged file would render on RTD
  as an unknown-directive error. This is why authoring and staging are two
  different planes.
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
- Never hand-write component HTML or an inline `style=` in the author
  bundle. Declare the component and let the directive layer emit it — that
  layer is the single source of component markup, and hand-written markup
  ships an unstyled shell. `web-sideload` refuses it outright.
- Never fork, edit or extend a template, the shared stylesheet
  (`docs/renderers/contracts/web_manual.css`), an emitter, or
  `tools/manual_md_directives.py` to make a sideloaded manual "look right".
  Those are shared surfaces serving every book; template and component
  changes belong to the pipeline, not to a bypass for content that has not
  entered the pipeline yet. If a shape genuinely has no component, use
  `{manual-table}` and record it as debt.
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
