# Code Optimization Log

Updated: 2026-11-20

This file records major maintainability milestones.
It is a history log, not the day-to-day usage guide.

Recent records stay here, newest first; add new records at the top. Older
records (the numbered 2026-03 to 2026-08 entries, the 2026-09 to 2026-10-03
operations/CQ entries, and the archived roadmap sections) are in
[`code_optimization_log_archive.md`](code_optimization_log_archive.md).
Grep the archive when you need history; do not read it whole.

For the active optimization checklist, use:

- [`next_optimization_checklist.md`](next_optimization_checklist.md)

For current rules, see:

- [`code-as-doc/README.md`](README.md)
- [`code-as-doc/build_doc_guide.md`](build_doc_guide.md)
- [`code-as-doc/code_style_guide.md`](code_style_guide.md)
- [`user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)

## 2026-11-19 to 2026-11-20: Web-first CLI, CI Node 24, strict mypy expansion, and portal v1.2

- **RTD portal & Product-Matrix v1.2**: shipped the four-asset-layer `知识资产`
  overview, `产品信息矩阵` (`v1.2` snapshot freshness, `产品档案`, `产品对比`,
  `参数表`, evolution timeline, and sync/review-PR shortcuts), and private RTD
  v3 Builds API + local publish-tree verification (`#1735`–`#1737`,
  `#1741`–`#1745`, `#1748`–`#1749`, `#1752`, `#1757`–`#1759`, `#1770`,
  `#1774`, `#1777`, `#1779`–`#1781`, `#1784`–`#1786`, `#1790`, `#1793`,
  `#1795`, `#1796`).
- **Web-first CLI & CI gate (`#1799`, `#1800`)**: wired `web-package`, `ir-qc`,
  and `ir-export` into [`build.py`](../build.py) (`#1799`, over `#1751`/`#1754`/`#1755`)
  and added the `web-ir-checks` job to `Manual Validation` (`#1800`).
- **GitHub Actions Node 24 & snapshot mirror sync (`#1801`)**: upgraded official
  Actions across 17 workflows and 3 composite actions to Node 24 majors
  (`checkout@v7`, `setup-python@v7`, `setup-node@v7`, `cache@v6`,
  `upload-artifact@v7`, `github-script@v9`), switched `sync-hello-docs.yml`
  checkouts to `fetch-depth: 1` with parentless `refs/sync/snapshot` bundles in
  [`scripts/sync_mirror.sh`](../scripts/sync_mirror.sh), and added `filter: blob:none`
  to read-only history checks — zero Node 20 warnings and mirror sync cut from
  `5m57s` (`#1800`) to `2m37s` (`#1801`, `−56%`) / `~2m13s` (`#1802`, `#1806`).
- **Strict `mypy` Web-first core expansion (`#1802`)**: cleared all 312
  `mypy --disallow-untyped-defs` errors across `tools/corpus` (0),
  `tools/product_matrix_base` (8 → 0), `tools/manual_knowledge` (22 → 0),
  `tools/rtd` (124 → 0), and `tools/web` (158 → 0), enrolling them alongside
  CQ-4.5 packages `tools/manual_ir`, `tools/component_specs`, and
  `tools/csv_pages` in `pyproject.toml` and
  [`tools/check_mypy_ratchet.py`](../tools/check_mypy_ratchet.py) (`8` ratchet
  packages + separately configured `tools/utils` = `9` strict-checked packages:
  `98 → 260` files, `19,603 → 61,306` LOC = `30.18%` of `tools/`'s `733` files /
  `203,108` LOC at `0` baselined errors; `keep-frozen` recorded in
  `data/frozen_package_registry.json`).
- **Catalog & asset-registry sync (`#1804`, `#1805`, `#1806`)**: added
  bot-accessible catalog table fallback in
  [`.agents/skills/product-manual-catalog/SKILL.md`](../.agents/skills/product-manual-catalog/SKILL.md)
  (`#1804`), synced verified Feishu asset definitions/sources into
  `data/asset_registry.csv` and `data/asset_sources.csv` (`#1805`), and preserved
  CN App sizing after Web asset hashing (`#1806`).

## 2026-11-18 to 2026-11-19: Binary externalization, mirror pruning, and repo slimming

- **External source pointers & binary ratchet (`#1783`, `#1787`, `#1789`, `#1791`, `#1792`)**:
  added `external-source-pointer/v1` + `data/raw_binary_ratchet_baseline.tsv`
  (`#1783`) and externalized `201/204` tracked `.ai`, `.bin`, and `>1 MiB` `.pdf`
  binaries (`1,677.00 MiB`) to Feishu Base pointers, shrinking the ratchet
  baseline `204 → 3` rows (`6.40 MiB` legacy label/cover PDFs left; `0` tracked
  `.ai`/`.bin` files).
- **`Hello-Docs` mirror overlay pruning (`#1794`)**: added
  [`tools/web/mirror_overlay_prune.py`](../tools/web/mirror_overlay_prune.py)
  (`MIRROR_OVERLAY_PRUNE_EXTERNALIZED=1`) so upstream-absent overlay files
  superseded by validated pointers are pruned from `Hello-Docs` `main` (`201`
  residuals / `1,677.00 MiB` dropped while keeping non-externalized downstream files).
- **Generated build & MA registry cleanup (`#1797`, `#1798`)**: untracked all
  234 generated files under `docs/_build/` (`157.61 MiB`, `#1798`) and
  batch-archived 89 expired `MA-*` rows (`MA-470`–`MA-179`) into
  `dev/merge_authorizations_archive.md` (`149 → 60` lines, `#1797`).

## 2026-11-16 to 2026-11-18: Legacy retirement and Bitable/TM-B hardening

- **Legacy surface retirement**: retired `site/` & review-preview packager
  (`#1728`, `−4,436` lines), removed DingTalk & Wukong modules/workflows (`#1733`,
  `−13,398` lines), gated 8 legacy template queue/cron workflows behind
  `LEGACY_TEMPLATE_QUEUE_ENABLED` (`#1756`), and added skills lifecycle
  frontmatter governance (`#1773`).
- **TM-B & Bitable reliability**: filtered TM-B reads to `Approved` rows and
  lifted the 2,000-row pagination cap (`#1729`), synced TM-B schema manifest &
  aligned `eu-pt`/`nl`/`pl`/`zh-TW` columns (`#1776`); hardened Bitable backups
  with aligned coordinates (`#1730`), bounded `429` retry + `O(1)` `record-get`
  readback (`#1746`), attachment inventory & business-key link restore (`#1747`),
  and nightly 50-field projected backups of the product matrix base (`#1761`).

## 2026-10-13: Module map, RTD portal, Web publish and quick start split into pages

The next tier of agent-facing docs (11–15K tokens each) followed the 2026-10-12 split:

- `dev/orchestration_module_map.md` keeps the entrypoint rule (§1) and the maintenance
  rules (§8); each module family (§2–§7, §9) is a page.
- `dev/rtd_manual_portal.md` is an index over four pages: manual center, system
  workspace, workspace and knowledge-base pages, maintenance and checks.
- `dev/web_publish_pipeline.md` keeps the two release actions (§1); §1.1, §2, §3,
  §4–§5 and the shared-component admission are pages. A compatibility anchor keeps the
  §2.2 links in frozen source-package READMEs working without touching their approval
  hashes.
- `user-guide/quick_start_guide.md` keeps the core rule, §6 and §9; the rest is five pages.
- Content moved verbatim; 42 deep links point at the owning page, and the
  maintainability guardrails cap the four hubs.

## 2026-10-12: Optimization checklist and style definition split into pages

The next two largest agent-facing docs followed the 2026-10-10 split:

- `next_optimization_checklist.md` (~40K tokens) keeps its update rules,
  baseline, deferred list and success criteria plus an index; each milestone
  (A–D, E to M, and the Milestone M slices) is a page under
  `next_optimization_checklist/`.
- `docs/renderers/contracts/STYLE_DEFINITION.md` (~37K) keeps the §1 binding
  table and §8, which tests read, plus an index; §0, §2–§7, §9, §10, the
  appendices and the Web artwork reuse rule are pages under `STYLE_DEFINITION/`.
  The 30 deep links into moved sections, AGENTS.md §3 among them, point at
  the pages.
- Content moved verbatim; the maintainability guardrails cap both hubs.

## 2026-10-04 to 2026-10-12: Machine-readable EU corpus, observation and governance

The machine-readable program runs EU first; each phase has its own plan and acceptance record in `dev/`.

- Phase 1 Machine Corpus (2026-10-04): manual-variant identity and provenance (#1434), the sealed
  machine-surface manifest and freshness check (#1435), workbench coverage (#1436) and the
  pilot audit (#1437); online checks closed with #1439.
  [Plan](dev/machine_readable_manual_corpus.md).
- Phase 2a Knowledge Observation (2026-10-11): the offline `observe` command (#1488–#1491),
  accepted in the [pilot audit](dev/machine_readable_knowledge_pilot_audit.md) (#1492), which
  lists 23 issues for the content owners.
- Phase 3a Knowledge Governance (opened 2026-10-12): the findings-ledger contract and check
  (#1495), `verify` / `propose` (#1498), the coverage matrix (#1503) and authority bindings
  (#1505) shipped as P3-0…P3-3. At P3-3 all 23 ledger entries were still `candidate`; the
  full acceptance P3-4 is open ([plan](dev/machine_readable_knowledge_governance.md) §7).

## 2026-10-10: Agent-facing docs split for on-demand reading

Parallel agent rounds (the Workstream Y lanes, #1350–#1423) paid for the same
documents once per agent: AGENTS.md sent every agent to `build_doc_guide.md`
(~76K tokens) and `hello_auto-doc.md` (~70K), merge grants lived in a 360 KB
registry (~109K), and this log had reached ~52K. Following CQ-7.5/7.6 (#1321):

- `build_doc_guide.md` and `hello_auto-doc.md` are indexes (54 and 40 lines) over
  20 and 17 topic pages of at most ~7.7K tokens. Content moved verbatim and was
  regrouped by topic; links were rebased and the four deep links repointed.
- `dev/merge_authorizations.md` keeps the protocol and only the live grants; the
  239 expired rows and the addenda moved to `merge_authorizations_archive.md`,
  and `next_registry_id` counts both files.
- This log keeps its recent records; older ones moved to
  [`code_optimization_log_archive.md`](code_optimization_log_archive.md).
- AGENTS.md §10 sets on-demand reading and sub-agent briefing; §5 and
  `code-as-doc.md` Rule 7 send new notes to the owning page; the maintainability
  guardrails cap the five hub and live files.
