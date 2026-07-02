# Phase2 Source Tables — Function & Field Reference

> **Purpose.** A single reference for the Feishu (Lark) bitable source tables behind the manual build — what each table is *for*, how it is *keyed*, what its *fields* mean, how tables *relate*, and where each one *lands in `data/phase2/*.csv`*. Written as the baseline for ongoing **structure optimization** (e.g. the value-dedup work in [`spec_overview_value_dedup_proposal.md`](spec_overview_value_dedup_proposal.md)).
>
> **Snapshot:** 2026-06-07. Schemas drift — re-dump with `lark-cli api GET …/tables/<id>/fields --as bot` before relying on an exact field list.
>
> **Machine-readable contract:** [`../../data/source_table_contracts/phase2_source_tables.json`](../../data/source_table_contracts/phase2_source_tables.json)
> records the current automation-facing contract for source-table keys, snapshot
> files, intake targets, writeback fields, source-record index mapping, and
> guarded writer boundaries. Update it together with this reference whenever the
> online source-table structure changes.

---

## 0. Where these live & how they reach the build

- **Phase2 base** (app token `DOp8bczA8aGLhJsc5iMcOqOvnpg`, wiki node `JKVAwNWlbilFiXkFc99cmRMPnhd`, "文档构建") holds the master + content tables (`02_主数据_*`, `03_内容源_*`).
- **Translation_Memory base** is **separate**. Since the G4 base convergence (2026-07-02) the canonical live base is whatever `$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN` names (tables resolved by name); the old A/wiki mirror (app token `LUIcbxeKdaCY2rsEHwCcnVQSnUe`, wiki node `X3O8wCpXPifqGKkP2sYccyxznQb`, "多维表CAT") is a **read-only archive**.
- **Naming convention:**
  - `02_主数据_*` — **master / dictionary** tables (controlled vocabularies, model/region/project registries). Mostly small, referenced by `Link` + `Lookup` from the content tables.
  - `03_内容源_*` — **content source** tables (the actual manual text, per language).
  - `99_归档_* / 99_实验_* / 99_系统生成_*` — archived / experimental / system-generated; **not** documented here and not part of the live build.
- **Source of truth = the online tables.** `python build.py sync-data` pulls them down into `data/phase2/*.csv`; **every CSV is a sync artifact** — never hand-edit one (it is clobbered next sync). Fix the online row via `lark-cli --as bot` (reads need `--as bot`; the user identity lacks `base:record:retrieve`).
- **Language-column convention.** Content tables carry one column per shipped language. The EU family uses `en` (source) · `fr` · `es` · `de` · `it` · `uk`; other markets add `pt-BR` · `ja`/`jp` · `zh` · `ko`. Column spelling is **not** uniform across tables — note `uk` vs `ukr`, `ja` vs `jp` below. Normalizing this is itself an optimization candidate (§6).

---

## 1. Master / dictionary tables (`02_主数据_*`)

These are the controlled vocabularies and registries. They are **not** exported as standalone CSVs; their values reach the build either (a) resolved into the content CSVs through Feishu `Lookup` fields (`Row_key`, `Slot_key`), or (b) via config/target resolution (model · region · language · build-family).

### 1.1 `02_主数据_参数名` — Row_key dictionary · `tbl3Jgz9qqNltYPe`
The controlled vocabulary for **`Row_key`** (the stable identifier of a spec row / overview callout, e.g. `ac_input`, `usb_c`).

| Field | Type | Meaning |
|---|---|---|
| `Row_label_source` * | Text | Human label, source language (e.g. `1 x AC`). Primary field. |
| `Row_key` | Text | Machine key (e.g. `ac_input`). What content tables link to. |
| `Remark` | Text | Notes. |

→ Content tables hold `Row_key_link` (Link → this table) + `Row_key` (Lookup), so the key is maintained **once** here. Derived CSV: `row_key_mapping.csv`.

### 1.2 `02_主数据_Slot` — Slot_key dictionary · `tblTyB0kvvLjDneb` · **NEW (2026-06-07)**
Controlled vocabulary for **`Slot_key`** — the variant discriminator that disambiguates multiple rows sharing one `Row_key`. Created to fix the usb_c 30W/100W render-empty collision (both rows had blank `Slot_key` → identical `source_row_key` → one dropped).

| Field | Type | Meaning |
|---|---|---|
| `Slot_label_source` * | Text | Human label (e.g. `默认 (main)`). |
| `Slot_key` | Text | Variant key: `main` (explicit default for blank), `30w`, `100w`, `140w`, … |
| `Remark` | Text | Notes (e.g. "空 Slot_key 的显式默认槽"). |

> **Caveat — `Slot_key` means different things in the two content tables.** In **Spec_Master** it is the **port variant** (`30w`/`100w`). In **page_placeholders** it is the **layout placement** (`side.spec`/`front.label`). They are *not* the same key — this is why the value-dedup match is an explicit row-link, **not** a `Slot_key` join (see §4.6 and the dedup proposal §5).

### 1.3 `02_主数据_Document_key` — model×region registry · `tbl8FDno2WH4OvpO`
The catalogue of buildable documents.

| Field | Type | Meaning |
|---|---|---|
| `Document_key` * | Formula | `Model_Region` (e.g. `JE-1000F_US`). The document identity. |
| `Model` | Link | → product master. |
| `Region` | Link | → region master. |
| `Documents` | DuplexLink | Linked document/version records. |
| `项目代码` | Lookup | Project code (e.g. `HTE153`), via Model. |
| `Description` | Text | Notes. |

### 1.4 `02_主数据_产品信息表` — product master · `tblAxOQ0FdpIYkcq`
Per-model metadata.

`Model` * · `是否支持加电包` (battery-pack support, Y/N) · `项目代码` (DuplexLink → project) · `产品简称` (short name, e.g. `E1000V2`) · `商品名称_en` / `商品名称_jp` / `商品名称_zh` (commercial names) · `品类` (category) · `备注` · `最后更新时间`.

### 1.5 `02_主数据_项目信息` — project master · `tbl6h8xii3ujXhri`
Per-project ownership.

`项目代码` * · `产品经理` / `项目经理` / `系统工程师` / `包材设计师` (roles) · `文档分类` (doc class, e.g. 用户手册) · `备注` · `关联产品型号` (DuplexLink → models).

### 1.6 `02_主数据_语言` — language master · `tblfgX7fV5WoOQH5`
`缩写` * (code, e.g. `EN`) · `语言` (name, e.g. 英语（美式）) · `区域法规` (DuplexLink → regions where the language ships).

### 1.7 `02_主数据_区域法规` — region master · `tblkQ8S5ColGXPJD`
`Region` * (e.g. `CN`) · `Build_family` (SglSel, e.g. `cn-zh` — maps to `configs/config.<family>.yaml`) · `Langs` (DuplexLink → languages) · `对应语言` (Lookup) · `规制` (regulatory regime) · `备注`.

---

## 2. Content-source tables (`03_内容源_*`)

### 2.1 `03_内容源_规格参数明细` — **Spec_Master** · `tblTw54UzV4ry5VD`
The specifications-page rows (`Page = specifications`). The largest, most-structured content table.

- **Identity / keying:** a row is uniquely identified by the composite **`source_row_key`** =
  `document_key__vVERSION__PAGE__sSECTION_order__rROW_order__Row_key__SLOT__lLINE_order`
  (blank slot → `main`; computed in `tools/spec_master_sources.py`). Held as a formula online and recomputed by the build from the synced columns.
- **Controlled keys:** `Row_key_link` (Link → §1.1) + `Row_key` (Lookup); `Slot_key_link` (Link → §1.2) + `Slot_key` (Lookup). Document scope via `Document_key_link` / `Document_key`.
- **Ordering:** `Section_order`, `Row_order`, `Line_order`, section/page identifiers.
- **Per-language content (×6+ langs):**
  - `Value_<lang>` — the electrical spec value (e.g. `100 W max., 5 V⎓3 A, …`).
  - `Row_label_<lang>` — the row's left-column label (e.g. `1 × USB-C-Ausgang 100 W`).
  - `Param_<lang>` — parameter-name text where used.
- **References:** `*_footnote_refs` (Link → Footnotes/Notes) attach ①②/※ markers.
- **Workflow (manual, operator-only):** `参数填写` / `多语言复核` checkboxes — progress tracking, **not** build inputs.
- **NEW (dedup pilot):** Spec_Master is the **link target** of `page_placeholders.spec_value_link`; its `Value_<lang>` is the single source the overview lookup reads (see §4.6).

### 2.2 `03_内容源_页面占位参数` — **page_placeholders** · `tblhckTT7PfVBsuG`
The product-overview callouts and page-level placeholders (`Page = Product overview`, app-setup, etc.).

- **Same schema as Spec_Master** (identical field set) — it is a second editing surface, split by `Page`.
- **Both Spec_Master and page_placeholders sync-merge into one file: `Spec_Master.csv`** (there is no separate `page_placeholders.csv`).
- **Known redundancy:** for ports that appear on both the spec page and the overview, the localized **value** is stored in *both* tables → drift risk (observed on `ac_input`/`ac_output`). The fix-in-progress is the row-link + lookup dedup (§4.6, proposal doc). Pilot scaffold left in place: `spec_value_link` (Link → Spec_Master) + `Value_de_ref` (Lookup), usb_c JE-2000F_EU linked.

### 2.3 `03_内容源_Manual_Copy_Source` — EN copy source · `tbl9grwLXLmpmZ1t`
The **source-language (en) strings** for non-spec manual copy: page titles, section titles, status-word phrases.

`copy_key` * (e.g. `lcd_icons.page_title`) · `page_id` · `copy_type` (e.g. `page_title`, `section_title`) · `Market` · `Model` · `Source_lang` · `Is_Latest` · `Version` · `source_text` (the en string) · `notes` · `section_order`.

→ Localized **not** by per-lang columns here but by **Translation_Memory lookup on the en string** (§3). Drives the derived CSVs `spec_titles.csv`, `Localized_Copy.csv`, `Status_Words.csv` — these have no own online table; they are *computed at sync* from Manual_Copy_Source × TM. (This is why editing a title means editing Manual_Copy_Source **and** ensuring the TM holds the localized pair — change only one and the derived title silently keeps the old translation.)

### 2.4 `03_内容源_规格页Footnotes` — spec footnotes · `tbl34wpGJkMipCrg`
The ①②… footnotes under the spec table.

`Footnote_id` * · `type` · `Region` · `Model` (MulSel) · `Source_lang` · `Is_Latest` · `Page` · `Footnote_order` · `Text_<lang>` (`en`, `fr`, `es`, `de`, `it`, `uk`, `pt-BR`, `zh`, `ja`) · `Enabled`.
→ `Spec_Footnotes.csv`. Attached to spec rows via `*_footnote_refs`.

### 2.5 `03_内容源_规格页notes` — spec notes · `tbl1vhTHwllyMGCx`
The ※ notes (e.g. trademark notices). Same shape as Footnotes:
`Note_id` * · `Type` · `Region` · `Model` · `Source_lang` · `Is_Latest` · `Page` · `Note_order` · `Text_<lang>` · `Enabled`. → `Spec_Notes.csv`.

### 2.6 `03_内容源_Symbols` — safety symbols · `tbl5ZXEVAzDMrvXN`
The warning/caution symbol legend.

`symbol_key` * · `order` · `block_type` · `image_path` · `Figure` (Attach) · `Is_Latest` · `Market` · `Model` · then **three columns per language** — `text_<lang>` (meaning), `label_<lang>` (short label), `aliases_<lang>` — for `en`, `fr`, `es`, `pt-BR`, `de`, `it`, `uk`, `jp`, `zh` · `notes`. → `symbols_blocks.csv`.

### 2.7 `03_内容源_LCD icons` — LCD display legend · `tblDII3oyqFhQYHn`
The LCD-screen icon names + descriptions.

`icon_en` * · `No.` · `Model` · `figure` (Attach) · `icon_<lang>` (icon name) + `icon_desc_<lang>` (description) for `en`, `fr`, `es`, `de`, `it`, `ukr`, `jp`, `zh`, `pt-BR` · `Is_latest` · `Version` · `has_variables` · `variable_keys` (MulSel). → `lcd_icons_blocks.csv`.
> Descriptions may embed `{{*_BUTTON_LABEL}}` variables (resolved from §2.9/§2.10). Keep the literal button noun on localization — do **not** collapse it to a bare label. Note the column spelling `ukr` (not `uk`) and `jp` (not `ja`) here.
> Line-leading state words (`On:`/`Off:`/`Blink:` + their localized forms) render **bold** via the status-word safelist — see §3 (`是否为 status word`) and the mechanism in §4.7.

### 2.8 `03_内容源_TROUBLESHOOTING` — troubleshooting · `tblUSuk3Q5BKTdTh`
Corrective measures keyed by error code.

`No.` * · `Model` · `Region` · `Is_latest` · `Version` · `error_code` (e.g. `F0`) · `corrective_measures_<lang>` for `en`, `fr`, `es`, `pt-BR`, `br`, `de`, `it`, `ukr`, `jp`, `zh` · `render_preview_en`. → `troubleshooting_blocks.csv`.

### 2.9 `03_内容源_Variable_Defaults` — placeholder defaults · `tblRyRdqRg2MGVgH`
Default values for `|TOKEN|` placeholders used across templates (button labels, etc.).

`Variable_key` * (e.g. `AC_POWER_BUTTON_LABEL`) · `Model` (Link) · `Value` · `is_default` · `Model_key` (Formula). → `Variable_Defaults.csv`.

### 2.10 `03_内容源_Variable_Lang_Overrides` — per-language placeholder overrides · `tblkcXujDMGXnHMo`
Where a token's value differs by language (e.g. button `AC` → `CA` in French).

`Variable_key` * · `lang` · `source_value` · `Value`. → `Variable_Lang_Overrides.csv`.

---

## 3. `Translation_Memory` — sentence-pair memory · `tbl6gKPJPTvOcTWv` (separate base)

The bilingual TM: one row per source sentence, with its translation in every language, plus maintenance/audit logs and terminology links.

- **Translations:** `en` * · `fr` · `es` · `de` · `it` · `uk` · `jp` · `ko` · `pt-BR` · `zh` — keyed by the **`en` source string** (the primary). This is the key the build uses to localize Manual_Copy_Source strings (§2.3).
- **Scope / classifiers:** `Model` (MulSel), `用途标签` / `content_attribute` (MulSel).
- **`是否为 status word`** (SglSel) — `Y` marks the row as an LCD **state-word prefix** (`On`/`Off`/`Blink`). Its per-language columns are exported to `Status_Words.csv` and used to **bold** the matching `On:`/`Off:`/`Blink:` line-leads in LCD descriptions (§2.7, §4.7). The localized value here is the **authority** for that word — `icon_desc_<lang>` must use the same spelling or it won't bold.
- **Glossary:** `Glossary_term` (Link) + `term_<lang>` (Lookup, per language) — terminology consistency.
- **Logs (one pair per language):** `…维护Log` (maintenance) + `…校验Log` (audit), each in an **AI** and a **人工 (manual)** variant — the trail the `bilingual-tm-maintenance` skill writes.
- **Gotcha:** duplicate `en` rows break the sync's TM index (a stale dup can win and re-introduce an old translation). Keep `en` unique; reconcile + delete dups.

---

## 4. Cross-table mechanisms

1. **Controlled `Row_key` / `Slot_key`** — dictionary table (§1.1/§1.2) + `*_link` (Link) + `*` (Lookup) in the content tables. The key is maintained once in the dictionary; content rows reference it. Adding a variant = add a dictionary row, then link.
2. **`source_row_key` composite** (§2.1) — the row identity used to align source → output and to dedup. Built from `document_key` + version + page + section/row/line orders + `Row_key` + `Slot_key`. A blank `Slot_key` defaults to `main`; two rows that collapse to the same key clobber each other (the usb_c bug).
3. **Document scope** — `Document_key` (`Model_Region`, §1.3) links a content row to its model×region; `Model`/`Region`/`Market` MulSel columns gate which rows a given build includes.
4. **Footnote attachment** — `*_footnote_refs` (Link) from spec rows → Footnotes/Notes (§2.4/§2.5).
5. **Variable resolution** — templates emit `|TOKEN|` / `{{TOKEN}}`; values come from Variable_Defaults (§2.9) with per-language overrides from Variable_Lang_Overrides (§2.10).
6. **Value dedup (NEW, in progress)** — `page_placeholders.spec_value_link` (Link → Spec_Master) + `Value_<lang>_ref` (Lookup) makes the overview callout *derive* the spec value instead of storing a copy. Match is an **explicit per-row link**, not a key-join (the two tables' `Slot_key` differ in meaning — §1.2). Pilot proven on usb_c JE-2000F_EU; rollout pending — see [`spec_overview_value_dedup_proposal.md`](spec_overview_value_dedup_proposal.md).
7. **Status-word bolding** — in LCD icon descriptions (§2.7) a **line-leading state word** (`On:` / `Off:` / `Blink:` and its per-language translations) renders **bold** (e.g. `**On:** Wi-Fi connected.`). The bold safelist is the per-language column of every `Translation_Memory` row flagged `是否为 status word = Y` (§3), exported to the derived `Status_Words.csv` and read by `tools/csv_pages/renderers_lcd_icons.py`. Two correctness conditions (both bit us, fixed 2026-06-07):
   - **The matcher tolerates a typographic space before the colon.** French uses `Allumé :` (space / NBSP / narrow NBSP), so it matches `词[ws]:`, not only `词:` (PR #334). Without this, **no French status line bolds**.
   - **The content word must equal the canonical status word** for that language. The TM status-word table is the authority; if `icon_desc_<lang>` uses a different word it silently fails to bold (seen: fr `Allumé/Éteint` vs table's old `Activé/Désactivé`, de `Blinkt` vs `Blinken`, it left untranslated English `On/Off`). Fix = conform the content to the table per language (or correct the table when it holds the worse term, as done for fr `On`→`Allumé`).

---

## 5. Sync → `data/phase2/*.csv` mapping

| CSV | Source | Notes |
|---|---|---|
| `Spec_Master.csv` | **Spec_Master + page_placeholders (merged)** | Both content surfaces collapse into one file. |
| `Spec_Footnotes.csv` | 规格页Footnotes | |
| `Spec_Notes.csv` | 规格页notes | |
| `symbols_blocks.csv` | Symbols | |
| `lcd_icons_blocks.csv` | LCD icons | |
| `troubleshooting_blocks.csv` | TROUBLESHOOTING | |
| `Manual_Copy_Source.csv` | Manual_Copy_Source | en source strings. |
| `Variable_Defaults.csv` | Variable_Defaults | |
| `Variable_Lang_Overrides.csv` | Variable_Lang_Overrides | |
| `spec_titles.csv` | **derived**: Manual_Copy_Source × TM | section/page titles, localized via TM en-lookup. |
| `Localized_Copy.csv` | **derived**: Manual_Copy_Source × TM | other localized copy. |
| `Status_Words.csv` | **derived**: Manual_Copy_Source (status words) × TM | |
| `row_key_mapping.csv` | **derived**: Row_key dictionary | |
| `page_registry.csv` | **derived**: page metadata | |

The `02_主数据_*` masters and `Translation_Memory` have **no standalone CSV** — masters reach the build via lookups (their values land inside the content CSVs) or via config; TM is read at sync time to produce the derived CSVs above.

---

## 6. Known redundancy & optimization candidates

These are the structural smells this reference exists to track. None block the current build; they are debt to retire deliberately.

- **Spec value duplicated across Spec_Master ↔ page_placeholders** (§2.2). Active drift observed. **Fix decided (Option A) and piloted** — row-link + lookup; full rollout pending. → `spec_overview_value_dedup_proposal.md`.
- **Language-column spelling is inconsistent** across tables: `uk` (Footnotes/Notes/Symbols/TM) vs `ukr` (LCD/Troubleshooting); `ja` (Footnotes/Notes) vs `jp` (Symbols/LCD/Troubleshooting/TM). A build-time alias map hides it today; normalizing the columns would remove a class of "wrong-column" bugs.
- **Wide per-language tables.** Each content table grows a new column set per language (×1–3 columns each). Adding a language touches many tables. A long-format (one row per lang) or TM-backed model would scale better but is a large migration — note, don't rush.
- **Recently cleaned (2026-06-07):** `Slot_key_legacy` and `source_row_key_link` deleted from the content tables after re-pointing dependent formulas to the `Slot_key` lookup. The `No.` field (sparse, manually filled, not synced) is a remaining cleanup candidate pending an operator decision.
- **`Slot_key` semantic overload** (§1.2): the same field name carries "port variant" in Spec_Master and "layout placement" in page_placeholders. Tolerable now, but any cross-table automation must treat them as distinct — a future split (`Variant_key` vs `Placement_key`) would remove the footgun.

---

## 7. Maintenance

- Re-dump field lists with `lark-cli api GET /open-apis/bitable/v1/apps/<base>/tables/<id>/fields --as bot --format json` (a ready dumper lived at `/tmp/dump_schemas.py` this session).
- When a table's schema changes, update this file and
  [`../../data/source_table_contracts/phase2_source_tables.json`](../../data/source_table_contracts/phase2_source_tables.json)
  in the same change, then run `python3 -m unittest tests.test_source_table_contract`.
- Companion docs: [`spec_overview_value_dedup_proposal.md`](spec_overview_value_dedup_proposal.md) (the active dedup workstream) and [`System Evolution Strategy.md`](System%20Evolution%20Strategy.md) (long-term direction). The phase2 / TM editing skills are registered in [`AGENTS.md`](../../AGENTS.md) §7.
