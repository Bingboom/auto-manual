# Specific historical operator exceptions

Introduced by PR1447 / commit3a556be836b105929dacbb1a27888cd7b2c876ee. This is specific operator evidence, not an inference from a whole-package release.

Source: code-as-doc/reviews/jhp3600c_us_en_web_intake_2026-10.md

## Lines 442–448

442: ## Shared reference screenshot reuse (app3)
443:
444: The user explicitly marked the cropped three-phone result image “用共用图啊 边缘不完整”. The candidate now reuses `docs/renderers/contracts/assets/app/app_connect_result_steps.png` byte-identically, with SHA-256 `17ccfa065009948c9e6e661017fab0b261adac03d880c025178d207e2f47ffe3`. All phone corners, status bars, bottom controls and steps 2.3/2.4/2.5 are present. The original crop is retained only for traceability and marked `superseded-do-not-reuse`. The unchanged shared `hb-app-phone-trio` size rule remains in use.
445:
446: This is an explicit reference-UI exception: the shared demonstration displays Explorer 1000 / 80% / 25°C / DC and AC, whereas the native screenshot displays HomePower 3600 Pro Max / 100% / 33°C / USB, AC and DC. The native functional instructions, product specifications and identity elsewhere remain authoritative; the source sentence “The above screenshots are for reference only.” is now selectable Web copy after the image. The image alt identifies it as a generic Explorer 1000 example. No screenshot was cropped or edited, and no shared renderer/CSS logic changed.
447:
448: App3 accepted at 1440px, 390px and 320px: the complete shared image loads at the existing trio limit, centered with unchanged aspect ratio and no clipping/overflow. Exactly one selectable reference-only paragraph follows it. There are zero references to the retired cropped result. Native-source line coverage is zero unmatched, 108 frozen replay files are byte-identical, strict standalone/aggregate Sphinx passed, and 5,609 baseline files remain unchanged. [Shared-art validation](jhp3600c_us_en_web_evidence/validation-app3.json), [preview](jhp3600c_us_en_web_evidence/preview-app3.png). Source commit: `e12ab22b09c4d9f715a61816858961009c659f88`.

## Lines 518–522

518:
519: The operator reported a much taller left column with large empty space below the right column. An opt-in shared `hb-fcc-balanced-flow` container now presents the existing FCC component as a balanced two-column text flow on desktop. The approved FCC mark floats at the opening so text can continue below it. The unchanged opening, NOTE body, four measures and MODIFICATION retain their DOM order; phones use one column. The complete semantic ComponentSpec, its print column break, native wording and artwork are unchanged. No renderer/schema adapter or new asset. Strict standalone Sphinx passed, 20 FCC semantic/rendering/contract tests passed, source-native coverage is zero unmatched and 116 files replay byte-identically. Version: `git-20261005-31fd0692-fccbalance1`.
520:
521: Final fccbalance1 source commit: `22fc451e1f348c0633b13cd20566556f0858a21b`. Strict aggregate Sphinx passed for 106 targets; all 5,609 baseline source files remain byte-identical. Canonical browser checks at 1440px and 1024px confirm balanced two-column copy, with bottom differences of 4.85px and 0px respectively. At 390px/320px the copy becomes a single column. All widths preserve exactly the previous FCC text, four measure items, loaded original logo, 84 headings and seven title availability labels, with no horizontal overflow. [Desktop](jhp3600c_us_en_web_evidence/fccbalance1-desktop.png), [mobile](jhp3600c_us_en_web_evidence/fccbalance1-mobile.png), [mobile ending](jhp3600c_us_en_web_evidence/fccbalance1-mobile-bottom.png), [DOM audit](jhp3600c_us_en_web_evidence/fccbalance1-audit.json), [sealed receipt](jhp3600c_us_en_web_evidence/language_projection_receipt-fccbalance1.json) and [candidate fingerprint](jhp3600c_us_en_web_evidence/candidate-fccbalance1.json) record the current canonical preview. Local Git only; root `tmp/`, all earlier sealed releases and unrelated targets remain intact.
522:
