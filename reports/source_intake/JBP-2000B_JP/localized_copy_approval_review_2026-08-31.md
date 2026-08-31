# JBP-2000B_JP localized-copy approval review

Reference PDF SHA-256:
`f7830bf9fb96d9a3e36737bad5196bbfac2d262eaef642f3406fe77eecd02b0b`.

Operator approval was recorded and the 22 target-data operations were executed
on 2026-08-31 with the business-plane `prod/bot` identity:

| Area | Count | Evidence and write mode |
| --- | ---: | --- |
| Symbols | 7 | Japanese fields patched; JP appended to Market; 7/7 same-record readback |
| LCD | 2 | Japanese label/description fields patched; 2/2 same-record readback |
| Troubleshooting | 13 | JP-only rows created; 13/13 readback; seven existing US rows unchanged |

## Symbol approval boundary

The seven descriptions are printed source text. `label_jp` and `aliases_jp`
are not printed headings: they are inferred semantic metadata for indexing.
That separate approval scope is recorded as true in the JSON evidence.

## LCD source normalization

The first LCD label/description now preserves the printed ASCII-parenthesis
form `バッテリー残量(%)`; the earlier full-width-parenthesis candidate was
rejected as an unrecorded normalization.

## Troubleshooting structure

HTP017 prints these thirteen rows in order:

`F0, F1, F2, F3, F4, F5, F6, F7, F8, F9, FA, FC, FF`.

The existing US source groups `F1, F2` and `F6-F9, FA, FC` into seven rows.
Retagging those records for JP would alter the printed JP structure, so the
proposed operation creates thirteen JP-only rows and does not mutate US data.

Exact record fields, created/updated record IDs, Market readback, and text are
in `localized_copy_approval_2026-08-31.json` under `write_evidence`.
