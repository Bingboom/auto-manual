# Source map, Feishu access, and apply techniques

Read this while mapping a manual revision back to source. It captures where each kind of
manual content actually lives, how to read/write the Feishu side, the safe apply patterns,
and the scope decisions to surface.

## Contents
- [The two-track model](#the-two-track-model)
- [Content → source map](#content--source-map)
- [Feishu access recipe (lark-cli)](#feishu-access-recipe-lark-cli)
- [Apply techniques](#apply-techniques)
- [Decision checklist (surface to operator)](#decision-checklist-surface-to-operator)

## The two-track model

Manual content has two sources of truth:

- **Repo templates** — editable here, normal branch/PR. RST under `docs/templates/`,
  recipes under `docs/templates/recipes/`, and `configs/config.*.yaml`.
- **Feishu phase2 bitable tables** — the source for **everything** under `data/phase2/`.
  `build.py sync-data` regenerates `data/phase2/*.csv` FROM these tables, so **no CSV is
  ever the source**: a hand-edit to any `data/phase2/*.csv` is overwritten on the next
  sync, and the durable fix is always the **Feishu source row** (write it with `lark-cli`,
  below). Most CSVs are 1:1 table mirrors; a few are **derived** —
  `data/phase2/spec_titles.csv` (also `Localized_Manual_Copy`, status words) is built by
  `build_spec_title_rows` (`tools/manual_copy_source.py`) from the `manual_copy_source`
  table (en source rows) joined to **Translation_Memory** for the localized columns. So a
  section *title*'s de/fr/es/it/uk value comes from the TM row matched on its en source
  string — fix the TM row, not the CSV.

`sync-data` is **operator-gated**: its preflight requires `FEISHU_PHASE2_BASE_TOKEN`,
`FEISHU_PHASE2_SPEC_FOOTNOTES_TABLE_ID`/`_VIEW_ID`, `..._SPEC_NOTES_...`, `..._SYMBOLS_BLOCKS_...`,
`FEISHU_TRANSLATION_MEMORY_BASE_TOKEN`, and `FEISHU_PHASE2_IDENTITY=bot`. Those live only in
the operator's environment. So you cannot run a real sync or build a from-scratch baseline
for a not-yet-local target; that is the operator's step. You CAN read and write the source
rows directly (next section).

## Content → source map

Authoritative table ids live in `configs/config-bases/phase2-sync-base.yaml` (and
`eu-single-language-base.yaml`). Confirm there; the ids below are a convenience snapshot of
the phase2 base (wiki node `JKVAwNWlbilFiXkFc99cmRMPnhd` → bitable app token
`DOp8bczA8aGLhJsc5iMcOqOvnpg`).

| Manual content | Source | Keying / where |
| --- | --- | --- |
| Spec-table values, spec-row labels (capacity, ports, AC/USB counts, DC symbol ⎓, output specs) | **Feishu Spec_Master** `tblTw54UzV4ry5VD` | `document_key` (e.g. `JE-2000F_EU`) + `Page` + `Row_key` + `Slot_key`; per-lang `Value_source`(=en)/`Value_fr|es|de|it|uk|br`, `Param_*`, `Row_label_*` |
| Product-overview labels, side/front callout specs, app-setup step text, settings values | **Feishu page_placeholders** `tblhckTT7PfVBsuG` | same schema as Spec_Master |
| Symbol meanings ("keep away from fire", etc.) | **Feishu symbols_blocks** `tbl5ZXEVAzDMrvXN` | `symbol_key` + `Market`/`Model` (shared across markets/models); `text_<lang>`, `label_<lang>`, `aliases_<lang>` |
| LCD-icon names + state descriptions (LCD DISPLAY section) | **Feishu lcd_icons_blocks** `tblDII3oyqFhQYHn` | `Model` (shared, no Region/document_key); `icon_<lang>` + `icon_desc_<lang>` (descs may embed `{{*_BUTTON_LABEL}}` placeholders) |
| Troubleshooting corrective measures | **Feishu troubleshooting_blocks** `tblUSuk3Q5BKTdTh` | `Model` (often `ALL`) + `Region` + `error_code`; `corrective_measures_<lang>`. EU vs `US, pt-BR` are SEPARATE rows |
| Spec footnotes (① …), spec notes | **Feishu Spec_Footnotes** `tbl34wpGJkMipCrg`, **Spec_Notes** `tbl1vhTHwllyMGCx` | `Model`/`Region`; `Text_<lang>` |
| Spec section titles (e.g. "ENVIRONMENTAL OPERATING TEMPERATURE") | **Feishu Translation_Memory** `tbl6gKPJPTvOcTWv` (de/fr/es/it/uk) + `manual_copy_source` `tbl9grwLXLmpmZ1t` (en source row) | matched on the en source string (`en` field). `data/phase2/spec_titles.csv` is a DERIVED sync artifact — do NOT edit it. TM is a *separate base* (see recipe); prefer the `bilingual-tm-maintenance` skill to write it with maintenance/audit logs |
| Operation-guide narrative, charging/UPS/storage prose, app-setup static lines, in-the-box | **repo templates** `docs/templates/page_<region-lang>/05_operation_guide_placeholder.rst`, `docs/templates/page_shared/<lang>/{06_ups_mode,08_charging_methods,charging,09_storage_and_maintenance,12_app_setup_placeholder}.rst` | per language; literal text (some button refs are `{{…}}`/`|…|` placeholders → already resolved from data) |
| Product-overview callout layout, front/right-side panels, static part labels (Handle, LCD, …) | **repo templates** `docs/templates/page_<region-lang>/03_product_overview_placeholder.rst` | LaTeX `\HBOverviewPair{LEFT}{}{RIGHT}{}` block + a parallel non-LaTeX `list-table`; edit BOTH; shared across models for that language |
| Safety boilerplate headings, cover/preface, language-scope line | **repo templates** `page_<region-lang>/safety_*.rst`, `page_<region>/00_preface.rst`, `configs/config.<region>.yaml` `rst_substitutions.MANUAL_LANGUAGE_SCOPE` | — |

Notes that bite you:
- The SAME content type often appears in BOTH a `Product overview` page row and a
  `specifications` page row in Spec_Master (e.g. `usb_c`, `ac_output`) — fix the right one.
- Button *labels* come from data (`page_placeholders` CONTROLS rows); button *references*
  inside narrative are literal text in the `05`/`page_shared` RST. Both may need the same
  terminology change.
- A revision's content can be split across 4+ tables AND templates — that is why the
  residual scan exists.
- If a section *title* changed, the convergence scan must include a **Translation_Memory**
  dump (and `manual_copy_source`), not just Spec_Master / page_placeholders — the title
  lives in TM, so a spec/ph-only scan falsely reports convergence. Likewise never treat a
  green `data/phase2/spec_titles.csv` as proof; it is a derived artifact, not the source.

## Feishu access recipe (lark-cli)

`lark-cli` is installed (it is the same tool `sync-data` uses). The phase2 base resolves
from the wiki node:

```bash
# wiki node -> bitable app_token (obj_token)
lark-cli api GET /open-apis/wiki/v2/spaces/get_node \
  --params '{"token":"JKVAwNWlbilFiXkFc99cmRMPnhd"}' --format json
# -> data.node.obj_token  (phase2 base = DOp8bczA8aGLhJsc5iMcOqOvnpg)
```

**Translation_Memory lives in a DIFFERENT base** ("多维表CAT"), not the phase2 base — needed
for section-title / derived-CSV fixes:

```bash
# TM base: wiki node X3O8wCpXPifqGKkP2sYccyxznQb -> app LUIcbxeKdaCY2rsEHwCcnVQSnUe
#          table tbl6gKPJPTvOcTWv (view veweqW2fQv); rows keyed by lang fields en/de/fr/es/it/uk/jp/...
```

For TM writes prefer the `bilingual-tm-maintenance` skill: it updates the en-linked row,
appends the `<lang>维护Log`/`<lang>校验Log` fields, and verifies by read-back.

Read records (paginate all):

```bash
lark-cli api GET /open-apis/bitable/v1/apps/<app_token>/tables/<table_id>/records \
  --params '{"page_size":500}' --as bot --page-all --page-limit 0 --format json > dump.json
```

**Use `--as bot`.** The default `user` identity lacks `base:record:retrieve` and returns
permission error `99991679`. Field reads work under either identity.

Write a single record field (PUT), then verify by reading it back:

```bash
lark-cli api PUT /open-apis/bitable/v1/apps/<app_token>/tables/<table_id>/records/<record_id> \
  --data '{"fields":{"Value_de":"…new value…"}}' --as bot --format json
```

Practical rules:
- Build the JSON payload in Python (`json.dumps(..., ensure_ascii=False)`) and call lark-cli
  via `subprocess`, to avoid shell quoting issues with the `⎓` (U+2393) DC symbol, accents,
  apostrophes, and Cyrillic.
- **Fetch → substring-replace → PUT → GET-verify.** Never retype a long field; replace the
  exact OLD substring inside the fetched value so you preserve everything else.
- Resolve `record_id` by predicate (document_key + Row_key + content), not by hardcoding —
  ids differ per row and per environment.
- This is a *test* Feishu instance; still, every PUT changes source of truth. Apply only
  confirmed, in-scope deltas, and report each old→new you wrote.

## Apply techniques

- **Accents / diacritics (it especially):** replace whole words with a unicode word
  boundary so you do not corrupt valid words — e.g. `re.sub(r"(?<![A-Za-zÀ-ÿ])puo(?![A-Za-zÀ-ÿ])", "può", t)`
  matches standalone `puo` but never `puoi`. Apply the specific words the reviewer changed;
  do not blanket `e`→`è` (often intentionally left).
- **Context-dependent term renames (button names):** apply qualified forms BEFORE the bare
  form so the bare rule does not eat the qualified ones. Example (it):
  `"Pulsante di alimentazione CC/USB"→"Pulsante DC/USB"`, then `"…CA"→"…CA"`, then bare
  `"Pulsante di alimentazione"→"Pulsante POWER principale"`. Beware non-button homographs
  ("stazione/sistema di alimentazione" must stay).
- **Negative lookbehind for prefix-adding renames:** `POWER-Taste`→`Haupt-POWER-Taste` with
  `(?<!Haupt-)POWER-Taste` so you never produce `Haupt-Haupt-POWER-Taste`.
- **Placeholder vs literal:** if a button reference renders from `{{LABEL}}`/`|LABEL|`, the
  label update (done in data) already fixes it — do not also edit a literal that is not
  there. Conversely, dropping a redundant word before a placeholder ("il pulsante di
  alimentazione {{AC…}}" → "il {{AC…}}") fixes a double-word when the label itself contains
  the noun.
- **Section headings need the underline too:** changing an RST title means resetting its
  `===`/`---` underline to `len(new_title)` (over-length is allowed, under-length errors). A
  longer new title with the old underline breaks the build.
- **Cross-language contamination is a real data bug:** e.g. German `Param_de` holding Spanish
  text and vice-versa (columns swapped at the source). Fix by swapping back, and flag it.
- **Region/locale terms are not universal:** an EU-Spanish preference (`coche`→`vehículo`,
  `falla`→`fallo`) should NOT be blindly applied to `US, pt-BR` (Latin-American) rows.

## Decision checklist (surface to operator)

Lay these out and wait — do not decide them yourself:
- **Model scope:** does the revision data even exist for this target locally? (Often the
  revised target lives only in Feishu, not yet synced — that is EXPECTED, not a blocker.
  Such targets are bitable-driven and build **online-first via the queue**
  (`process_build_queue` runs `sync-data` before building); do NOT assume you must
  hand-add a `config.*.yaml` target. Stale/missing local `data/phase2` rows are normal.)
- **Region scope:** EU-only, or also US/JP/CN/pt-BR? Same-looking terms can be locale-correct
  elsewhere.
- **Sibling models:** apply a shared-terminology fix to other models' rows (e.g. JE-1000F_EU,
  JE-2000E_EU) for family consistency, or scope strictly to the revised model?
- **Intentional non-changes:** some tracked changes are reviewer artifacts (a working
  version label) or contested (one language's reviewer "corrected" a spec count another kept).
  Confirm spec-fact changes against the product, not the docx.
- **Numbering / structural cosmetics:** confirm before adding/removing step numbers, etc.
