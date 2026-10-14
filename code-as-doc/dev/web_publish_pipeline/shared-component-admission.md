# Web Publish pipeline: native multilingual shared-component admission

Status: active · Part of the [Web Publish pipeline](../web_publish_pipeline.md) contract; its index lists the
other sections. Change this part of the contract here, not in the hub.

## Native multilingual shared-component admission

Native portable-manual imports use one semantic coverage policy in
[`frozen_web_component_coverage.py`](../../../tools/web/frozen_web_component_coverage.py).
A valid `manual-ir/v2` envelope or `whole-document-components/v1` flag alone
is insufficient: an ordinary table can satisfy the IR schema while missing
its shared presentation, as happened to the JE-1000F key-combination table.
The policy checks actual chapter flow against the existing component registry:

| Semantic chapter | Required shared presentation |
| --- | --- |
| symbols | Signal meanings and pictogram meanings |
| in_the_box | Inbox composition |
| product_overview | Overview composition or governed reference figures |
| lcd_display | LCD icon glossary |
| operations | Operation panels, LCD modes, auto-resume and key combinations |
| troubleshooting | Troubleshooting table |
| specifications | Specification tables |
| warranty | Lead, sections and years card |
| app_setup | App composition |

Requirements use stable chapter/component IDs, not translated headings, model
names or counts copied from another product. Singleton semantic tables must
occur once; variable specification groups, operation panels and warranty/App
sections have no model-specific fixed count. The actual component inventory
must match its declaration. Bare flow tables/images outside components fail;
registered component carriers and approved dense-callout reference figures
remain valid. Ordinary paragraphs and lists remain native semantic flow.

`frozen_ai_web.assemble_book` validates new `frozen-pdf-json` output before
writing the IR or Markdown and stores a `shared_component_coverage` report.
`replay_package` recomputes coverage before replay for newly stamped packages;
the contents of the stored report cannot turn admission off.
`require_publishable_manual_ir` checks both native PDF
and historical frozen AI sources at release sealing and evidence verification.
Historical unstamped replay remains available for comparison, but generic
legacy layouts must be migrated before a new publication is sealed. Other
RST/projection releases do not inherit this import-specific chapter contract.

When admission fails, migrate the named semantic block to its existing
ComponentSpec. If no suitable component exists, define and validate the shared
component first. Do not add a per-language stylesheet or relabel a screenshot
as a semantic table. Rebuild into a new immutable version; do not edit the
historical package. A library fix alone does not update already frozen books:
rebuild and republish every affected language, then verify the live routes.

Regression coverage includes the ten reviewed native imports (JE-1000F four
languages and JE-2000F/E three each), the actual pre-fix four-language snapshot,
and correctly rehashed IR with a removed binding. The pre-fix snapshot fails
admission; the corrected ten books pass. These checks establish component
coverage, not translation correctness or pixel-perfect layout: desktop/mobile
preview and source comparison remain part of release acceptance.
