# Production-Readiness Review — 2026-07-17

Reviewer: Claude Code (four parallel deep-dives: architecture/coupling, maintainability, enterprise ops, scalability; findings verified against files at HEAD `ecdcb83`).

Purpose: assess the repo as a future multi-developer enterprise platform (10 devs / 50 product lines / hundreds of templates), not as a single-operator automation project. The execution plan derived from this review lives in [`../optimization_project.md`](../optimization_project.md) Workstreams T / U / V.

## Verdict

The **code plane is already enterprise-grade** (real behavior-level tests, CI-enforced size ratchets, no dependency cycles, centralized path handling, documented bus-factor register, release manifests with toolchain provenance and per-output sha256). The **operating plane is not**: a single operator gates every flow, one delivery leg runs on one Mac, the frozen-copy review-branch model makes shared fixes O(N) manual work, observability is print-based with no alerting on the queue path, and the Feishu source-of-truth has no durable backup.

Scores: Architecture **B** · Maintainability **B** (code A−, operations C) · Enterprise readiness: **not yet** — gaps are operational/organizational, not code quality.

## 1. Architecture — B

Well-architected:

- No import cycles found in any suspected hotspot (`build_docs` facade, `cloud_doc_backport_*` cluster, `queue_*`).
- [`../../tools/config_loader.py`](../../tools/config_loader.py): minimal `extends:` deep-merge with cycle detection; 17 leaf configs over 3 bases.
- [`../../tools/utils/path_utils.py`](../../tools/utils/path_utils.py): 58 importers, rule-enforced; no path-segment sprawl.
- [`../../tools/check_maintainability_guardrails.py`](../../tools/check_maintainability_guardrails.py): CI-enforced line ratchet on 40 hotspots, some pinned with zero headroom.
- `tools/idml/`: the model package — 41 files, nested `components/` registry.

Structural problems:

1. **234 flat files in `tools/`** with filename prefix as the only boundary; queue (~37), word bundle (13), backport (13), intake (~13), sync (~13) are unpackaged while idml/utils/dingtalk/manual_ir are proper packages. Nothing enforces import direction between prefix families.
2. **Feishu transport duplicated 5+ ways**: [`../../tools/feishu_record_transport.py`](../../tools/feishu_record_transport.py) has one importer, while independent `run_lark_cli_json`-style runners exist in `queue_lark_ops.py`, `listen_build_queue_lark.py`, `listen_build_queue.py`, `spec_master_rebuild.py`, `bitable_schema.py`, plus hand-rolled `lark-cli` argv in ~19 files. Retry/rate-limit/error semantics cannot be fixed in one place.
3. **`tools/build_docs.py` doubles as a shared library**: 8 non-build modules (incl. queue code, `queue_bound_outputs.py`) import the 838-line facade just for `load_config` / `resolve_build_targets`, dragging in Sphinx/export machinery transitively.
4. **Two dispatch paradigms in one CLI**: `build_dispatch.py` mixes in-process calls with subprocess argv shell-outs that re-invoke sibling scripts — different error/observability semantics per command.
5. **DI ceremony**: `dispatch_action` takes 28 callables mirrored by a 28-field `DispatchContext`; `build.py` is 751 lines of shims at its guardrail ceiling.

## 2. Maintainability — B (code A−, operations C)

Code side (strong):

- Hardcoded values actively managed: model names appear in `tools/` only in comments/help text; table IDs are env-driven; no secrets committed (verified by pattern grep).
- Near-zero global state (one renderer registry, 4 `lru_cache`).
- Tests are behavior-level, not snapshot-brittle (152 files; only 4 golden-pattern references, 12 subprocess users).
- Prefix-family "duplication" is documented decomposition, not copy-paste; `audit_code_copy.py` + `check_docs_duplicate_text.py` police the real risks.
- Knowledge is in-repo: `ONBOARDING.md` bus-factor register (§3) + quarterly cold-start drill (§7), table-ID inventory in `user-guide/two_plane_map.md` §1.1, `build.py doctor`, credential-free fixture builds (`--data-root tests/fixtures/phase2`).

Operations side (weak):

- **158 distinct external-service env vars** (`FEISHU_*`, `DINGTALK_*`, `OPENCLAW_*`, `OSS_*`, …); secret values exist only in the Feishu admin console and the operator's home directory.
- **InDesign finalize runs on exactly one Mac** (`tools/idml/indesign_finalize.jsx`), no CI, no version lock — the one delivery leg a successor cannot reproduce.
- The two 100 KB+ guides (`build_doc_guide.md`, `hello_auto-doc.md`) are too large to keep verifiably in sync; ONBOARDING already carries one stale claim ("no lock file" — `requirements.lock` now exists).

## 3. Scalability — what breaks first at 10 devs / 50 lines

Ranked, soonest first:

1. **Shared-template propagation to review branches** — each `review/<MODEL>-<REGION>` branch carries a frozen copy of shared templates; a `docs/templates/**` fix on `main` reaches zero open branches ([`../../tools/check_review_branch_sync.py`](../../tools/check_review_branch_sync.py) is explicitly advisory; a real 2026-07-08 drift incident is cited in its docstring). Only safe propagation is a human `sync-review` per branch with clobber risk. Manageable at ~17 branches; impossible at 200. Requires re-architecture (Workstream V), not tooling.
2. **Single-operator gating** — no self-merge, operator-held sync secrets, per-row ingest confirmation, backport scope judgment. Throughput caps at one human regardless of infra.
3. **Serial CI queue + uncached TeX** — `feishu-build-queue.yml` globally serialized, plain `for` loop in `queue_orchestration.py`, full TeXLive apt install every run, `xelatex_runs: 3` per target. Org Actions quota was already exhausted once at current scale.
4. **Git binary growth, no LFS** — pack 147.7 MiB; two 18.9 MB PDFs under `docs/_build/**/latex/assets/`; orphaned multi-MB release blobs in history; one model ≈ 158 MB uncompressed tracked under `docs/_build`. Committing the RST intermediate is sound design; the raw binary assets riding along are the problem, and history damage is already irreversible without a rewrite.
5. **200 long-lived review/backport branches** → merge skew, per-date backport variants, opaque `review/id-rec*` names.
6. **Data sync**: full-table pulls of the shared phase2 base per sync; zero retry/backoff/rate-limit in the Python sync path (verified by grep); no file locking → concurrent syncs race on `data/phase2/*.csv`.
7. **Per-region template cloning** (237 files, clone-based new-region setup) with no cross-model inheritance.
8. **Language onboarding edits code**: hardcoded enumerations (`signal_words.py`, `sync_data_models.py`, `localized_copy.py`, `manual_copy_source.py`) plus golden-test expectations.
9. **10-dev collisions**: flat `tools/` namespace, `JE-1000F`-hardcoded fixtures, unmergeable binary conflicts in `docs/_build`.

## 4. Enterprise readiness by dimension

| Dimension | State | Notes |
| --- | --- | --- |
| CI quality gates | OK | 13-job PR validation (lint, guardrails, unittest, scoped mypy, doctor, build smokes) |
| Secrets hygiene | OK | Nothing committed; stdin-fed secrets; daily live credential probe with auto-Issue |
| Secrets lifecycle | Gap | No rotation automation; DingTalk sink runs on hand-refreshed browser-session tokens |
| Reproducible environments | Gap | `requirements.lock` exists but **no CI/RTD job installs from it** (verified); no container; TeX unpinned; InDesign leg unreproducible |
| Release traceability | OK | Manifests: git SHA, toolchain provenance, sha256 per output |
| Versioning & rollback | Gap | No tags/releases; no rollback runbook |
| Observability | Critical gap | Zero `logging` imports, 423 `print()` calls; queue-processing failures open no Issue/notification (sentinels do; the queue does not) |
| Access control | Gap | No `CODEOWNERS` (verified absent); single reviewer; local-only hooks; no secret scanning / dependabot |
| Data governance | Mixed | Structural drift detection excellent (daily prod/dev schema parity); content-level validation and point-in-time Bitable backup/restore absent |
| Queue integrity | Gap | RUNNING write is a soft claim, not compare-and-swap; the three queue workflows share no concurrency group — safe today only because cron is disabled and dispatch is single-operator |

## 5. Technical debt ranking

- **Critical**: InDesign single-Mac finalize; no durable Bitable source backup; frozen-copy review-branch model; raw binaries in git history without LFS.
- **High**: dead lockfile / no container / unpinned TeX; 5× duplicated Feishu transport (and the sync path's missing retry/rate-limit); non-atomic queue claim; print-based logging + silent queue failures; no CODEOWNERS / secret scanning / dependabot.
- **Medium**: flat `tools/` namespace; `build_docs.py` facade fan-in; dual dispatch paradigms; sync concurrency races; DingTalk browser-session tokens; oversized guide docs; code-edit language onboarding; serial queue without TeX cache.
- **Low**: `build.py` shim ceremony / 28-field `DispatchContext`; stale Python-3.9 and ONBOARDING lock-file notes; `review/id-rec*` branch naming; no semantic release labels.

## 6. Phase plan (executable form: Workstreams T / U / V)

- **Phase 0 — stop the bleeding** (days–weeks, no architecture change): lockfile into CI, TeX cache/pin, LFS for build binaries, scheduled Bitable exports + restore runbook, queue-failure alerting via the existing Issue-sentinel path, CODEOWNERS + secret scanning + dependabot, InDesign second-host + version lock. → Workstream T.
- **Phase 1 — platformize** (a quarter): one Feishu transport client with retry/rate-limit/locking, package `tools/` along the idml pattern, extract target/config resolution from `build_docs.py`, structured logging, atomic leased queue claims + parallel build matrix, data-driven language onboarding, release labeling + rollback runbook. → Workstream U.
- **Phase 2 — re-architect the one thing tooling can't fix**: replace frozen-copy review branches with per-target derivatives + a pinned-but-advanceable template reference, propagated as automated per-branch bump PRs; distribute the operator's review load via CODEOWNERS scopes so operator judgment is reserved for compliance/content decisions. Design doc required before implementation. → Workstream V.
