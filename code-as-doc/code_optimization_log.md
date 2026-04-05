# Code Optimization Log

Updated: 2026-04-05

This file records major maintainability milestones.
It is a history log, not the day-to-day usage guide.

For current rules, see:

- [`code-as-doc/README.md`](README.md)
- [`code-as-doc/build_doc_guide.md`](build_doc_guide.md)
- [`code-as-doc/code_style_guide.md`](code_style_guide.md)
- [`user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md)

## 1. 2026-03-08: Initial P0 / P1 Refactor Wave

Main outcomes:

- extracted shared target resolution helpers
- reduced duplicated target/token logic across build entry scripts
- split [`tools/phase1/renderers.py`](../tools/phase1/renderers.py) into smaller renderer modules
- split [`tools/word_bundle.py`](../tools/word_bundle.py) into `common / html / docx`
- introduced stronger config page parsing
- cleaned build noise and cache tracking from Git

Why it mattered:

- less duplicated logic
- clearer code ownership
- easier testing and future refactor work

## 2. 2026-03-11: Cross-Platform Builder and Output Layout

Main outcomes:

- introduced [`build.py`](../build.py) as the primary cross-platform entrypoint
- normalized actions such as `rst`, `word`, `html`, `pdf`, `all`
- grouped runtime outputs by target under:
  - [`docs/_build/<model>/<region>/rst`](../docs/_build)
  - [`docs/_build/<model>/<region>/html`](../docs/_build)
  - [`docs/_build/<model>/<region>/word`](../docs/_build)
  - [`docs/_build/<model>/<region>/pdf`](../docs/_build)
- moved away from relying on `make` as the main user entrypoint

Why it mattered:

- Windows, macOS, and CI can all use the same command surface
- target outputs stopped overwriting each other as easily

## 3. 2026-03-11 to 2026-03-12: Review-First Workflow

Main outcomes:

- introduced [`docs/_review/<model>/<region>/`](../docs/_review) as the review working layer
- added `build.py review`
- added `build.py check`
- added `build.py sync-review`
- changed default build behavior to overlay `_review` onto runtime bundles when present
- made reviewed content the real daily editing surface after review starts

Why it mattered:

- target-specific review edits no longer need to mutate shared templates
- Git history becomes meaningful at the target level
- publishing can happen from reviewed text instead of only from raw template output

## 4. Data and Contract Improvements

Main outcomes:

- page contracts added for placeholder-heavy pages
- current contract coverage includes:
  - `03_product_overview`
  - `05_operation_guide`
  - `12_app_setup`
- `check` now validates more than config syntax:
  - product identity
  - unresolved placeholders
  - missing includes
  - missing assets
  - contract-required placeholders

Why it mattered:

- missing parameter data is caught earlier
- template drift is easier to detect

## 5. Revision Tracking and Reports

Main outcomes:

- introduced `build.py diff-report`
- added file, page, and field level report exports
- added HTML report pages and report index pages
- added source tracing back to [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) rows where possible
- added first-baseline detection and `--ignore-initial-adds`

Why it mattered:

- document review history can be exported as tables
- reviewers can see not only which files changed, but which fields changed

## 6. Shared Config Family Rule

Main outcomes:

- stopped normalizing around one config per model
- consolidated to shared family configs:
  - [`config.us.yaml`](../config.us.yaml)
  - [`config.ja.yaml`](../config.ja.yaml)
- active family configs are now centered on US / JP shared configs instead of per-model files
- moved per-target differences to CLI target selection and phase1 data

Why it mattered:

- less config sprawl
- easier maintenance for multi-model families

## 7. Current Direction

The system is now optimized around:

- shared template families
- phase1 data as the structured source
- `_review` as the target editing surface
- [`build.py`](../build.py) as the primary command surface
- `diff-report` as the revision export layer

Future optimization logs should keep recording only meaningful maintainability milestones, not every small edit.

## 8. 2026-03-15: Stability, Contract V2, Release Traceability, and Preview Flow

Main outcomes:

- removed hardcoded `JE-1000F` defaults from `build.py diff-report`
- fixed runtime bundle asset classification when canonical paths pass through symlinked or temp-backed roots
- limited review overrides to `_assets`, `_static`, and `renderers` so review metadata files do not leak into publish bundles
- added stale identity scanning to `check`
- extended page contracts with `required_spec_keys`, `required_page_values`, `required_assets`, and `allowed_*` scope fields
- added `build.py release-manifest`
- added `build.py preview` and `build.py fast`
- added the GitHub Actions baseline workflow at [`.github/workflows/manual-validation.yml`](../.github/workflows/manual-validation.yml)

Why it mattered:

- target-aware diff reports no longer silently inspect the wrong subtree
- review metadata is now separated cleanly from runtime publish inputs
- missing CSV keys, missing assets, and stale model names are caught earlier in `check`
- release outputs now have a JSON / CSV traceability record with file hashes
- maintainers have a fast page-scoped preview path and a lightweight runtime draft path

## 9. 2026-03-31: Phase2 Snapshot Sync and Shared Data-Root Resolution

Main outcomes:

- added [`build.py sync-data`](../build.py) as the explicit local sync step for Feishu/Lark content snapshots
- introduced [`tools/data_snapshot.py`](../tools/data_snapshot.py) to centralize structured-data path resolution
- added `--data-root` support across build, check, diff-report, and release-manifest entrypoints
- added [`data/phase2/`](../data/phase2) as the preferred frozen snapshot root while keeping [`data/phase1/`](../data/phase1) as the legacy baseline
- kept [`data/phase1/page_registry.csv`](../data/phase1/page_registry.csv) and [`data/layout_params.csv`](../data/layout_params.csv) as repo-maintained inputs outside the Feishu sync flow

Why it mattered:

- online content governance is now separated cleanly from the offline build contract
- build-time consumers no longer need their own ad hoc CSV path rules
- maintainers can switch between phase1 and phase2 snapshots without changing manifests or renderer logic

## 10. 2026-04-04: Queue Action Normalization and Staged Verification Outputs

Main outcomes:

- made `Workflow_action` the primary queue-action field for `Document_link` while keeping `Doc_phase` as a compatibility fallback
- updated local/GitHub queue entrypoints to prefer `--workflow-action build-draft-package|publish`
- added `--staging-root` and `AUTO_MANUAL_STAGING_ROOT` so `docs/_build`, `reports/version_tracking`, and `reports/releases` can be redirected under an isolated root during verification
- extended `check`, `sync-review`, `review_bundle`, `release-manifest`, and publish-path helpers to read/write against staged output roots
- updated maintainer docs to keep `page_registry`, page selection/applicability, and `layout_params` explicitly repo-owned while queue data stays phase2-driven

Why it mattered:

- queue semantics are now less ambiguous for operators and Feishu automation authors
- local parity checks and smoke runs no longer need to pollute tracked output directories
- release-path consumers can rely on one normalized action vocabulary and one isolated-output mechanism

## 11. 2026-04-04: Branch Start Guardrails

Main outcomes:

- added [`scripts/start_branch.ps1`](../scripts/start_branch.ps1) as the supported branch-creation entrypoint from fresh `origin/main`
- added [`scripts/start_branch.sh`](../scripts/start_branch.sh) so the same branch-start flow is available on mac/Linux
- moved the repo-managed [`.githooks/pre-push`](../.githooks/pre-push) guard off the earlier bash-only path and shipped companion Windows launchers [`.githooks/pre-push.cmd`](../.githooks/pre-push.cmd) plus [`.githooks/pre-push.ps1`](../.githooks/pre-push.ps1)
- documented the local `git config core.hooksPath .githooks` setup, the Windows/mac entrypoints, and the intentional bypass path `git push --no-verify`

Why it mattered:

- continuing work in the same shell after a PR merge or close is less likely to accidentally reuse an outdated base
- the same freshness guard can now be applied from Windows and mac without depending on a bash-only hook path

## 12. 2026-04-04: Staging-First Local Validation

Main outcomes:

- added [`scripts/local_build.py`](../scripts/local_build.py) plus [`scripts/local_build.ps1`](../scripts/local_build.ps1) and [`scripts/local_build.sh`](../scripts/local_build.sh) as the local verification wrappers that default staging-safe build actions into `.tmp/staging`
- updated [`scripts/process_build_queue.ps1`](../scripts/process_build_queue.ps1) and [`scripts/listen_build_queue.ps1`](../scripts/listen_build_queue.ps1) so local queue runs also default to `.tmp/staging`
- updated the maintainer and user workflow docs so local `check`, `diff-report`, `release-manifest`, and `publish` examples stop requiring a hand-written `--staging-root`

Why it mattered:

- routine local verification no longer needs to pollute repo `docs/_build`, `reports/version_tracking`, or `reports/releases`
- Windows and mac operators now have the same default isolated-output workflow for local validation

## 13. 2026-04-05: Workflow_action Deprecation Cutover

Main outcomes:

- kept `Workflow_action` as the only recommended queue-action field in docs and CLI examples
- retained `Doc_phase` only as a compatibility fallback, with explicit warnings in build-queue logs and CLI translation paths
- updated queue writeback/result diagnostics so `workflow_action` stays primary and legacy `Doc_phase` only appears as `legacy_doc_phase` when that fallback path was used

Why it mattered:

- queue-action migration now has one clear primary field and one explicitly deprecated fallback
- legacy queue rows can still run without hiding which compatibility path was taken

## 14. 2026-04-05: Modular Decomposition of Build and Queue Orchestration

Main outcomes:

- extracted build path/staging/config helpers into [`tools/build_paths.py`](../tools/build_paths.py)
- extracted diff-report and publish-path command helpers into [`tools/build_reports.py`](../tools/build_reports.py)
- extracted CLI command assembly helpers into [`tools/build_entry_commands.py`](../tools/build_entry_commands.py)
- extracted doctor environment/preflight helpers into [`tools/build_doctor.py`](../tools/build_doctor.py)
- extracted shared queue dataclasses into [`tools/queue_contract.py`](../tools/queue_contract.py)
- extracted queue action normalization into [`tools/document_link_actions.py`](../tools/document_link_actions.py)
- extracted queue record parsing/binding/filtering into [`tools/document_link_queue.py`](../tools/document_link_queue.py)
- extracted queue config-family routing into [`tools/queue_config_resolution.py`](../tools/queue_config_resolution.py)
- extracted queue runtime/worktree helpers into [`tools/queue_runtime.py`](../tools/queue_runtime.py)
- extracted queue-triggered build execution into [`tools/queue_build_execution.py`](../tools/queue_build_execution.py)
- extracted per-group queue processing and writeback orchestration into [`tools/queue_group_processing.py`](../tools/queue_group_processing.py)
- extracted grouped dry-run preview formatting into [`tools/queue_dry_run.py`](../tools/queue_dry_run.py)
- extracted grouped queue bucketing rules into [`tools/queue_grouping.py`](../tools/queue_grouping.py)
- extracted queue-session bootstrap and pending-state loading into [`tools/queue_session.py`](../tools/queue_session.py)
- extracted Lark drive/wiki transport helpers into [`tools/queue_lark_ops.py`](../tools/queue_lark_ops.py)
- extracted queue output staging and publish metadata helpers into [`tools/queue_outputs.py`](../tools/queue_outputs.py)
- extracted queue writeback/result formatting into [`tools/queue_writeback.py`](../tools/queue_writeback.py)
- reduced [`tools/process_build_queue.py`](../tools/process_build_queue.py) from the earlier 1600+ line range down to a smaller orchestration-focused core

Why it mattered:

- future changes to queue transport, writeback, output staging, or action semantics no longer need to touch one giant file
- wrapper-compatible extraction kept the public entrypoints stable while shrinking the regression surface
- maintainers now have explicit module boundaries to extend instead of continuing to accrete logic into `build.py` and `process_build_queue.py`

## 15. 2026-04-05: Module Boundary Map For Ongoing Maintenance

Main outcomes:

- added [`code-as-doc/dev/orchestration_module_map.md`](dev/orchestration_module_map.md) as the living map for build and queue module ownership
- recorded the current rule that [`build.py`](../build.py) and [`tools/process_build_queue.py`](../tools/process_build_queue.py) should stay orchestration-first while helper modules absorb low-level logic
- linked ongoing decomposition maintenance to both the roadmap and the optimization log

Why it mattered:

- decomposition work is now discoverable after the commit lands, not only recoverable from Git history
- maintainers have a stable place to document future module moves as the next large files are split

## 16. 2026-04-05: Queue Entry Boundary Tightening

Main outcomes:

- extracted [`tools/queue_orchestration.py`](../tools/queue_orchestration.py) so [`tools/process_build_queue.py`](../tools/process_build_queue.py) now delegates its top-level session loop instead of carrying the full pending-state / dry-run / real-run branch logic
- extracted [`tools/queue_bound_outputs.py`](../tools/queue_bound_outputs.py) so repo-root-aware output and release adapters live outside the entry file
- preserved test-time `ROOT` patching by wiring the bound-output module through a dynamic repo-root provider instead of hardcoding repo state inside the helper
- refreshed [`code-as-doc/dev/orchestration_module_map.md`](dev/orchestration_module_map.md) to record the new queue ownership split

Why it mattered:

- queue entry behavior is now cleaner to reason about because session orchestration and repo-root output adaptation are explicit modules
- the remaining `process_build_queue.py` surface is closer to compatibility wrappers plus dependency wiring instead of mixed implementation

## 17. 2026-04-05: Queue Runtime And Transport Adapter Split

Main outcomes:

- extracted [`tools/queue_bound_runtime.py`](../tools/queue_bound_runtime.py) for repo-root-aware command/worktree helpers and bound `build.py` command assembly
- extracted [`tools/queue_bound_lark_ops.py`](../tools/queue_bound_lark_ops.py) for repo-root-aware Lark CLI adapters used by the queue entrypoint
- kept compatibility names such as `_run_command`, `_run_lark_cli_json`, `get_wiki_node`, and `_command_failure_message` on [`tools/process_build_queue.py`](../tools/process_build_queue.py) so existing tests and callers still patch the same surface
- reduced [`tools/process_build_queue.py`](../tools/process_build_queue.py) further into a smaller orchestration-and-compatibility layer

Why it mattered:

- queue-specific runtime and transport binding no longer need to live inline with queue record/action orchestration
- the remaining hot spots in `process_build_queue.py` are now narrower and easier to isolate in later passes
