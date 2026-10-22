# Just-in-time document map

Paths below are relative to this reference in the incubation repository. Follow
the relevant link; do not preload every document or create another SSOT.

| Task | Read | Authority |
| --- | --- | --- |
| Architecture / feature boundary / dependency | [Charter](../../../../code-as-doc/dev/research-intelligence-charter.md) before changing anything | Long-term direction, current/future concepts, migration, data decisions, acceptance/rollback |
| Schema / package API / adapter / output | [Contract](../../../../code-as-doc/dev/product-intelligence-contract.md) | Current event-first schemas and package/host boundary |
| Scope / phase / delivery sequence | [Demo Plan](../../../../code-as-doc/dev/product-intelligence-demo-plan.md) | Incubation delivery and deferred independent-repository work |
| Operator-facing change | [Operator guide](../../../../user-guide/hello_auto-doc/product-intelligence-demo.md) | Commands and offline examples; live section is gated |
| Live test planning / migration acceptance | [Pending runbook](../../../../code-as-doc/tests/external_intel_live_integration_2026-10.md) | Migration prerequisites and future T0–T5; not executable in auto-manual |
| Host-side rendering / optional lens | [Module map](../../../../code-as-doc/dev/orchestration_module_map/decomposition-candidates.md) | Host adapter ownership; no requirement to depend on Hello-Docs |

## Discovery in this repository

Claude Code discovers `.claude/skills/research-intelligence-architecture/SKILL.md`
from the repository root and its descendants, including a session started at
`tools/intel/`. Only its name/description is available before selection; the body
loads on invocation or task match, and this reference loads only when needed.
This Skill does not change the root `CLAUDE.md` or `AGENTS.md`. The directory-local
`tools/intel/CLAUDE.md` imports its local `AGENTS.md` and explicitly directs the
agent to read the host rules if not already loaded. Do not assume every client
injects all ancestor `AGENTS.md` files; the verified CLI loads the nearest one
when starting in the core. The local file links the same Skill for Codex/manual
loading. No duplicate `.agents/skills` copy is required.

From either repo root or `tools/intel/`, invoke
`/research-intelligence-architecture`; confirm it appears in the session's skill
inventory. Startup modes that disable skills cannot prove discovery. A cloud
environment that does not load repository skills must explicitly read the linked
`SKILL.md` and this map; do not assume desktop discovery proves cloud loading.
Claude's [Skills documentation](https://code.claude.com/docs/en/skills) describes
project skills and supporting files. A frontmatter validator alone does not
prove discovery; use the actual installed loader. Record the evidence in the
description of the PR that adds or moves this Skill.

## Independent-repository targets (not created in auto-manual)

Move `tools/intel/AGENTS.md` to the new repository's root `AGENTS.md`, adapt host
references there and make a root `CLAUDE.md` importing it. Move this Skill to the
new root `.claude/skills/research-intelligence-architecture/`. Preserve one copy
of the charter, contract, plan and migrated runbook under `code-as-doc/`, and move
the platform operator sections to the new repository's own guide. Rebase every
link here and in the Skill/local entrypoints after extraction (their relative
depths change), update module/test names and rerun loader/link/standalone checks.
Do not transplant auto-manual's global production rules into the new platform.
