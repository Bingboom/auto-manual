# Prepared-document shared-component admission

Status: active. Admission merged in #1342 on September 30, 2026; the scoped
14-manual rollout is published and verified (see the
[release acceptance](eu_shared_component_rollout_2026-09.md#published-acceptance--2026-09-30)).
The additional six-locale JE-1000H LCD repair remains PR #1343, not published.
The combined pre-merge suite ran 4,928 tests
with no failures or errors (19 skipped). The 51 prepared and 10 native packages
passed fresh admission; all 958 component/chapter removal mutations were
rejected. A real App artwork tamper with recomputed candidate hashes was also
rejected by the independent debt pin. These results do not claim that deferred
App/LCD migration is complete.

## Boundary and owning contracts

`tools/web/component_admission.py` gates new EU/UK/EUUK Web inputs at queue
staging, projection sealing, frozen-source sealing and fresh evidence verification.
A real `manual.ir.json` is mandatory. Removing a coverage marker cannot opt out.
Target identity, pending source review, the IR envelope/content hashes, actual
component slots and packaged asset bytes are checked. Other regions retain their
existing policy. A new, unenrolled prepared target requires applicability review.

`tools/prepared_component_coverage.py` counts actual flow nodes against an
independent policy. Candidate inventory is never the source of requirements.
`tools/prepared_component_policy.py` resolves
[`prepared_component_admission.json`](../../docs/renderers/contracts/prepared_component_admission.json),
which enrolls the 51 existing prepared EU targets from the September 30 audit.
It is one reviewed corpus contract, not a new configuration per model.

Each page retains its exact assembly identity/slot, including renamed CSV
pages and template-path slots. Requirements count component **variants** within
that page; two App downloads cannot replace a missing add-device component.
Removed or newly added pages require applicability review. Existing component
counts are a minimum: ordinary copy can evolve without changing enrollment,
but deleting a bound component or switching its variant cannot silently pass.

Newly enabled AC-resume/expansion/UPS capabilities without a reviewed chapter
binding also block publication; existing enrollment cannot silently skip them.

Capability values come from `data/model_capabilities.csv` through the existing
loader. Missing rows use the existing `data/capability_known_missing.csv`
decisions; unknown is not false. AC-resume, expansion and UPS page applicability
is checked against that source. App applicability follows the reviewed assembly,
since App is not a capability-table field. Accessories and DC-only products do
not inherit portable-host AC/App requirements.

Native `frozen-ai-json` / `frozen-pdf-json` inputs retain the native admission
owned by PR #1339. The prepared enrollment assumes the repairs in PR #1340 and
PR #1341. These changes were composed and validated before activation, then merged in
dependency order. Future changes must preserve that composed validation.

## Historical replay versus a new publication

The existing `stored=True` evidence-verification path continues to validate old
immutable inventories without applying today's new component admission. It
still rejects pending source review. Fresh seal/stage/verify entrypoints never
take this decision from candidate metadata. A historical package lacking IR can
be replayed but cannot pass a new EU/UK release seal merely by reusing its files.
This gate does not modify or republish already shipped manuals.

## Bounded migration debt

Exceptions pin target, page, node location, node kind, complete node SHA-256 and
review category/reason. Chapter exceptions also pin referenced packaged asset
hashes, so updating candidate metadata cannot reapprove changed artwork.
Changes, growth, movement, duplicates and stale entries
fail admission. Whole-chapter exceptions are restricted to the 27 legacy App
chapters and six unadapted warranty chapters. They hash the ordered flow,
normalizing only ComponentSpec source directory prefixes for relocatable builds.
They cannot satisfy other pages' requirements, and they are reported as debt,
not counted as shared components. Candidate builds never refresh these hashes.

The reviewed post-repair corpus contains 50 raw table nodes. One is inside the
JA-CC30A warranty chapter exception; the remaining 49 have individual bindings:

| Category | Nodes | Treatment |
| --- | ---: | --- |
| Diagram labels | 18 | Preserve exact labels; not an operation-table defect |
| Regulatory radio tables | 6 | Preserve exact regulatory rows |
| LCD text-only fallbacks | 9 | Source/icon review debt, not shared icon coverage |
| Localized callouts | 5 | JBP-2000B note/caution adapter follow-up |
| JE-3600A operation tables | 4 | Source-compatible LCD/key adapters still needed |
| Charger compatibility/status | 2 | New shared definitions needed |
| Multi-port output combinations | 5 | Shared matrix definition needed |

These are **local rebuild counts**, not a revised online defect count. The
online audit found 13 LCD fallbacks; the composed rebuild labels two additional
JBP-2000B locales as text-only. Those classification counts describe the pre-publication audit; the subsequent
14-manual publication is recorded above. Likewise the six
radio tables here must not replace the older DOM audit's five-table exclusion
without checking the deployed outputs.

A follow-up comparison of the cached online JBP-2000B es/fr LCD tables
confirmed zero inline images both before and after rebuilding. Their eight
body cells match after whitespace/apostrophe normalization. The old HTML has
four empty header cells that the rebuilt table omits. The new fallback marker
is not evidence of newly lost icons; this is not a claim of pixel parity.

Finished panels remain separately governed artwork. Their source provenance
must match the packaged asset manifest, and replay checks the actual bytes.
Neither approved artwork nor an invented `hb-*` class manufactures ComponentSpec
ownership. Normal prose and lists need not be components.

## Enrollment and maintenance procedure

1. Build the target through its actual `build.py md` Web path with its approved
   snapshot. Compare source copy, figures and existing shared variants.
2. Review canonical assembly pages and capability applicability. Add explicit
   page/variant requirements to the one admission contract. Do not copy counts
   blindly from a candidate whose coverage is in question.
3. Resolve unbound nodes to adapters first. If genuinely deferred, classify a
   narrow exception with its exact hash/location and a review reason. No general
   wildcard exceptions or automatic baseline refresh are supported.
4. When migrating debt, remove its exact exception and add component/variant
   requirements in the same change. Unused exceptions fail, preventing stale
   waivers from accumulating.
5. Run policy/admission tests, the real target build and fresh seal, mutation
   cases, then composed release validation. Rendering and visual acceptance
   remain necessary; this gate is not a claim of pixel-perfect layout.

## Old App and finished-panel migration order

The 27 chapters are JE-1000H six languages, JE-2000E and JE-2000F six each,
JE-3000C six, and JE-3600A three. The reviewed legacy ledger retains each one.

First separate App discovery from unrelated operation-art eligibility:
`discover_registered_components` currently gates download/inline adapters on
`supports_figures`. JE-3000C French has valid App source patterns but an empty
`figure_targets` list. Do not enable all product artwork to work around this.

Then migrate one representative per source shape: JE-3000C/fr placeholder,
JE-1000H/en direct chapter, JE-2000E/de model-specific chapter, JE-2000F/en
placeholder, JE-3600A/en direct chapter. Bind download and inline-control to the
existing `HB-SPECIAL-APP` variants. Add-device finished panels need an explicit
provenance-preserving adapter; do not redraw or strip approved captions.

For each representative, compare source captions and asset hashes, validate
mobile/desktop layout, then expand only its matching languages. Keep QR/store
artwork, device-add steps and inline controls distinct. Delete the chapter debt
only after all three variants are governed. These migrations remain follow-up
work; enrollment does not assert they have happened.

### JE-1000H LCD follow-up (2026-09-30)

The six JE-1000H LCD chapter exceptions have been replaced with required
`HB-TABLE-LCD-ICON/icon-catalog` bindings. The frozen source now supplies 27
existing icon attachments by semantic identity while retaining the approved
26-callout numbering (two temperature rows share 23). Missing this component
now fails admission. The remaining legacy inventory is 82 exceptions: 49
individual tables, 27 App chapters and six warranty chapters. This is source
coverage, not a claim that all six updated manuals have been republished.
The connected-batteries image retains its documented resolution debt.

The JBP-2000B EU French and Spanish connection pages now use shared callout
components. French requires two `HB-CALLOUT-STRIP/note` instances; Spanish
requires one caution and one note. Their three obsolete ordinary-table debt
pins were removed when sealing the transparent-symbol repair on 2026-10-05.
The required component counts remain independent of candidate inventories.


JA-AD600A/EU/en 的 0924 原稿修正版于2026-10-07按 MA-264 登记：保留9页/slot、规格及九项包装组件，新增5个原生 ReferenceFigure 要求；警告和10步配图由已审源容器承载，未冒充旧 footer-panel/callout/warranty ComponentSpec。兼容、灯状态和原稿质保周期三张表按准确节点/位置/哈希登记，质保正文仍是原生标题段落。旧绑定只适用于历史 stored 证据，不能作为新修正版门禁。
