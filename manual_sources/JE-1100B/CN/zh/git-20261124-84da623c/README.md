# JE-1100B / CN / 简体中文 — 1100 Pro 2

Approved-source Web conversion of the operator-supplied 12-page `16-0102-000071` PDF, SHA-256 `84da623c6424a0fe3d48475c76094422025c8e9b18972f6373c316c08ab396d9`.
The technical snapshot name identifies Git inputs; the printed edition is unknown.

The authority is this exact source PDF plus the operator's 2026-11-24 instruction to use the same shared-component process, reuse public artwork, verify mobile and publish after checks pass (MA-483). The operator separately confirmed the App step 2.2 correction from long press to short press, matching the source's section 2.3.1. No other technical or editorial correction is made.

## Editing and replay

- `source/intake.py`: visually checked transcription, original reading order, shared ComponentSpec assembly and source-page bindings.
- `source/zh/content.json`: deterministic native flow consumed by `rebuild.py`.
- `source/figures.json`, `source/panel-recipe.json`, `audit/asset-provenance.json`: exact complete source-panel crops and byte-identical reuse decisions.
- `source/presentation.css`: geometry only. The shared theme owns typography, colors, callouts and table styling.
- `original.pdf.source-pointer.json`: durable original-source archive coordinates and exact byte identity; raw PDF is ignored locally and never added to Git.
- `web/zh/`: frozen replay output, never hand-edited.

From repository root, use a new output directory:

```sh
python manual_sources/JE-1100B/CN/zh/git-20261124-84da623c/rebuild.py --output <unused-directory>
```

Replay checks every pinned package/repository input before rendering through the shared Manual IR pipeline. This source does not enroll a new phase2 or print target. The standard JE-1000F US fixture check remains a repository regression gate and does not establish this Chinese body's fidelity.

## Content and artwork

Nine semantic chapters retain the introduction, 18 specification rows, product and LCD information, native operating copy, parallel operation, charging, 11 safety items, three inbox items, App steps and back-cover service/certificate information. The print cover is represented by Web identity and its website in the footer; its large illustration and material barcode stay in the original PDF.

All 19 LCD icons, the manual/cable icons, registration QR, service QR and the identical App add-device pair are reused as existing bytes. Embedded-image digests in both original PDFs prove the three QR/App reuse decisions; no model facts are imported from the donor. The 14 remaining source-specific figures use the committed crop-only asset pipeline, then native vector SVG export. Complete gray panels, borders, Chinese labels, phone frames and all four edges are preserved. These source-bound illustrations are not promoted to a shared registry or online asset table.

Detailed prose, specifications, thresholds and callouts remain native searchable content. Complete dense annotated/connection panels carry their printed copy as accessible image text. The source's label-only LCD catalog cannot fit a mandatory name/description component without inventing or repeating a description. It is the one explicitly declared native table exception in `source_manifest.json`: number, reused icon and name, followed by the original explanation paragraphs. The existing text-reference adapter rejects image cells, so it is not used to impersonate an icon component.

The source's App long/short-press discrepancy is resolved only by the operator's explicit decision. The printed specification says two ports total 3000W in parallel, while the parallel panel says four AC ports total 3000W; those distinct printed descriptions remain unchanged and are called out in `audit/source-review.md`.

## Acceptance

Strict standalone/full-site builds, prepared-style admission, source-page/numeric review, 12× SVG/PDF pixel comparison, two cold replays, asset-tamper rejection, frozen registry, regression and responsive browser evidence are recorded in `audit/` and the accompanying release artifact. Release requires a real archive pointer, final green checks, the MA-483 protocol and the exact merged source commit. Publication uses only this target's Hello-Docs `docs/publish/**` changes and the private RTD exact-commit build verification contract.

原图有效载荷：`source/export_panels.py --panels-dir <asset_intake产出的artifacts/panels>` 使用既有原生SVG选择器清理裁框外不可见路径。完整灰框、文字、透明度、图片及坐标不变；14张图以12×像素比对验证。
