# Research & Intelligence Incubation

Read the [root `AGENTS.md`](../../AGENTS.md) before editing; it remains the
host's operating authority even when a client loads only the nearest local file.
This directory is the
separable research core; its architecture authority is the
[charter](../../code-as-doc/dev/research-intelligence-charter.md).

For architecture, boundary, feature or migration work, read the
[architecture Skill](../../.claude/skills/research-intelligence-architecture/SKILL.md)
and only the task-relevant documents it routes to. Codex can read that file
directly; Claude discovers it from the project's `.claude/skills/` directory.

Only static, fixture/fake-transport and standalone checks run here. Real Feishu
reads/writes (including sync dry runs), Base/group creation and sends wait for
the independent repository and the charter's migration gate. PRs for this core
target the incubation branch `feat/product-intelligence-demo`; never merge into
or modify `main`.

## Validation

All offline; none of these calls Feishu.

- Package and boundary tests: `python3 -m unittest tests.test_intel_events tests.test_intel_digest tests.test_intel_sync tests.test_intel_push tests.test_intel_cli tests.test_intel_feishu tests.test_intel_wiki tests.test_external_intel_boundary`
- Lint: `python3 -m ruff check tools/intel tests/test_intel_*.py tests/test_external_intel_boundary.py`
- After a charter, contract, plan, guide or runbook change: `python3 -m tools.check_doc_link_integrity`
