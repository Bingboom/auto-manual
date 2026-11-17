# Web Manual Agent Authoring — Reference Checklist

Supporting reference for [`SKILL.md`](../SKILL.md).

## 1. Stage Commands & Entrypoints

| Stage | Purpose | Command / Module |
| --- | --- | --- |
| Stage 0 | Preflight inventory (siblings, assets, CSS, components) | `python .agents/skills/web-manual-agent-authoring/scripts/authoring_preflight.py --model <MODEL> --region <REGION> [--lang <LANG>] --json` |
| Stage 1 | Textless extraction (only when reuse gate fails) | [`asset-textless-extraction`](../../asset-textless-extraction/SKILL.md) + `python -m tools.asset_intake` |
| Stage 2 | Live `Translation_Memory` & `Terms` lookup | `python .agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py --query-text "<text>" --scope sentence --source-lang en --target-lang <lang>` |
| Stage 2 | Sibling `manual.ir.json` corpus harvest | `python -m tools.corpus.harvest_web_ir --model <MODEL> --region <REGION>` |
| Stage 3–4 | `ManualIR v2` schema & document validation | [`tools/manual_ir/validate.py`](../../../../tools/manual_ir/validate.py) (`validate_manual_ir`) + [`tools/manual_ir/document.py`](../../../../tools/manual_ir/document.py) (`validate_document`) |
| Stage 4 | Shared-style & component admission gates | [`tools/web/prepared_style_audit.py`](../../../../tools/web/prepared_style_audit.py) + [`tools/web/component_admission.py`](../../../../tools/web/component_admission.py) |
| Stage 4 | Declarative replay / HTML assembly | [`tools/web/frozen_ai_web.py`](../../../../tools/web/frozen_ai_web.py) (`replay_package`) |
| Stage 5 | Sealed package registration & drift check | `python -m tools.web.frozen_package_registry register --approval <REF> <PKG_DIR>` and `python -m tools.web.frozen_package_registry check` |

## 2. Registered `ComponentSpec` Catalog (`component_registry.yaml`)

Inspect full slot definitions, `variant` options, and `asset_roles` in [`docs/renderers/contracts/component_registry.yaml`](../../../../docs/renderers/contracts/component_registry.yaml) or via Python:

```sh
python -c "from tools.component_specs.registry import load_component_registry; print(sorted(load_component_registry()['components']))"
```

Current registered IDs:
- **Special compositions**: `HB-SPECIAL-OVERVIEW`, `HB-SPECIAL-INBOX`, `HB-SPECIAL-OPERATION`, `HB-SPECIAL-APP`, `HB-SPECIAL-FCC`, `HB-SPECIAL-REFERENCE-FIGURE`
- **Callouts**: `HB-CALLOUT-STRIP`
- **Structured tables**: `HB-TABLE-SPEC`, `HB-TABLE-KEY-COMBINATIONS`, `HB-TABLE-LCD-ICON`, `HB-TABLE-LCD-MODE`, `HB-TABLE-AUTO-RESUME`, `HB-TABLE-TROUBLESHOOTING`, `HB-TABLE-SYMBOL-ICON`, `HB-TABLE-SYMBOL-SIGNAL`, `HB-TABLE-REFERENCE`
- **Warranty**: `HB-WARRANTY-LEAD`, `HB-WARRANTY-SECTION`, `HB-WARRANTY-YEARS`

## 3. CSS Geometry-Only Allowlist vs Forbidden Overrides

Shared look-and-feel lives in `docs/renderers/contracts/web_*.css`. Package-local `source_stylesheet` files are governed by [`tools/web/prepared_style_audit.py`](../../../../tools/web/prepared_style_audit.py):

- **Allowed in `source_stylesheet` (geometry only)**:
  - Positioning and layout coordinates (`position`, `top`, `left`, `right`, `bottom`, `inset`, `transform`, `width`, `height`, `max-width`, `aspect-ratio`, `grid-*`, `flex-*`, `gap`, `margin`, `padding`, `z-index`, `text-align`).
  - Marker pin coordinates, callout leader anchor offsets, and panel hotspot geometry.
- **Forbidden outside shared components**:
  - Inline `style="..."` attributes on any flow node.
  - Custom non-theme CSS class names (only classes defined in `docs/renderers/contracts/*.css` or `GENERIC_CLASSES` are admitted).
  - Paint/visual properties in `source_stylesheet`: `color`, `background*`, `border*`, `fill`, `stroke*`, `box-shadow`, `outline*`, `text-shadow`, `text-decoration-color`.
  - Unregistered bare tables without an explicit `shared_component_exceptions` entry (`language`, `page_id`, `kind: table`, `text_sha256`, `reason`).

## 4. Artwork Reuse Decision Table

Follow [`web-artwork-reuse.md`](../../../../docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md) before introducing any image file:

| Priority | Source | Rule |
| --- | --- | --- |
| 1 | Shared icon/button registry (`shared/buttons/`, LCD/symbol shared assets) | Match by semantic key (`button/power`, LCD icons, safety symbols); never recrop per language or PDF page. |
| 2 | Approved `✅成品` rows in [`data/asset_registry.csv`](../../../../data/asset_registry.csv) | Reuse sibling/model assets byte-for-byte with original SHA-256 when hardware/UI matches. |
| 3 | Complete product panels & App UI frames | Preserve whole panel/frame intact; translate only external HTML labels/anchors inside `ComponentSpec` slots. |
| 4 | Net-new extraction ([`asset-textless-extraction`](../../asset-textless-extraction/SKILL.md)) | Allowed only after recording why priorities 1–3 cannot satisfy the slot in the review record. |

## 5. Pre-PR & Release Acceptance Checklist

- [ ] Stage 0 preflight executed and sibling `manual-ir/v2` + `✅成品` asset inventory recorded.
- [ ] Every image asset resolves to a registered `asset_key` (zero unapproved screenshots or sliced sub-icons).
- [ ] All reusable copy grounded in `Approved` `Translation_Memory` / `Terms` or harvested sibling `manual.ir.json`; provenance sidecar records `asset_key` and `tm_record_id` in separate units.
- [ ] `ManualIR v2` uses `whole-document-components/v1` (or justified `whole-document-flow/v1`), passes `validate_manual_ir`, `component_admission`, and `prepared_style_audit`.
- [ ] Built HTML verified at `1440px` desktop and `390x844` mobile with zero horizontal overflow.
- [ ] If sealed for release: `source_manifest.json` SHA-256 inventory complete and package enrolled in `data/frozen_package_registry.json` via `tools.web.frozen_package_registry`.
- [ ] Repo guardrails pass (`ruff check`, `unittest`, `check_maintainability_guardrails`, `check_doc_link_integrity`).
