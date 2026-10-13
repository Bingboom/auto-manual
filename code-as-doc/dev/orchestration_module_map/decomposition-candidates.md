# Orchestration module map: known next decomposition candidates (§9)

Status: active · Part of the [orchestration module map](../orchestration_module_map.md); its index lists the other
module families. Update this page in the same PR that moves a boundary here; do not add
module notes to the hub.

## 9. Known Next Decomposition Candidates

These areas still deserve follow-up only when a concrete hotspot reappears:

- [`tools/build_queue/process_build_queue_services.py`](../../../tools/build_queue/process_build_queue_services.py)
- [`tools/build_queue/lark_ops.py`](../../../tools/build_queue/lark_ops.py)
- [`tools/gen_index_bundle.py`](../../../tools/gen_index_bundle.py)

Keep future extraction notes here once those boundaries stabilize again.

Package-level moves (prefix families into real subpackages) are planned in
[Workstream Y CQ-1](../code_quality_iterability_plan.md); the proposed package
per domain is in [`code_style_guide.md`](../../code_style_guide.md) §2.16. Update
this map in the same PR that moves a family.

### Whole-document Web boundary

`word_bundle_html` selects ordered pages once; `web_document_source` owns the
RST/HTML adapter, target illustration bindings, component ownership and asset
packaging, resolves the actual `(model, region)` Web presentation stack, then
calls `manual_ir.builder.build_manual_ir_from_source`. The IR freezes that
resolved target-only contract and its selected layer IDs; replay never reopens
the shared/skeleton/overlay files.
`manual_ir.document`, `manual_ir.flow` and `manual_ir.components` own finite
flow/component validation. `web_document_ir` consumes the complete IR and
dispatches the five embedded registered families through
`web_embedded_components`; it does not invoke their scoped DOM source projectors.
Source-page reads no longer occur inside the actual Web rendering loop. Historical
v1/cut-1 packages keep compatibility paths, and Word's whole-document converter
remains separate. See [execution evidence](../ir_document_closeout.md).

`document_assets` owns the shared local image probing/copying implementation;
Word keeps compatibility wrappers, and the Web IR renderer imports the lightweight
helper directly so cold replay never imports source-table readers.

`frozen_ai_web` is the bounded alternate intake for approved frozen AI JSON.
`frozen_web_component_coverage` owns native-import semantic coverage admission;
assembly, cold PDF replay and release-evidence checks call the same policy.
It inspects actual component bindings rather than trusting inventory metadata.
`frozen_pdf_web` reuses that assembler after `frozen_pdf_intake` reads native PDF text,
`frozen_pdf_glyphs` verifies missing glyphs against the AI original, and
`frozen_pdf_source` binds explicit asset hashes. `frozen_pdf_document`,
`frozen_pdf_media`, `frozen_pdf_app`, `frozen_pdf_lcd`, `frozen_pdf_frontmatter`
and `frozen_pdf_reference` map source geometry to the existing shared components.
`frozen_pdf_finished_overview` binds only explicitly approved source-language
front/right panels through the existing composite adapter while retaining IR
callout semantics. Body/table screenshots and printed Contents stay excluded.
`frozen_ai_source` verifies source/assets and errata; `frozen_ai_document`
orders source chapters; `frozen_ai_flow`, `frozen_ai_table_components` and
`frozen_ai_media_components` map neutral prose and registered components.
They use the same assembler and public `web_document_ir` consumer. The
source-scoped locale validator is `manual_ir.external_languages`; it does
not expand phase2 or print language registration. See the
[four-language alignment](../four_language_shared_ir_alignment.md).

Prepared Web admission: `tools/web/component_admission.py` owns fresh-publication checks; `tools/prepared_component_policy.py` loads reviewed chapter applicability and existing capability data; `tools/prepared_component_coverage.py` audits actual flow nodes and bounded debt. See [contract and maintenance](../prepared_component_admission.md).

- `tools/component_specs/authored_tables_html.py`: explicit authored-table admission and specification heading normalization; no filename/model guessing. `reference_table.py` owns text-reference semantics; `tools/web/reference_table_component.py` owns its Web projection. CSV page roles enter through `word_bundle_html.py`; projected warranty leads preserve their ordered paragraph prefix.

`component_specs/operation_tables_html` binds explicitly normalized RST auto-resume and key-combination tables to the shared ComponentSpec registry. `manual_ir/whole_document_components` owns their flow claims; the target presentation contract owns chapter applicability.

`tools/component_specs/plain_inventory.py` owns recognition of complete, text-only packing inventories and their `HB-TABLE-REFERENCE/plain-inventory` spec. Word reuses the same source-shape check; whole-document Web IR claims the table and preserves sibling notes. Illustrated Inbox parsing remains strict.

`component_specs/app_label_source.py` admits the explicitly bound historical control-image/paragraph shape before the common App parser. `_claim_inbox` owns illustrated/plain inventory dispatch in the whole-document component collector. The JP warranty overlay declares seven sections and no year-card table; authored line blocks remain ordered rich paragraph content.

`component_specs/lcd_mode_source.py` owns standalone LCD image/action-matrix recognition, preserving authored headers through the shared reference table. `plain_inventory.py` admits complete three-item lists as well as one-row inventories. `app_label_source.py` preserves a separating note outside the explicitly bound shared panel.


### RTD 产品知识

`tools/rtd/product_learning.py` 将工程维护的通用课程词条与冻结产品目录关联；`tools/rtd/portal.py` 只注册页面。首页 `navigation` 是产品定位分组的同一来源，知识页不建立第二份型号定位表。
