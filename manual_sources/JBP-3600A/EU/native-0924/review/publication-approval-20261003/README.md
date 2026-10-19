# Approved JBP publication preflight

MA-244 records the actual operator instruction to merge and publish the reviewed eight native languages and their necessary English r6 baseline. The [approved source](../../../git-20261003-44b6ce61-reviewed/README.md) is a new immutable package; all historical candidates and seals remain intact.

- `approved-verification.json`: nine fresh-admission passes, strict Sphinx, cold rebuild and exact HTML equality against independent final acceptance; original candidates remain blocked.
- `approved-package-independent.json`: independent follow-up from the originating review chat; all nine HTML hashes and 21/22 PNG bytes match its prior acceptance.
- `trial-scope.json`: existing assembler produces 96 targets; the other 87 target records and 4658 source files remain unchanged. Aggregate Sphinx passed; its shared stylesheet hash is `0319fe2d03c6963e47cec388fc0599910dcda39d39a5b530377a01a8d7425d87`, exactly the reviewed candidate stylesheet.

Admission reports are stored beside the source, outside each publishable Markdown root, because the existing assembler supports only the canonical manual sidecars. The original 27/28-file candidate packages become 26/27-file approved Markdown packages; the displaced report is preserved in `admission/<language>.json`. No visible content changed.

PR1409 is absent from the current admission call chain and is not a release dependency. Current admission checks trusted locale policies, native pending-review resolution, ComponentSpec slots and actual asset bytes. Existing phase2 checks are regression coverage; native body acceptance is independently recorded.

The trial is a preflight, not an engineering merge, publication or RTD receipt. Final code validation and deployment evidence are recorded separately.

## Secret-scan false positives

The initial PR scan matched four SHA-1 `run_key` values in two sealed unit-test logs. PDF annotation and TM hit-rate code derive these from test content. The logs remain byte-identical. A rule-specific exception requires both exact log paths and exact field/digest values; five negative cases verify that changed values, field names, paths and synthetic credential shapes remain blocked. See `secret-scan-resolution.json` and `gitleaks-boundary-result.json`. The full tracked-file scan with CI version 8.30.1 passes with zero findings.
