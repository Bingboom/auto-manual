# JE-3000C EU PV line break acceptance

- PT/NL/PL native-source builds and strict Sphinx builds passed.
- Source-free replay retains one explicit break inside the existing DC input cell; missing/ambiguous markers and missing rows fail closed.
- Full manual visible text matches the respective released snapshots after whitespace normalization. Artwork bytes are unchanged. Dutch AC and combined car input 8 A corrections remain intact.
- Desktop browser checks cover all three languages. Portuguese also checked at 390 × 844: PV starts below the car description and wraps within the cell. See the adjacent screenshots and parity.json.
- ruff, maintainability guardrails and documentation links passed.
- build.py check passed with configs/config.us-en.yaml, JE-1000F/US and the existing root phase2 snapshot; this is a repository regression, not semantic validation of these frozen language bodies.
- Aggregate publication Sphinx build passed with -W --keep-going. The publication diff is 28 files, all three target locales plus publish_manifest.json; unchanged six original languages and other targets.

Source snapshot commit: 29cd41011ca4069d31e7d2809dc16e6577906753. Publication and live acceptance are tracked separately; these are local verification results.
