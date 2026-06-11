# User Guide Directory

`user-guide/` contains operator-facing workflow documentation.

## Map

- `hello_auto-doc.md`: current human workflow guide.
- `quick_start_guide.md`: happy-path onboarding and sample commands.
- `dingtalk_alidocs_upload_setup_guide.md`: DingTalk/AliDocs setup workflow.

## Local Rules

- If a code change affects current workflow, editing surface, environment setup, or release flow, update `hello_auto-doc.md`.
- If a code change affects the happy-path example, onboarding steps, or target-specific sample commands, update `quick_start_guide.md`.
- Keep commands copy-pasteable and aligned with `build.py`.

## Validation

- Docs link check: `python3 tools/check_doc_link_integrity.py`
- For changed sample commands, run the matching command or explain why it was not run.
