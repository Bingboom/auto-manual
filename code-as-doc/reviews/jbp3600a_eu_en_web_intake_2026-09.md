# JBP-3600A EU/en Web intake and acceptance

Date: 2026-09-06

Implementation baseline: `ef45a0df4582e89b0edabbb26d529ecec9d65bf3`

Target: `JBP-3600A / EU / en` (`HTP011`, Jackery Battery Pack 3600)

## Authority and source inventory

The current published booklet is the content authority. Its external file title
incorrectly says JBP-3000A; the visible cover, body, source AI, and source-list
model all say JBP-3600A. This implementation preserves the external naming debt
and binds the target to the visible/manual identity.

| Source | Version | Pages used | SHA-256 |
| --- | --- | --- | --- |
| Current published PDF | V2.0-2026-08-04 | cover 1; shared English preface 2; English body 5-12; EU declaration/manufacturer tail 45 | `084dd4517feddcd9b77da10415a2787ec4427f882a7b819160725fdff679ccfe` |
| Illustrator-compatible AI (`hgXiHot5Ow.ai`) | source-list attachment inspected 2026-09-06 | cover, English preface, English body pages 01-08 | `e0ccc33427f89c77c30d32e073a3027123f4c8a9c9f5029d2378172a7f0a3761` |

The PDF text layer was used only as an inventory aid. Pages 5-12 and 45 were
rendered and inspected. The implementation keeps visible product markings and
uses the target's own Explorer 3600 Plus connection/charging figures; it does
not reuse JBP-2000B artwork or parameters.

## Live business-plane readback

Read-only queries used the business phase2 Base
`LD3lb4G1ua4GOVs1vxAc9W2enje` with the configured bot identity. No live writes
were made.

Direct filtered reads on `Document_key=JBP-3600A_EU` returned zero rows from
Document_key, build, specification, and page-placeholder tables. Direct target
reads also returned zero rows from Product, Manual_Copy_Source,
TROUBLESHOOTING, and all three `04_资产*` tables. The Symbols and LCD `Model`
multi-select filters rejected JBP-3600A as an unregistered option. These reads
describe the 2026-09-06 live state; they do not authorize a source-table write.

## Source-to-structure mapping

| Published content | Slot / shared component | Target data or illustration |
| --- | --- | --- |
| cover | `cover` | target cover asset |
| English IMPORTANT | `preface_important` | existing BP English carrier; published wording |
| safety + meaning of symbols | `safety_info`, `symbol_meaning` | shared BP safety carrier and Symbols component |
| three package items | `box_contents` / `HB-SPECIAL-INBOX` | Battery Pack 3600, Expansion Cable, User Manual |
| front + left-side overview | `product_overview` | one complete labeled target panel |
| two LCD indicators | `lcd_display` | target rows and complete labeled LCD panel |
| power and display controls | `operation` | target copy and two complete labeled panels |
| fault codes F0-FF | `troubleshooting` | target rows; no JBP-2000B retagging |
| clearance, stacking, lock/unlock | `connections` | target copy and three complete labeled panels |
| AC and solar charging | `charging` | Explorer 3600 Plus copy and target figures |
| storage | `storage` | published 1/3/12-month ranges and long-storage advisory |
| specifications | `specifications` | target specification rows |
| warranty | `warranty` | published repair-or-replace variant, 3+2 years |
| EU declaration + manufacturer | `regulatory_compliance` | target-neutral carrier with target substitutions |

The published book contains all BP@INTL required body slots, including
operation, troubleshooting, and storage. No blueprint requirement is relaxed
and no source-absent chapter is invented.

## Implementation phases and safety nets

1. Add a reusable BP/EU/en region profile and resolved manifest, plus an exact
   target config for JBP-3600A. Keep the existing six-language BP/EU target
   byte-stable.
2. Make the existing BP English carriers target-neutral where they still name
   JBP-2000B or its assets; bind JBP-3600A values in config/structured fixture.
3. Extract deterministic target illustrations from the source AI, record the
   source/recipe/hashes, and bind them with `web-illustrations/v1`.
4. Add target-specific, source-backed fixture rows and contract tests. Run the
   real `build.py` Web entrypoint, public-IR cold replay/hash-failure checks,
   and desktop/375 px browser acceptance.
5. Re-run JBP-2000B EU plus JE-1000F EU/en regression and the repository
   lint/unit/guardrail/doc-link ladder before opening the engineering PR.

Non-goals: live Base writes, review reseeding, IDML native pagination, other
languages, direct Hello-Docs code changes, Web Publish, and formal production
URL verification.

## Acceptance status

Engineering acceptance passed on the target fixture; no formal publish or merge
was run.

| Gate | Result |
| --- | --- |
| Repository unit suite | `python -m unittest` passed |
| Python lint | `python -m ruff check build.py integrations tools tests scripts` passed |
| Maintainability | `python tools/check_maintainability_guardrails.py` passed; no new debt |
| Documentation links | `python tools/check_doc_link_integrity.py` passed: 158 documents, 1,714 links, 0 broken |
| Target quality gate | `build.py check` for JBP-3600A/EU/en passed |
| Regression targets | JBP-2000B/EU/en and JE-1000F/US/en `build.py check` passed |
| Target contract suite | seven source, manifest, component, cold-replay, tamper, asset-hash, and isolation tests passed |
| Sphinx Web build | passed; 21 packaged images, 0 missing |

The final acceptance build used:

```text
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md \
  --config configs/config.bp-eu-en-web.yaml \
  --model JBP-3600A --region EU --lang en \
  --data-root tests/fixtures/phase2 \
  --staging-root /tmp/jbp3600a-web-acceptance-20260906-final

python -m sphinx -b html \
  /tmp/jbp3600a-web-acceptance-20260906-final/docs/_build/JBP-3600A/EU/en/md \
  /tmp/jbp3600a-sphinx-acceptance-20260906-final
```

Artifact SHA-256 values from the original implementation acceptance (historical,
not the latest-main integration artifacts):

| Artifact | SHA-256 |
| --- | --- |
| Generated Markdown | `b43a642da6b78367785d07d8af7020758e21106fcc0d3e42b9f09ac103c9ab9b` |
| Public Manual IR | `36d7628fbe4759f74ca18661e1c921ef74ce36be6af072d65fba32519fab9c4e` |
| Sphinx `index.html` | `c4266047acf968e827a403cf901905686d93bfcd7a42dfe97cae3af43cfcebd9` |
| Approved asset recipe | `68fdf5c93fe9422e531234d264698709b2da81530690c6d8fbe6d972d34d63d1` |
| Web illustration manifest | `b4e72a782d9acb6d88a133e53ef445695c375c346371fe0b2ae24e6ce0da47d4` |

Browser acceptance used the byte-identical Sphinx HTML on desktop 1440 x 900
and an emulated 375 x 812 mobile viewport. Both had equal client/scroll widths,
all 21 images loaded, and the three inbox cards remained readable without
horizontal overflow.

Passing fixture builds prove the engineering target and frozen Web package. A
formal publish remains blocked until an operator creates and reads back the
approved live source, target asset, Document_key, and build records. The source
association must preserve the verified JBP-3600A identity and source hash; the
external JBP-3000A filename is naming debt, not a reason to repeat a version
comparison or replace the current published content. Hello-Docs can then create
and review the frozen `docs/publish/**` snapshot PR.

## Latest-main integration (2026-09-06)

The target now uses a `battery-pack-v1` presentation overlay. It does not opt
into the portable-power-station Overview geometry. The five Overview, Operation
and Charging slots are required finished panels under the shared coverage gate;
the LCD panel and two connection panels remain bound by the eight-entry
illustration manifest, whose assets are all checked in the rendered HTML by hash.
Variable-card and optional-TIP Inbox changes coexist, including a combined
five-card/no-TIP regression. The unit fixture substitutes only the external
Pandoc conversion step; real Pandoc/Sphinx conversion is a separate local
acceptance check, and subprocess failures now include build stderr.
