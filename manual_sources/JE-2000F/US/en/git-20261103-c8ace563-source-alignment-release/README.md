# JE-2000F US English approved release snapshot

This snapshot is approved under operator authorization MA-381. `publication_eligible=true`; deployment is a separate operation. Source: `manual_sources/JE-2000F/US/en/git-20261103-c8ace563-source-alignment`. All candidate content, geometry, artwork and local review evidence are preserved. Historical candidate status in copied evidence records its original acceptance time.

Rebuild with `python rebuild.py --output <unused-directory>` from a repository runtime matching every recorded `repo_inputs` hash. No runtime pin was changed for approval. `source/approval.json` binds the current source inputs; `evidence/release-authorization-equivalence.json` records the approved cold build and exact content equivalence.

## Original candidate notes (historical)

# JE-2000F US source-alignment candidate

Status: `candidate-pending-operator-review`; `publication_eligible=false`. Whole-body local source/content/layout review is complete; publication approval remains separate.

Own current PDF: `JE-2000F-US-EN.pdf` (`c8ace563cc4575909156b4bcd224016fbd30cf9f8f077cd97738638f67e509e4`). Front cover and paper TOC excluded; all body and p22 back contacts included.

Run `python rebuild.py --output <new-directory>` for a source-pinned replay. `source/differences.md` reviews every old layout declaration; `evidence/final-layout-review.json` stores complete local evidence. Native editable text/tables and exact source figures are retained. Source concerns, including p14 HomePower 2000 Plus, remain unchanged.
