# JBP-3600A EU reviewed nine-language release

MA-244 binds the actual 2026-10-03 operator publication instruction to EN r6 / FR r5 / ES r3 / DE IT UK PT NL PL r2. See [approval](approval.json) and [unchanged content proof](approval-parity.json). Reviewed native source differences are retained. The paper-manual version remains unknown.

`web/<language>` is a new approved snapshot. Only review/admission metadata differs from the immutable accepted candidates. Native wording, tables, image bytes, CSS clock and layout are unchanged. Eight locale policies use the independently reviewed English chapter/component applicability, with source exceptions recorded explicitly. PR1409 is not a dependency of current admission.

Git-only: no live source, queue, asset or link writes. Strict Sphinx, cold replay, build regression checks and final deployment receipts are separate release gates.
