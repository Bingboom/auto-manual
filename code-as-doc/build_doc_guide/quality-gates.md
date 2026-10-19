# Build guide: check gates (terminology, capability, language scope)

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

## 5.1 Terminology Gate

`build.py check` also scans each built bundle for wording the Style Guide has retired:

- `data/terminology_rules.csv` — one row per retired wording: `rule_id`, `lang`, `deprecated_regex`, the `preferred` replacement quoted back in the message, an optional `allow_regex` for contexts where the old form is deliberate (an intentional first-mention gloss, a placeholder token), and a `note` pointing at the Style Guide clause.
- Pages are matched by language: generated pages take the language from their `_<lang>` filename suffix, authored pages inherit the target's language, so a `ko` rule never fires on a German page. A single-language family that declares no per-target `lang` (the JP config, `languages: [ja]`) still resolves its authored pages to that one language; a multi-language family leaves unsuffixed pages unclassified.
- Japanese rules are keyed `ja` — the JP bundle's page suffix (`spec_ja.rst`) and the JP config's language — not the IDML `jp` prefix. `cover_jp.rst` therefore sits outside them; it carries only product naming. Python's `\b` does not break between kana and ASCII (`APPの` has no word boundary), so Japanese patterns use explicit `(?<![A-Za-z])…(?![A-Za-z])` lookarounds.

Findings surface as `TERMINOLOGY_DEPRECATED`, a warning-only code — a rule can be registered the day a wording is retired and its existing hits cleaned up afterwards without blocking builds. Flip it to a blocking code only once the tracked lines are at zero, the way the capability gate tightened.

The rule table is the machine-readable half of the Style Guide (飞书知识库「多语言语言资产规范」); when a clause there changes, update the matching row here in the same change.

The gate only sees built bundles. A retired wording sitting in the library stays invisible until some manual renders it — `python -m tools.lang_asset_sweep --terminology` reads Translation_Memory, Terms and the print source tables directly and reports those rows, including ones already marked `Approved`. Template hits are skipped there because the gate already covers rendered pages.

## 5.1 Capability Gate

`build.py check` validates each target against the product capability matrix:

- `data/model_capabilities.csv` — per-`Document_key` feature booleans, mirrored from the 文档构建表 checkboxes (说明书盘点 2026-07-06).
- `data/capability_known_missing.csv` — reviewed `Document_key,reason` exemptions for targets whose capability row is not yet mirrored; unlisted missing rows surface as non-blocking `CAPABILITY_ROW_MISSING` warnings.
- `data/capability_page_rules.csv` — capability -> chapter mapping. `scope=page` requires/forbids a bundle page stem; `scope=section` greps a regex inside matching pages. `required_when_true` / `forbidden_when_false` toggle enforcement per direction, so uncertain rules can be recorded without failing builds.
  The ordered `capability` values in this CSV are also the source for the `model_capabilities.csv` mirror header; do not add a capability to a second Python tuple.

Failure codes: `CAPABILITY_CONTENT_MISSING` (capability TRUE, chapter absent) and `CAPABILITY_CONTENT_UNEXPECTED` (capability FALSE, chapter present). `CAPABILITY_ROW_MISSING` is a warning-only inventory signal unless the target is listed in the known-missing ledger; missing capability rows continue to keep page selection fail-open.

The page assembler consumes the same capability names through manifest
`capability:` annotations. The current 17-manifest family inventory contains 24
UPS page entries, all bound to `UPS功能`; this is enforced by
`tests/test_capability_pages.py` so a new language or single-language carrier
cannot silently bypass assembly-time filtering.

`check` also runs the language-tree parity gate (`tools/check/docs_lang_parity.py`, Milestone I1): `LANG_PARITY_FOREIGN_SHELL` (a ko/ja/zh/uk page carrying almost no target-script text — an untranslated shell), `LANG_PARITY_FOREIGN_LANG_BLOCK` (language-tagged blocks such as `**FR IMPORTANT**` or `\HBApplyLang{xx}` outside the family's languages), `LANG_PARITY_MISSING_LANG_PAGE` / `LANG_PARITY_FOREIGN_LANG_PAGE` (per-language generated page set incomplete, or a leftover page from another language line). Pre-existing findings are registered in `data/lang_parity_known_exceptions.csv` (model, region, code, page, note) so only NEW drift fails; delete a row once its content decision lands.

## 5.2 Language Scope Gate

A family config's `build.languages` is the **union** across every model in that
region, not one model's shipping list: `configs/config.eu.yaml` declares six
languages because the EU line carries Ukrainian templates, while JE-1000F does
not ship Ukrainian. `data/model_languages.csv` holds the per-model answer, keyed
on the same `<MODEL>_<REGION>` document key the capability mirror uses:

- `Document_key,Project,languages,notes` — `languages` is a `;`-separated list
  of registry language codes (semicolon, because a half-width comma inside a
  CSV field has bitten this repo's contracts before).
- Resolution is an **intersection that preserves the family's declared order**,
  so the family config stays the only place that decides ordering and the table
  can only subtract.
- Fail-open, like the capability gate: no row keeps every family language, and a
  row that excludes *every* family language leaves the build unchanged and
  fails `check` instead.

`tools/model_languages.py` resolves the scope; `tools/gen_index_bundle_plan.py`
applies it before any page is planned, so an unshipped language's pages —
including its `csv_page` data pages (`spec_uk.rst`, `symbols_uk.rst`, …) — are
never materialized. Structural problems in the table (missing column, duplicate
key, blank cell, unregistered code) raise instead of parsing to a wrong set.

Pages that carry several languages *inside one file* — the prefaces — cannot be
handled by page selection. Those manifest entries opt in with `lang_blocks:
true`, and `tools/language_block_trim.py` drops the out-of-scope blocks
(`\HBLangTagLine{XX}` in `raw:: latex`, `**XX ...**` bold headers) while
preserving page-structure macros such as `\HBPrefacePageBegin` /
`\HBPrefacePageEnd`. The annotation is opt-in, never sniffed, because `**IT ...**`
is legitimate bold prose elsewhere. When nothing is out of scope the page text
is returned unchanged, so an untrimmed family keeps byte-identical output.
The US en/fr/es document manifests are a deliberate exception: IDML/Word/PDF
must retain all three preface languages. Their configs instead declare
`build.web_language_block_pages: {00_preface.rst: en}`. Only the Web source
materializer converts that setting into language-block metadata. During its
shared review overlay, the declared page is exempt from the ordinary whole-page
language filter even if its outer `\HBApplyLang` marker names English; the Web
projection then keeps only the requested en, fr, or es block.
Trimming the shared trilingual preface to `en` reproduces the hand-forked
`00_preface_single_language.rst` byte-for-byte after the bundle's own
empty-line-block normalisation — enforced by
`tests/test_language_block_trim.py`.

A trimmed target also overrides the `MANUAL_LANGUAGE_SCOPE` substitution with
the label derived from its resolved languages, so a five-language EU book no
longer prints "… / Ukrainian" on its preface. The derivation reproduces each
whole-book family's configured literal exactly
(`tests/test_model_languages.py`), and single-language derivative configs keep
their configured literal because they are not trimmed.

Materialized page names disambiguate duplicates with a positional `pNN_`
prefix (`p22_01_fcc.rst` is the fr copy of `01_fcc.rst`), and those names are
pinned outside the build: committed review branches use them as file names and
the approved reference-layout contract lists them as ordered `source_ref`s.
Inserting a manifest entry mid-list would therefore renumber every later
duplicate and irreparably break the contract (`reference_layout_rebind`
refuses a changed `source_ref` sequence). Print-only insertions — the US
book's `00_toc.rst` and `99_back_cover.rst` — declare `ordinal_neutral: true`
on their `rst_include` entries instead: the page materializes in place but
does not consume a numbering ordinal, so every existing `pNN_` name stays
stable. `tools/gen_index_bundle_plan.py` applies the skip; the annotation is
`rst_include`-only and validated like `lang_blocks`
(`tests/test_gen_index_bundle_plan.py` pins the numbering behaviour).
Background: the 2026-08-13/14 same-source-gate incidents, where reseeds
dropped these two pages because they lived only in a hand-edited review index.

Failure codes (`tools/check/docs_language_scope.py`):
`LANG_SCOPE_UNSHIPPED_LANGUAGE` (the scope row is disjoint from the family the
config declares — e.g. `configs/config.eu-uk.yaml` pointed at a model that ships
no Ukrainian) and `LANG_SCOPE_FOREIGN_SCRIPT` (a bundle page carries the script
of a *dropped* language, catching leakage with neither a `_<lang>` page suffix
nor a language tag). Only dropped languages are scanned, so an EU bundle's
allowed CJK identity literal is not treated as drift. The scoped language set is
also what the per-language contract, generated-page, identity and parity
collectors see, so a model that ships five of six family languages no longer
fails on the sixth's missing source data.

Every Sphinx run also feeds the **warning ratchet** (`tools/warning_ratchet.py`, Milestone I2): the warning stream is written to `<out>/sphinx-warnings.log`, sanitized (paths, line numbers, ANSI, and target-specific `docs/_build/<model>/<region>[/<lang>]/rst/` prefixes), and diffed against the committed baseline `data/known_warnings/<stream>-known-warnings.txt`. A warning in the baseline is registered debt; a warning not in it is news. Enforcement is staged: the in-build hook reports by default and fails only with `AUTO_MANUAL_WARNING_RATCHET=strict` (set `off` to silence); the standalone CLI `check` is always strict (new warning → exit 1, missing baseline → exit 2). Seed or refresh a baseline with `python -m tools.warning_ratchet update --stream sphinx-html --log <warnings.log>` and review the diff like code. Flip the default to strict once a few queue rounds have stable baselines.
