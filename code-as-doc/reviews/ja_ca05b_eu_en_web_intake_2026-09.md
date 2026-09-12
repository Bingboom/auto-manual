# JA-CA05B EU English Web intake - 2026-09

## Authority and target mapping

- Target: `JA-CA05B / EU / en`; delivery-table short name: `5M延长线`.
- Operator-designated DingTalk source: Base `YndMj49yWjP03jNjCDojvAQdJ3pmz5aA`, table `97v7518`, record `iQfwYCuoZ7`.
- Source attachment: `翻译用 38-0001-000942 太阳能板连接指南折页 通用 RoHS REACH.ai`, 89,943,352 bytes, SHA-256 `f5359ac0da04a79175531f0b0cbc8a05e5b65d90a6dd653d47f487a101b6dee6`.
- The record has no current PDF link. The AI attachment is the authorized Web input, while a formal published-paper revision is not claimed.
- The source title is `Jackery Solar Generator Connection Guide`. The model mapping and delivery short name are recorded separately; the Web content does not fabricate a model-specific extension-cable-only manual.

## Semantic mapping

The target stays in the shared `charger-eu-en` family. Its target-owned Product Manual Plan selects the single `connection_guide` slot. The source title, website/customer-support direction, and compatibility sentence remain native HTML text. The source grey guidance box becomes the shared semantic NOTE callout. No Inbox, specifications table, warranty, LCD, UPS, App, or combination-project section is added.

The charger skeleton's product-content slots are optional because the family now includes both full product manuals and compact accessory guides. Existing JA-AD01A and JA-AD600A plans explicitly select their previous required slots; their resolved manifests remain unchanged.

## Illustration contract

`data/asset_recipes/manual_ja_ca05b_eu_en_web.json` freezes the one-page PDF-compatible AI source and three approved crops:

- connector and DC input reference: `[391, 489, 694, 840]` pt;
- DC8020 connection panel: `[694, 489, 1099, 665]` pt;
- DC7909 connection panel: `[694, 664, 1099, 840]` pt.

The figures retain all image-owned product markings, connector labels, grey cells, cables, and leader lines. They exclude the title and prose, and no full sheet is used as Web content. Splitting the source grid into three panels keeps the labels readable at narrow widths without duplicating them as body copy.

## Acceptance checklist

- [x] Source bytes, metadata, text layer, and rendered sheet reviewed.
- [x] Exact target/source coordinates and absence of a current PDF link recorded.
- [x] Shared family, Product Manual Plan, resolved manifest, recipe, illustration manifest, registry, and Git fixture prepared.
- [x] Approved asset recipe replay reproduces all three committed hashes.
- [x] Runtime build emits one-page `whole-document-components/v1` ManualIR with three finished panels and one semantic callout.
- [x] Target test and affected charger-family tests pass.
- [x] Real Pandoc and strict Sphinx build pass.
- [x] Desktop and 375 px browser checks pass with zero broken images or whole-page overflow.
- [x] Full repository validation passes.
- [x] Standalone engineering package and local preview prepared.
- [x] Branch merged with latest `origin/main`, committed, pushed, and PR opened.
- [ ] Central review and merge complete.
- [ ] Hello-Docs publication snapshot and live RTD route verified.

No live DingTalk/Feishu table, publication queue, OSS path, Hello-Docs tree, or RTD deployment is written by this engineering task.
