# Workflow guide: build commands

Part of the [workflow guide](../hello_auto-doc.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

## 8. Build Commands

Cross-platform entrypoint:

```powershell
python build.py doctor --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py doctor --data-plane --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2
python build.py rst
python build.py review
python build.py check
python build.py sync-review
python build.py publish
python build.py release-manifest
python build.py preview --config configs/config.us-en.yaml --model JE-1000F --region US --page 03_product_overview_placeholder
python build.py fast --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py html
python build.py word
python build.py pdf
python build.py all
```

Config scope rule:

- [`configs/config.us.yaml`](../../configs/config.us.yaml): shared EN / US template-family config
- [`configs/config.us-en.yaml`](../../configs/config.us-en.yaml): canonical US English single-language review / CI / explicit review-preview landing target
- [`configs/config.ja.yaml`](../../configs/config.ja.yaml): shared JP template-family config
- [`configs/config.zh.yaml`](../../configs/config.zh.yaml): shared CN zh template-family config using [`docs/manifests/manual_zh.yaml`](../../docs/manifests/manual_zh.yaml)
- [`configs/config.kr.yaml`](../../configs/config.kr.yaml): shared KR ko template-family config for `JE-1000F_KR` and `JE-2000E_KR`, using [`docs/manifests/manual_kr.yaml`](../../docs/manifests/manual_kr.yaml)
- [`configs/config.eu.yaml`](../../configs/config.eu.yaml): shared EU merged template-family config using [`docs/manifests/manual_eu.yaml`](../../docs/manifests/manual_eu.yaml)
- [`configs/config.eu-en.yaml`](../../configs/config.eu-en.yaml), [`configs/config.eu-fr.yaml`](../../configs/config.eu-fr.yaml), [`configs/config.eu-es.yaml`](../../configs/config.eu-es.yaml), [`configs/config.eu-de.yaml`](../../configs/config.eu-de.yaml), [`configs/config.eu-it.yaml`](../../configs/config.eu-it.yaml), and [`configs/config.eu-uk.yaml`](../../configs/config.eu-uk.yaml): explicit EU single-language configs using [`../docs/manifests/manual_eu-en.yaml`](../../docs/manifests/manual_eu-en.yaml) plus the corresponding [`../docs/manifests/manual_eu-single-*.yaml`](../../docs/manifests) stacks
- [`configs/config.solar-eu-en.yaml`](../../configs/config.solar-eu-en.yaml): exact `JS-100I / EU / en` and `JS-40C / EU / en` Web entrypoint using the reusable [`Solar@INTL` skeleton](../../docs/manifests/skeletons/solar-intl/blueprint.yaml). JS-100I uses five Inbox cards plus unfolding/folding; JS-40C uses seven Inbox cards plus Solar Panel Storage. Both use frozen phase2 specifications and target-bound English figures; this config is not a fallback for portable-power-station targets.
- [`configs/config.solar-eu-multilingual.yaml`](../../configs/config.solar-eu-multilingual.yaml): JS-100I / EU 的 `fr/es/de/it/uk/pt/nl/pl` Git 源候选；逐语指定 `--lang` 和匹配的 `added-locales/2026-09-28/phase2/<lang>` 数据目录。沿用太阳能板 RST/CSV、manual-ir/v2 和共用 Web 组件。英语保留原结构数据，操作图拆分为原生透明插图并配可选中文本，手机参数表在容器内换行。荷兰语 `OPMERKING`、波兰语 `Uwaga` 以原文进入共用提示条；各语言发布前必须通过组件适用性及保修原文哈希检查。[来源、勘误与本地验收](../../code-as-doc/reviews/js100i_eu_nine_language_2026-09.md) 不代表已发布、已写 Base 或已晋升插图资产。
- [`configs/config.us-en.yaml`](../../configs/config.us-en.yaml), [`configs/config.us-es.yaml`](../../configs/config.us-es.yaml), [`configs/config.us-fr.yaml`](../../configs/config.us-fr.yaml), and [`configs/config.pt-br.yaml`](../../configs/config.pt-br.yaml) now inherit their shared single-language US defaults from [`../configs/config-bases/us-single-language-base.yaml`](../../configs/config-bases/us-single-language-base.yaml); keep common single-language build defaults there and keep language-specific page order in [`../docs/manifests/manual_us-single-en.yaml`](../../docs/manifests/manual_us-single-en.yaml), [`../docs/manifests/manual_us-single-es.yaml`](../../docs/manifests/manual_us-single-es.yaml), [`../docs/manifests/manual_us-single-fr.yaml`](../../docs/manifests/manual_us-single-fr.yaml), and [`../docs/manifests/manual_pt-br.yaml`](../../docs/manifests/manual_pt-br.yaml)
- [`configs/config.us-en.yaml`](../../configs/config.us-en.yaml) additionally sets `md_output` so its Markdown / Web artefact stays `manual_je1000f_us`, the stem the published `JE-1000F/US/en/md/` page already uses; its Word and PDF artefacts keep the inherited `_en` suffix, and `config.us-fr.yaml` / `config.us-es.yaml` keep the inherited `_fr` / `_es` suffix on every artefact. See [`code-as-doc/dev/web_publish_locale_queue.md`](../../code-as-doc/dev/web_publish_locale_queue.md) for why a published locale route cannot be renamed
- the current maintained baseline target is `JE-1000F` across these active config families, including `JE-1000F / US`, `JE-1000F / EU`, and `JE-1000F / JP`
- do not create a new config only because the model changed; pass `--model` and `--region` instead
- create a new config only when the page stack, template family, or output conventions are genuinely different

Useful target-scoped examples:

```powershell
python build.py doctor --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py rst --config configs/config.ja.yaml
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US --refresh-review
python build.py sync-review --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py publish --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check --config configs/config.zh.yaml --model JE-2000E --region CN
python build.py check --config configs/config.kr.yaml --model JE-2000E --region KR
python build.py rst --config configs/config.us.yaml
python build.py word --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py pdf --config configs/config.ja.yaml --model JE-2000F --region JP
```

Source mode examples:

```powershell
python build.py rst --config configs/config.ja.yaml --model JE-1000F --region JP --source runtime
python build.py word --config configs/config.ja.yaml --model JE-1000F --region JP --source review
```

Source mode meaning:

- `auto`: use `_review` if it exists, otherwise use template/data runtime draft
- `runtime`: ignore `_review` and build from template/data
- `review`: require `_review` and build from it

PR preview note:

- when a PR changes `docs/_review/<model>/<region>/`, GitHub review-preview derives that exact target from the diff and uses the same target-aware config matching as Start Review/Draft/Publish; for example, `JBP-2000B / US` uses `configs/config.bp-us.yaml`, while ordinary US host targets keep the MAIN config
- when a PR changes the zh manual family under `docs/templates/page_zh/`, `docs/templates/recipes/zh/`, or `docs/manifests/manual_zh.yaml`, the preview tool still selects the config-derived CN runtime target automatically, while packaging every existing review model
- `python -m tools.process_docs.build_review_preview` can omit `--config` when `--model` and `--region` identify a declared target; it can omit all three in CI-style runs and infer the target from the changed review bundle or existing review tree. Keep `--config configs/config.us-en.yaml` when you explicitly want the US English single-language target
- the Vercel review-preview fallback derives those family configs and its first fallback target by scanning `configs/config*.yaml`; it is used only when `PREVIEW_MODEL` / `PREVIEW_REGION` and the review tree do not provide a target

`publish` behavior:

- requires explicit `--model` and `--region`
- requires an existing `_review/<model>/<region>/`
- exports revision reports to [`reports/version_tracking/<model>/<region>/`](../../reports/version_tracking) by default
- writes a release manifest to [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../../reports/releases)
- queue-driven `Workflow_action=Publish` stages the formal DOCX, PDF, Markdown, IDML outputs, and designer handoff ZIP under [`../reports/releases/<model>/<region>/<lang>/versions/<version>/`](../../reports/releases), then writes the uploaded handoff ZIP URL to `idml_file`; it does not build a Draft cloud doc or HTML
- queue-driven `Workflow_action=Web Publish` forces live asset sync, renders web-profile MyST/HTML, advances the `Hello-Docs/publish:docs/publish/` candidate, and opens or updates its `docs/publish/**`-only PR into `main`; after a human merges that PR, `web-publish-receipt.yml` verifies the live deployment and writes the canonical nested RTD page (for example `https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us.html`) to `HTML_link`; the short root alias (for example `/manual_je1000f_us.html`) remains the printed/QR entry layer, and the queue does not upload or overwrite IDML/PDF/DOCX outputs
- an authorized Git-only Web release takes reviewed, committed sources and `source_manifest.json` through exact-ref checks, Web MyST, strict Sphinx, release metadata, and the same publish assembler. It reads or writes no online tables and creates no queue row. Its durable proof is the source and Hello-Docs commits, hashes, manifests, RTD build commit, canonical routes and aliases; see the [Git-only transaction](../../code-as-doc/dev/web_publish_pipeline.md#22-git-only-transaction)

`preview` behavior:

- requires explicit `--model`, `--region`, and `--page`
- `--page` must match one exact page selector
- writes to [`docs/_build/<model>/<region>/preview/<page>/rst/`](../../docs/_build)
- does not rewrite root [`docs/index.rst`](../../docs/index.rst)

`fast` behavior:

- equivalent to a runtime-only `rst --prepare-only --no-clean`
- useful for template or placeholder debugging without export steps

`sync-review` behavior:

- first refreshes the runtime bundle from template/data
- then updates only data-driven review files by default
- does not replace ordinary review prose pages unless you explicitly name them with `--page-file`
- skips exact target-local paths declared by the review bundle's `manifest.json` `sync_preserve_paths`, including paths explicitly named with `--page-file`; only relative `.rst` files under `page/` or `generated/` are accepted
- data-driven means:
  - all generated CSV pages
  - all materialized `spec_*` / `safety_*` pages
  - all template pages whose source contains placeholders such as `|PRODUCT_NAME|` or `|MAIN_POWER_BUTTON_LABEL|`
  - cover pages generated from title/product identity
- generated cover pages still feed PDF/LaTeX output, but HTML now opens directly on the first manual content section instead of a blank cover-style landing screen
- manual HTML preview also suppresses most default Furo sidebar / TOC chrome, stays in a continuous reading flow instead of browser-side fake pagination, regenerates a lightweight left outline from the manual headings, and renders generic headings, copy width, figure presentation, ordinary table spacing, and the multilingual preface notice in a restrained neutral manual-reader style while keeping dedicated component layouts such as `SPECIFICATIONS`, so the result feels like a manual reader instead of a documentation site
- review-preview workspace manual pages now reuse the same manual HTML/CSS/JS treatment as the local build, including the generated heading sidebar and the same no-top-switcher layout

Shared-source propagation audit (read-only):

```powershell
python -m tools.check_review_branch_sync --base origin/main --remote origin --json
```

- the ledger reads every live `review/*` branch manifest, so legacy
  `review/id-*` names do not need to encode model or region
- each row binds one affected branch to one changed shared-source file and is
  either `merge_params_safe` or `needs_human`
- `merge_params_safe` is a narrow proof: the change is confined to stable
  placeholder-bearing lines and the reviewer has not edited text outside those
  placeholders on the same line
- unresolved branch refs/manifests, non-parameter files, structural changes,
  ambiguous derivative mapping, and same-line reviewer edits abstain as
  `needs_human`; the command never modifies or syncs a branch

Equivalent lower-level examples:

```powershell
.\.venv\Scripts\python.exe tools\build_docs.py --config configs/config.us-en.yaml --model JE-1000F --region US --prepare-only
.\.venv\Scripts\python.exe tools\build_docs.py --config configs/config.us-en.yaml --model JE-1000F --region US --formats word --no-open
```

Word styling note:

- the US English Word path now reapplies the `reference_en.docx` heading, table, and default paragraph styling after DOCX generation, while leaving the generated `safety` and `spec` pages as-is
- Word output now also normalizes image relationships to embedded media before the final DOCX post-processing step, which improves Feishu and other third-party preview compatibility for image-backed tables
- the exporter preserves `manual_bundle.html` unchanged for traceability, but
  removes only `<main ...>` wrapper tags in a temporary Pandoc input. This keeps
  all page children and component order while preventing an earlier empty
  `<main></main>` from making the generated DOCX body empty; the temporary file
  is deleted after conversion
