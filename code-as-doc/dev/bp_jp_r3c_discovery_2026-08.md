# BP@JP R3c target discovery (JBP-2000B_JP)

Date: 2026-08-31

## Outcome boundary

R3c must prove that the target-neutral BP@JP skeleton can produce the first
real target, `JBP-2000B_JP`, by adding target data and Japanese carriers rather
than another model-specific page implementation. Completion means the four
repository renderers, a native InDesign open/save/export pass, a twelve-page
visual comparison, and a clean-room delivery ZIP all pass for the same resolved
target.

## Frozen production facts

- Canonical target: `JBP-2000B_JP`, material/project code `HTP017`.
- Display name: `Jackery Battery Pack 2000`.
- Paired host hardware: the same hardware as the US `HomePower 2000 Plus`, but
  the JP target's authoritative market name is
  `Jackery ポータブル電源 2000 Plus`. EU uses `Explorer 2000 Plus`; only US
  uses `HomePower 2000 Plus`. The operator confirmed this same-hardware,
  market-name mapping on 2026-08-31. This is target data, not page logic.
- Japanese domestic use only.
- Support email: `jackery.jp@jackery.com`.
- House-style version: `jp-v2`.
- Warranty: three years plus a two-year extension.
- Optional slots enabled by the HTP017 product plan: `toc`,
  `symbol_meaning`, and `troubleshooting`; no terminal slot.
- The HTP017 v2 source does not establish a sufficiently precise legal company
  name for `LEGAL_COMPANY_NAME`. The target carrier does not emit that field,
  so R3c deliberately leaves it unset instead of copying the older HTP007
  value or inventing a legal entity.

## Reference authority

The frozen source PDF is outside the worktree:

`/Users/pika/Desktop/基于泛分类/信息架构分析/便携加电包/HTP017/日规/Jackery Battery Pack 2000取扱説明書V2.0-2026-05-28.pdf`

- SHA-256: `f7830bf9fb96d9a3e36737bad5196bbfac2d262eaef642f3406fe77eecd02b0b`
- Byte size: 3,317,375.
- Physical pages: 12.
- Page size: 368.754 x 524.659 pt.
- Creator: Adobe Illustrator 30.1 (Windows).
- Text and graphics are not a flattened screenshot-only book. Japanese text is
  extractable and the PDF embeds Noto Sans JP variants plus supporting Latin
  and symbol fonts.

The printed-page assembly is already evidenced by the R3a three-book ledger:

1. cover;
2. TOC;
3. safety;
4. symbol meanings;
5. box contents plus product overview;
6. LCD display plus operation;
7. connections;
8. connections continuation;
9. charging;
10. troubleshooting plus specifications;
11-12. warranty.

## Existing reusable contract

- `docs/manifests/skeletons/bp-jp/blueprint.yaml` owns the stable slot universe,
  `jp-v2` order, and the semantic `lcd_display + operation` co-page group.
- `docs/manifests/skeletons/bp-jp/slot_templates.yaml` owns slot-to-carrier
  mappings and versioned safety/warranty carriers.
- `docs/manifests/region_profiles/jp.yaml` owns the Japanese language and the
  shared BP@JP recipe bindings.
- `docs/manifests/manual_bp-jp.yaml` is a generated required-core anchor. It is
  deliberately not the HTP017 target manifest because it omits the three
  optional HTP017 slots.
- `tools/skeleton_resolve.py` already accepts a file-backed product plan with
  `house_style_version`, `enabled_optional_slots`, and `terminal_slots`.
- The existing BP@INTL target assemblies and shared IDML composition types are
  reusable. R3c may declare target geometry and composition data but may not add
  a model-name branch in a renderer.

## Data and asset gaps closed in R3c

- Japanese is registered for the shared symbols, LCD, troubleshooting, and
  specification data pages.
- Seven HTP017 symbol rows and two LCD rows carry approved Japanese fields; the
  symbol rows include the JP Market tag.
- Thirteen JP-only troubleshooting rows preserve the printed F0-FF order while
  the seven existing US rows remain unchanged.
- The 17-row intake package was approved and promoted: 11 specification rows,
  6 placeholder rows, and 2 shared `Spec_Notes` records were read back from the
  live business-plane Base. Record IDs are frozen in
  `reports/source_intake/JBP-2000B_JP/source_data_approval_2026-08-31.json`.
- Eight JP assets (cover plus seven connection/charging assets) passed their
  twelve-times-zoom approval, hash contract, and registry enrollment. The
  approved extraction recipe is
  `data/asset_recipes/manual_jbp2000b_jp_assets.json`.

## Baseline safety net

Real entrypoint executed before implementation:

```text
python3 build.py check --config configs/config.bp-jp.yaml --model JBP-2000B --region JP
```

It exits 1 with:

```text
[validate_config] ERROR: config not found: .../configs/config.bp-jp.yaml
```

This is the expected pre-R3c gap. The target must progress from this missing
configuration to a complete four-renderer and native package proof without
changing existing MAIN@JP or BP@INTL bytes.

## Approval gates that remain closed

- No candidate assembly is an approved reference layout; it stays
  `status=candidate` and `production_eligible=false` in R3c.
- Native InDesign save/reopen, PDF/X export, and the final twelve-page visual
  ledger must pass before the PR can claim delivery acceptance.

## Non-goals

- No BP@JP resolver branch for HTP017, `JBP-2000B`, titles, page numbers, or
  source filenames.
- No copied twelve-page renderer or copied JBP-US twenty-eight-page assembly.
- No mutation of the root checkout or its generated/review artifacts.
- No formal live source-table, localized-copy, asset-registry, or build-queue
  write before its approval gate.
- No reference-layout promotion in this target-onboarding PR.
