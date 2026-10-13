# Web Publish Pipeline

Status: active

This document owns the release contract for responsive manuals published to
Read the Docs. Web delivery is intentionally separate from print delivery.

## How to use this contract

This file keeps the two release actions (§1) and this index. Every other section moved,
with its number, to a page: open only the page your task needs and change the contract
on that page. Add a row here only for a new page.

| Section | Page | Read it when |
| --- | --- | --- |
| §1.1 | [`semantic-tables-and-figures.md`](web_publish_pipeline/semantic-tables-and-figures.md) | you change how Web publish carries semantic tables and frozen figures |
| §2 | [`input-paths.md`](web_publish_pipeline/input-paths.md) | you run or change a Web Publish input path: the queue-driven transaction, the Git-only transaction, or the catalog mirror and reconciliation |
| §3 | [`hosting-boundaries.md`](web_publish_pipeline/hosting-boundaries.md) | you need the repository and hosting boundaries, or the hosting convergence and legacy entry review |
| §4, §5 | [`operator-contract-and-rollback.md`](web_publish_pipeline/operator-contract-and-rollback.md) | you need the operator contract, the receipt timing, or how to roll a Web publication back |
| Admission | [`shared-component-admission.md`](web_publish_pipeline/shared-component-admission.md) | you admit shared Web components for a native multilingual source |

<a id="22-git-only-transaction"></a>Links to §2.2 *Git-only transaction* from frozen source-package
READMEs, which their approval hashes keep unchanged, land here; the section is on
[`input-paths.md`](web_publish_pipeline/input-paths.md#22-git-only-transaction).

## 1. Two independent release actions

| `Workflow_action` | Worker | Output authority |
| --- | --- | --- |
| `Publish` | `feishu-build-queue.yml` | IDML, LaTeX, PDF, DOCX, formal Markdown and release manifests |
| `Web Publish` | `feishu-web-publish-queue.yml` + `web-publish-receipt.yml` | frozen MyST candidate under `Hello-Docs/publish:docs/publish/`, a scope-guarded PR into `main`, and — after that PR merges and the deployment verifies — `HTML_link` |

`Publish` never deploys HTML. `Web Publish` never uploads or rewrites print
artifacts. Both actions render reviewed content selected by
`Document_link.Git_ref` with the current `main` toolchain.

The table above describes the queue-driven input path. An authorized Git-only
release can instead use reviewed, committed sources and assets without creating
queue rows or reading or writing online tables. It does not change either
workflow. Both input paths converge on the same assembler, the same
`docs/publish/**`-only release PR, and the same Read the Docs production build.
Explicit Git-only [withdrawal/restoration](web_publication_withdrawal.md) uses
the same assembly and atomic promotion helpers with a durable action ledger.
Publication omission still means preservation; withdrawn versions cannot be
reintroduced by an ordinary retry.
