# InDesign Finalize Batch Acceptance — 2026-07-31

## Scope

This record covers Workstream W Stage 4a item 12: one ExtendScript outer loop
per InDesign application group, with per-document failure isolation. It does not
approve a production manual, reference-layout parity, or the fixture content.

Design host:

- Adobe InDesign 2026 21.0.1.6
- committed version pin: exact match
- runner: `python tools/indesign_finalize.py --jobs <manifest.json>`
- both manifests contained two jobs with `application=Adobe InDesign 2026`

All acceptance outputs were written under `/private/tmp`; no generated output
was committed.

## Run 1 — failure isolation with production and flow IDML

The first manifest used the locally built JE-1000F US production and flow IDML
files. InDesign returned `用户已取消此动作` while the first document was at
`stage=export_pdf`. The JSX batch did not abort: the second document opened,
saved its INDD, exported its PDF, wrote its report, and reached
`stage=complete`.

Observed second-job evidence:

- page count: 52
- exported PDF/X-4: pass
- output intent: Japan Color 2001 Coated / JC200103, pass
- preflight result: fail because the existing flow handoff has eight overset
  stories

This run proves that one document's InDesign exception does not cancel the
following document in the same JSX loop.

## Run 2 — two complete export paths in one dispatch

The second manifest packaged the committed English and French IDML golden
trees into two separate IDML inputs. Both documents reached `stage=complete`
in one application-group dispatch and independently produced:

- INDD;
- PDF;
- `indesign-preflight/v1` report; and
- an entry in the aggregate `indesign-finalize-jobs/v1` report.

| Job | Pages | INDD | PDF | Report | Fixture preflight |
| --- | ---: | --- | --- | --- | --- |
| golden-en | 11 | written | written | written | 2 overset, 36 unresolved fixture links |
| golden-fr | 11 | written | written | written | 2 overset, 32 unresolved fixture links |

The expected fixture preflight failures are content/package limitations of the
unpacked golden trees; neither job has an export-stage error. They do not weaken
the batch-loop acceptance claim.

## Result

Machine/design-host execution evidence: **passed**.

- one dispatch processed two documents sequentially;
- each document wrote independent outputs and preflight evidence;
- a first-document exception did not prevent the second document from running;
- aggregate order matched manifest order; and
- the repository and its generated build directories were not mutated.

The operator may still inspect or amend this record before merging the PR; no
production parity or release approval is implied.
