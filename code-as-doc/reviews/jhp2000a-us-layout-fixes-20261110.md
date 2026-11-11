# JHP-2000A US English layout correction

Status: active

Candidate in verification; publication is not authorized.

The operator supplied the published page and marked LED label alignment, then reported the contact QR top border missing. Source/package, measured causes, bounded correction plan and verification commands are recorded in the [candidate](../../manual_sources/JHP-2000A/US/en/git-20261110-5b60448e-layout-fixes/README.md). The prior published package remains immutable.

## Asset reuse decisions (before extraction)

| Slot | Inventory / candidates | Identity check | Decision and reason | Source / boundary policy |
| --- | --- | --- | --- | --- |
| LED panel | Prior JHP-2000A US release `assets/led-light.png`; same-model original intake | Same model, market, language, PDF; complete panel already correct | Reuse prior release bytes; only native labels move | SHA-256 `5974b0f8bdf974e4ac7df22aa54587a038a7526d86e0874691f0c054dc2a743a`; retain full panel |
| Contact / QR | Prior JHP-2000A US release `assets/source-contact-frame.png`; original intake has no source-contact-frame; shared/template assets are not this complete own-source panel | Prior release top y=460 clips the source frame at y=459.60983; same PDF p24 contains the full frame | Correct existing crop to y=459, retaining existing text stripping and every QR module; no suitable intact existing panel | Own PDF p24 `[28,459,344,498]`; preserve border, glyphs, divider and QR |

## Verification

Passed: native-copy parity, unchanged-artwork hashes, QR module pixel parity, strict Sphinx, identical final cold replay, desktop/390px geometry and overflow checks, frozen-package and documentation guardrails. Evidence is in the candidate’s `evidence/layout-fixes/verification.json`. Full-suite limitations and clean-main reproductions are recorded in the linked JS-100I review; no PR or publication was performed.

The operator subsequently added the [JS-100I English source-layout corrections](js100i-eu-layout-fixes-20261110/README.md) to the same screenshot-repair task.
