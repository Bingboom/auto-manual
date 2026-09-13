# MAIN@INTL JE-2000F Web skeleton discovery (2026-09)

Status: implementation and parity evidence for the first post-S6 Milestone M
Web slice; broad validation and PR gates remain pending.

## 1. Scope authority

The operator-provided DingTalk AI Table view is the only product list for this
slice. A read-only MCP query of `交付工作管理 / 电子说明书新增语言 / 表格`
returned 20 English bootstrap records on 2026-09-12. No DingTalk row was
written. The rows do not assert that the EU products are English-only: English
is the first skeleton/build proof, and the remaining required languages are a
follow-on part of the same Web milestone.

The 20 model values are:

`JE-100C`, `JS-40C`, `JS-100I`, `JE-1000F`, `JBP-2000B`, `JE-1000H`,
`JS-200E`, `JE-3000C`, `JA-AD600A`, `JA-CC30A`,
`JAAC-WHE-100-EUA1`, `JE-3600A`, `JE-300D`, `JE-2000E`,
`JBP-3600A`, `JA-CA05B`, `JE-2000F`, `JA-CA3SA`, `JE-500A`, and
`JA-AD01A`.

Repository inventory separates Web availability from skeleton authority:

- all 20 have an engineering Web target entry;
- 8 have a matching EU Product Manual Plan;
- four explicit Blueprint directories exist: `bp-intl`, `bp-jp`,
  `solar-intl`, and `charger-intl`;
- the largest uncovered skeleton cell is `MAIN@INTL`, with nine list members:
  `JE-100C`, `JE-1000F`, `JE-1000H`, `JE-3000C`, `JE-3600A`, `JE-300D`,
  `JE-2000E`, `JE-2000F`, and `JE-500A`.

`HTO2682` is not in the MCP view and is not part of this work.

Language completion is resolved per model, not inferred from `EU`. Existing
operator-confirmed registry rows already demonstrate the difference:
`JE-1000F_EU` declares `en/fr/es/de/it`, while `JE-2000F_EU` declares
`en/fr/es/de/it/uk`. The English-only rows for newer products remain bootstrap
scope until their authoritative required-language sets are confirmed; they
must not be silently promoted to a blanket five- or six-language default.

## 2. First vertical slice

The first target is `JE-2000F / EU / en` (`MAIN@INTL`). It already has all
inputs required to make this a composition-only change:

- frozen source: `manual_sources/JE-2000F/EU/en/2.0/`;
- family config: `configs/config.eu-en.yaml`;
- current family manifest: `docs/manifests/manual_eu-en.yaml`;
- hash-registered Web illustrations:
  `docs/renderers/web/je2000f_eu_en_illustrations.json`;
- target acceptance: `tests/test_je2000f_eu_en_web.py`;
- source and Web intake evidence:
  `code-as-doc/reviews/je2000f_eu_en_web_intake_2026-09.md`.

The current manifest contains model-level generated-page overrides, but none
of those overrides selects a JE-2000F carrier. The target therefore uses the
family defaults for Overview, Operation and App. A target-neutral resolved
manifest can express JE-2000F without copying the unused override table.

## 3. Characterization safety net

Before implementation, the target test passed 6/6. The real Web entrypoint was
also run against the frozen source:

```text
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off
AUTO_MANUAL_PRESENTATION_PROFILE=web
python3 build.py md --config configs/config.eu-en.yaml \
  --model JE-2000F --region EU --lang en \
  --data-root manual_sources/JE-2000F/EU/en/2.0/phase2 \
  --staging-root <baseline>
```

Baseline facts:

- 17 IR pages after the false `加电包扩容` capability is filtered;
- `manual.ir.json.content_sha256` =
  `b995230d60622dbc48832b49b38617e29a2774b326432e7f7e9d9b86da211578`;
- `manual_bundle.html` SHA-256 =
  `ce9513bf6c62db3daaa8141deacbca996917ace8d9b8aa54a0ad3121acc718a7`;
- 12 required figure-coverage slots: 11 finished panels and one governed
  editable fallback;
- 14 finished-illustration elements, including the text-bearing Overview,
  Operation, Charging and App panels already accepted by the target suite.

The raw whole-IR file hash is not used as a parity oracle because it includes
the disposable staging root in `bundle_root` and page `source_path` values.
Content hash, semantic page projection, embedded ComponentSpecs, asset refs,
asset hashes and the final HTML are the comparison surfaces.

## 4. Naming compatibility trap

`manual_eu-en.yaml` is a legacy manifest without `slot_id`. Its materialized
page names come from the source carrier basenames, for example
`00_preface.rst`, `03_product_overview_placeholder.rst`, and
`12_app_setup_placeholder.rst`.

The existing skeleton path names every slot-bearing page as `<slot_id>.rst`.
Binding JE-2000F directly to such a manifest would rename pages even if their
contents were identical. That is unsafe because `origin/review/JE-2000F-EU`
exists and later `sync-review` runs must not receive an accidental page-rename
migration.

The compatibility change is therefore an optional `materialized_name` on a
slot-bearing resolved-manifest entry:

- `slot_id` remains the stable semantic identity;
- `materialized_name` preserves the already-shipped safe `.rst` basename;
- entries without it retain the current `<slot_id>.rst` behavior;
- entries without `slot_id` retain the complete legacy path;
- path traversal, non-RST names, duplicate names and `pNN_`-shaped names fail.

This is ordinal/name decoupling for one existing target without renaming or
editing any committed `docs/_review/**` derivative.

## 5. Implementation phases

1. Add and characterize the optional `materialized_name` carrier in config
   parsing, skeleton resolution and bundle planning.
2. Add `main-intl` Blueprint and slot-template catalog, a target-neutral
   `main-eu-en` region profile, and the `je2000f_eu` Product Manual Plan.
3. Emit and commit one target-neutral resolved manifest, then bind only
   `JE-2000F_EU` through `config.eu-en.yaml`; no per-model config is added.
4. Register the new manifest as the `MAIN@INTL` repository anchor and verify
   the family fold.
5. Extend the JE-2000F target suite with three-layer resolution, naming,
   required-slot, no-model-literal and before/after Web-parity assertions.
6. Run the validation ladder and record the completed English anchor slice in
   the optimization log. A second `MAIN@INTL` target is a later proof after
   this carrier is stable.
7. Reconcile the model-level required-language sets for the 20 products, then
   add each remaining locale as content/asset variants through the same
   skeleton and Product Manual Plan. Do not duplicate the Blueprint or Web
   styles for a translation.

## 6. Non-goals

- no live DingTalk or Feishu writes;
- no online operations index;
- no `IR-D01`-`IR-D06` IDML/Word/PDF migration;
- no renderer or style redesign;
- no model-specific Python or CSS;
- no new per-model config;
- no `docs/_review/**`, approved reference-layout, workflow, dependency or
  source-table schema change;
- no image extraction or replacement (the accepted text-bearing Web panels
  remain frozen).

Non-English content population is outside this first implementation PR, but it
is not dropped from Milestone M: the product-language closeout follows the
English skeleton proof and uses the same composition path.

## 7. Acceptance and rollback

Acceptance requires:

- Blueprint required slots 100% resolved and no unclassified required chapter;
- JE-2000F materialized page names unchanged;
- same 17 effective page contents, ComponentSpecs, asset refs and asset hashes;
- byte-identical final Web HTML;
- frozen-source target build and cold IR replay pass;
- existing BP, solar, charger and legacy MAIN behavior remains green;
- Ruff, targeted tests, full unit suite, maintainability guardrails, manifest
  family fold and documentation links pass.

Rollback is one `git revert`: remove the target manifest binding and the new
declarative carriers. Existing manifests ignore the optional parser field, so
the compatibility implementation has no migration side effect.

## 8. Implementation parity result

Base (`origin/main=ff5e3556`) and the implementation worktree were built through
the same `build.py md` entrypoint and the same staging root, using the frozen
JE-2000F source and `AUTO_MANUAL_PRESENTATION_PROFILE=web`.

- final `manual_bundle.html`: byte-identical, shared SHA-256
  `515f2cc1fb5c32f85ca2b3a98fe4286574a1c1c9043e8e1bfad4806880b11869`;
- effective pages: 17/17 IDs, order and page payloads identical;
- embedded ComponentSpecs: identical;
- `asset_refs`: 54/54 identical, including content hashes;
- whole-document `content_sha256`: identical at the shared staging root;
- metadata differences: only `page_slots`, intentionally upgraded from legacy
  file/page names to the new semantic slot IDs.

The comparison uses one shared staging root because Web HTML and ComponentSpec
`source_ref` values deliberately contain absolute local file URIs. Comparing
two unrelated output roots would report path-only byte differences and is not
a valid content regression signal.
