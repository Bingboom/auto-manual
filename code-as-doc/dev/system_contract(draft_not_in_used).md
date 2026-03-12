# System Contract Draft (Not In Use)

Updated: 2026-03-12

Status:

- draft only
- not normative
- not used as the contract for the current build and review system

The current working contract is distributed across these active documents:

- [`code-as-doc/code_style_guide.md`](../code_style_guide.md)
- [`code-as-doc/spec_master_user_guide.md`](../spec_master_user_guide.md)
- [`code-as-doc/build_doc_guide.md`](../build_doc_guide.md)
- [`user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)

Current implemented system features include:

- shared config families instead of per-model config sprawl
- [`build.py`](../../build.py) as the main entrypoint
- `_review` as the review authoring surface after review starts
- `sync-review` for data-driven refresh during review
- `publish` for formal release
- `diff-report` for revision export
- page contracts for selected placeholder-heavy pages

Keep this file only as an archive marker for an abandoned draft direction.
