# New Region Line — Setup Map

The complete surface for bringing up a `(Model, Region, Language)` line, with the
exact files, Feishu tables, `lark-cli` recipes, and command order. Worked example
at the end is the **KR JE-1000F ko** line (2026-07).

## Data flow (know this first)

```
规格书 PDF ──(extract + 字段映射规则表)──▶ 入库表(staging, operator confirms 确认=TRUE)
                                                     │  (manual promote)
                                                     ▼
Feishu source tables ──(build.py sync-data)──▶ data/phase2/*.csv ──(build.py check/build)──▶ manual
  · 规格参数明细 (spec rows, Page=specifications)
  · 页面占位参数 (generated-page placeholders: 03/05/12)
  · symbols_blocks / lcd_icons / troubleshooting (localized content, column-per-language)
  · manual_copy_source (+ Translation_Memory) ──derives──▶ Localized_Copy.csv, Status_Words.csv
  · dictionary tables: document_key, Region, Row_key, Slot_key
```

Two write categories, per AGENTS.md:
- **Repo** (this branch): config, manifest, templates, code, `page_registry.csv`.
- **Feishu source tables** (approval-gated F6 path in principle; in practice
  operator-confirmed rows via `lark-cli`): all the phase2 + dictionary + TM data.
`data/phase2/*.csv` are **sync snapshots** — most are gitignored (except
`page_registry.csv`). Never hand-edit the snapshots; edit the source + re-sync.

### ⚠️ Repo changes go to `auto-manual`, not the `Hello-Docs` mirror
`Bingboom/Hello-Docs` is a **one-way, destructive mirror** of `Bingboom/auto-manual`.
`.github/workflows/sync-hello-docs.yml` fires on every push to **auto-manual/main** and
runs `rsync -a --delete --exclude '.git/' source/ mirror/` — so Hello-Docs/main is
force-overwritten and **any change committed only in Hello-Docs is deleted on the next
sync**. All repo-side changes above MUST be committed to **`auto-manual`** and PR'd into
`auto-manual/main`; the mirror receives them after merge. `git remote -v` before you
commit. On this machine auto-manual is at `../auto-manual`; port from a Hello-Docs
checkout via an isolated worktree that leaves any in-progress branch untouched:
```
git -C ../auto-manual fetch origin
git -C ../auto-manual worktree add -b <branch> /path/to/wt origin/main
# apply repo changes in the worktree (git am the patches, or edit directly), validate, push, PR into auto-manual/main
git -C ../auto-manual worktree remove /path/to/wt   # when done
```
Feishu source tables (+ dictionary + TM) are **shared** and unaffected by the mirror.

---

## 1. Repo config + templates

Clone the closest existing single-language line. Non-EU single lines: `config.ja.yaml`
(jp-ja), `config.pt-br.yaml` (pt-br). EU-derived English source: `config.eu-en.yaml`
/ the EU manifests. KR cloned the **EU English** templates (source = EN).

Create:
- `configs/config.<region>.yaml` — `extends: config-bases/phase2-sync-base.yaml`.
  - `build`: `family_id`, `default_model`, `default_region`, `targets`, `languages: [<lang>]`,
    `include_lang_in_output_path: true`, `word_reference_doc`, `word_title`, `rst_substitutions`
    (`MANUAL_LANGUAGE_SCOPE`, `WARRANTY_EMAIL`, `LEGAL_COMPANY_NAME`).
  - **`paths`: include the FULL block** (`docs_dir`, `structured_data_dir`,
    `layout_params_csv`, `page_registry_csv`, `page_blocks_dir`, `spec_master_csv`,
    `spec_footnotes_csv`, `spec_notes_csv`, `spec_titles_csv`, `page_manifest`).
    ⚠️ The minimal `config.pt-br.yaml` (only `page_manifest`) passes *validate* but the
    **build aborts** with `config missing paths.layout_params_csv`. Copy `config.eu.yaml`'s paths.
- `docs/manifests/manual_<region>.yaml` — clone the source-lang manifest
  (`manual_eu-en.yaml` for EN source); point `rst_include`/`generated_page` at the
  new template dirs; keep `csv_page` (symbols/lcd_icons/troubleshooting/spec) with
  `langs: [<lang>]`; reuse shared recipes (`recipes/eu-en`, `recipes/eu-shared-en`).
- `docs/templates/page_<base>-<region>/` ← clone `page_eu-en/` (safety, product_overview
  + operation_guide placeholders). Rename `safety_en.rst` → `safety_<lang>.rst`.
- `docs/templates/page_shared/<lang>/` ← clone `page_shared/en/`. These are the
  **to-be-translated source baseline** (English until translated).

## 2. Register a NEW output language in code

Only if the language is new to the repo. `renderers` resolve columns dynamically via
`_lang_suffix_candidates(lang)` with an `_en` fallback (lcd/troubleshooting), so no
renderer edits — but these enumerations DO need the language:

- `tools/signal_words.py` — add to `_SUPPORTED_LANGS`.
- `tools/sync_data_models.py` — add the per-language columns to the `columns` tuples:
  symbols_blocks (`label_<l>`,`aliases_<l>`,`text_<l>`), lcd_icons (`icon_<l>`,`icon_desc_<l>`),
  troubleshooting (`corrective_measures_<l>`).
- `tools/localized_copy.py` — `_LANG_TEXT_COLUMNS`: `"<l>": "text_<l>"`.
- `tools/manual_copy_source.py` — `LOCALIZED_COPY_COLUMNS` (+`text_<l>`),
  `LOCALIZED_COPY_TEXT_COLUMNS` (`text_<l>`→`<l>`), `TM_LANGUAGE_FIELDS` (`<l>`→`<l>`),
  and `STATUS_WORD_COLUMNS` (+`<l>`).
- `data/phase2/page_registry.csv` (**tracked**, not gitignored) — add `<l>` to the
  `langs` of the symbols/lcd_icons/troubleshooting/spec rows. Miss this and the
  csv-page builder returns `files=0` → `Missing source RST ... <page>_<l>.rst`.
- Update hardcoded expectations in `tests/test_sync_data.py` and
  `tests/test_manual_copy_source.py`.

## 3. Feishu data (base = phase2 `LD3lb4G1ua4GOVs1vxAc9W2enje`)

Identities (per hello-docs-machine-setup): **reads** need `--as bot`; **writes**
(`+field-create`/`+record-batch-create`/`+record-batch-update`/`+record-upsert`) use
default `--as user`.

### lark-cli recipes (gotchas that cost time)
- `lark-cli base +field-list --as bot --base-token <bt> --table-id <tid> --limit 500`
- `+record-list … --format json --jq "." --limit 200` returns **columnar** JSON
  (`data.fields`, `data.data` rows, `data.record_id_list`) and **paginates** — loop
  `--offset` until `has_more=false` (a single call caps ~one page; newly-added rows
  are on later pages).
- `--json @file` must be a **relative path inside cwd** (absolute → invalid_argument);
  stage payloads in the repo `.tmp/` and pass `@./.tmp/x.json`.
- `+record-batch-create` payload = `{"fields":[names], "rows":[[values]]}`.
- `+record-batch-update` = `{"record_id_list":[…], "patch":{field:value}}` (one patch
  for all; ≤200/call).
- Multi-select fields do **not** auto-create options on write ("not_found"): add the
  option first with `+field-update --yes` (full-PUT: send the complete field def incl.
  all existing options + the new one), then batch-update the rows.
- `sync-data --table` does **not** accept `translation_memory`; TM-derived files
  (`Localized_Copy.csv`, `Status_Words.csv`) regenerate on a **full** `sync-data` (no `--table`).

### 3a. Dictionary / master entries
- **Region** dict `tblvBsr8qGPjXWdA` — most regions already exist (KR=`recvg5S7r6JiU5`).
  Create if missing (mirror an existing region record).
- **document_key** dict `tbltnkDIdwiDOP7d` — create `<Model>_<Region>`; set the
  `Model` + `Region` **link** fields (`[{"id":"rec…"}]`); `Document_key` + `项目代码`
  are formulas/lookups (auto). Model JE-1000F record = `recvg5TQhZWVVm`.

### 3b. Spec params → `规格参数明细 tblPUFJqt2uGGvTT`
- Operator flow: extract PDF → map via **字段映射规则表 `tblHrelfzylJIRT2`** (取值规则:
  exclude/passthrough/default/manual/capacity/weight/dims_mm_to_cm/dc12/temp/cycle_life)
  → write rows to the **入库表 `tblIi0BEufjvGLIU`** (`document_key=<Model>_<Region>`,
  `Source_lang=en`, `状态`=✅直通/⚠️需确认, `确认` unchecked) → **operator confirms**
  in Feishu (may edit values + tick 确认=TRUE) → promote confirmed rows into the source table.
- Source-table rows need **link** fields: `Document_key_link`→document_key dict,
  `Row_key_link`→`tbl8yQfXYe3KKyAM`, `Slot_key_link`→`tblS7qyV1DTZkoNq`
  (`document_key`/`Row_key`/`Slot_key` are formula/lookup — not writable directly).
  Reuse an existing line's rows for the structural fields (Section/Section_order/
  Row_order/Line_order/Row_key_link/Slot_key_link), swap `Document_key_link` to the new
  dict id, and set `Row_label_source`/`Value_source`/`Param_source` from the confirmed
  intake values. Selects (Section/Source_lang/Is_Latest/Version/Page) as plain strings.
- **`product_name` is required** by the build but is NOT in the spec PDF (cover is an
  image) — operator must supply the display name.

### 3c. Page placeholders → `页面占位参数 tblEhqJVXiyKtnwq`
- Clone an existing line's ~28 rows (product_overview / operation_guide / storage /
  ups_mode); set `Document_key_link` to the new dict id; keep structural fields.
- **Region-specific rows** need the region's values, e.g. `ac_input/side.spec` and
  `ac_output/front.spec` carry voltage/frequency (KR = 60 Hz). Everything else
  (DC ports, USB, buttons, energy-saving, storage temps, UPS) is region-invariant.
- Miss this and generated pages fail with `MISSING_REQUIRED_SPEC_ROW`
  (total_output/main_power_button/energy_saving_*).

### 3d. Localized content (column-per-language, product-level)
- `symbols_blocks tblSZX8hBzpJLqAe`: add `label_<l>`/`aliases_<l>`/`text_<l>` (`+field-create`),
  fill content (placeholder `test` via `+record-batch-update`).
- `lcd_icons tblW5fCuJ6YdAcND`: add `icon_<l>`/`icon_desc_<l>`.
- `troubleshooting tblOmJoAfU35brkb`: add `corrective_measures_<l>`.
- **Market / Region tags** (else the region matches 0 rows):
  - symbols `Market` = **multi-select** — add the region option via `+field-update --yes`,
    then tag the EU/AU-set rows (`+record-batch-update`, patch list e.g. `["US","EU","pt-BR","AU","KR"]`).
  - troubleshooting `Region` = **text** — patch e.g. `"EU, AU"` → `"EU, AU, KR"`.
  - lcd_icons has no market column (applies to all).
- `manual_copy_source` → `Localized_Copy.csv`: derived; a new lang **falls back to the
  English source_text** (fine as placeholder). No table edit needed beyond the code
  registration in step 2.
- `Status_Words.csv` (lcd Off/On/Blink) is derived from the **CAT Translation_Memory**
  (base `Ji1hb5ub1aUbewsTljGccvx5nhc`, table `tblqtvNbgjDwR4ya`). That table **already
  has a `ko` column** (Off/On/Blink = 꺼짐/켜짐/점멸). For a genuinely new lang, add the
  TM column + values; then `STATUS_WORD_COLUMNS` (step 2) + a **full** sync surfaces it.

## 4. Sync

```
set -a; source .tmp/hello-docs-binding/binding.env.sh; export FEISHU_PHASE2_IDENTITY=bot; set +a
python build.py sync-data --config configs/config.<region>.yaml --table spec_master
python build.py sync-data --config configs/config.<region>.yaml --table symbols_blocks
python build.py sync-data --config configs/config.<region>.yaml --table troubleshooting
python build.py sync-data --config configs/config.<region>.yaml            # full run → TM-derived files
```

## 5. Validation → PR

```
python build.py check --config configs/config.<region>.yaml --model <MODEL> --region <REGION>
python build.py check --config configs/config.us.yaml --model JE-1000F --region US   # regression
python -m unittest
python tools/check_maintainability_guardrails.py
```
Then branch/commit/PR per AGENTS.md §8.6 (do not self-merge).

---

## KR worked example (reference values)

- Line: `config.kr.yaml` (family `kr-ko`, region `KR`, `languages:[ko]`, source EN),
  `manual_kr.yaml`, `page_eu-kr/` + `page_shared/ko/` (cloned from EU-en).
- `product_name` = `Jackery Explorer 1000`; `WARRANTY_EMAIL` = `hello.kr@jackery.com`;
  `word_title` = `|PRODUCT_NAME| 사용자 매뉴얼`.
- Spec A1 (2026-06-30) changed AC output to **220 V / 60 Hz / 6.8 A** (A0 was 230/50/6.5);
  AC input 60 Hz. Region-invariant params identical to AU except certs + AC freq/voltage.
- document_key dict `JE-1000F_KR` = `recvnZySykX01w`.
- ko content = placeholder: symbols/lcd/troubleshooting `test`; localized copy = English
  fallback; status words = real Korean (already in TM). Replace with real translations later.
- Result: `build.py check JE-1000F/KR/ko` → `[check] OK`; US/EU regression OK; 1172 tests OK.
  See PR Hello-Docs#3 and memory `hello-docs-spec-ingest-architecture`.
