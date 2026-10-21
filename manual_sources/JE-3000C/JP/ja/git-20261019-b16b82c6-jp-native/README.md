# JE-3000C JP V2 — Git-only Web candidate

Source: user-supplied Japanese **Jackery ポータブル電源 3000 New** PDF, 26 physical pages, cover model **JE-3000C**, printed **V2**. SHA-256: `b16b82c6c6b2ac86bf4dd438cd597e7d0be66344a9da3e2b7ea9c2d561d61a7b`.
The PDF metadata title refers to HTE1401500A; the actual cover/body determine identity. The folder label HTE156 is not model authority.

JE-1000F JP is the structure/reference edition only. This candidate uses its chapter order and the current shared ComponentSpec/theme pipeline; specifications, copy, interface artwork and App screens come from the supplied JE-3000C JP source. No per-model renderer or configuration was added.

`source/page-map.json` maps all 13 chapters to physical/printed pages. Physical pages 1 (cover), 2 (printed contents) and 26 (blank back) remain archived, outside the Web body. Web navigation replaces the printed contents. Prose, lists and all tables are native selectable HTML. Dense overview callouts, LCD numbering and phone UI remain source figures, with exact source crops and hashes.

`source/outlined-text-recoveries.json` records visually checked text absent from the PDF text layer. `source/native-text-spans.json` preserves raw native text, geometry and hashes. `source/asset-decisions.md`, `asset-recipe.json` and `asset-provenance.json` record reuse and extraction. All reused symbols, LCD/button icons, AC cable and document pictograms retain their original bytes.

## Rebuild and verify

Run from the repository root (replace the example output folder if it already contains work):

```sh
python3 -m sphinx -n -W --keep-going -b html manual_sources/JE-3000C/JP/ja/git-20261019-b16b82c6-jp-native/web/ja /tmp/je3000c-jp-html
python3 -m tools.check_maintainability_guardrails
```

The existing `tools.web.frozen_ai_web.replay_package` replays `web/ja/manual.ir.json` without reading source tables or the PDF. `source/validation.json` records the cold-replay comparison, component admission and browser checks. The packaged stylesheet is assembled from shared modules without target CSS.

## Review boundary

- Physical PDF page 21 / printed page 19: footnote ① visibly ends at `できま`. The Web preserves the visible original and does not invent a completion. This is a source clarification item, and `publication_eligible` remains false.
- Original PDF metadata and the App control schematic are preserved as source evidence; the App schematic is simpler than the hardware overview. No unapproved artwork correction is inferred.
- This is an engineering draft candidate. Merge, Hello-Docs/RTD publication and live acceptance are not included. No Feishu/Base, queue, source-table, online asset or HTML_link write was performed.
