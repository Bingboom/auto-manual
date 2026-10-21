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
the independent repository and the charter's migration gate. Keep PR #1585's
base `feat/product-intelligence-demo`; do not merge or modify `main`.
