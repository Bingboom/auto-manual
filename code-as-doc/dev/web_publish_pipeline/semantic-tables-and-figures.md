# Web Publish pipeline: semantic tables and frozen figures (§1.1)

Status: active · Part of the [Web Publish pipeline](../web_publish_pipeline.md) contract; its index lists the
other sections. Change this part of the contract here, not in the hub.

## 1.1 Semantic tables and frozen figures

The Web profile renders explicitly declared specification sections across
targets. `h2.hb-spec-section` with a source-authored
`.hb-spec-section-text` title and its adjacent `hb-spec-table` or
`manual-spec-table` are the declaration. The Web adapter in
[`web_spec_component.py`](../../../tools/web/spec_component.py) projects their
label/value rows through the existing `HB-TABLE-SPEC` ComponentSpec and public
`web_spec_table_projection`. It keeps inline markup, row order, label spans,
references and adjacent footnotes/safety copy. Only the declared decorative
heading bullet is removed; the Web theme supplies its heading marker.

This semantic path runs before figure routing and does not require an artwork
grant. A matching filename or an ordinary two-column table is insufficient;
missing declarations stay unchanged, while malformed declared sections fail
the build. Section and reference counts come from the source, not a target
constant. `web_manual.json.specifications` remains readable for serialized
compatibility but its old `spec_*`, four-section and two-reference selectors
no longer route or constrain rendering. The `{spec-table}` Markdown directive
already consumes the same public adapter and requires no new interface.

Troubleshooting follows the same semantic-before-figure boundary. In the
RST-to-Web bundle path, [`word_bundle_html.py`](../../../tools/word/bundle_html.py)
resolves the current target's `plan_materialized_pages` once and passes a
declaration for the exact materialized paths of `CsvPage(page="troubleshooting")`.
The existing planner owns language/capability selection and `slot_id` naming;
the Web adapter does not infer intent from filenames, translated headers or
error codes. This also covers unmarked `review-asis` snapshots without editing
their reviewed RST. Explicit `table.hb-troubleshooting-table` declarations can
scope individual tables in mixed HTML fragments.

[`web_troubleshooting_component.py`](../../../tools/web/troubleshooting_component.py)
shares validation and DOM projection with `{troubleshooting}`. It consumes the
existing `HB-TABLE-TROUBLESHOOTING` CSS; that style binding is **not** a registered
ComponentSpec, and this adapter adds no public schema. The standalone Markdown
extension pack includes this module and is tested outside the repository's
import path. Directive headers and its optional label remain source-owned;
the existing English default headers and ` / ` step syntax remain supported.

A declared CSV page must have exactly one table. Each declared table requires
two nonempty, unspanned header cells and at least one two-cell data row; missing
or ambiguous declared content fails with its source reference. An unmarked
fragment without a page declaration stays unchanged. When an explicitly
declared table has no `thead` (the current JP template uses `header-rows: 0`),
its authored first row becomes `thead`/`th scope="col"`. Existing headers,
ordered body rows, lists, line blocks, links and inline markup are retained.
The existing figure scroll surface gains `tabindex="0"` for keyboard access;
its accessible label comes from the directive label or source header cells.
`web_manual.json.troubleshooting_table` remains readable for serialized
compatibility, but its source patterns no longer route rendering and there is
no fixed error-code inventory. CSV readers, templates and review snapshots
are unchanged.

`figure_targets`, per-figure source patterns, target instances and frozen
composite approval/hash checks retain their existing scope. Warranty is a
shared semantic composition and runs independently of that artwork grant: its
source-owned localized unit and label are retained while the Web adapter supplies
the common 3-year/2-year badge treatment. LCD, specifications, troubleshooting
and Inbox likewise follow their own declaration/semantic admission rules. For a
target outside the frozen figure contract, Web starts at its manifest's first
included page; it does not invent a preface. The frozen US target retains its
preface rule. Cover/TOC/back-cover exclusions remain in force.

Figure carrier choice is part of the component contract, not an extraction
default:

- Product Overview, the five Operation panels, and the four Charging panels use
  locale-matched `localized-full-page` composites. Their visible callouts,
  prerequisites, connection labels, and Operation `On` / `Off` instructions are
  intentionally embedded in the approved crop. Extraction may crop the panel but
  must not redact that localized text. The section heading remains live HTML.
- The Operation LCD screen-mode block is deliberately hybrid: only the
  market-correct product/display artwork is an image, while the six-row state /
  action / explanation table remains searchable, responsive HTML. A screenshot
  of the complete LCD table is not a valid replacement.
- Specifications, troubleshooting, the LCD-icon glossary, Warranty and other
  semantic tables remain live components unless their own contract explicitly
  says otherwise.

Target reuse follows inheritance plus narrow overrides. A child Product Overview
instance may `extend` a validated base instance; lists whose members have stable
`id` values merge by `id`, so the child can override only target identity,
market-specific artwork keys and locale declarations while inheriting callout
order and Web/IDML geometry. Ordinary lists still replace as a unit. Composite
locale resolution prefers the materialized document language; filename patterns
remain only a legacy fallback. Coverage provenance identifies an approved
composite by `asset_key + locale + content_sha256`, including the case where two
locales intentionally share identical bytes.

`JE-1000F / EU` is admitted to the figure contract and its Overview instance
extends `je1000f-us-v1`; EN/FR/ES/DE/IT use one shared component definition with
locale-specific composite bindings. EU does not inherit the US-only preface
rule. Extracted PDF composites remain quarantine candidates until pixel review
and normal manifest/registry approval; contract admission alone is not asset
promotion.

The App connect-result figure is the one EU composite bound as `locale=shared`.
The EU/UK print repeats the same English screens in all five language blocks,
so one panel serves EN/FR/ES/DE/IT, as the US `reference.app-connect-result`
does. As an App UI crop, its recipe entry stays quarantined under the
App/QR/URL/localized-UI recipe gate; approved `04_资产定义` and `04_资产导出物`
rows make it Web-buildable. For print, the reviewed promotion
`je1000f-eu-app-ui-v1` resolves `asset:app/add_device` and
`asset:app/connect_result` to the EU print's own screens for JE-1000F/EU;
review pages that still carry raw `common_assets/app/*.png` paths keep the
shared JP-market images until they switch to `asset:` URIs.
The frozen JE-1000F/EU 2.0 review copy made that switch on 2026-09-24 (the
FR/ES/DE/IT/UK pages; the EN page already used the URIs), so a Web rebuild from
it carries the EU export, not the JP screenshot, as the connect-result figure's
hidden semantic image in all five routes.

The in-box unit, LCD display mode and UPS figures are ordinary registry art, not
composites. Their JE-1000F/EU target overrides (`in_the_box/je1000f_eu/main_unit1`,
`operation/je1000f_eu/lcd_mode` and `operation/je1000f_eu/ups_mode`, each with an
`_en` sibling; recipe `manual_je1000f_eu_uk_20260618_block_art.json`) vary by
language: EN takes the English block (BS 1363 sockets), FR/ES/DE/IT/UK the French
block (EU sockets). The frozen review copy switched those references to `asset:`
URIs on 2026-09-26, so a Web rebuild shows the print's own art in those three
visible figures on all five routes instead of the shared art (a US-outlet unit and
another, wheeled model).

`JE-2000F / EU` binds its App connect-result panel through its six per-language
`web-illustrations/v1` manifests rather than composites. The six language blocks
of its EU/UK print place the same five screen bitmaps, so one panel cut from the
EN block (p21: the three screens with their embedded 2.3/2.4/2.5 captions)
replaces `connect_result.png` in every language, and the localized "screenshots
are for reference only" sentence stays live text. Its recipe,
`data/asset_recipes/manual_je2000f_eu_web_app.json`, keeps the crop quarantined
under the same gate: the hash-pinned manifest entries are its only route onto
the page, and the frozen source binds the recipe as `app_asset_recipe`.
`JE-3000C / EU` does the same for its fr/es/de/it/uk routes through five
one-entry manifests, cut at the 12x scale of its English App panels; English
keeps its own approved panel. `JE-2000E / EU` replaces both App figures of its
fr/es/de/it/uk routes the same way (add-device 2.1/2.2 and connect-result). The
print's control-panel box below the add-device screens carries per-language
button labels, so since 2026-09-24 EN/FR/ES/DE/IT (and since 2026-09-26 UK) each
bind their own block's crop of the screens together with that box, and the
page's four label lines become covered annotations (kept as the figure's alt
text). Since 2026-09-26 the German and Italian pages also name those buttons as
their print blocks do (DE `POWER-Taste`, IT `CC / USB`). The UK block prints
`AC1` for the AC2 button, so its crop re-sets that one character from the
print's own glyphs (`redact_text_region`, then `copy_pdf_region`). The operator
accepted that correction on 2026-09-27, so its registry row is `✅成品` like the
other panels.
`JE-3600A / EU`, whose English route also showed the JP screenshot, binds one
shared connect-result panel for en/fr/es: an extra entry in its English manifest
and one-entry fr/es manifests. Earlier
Web App panels for JE-1000H, JE-2000E and JE-3000C were recipe-approved only
because their keys carry none of the gate's tokens. Since 2026-09-25 the
JE-1000H/EU (download, add-device and connect-result, six languages) and
JE-3000C/EU English App panels are quarantined with App risk tags, keeping
their keys, files and hashes. `tests/test_app_figure_gate.py` requires every
manifest entry that replaces an App setup image (`download.png`,
`add_device.png`, `connect_result.png`) or carries an `app-` reference id to
resolve to a quarantined recipe asset. The JE-2000E/EU English connect-result
panel was quarantined the same way on 2026-09-26, after #1258 moved its
add-device figure to the App recipe, so the test lists no exceptions.

The App add-device figure of `JE-2000F / EU` (six routes), `JE-3000C / EU`
(fr/es/de/it/uk) and `JE-3600A / EU` (en/es/fr) is, since 2026-09-24, each
language block's own crop of the 2.1/2.2 screens together with that model's
control-panel box and its printed button labels (quarantined App recipe entries
`web/<model>/eu/<lang>/app_add_device_panel`). It replaces the shared
composition of generic App screens with the JE-1000F/US control-panel drawing,
and on the JE-2000F and JE-3600A English routes a crop of the control-panel box
without the screens. The page's button-label lines become covered annotations
(the figure's alt text). The JE-3000C English route already had its own complete
panel.

Every newly generated Web `manual.ir.json` contains a
`metadata.web_figure_coverage` payload with schema
`web-figure-coverage/v1`. It audits actual rendered Overview, Operation and
Charging slots through one status vocabulary:

| Status | Meaning |
| --- | --- |
| `finished-panel` | A `web-illustrations/v1` entry replaced one or more source images with one approved, hash-pinned panel. |
| `approved-composite` | A target/locale/source-matched `web-composite-manifest/v1` asset overrides the semantic fallback. |
| `editable-fallback` | The governed semantic figure remains live/searchable because no approved composite was bound. |
| `missing` | The rendered source image has neither an approved finished panel nor an admitted semantic fallback. |

The inventory records page, section and stable slot identity; approved rows
also retain their packaged path and SHA-256 evidence. Its totals are validated
again before IR replay. It is an audit, not an automatic approval gate: known
asset debt remains buildable and visible. A missing row is closed only by
adding an approved manifest/recipe asset; copying another region's panel or
adding page-specific Python/CSS is not a valid override.

Local verification uses the same Markdown-to-Sphinx path without a queue or
online source update. For example, with a separate staging directory:

```bash
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md --config configs/config.us.yaml --model JE-1000F --region US --source review-asis --data-root tests/fixtures/phase2 --staging-root .tmp/web-check --no-clean --skip-root-index
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md --config configs/config.ja.yaml --model JE-1000F --region JP --source runtime --data-root tests/fixtures/phase2 --staging-root .tmp/web-check --no-clean --skip-root-index
python -m tools.readthedocs_source --build-root .tmp/web-check/docs/_build --output-dir .tmp/web-check/docs/_build/rtd
python -m sphinx -b html .tmp/web-check/docs/_build/rtd .tmp/web-check/html
```

Inspect both targets at narrow and wide widths, compare all ordered copy and
asset hashes against the baseline, and compare document-profile outputs
separately. This is local rendering evidence; it does not grant asset approval,
change JP D1–D4 or promote production eligibility.
