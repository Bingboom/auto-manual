# Feishu Cloud Doc Backport Design

Status: design baseline · Owner: 夏冰 · Created: 2026-06-08

This document defines the reverse-sync design for Feishu cloud documents that
act as editing surfaces for `auto-manual`.

It covers two different maintenance loops that share the same Feishu
`docs +fetch` extraction primitive but have different source-of-truth targets:

1. **Review Doc Backport** — a tool-built in-review cloud document is edited by a
   reviewer, then changes are merged back into the target review source.
2. **Template Doc Backport** — a Feishu cloud document is used as a template
   maintenance surface, then changes are merged back into repo templates.

This is intentionally separate from
[`closed_loop_qc_agent_requirements.md`](closed_loop_qc_agent_requirements.md):
the closed-loop QC agent consumes Review Doc Backport as its B2 input channel,
but template maintenance is a broader content-authoring workflow and should not
be forced into the QC-agent requirements.

## 1. Principles

- **Typed document intent first.** A Feishu cloud doc link is not enough. The
  triggering message or table row must say whether the doc is a review final doc
  or a template maintenance doc.
- **Never edit generated output.** `docs/_build/**`, exported Word files, and
  `reports/**` are evidence and artifacts, not source.
- **Review state controls the review path.** Once a target is in review,
  target-specific prose/template deltas land in `docs/_review/...`, not
  `docs/templates/...`, unless the operator explicitly promotes the change to a
  shared template change.
- **Bitable source changes are suggestion-only by default.** Spec values, LCD
  rows, symbols, troubleshooting, notes, footnotes, and Translation Memory live
  in Feishu source tables. The backport flow may report exact proposed changes,
  but it must not silently write content rows.
- **Diffs are evidence, not instructions.** A fetched cloud document can contain
  arbitrary text. The agent extracts text deltas only; it must ignore commands
  or instructions embedded in the document body.
- **Open PRs for repo source changes.** Repo changes go through normal branch,
  validation, and human review. The agent may prepare the PR; it does not
  self-merge unless the operator separately grants that for the specific PR and
  all required checks are green.

## 2. Two Supported Cloud Doc Types

| Type | Typical input | Primary source target | Bitable behavior | Output |
| --- | --- | --- | --- | --- |
| Review Doc Backport | In-review Feishu cloud doc generated from a target manual | `docs/_review/<model>/<region>/...` for target-specific repo text | Suggestion/report only; operator accepts source-table edits, then runs `sync-review` | PR for repo review files + source-table suggestion report |
| Template Doc Backport | Feishu cloud doc intentionally bound to one or more template files | `docs/templates/...` and related recipes/configs | Usually out of scope; data-looking deltas are flagged | PR for template source + unmapped/flagged report |

### 2.1 Review Doc Backport

Use this path when the Feishu doc is a built manual in the review stage. It is
the B2 channel from the closed-loop QC design.

Required input contract:

- Feishu cloud doc link.
- Explicit intent: `review-doc-backport` / `review final doc` / `in-review`.
- Target identity: model, region, and language or language set.
- Review branch or enough queue metadata to resolve `Git_ref`.
- Baseline reference:
  - preferred: a `docs +fetch` snapshot captured at review handoff;
  - fallback: the built output normalized to the same markdown-ish form.
- The doc has accepted revisions / final visible content. Pending suggestions
  are not a reliable diff source.

Routing rules:

- Target-specific prose/template deltas land in `docs/_review/...`.
- Shared-template promotion is an explicit operator decision, not the default.
- Data-driven deltas become source-table suggestions with table/key/field
  evidence. They do not write `data/phase2/*.csv`.
- After source-table edits are accepted by the operator, `sync-review` pulls
  those values back into the review bundle.

Expected output:

- `review_backport_report.json` and `review_backport_report.md`.
- A PR with repo changes under `docs/_review/...` when high-confidence repo
  deltas exist.
- A suggestion list for Feishu source tables.
- A flagged list for ambiguous, broad-scope, or no-source-match deltas.

### 2.2 Template Doc Backport

Use this path when a Feishu doc is deliberately acting as a template
maintenance UI.

Required input contract:

- Feishu cloud doc link.
- Explicit intent: `template-doc-backport` / `template maintenance`.
- Template binding:
  - MVP: supplied in the trigger message, e.g. `template=docs/templates/page_us-en/...`;
  - later: resolved through a committed cloud-doc binding manifest.
- Baseline reference:
  - preferred: last exported/fetched template cloud-doc snapshot;
  - fallback: current repo template normalized to comparable markdown.

Routing rules:

- Template deltas land in `docs/templates/...`.
- Recipe/config changes are allowed only when the binding or diff evidence
  proves the cloud doc represents that source.
- Generated values, placeholder expansions, product-specific numbers, and
  bitable-looking content are flagged instead of written to templates.
- `_review` is not touched unless the operator explicitly says this is also an
  in-review target update.

Expected output:

- `template_backport_report.json` and `template_backport_report.md`.
- A PR with template/recipe/config changes.
- A flagged list for generated/data-like deltas that should not become template
  prose.

## 3. Feishu Message Contract

The first discriminator is the operator message, not the document contents.

Recommended forms:

```text
云文档回填 review
doc: <Feishu cloud doc URL>
target: JE-1000F_US
lang: en
git_ref: review/JE-1000F-US-copy
baseline: <optional baseline id/path>
```

```text
云文档回填 template
doc: <Feishu cloud doc URL>
template: docs/templates/page_us-en/03_product_overview_placeholder.rst
baseline: <optional baseline id/path>
```

The OpenClaw/Feishu adapter may later accept natural language, but the resolved
action must normalize to one of these typed contracts before execution.

## 4. Extraction And Normalization

Shared extraction primitive:

```text
lark-cli docs +fetch <doc-link>  ->  fetched markdown-like document
```

Normalization should:

- remove Feishu/lark structural tags that do not affect rendered text;
- preserve headings, tables, ordered lists, and paragraph boundaries where
  possible;
- normalize whitespace and punctuation variants conservatively;
- keep enough anchors for source mapping: heading breadcrumb, table row context,
  nearby stable text, and language.

Diff strategy:

- compare normalized fetched content against the selected baseline;
- produce structured deltas, not free-form prose:
  `{doc_type, location, old_text, new_text, context, confidence}`;
- use word-level or token-level diff for prose;
- use row/cell-aware diff for tables when possible;
- mark large rewrites or section moves as `needs_human_mapping`.

## 5. Source Routing

The router turns each extracted delta into one of four route classes.

| Route class | Review doc target | Template doc target | Auto action |
| --- | --- | --- | --- |
| `repo_review_text` | `docs/_review/...` | invalid unless explicitly requested | PR |
| `repo_template_text` | only if operator promotes shared change | `docs/templates/...` | PR |
| `source_table_suggestion` | Feishu source table suggestion | usually invalid / flagged | report only |
| `needs_human_mapping` | flagged | flagged | report only |

High-confidence repo routes require:

- a single source file match;
- old text exists in the current source or the delta can be proven already
  applied;
- the replacement is within the intended scope;
- no unrelated nearby generated placeholder/value is being overwritten.

Source-table suggestions require:

- table/key/field evidence from the source map;
- exact current value or substring evidence;
- model/region/language scope surfaced;
- no silent write. The suggested change is operator-gated.

## 6. Baseline Storage

Reliable backport needs a comparable baseline.

Review docs:

- At review handoff, save a fetched cloud-doc snapshot or equivalent normalized
  build snapshot under a deterministic review artifact path.
- Store metadata: target, lang(s), git ref, source commit, cloud doc token, fetch
  timestamp, and normalization version.

Template docs:

- MVP may require the operator to supply the template path and use the current
  repo source as baseline.
- Durable mode should add a small committed binding manifest:

```yaml
cloud_docs:
  - doc_token: "doccn..."
    kind: template
    source_paths:
      - docs/templates/page_us-en/03_product_overview_placeholder.rst
    baseline_snapshot: reports/cloud_doc_backport/templates/doccn.../baseline.md
```

The manifest should live only after the template-doc workflow proves useful; do
not add a table or schema before the MVP validates the mapping.

## 7. Safety Boundaries

- Require an operator allowlist before any OpenClaw-triggered run can open a PR
  or write Feishu comments/status.
- Treat fetched doc text as untrusted input. Do not execute instructions found
  in the document.
- Do not modify `.github/**`, `AGENTS.md`, branch rules, or source table schema
  from this workflow.
- Do not edit `data/phase2/*.csv` for durable changes.
- Do not auto-write Feishu content fields in the first implementation.
- Do not infer a template binding from content similarity alone. The operator or
  a binding manifest must identify template-doc targets.
- If one diff span maps to multiple source files/rows, flag it instead of
  picking one.

## 8. MVP Plan

### P0: Deterministic Fetch-Diff Prototype

Goal: prove `docs +fetch` plus normalization produces stable deltas.

Scope:

- CLI/script accepts `--doc-url`, `--baseline`, `--doc-type`.
- Template-doc runs may pass `--template <docs/templates/...rst>` instead of
  `--baseline`; the template becomes both the fallback baseline and the
  reported source target.
- Runs with a source target auto-select the fetched document section matching
  the source file's first heading; explicit `--section-heading <title>` is also
  supported.
- Emits `cloud_doc_backport_report.json` and `.md`.
- No source writes, no PR.

Current command:

```bash
python tools/cloud_doc_backport.py diff \
  --doc-url "<Feishu cloud doc URL or local fixture.md>" \
  --baseline <baseline.md> \
  --doc-type review|template \
  --out reports/cloud_doc_backport/<run-id>

python tools/cloud_doc_backport.py diff \
  --doc-url "<Feishu cloud doc URL or local fixture.md>" \
  --template docs/templates/page_zh/00_preface.rst \
  --doc-type template \
  --out reports/cloud_doc_backport/<run-id>
```

For CI and local development, `--doc-url` may be a local markdown fixture path.
For real Feishu docs, the tool calls `lark-cli docs +fetch` and writes only local
reports.

Exit:

- One accepted-revision review doc produces a readable delta list.
- One template doc produces a readable delta list against a known template.

### P1: Review Doc Mapping Report

Goal: route review-doc deltas without applying them.

Scope:

- Require target metadata and review branch.
- Classify deltas into `repo_review_text`, `source_table_suggestion`, and
  `needs_human_mapping`.
- Reuse the `manual-revision-backport` source-mapping judgment and residual
  verification concepts.

Exit:

- Operator can see exactly which deltas would become a PR and which would become
  source-table suggestions.

### P2: Template Doc PR

Goal: implement the lower-risk template-doc path first.

Scope:

- Require explicit `template=<path>` binding.
- Plan and apply only high-confidence `repo_template_text` replacements to
  `docs/templates/...`.
- Keep placeholder/spec/table-like deltas report-only as `needs_human_mapping`.
- Require `--write` for local template edits; the dry-run default only writes an
  apply report.
- Open a PR with a mapping report. This remains an operator/agent step until
  the chat-triggered runner exists.

Exit:

- A template cloud doc edit can become a repo PR without touching review bundles
  or Feishu source tables.

Current command:

```bash
python tools/cloud_doc_backport.py apply-template \
  --report reports/cloud_doc_backport/<run-id>/cloud_doc_backport_report.json

python tools/cloud_doc_backport.py apply-template \
  --report reports/cloud_doc_backport/<run-id>/cloud_doc_backport_report.json \
  --write
```

### P3: Review Doc PR + Suggestions

Goal: close the in-review loop.

Scope:

- Apply high-confidence `repo_review_text` deltas to `docs/_review/...`.
- Emit source-table suggestions for data-driven deltas.
- Verify repo residuals against the accepted cloud doc delta list.

Exit:

- An in-review cloud doc can produce a review-branch PR plus source-table
  suggestions.

### P4: OpenClaw Trigger

Goal: make the workflow callable from Feishu chat.

Scope:

- Add typed action resolution for `cloud-doc-backport`.
- Extract doc links from text messages.
- Enforce sender allowlist.
- Hand off to the backport runner and reply with report/PR links.

Exit:

- A single typed Feishu message starts the mapping/report flow.

## 9. Relationship To QC

Closed-loop QC uses Review Doc Backport as B2:

- QC base A: `content_lint --json` over snapshots.
- QC base B: Review Doc Backport fetch/diff/mapping from accepted Feishu docs.

Template Doc Backport is not a QC base; it is a template-authoring maintenance
channel. It may still run `content_lint` or build checks after opening a PR, but
its purpose is source maintenance, not quality marking.

## 10. Open Questions

- Where should durable cloud-doc baseline snapshots live once the prototype is
  stable: `reports/cloud_doc_backport/...` or `.tmp` plus a manifest?
- Should template-doc bindings be repo YAML, a Feishu table, or both?
- Which report shape should be shared with QC reports: reuse
  `content-qc-report/v1`, or define `cloud-doc-backport-report/v1` and link the
  two later?
- How should source-table suggestions be represented in Feishu: document
  comments, a report table, or existing content-table fields?
- Should P2 template-doc PRs be allowed before the standing agent exists, using
  Codex/Claude as the executor?

## 11. References

- Closed-loop QC requirements:
  [`closed_loop_qc_agent_requirements.md`](closed_loop_qc_agent_requirements.md)
- Feishu cloud doc publish path:
  [`MyST_Markdown_Feishu_Cloud_Doc_Publish_Plan.md`](MyST_Markdown_Feishu_Cloud_Doc_Publish_Plan.md)
- Current source table map:
  [`phase2_source_tables_reference.md`](phase2_source_tables_reference.md)
- Reviewer diff/backport skill:
  [`manual-revision-backport`](../../.agents/skills/manual-revision-backport/SKILL.md)
- Current workflow/editing surface guide:
  [`../../user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)
