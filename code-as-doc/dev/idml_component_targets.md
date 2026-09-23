# IDML component targets

Status: pilot. `JE-1000F / US / en` is the only declared target; whole-book
designer sign-off is pending.

## 1. What a component target is

A component target is a **single-language** IDML build that composes the
registered components of an approved reference-layout plan without that plan's
physical page placement. The approved
[`JE-1000F US V2.0 contract`](../../docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json)
is a trilingual (en+fr+es) 58-page book. Its English pages were also reviewed
natively as components of the single-language English manual (v4: pages 6, 7,
12, 13 and 15), but that book as a whole was not.

Before this change `build.py idml` treated `JE-1000F / US / en` as an ordinary
unapproved target: it built the LaTeX PDF and applied the measured LaTeX page
plan, so none of those compositions reached the formal entry (or the publish
queue, which calls it with `--source review`).

## 2. Declaration

A registry entry in
[`reference_layout_registry.json`](../../docs/renderers/contracts/reference_layout_registry.json)
may carry `component_targets` beside `target` and `path`:

```json
"component_targets": [
  {
    "language": "en",
    "status": "pilot",
    "evidence": "v4 native InDesign review of the registered pages 6, 7, 12, 13 and 15; whole-book designer sign-off pending"
  }
]
```

`language`, `status` and `evidence` are the only keys; `status` must be `pilot`;
`evidence` must be non-empty; a language may appear once. A malformed
declaration, or a plan that is not approved, has an unsupported schema or a
target that differs from its entry, stops the export. Other registry readers
only use `target` and `path`, so the approved trilingual build is unaffected.

## 3. Activation

[`tools/idml/component_targets.py`](../../tools/idml/component_targets.py)
decides once per export, right after the Manual IR is built. The declaration
applies only to a single-language build of a declared language. It is **active**
when

- no approved plan registered for exactly this build and no configured target
  assembly plan owns it, and
- every source page of the build is pinned by the entry's approved plan with the
  same `source_sha256` (the single-language build carries 17 of the 20 English
  pins; cover, TOC and back cover belong to the trilingual book).

Otherwise it is **inert**: the build keeps the ordinary layout (the measured
LaTeX plan through `build.py idml`) and prints every reason:

```text
[export-idml] WARNING: COMPONENT TARGET INERT (pilot): JE-1000F/US/en keeps the ordinary layout; 4 issue(s)
[export-idml] WARNING:   page/symbols_en.rst: source_sha256 does not match (pinned=e0ef55116742, built=2e3cf36d2cbc)
```

An active build prints:

```text
[export-idml] COMPONENT TARGET OK (pilot): JE-1000F/US/en | pinned=17/17 by docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json
[export-idml] PAGE PLAN SKIPPED (component target): JE-1000F/US/en composes its registered pages; the measured LaTeX plan is not applied
```

Business review content (`--source review`) activates the pilot today. Runtime
source (`--source runtime`, the default for this unapproved target) differs from
the reviewed pages in four sources and stays inert.

The pins are the approved plan's own. After a content change, refresh them with
the approved plan's rebind route (see
[`build_doc_guide.md`](../build_doc_guide.md), approved-PDF replica); the
pilot follows that review automatically. Never edit a pin by hand to reactivate
it.

## 4. What an active target composes

| Route | Effect | Module |
| --- | --- | --- |
| Page plan | measured LaTeX plan not applied | `ir_projection.build_reference_page_plan` |
| LCD | approved `lcd_icon_table` row order, numbering, heights and icon size | `ir_projection.governed_lcd_page_data` |
| Overview | native editable composition | `ir_projection.uses_native_overview_page` |
| Charging | reference-figure composites; the final car notice moves to Storage | `registered_component_plan`, `prose_flow` |
| Storage + Troubleshooting | one registered page; the car notice gets its own frame above Storage | `target_assembly_render`, `shared_page` |
| Warranty | governed frame offsets, extra depth and language; final panel −6 pt footer clearance | `reference_story_flow`, `registered_component_plan` |
| Operation rhythm | the 48.2 pt page-foot gap applies only to the structural inter-section body | `story_rhythm` |
| Main power | the drawn base-art clock stays the only clock; the editable duration starts after it | `components/oppanel` |

The main-power mode comes from the target's Operation contract (the same one the
Web uses, see [`je1000f_us_base_art_web.md`](je1000f_us_base_art_web.md)), but
only an active component target applies it. The AC, DC/USB, energy-saving and
LED panels are unchanged. Each registered composition is a one-page plan
(`plan_source: registered-component`) for exactly the sources the approved plan
grouped, so it never places other pages.

## 5. What does not change

Undeclared targets, other languages (US fr/es), the trilingual approved build,
inert builds and the flow IDML (`manual.flow.idml`) keep their previous output.
The IDML goldens are unchanged. The characterization tests added with this
change pin the shared behaviour at every point #1220 changed globally.

## 6. Evidence (live phase2 sync 2026-09-23T02:07Z, Hello-Docs `review/JE-1000F-US`)

- `build.py idml --source review` for `JE-1000F / US / en` is member-for-member
  identical (251/251, after normalizing only absolute paths) to the #1220
  no-plan export of the same content.
- Against the natively reviewed v4 package, all 251 members are identical except
  link targets that come from live data: 36 LCD/symbol attachment file names
  (record tokens and symbol ordinals) and the WEEE symbol, which the current
  data resolves to the shared `common_assets/symbols/weee.png`.
- Every other matrix target built through `build.py idml` (JE-1000F US
  runtime/fr/es/trilingual, AU, EU en/de/fr, JP; JE-3000C KR review; JBP-2000B
  US/EU/JP; JE-2000E CN) is identical to `main` in both the production and the
  flow IDML. Of the 30 archived packages only the pilot's production IDML
  changed; its flow IDML is identical too. The two known KR failures (JE-3000C
  and JE-1000F runtime builds) fail the same way.

## 7. Scope limits

- Adding a target needs an approved plan that pins its language and native
  review evidence for its registered pages; promotion beyond `pilot` needs a
  whole-book designer sign-off and its own reviewed change.
- No button recognition, automatic leader routing, multilingual auto-positioning,
  forced SVG migration or InDesign automation.
- Known, unchanged: a direct `tools/export_idml.py` run with no page plan at all
  (no LaTeX PDF beside the bundle) prints warranty component JSON as text for
  undeclared targets, as on `main`.
