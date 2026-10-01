---
name: asset-textless-extraction
description: Extract text-free (无字化) illustration assets from an .ai/PDF master via the committed asset pipeline (data/asset_recipes + tools/asset_intake.py) — choosing the right transform operator (redact_text vs remove_if_touched vs drop_leader_strokes vs leave-alone), tuning safely in a scratchpad, verifying at 12x zoom, getting operator confirmation with PIL side-by-side pairs, and closing with the three-place hash sync + registry enrollment. Use whenever a burned-text illustration must become language-neutral (CN/JP/KR line swaps, master榨取 rounds, 底图白块/削口 repair). NOT for template/IDML re-pointing (integration swap is its own PR) and NOT for registering non-extracted assets (plain registry row work).
---

# Asset Textless Extraction (无字化)

Turning a burned-text illustration into a language-neutral vector asset looks
like a parameter tweak and is actually five rounds of hard-won judgment: the
wrong operator cascade-kills fingers and dials, whiteout punches visible holes
through artwork, zero-area bboxes evade intersection tests, and a "fixed"
recipe can violate an immutable promotion contract. This skill encodes the
judgment; `references/operator-playbook.md` holds the full decision tree,
traps, and closing checklist — keep it open.

## Reuse before extraction

Follow the shared [Web artwork selection contract](../../../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)
before choosing any transform. Inventory target assets, same-model/region
assets in other languages, then shared/template assets. Open candidate images
and verify identity, content, language and quality. Record the candidates,
decision, source/hash and background policy in the target's existing review
record using the contract's table. A new language, PDF or page number alone
does not justify another extraction.

If a matching asset exists, reuse it unchanged and stop extraction work.
Frozen-package copies must remain byte-identical with source path/hash recorded.
If only external labels change, reuse the artwork and update native labels.
Extract only after documenting a missing suitable asset, insufficient quality,
or a concrete target difference. Do not invent a new registry/schema for this
review record or treat the record as an implemented build gate.

## Classify the artwork before removing backgrounds

- **Small standalone icons (LCD/status icons and individual button symbols):** remove identified page/cell
  backdrops and export real transparency. Preserve product shading, button
  faces and markings. White fill or CSS blending is not transparency.
- **Complete panels, including text-free App control panels:** preserve native
  gray backgrounds, white caption bands, rounded borders, badges and complete
  leader geometry. Removing labels does not authorize removing the panel.
- **App screenshots:** prefer matching existing screenshots; preserve all phone
  edges, corners, status bars and bottom UI. Do not crop to interior content.
- Never delete gray/white objects by color alone. Compare any new extraction
  with all four source edges at 12x, then verify the target Web component on
  desktop and mobile. Transparency checks apply only to these small icons. Classify by semantic role,
  not display size: shrinking a complete diagram does not turn it into an icon.

## Core rules

1. **Choose the operator from the drawing's structure, not from habit.**
   After the reuse check and classification, default for needed text stripping
   is `redact_text`, graphics preserved. Complete finished panels use crop only.
   Escalate
   to `remove_if_touched` only when leader lines touch label text; to
   `drop_leader_strokes` only for paired halo+stroke leaders drawn over
   artwork; and **leave the asset alone when evidence says the structure
   doesn't fit** — the same operator that fixed `front_controls` made
   `main_power` and `right_side_ports` worse. 按证据砍范围.
2. **Tune in a scratchpad, never with full intake runs.** Replicate the
   pipeline semantics in a throwaway script to iterate bboxes (a full
   `tools/asset_intake.py` run ≈ 1.5 min and edits nothing anyway — it is
   package-only). Verify at **12x zoom**; 4x hides capsule nicks.
3. **The operator confirms pixels, not prose.** Before touching the registry,
   send a PIL left/right before/after pair (「比文字描述有效得多」) plus the
   hash and source annotation, and wait for confirmation.
4. **Approved promotion contracts are immutable.** If the main recipe's hash
   is pinned by an approved contract (`promotion recipe binding is not
   immutable` error), do NOT rebind — split the corrective asset into its own
   recipe file, keep the main recipe byte-identical, and add a test pinning
   it (the `manual_je1000f_us_front_controls.json` precedent).
5. **Close the loop or the build lies.** Hash lives in THREE places that must
   move together (recipe `expected_sha256`, registry 12-hex 内容哈希, pinned
   test censuses), the registry row is enrolled in both the CSV mirror and
   the Feishu 插图资产表 with attachment read-back, and integration swaps
   (templates/IDML consuming the new asset) go in a separate PR with their
   golden/parity rebaseline.

## Boundaries

- Bitable row/attachment mechanics → `lark-cli-bitable-ops` (write-readback
  discipline applies: upload, then confirm the file token is non-empty).
- Which pages actually consume an asset is a fact to verify, not assume —
  e.g. `front_controls` is consumed only by JP/ZH app-setup pages; the US
  front view is a whole-page PDF extract.
- Registry debt rows (missing/temporary assets) follow the asset-loop rules:
  explicit debt entries, never delete rows, re-audit the want-list after new
  supply (old debts may already be paid by a master delivery).

## Use bundled resources

- `references/operator-playbook.md` — the operator decision tree with real
  failure cases, tuning recipe, known traps (zero-area bbox, CTM stack,
  whiteout-on-gray, engraving-vs-span), confirmation protocol, and the
  closing checklist (hash three-place sync, registry enrollment, contract
  split).
