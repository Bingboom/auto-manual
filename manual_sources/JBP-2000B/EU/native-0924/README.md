# JBP-2000B EU remaining four Web languages

The operator supplied `HTP017-EU-9国说明书-0924.ai` to complete uk/pt/nl/pl. The existing en/fr/es/de/it release is preserved. This is a frozen Git-only Web intake, not a phase2/print language expansion or a live Base write.

Original AI is PDF-compatible, 80 physical pages, SHA256 `b7d7fca4207792e6337c6e14003d12fd418fcd192ecc23137519c1147b6f85a3`. The English reference was reproduced through `build.py md --config configs/config.bp-eu-en.yaml --model JBP-2000B --region EU --lang en --data-root manual_sources/JBP-2000B/EU/en/2.0/phase2 --staging-root <scratch> --skip-root-index`, with Web presentation and OSS archive disabled. Its published source revision is `e267ff15b3d20b0309ce9ad88e589882683c34e8`.

| Language | Frontmatter | Native body | Shared legal |
| --- | --- | --- | --- |
| uk | 3 | 48–55 | 80 |
| pt | 4 | 56–63 | 80 |
| nl | 4 | 64–71 | 80 |
| pl | 4 | 72–79 | 80 |

`copy-maps/` binds native paragraphs, table cells and source differences. `source-snapshots/` records extracted blocks and their physical-page coordinates; outlined Ukrainian storage/exclusion text was visually transcribed. `web/<lang>/manual.ir.json` is the complete semantic carrier; MyST is derived by the existing shared renderer. Dense native overview/LCD labels remain in bounded finished panels; safety, descriptions, operation text, tables, specifications and warranty remain selectable.

Replay each package with `tools.web.frozen_ai_web.replay_package(Path('manual_sources/JBP-2000B/EU/native-0924/web/<lang>'))`; its MyST must remain byte-identical. Build HTML with `python -m sphinx -b html -W --keep-going manual_sources/JBP-2000B/EU/native-0924/web/<lang> <scratch-html>/<lang>`. Run fresh component, source-bound symbol and caption-frame admission before sealing through `tools.web.frozen_source_evidence.seal_frozen_web_evidence`. Source manifest inputs bind all package files; output receipts stay outside this source root.

`artwork-recipes.json` specifies original-page crops and removal/copy operations for the two shared neutral panels, retaining original PDF content, clip masks and product markings. Render at 4x; verify edges at 12x. The Li-ion source-specific shared SVG retains page48 drawings47–55 and their original ancestors; existing variants did not pass native glyph comparison. The existing no-bar battery WEEE PNG is reused unchanged. Every actual symbol row has source caption pixels, glyph selection, shared key and candidate hash in `symbol-admission.json`. Registry promotion is not part of this intake.

Agent verification is recorded in `reports/jbp2000b-four-language/acceptance.md`. It is not human approval or a merge grant. MA-257 covers only the existing five online languages and excludes new ones. Operator review and a new recorded grant are required before engineering merge and Git-only publication of these four locales.
