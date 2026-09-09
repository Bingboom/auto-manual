# JAAC-WHE-100-EUA1 / EU / en Web intake review (2026-09)

## Traceable checklist

- [x] Target identity is `JAAC-WHE-100-EUA1 / EU / en`.
- [x] Source coordinates are DingTalk Base `YndMj49yWjP03jNjCDojvAQdJ3pmz5aA`, table `97v7518`, record `QKRfBknCr9`.
- [x] The operator-designated AI source is Git-frozen at `manual_sources/JAAC-WHE-100-EUA1/EU/en/source.ai` with SHA-256 `58e84bd618d17b37e67a32a18f987c750756019bfd2e53a8a07b835dc7244694`.
- [x] The record has no published-PDF link; engineering uses the current AI without version calibration and makes no formal publication claim.
- [x] The supplied 38-row scope snapshot is Git-frozen without signed download URLs.
- [x] Record `e6lR7qNTJd` (`收纳小推车`) says it is the same as `折叠小推车`; it maps to this manual and does not create a second target.
- [x] The one 2910.04 × 2046.75 pt artboard was visually mapped to cover/back plus two English body panels.
- [x] Product Plan selects only Inbox, specifications, and how-to-use.
- [x] Inbox, specifications, three description notes, quantities, and the damaged-or-lost note are native semantic Web content.
- [x] The two how-to figures retain complete source-owned English cards, gray frame, callout leaders, and trolley outline art; no adjacent duplicate instructions are emitted.
- [x] The stale `JA-ST01A` literal in the tiny Inbox manual thumbnail footer is excluded from the promoted crop.
- [x] No LCD, UPS, App, charger-only safety/FAQ/installation, or warranty content is invented.
- [x] Asset recipe cold-replays from the Git-frozen AI and verifies all seven promoted hashes.
- [x] The control-panel crop normalizes RGB to four bits per channel before
  hashing: macOS and Linux differed at only 2 of 1,263,456 pixels under the
  pinned PyMuPDF/MuPDF runtime, and the reviewed normalized bytes are identical.
- [x] Target build/check, full regression, and exact 375 px narrow-screen browser review are complete.
- [x] Latest `origin/main` (`d1eeb282`) was integrated without rebase, branch
  `codex/web-jaacwhe100-eu-en` was pushed, and PR #1097 was opened against `main`.

## Shared architecture

The target stays in `configs/config.charger-eu-en.yaml`. The shared `charger-intl`
skeleton gains an `accessory-v1` order profile and makes product overview and
warranty optional; the existing JA-AD01A and JA-AD600A Product Plans explicitly
retain those pages, while this trolley selects only its source-backed slots.
No target-specific config, parser, or portable-power-station behavior is added.

## Publication boundary

A local bundle, localhost preview, pushed branch, open pull request, and green CI
are separate evidence. This change does not merge itself, publish through
Hello-Docs/RTD, upload to OSS, mutate a live Base, or update a publication queue.
