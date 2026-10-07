# JBP-3600A EU nine-language overview sizing

Status: active

The published English front/left panels match the existing 25rem/34rem rules. The eight native locales use content-addressed asset paths, so the English-path selectors miss them and leave inline width:100% unconstrained.

Extend the two existing selectors to the exact reviewed FR/ES/DE/IT/UK/PT/NL/PL panels from `manual_sources/JBP-3600A/EU/git-20261003-44b6ce61-reviewed/web`. Preserve English limits, centering, image bytes, native labels and every frozen source package. No crop, source-copy rewrite, registry promotion, Base or queue write is involved.

Validation: all nine strict Sphinx builds and all eighteen panel selector matches are checked in the local candidate. The existing JBP-3600A English regression suite, maintainability and documentation link checks are run separately. Browser acceptance passes for all nine locales at 1280px and 390px: front/left widths are 400/544px on desktop, both 358px on mobile, loaded images and no horizontal overflow. A new dedicated tab resolved the stale-tab timeouts. Live publication remains pending. Local preview lives outside the repository at `/private/tmp/jbp3600a-sizing-preview/html`.

README navigation, CLI, schema and workflow topology are unchanged. Rebuild publication styles from the engineering change; do not hand-edit historical accepted source snapshots.
