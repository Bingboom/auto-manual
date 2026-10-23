---
name: research-intelligence-architecture
description: Review or change the incubating Research & Intelligence platform's architecture, feature boundaries, contracts, Agent context or repository migration. Use for tools/intel and the research charter/plan/contract; unrelated Hello-Docs manual production stays under host rules.
---

# Research & Intelligence Architecture

1. Before architecture or feature changes, read the
   [charter](../../../code-as-doc/dev/research-intelligence-charter.md). It owns
   platform direction, future concepts, current limits and migration gates.
2. Use the [document map](references/document-map.md) to load only the contract,
   plan, operator guide or runbook needed by this task. Existing documents remain
   authoritative; do not copy their schemas or procedures into new instructions.
3. For a new feature, state the research question it serves, what evidence and
   human judgment it needs, and whether it changes the platform boundary,
   contract, data custody or external dependencies. Mark proposed capabilities
   separately from implemented and verified behavior. Do not implement broader
   models or integrations just because the charter names future concepts.
4. In auto-manual, validate with fixtures/fake transports and standalone tests
   only. Real Feishu reads/writes, Base/group creation and messages wait for the
   independent repository's migration gate; a sync dry run still reads the table.
   A runbook, existing credential or incubation merge does not unlock that gate.
5. Keep the host operating rules, and target this core's PRs at the incubation
   branch `feat/product-intelligence-demo`. Report document checks, skill
   discovery, standalone validation and live acceptance separately. Nothing from
   the incubation branch merges into `main` or deploys.
