# Build guide: standard Windows flow

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

Windows cleanup note:

- build actions except `fast` run with clean enabled unless you pass `--no-clean`
- if cleanup fails with a file-in-use error under [`docs/_build/`](../../docs/_build), close File Explorer, browser, Word, or PDF windows pointing at that target output and rerun
- `--no-clean` is the temporary workaround when you only need to rebuild in place

## 3. Standard Windows Flow

### 3.1 Validate Environment and Config

```powershell
python build.py validate --config configs/config.us.yaml
```

Equivalent low-level checks:

```powershell
python tools\validate_config.py --config configs/config.us.yaml
python tools\validate_layout_params.py --csv data\layout_params.csv
```

Minimal static check:

```powershell
python -m pip install ruff
python -m ruff check build.py tools tests scripts
```

The committed Ruff gate is intentionally small and low-noise. It currently checks bare `except`, undefined names, and unused local variables before CI runs the heavier unit/build validation paths.

If you use the Feishu-backed phase2 workflow, sync the frozen snapshot before runtime build:

```powershell
python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --dry-run
python build.py sync-data --config configs/config.us.yaml --data-root data/phase2
python build.py process-build-queue --config configs/config.us.yaml
python build.py message-control-dry-run --message "publish JE-1000F us-merged from branch feature/review-123"
```

That command requires:

- a working `lark-cli` binary on `PATH`
- a valid local `lark-cli` login session
- the `FEISHU_PHASE2_*` environment variables referenced by [`../configs/config.us.yaml`](../../configs/config.us.yaml) or [`../configs/config.ja.yaml`](../../configs/config.ja.yaml)
- `FEISHU_TRANSLATION_MEMORY_BASE_TOKEN`, `FEISHU_TRANSLATION_MEMORY_TABLE_ID`, and `FEISHU_TRANSLATION_MEMORY_VIEW_ID` for Translation Memory rows that generate `Localized_Copy.csv` and `Status_Words.csv`
- `--dry-run` is the recommended machine-readiness check first; it now aggregates missing CLI, missing `FEISHU_PHASE2_*` bindings, and missing Translation Memory binding into one preflight error before any fetch
- `build.py` auto-loads `~/.auto-manual-phase2.env` at startup when that file exists (via [`../tools/local_env.py`](../../tools/local_env.py)), so the bindings above can live in a single `$HOME` env file instead of being `source`-d into every shell — this is what lets a command runner such as the OpenClaw gateway run `sync-data` without a manual `source`. It does not override variables already set in the environment, and `AUTO_MANUAL_PHASE2_ENV_FILE` redirects the path
- on Windows, the default `sync.phase2.cli_bin: lark-cli` is resolved to the installed shim automatically during fetch, so you do not need a Windows-only config override
- when `spec_master` is included, the sync also refreshes [`../data/phase2/row_key_mapping.csv`](../../data/phase2/row_key_mapping.csv) as the phase2 mirror of the row-label mapping table
- if you also use the Feishu `Document_link` build queue, set `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID` and `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID`; `process-build-queue` reuses the same `FEISHU_PHASE2_BASE_TOKEN`, auto-derives the current wiki destination from that base when possible, and optionally accepts `FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN` when you want to force a different parent wiki node
- `spec-master-rebuild --bootstrap-source-tables` also needs `FEISHU_PHASE2_DOCUMENT_KEY_TABLE_ID` and `FEISHU_PHASE2_ROW_KEY_TABLE_ID` so it can create source-table link fields against the copied Base's dictionary tables
- if you want Feishu/wiki primary plus DingTalk sync, set `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session` plus either global `DINGTALK_DOCS_A_TOKEN`, `DINGTALK_DOCS_XSRF_TOKEN`, and `DINGTALK_DOCS_COOKIE` with optional `DINGTALK_DOCS_TARGET_NODE_URL` and `DINGTALK_DOCS_BX_V`, or a per-operator session registry under `AUTO_MANUAL_DINGTALK_SESSION_ROOT`; when a row carries `operator_union_id`, the worker first looks for `<session_root>/<operator_union_id>.json` before falling back to the global envs. `DINGTALK_DOCS_TARGET_NODE_URL` is only the default target, and checked rows with `DingTalk_target_node_url` can override it or supply the target on their own
- if Feishu/wiki remains primary, DingTalk mirror setup problems now degrade to `dingtalk_sync=failed` instead of aborting the whole build; blank or placeholder `-` target values are treated as unset and fall back to the default target when one exists
- if you want successful Publish runs to hand their artifacts to the DingTalk delivery agent, set `AUTO_MANUAL_DELIVERY_OUTBOX_ROOT` to an ignored directory (the repo ignores `/output/`); [`../tools/delivery_outbox.py`](../../tools/delivery_outbox.py) then drops the print PDF, handoff zip, Word, and Markdown into `<root>/<job_id>/` with an immutable `delivery_manifest.json`, and the row records `delivery_outbox=ok|skipped|failed` alongside `dingtalk_sync=*`. `skipped` means the target is not listed in [`../data/dingtalk_delivery_map.csv`](../../data/dingtalk_delivery_map.csv) and is a normal state; a delivery problem never fails a build whose artifact already reached the knowledge base. Verify a drop by hand with `python -m tools.delivery_outbox --manifest <root>/<job_id>/delivery_manifest.json`
- for local polling automation on Windows, schedule [`../scripts/process_build_queue.ps1`](../../scripts/process_build_queue.ps1) instead of calling `python build.py process-build-queue ...` directly, so the scheduled run inherits the repo `.venv`, the local `lark-cli` shim path, and the saved `FEISHU_PHASE2_*` user env vars consistently; use [`../scripts/process_build_queue_feishu.ps1`](../../scripts/process_build_queue_feishu.ps1) when you want the upload target fixed without touching env vars first
- for push-based immediate builds, add the `drive.file.bitable_record_changed_v1` event to the Feishu self-built app in Open Platform, publish the app change, then start [`../scripts/listen_build_queue.ps1`](../../scripts/listen_build_queue.ps1) at login or from the Windows Startup folder; the listener will auto-subscribe the current base token on startup

### 3.2 Create a Runtime Draft

```powershell
python build.py rst --config configs/config.ja.yaml --model JE-1000F --region JP --source runtime
```

This creates:

- [`docs/_build/JE-1000F/JP/rst/`](../../docs/_build/JE-1000F/JP/rst)

Use `--source runtime` when you want a fresh draft from template + data only.

If the model is only partially entered (for example a brand-new model still being populated), add `--draft-placeholders` to materialize anyway — missing required Spec_Master values render as `==MISSING:<FIELD>==` instead of aborting, so you can preview the layout and then fill the flagged rows. Strict builds (and `publish` / `release`) still fail fast with a report that names the model/region/lang and each missing binding. Do not use `--draft-placeholders` for publish.

### 3.3 Enter Review

```powershell
python build.py review --config configs/config.ja.yaml --model JE-1000F --region JP
```

This seeds:

- [`docs/_review/JE-1000F/JP/`](../../docs/_review/JE-1000F/JP)

After review starts, daily editing should happen in `_review`, not in `_build`.

### 3.4 Refresh Review After Data Changes

If you update any of these:

- [`data/phase2/Spec_Master.csv`](../../data/phase2/Spec_Master.csv)
- [`data/phase2/Spec_Footnotes.csv`](../../data/phase2/Spec_Footnotes.csv)
- [`data/phase2/Spec_Notes.csv`](../../data/phase2/Spec_Notes.csv)
- [`data/phase2/spec_titles.csv`](../../data/phase2/spec_titles.csv), generated from `Manual_Copy_Source.csv` plus Translation Memory `manual_copy` rows
- [`data/phase2/symbols_blocks.csv`](../../data/phase2/symbols_blocks.csv)
- [`data/phase2/troubleshooting_blocks.csv`](../../data/phase2/troubleshooting_blocks.csv)

The dormant known `Spec_Master` value repairs are tracked in [`../data/spec_master_value_repairs.csv`](../../data/spec_master_value_repairs.csv). The repair pass reads this CSV and fails closed on a missing, malformed, or duplicate repair key; do not add target/value patches back into Python.

Safety page note:

- US safety intro pages are maintained directly in [`docs/templates/page_us-en/safety_en.rst`](../../docs/templates/page_us-en/safety_en.rst), [`docs/templates/page_us-fr/safety_fr.rst`](../../docs/templates/page_us-fr/safety_fr.rst), and [`docs/templates/page_us-es/safety_es.rst`](../../docs/templates/page_us-es/safety_es.rst)
- the standalone user maintenance instructions page is maintained in the shared templates, for example [`docs/templates/page_shared/en/01_user_maintenance_instructions.rst`](../../docs/templates/page_shared/en/01_user_maintenance_instructions.rst), and each US/EU manifest includes it immediately before the `symbols` CSV page
- the JP manual maintains its safety intro in [`docs/templates/page_jp/safety_ja.rst`](../../docs/templates/page_jp/safety_ja.rst) through [`docs/manifests/manual_jp.yaml`](../../docs/manifests/manual_jp.yaml)
- edit those `safety_*.rst` files when a family's safety intro page needs copy/layout changes
- FridgeGuard EN/FR/ES Web safety leads share the declared `hb-safety-instruction` / `hb-safety-lead` signal-panel variants. Keep the risk table inside its protected figure, reuse the shared SVG triangles with explicit dimensions, and align the outer column edges; compact typography and full-width mobile stacking are owned by [the shared style contract](../../docs/renderers/contracts/STYLE_DEFINITION.md#1011-例外模板自带双分支的页安全页fcc).
- the detailed JP safety warnings remain in [`docs/templates/page_jp/01_meaning_of_symbols.rst`](../../docs/templates/page_jp/01_meaning_of_symbols.rst)
- the old `content_blocks.csv` safety source has been removed from the active repo flow

Parallel-language template note:

- for manually maintained parallel-language prose templates, treat the source-language page as the structure owner
- when that source-language page changes shared headings, section order, placeholders, includes, or `.. only::` model gates, update the derived-language counterparts in the same change before review/build
- current example: keep the `charging.rst` JE-2000E battery-pack `.. only:: model_je_2000e` block aligned across `page_us-en`, `page_us-es`, `page_us-fr`, and `page_zh`
- before you touch page templates for a new Markdown intake, fill out [`dev/manual_template_intake_checklist.md`](../dev/manual_template_intake_checklist.md) to decide manifest mapping, placeholder policy, and validation scope first

Carrier tag axes:

- a page can gate a body on four axes: `model_<model>`, `region_<region>`, `lang_<lang>`, and `category_<product line>`
- the category is `build.skeleton_family` in the config (`BP` for the battery-pack line, `MAIN` when undeclared), resolved by `resolve_category` in [`tools/page_contracts.py`](../../tools/page_contracts.py) — the same value the `category:` contract tier selects on, so a page's requirement and its `.. only::` body always agree
- both renderer planes emit it: Sphinx as `-t category_<value>` and the manual IR as a `category_<value>` base tag. Never add an axis to one plane only — `.. only::` omits an unmatched body silently, so a one-plane tag prints in the PDF and vanishes from IDML with no error
- prefer a category branch over cloning a page. Two carriers whose structure is identical and whose prose differs by product line belong in one file with two `.. only:: category_*` bodies; the parallel-language note above then applies once instead of twice

`symbols_blocks.csv` note:

- `image_path` stores the RST image reference path for each symbols-table icon
- when the phase2 authoring Base provides a `Figure` attachment, `sync-data` downloads it into `data/phase2/_attachments/symbols/` and writes that local file back to `image_path`
- use `block_type=table_row` for the normal symbol/meaning grid and `block_type=signal_row` for warning/caution/danger/note/tip signal metadata
- signal rows must include the four rendered `symbol_key` values `warning`, `caution`, `note`, and `tips`; add `danger` as a signal row for alert-label recognition when needed. Maintain visible signal labels and meanings in `Manual_Copy_Source.csv` with matching Translation Memory rows tagged `manual_copy`; `Localized_Copy.csv` is the generated runtime copy. The `label_*` and `aliases_*` columns in `symbols_blocks.csv` are compatibility mirrors for old variants and rewrite detection, not separate maintained copy; put editorial context in `notes`
- image alt text is derived from page titles, panel titles, `symbol_key`, or the corresponding signal-row `label_*`; do not maintain `copy_type=alt_text` rows in `Localized_Copy.csv`
- `Market` and `Model` select the target rows; `symbols_blocks.csv` does not use `Region`
- `Source_lang` stores the row's source-language code, using the same naming rule as [`Spec_Master.csv`](../../data/phase2/Spec_Master.csv)
- use `Market=Global` when one symbols row is shared across markets
- `sku_scope` is no longer used in [`symbols_blocks.csv`](../../data/phase2/symbols_blocks.csv)

`troubleshooting_blocks.csv` note:

- maintain the online TROUBLESHOOTING Base table as the source, then refresh with `python build.py sync-data --config configs/config.us.yaml --table troubleshooting --data-root data/phase2`
- use `Region`, `Model`, and `Is_latest` to select rows for the target manual; blank placeholder rows are ignored by the renderer
- keep title, intro, headers, widths, and header-row settings in the active language RST template: `docs/templates/**/10_troubleshooting.rst`
- keep error-code rows and localized corrective measures in the TROUBLESHOOTING Base table; the RST template exposes `{{ troubleshooting_rows_rst }}` where those rows are inserted

`Spec_Master.csv` note:

- Specification rendering preserves distinct localized row labels and label-footnote references even when records share `Row_key`. Equal labels/references retain multiline grouping; distinct subrows follow `Line_order` within their semantic group, not CSV storage order. Do not derive port labels from wattage or repair a missing source row with CSS.
- in Feishu, maintain `Page=specifications` rows in `规格参数明细` and maintain non-spec page placeholders in `页面占位参数`; `sync-data --table spec_master` reads those two source tables and writes the local read-model CSV
- `spec_row_key` is the first read-model key and `document_key` remains the target dimension field
- the `Page` column may now hold a comma-separated page list
- use `Product overview` for Product overview-only page-value rows
- use `Product overview, specifications,` when a row is intentionally shared by both pages
- `Row_label_source`, `Param_source`, and `Value_source` are the shared source-text columns; they should hold the row's source-manual text
- `Source_lang` stores that source-language code explicitly; use values such as `en`, `ja`, and `zh`, and do not rely on `Region` to infer it
- `document_key` is a derived helper column and may use either `[Model]_[Region]` or `[Model]_[Region]_[Source_lang]`
- `Row_order` is now the explicit row order inside each `document_key + Page + Section`, while `Line_order` controls the line order inside one logical row
- `Line_order` is required for rebuilds; use `1` for single-line rows and `1`, `2`, `3`, ... for multi-line rows under the same logical parameter
- generated `spec_titles.csv section_order` can hold the default order for visible spec sections, but a filled `Spec_Master.csv Section_order` overrides it
- `project_code` / `项目代码` is no longer part of `Spec_Master.csv`; target rows by `Region` + `Model`
- if a CLI/build target passes a document-key style model such as `JE-1000F_JP` or `JE-1000F-JP`, spec lookup first normalizes it back to the base model `JE-1000F` and still chooses rows by the explicit `Region`, so `JP` targets stay on `JP` spec rows
- `Row_label_en`, `Param_en`, and `Value_en` are no longer supported; rename them to `*_source` before importing or checking the sheet
- `Row_label_footnote_refs`, `Param_footnote_refs`, and `Value_footnote_refs` hold comma-separated `Footnote_id` values; do not handwrite `①②③` into the visible spec text columns

`Spec_Footnotes.csv` note:

- keep one row per reusable footnote definition
- CSV/PDF and IDML readers share the same reference-ID deduplication and numeric
  marker formatting. Put reference IDs in the desired order; repeated IDs print
  once. This shared rule does not alter target/language selection or text fallback.
- use `Footnote_id` as the stable reference key
- use `Footnote_order` to control the rendered superscript order
- keep `Type=Footnote` in the synced Feishu-backed rows so downstream renderers preserve the explicit trailer type
- keep only plain footnote body text in `Text_*`; the renderer derives the visible superscript marker automatically
- `project_code` / `项目代码` is no longer part of `Spec_Footnotes.csv`; target rows by `Region` + `Model`

`Spec_Notes.csv` note:

- use this file for bottom-of-spec notes that are not tied to a superscript reference
- use `Note_id` as the stable note key and `Note_order` as the rendered order
- keep `Type=Note` in the synced Feishu-backed rows so downstream renderers preserve the explicit trailer type
- keep only plain note text in `Text_*`
- when both note and footnote blocks appear at the bottom of one spec page, the final display order follows the template named by the `spec` row of the `page_registry.csv` the build reads (each frozen `manual_sources/.../phase2` source carries its own; [`../data/phase2/page_registry.csv`](../../data/phase2/page_registry.csv) serves every live target):
  - [`../docs/templates/spec_template.rst`](../../docs/templates/spec_template.rst), the default, puts the notes (such as the ※ USB Type-C trademark note) first
  - [`../docs/templates/spec_template_footnotes_first.rst`](../../docs/templates/spec_template_footnotes_first.rst) puts the footnotes first, for sources whose print sets them first; [`../tests/test_spec_notes_order.py`](../../tests/test_spec_notes_order.py) lists the frozen sources that name it
  - the two templates differ only in the order of their two HTML trailer placeholders, so the Web and the Word bundle (which takes its trailer order from the HTML) follow the named template, while the LaTeX branch, and with it the PDF and IDML output, is the same; keep the files otherwise identical (the test checks it)

run:

```powershell
python build.py sync-review --config configs/config.ja.yaml --model JE-1000F --region JP
```

By default this updates data-driven files in the review bundle without resetting the entire review text.

That same parameter-only sync now also runs automatically before `check`, `html`, `word`, `pdf`, and `publish` when the target already builds from review.
Placeholder-backed RST pages keep manual review prose, while parameter-driven lines are refreshed from runtime.
That sync now also refreshes `generated_page` placeholder files under `page/*.rst`, so final review builds do not keep stale placeholder text after runtime/generated data changes.
If approved copy on a target-specific page must remain byte-stable, list its exact relative path under `sync_preserve_paths` in that review bundle's `manifest.json`. Protected paths are skipped even when they are data-driven or named with `--page-file`; the sync manifest records them in `last_sync_preserved_files`. The field accepts only relative `.rst` paths under `page/` or `generated/`. Remove the declaration before an intentional page refresh, or use `review --refresh-review` for a deliberate full reseed.
When a single-language build points at a merged review branch and only `docs/_review/<model>/US/` or `docs/_review/<model>/EU/` exists, that automatic sync falls back to the merged review root instead of skipping the refresh, then remaps shared-family review pages onto the requested single-language page layout.
For the single-language US English config, the canonical review root is `docs/_review/<model>/US/en/`; for `configs/config.pt-br.yaml`, it is `docs/_review/<model>/pt-BR/pt-BR/`; for the single-language EU configs, the canonical review roots remain `docs/_review/<model>/EU/<lang>/`. Do not use or recreate the old shared single-language `docs/_review/<model>/<region>/page/**` layout. For the merged `configs/config.us.yaml` / `configs/config.eu.yaml` queue/review flows, the canonical shared review roots are `docs/_review/<model>/US/` and `docs/_review/<model>/EU/`.

Useful variants:

```powershell
python build.py sync-review --config configs/config.ja.yaml --model JE-1000F --region JP --sync-scope generated
python build.py sync-review --config configs/config.ja.yaml --model JE-1000F --region JP --page-file 02_whats_in_the_box.rst
```

### 3.5 Build from Review

Once `_review` exists, these commands use review content by default because `--source auto` overlays review on top of the runtime bundle:

```powershell
python build.py check --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py html --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py word --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py pdf --config configs/config.ja.yaml --model JE-1000F --region JP
python build.py all --config configs/config.zh.yaml --model JE-2000E --region CN
```

`check` now also catches stale foreign model names and contract-required spec keys, required page-value selectors, and assets.

PR review-preview note:

- when a PR changes `docs/_review/<model>/<region>/`, the review-preview workflow derives that exact target from the diff and uses the same target-aware language/config matching as the queue. A target-specific declaration wins before the shared regional fallback, so `JBP-2000B / US` resolves to `configs/config.bp-us.yaml` while ordinary US host targets keep the MAIN config.
- when a PR changes the zh manual family under `docs/templates/page_zh/`, `docs/templates/recipes/zh/`, or `docs/manifests/manual_zh.yaml`, the preview tool still switches the default landing target to the config-derived CN runtime target; the packaged workspace continues to include every existing review model
