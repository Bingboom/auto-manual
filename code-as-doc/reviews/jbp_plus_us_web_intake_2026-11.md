# JBP-2000A / JBP-1000A US English Web review candidates (2026-11-13)

Status: active

## Scope

Operator request 「把这几本说明书 转网页版」 for the 发布文档管理 › 说明书网页 › 美规 rows marked 是否要转网页文档 = Y-待转. These two are existing manuals, so they take the PDF / AI to Web route in [project positioning §5.1](../architecture/Hello_Docs_Positioning.md#51-网页说明书的三条路线). The method follows the five US packages in [us_y_web_intake_2026-11.md](us_y_web_intake_2026-11.md). Both packages are **review candidates only**: `publication_eligible: false`, no approval file, no merge authorization and no Feishu/Base writes.

## Candidates

| Model | Product | Material | Printed version | Candidate | Source SHA-256 |
| --- | --- | --- | --- | --- | --- |
| JBP-2000A | Jackery Battery Pack 2000 Plus (HTP002, US+CA) | 38-0001-000574 | JAK-UM-V1.0 | [source](../../manual_sources/JBP-2000A/US/en/git-20261113-90e9ed96-m000574/README.md) | `90e9ed96c7128d4849825ef8179e6e79a677f9c3a709b19cc78c3cffa6d7b050` |
| JBP-1000A | Jackery Battery Pack 1000 Plus (HTP003, US+CA) | 38-0001-000575 | JAK-UM-V5.0 | [source](../../manual_sources/JBP-1000A/US/en/git-20261113-a69ce9e1-m000575/README.md) | `a69ce9e14ba0c83a762b9b6530f7bb2652f1cb771d595ffc251cd960c10662ec` |

## Method and evidence

- The 单语言 attachments are image-only, with eleven 300-dpi pages each and no text layer. The text is Tesseract 5 OCR, hand-corrected line by line against the pixels. Each booklet is transcribed from its own pages.
- The Web output uses shared components and the shared theme only, with no plain-table exceptions. The block-to-component map is in each `source_manifest.json`.
- Artwork reuse was decided before extraction. No same-family donor matches these drawings, so the complete source panels are cropped at native resolution. The FC mark is reused byte-for-byte from JBP-3600A US.
- An independent sub-agent QC compared every block, cell and image against the pixels. It found one error per manual: the website line had been rewritten. That error is fixed. Three typography items come from the shared components and are left to the operator.
- Further evidence: strict Sphinx, real 1280/390 Chromium screenshots with no broken images or overflow, cold-rebuild identity, and tamper rejection for the PDF, native body, art and CSS.

Operator decisions and source concerns are listed in each transcription (`source_concerns`) and in the PR.
