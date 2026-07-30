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

## Core rules

1. **Choose the operator from the drawing's structure, not from habit.**
   Default is pure text stripping (`redact_text`, graphics preserved). Escalate
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
