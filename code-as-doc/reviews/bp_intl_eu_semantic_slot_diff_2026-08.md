# BP@INTL EU semantic slot diff (R1a, 2026-08)

## 1. Decision

`JBP-2000B_EU` remains in the existing `skeleton_id=bp-intl` cell. The
approved 54-page EU master has the same twelve body semantics, in the same
order, as the JBP-2000B US line. It does not justify a second skeleton or any
model-, title-, filename-, or page-number-specific renderer branch.

R1a is report-only. It adds no EU config, region profile, resolved manifest,
template, asset, resolver behavior, or live source-table row. The next code
gate is a target-neutral R1b prerequisite for region-selected terminal
carriers, followed by family-level language carrier readiness. Target intake
remains R2.

## 2. Frozen evidence

### 2.1 EU source authority

| Field | Value |
| --- | --- |
| Material | `16-0102-000400` |
| Product / project | JBP-2000B / HTP017 |
| Approved market scope | EU only; no UK market claim or UK legal carrier |
| Languages | `en/fr/es/de/it/uk`; `uk` is Ukrainian |
| Physical pages | 54 |
| Page size | 368.754 x 524.659 pt |
| Editable source authority | Illustrator-editable PDF created by Adobe Illustrator 30.4 |
| SHA-256 | `0a240f2653ab4135b354e0d697e692842027689de578a72c1c802174a644c1c6` |

The source filename contains `EUUK`, but that is not authority for a United
Kingdom market claim. The operator explicitly ruled the target EU-only.

### 2.2 Frozen JBP-US contract

| Carrier | SHA-256 |
| --- | --- |
| [`blueprint.yaml`](../../docs/manifests/skeletons/bp-intl/blueprint.yaml) | `5203be26a8846ceac8bf59ca706d7879954ff7800bd016500badb0d716a390f8` |
| [`slot_templates.yaml`](../../docs/manifests/skeletons/bp-intl/slot_templates.yaml) | `c259beae86b7b8d60fae514814af0e6cab6706ebcb6b7fbeadb1ded669ac1646` |
| [`skeleton_resolve.py`](../../tools/skeleton_resolve.py) | `3421f97a1b6313c660f9dbd609bc9200aa37f3c44eae9ca2eb1b1a735d576e96` |
| [`manual_bp-us.yaml`](../../docs/manifests/manual_bp-us.yaml) | `94e7276ab3f20bbd804eb66864b360dd5780c886b3d29ed5377161162da5cc8b` |

`skeleton_resolve.py verify` passes, so the committed JBP-US manifest is
byte-identical to the current three-layer resolver output. R1a changes none of
the four carriers above.

## 3. Physical-page normalization

The complete page-by-page evidence is in the
[54-page physical ledger](bp_intl_eu_semantic_slot_diff_2026-08.csv).

The 54 pages reconcile without an unexplained page:

| Physical range | Count | Semantic role |
| --- | ---: | --- |
| p01 | 1 | `cover` |
| p02-p03 | 2 | one `preface_important` carrier spanning six language blocks |
| p04-p05 | 2 | one `toc` carrier spanning six language blocks |
| p06-p13 | 8 | English body, printed 01-08 |
| p14-p21 | 8 | French body, printed 09-16 |
| p22-p29 | 8 | Spanish body, printed 17-24 |
| p30-p37 | 8 | German body, printed 25-32 |
| p38-p45 | 8 | Italian body, printed 33-40 |
| p46-p53 | 8 | Ukrainian body, printed 41-48 |
| p54 | 1 | `regulatory_compliance` in the terminal back-page form |

Each eight-page language block has the same semantic composition:

| Relative page | Semantic slots | Physical composition |
| ---: | --- | --- |
| 1 | `safety_info`, `symbol_meaning` | co-page |
| 2 | `box_contents`, `product_overview` | co-page |
| 3 | `lcd_display`, `operation` | co-page |
| 4 | `connections` | chapter start and main illustration |
| 5 | `connections`, `troubleshooting` | locking continuation above troubleshooting |
| 6 | `charging` | single page |
| 7 | `storage`, `specifications` | co-page; already recorded by the blueprint |
| 8 | `warranty` | single page |

The front matter grows from one US preface page and one US TOC page to two of
each because it carries six languages. That is a page-budget difference, not
a new slot or a different user journey.

## 4. Semantic diff against JBP-US

| Surface | JBP-US resolved contract | EU master | R1a ruling |
| --- | --- | --- | --- |
| Skeleton | `bp-intl` | Same twelve body semantics and order | Reuse `bp-intl` |
| Languages | `en/fr/es` | `en/fr/es/de/it/uk` | Region/language data difference |
| Front matter | `cover`, `preface_important`, `toc` | Same slots; preface and TOC each occupy two pages | Same slots, different page budget |
| Capability slots | `ups_mode` and `extra_battery` are emitted with capability annotations and filtered for the battery pack | Neither topic appears | No EU exception |
| Body | Twelve effective slots per language | Same twelve slots per language | No blueprint order delta |
| Compliance | FCC fragment repeated after `symbol_meaning` for each US language | One RED declaration on physical p54 | Region-owned compliance carrier difference |
| Terminal page | QR-only `back_cover` | RED declaration, CE mark, manufacturer/contact data, and QR on one terminal page | EU terminal semantic is `regulatory_compliance`; do not emit an additional US QR back cover |
| Warranty | Three-year standard plus two-year extended | Same policy in all six language blocks | Target copy/data difference, not slot logic |

The EU charging voltage, support email, localized labels, specifications, and
warranty text are target data. They do not alter the skeleton contract.

## 5. Target-neutral terminal-carrier gap

The current resolver cannot express the approved EU terminal page while also
preserving the frozen JBP-US manifest bytes:

1. Blueprint `optional` requirements are deliberately rejected.
2. A new required back-block `regulatory_compliance` slot would be emitted in
   JBP-US and change `manual_bp-us.yaml`.
3. Region-profile compliance rows can emit after an existing slot and can
   repeat for the primary language or every language. They cannot select a
   single terminal semantic after all body languages while also suppressing
   the unrelated QR-only `back_cover` slot.
4. Relabeling the EU RED page as `back_cover` would hide a real compliance
   topic and would make the later `page_registry` authority migration encode
   the wrong semantic.

R1b therefore needs a generic, region-selected terminal-slot mechanism. Its
schema spelling is an implementation decision, but it must prove all of these
observable properties:

- a region can select `back_cover`, `regulatory_compliance`, or an explicitly
  empty terminal set without a target/model branch;
- a selected back-block carrier emits once after all language body blocks;
- the US profile resolves byte-identically to the frozen
  `94e7276a...` manifest;
- a synthetic six-language profile resolves one final
  `regulatory_compliance` entry and no QR-only `back_cover` entry;
- the resolver remains free of `JBP-2000B_EU`, HTP017, EU title, filename, and
  page-number literals.

If this requires resolver behavior, it lands as a target-neutral prerequisite
before shared language carriers. It must not be hidden inside the later EU
target-onboarding PR.

## 6. de/it/uk carrier readiness

The canonical language registry and `page_registry.csv` already support
German, Italian, and Ukrainian for the four structured CSV pages. That is not
the same as having a complete BP family language carrier.

| Area | de | it | uk | Owner after R1a |
| --- | --- | --- | --- | --- |
| Canonical language registry | ready | ready | ready | existing platform contract |
| `symbols`, `lcd_icons`, `troubleshooting`, `spec` schemas | registered | registered | registered | R2 supplies target rows |
| BP `preface_important` composite | missing from current three-language carrier | missing | missing | R1b family/region carrier |
| BP `toc` composite | missing from current three-language carrier | missing | missing | R1b family/region carrier |
| `page_bp/<lang>` body carriers | directory absent | directory absent | directory absent | R1b family language carriers |
| Product/operation/connection assets | no language variant | no language variant | no language variant | R2 approved asset delta |
| BP warranty carrier | absent | absent | absent; source page has German residue | R1b structure, R2 approved target copy |
| Long-storage snippet | host wording is not source-identical | source paragraph is text-identical after line-wrap normalization | host wording is not source-identical | R1b may register only the proven Italian reuse; DE/UK use source-authoritative BP variants, not host-copy inference |

The current BP tree has 11 English files, 8 French files, 8 Spanish files, and
no German, Italian, or Ukrainian `page_bp` files. The front carrier is also
hard-coded to the three US languages and the US TOC page ranges. R1b must make
that readiness family/region data; it must not copy those assumptions into an
EU target file.

The Ukrainian warranty source is not reusable verbatim: physical p53 contains
the German `Umtausch` heading and exchange paragraph. R2 must use the
operator-approved HTE154/HTE152 Ukrainian replacement. R1b may define the
shared warranty composition, but must not invent or silently repair target
copy.

## 7. No-target-logic and rollback evidence

At the R1a baseline:

- `JBP-2000B_EU` has zero hits under `tools/` and `docs/renderers/`;
- HTP017 has two pre-existing comment-only hits:
  `tools/asset_pipeline/leaders.py:68` and
  `tools/renderer_acceptance.py:116`;
- R1a adds no hit in either tree;
- no live Base or asset-registry write occurs;
- removing this Markdown file and its CSV reverts the entire R1a change.

## 8. R1a exit and R1b handoff

R1a is complete when this evidence PR is reviewed and merged. R1b then starts
from latest `main` and is limited to:

1. a target-neutral terminal-carrier prerequisite if the generic resolver
   contract needs one;
2. family/region-owned six-language front matter and BP de/it/uk carriers;
3. exact reusable snippet variants only where source identity is proven;
4. tests proving the frozen JBP-US manifest and existing 28-page mechanical
   gates remain unchanged.

R1b still does not create `JBP-2000B_EU`, its config, its region profile, its
resolved manifest, its source rows, or its assets. Those remain R2.
