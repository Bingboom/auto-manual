# Four-language native Web layout correction

Discovery: fresh PDF text reached shared IR, but chapter levels, preface paragraph boundaries and several component adapters did not match the template route. Charging labels fell into body prose; LCD lost its icon column; App step captions were absent. Dense overview leader-line panels need the corresponding-language finished source artwork, as explicitly requested by the operator.

Scope: JE-1000F/EU uk/pt/nl/pl only. Restore chapter/subsection levels, source preface, safety warning and eight precautions, warranty emphasis/cards, App 2.1–2.5 captions, LCD 26-row four-column table, and eight source-language overview panels. Preserve the accepted three charging labels in each language, existing body wording, approved errata, old five languages and all other targets. Keep body/table HTML native and overview semantics in IR. No live source-table writes or workflow changes.

Phases: integrate existing shared components; validate source text and independent artwork hashes; regenerate one immutable layout-fixes package; verify four strict builds and cold replay; run repository checks; engineering PR and authorized gate-on-green merge; four-only Hello-Docs publication; actual RTD verification.

Safety net: historical published packages remain unchanged. The unpublished figure-labels candidate is retained in commit history and /tmp/figure-labels-pre-warranty-source. The earlier warranty-only candidate is replaced only after preserving it locally. Shared stylesheet stays on existing contracts; no language-specific renderer.

Validation: focused unittest, Ruff, full unittest, maintainability, doc links, US fixture check, four strict Sphinx builds, cold replay and hashes, source parity, final portal preflight, publication-scope and live asset checks. Automated browser checks are separate from static DOM checks; do not claim screenshot validation when browser control is unavailable.

Branch: managed isolated worktree fix/web-solar-inline-labels. Verified equivalent local base 6962b552 and engineering main 99edfd22 share tree e4d7e8ee. Git transport timed out; authenticated Git Data API is the working update channel. No foreign checkout files were modified.

Source discrepancy retained for review: Dutch source right-view artwork says dual-input vehicle 16A, while the other three source-language panels say 8A. This presentation correction does not silently rewrite source specifications.
