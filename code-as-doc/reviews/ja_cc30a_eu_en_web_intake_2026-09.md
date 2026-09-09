# JA-CC30A / EU / en Web intake review (2026-09)

## Scope and source authority

- Target: `JA-CC30A / EU / en / Web`.
- Product: Jackery Extreme Guard Carrying Bag (L Size), a powered low-temperature protection accessory.
- Operator-designated source record: Base `YndMj49yWjP03jNjCDojvAQdJ3pmz5aA`, table `97v7518`, record `Li32wwM6MY`.
- Source: `38-0001-000673 HTO859A-US CA EU UK-JAK 说明书 RoHS REACH.ai`, SHA-256 `0eb2b7ba99e9b5b941f147f3b3b60f89229b007af77fc80e7dc9451d7aaa50d3`.
- The PDF-compatible Illustrator file contains one 5687.26 × 4011 pt artboard. The English manual occupies five printed pages on the artboard.
- The source record has no published-PDF link. This task uses the operator-designated AI without version calibration and does not claim a published revision.
- The exact AI bytes and the target CSV carriers are frozen under `data/manual_sources/ja_cc30a_eu_en`; reproduction requires no live-table access.

## Structure and ownership

The target reuses `config.charger-eu-en.yaml`, the `charger-intl` skeleton, Product Manual Plan resolution, shared ManualIR, and shared Web components. The reusable `powered-protection-accessory-v1` profile selects only the source-supported chapters: disclaimer, overview, precautions, specifications, package list, use, maintenance, customer service/warranty, and FCC text. It does not inherit LCD, UPS, App, charging, or portable-power-station feature chapters.

| Source content | Web ownership |
|---|---|
| Product overview | Complete source figure plus native numbered legend |
| Technical parameters | Native semantic specification table |
| Package list | Three responsive Inbox cards with item-only source crops |
| How-to steps 0–4 | Four complete English source panels; duplicated visible body copy is not repeated |
| Side ventilation/support bars | Native introductory paragraph plus complete source panel |
| Precautions, cleaning, warranty, contact, FCC | Native searchable HTML/RST copy |

The package-list User Guide crop excludes the source QR because its destination is not verified. Cover, contents, printed page numbers, manufacturer production marks, and artboard annotations are not Web body content.

## Traceable checklist

- [x] Exact source record coordinates and source SHA-256 recorded.
- [x] Exact AI bytes and target-scoped CSV inputs frozen in Git.
- [x] Product Manual Plan resolves only the powered-accessory chapter set.
- [x] Deterministic asset recipe replayed from the frozen AI.
- [x] Eight approved exports visually checked and hash-locked in recipe, registry, and illustration manifest.
- [x] Real `build.py md` produces `whole-document-components/v1` ManualIR.
- [x] Target regression (30 tests), target `build.py check`, and strict Sphinx pass.
- [x] Asset registry, links, secrets, lint, maintainability, and full repository regression (3,910 tests; 22 skipped) pass.
- [ ] Clean-checkout replay passes from committed source inputs.
- [ ] Latest `origin/main` merged normally after validation.
- [ ] Branch pushed and PR opened to `main`; merge and formal publication remain pending.

## Publication boundary

Local build, local preview, pushed branch, open PR, merged engineering code, and formal Hello-Docs/RTD publication are distinct states. This change does not write DingTalk/Feishu, dispatch a queue, upload OSS, merge its own PR, or publish a live Web manual.
