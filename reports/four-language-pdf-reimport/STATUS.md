# Four-language native PDF re-import status

The operator approved the native Polish sample and authorized completion,
verification and RTD publication of JE-1000F/EU uk, pt, nl and pl (MA-196).

## Complete

- All four books assembled from fresh selectable PDF text through manual-ir/v2,
  existing ComponentSpecs and the public Web renderer; no OCR or body screenshots.
- Independent content audit: 836 positioned fields and 68 PDF body pages,
  26 LCD legend rows and 11 fault rows per language; approved errata preserved.
- Four strict Sphinx builds and shared cold replay passed on candidate packages.
- Final delivery full unit suite: 4,783 tests, 22 skips, no failures (667.560s).
- Subsequent provenance portability checks: 12 focused tests passed.
- Ruff, maintainability guardrails, documentation links and isolated US check passed.

## Final visual and package checks

Candidate4 resolves the Overview and App issues. All four Overview views passed
390/768/1024/1280 px DOM collision/clipping and page-width checks. App controls
were inspected in all four locales on desktop/mobile. Source inventory and
portable cold replay passed; final PDF audit reports no missing/duplicated copy.
Strict aggregate Sphinx preflight also passed. Publication evidence is not yet
final: release receipts must bind the merged engineering commit.

## Remaining release gates

- Push the final commit to PR #1316.
- All checks/reviews clear, merge engineering PR, verify Hello-Docs mirror.
- Scoped publish PR preserving all other targets and the original five languages.
- RTD deployment and actual live-page acceptance.

Candidate4 has local visual/content acceptance; it is not yet deployed.
