# Code Optimization Log

Updated: 2026-07-21

This file records major maintainability milestones.
It is a history log, not the day-to-day usage guide.

For the active optimization checklist, use:

- [`next_optimization_checklist.md`](next_optimization_checklist.md)

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
- added source tracing back to `Spec_Master.csv` rows where possible; the original phase1 CSV baseline has since been retired
- added first-baseline detection and `--ignore-initial-adds`

Why it mattered:

- document review history can be exported as tables
- reviewers can see not only which files changed, but which fields changed

## 6. Shared Config Family Rule

Main outcomes:

- stopped normalizing around one config per model
- consolidated to shared family configs:
  - [`configs/config.us.yaml`](../configs/config.us.yaml)
  - [`configs/config.ja.yaml`](../configs/config.ja.yaml)
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
- kept page registry metadata and [`data/layout_params.csv`](../data/layout_params.csv) as repo-maintained inputs outside the Feishu sync flow; the active page registry now lives at [`data/phase2/page_registry.csv`](../data/phase2/page_registry.csv)

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

## 14. 2026-04-10: OpenClaw Phase 1 Control-Layer Bridge

Main outcomes:

- added a repo-owned OpenClaw plugin package under [`../integrations/openclaw/auto-manual-control-layer/`](../integrations/openclaw/auto-manual-control-layer)
- registered `/start-review`, `/build-draft`, `/publish`, and `/manual-status` as the supported Phase 1 command surface
- hardened the three `main`-owned GitHub workers with `openclaw_dispatch_nonce` plus the `openclaw-run-metadata` artifact for run correlation
- added a shared Python helper at [`../integrations/openclaw/scripts/write_workflow_run_metadata.py`](../integrations/openclaw/scripts/write_workflow_run_metadata.py)
- extended CI so the OpenClaw package runs through `npm ci && npm test` in `Manual Validation`

Why it mattered:

- operators now have one control-layer entrypoint without moving build execution or Feishu secrets out of GitHub Actions
- manual retries and status lookups can map back to one specific workflow run instead of guessing the latest dispatch
- the OpenClaw integration stays isolated from the Python execution plane while still living in the same repo history
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

## 18. 2026-04-05: Queue Binding And Record Adapter Split

Main outcomes:

- extracted [`tools/queue_bound_binding.py`](../tools/queue_bound_binding.py) for `Document_link` preflight and binding resolution helpers
- extracted [`tools/queue_bound_records.py`](../tools/queue_bound_records.py) for queue record parsing, workflow-action facade logic, config routing, and grouping helpers
- preserved `ROOT` and `load_config` patchability by wiring repo-root and config-loader providers from [`tools/process_build_queue.py`](../tools/process_build_queue.py)
- reduced [`tools/process_build_queue.py`](../tools/process_build_queue.py) further into a smaller compatibility-and-entrypoint layer

Why it mattered:

- queue record/config routing is now isolated from runtime, transport, output staging, and top-level orchestration
- future changes to record semantics or config-family routing can land in smaller modules without reopening the full queue entry file

## 19. 2026-04-05: Maintainability Milestone 1, Foundation And Entrypoint

Main outcomes:

- added shared config/bootstrap helpers in [`tools/config_loader.py`](../tools/config_loader.py) and [`tools/script_bootstrap.py`](../tools/script_bootstrap.py)
- switched build/report/sync entry scripts to the shared config-loading and repo-root bootstrap foundation
- extracted `build.py` runtime helpers into [`tools/build_runtime.py`](../tools/build_runtime.py)
- extracted `build.py` publish and diff-report orchestration into [`tools/build_publish.py`](../tools/build_publish.py)
- extracted `build.py` CLI parsing into [`tools/build_cli.py`](../tools/build_cli.py)
- extracted `build.py` top-level action routing into [`tools/build_dispatch.py`](../tools/build_dispatch.py)
- extended [`tools/build_doctor.py`](../tools/build_doctor.py) so the doctor runner no longer lives inline in [`build.py`](../build.py)

Why it mattered:

- the repo now has one shared config/bootstrap foundation instead of repeating path setup and config loading across entry scripts
- `build.py` is closer to an orchestration shell, with parser and action dispatch logic separated from runtime and publish implementation
- later decomposition work can keep compatibility wrappers stable while moving real logic into smaller modules

## 20. 2026-04-05: Maintainability Milestone 2, Build Pipeline Decomposition

Main outcomes:

- split [`tools/build_docs.py`](../tools/build_docs.py) into dedicated CLI, entry, target-resolution, bundle, validation, I/O, export, theme, path, sphinx, HTML, page/index, and shared-support modules
- reduced [`tools/build_docs.py`](../tools/build_docs.py) from the earlier 1400+ line range down to a thinner orchestration facade
- split [`tools/gen_index_bundle.py`](../tools/gen_index_bundle.py) into planning, materialization, asset, page-render, and runtime helper modules
- split [`tools/check_docs.py`](../tools/check_docs.py) into bundle/reference, contract, generated-page, identity, runtime, and CLI helper modules
- added config `extends` support and moved shared US single-language defaults into [`configs/config-bases/us-single-language-base.yaml`](../configs/config-bases/us-single-language-base.yaml) so `config.us-en/es/fr.yaml` became thin overrides with manifest-owned page stacks

Why it mattered:

- build-pipeline changes now land in smaller, more explicit modules instead of reopening one large mixed-responsibility file
- bundle generation, checking, and export flow now have clearer ownership boundaries and lower regression risk
- single-language config maintenance no longer depends on copying whole-family YAML files for small language-specific differences

## 21. 2026-04-05 to 2026-04-06: Maintainability Milestone 3, Reporting, Queue, and Domain Split

Main outcomes:

- split [`tools/diff_report.py`](../tools/diff_report.py) into dedicated git/path, field extraction, rendering, report-generation, and model helper modules while keeping the public facade stable
- moved release-manifest runtime assembly behind [`tools/release_manifest_service.py`](../tools/release_manifest_service.py) without changing CLI or path semantics
- completed the queue decomposition wave across listener, review-start, build-session wiring, phase2 support, and queue-bound adapter modules while preserving patchable entry surfaces
- split [`tools/utils/spec_master.py`](../tools/utils/spec_master.py) into dedicated shared, lookup, auditing, mapping, and repair modules while keeping the original public exports stable
- completed the execution tracker in [`maintainability_refactor_tracker.md`](maintainability_refactor_tracker.md)

Why it mattered:

- reporting, queue integration, and spec-master domain logic now have clear ownership boundaries instead of living in the same large facade files
- maintainers can change lookup, validation, mapping, repair, reporting, or queue-adapter behavior with a much smaller regression surface
- the maintainability campaign now has a closed loop across code, tracker state, and milestone history

## 22. 2026-04-06: Workstream A Closure, Entrypoint And Tooling Parity

Main outcomes:

- removed hardcoded `JE-1000F` diff-report defaults from [`tools/diff_report.py`](../tools/diff_report.py) so tracked-root and output-root behavior now aligns with [`build.py`](../build.py)
- added shared target/config defaults in [`tools/target_defaults.py`](../tools/target_defaults.py) and rewired [`scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py) plus `scripts/build_us_manuals.ps1` (removed 2026-07-02) to derive matrix targets from shared metadata instead of duplicating literals
- updated [`tools/process_docs/build_review_preview.py`](../tools/process_docs/build_review_preview.py) and [`tools/process_docs/vercel_build_review_preview.py`](../tools/process_docs/vercel_build_review_preview.py) so family-default preview config resolution matches the supported `US` / `JP` / `CN` workflow
- refreshed [`README.md`](../README.md), [`build_doc_guide.md`](build_doc_guide.md), and [`hello_auto-doc.md`](../user-guide/hello_auto-doc.md) so script examples and preview guidance match the current supported baseline

Why it mattered:

- `build.py`, low-level tools, and matrix wrappers no longer disagree on review roots, report roots, or default target config resolution
- maintainers can change shared family defaults in one place instead of editing multiple wrappers and preview scripts independently
- user-facing script examples now describe the same entrypoint behavior that the code actually implements

## 23. 2026-04-06: Maintainability Milestone 4, Preview, Domain, Export, and Sync Decomposition

Main outcomes:

- split [`tools/process_docs/build_review_preview.py`](../tools/process_docs/build_review_preview.py) into dedicated target, data, render, page, postprocess, and workspace helper modules while preserving the public facade
- reduced [`tools/utils/spec_master.py`](../tools/utils/spec_master.py) to a thin facade over dedicated shared, row-helper, lookup, auditing, mapping, and repairs modules
- split [`tools/word_bundle_html.py`](../tools/word_bundle_html.py) into models, HTML-only, render, images, and rewrite helper modules
- split [`tools/sync_data.py`](../tools/sync_data.py) into config, records, runtime, and CLI-output helpers while keeping `LarkCliSource`, `ROOT`, and existing patch surfaces stable
- finished the remaining shared-bootstrap rollout across entry scripts and reduced queue-side phase2 helper coupling through [`tools/phase2_support.py`](../tools/phase2_support.py)

Why it mattered:

- the remaining large maintenance hot spots were reduced to orchestration-oriented facades instead of mixed implementation files
- tests and queue/review callers kept the same patchable public surface while real implementation moved into smaller modules
- preview, export, sync, and domain-rule changes can now land with lower regression risk because ownership boundaries are explicit

## 24. 2026-04-07: Next Optimization Milestone A, Quality-Gate Hardening

Main outcomes:

- removed import-time config loading from [`tools/process_docs/build_review_preview_targets.py`](../tools/process_docs/build_review_preview_targets.py) while keeping the existing preview-template iterable surface stable
- split [`tools/validate_spec_master_runtime.py`](../tools/validate_spec_master_runtime.py) into focused rule collectors for row, header, footnote, note, and selector validation
- split [`tools/check_docs_generated.py`](../tools/check_docs_generated.py) into loader, recipe, binding, snippet, placeholder, contract, and orphan-snippet helpers
- added a minimal Ruff gate through [`pyproject.toml`](../pyproject.toml) and [`.github/workflows/manual-validation.yml`](../.github/workflows/manual-validation.yml)
- added shared orchestration-test helpers in [`../tests/test_helpers.py`](../tests/test_helpers.py) and migrated representative build/check/queue/target-resolution tests onto the shared scaffolding

Why it mattered:

- quality-gate hotspots are now easier to change without reopening giant mixed-responsibility functions
- CI can catch a small set of high-signal static issues before the heavier unit/build jobs run
- orchestration-heavy tests now have less duplicated temp-dir, fixture-writing, and patch boilerplate, so follow-up refactors have a lower maintenance tax

## 25. 2026-04-08: Next Optimization Milestone B, Diff/CI/Boundary Closure

Main outcomes:

- fixed high-value `diff-report` regression coverage around template back-mapping, placeholder label renames, section-order fallback, and report generation through committed fixture repos under [`tests/fixtures/diff_report/`](../tests/fixtures/diff_report)
- expanded [`.github/workflows/manual-validation.yml`](../.github/workflows/manual-validation.yml) with smoke paths for `build.py diff-report` and `build.py release-manifest`
- tightened [`.github/workflows/review-preview.yml`](../.github/workflows/review-preview.yml) into a stable smoke package path with `--skip-word` plus explicit packaged-artifact checks before upload
- centralized GitHub-hosted Feishu worker bootstrap in [`.github/actions/feishu-common-setup/action.yml`](../.github/actions/feishu-common-setup/action.yml) and [`scripts/validate_required_env.sh`](../scripts/validate_required_env.sh)
- extracted [`tools/build_main.py`](../tools/build_main.py), [`tools/build_docs_main.py`](../tools/build_docs_main.py), [`tools/process_build_queue_main.py`](../tools/process_build_queue_main.py), and [`tools/build_docs_artifacts.py`](../tools/build_docs_artifacts.py) so entry files stay facade-first while export planning/output steps live in dedicated helpers
- updated [`next_optimization_checklist.md`](next_optimization_checklist.md), [`optimization_project.md`](optimization_project.md), [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md), and [`architecture/Hello_Docs_Architecture.md`](architecture/Hello_Docs_Architecture.md) to match the closed milestone

Why it mattered:

- diff-report heuristic drift now has fixed regression inputs instead of relying only on ad hoc temp-repo tests
- CI now checks more of the workflow surfaces the repo actually depends on without turning every run into a full publish/build
- shared GitHub-hosted worker setup is easier to maintain because dependency/bootstrap changes now land in one place
- `build.py`, `tools/build_docs.py`, and `tools/process_build_queue.py` stayed wrapper-compatible while real export/bootstrap logic moved further out of the entry files

## 26. 2026-04-12: Feishu IM Webhook Adapter Ingress

Main outcomes:

- added a repo-external Feishu IM ingress package under [`../integrations/openclaw/feishu-im-webhook-adapter/`](../integrations/openclaw/feishu-im-webhook-adapter/)
- kept the adapter thin by reusing the repo-owned control surfaces `queue-query`, `queue-resolve-action`, and `queue-execute`
- added publish-confirmation state, event-id dedupe, same-thread Feishu replies, and later hardened the adapter with encrypted callback support
- aligned maintainer docs, user docs, and control-layer architecture notes with the new ingress layer

Why it mattered:

- operators can now enter review/build/publish asks from Feishu IM without moving build execution or Feishu writeback out of the existing queue/workflow plane
- the ingress layer stays isolated from the Python execution core while still sharing one deterministic action contract
- deployment and callback-mode limits are now explicit instead of being hidden behind local-only assumptions

## 27. 2026-04-12: ECS Feishu Adapter Deployment Contract

Main outcomes:

- added repo-owned ECS wrapper scripts at [`../scripts/run_feishu_im_webhook_adapter_service.sh`](../scripts/run_feishu_im_webhook_adapter_service.sh) and [`../scripts/run_feishu_im_cloudflared_service.sh`](../scripts/run_feishu_im_cloudflared_service.sh)
- added reusable `systemd` unit templates plus a named-tunnel config example under [`../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/`](../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/)
- documented the expected `env.sh` contract, service validation commands, restart flow, and the difference between unstable `trycloudflare.com` smoke URLs and stable named-ingress deployment
- aligned maintainer docs and user workflow docs so a future ECS rebuild can follow one repo-owned checklist instead of recovering ad hoc shell history

Why it mattered:

- the Feishu IM ingress no longer depends on manual `nohup` processes to survive reboots or crashes
- server rebuilds now have one explicit source of truth for runtime env, process bootstrap, and tunnel startup expectations
- deployment hardening moved from tribal knowledge into versioned repo assets, which lowers the risk of reconfiguration drift on the next machine

## 28. 2026-05-07: Contract and Queue Baseline Hardening

Main outcomes:

- absorbed the four short-term optimization PRs into the maintained baseline: phase2 snapshot manifest completeness, CLI action registry, config contract validation, and queue `RUNNING` writeback
- added [`dev/external_table_contracts.md`](dev/external_table_contracts.md) as the first explicit external table contract for phase2 snapshots, `Document_link`, and Review Init
- added [`dev/queue_state_model.md`](dev/queue_state_model.md) to document `pending -> running -> success/failed` queue semantics and writeback-failed handling
- split queue writeback field tests into [`../tests/test_process_build_queue_writeback.py`](../tests/test_process_build_queue_writeback.py) as the first domain-based reduction of the largest queue test hotspot
- refreshed [`../optimization_project.md`](optimization_project.md), [`next_optimization_checklist.md`](next_optimization_checklist.md), and [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md) so roadmap, checklist, and module ownership match the current baseline

Why it mattered:

- external table fields are now treated as explicit software contracts instead of scattered queue assumptions
- queue operators and OpenClaw/DingTalk follow-ups can reason about running, success, failure, and writeback-failed states consistently
- future queue transition and schema-drift work now has a documented baseline plus a smaller test surface to extend

## 29. 2026-05-08: Midterm Queue Contract and Drift Gates

Main outcomes:

- added [`../tools/queue_transitions.py`](../tools/queue_transitions.py) as the explicit transition payload layer for running, success, failure, and writeback-failed queue states
- added [`../tools/schema_drift.py`](../tools/schema_drift.py) so phase2 logical tables, required CSV headers, and `Document_link` writable fields can be checked from fixtures or local snapshot payloads without live Feishu access
- added offline external integration smoke fixtures in [`../tests/fixtures/external_integrations/`](../tests/fixtures/external_integrations/) covering missing fields, writeback permission failure, duplicate Start Review dispatch, Publish confirmation, and DingTalk fallback
- split queue routing/config/grouping tests into [`../tests/test_process_build_queue_routing.py`](../tests/test_process_build_queue_routing.py), further reducing the largest queue test hotspot without changing behavior
- added a `queue-contract` CI job in [`.github/workflows/manual-validation.yml`](../.github/workflows/manual-validation.yml) so queue transition and schema drift failures have a distinct failure surface

Why it mattered:

- the queue state machine is now testable before transport, upload, or Feishu/Lark writeback code runs
- external integration drift can fail in fixture tests instead of first appearing as a production worker surprise
- maintainers can now distinguish lint/unit/build-smoke/queue-contract failures more quickly in CI

## 30. 2026-05-08: Content Assembly Pilot Safety Net

Main outcomes:

- added [`dev/content_assembly_pilot_plan.md`](dev/content_assembly_pilot_plan.md) to freeze the `03_product_overview` dependency inventory and first functional block taxonomy before template splitting starts
- added fixture-backed content assembly tables under [`../tests/fixtures/content_assembly/`](../tests/fixtures/content_assembly/) for `page_assembly`, `content_blocks`, `block_fields`, `asset_registry`, and `block_rules`
- added [`../docs/templates/assembly_contracts/03_product_overview.yaml`](../docs/templates/assembly_contracts/03_product_overview.yaml) as the first declaration for the pilot page, family, region/language targets, fallback language, block types, and required fields
- added [`../tools/content_assembly_contract.py`](../tools/content_assembly_contract.py) so schema drift, unknown blocks, missing fields, missing assets, and missing fallback declarations can fail before any template is split
- added [`../tools/content_assembly.py`](../tools/content_assembly.py) as a no-op assembler that renders deterministic temporary RST from fixtures without replacing the existing HTML/PDF build path

Why it mattered:

- the first long-term content pilot now has a safety net around inputs, contracts, assets, fallback behavior, and regression samples
- `03_product_overview` can be split in the next phase behind an explicit page-level pilot switch instead of mixing data-contract work with template rewrites
- current PDF/HTML generation remains on the existing templates and renderer while the new assembly layer proves itself independently

## 31. 2026-05-08: Product Overview Assembly Pilot Switch

Main outcomes:

- added block templates under [`../docs/templates/assembly_blocks/03_product_overview/`](../docs/templates/assembly_blocks/03_product_overview/) for `product_identity`, `feature_overview`, `spec_summary`, and `asset_callout`
- wired `assembly_pilot` into the draft recipe path so only configured region/language targets use fixture-backed assembly
- enabled the pilot for `US/en` and `JP/ja` product overview recipes while keeping non-matching targets on the old template fallback path
- added Japanese product overview layout support to the renderer so the JP pilot path does not fall back to English headings
- expanded tests around pilot applicability, invalid pilot failure, required substitution checks, and assembled product overview output

Why it mattered:

- `03_product_overview` is now the first real page connected to declaration-driven assembly without a repo-wide template rewrite
- the default build behavior remains controlled by a page-level switch, and pilot failures stop the build clearly
- the next expansion can add more product overview blocks or another page using the same contract/fixture/template boundary

## 32. 2026-05-24: Spec Master Source Split and Read Model

Main outcomes:

- split Feishu spec authoring into `规格参数明细` for `Page=specifications` rows and `页面占位参数` for non-spec placeholder rows while keeping the original `spec_master` table ID as the read model for existing sync/build code
- added `spec_row_key` as the first read key, with `document_key` retained as the target dimension field
- added [`../tools/spec_master_rebuild.py`](../tools/spec_master_rebuild.py) and the `python build.py spec-master-rebuild` action to merge source tables, validate row counts, enforce unique keys, and optionally write merged rows back to the Feishu total table
- made source-table `source_row_key` a formula primary key and source-table `Row_key` a lookup from `参数名.Row_key`, leaving `Row_key_link` as the human-maintained dictionary selector
- removed source-table `Model` and `Region`; the rebuild step derives them from `document_key` while preserving the compatible read-model columns
- pinned the source table IDs in [`../configs/config.ja.yaml`](../configs/config.ja.yaml) and [`../configs/config.us.yaml`](../configs/config.us.yaml) under `sync.phase2.spec_master_sources`
- updated maintainer and user docs so humans edit the source tables and treat `spec_master` as a read model

Why it mattered:

- maintainers no longer have to edit target identity, page placeholders, visible spec rows, row keys, and ordering in one mixed table
- new-model onboarding can follow a copy-and-edit SOP across two source tables plus the existing dimension dictionaries
- downstream renderers and `sync-data` keep reading a compatible `Spec_Master.csv` shape while the human authoring surface becomes smaller and less error-prone

## 33. 2026-05-25: Phase2-Only Structured Data Cutover

Main outcomes:

- made [`data/phase2/`](../data/phase2) the only active structured-data root for configs, manifests, docs, review preview, release traceability, and low-level spec-maintenance scripts
- renamed the active CSV page renderer package from `tools.phase1` / `tools/phase1_build.py` to [`tools.csv_pages`](../tools/csv_pages) / [`tools/csv_page_build.py`](../tools/csv_page_build.py)
- rejected `csv_page.source` values other than `phase2`
- kept old configured `data/phase1` paths only as a legacy redirect guard inside `tools/data_snapshot.py`

Why it mattered:

- new build, review, publish, and queue paths cannot silently fall back to the retired snapshot
- current docs and tests now speak in phase2 terms, with phase1 limited to historical notes and explicit legacy-redirect coverage

## 34. 2026-05-28: Runtime Page Registry Snapshot Copy and Phase1 CSV Removal

Main outcomes:

- removed the stale tracked `data/phase1/*.csv` copies so structured CSV data has a single active phase2 home
- made `sync-data` copy [`data/phase2/page_registry.csv`](../data/phase2/page_registry.csv) into isolated `--data-root` snapshot roots such as `.tmp/review-start/phase2`
- recorded `page_registry` as a required derived file in `snapshot_manifest.json` alongside `row_key_mapping`

Why it mattered:

- review-start workers can now build from freshly synced temporary phase2 roots without missing `page_registry.csv`
- page order and CSV-page enablement remain repo-owned while runtime snapshots stay self-contained

## 35. 2026-05-30: Central Path Management Through path_utils

Main outcomes:

- made [`tools/utils/path_utils.py`](../tools/utils/path_utils.py) the single source of truth for repo-relative path segments via a `PathSegments` constant class, plus `*_of(base)` suffix helpers (`docs_build_dir_of`, `review_dir_of`, `static_dir_of`, `latex_renderer_of`, `contracts_dir_of`, `word_common_assets_of`, `version_tracking_of`, `releases_of`) and new `Paths` members (`review_dir`, `static_dir`, `contracts_dir`, `recipes_dir`, `params_tex`, `fonts_tex`, `version_tracking_dir`, `releases_dir`, `clean_targets`)
- added a config-aware docs anchor (`Paths.from_docs_dir` / `paths_for_docs_dir`) so a resolved `docs_dir` threads through every derived path without changing the default `root/"docs"` behavior
- rewired [`tools/build_paths.py`](../tools/build_paths.py) to delegate every join to `path_utils` while keeping its public signatures unchanged, so [`build.py`](../build.py) and its importers were untouched
- migrated ~25 scattered consumers (the `_build`, `_review`, `reports/version_tracking`, `reports/releases`, `docs`, `templates/{recipes,contracts,word_template}`, `renderers/latex`, `params.tex`, `fonts.tex`, `layout_params.csv` joins) off hand-built literals onto the central helpers, preserving each site's existing base (repo-root, config-parent-relative, worktree, or injected `docs_dir`)

Why it mattered:

- a path-segment rename now lands in one place instead of across two parallel modules plus ~40 ad-hoc joins
- the central module is config-aware, so a non-default `docs_dir` flows through consistently rather than being silently re-anchored
- follow-ups remain scoped and explicit: centralize the `generated` segment (~18 sites) and dedup the ~6 per-module `resolve_docs_dir` config-readers that disagree on repo-root vs config-parent base

## 36. 2026-05-30: Relocate Family Configs Into `configs/`

Main outcomes:

- moved the 14 root `config.*.yaml` family configs and the `config-bases/` overrides into [`configs/`](../configs) (with `config-bases/` now at [`configs/config-bases/`](../configs/config-bases)), so config-dir-relative `extends:` chains keep resolving with zero content edits
- added `PathSegments.CONFIGS` plus `Paths.configs_dir` / `Paths.config_file(name)` and repointed `Paths.config_yaml` at `configs/`, per the §3 rule that repo paths go through `path_utils`
- updated every reference (~55 files): `build.py` default, all CLI `--config` defaults, `target_defaults`, the review-preview config map, the config-discovery globs in [`tools/queue_config_resolution.py`](../tools/queue_config_resolution.py) (now `configs/config*.yaml`), the 6 CI workflows, docs, and `AGENTS.md` validation commands
- updated tests for the new layout: real-config refs prefixed with `configs/`, discovery-fixture writes redirected under `<tmpdir>/configs/`, while tmpdir temp configs and basename (`config_path.name`) comparisons were deliberately left unchanged

Why it mattered:

- the repo root no longer carries 14 loose config files; all build configuration lives under one `configs/` tree
- config discovery and defaults resolve from the new location, and the `extends:` inheritance graph survived the move untouched

## 37. 2026-05-30: Move Chat-Persona Docs Into `agent/`

Main outcomes:

- moved the four BlockClaw chat-persona docs (`BOOTSTRAP.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`) from the repo root into [`agent/`](../agent)
- kept [`CLAUDE.md`](../CLAUDE.md) and [`AGENTS.md`](../AGENTS.md) at the root because Claude Code and Codex auto-discover them there (and CLAUDE.md `@AGENTS.md`-imports), then repointed their links plus the AGENTS.md §8.4 protected-files list at `agent/`
- updated all inbound links (README, code-as-doc architecture/openclaw docs, integrations/openclaw README) and re-based `BOOTSTRAP.md`'s own outbound links by one level; left the openclaw-local `integrations/openclaw/IDENTITY.md` reference untouched (distinct file)

Why it mattered:

- the repo root is now limited to the two auto-discovered agent entrypoints; persona/identity docs live together under `agent/`
- no in-repo code loads the persona files by path, so the move is link-only — but the external OpenClaw runtime must read them from `agent/` (operator-confirmed)

## 38. 2026-05-30: Move `optimization_project.md` Into `code-as-doc/`

Main outcomes:

- moved the repo-optimization roadmap from the repo root into [`code-as-doc/optimization_project.md`](optimization_project.md), beside its sibling planning docs (`next_optimization_checklist.md`, `maintainability_refactor_tracker.md`)
- re-based ~14 inbound links across `AGENTS.md`, `README.md`, and `code-as-doc/**` (siblings drop a `../`; deeper `code-as-doc/{dev,architecture}` docs drop one `../`)
- normalized the moved file's own ~34 links from machine-specific `/Users/...` absolute paths to repo-relative ones: once the file entered the doc-link checker's `code-as-doc/` scope, those absolute paths (which only resolved on one machine) failed CI, so they were rewritten relative to `code-as-doc/`

Why it mattered:

- the remaining root files are now limited to tooling-pinned entrypoints/configs (`build.py`, `pyproject.toml`, `requirements.txt`, `vercel.json`, `.readthedocs.yaml`, `Makefile`, `CLAUDE.md`, `AGENTS.md`, dotfiles) plus the Codex `config.toml`
- planning/roadmap docs now live together under `code-as-doc/`

## 39. 2026-05-31: Consolidate Short Copy Into `localized_copy`

Main outcomes:

- introduced [`data/phase2/Localized_Copy.csv`](../data/phase2/Localized_Copy.csv) as the phase2 short-copy snapshot for page titles, table headers, and Product overview labels; LCD status words are marked in Translation Memory with `是否为 status word=Y` and exported to `Status_Words.csv` for renderer prefix bolding, while image alt text is derived from existing titles, `symbol_key`, or signal-row labels
- wired `localized_copy` into sync/schema/snapshot validation alongside `lcd_icons`, `variable_defaults`, and `variable_lang_overrides`
- added `{{ copy:<copy_key> }}` resolution so RST templates keep layout while short copy comes from data
- moved live LCD / Symbols renderer chrome and representative Product overview labels for US/en, JP/ja, and ZH out of Python/RST literals
- recorded the Operation guide / App setup block-migration assessment in [`code-as-doc/dev/content_block_migration_assessment.md`](dev/content_block_migration_assessment.md)

Why it mattered:

- short copy now has one operational source instead of being repeated across renderer constants and per-language templates
- missing copy fails during rendering/check instead of silently falling back to Python literals
- long-form procedural pages have an explicit migration boundary before any risky prose block move

## 40. 2026-06-01: Replace Online Localized Copy With Manual Copy Source

Main outcomes:

- introduced [`data/phase2/Manual_Copy_Source.csv`](../data/phase2/Manual_Copy_Source.csv) as the synced, single-language authoring snapshot for reusable page titles, table headers, Product overview labels, and spec page / section titles
- kept [`data/phase2/Localized_Copy.csv`](../data/phase2/Localized_Copy.csv) as a generated runtime file for existing `{{ copy:<copy_key> }}` rendering, and kept [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv) as a generated compatibility file for the existing spec renderer
- moved `localized_copy` and `spec_titles` out of required synced tables and recorded them, together with `Status_Words.csv`, under manifest `derived_files`
- added conflict detection for duplicate `manual_copy` TM rows, source-text fallback for missing target translations, and a missing-translation report at `reports/content_audit/manual_copy_missing_translations.csv`

Why it mattered:

- operators now maintain one source-language copy table plus Translation Memory tags instead of a disconnected multilingual copy table
- the online `03_内容源_Localized_Copy` and `03_内容源_多语言标题` tables are no longer active maintenance surfaces; generated copy remains reproducible from the synced source rows and TM snapshot
- signal-copy follow-up is tracked below because Symbols signal labels and meanings now use the same source table plus TM path.

## 41. 2026-06-02: Move Symbols Signal Copy Into Manual Copy Source

Main outcomes:

- moved reusable Symbols signal labels and meanings (`warning`, `caution`, `note`, `tips`, plus `danger` for rewrite detection) into [`data/phase2/Manual_Copy_Source.csv`](../data/phase2/Manual_Copy_Source.csv), with generated multilingual output in [`data/phase2/Localized_Copy.csv`](../data/phase2/Localized_Copy.csv)
- kept [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv) as the structure and targeting surface for `signal_row` order, scope, and optional icon assets; legacy `label_*` / `aliases_*` columns are compatibility mirrors only
- rewired the symbols renderer and Word HTML rewrite to resolve signal labels from generated copy while preserving existing renderer entrypoints and the existing `\HBSymbolSignalRow` / `hb-warning-lockup` component surfaces
- refreshed the code-copy audit guidance so future scans route signal words and signal meanings to `Manual_Copy_Source.csv` plus tagged Translation Memory, not back into Python or `symbols_blocks.csv`

Why it mattered:

- visible signal copy now follows the same source-language table plus Translation Memory flow as LCD / Symbols page chrome and Product overview labels
- the warning/caution/note/tip table can render localized dark lockups without hardcoded banner images or per-language labels in code

## 42. 2026-06-21: Backport Surface Becomes CLI-Only (Drop OpenClaw/IM Backport)

Main outcomes:

- removed the entire cloud-doc backport surface from the Feishu and DingTalk IM adapters — the action module, `repo-control` methods, `message-handler` branches, `reply-format` formatters, config env, and tests; the adapters keep only queue / status / manual-index actions (#453)
- deleted `code-as-doc/dev/im_backport_approval_runbook.md` and trimmed the IM-ingress (§3), IM-approval-entry (§5.1 R9), and P4 OpenClaw-trigger sections of [`architecture/Feishu_Cloud_Doc_Backport_Design.md`](architecture/Feishu_Cloud_Doc_Backport_Design.md); de-IM'd `README.md`, `user-guide/hello_auto-doc.md`, `user-guide/quick_start_guide.md`, `build_doc_guide.md`, the activation checklist, the edit-permission setup, and the QC requirements
- dropped the three dead `FEISHU_IM_CLOUD_DOC_BACKPORT_*` variables from the hello-docs binding scripts and reframed [`AGENTS.md`](../AGENTS.md) §3 as Claude Code / Codex / CLI only, not BlockClaw / IM
- realigned the Workstream Q and Milestone F wording: source-table-sync approval is now the operator deliberately running `apply-source-table --write` with explicit `--table-binding`s, not a Feishu IM `approve`/`reject` message

Why it mattered:

- in live use the chat LLM's target-resolution was too uncertain — a CN-doc backport ask resolved to the wrong (EU) review branch and reported 379 phantom cross-language diffs against a doc nobody had edited
- the deterministic [`tools/cloud_doc_backport.py`](../tools/cloud_doc_backport.py) CLI (unchanged) resolves the review branch from the build table, so backport stays a confident, reviewable operation; the decision keeps high-risk, strong-determinism writes on the CLI execution plane instead of the LLM chat control plane

## 43. 2026-06-25: Backport Hotspot Decomposition + Hotspot Governance

Main outcomes:

- governed the previously-ungoverned backport/data-sync hotspots in [`tools/check_maintainability_guardrails.py`](../tools/check_maintainability_guardrails.py): `tools/cloud_doc_backport.py` had reached 4183 lines — the largest file in the repo — outside any threshold; added it (capped exactly, only-descend) plus `sync_data_runtime.py` / `content_lint.py` / `translation_memory.py` / `source_record_index.py` / `source_table_sync.py` (#478)
- decomposed [`tools/cloud_doc_backport.py`](../tools/cloud_doc_backport.py) from **4183 → 202 lines (−95%)** into nine focused modules behind a re-export entry shim: `_model` (Block/parse/normalize/section), `_util` (schema consts + scaffolding), `_routing` (classify/route/diff), `_apply` (Class-R write-back), `_render` (markdown), `_transports` (Feishu transports), `_reports` (report builders), `_pr` (gh PR helpers), `_cli` (CLI + orchestration conductor) — #479–#487
- every step was behavior-preserving (move + re-export; the entry file re-exports all public symbols, so every `from tools.cloud_doc_backport import X` and `python3 tools/cloud_doc_backport.py …` is unchanged) and gated by the full suite (1183 tests) + ruff + guardrails, ratcheting the threshold down each step
- recorded the new module map in [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md) §6 (incl. the leaf→cli→shim import layering, the test layers, and the sync-env bootstrap pointer)

Why it mattered:

- the loop's core had escaped the maintainability guardrail entirely and grown through ~90 mostly-reactive PRs into a 4183-line grab-bag; this consolidated the debt before any further closed-loop optimization (prefer complexity-reducing work first)
- the AST-closure-check + re-export method (verify a cluster's deps are only stdlib/leaf-modules, move it, re-export, ratchet) kept each extraction safe and independently revertable; the conductor stays as a single `_cli` module so the live entry behavior is unchanged

## 44. 2026-06-29: Dev→Prod Bitable Tenant Sync + Drift Alert (Closed-Loop Gap E)

Main outcomes:

- [`tools/bitable_schema.py`](../tools/bitable_schema.py) gained cross-tenant write (`--profile` / `--identity`) so the prod side of a dev→prod structure sync runs from one machine via a separate prod-tenant device-flow profile (dev's default profile untouched), plus a select-field write-format fix (`_field_for_write`: options must be `[{"name": …}]` objects, not bare strings — bare strings were silently dropped) and a table-id re-list fallback — #498 and follow-up
- `parity` gained `--ignore-table-prefix` / `--ignore-table` (drop dev-only `99_*` scratch tables) and `--fail-on missing` (alert only when prod is *missing* a table/field; report drift without failing, since the dev tenant may carry extra/dirty select options)
- added [`.github/workflows/feishu-schema-parity.yml`](../.github/workflows/feishu-schema-parity.yml): a daily read-only parity that alerts (open/auto-close a `[schema-drift]` issue) when prod structure lags dev — the read-only half of Gap E in [`dev/closed_loop_gaps.md`](dev/closed_loop_gaps.md)
- runbook [`dev/bitable_schema_sync.md`](dev/bitable_schema_sync.md) updated with the cross-tenant profile flow, the seed/record mechanics (record-upsert raw map, `--yes` delete, select object format), and the CI alert

Why it mattered:

- code mirrors dev→prod automatically but Bitable **structure** does not; a mirrored code change that expects a new table/field would break a prod build silently. This makes structure promotion a recorded, repeatable act and adds an automated "prod is behind" alarm instead of waiting for a broken build.

## 45. 2026-06-29: Idempotent Reference-Data Seed Sync (Closed-Loop Gap C)

Main outcomes:

- [`tools/bitable_schema.py`](../tools/bitable_schema.py) gained `seed-export` (a reference table's simple-field rows → committed CSV) and `seed-import` (idempotent upsert of those rows into a target tenant, matched by a **business key**; dry-run unless `--write --yes`; `--prune` to delete rows absent from the seed; only simple writable fields touched; an empty cell never clears)
- the business key may be **composite** (comma-separated): the rule library needs `Row_key,规格书字段` because `Row_key` alone repeats (a parameter recurs across sections; `(剔除)` excludes one row per source field). `seed-import` flags a non-unique key as `DUPLICATE` rather than silently mismatching
- hardened `_lark` to also parse JSON from stderr (record-upsert emits its result there), replacing the earlier hand-rolled `record-upsert` loop that was not idempotent (it created duplicate rows — observed live: 26 → 53 → 79 before a manual wipe)
- proven idempotent against the prod rule library (`create 0, update 0, skip 26, extras 0`); docs: `dev/closed_loop_gaps.md` (Gap C done), `dev/bitable_schema_sync.md` (§4 rewritten around the new commands)

Why it mattered:

- only *structure* rode the dev→prod path; config tables whose **rows** drive code behavior (the extraction rule library, dictionaries) were seeded by hand and the import duplicated rows on re-run. This makes reference-data promotion a safe, re-runnable command — the last shared-config leg of dev→prod before a single `promote` (Gap A) can compose structure + reference data + env.

## 46. 2026-06-29: One-Step Dev→Prod `promote` (Closed-Loop Gap A)

Main outcomes:

- [`tools/bitable_schema.py`](../tools/bitable_schema.py) gained `promote`: one dev→prod step that runs `apply` (structure — converging a freshly-created table's fields over up to 2 passes), then `seed_import` for every table in the committed `bitable_schema/seeds.json` registry (reference data), prints the **env delta** (new table IDs for the prod `FEISHU_PHASE2_*`), and self-gates with a post-apply re-check (`structure up to date ✅` or a still-missing list). Dry-run unless `--write --yes`; `--profile`/`--identity`/`--prune` pass through
- added the committed seed registry [`bitable_schema/seeds.json`](../bitable_schema/seeds.json) (table → seed CSV → business key), so adding a reference table to the promotion is a one-line edit
- proven against the live prod tenant as a clean no-op once promoted (`+0 tables, +0 fields, skip 26`); docs: `dev/closed_loop_gaps.md` (Gap A done; recommended order updated), `dev/bitable_schema_sync.md` (new §3 one-step promote, granular steps renumbered 3a/3b)

Why it mattered:

- a structure+table+seed+env change previously landed in 4–5 separate manual steps; `promote` bundles {structure + reference data + env delta} into one self-gated command (code already rides `sync-hello-docs`). Together with B (parity) and E (daily drift alarm), the dev→prod **structure/reference** loop is now closed end-to-end: one operator command to promote, one daily CI alarm if prod falls behind.

## 47. 2026-07-02: Business Closed-Loop Engineering (Milestone G / Workstream R, G0–G7)

Main outcomes:

- **Revision reflow closed (G1, #514 + G0 tail, #517):** every `revision_ledger ingest` now auto-reconciles earlier rounds' pending rows (`--no-reconcile` opts out) and `reconcile --auto` stamps merge metadata from git; verdicts gained a similarity layer (best-window partial ratio ≥ 0.90, min needle 12 chars) so punctuation-level edits stop misclassifying; `stats` reports `reflow_rate`. The backport orchestration feeds the ledger best-effort per round (`AUTO_MANUAL_REVISION_LEDGER_PATH`; `off` disables) — the ledger is a local artifact, so the per-round piggyback, not CI, is the trigger.
- **Reviewer corrections reach the TM (G2, #518):** `tm-candidates` projects accepted review-route rows into the suggestion shape the existing gated TM write path consumes; `tm-apply` drives `translation_memory_sync.apply_translation_suggestions` (approval hashes, exact-or-abstain, GET-verified) — no new write path was built.
- **TM utilization is measurable (G3, #515):** the preprocess `Matcher` counts sentence-level units attempted vs matched; each run appends to `reports/tm_hit_rate/ledger.jsonl` via the stdlib-only [`tools/tm_hit_rate.py`](../tools/tm_hit_rate.py) (`stats` = overall + per-language-pair rates).
- **One canonical TM base (G4, #521, operator decision):** the env-token base (`$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN`, tables by name) is the single write base; the A/wiki mirror is a read-only archive — the query script no longer falls back to it silently, the preprocess script resolves env-first, and the `bilingual-tm-maintenance` write skill targets the canonical base.
- **PDF gains an annotation surface (G5, #520):** [`tools/pdf_annotate.py`](../tools/pdf_annotate.py) (PyMuPDF) renders `content_lint` findings as highlight+note annotations on a sidecar `*_annotated.pdf` — annotate on the PDF, correct at the source; unlocatable findings degrade to a page-1 summary note, never a misplaced highlight. New skill `pdf-annotate-qc`.
- **Nobody has to remember the backport (G6, #519):** [`tools/backport_reminder.py`](../tools/backport_reminder.py) + a daily `backport-reminder.yml` sentinel compare every InReview doc's live text against its committed render baseline (content, not timestamps) and keep a `[backport-reminder]` issue open exactly while un-backported edits exist.
- **The intake gate cannot be skipped silently (G7, #516):** `spec-extract` without `--reference` errors out unless `--skip-completeness` is explicit; the "ambiguous keys only warn" claim was verified stale (multi-match already escalates to `needs_review`).
- **Prerequisite refactor (G0, #517):** the 1380-line `cloud_doc_backport_cli.py` split into `args` / `commands` / `orchestration` / a 222-line dispatcher, all under per-module guardrails (22 hotspot files governed); 39 test patches retargeted to the orchestration seams (patching a re-export never intercepted the real call).

Why it mattered:

- the 2026-07-02 closed-loop analysis found the main line broke at reflow: reviewer corrections were recorded but never reconciled (reflow rate ≈ 0%) and never reached the TM corpus, TM utilization had no denominator, and PDF was the only reviewer surface with zero annotation capability. G0–G7 close the loop end-to-end and make its health measurable (reflow rate, hit rate); the remaining operator legs are the first live hit-rate baseline run, a `workflow_dispatch` of the reminder sentinel, and migrating any rows unique to the archived A base.

## 48. 2026-07-03: Three-Flow Dashboards (Milestone H, H3)

What changed:

- **One command, two faces (H3):** [`tools/flow_dashboard.py`](../tools/flow_dashboard.py) `report` aggregates the existing run artifacts (revision ledger — multiple checkouts merged and de-duplicated by `delta_hash` — TM hit-rate ledger, `pdf_annotate` run ledger, `tm_candidates` files, content-audit/QC reports, family configs, release manifests) into `reports/flow_dashboard/dashboard.{md,json}`. Ops face: reflow rate, TM hit rate, second-revision rate, template recurrence rate, template-sentence corpus coverage. Value face: audited-PDF count, model/region/language coverage, machine-findings count, reflow counts, TM candidate counts, and the time-saved narrative (`--baseline-hours-per-manual`, the operator's pre-system effort estimate).
- **Record-from-zero rule enforced in code:** a metric whose data source does not exist yet renders as `no_data` with the reason (the two template-flow metrics stay `no_data` until H1/H2 land); nothing is fabricated. Every ledger-backed metric buckets by month so trend review works as soon as history exists.
- **`pdf_annotate` gained a run ledger (`reports/pdf_annotate/ledger.jsonl`)** mirroring `tm_hit_rate.py` (idempotent by run key, best-effort append, `--no-ledger` opt-out, `--backfill-summary` for historical runs), so the audited-PDF count has a data source.

Why it mattered:

- Milestone G made the loop *work*; H3 makes it *visible* — the very first real run surfaced an actionable gap (reflow rate 0%: the JE-2000F CN round's 39 deltas all landed in source tables but were never stamped `accepted` in the ledger), which is exactly the class of silent drift the dashboard exists to catch. The value face gives stakeholder-facing numbers a single provenance-backed source instead of ad-hoc counting.

## 49. 2026-07-13: Unknown-Unknown Probes + Handover Assurance (Milestone I)

What changed:

- **Hand-over became a tested property (I0, #655):** repo-root [`ONBOARDING.md`](../ONBOARDING.md) is the single first-hour entrypoint (two-plane map, what-runs-where bus-factor register, golden-path drill); the quarterly cold-start drill protocol makes "someone else can maintain this" verifiable instead of assumed.
- **Language-tree parity gate (I1, #657):** [`tools/check_docs_lang_parity.py`](../tools/check_docs_lang_parity.py) in `check` — foreign-script shells, foreign lang-tag blocks, per-language page-set completeness — with `data/lang_parity_known_exceptions.csv` keeping registered debt green. First run caught the us-en trilingual-preface leftover (decision pending).
- **Warning ratchet (I2, #658):** every Sphinx run captures `-w` and diffs the sanitized stream against `data/known_warnings/` baselines (esp-docs pattern); staged enforcement (report → env-strict → default-strict after stable rounds). The one seeded warning is itself a real defect now visible as debt.
- **Toolchain provenance (I3, #656, raised to a render-projection prerequisite after #648):** `requirements.lock` + [`tools/toolchain_provenance.py`](../tools/toolchain_provenance.py) feeding both `doctor` and the release manifest — every published PDF names its environment.
- **Printed-URL inventory (I4):** [`tools/printed_url_inventory.py`](../tools/printed_url_inventory.py) scan/check/liveness over templates/renderers/configs/phase2; tracked inventory + manual QR register; monthly ops rhythm.
- **Base rebuild drill (I5, first run):** ops guide §4.7 — scratch base + mirrored schema + seed rows restored from repo artifacts in 86s; headline finding: the schema mirror covers only 2/20 business tables (follow-up: extend `bitable_schema export`).
- **Repo-health metrics (I6):** the flow dashboard's ops face now reports worktrees / dirty files / tracked `_build` files / tools module count and largest module — complexity growth is a monthly number.

Why it mattered:

- The workspace census × esp-docs comparison showed auto-manual's defenses concentrated on content correctness while the blind spots concentrated on publication sustainability and maintainer hand-over. Milestone I converts those unknown-unknowns into sensors — and the sensors validated themselves immediately: I3 caught a rebuilt venv on day one, I1 caught live trilingual-preface debt, I5's first drill exposed the 2/20 schema-mirror gap.

## 50. 2026-07-15: Asset Registry Enters Bundle Assembly (Milestone J, P1 Core)

What changed:

- RST image/figure/substitution and raw-HTML `src` references can use `asset:<asset_key>`; contract checking and materialization share one resolver, and model/region/language plus approved-status checks fail closed.
- bundle preparation now finalizes assets after review overlays and attachment aliases, then freezes `asset_usage_manifest.json`, the exact `asset_registry_snapshot.csv`, final RST/config/support-tree records, and `bundle_sha256` in `bundle_manifest.json`.
- review seeding restores semantic URIs from rewrite provenance; explicit review overrides retain the `asset_key` and are recorded separately, while path-based images remain compatible but visible as `legacy-path` debt.
- asset staging accepts only PNG/JPG/JPEG/SVG/PDF, never falls back to `.ai`, freezes source bytes before copying, and rejects traversal, symlink escape, collisions, staged tampering, and conflicting nested-include language contexts.
- the registry gained explicit region scope and a quarantined status; the known full-page back cover is quarantined until its printed QR/legal risk is independently cleared.
- created the isolated live `04_资产源文件` / `04_资产定义` / `04_资产导出物` tables and froze their real table/view/field bindings in `data/asset_base_bindings.json`; neither the legacy illustration table nor the staging intake table was used.
- archived the JE-1000F US `.ai`, deterministic ZIP, and manifest under source record `recvpvE4YHA8rW`, then downloaded all three and verified exact SHA-256 parity; the live archive contains 10 definitions (9 approved / 1 quarantine) and 142 export rows (59 archive pages / 59 previews / 24 semantic exports).

Why it mattered:

- image choice is now part of the deterministic document-assembly contract instead of an untracked renderer side effect, and the HTML/Word/PDF/Markdown bundle exporters see the same post-review staged bytes.
- the migration is observable without being overstated: current legacy paths are accounted for but are not registry-gated until templates move to `asset:`; IDML bundle-root enforcement and release-manifest asset lineage remain separate follow-up phases.
- the first source now proves the full local-package → live-archive → attachment-download verification loop without duplicating the 142 physical exports as Base attachments; future work can build registry sync on a reviewed, real binding instead of placeholder IDs.

## 51. 2026-07-17: Enterprise Ops Hardening — Milestone K Tier 1 (K4/K5/K7/K1)

What changed:

- **The planning wave first (#674):** a four-dimension production-readiness review (archived at [`reviews/production_readiness_review_2026-07-17.md`](reviews/production_readiness_review_2026-07-17.md)) found the code plane enterprise-grade but the operating plane not; it was converted the same day into Workstreams T/U/V, the capacity-driven Platform Owner roadmap ([`architecture/platform_evolution_roadmap.md`](architecture/platform_evolution_roadmap.md) — phases advance through operator-load reduction, observable exit criteria, and organizational triggers, not calendar), and Milestone K triaged into three execution tiers so the task list reads "4 in flight", not "15 pending".
- **K4 — source-table content backup + restore (#676):** [`tools/bitable_content_backup.py`](../tools/bitable_content_backup.py) (export / restore / verify over the schema-manifest table list, reusing `bitable_schema` primitives; restore is dry-run by default, explicit-token-only, refuses non-empty tables, never writes computed fields) + nightly `phase2-content-backup.yml` (90-day dated artifacts, sentinel Issue on failure) + ops guide §4.7b runbook. Live drill same day: TM base export 10s, business base 21 tables/1,313 rows 58s, scratch restore 888/888 verified. The drill immediately caught real drift — select options added after the schema snapshot made batch-create reject a whole table (800030005); restore now pre-syncs options via field-update. Known limitation recorded: multi-select cells restore as one concatenated option.
- **K5 — queue-failure sentinel (#677):** reusable [`queue-sentinel-issue`](../.github/actions/queue-sentinel-issue/action.yml) composite action wired as the final `if: always()` step of all three queue workflows. Issue titles carry the record_id, so the open/close lifecycle is per-record; cancelled runs open nothing; the failure body names the writeback silent-divergence case (exit-code propagation verified: writeback failures fail the job). Wiring pinned by `tests/test_queue_failure_sentinel.py`; ops guide §3b.
- **K7 — InDesign version lock + second host (#678):** committed pin [`tools/idml/indesign_version_pin.json`](../tools/idml/indesign_version_pin.json) (seeded live: Adobe InDesign 2026 21.0.1.6); `tools/indesign_finalize.py` checks it at finalize time — mismatch refuses to run (`--allow-version-mismatch` overrides, recorded in the report's `toolchain` block), plus `--check-host` / `--write-pin`; exact-match policy: upgrades re-pin all hosts together instead of loosening. From-zero second-host procedure at [`dev/indesign_second_host_runbook.md`](dev/indesign_second_host_runbook.md); ONBOARDING §3 register row moved from 无版本锁（已知风险） to a documented recovery path. **Residual: the one-time second-host verification run is the operator's; checklist K7 stays `in_progress` until it's recorded.**
- **K1 — the lock becomes the install source (#679):** all 10 `pip install -r requirements.txt` sites (manual-validation ×7, review-preview, feishu-common-setup — covering every Feishu workflow — and `.readthedocs.yaml`) now install from `requirements.lock`; the pip cache key follows the lock; the lock header carries the refresh when/how; stale "Python >= 3.9" and ONBOARDING "无 lock 文件" notes corrected.

Why it mattered:

- Three of the review's four Critical items closed in one day: a destructive Bitable edit is now restorable from a dated export via a drilled runbook, a failed queue run alerts on its own instead of requiring a watcher, and the one delivery leg outside CI gained a version gate plus a recovery procedure. The fourth Critical (frozen-copy review-branch propagation) is deliberately parked behind the K15 design gate.
- The discovery-engine rule proved itself twice within hours: the K4 drill exposed select-option drift the schema mirror could not see, and the K7 test suite caught a sentinel-vs-None API ambiguity before it shipped.
- Tier 1 was scoped as "what one operator + agents can deliver between business deliveries with no organizational trigger" — and it closed as scoped. Everything remaining in Milestone K now waits on a named business-pain trigger (Tier 2) or dedicated capacity (Tier 3), which is the capacity-driven model working as designed.

## 52. 2026-07-20: Milestone K Operational Verification

What was verified:

- **K4 first-nightly artifact:** run [`29672759849`](https://github.com/Bingboom/auto-manual/actions/runs/29672759849) was green, but its artifact was incomplete. The business manifest contained 18 tables / 850 rows and missed three required tables; the TM manifest contained zero tables and missed both `Translation_Memory` and `Terms`. Included CSV row counts and SHA-256 values were internally consistent, so the failure is completeness, not archive corruption. The workflow's `export | tee` pipeline masks the exporter's non-zero exit code without `pipefail`; K4 was reopened pending an operator-approved workflow fix and one complete 21 + 2 table artifact. The restore-drill scratch Base was moved to the Feishu recycle bin and an exact-name search returned no active result.
- **K7 second-host preflight:** `ArriettyMac-mini.local` reported an exact version-pin match for Adobe InDesign 2026 21.0.1.6. The downloaded-main checkout contained no known-good IDML, so no finalize report was produced; the runbook now distinguishes this preflight from the still-pending end-to-end second-host verification.

Why it mattered:

- the first operational follow-up caught two ways a checklist can overstate readiness: a green CI status with an incomplete recovery point, and a version match without a rendered deliverable. The checklist now remains open until the observable exit criteria are actually present.

## 53. 2026-07-21: Publish Repaired Repo-Wide + Milestone K Tier 1 Closed

What changed (the JE-1000F_US 1.6 publish campaign — 11 runs, 5 real gates, 10 green-gated PRs):

- **Publish had been silently broken for every target since #675 (07-17)** — `check` never exercised the LaTeX asset-copy or IDML paths, so CI stayed green while the publish leg was dead. The first real publish surfaced five independent gates, fixed in sequence:
  1. env: the capability-gate table id (`FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID` → `02_主数据_Document_key`) was newer than the local env files;
  2. asset three-source basename conflicts → the **target-override precedence trilogy** ([#690](https://github.com/Bingboom/auto-manual/pull/690)/[#691](https://github.com/Bingboom/auto-manual/pull/691)/[#694](https://github.com/Bingboom/auto-manual/pull/694)): registry-declared overrides (`renderers/latex/assets`) win the flat latex namespace **by bytes, in either arrival order**; unknown-provenance and generic-vs-generic conflicts still hard-fail. One wrong turn owned and reverted ([#688](https://github.com/Bingboom/auto-manual/pull/688)→[#689](https://github.com/Bingboom/auto-manual/pull/689)): writing a US-specific override into the global shared slot — the registry hash gates caught it exactly as designed, and merges have been exit-code-green-gated since;
  3. the approved reference contract was un-satisfiable after a partial refresh (3/55 identity fields) → temporarily unregistered ([#693](https://github.com/Bingboom/auto-manual/pull/693)), complete re-baseline owed by the replica line;
  4. review-branch overview pages still carried the 1.5-era grid → 1.6 params zipped into the old grid produced malformed tables → propagated main's balanced grid ([#695](https://github.com/Bingboom/auto-manual/pull/695); branch CI cannot resolve `asset:` URIs, so legacy image paths were kept);
  5. page parity 63-vs-61 proved compositional (LaTeX packs preface+safety and gives the TOC no page; the writer anchors them discretely) → the equality gate now binds **only approved reference plans**, fallback prints an explicit NOTE ([#696](https://github.com/Bingboom/auto-manual/pull/696)).
- **Acceptance semantics corrected: known-good = known-BASELINE.** Overset ⊞ is a designed designer-workflow item (the delivery's own checklist documents drag-to-reveal); no overset=0 package has ever existed. The second-host runbook now accepts on report parity against the shipped baseline — which retroactively re-explains the 1.5 "failure" (the real defect was a fonts-less package; its 2 oversets were by design).
- **K7 closed / Tier 1 fully closed:** `ArriettyMac-mini` finalized the 1.6 handoff zip end-to-end; the report matched the main-Mac baseline item-for-item (63 pages, 546 stories, 11 identical overset ids, fonts/links clean, PDF/X-4 + Japan Color 2001 Coated pass, pin=match; JSON diff zero after path fields) ⇒ hosts equivalent ([#697](https://github.com/Bingboom/auto-manual/pull/697)). The one delivery leg outside CI now has a version pin, a drilled second host, and a baseline-parity acceptance contract.

Why it mattered:

- The campaign was the discovery engine at full throttle: one business deliverable (a verification package) surfaced and fixed a repo-wide publish outage, hardened the asset-override design to its declared semantics, exposed the incomplete contract re-baseline, and corrected a wrong acceptance criterion — none of which any planning exercise had found.
- Standing follow-up (owned by the replica line): the complete approved-contract re-baseline for 1.6-class content (then re-register #693, strict parity returns via #696, and the 11 fallback oversets resolve under approved frame geometry).


## 54. 2026-07-27: Asset Registry Joins sync-data — Milestone J P1 Closed

What changed:

- `tools/sync_asset_registry.py` mirrors the live `04_资产定义` table into `data/asset_registry.csv` on every `sync-data`, following the capability-mirror shape (pure transform, injected collaborators, tracked CSV, `derived_files` manifest entry) so the git diff of the registry is the review surface for asset-status changes.
- The mirror is an **overlay, not a replace**, because two authorities meet in that one file: the Base owns what an asset is and whether it may build (类别 / 语言维度 / 状态 / 待无字化 / 适用机型 / 适用区域 / 语言变体), while the repository keeps `导出物路径` and `内容哈希` — they describe committed bytes — and `备注`, whose Base counterpart is intake/gate rationale rather than maintenance history.
- Rows are never deleted: an asset vanishing from the Base leaves its registry row standing instead of silently dropping an asset templates still resolve through.
- The merged CSV is parsed back through the resolver's own loader before it is written, so a bad Base value fails the sync rather than landing a registry the build would later reject.
- Table coordinates default to the Phase B artifact `data/asset_base_bindings.json`, with `FEISHU_PHASE2_ASSET_DEFINITIONS_TABLE_ID` as an override — no new GitHub secret, so the loop closes without waiting on ops provisioning.

Why it mattered:

- Milestone J's P1 is now closed on evidence rather than assertion. The other two acceptance conditions were re-verified live instead of assumed: all 183 template image/figure directives resolve through `asset:`, and resolution rejects an unregistered key, the `⛔隔离` back cover, and the `🔧临时替代` warning lockup, while `--publish` additionally refuses the `--allow-temporary` escape hatch.
- The overlay design came from checking before building: the Base holds 10 definitions while the registry holds 82 rows, so the obvious full-replace mirror would have deleted 72 repo-native census rows, and syncing `备注` would have overwritten the human maintenance history with intake rationale. A live dry run confirms the merge is a byte-identical no-op today (82 in / 82 out, 10 managed), and that a simulated Base edit propagates while the repo-owned columns survive.

## 55. 2026-07-27: Publish Asset Lineage and Gate (Milestone J P3, partial)

What changed:

- `tools/release_asset_lineage.py` lifts the prepared bundle's frozen asset record into the release manifest as an `assets` section (the I3 provenance shape): bundle fingerprint, registry-snapshot hash, and every registry-backed asset the build actually consumed with its format, content SHA, status and resolution source. The release CSV gained four flattened scalar columns.
- `publish` gained a gate between the last prepare and the release manifest. It refuses a bundle that consumed a `🔧临时替代`, `❌缺失` or `⛔隔离` asset, or that carries no frozen lineage at all — a print run cannot be corrected afterwards, so the failure has to happen before any artifact is released. Position matters and is asserted in the build-script test: the word stage cleans and re-prepares, so an earlier read would inspect a stale bundle.
- QR assets now cross-check the printed-URL inventory inside `asset-check`, which is already a CI job. An approved `二维码` asset must declare what it encodes in `data/printed_url_manual_entries.csv` (which gained an `asset_key` column), a quarantined or temporary candidate may not be registered as a live printed target, and a printed target may not point at an unregistered asset.
- `build.py`'s guardrail pin moved 750 → 761 with the reason recorded at the pin: a new injected entrypoint needs an import, a seven-line resolver and a call site, and the bundle-path resolution was pushed down into `tools/` first to keep that the irreducible minimum.

Why it mattered:

- A shipped PDF can now be traced to the bytes of every illustration inside it and to the registry state those bytes were approved under, instead of that provenance living only in a bundle sidecar that no release record points at.
- Two decisions came from checking the real bundle rather than the plan. The gate does **not** block `legacy-path` images: the JE-1000F US bundle still consumes 50 of them from data-generated pages, so the plan's literal wording would have blocked every publish; the count is recorded in the manifest so the debt is visible and can be ratcheted down. And the back-cover QR was decoded independently instead of trusted from its 备注 — the approved AI candidate encodes `160102000404`, the master's own document number rather than a URL, while the quarantined frozen reference encodes the older `160102000161`. That is why the cross-check asserts a declared payload rather than URL liveness.

## 56. 2026-07-27: InDesign Package in the Release Record (Milestone J P3)

What changed:

- `tools/release_indesign_package.py` records the print deliverable into the release manifest as an `indesign_package` section: the production IDML, the INDD, the InDesign PDF, the delivery handoff zip (which already carries `Links/` and the font manifest from `tools/idml/delivery.py`), and both the finalize and parity reports — each with sha256 — plus the preflight numbers (pages, overset, missing fonts, bad links, PDF/X verdict, InDesign build) and the parity verdict. Six flattened columns join the release CSV.
- Finalize and parity artifacts gained a canonical home beside the production IDML in `docs/_build/<model>/<region>[/<lang>]/idml/`. They previously had none: `indesign_finalize.py` writes wherever the operator points it, and the only documented example wrote to `/tmp`.
- `publish_meta.json` gained `handoff_package_path`. The queue publish worker already copied the handoff zip into the release version directory, but no release record named it — the print deliverable was being staged and then forgotten.

Why it mattered:

- A release record that names only the PDF cannot answer "what do we send the printer". Now it names the InDesign document, the IDML it came from, the packaged links and fonts, and whether that document passed preflight — all hash-verifiable.
- Optionality is the design, not a shortcut: InDesign finalize and the parity check run on an operator's Mac and never in CI, so a collector that demanded them would fail every unattended publish. The record states what was found and what was not, and `complete` is true only when the full set is present — the same shape `collect_asset_lineage` established.
- Verified against a real build directory rather than fixtures alone: the collector picks up a 741 KB production IDML and a 3.2 MB `1.7_handoff.zip`, hashes both, and correctly reports `complete=false` for the absent INDD and preflight.
- The work surfaced a blocker that is now registered rather than papered over: production IDML cannot be built from a clean checkout, because the committed `data/layout_params.csv` and the approved reference-layout contract disagree (`b174d541…` vs the pinned `046f6f5a…`) even though both were last changed in the same commit, and because `snapshot_sha256` binds the contract to an untracked phase2 snapshot. No CI job builds production IDML, so neither half was caught. The repair tool exists (`reference_layout_rebind.py`), but re-pinning a contract that carries an `approval` block is an operator decision.

## 57. 2026-07-27: The Reference-Layout Pin That Nothing Watched

What changed:

- Refreshed `source_identity.layout_params_sha256` in the approved JE-1000F/US reference-layout contract. #720 had refreshed it and then taken one more correction to `data/layout_params.csv` (`lang_en_idml_ups_caution_space_after` 9.9pt → 15.9pt) without recomputing it, so the pin described the pre-correction file and the same-source gate refused every production IDML build.
- Added `tools/check_reference_layout_pins.py` and its own CI job. It recomputes the two pins that derive from tracked files — `layout_params_sha256` and `style_contract_sha256` — and fails on drift. It never rebinds: re-pinning an approved contract is an operator decision, so the failure message points at `reference_layout_rebind.py` and asks for a parity re-run. `manual_content_sha256` and `snapshot_sha256` are deliberately out of scope because they derive from an untracked phase2 snapshot.
- Normalized `data/layout_params.csv` line endings. The committed blob had 850 CRLF + 47 LF against a `*.csv text eol=crlf` attribute, so every fresh checkout reported it modified before anyone touched it. It was the only tracked CSV with the problem (1 of 49).

Why it mattered:

- The cause was established by reproduction, not inference: reverting only that one value in the committed CSV reproduces the pinned `046f6f5a…` byte for byte, and the pin agreed with the CSV in #715 and #718. That is what made the repair safe to make surgically — 15.9pt was the deliberate correction, so the pin simply had to finish the interrupted step — and it is why the pin refresh is its own commit.
- The interesting failure is not the stale pin but the silence around it. `source_identity` is only read by the production IDML build, which no CI job runs, so a derived artifact had no guard at all; #720's own post-merge run was then cancelled by the three merges that followed, so even the runs that existed reported nothing. Three PRs later the only way to find it was to try the build by hand.
- Honest half-measure, recorded as such: the layout half of the gate now passes and the build's error is down to `snapshot_sha256` alone. That half binds the contract to a snapshot outside git, so it cannot be resolved from a checkout, and the approved layout has still not been re-validated against 15.9pt by a parity run.
- The line-ending fix looks cosmetic and is not: multi-window work depends on "git status is clean" carrying information, and this was the one file whose late edit caused the decoupling.

## 58. 2026-07-27: Review Refresh Stops Laundering Asset URIs (legacy-path 50→37)

What changed:

- `tools/sync_review.py` now calls `restore_registry_asset_uris` after copying generated pages from the finalized runtime bundle — the same restore step `review_bundle.py` has always applied when seeding `docs/_review`. The finalized bundle's RST carries staged file paths, so the data-refresh path was rewriting every semantic `asset:` reference in the review overlay back into a bare path on each sync; the seeding path preserved them, the refresh path laundered them.
- The nine review-overlay image references whose bytes are identical to their registry exports were keyed to `asset:` URIs (27 directives across 12 files, three languages). Verified per reference by byte comparison before rewriting: each key resolves — through the target's override where one exists — to the exact same file the bare path pointed at.
- Two references were deliberately NOT keyed, because the byte comparison showed they are different images: the review overlay pins the shared `front_controls.png` and `energy_saving.png`, while the registry's JE-1000F/US overrides (from the master `.ai`) carry the US three-socket panel and the textless v2 respectively — the registry rows even say the override is the intended image for this target ("禁止把区域插座图写回 common assets"). Swapping a printed image is a reviewer call, not a mechanical fix; the divergence is now explicit instead of silent.

Why it mattered:

- The publish gate landed in #722 covering only registry-resolved assets; the JE-1000F/US bundle still consumed 50 `legacy-path` images it could not see. The committed keying alone brings it to 41; the first sync cycle after merge restores the raw-LaTeX/raw-HTML references from template provenance as well, and the verified steady state is 37 — all of them Feishu attachment images (LCD icons + symbols), which are a different problem: their identity is the Feishu file token, so they need collection-level ownership (`feishu/*_attachments` rows exist already), not per-file keys.
- The first attempt was hand-keying `docs/_review` alone — and verification caught it being silently reverted: `check --source review` runs sync-review, which copied the finalized bundle back over the hand edits. The mechanism fix plus the keying together survive the full cycle (verified: `[sync-review] restored 45 semantic asset reference(s)`, review still carries `asset:` after check, manifest legacy count 50→37, registry-backed 20→22).
- Working-tree hygiene finding, recorded for the next window: sync-review also refreshes generated review pages' prose from templates/data (V2.0 wording like `DC 12V/USB OUTPUT`), so a `check --source review` run dirties `docs/_review` with legitimate-but-unrelated refreshes. Keep those out of unrelated commits.


## 58. 2026-07-27: Legacy-Path Blind Spot Ratcheted to Zero (JE-1000F/US)

What changed:

- The bundle finalizer attributes synced Feishu attachment images (`_repo_assets/data/phase2/_attachments/<category>/…`) to their registry collection rows (`feishu/lcd_icons_attachments`, `feishu/symbols_attachments`) as `feishu-attachment` manifest entries instead of `legacy-path`/`legacy-unmanaged`. Each row still records the exact bytes that shipped; the collection row's registry status now gates publish for the whole column; the RST keeps its path reference because the file identity is a Feishu token that changes on re-upload — these images are deliberately never keyed per file. No matching collection row (or a scope miss) falls back to legacy-path, so no attribution is ever invented.
- Together with #726 (mechanical keying of 9 overlay paths + the sync-review laundering fix) and #730 (the two operator-reviewed image flips), the JE-1000F/US publish-gate blind spot went 50 → 0: `legacy_path_count=0`, `registry_asset_count=59`, verified with a full review-source build.

Why it mattered:

- The publish gate built in #722 governed 20 of 70 consumed assets; the other 50 could ship a quarantined or wrong image with no gate in the way. Now every image in the bundle is either registry-resolved, explicitly review-overridden, or attributed to a status-gated collection — and a single status flip in the Feishu asset table stops the affected column from printing.
- The classification is fail-open to visible debt by design: an attachment tree with no collection row stays `legacy-path` rather than being silently attributed, so the zero is honest and a future unmanaged tree re-raises the count instead of hiding under it.


## 59. 2026-07-28: The Design-Side Request List Audited Down to One Item

What changed:

- Closed out `kr/image_placeholders`: the operator challenged the standing "design side owes us images" list against the delivered master `.ai`, and a key-by-key resolution audit proved the KR pages' 8 semantic references all resolve for the KR target from master-extracted exports — the placeholder row was a fossil from the KR backport round, predating the harvest. Row deleted; the registry test now pins its absence.
- Refreshed the shared `operation/energy_saving` export: the committed common-assets PNG was a wheeled non-JE-1000F model with burned-in English — every line resolving through the shared row (KR, EU, JP, CN templates all reference the key) printed a wrong-model figure. The textless v2 extracted from the master (p13) is now the shared bytes, hash updated in the same change so `asset-check` proves consistency. The US line is unaffected — it already resolves through its `je1000f_us` override to the same art.
- The shared-row note records the fleet caveat: the body drawn is a JE-1000F, so a non-JE-1000F line finalizing for print adds a model override (the `main_power` trio set this precedent in the #662 swap) rather than editing the shared bytes back.

Why it mattered:

- "向设计侧要图" was carrying three items on momentum; after the audit only `mark/jp_certifications` genuinely needs external input — and even that is "provide the JP manual's .ai if one exists" before it is "ask a designer to draw". `illustration/cjk_operation_set` remains registered but is now understood as engineering work (switch CN/JP lines to the textless assets), not design work.
- The KR line's image needs were satisfied by an asset harvest that happened after the debt was registered — nobody had re-checked the debt against the new supply. Standing request lists rot in exactly this way; the fix was one resolution loop, not new assets.

## 60. 2026-07-28: The Front-Controls Base Map Stops Punching Holes In Itself

What changed:

- `tools/asset_pipeline/leaders.py` + the `drop_leader_strokes` recipe op remove callout leaders as **objects** instead of painting over them. The leaders sit *above* the device artwork and each carries a wide white halo under a thin dark line; that halo is what erases the vent grille and the panel divider wherever a leader crosses them, so a `whiteout` can only ever punch a hole. Turning each leader's paint operator into `n` (end path, paint nothing) lets the artwork underneath render intact — the geometry bytes are not touched.
- `overview/je1000f_us/front_controls` moved to the new op and its 8 `whiteout` blocks (up to 77x40pt) are gone. Re-exported, registry hashes and note updated.
- The corrected asset lives in its own recipe, `data/asset_recipes/manual_je1000f_us_front_controls.json`, because the master recipe's SHA-256 is pinned immutably by the reviewed App-UI promotion (`EXPECTED_RECIPE_SHA256`, decided 2026-07-20). The master recipe and the promotion are byte-unchanged; a test asserts both that the split recipe uses the structural op and that the master still matches the frozen pin.

Why it mattered:

- The operator spotted the artifact by eye ("这一块白 那一块白的") on a shipped base map. The diagnosis had to explain *why* three separate patch-style attempts all failed: text-only redaction leaves every leader in frame; per-leader white corridors still cut the device outline where a leader crosses it; and layer toggling does nothing because all page art is on one OCG. Flattened erasure cannot restore what a halo hid — only removing the halo can.
- Two detection traps are now pinned by tests rather than rediscovered: a perfectly horizontal or vertical line has a **zero-area** bounding box, so `fitz.Rect.intersects` reports False and every single-segment leader goes missing (this cost a full round — 10 of 13 leaders found, 3 left standing); and the content stream stores local coordinates under `cm`, so the walker must track the CTM before comparing geometry in page space.
- The op is deliberately structural — it finds leaders by their halo/line stroke-width pair and axis alignment — so no coordinates are baked into a recipe where they could rot. It refuses to run silently: extraction fails unless it suppresses exactly two strokes per detected leader.
- Scope was cut on evidence, not ambition: the same op made `operation/main_power` and `overview/right_side_ports` **worse** (their leaders are not halo/line pairs, and removing their whiteouts exposed artwork the blocks had been hiding), so both keep their existing recipe. Only the asset the operator reported is changed.

## 61. 2026-07-31: Queue Runners Share the Feishu Record Transport Boundary (Workstream W / K8 slice 1)

What changed:

- Added the shared `run_lark_cli_json` boundary to [`tools/feishu_record_transport.py`](../tools/feishu_record_transport.py). It owns command execution, injected CLI resolution, JSON parsing, and Feishu API response validation for queue and build-listener callers.
- Converted [`tools/queue_lark_ops.py`](../tools/queue_lark_ops.py) and [`tools/listen_build_queue_lark.py`](../tools/listen_build_queue_lark.py) into compatibility wrappers over that boundary, preserving their patchable entrypoint names and listener-specific output behavior.
- Added focused transport and delegation tests. Retry/backoff, pagination, snapshot locking, and the remaining Feishu callers stay in their separately gated K8 slices.

Why it mattered:

- Queue runners no longer carry independent copies of the lowest-level `lark-cli` subprocess and response-validation mechanics, so the next K8 slices have one transport seam to extend without changing queue record semantics.
- The first slice deliberately keeps retry policy and pagination unchanged; this is a behavior-preserving boundary move, not a new external-integration policy.

## 62. 2026-07-31: Spec and Schema Callers Join the Feishu Transport (Workstream W / K8 slice 2)

What changed:

- Routed [`tools/spec_master_rebuild.py`](../tools/spec_master_rebuild.py)'s base commands through `feishu_record_transport`, preserving its temporary JSON payload cleanup, token redaction, and existing `_run_lark_base` seam.
- Routed [`tools/bitable_schema.py`](../tools/bitable_schema.py)'s profile/identity-aware commands through the same transport, preserving its stdout/stderr response fallback and patchable `_lark` seam.
- Added delegation tests for both callers. Retry/backoff, pagination, and snapshot locking remain separate slices; this PR does not change schema or source-record semantics.

Why it mattered:

- The queue, listener, spec-master, and schema workflows now share one lowest-level `lark-cli` subprocess and common response-validation boundary. Caller-specific routing and payload parsing remain at the wrappers where they belong.
- Keeping the wrappers stable avoids breaking existing tests and operational scripts while making the remaining K8 policy changes a single transport-level change.

## 63. 2026-07-31: Feishu Transport Owns Rate-Limit Retry and Pagination Policy (Workstream W / K8 slice 3)

What changed:

- Added bounded exponential retry/backoff for rate-limited `lark-cli` responses, including bounded `retry_after` hints, to [`tools/feishu_record_transport.py`](../tools/feishu_record_transport.py).
- Added one page iterator with a positive-limit check, offset advancement, and fail-closed empty-page handling when a response claims more data.
- Routed field-list pagination in [`tools/listen_build_queue_lark.py`](../tools/listen_build_queue_lark.py) and record reads in [`tools/bitable_schema.py`](../tools/bitable_schema.py) through that iterator without changing identity, profile, schema, or record mapping semantics.
- Added focused tests for retry timing, retry-after handling, offset ownership, and pagination behavior.

Why it mattered:

- Feishu callers now have one bounded rate-limit policy and one pagination safety policy instead of independently reimplementing the two failure-prone mechanics.
- The slice deliberately leaves snapshot write locking to the next K8 gate and does not change source-table or schema semantics.

## 64. 2026-07-31: Phase2 Snapshot Writes Take One Cross-Process Lock (Workstream W / K8 slice 4)

What changed:

- Added a portable advisory lock in [`tools/sync_data_records.py`](../tools/sync_data_records.py), using a stable sibling lock file for each phase2 export root.
- Wrapped the final batch of phase2 CSV, derived-file, and `snapshot_manifest.json` atomic replacements in [`tools/sync_data_runtime.py`](../tools/sync_data_runtime.py) with that lock.
- Kept dry-run behavior unchanged and added a POSIX exclusivity test; the lock file is operational state, not a snapshot input.

Why it mattered:

- Concurrent sync workers can still fetch and prepare independently, but their final multi-file snapshot commits cannot interleave, so a reader observes one complete writer result rather than a mixed CSV/manifest set.
- This closes the last K8 slice without changing source-table normalization, snapshot contents, or manifest semantics.

## 65. 2026-07-31: Reference Layout Identity Scaffold Stays Outside Activation (Workstream W / Stage 4a item 10)

What changed:

- Added [`tools/idml/reference_layout_scaffold.py`](../tools/idml/reference_layout_scaffold.py) and its named-output CLI [`tools/reference_layout_scaffold.py`](../tools/reference_layout_scaffold.py).
- The scaffold copies an existing 52-source reference contract's physical composition map, refreshes Manual IR identity/per-page digests, and emits a review-only `reference-layout-scaffold/v1` draft.
- Draft output is explicitly `approval.status=draft`, `production_eligible=false`, and is never written to the approved-plan registry.
- Source-ref order, page-language drift, missing frozen snapshot identity, and invalid physical composition fail closed before output.

Why it mattered:

- A refreshed snapshot no longer requires hand-editing 52 hashes before a reviewer can inspect the actual composition/approval surface.
- The production activation path remains unchanged and fail-closed: only an approved, registry-bound contract can govern IDML; a scaffold draft cannot silently become a fallback or production plan.

## 66. 2026-07-31: InDesign Finalize Jobs Are Explicit and Failure-Isolated (Workstream W / Stage 4a item 11)

What changed:

- Added [`tools/indesign_finalize_jobs.py`](../tools/indesign_finalize_jobs.py)
  and `python tools/indesign_finalize.py --jobs <manifest.json>` for batch
  orchestration around the existing one-document ExtendScript.
- The `indesign-finalize-jobs/v1` manifest requires every job to declare its
  PDF preset, output intent, output condition, and PDF/X level. Batch mode
  therefore cannot silently inherit a host's `[PDF/X-4:2008 (Japan)]` or ICC
  default for a different print contract.
- Each job is reported independently; one osascript/preflight failure does not
  stop the remaining jobs. The aggregate report includes before/after scans of
  the IDML directories and groups `indesign_package.complete=FALSE` entries for
  handoff follow-up.

Why it mattered:

- Finalize was previously a one-shot command with no safe batch boundary, so a
  failed design-host document required manual restart and gave no complete
  inventory of unfinished packages.
- The single-job path still uses the same extracted runner and keeps its
  existing version-pin, PDF/X, and preflight behavior; the new layer is
  additive and does not alter the production IDML or approval contracts.

## 67. 2026-07-31: App Page Ownership Moves Into the Approved Contract (Workstream W / Stage 4a item 13)

What changed:

- Added exact `page_owners` to the approved `app_add_device` component contract
  and validate that list against the Manual IR pages that contain Add Device
  art.
- Replaced the JE-1000F/US-named page predicates with generic component-page
  ownership helpers. Bundle asset freezing resolves the exact registered
  contract; prose promotion, page splitting, and story placement consume the
  same contract from the normalized approved plan.
- Added a maintainability regex that rejects model/region-named IDML page
  predicates, plus a synthetic future-target test proving that contract data
  alone can opt in a differently named source page.

Why it mattered:

- A new approved product line no longer needs another `is_<model>_<region>_*`
  branch to receive the App composition and its hidden assets.
- Ownership now fails closed on draft contracts, missing owners, wrong source
  refs, or mismatched page languages, while the existing 58-page composition,
  asset identities, and geometry remain unchanged.

## 68. 2026-07-31: IDML Assembly Uses Explicit Page Roles (Workstream W / Stage 4a item 14)

What changed:

- Added [`tools/idml/page_roles.py`](../tools/idml/page_roles.py) as the single
  target-neutral mapping from semantic source-page identity to production
  assembly role.
- Classified every projected page once in [`tools/export_idml.py`](../tools/export_idml.py)
  and replaced its independent prefix, substring, and stem routing checks with
  role comparisons.
- Added inventory and CLI safety nets: every current template page must have an
  explicit role, while an unknown page keeps the historical prose fallback and
  emits one deterministic `assembly coverage` warning naming its source ref.

Why it mattered:

- A renamed or newly introduced special page can no longer silently look like
  intentionally ordinary prose; the export remains reviewable and identifies
  the exact missing assembly decision.
- The change adds no model/region/language predicate and does not alter existing
  content, geometry, composition, or golden IDML bytes.

## 69. 2026-07-31: Release CSV Exposes Native Layout Signals (Workstream W / Stage 4a item 15)

What changed:

- Audited the roadmap item against current `main` and confirmed that PR #723
  already records native page and overset counts in release JSON under
  `indesign_package.preflight`; no duplicate top-level schema was added.
- Added `indesign_preflight_page_count` and
  `indesign_preflight_overset_stories` to the flat release CSV so dashboards
  can consume the same two signals without decoding nested JSON.
- Preserved an explicit empty overset list as `0`, while a legacy/partial
  finalize report with no overset field now remains unknown (`null` in the
  summary and blank in CSV) instead of looking clean.

Why it mattered:

- Release automation can trend page drift and overset counts directly from its
  scalar carrier, while JSON and CSV still share one collector authority.
- “No native evidence” is no longer conflated with “native preflight verified
  zero oversets”; the change adds observability without adding a release gate.

## 70. 2026-07-31: Review Propagation Gets a Read-Only Safety Ledger (Workstream W / Stage 5 item 7)

What changed:

- Extended [`tools/check_review_branch_sync.py`](../tools/check_review_branch_sync.py)
  with `--json` and moved evidence collection/classification into
  [`tools/review_propagation_ledger.py`](../tools/review_propagation_ledger.py).
- The ledger reads the checked-in manifest from every live `review/*` branch,
  including legacy `review/id-*` names, and emits one row per affected
  branch/shared-source pair with seed SHA, target identity, mapped derivative,
  and a reason-coded classification.
- `merge_params_safe` now requires a narrow machine proof: source line
  structure is stable, all changed lines retain the same placeholders, and the
  review derivative still matches the seed template outside placeholder values.
  Every unresolved or broader change becomes `needs_human`.

Why it mattered:

- The old advisory named branches from a region-name heuristic and could not
  distinguish a safe parameter refresh from a reviewer-clobber risk.
- A real 15-branch replay now keeps legacy targets visible, narrows direct
  template impact through seed/current manifest references, and abstains rather
  than inventing safety. The ledger remains report-only: no sync, branch write,
  or PR creation was introduced before the K15 design gate is approved.

## 71. 2026-07-31: IDML Primary Font Family Becomes One Token (Workstream W / Stage 5 item 8)

What changed:

- Added an immutable primary-family token in
  [`tools/idml/font_family.py`](../tools/idml/font_family.py), including the
  existing face-resource and delivery-manifest metadata.
- Production paragraph styles, flow paragraph styles, `Fonts.xml`, and the
  designer delivery font table now consume that one contract.
- Added byte-level regression locks for all four outputs plus a static guard
  against reintroducing the primary family literal in former authority sites.

Why it mattered:

- A future family change can no longer update the visible styles while leaving
  the IDML font resources or designer handoff manifest stale.
- The consolidation leaves generated bytes and approved reference-layout
  hashes unchanged; language-specific CJK routing remains behind its separate
  operator gate.

## 72. 2026-07-31: Japanese and Korean IDML Gain Real Golden Baselines (Workstream W / Stage 5 item 9)

What changed:

- Added committed Japanese and Korean snapshots to the production IDML golden
  matrix and made the test execute all four registered variants.
- The CJK fixture adapter now localizes representative prose, component,
  list-table, symbol, LCD, troubleshooting, and specification content, while
  preserving the source bundle's composition coverage.
- Added deterministic double-build checks, language-specific text sentinels,
  and a Japanese-versus-Korean byte-distinctness assertion.

Why it mattered:

- The earlier language adapter changed only `HBApplyLang`; semantic page names
  and content remained English, so French, Japanese, and Korean attempts could
  produce the same package and still look like a valid variant.
- The new snapshots are a truthful byte-level safety net for the gated CJK
  fallback work. This slice changes no exporter behavior, font selection,
  reference-layout contract, or production source data.

## 73. 2026-07-31: Product Overview Chrome Consumes Localized Copy (Workstream W / Stage 5 item 6)

What changed:

- Replaced seven literal Product Overview page, panel, and part labels in the
  US Spanish, French, and Brazilian Portuguese templates with the existing
  `product_overview.*` runtime copy keys.
- Added a characterization test that resolves the committed phase2 fixture and
  locks every migrated template to its pre-migration SHA-256.
- Recorded the migration boundary in the maintainer and operator guides; EU
  raw-LaTeX pages and descriptive image-alt prose remain outside this pilot.

Why it mattered:

- The same localized chrome no longer has two independently editable sources.
- Missing copy data still fails closed, while the byte-parity lock proves the
  migration changes no rendered RST, page geometry, reference-layout contract,
  production Base row, or asset.

## 74. 2026-07-31: PV Input Range Moves to Page-Value Data (Workstream W / Stage 5 item 4a)

What changed:

- Replaced the literal solar-panel input range in eight shared-language
  charging-method templates with `|PV_INPUT_RANGE|`.
- Added semantic fixture rows using `Page=charging_methods`,
  `Row_key=pv_input_range`, and `Slot_key=value`; no legacy `tpl_*` binding was
  introduced.
- Added a page contract and an eight-language characterization test. Every
  resolved template retains its pre-migration SHA-256.

Why it mattered:

- One safety-critical electrical parameter no longer has eight independently
  editable template copies.
- Missing target data now fails closed. The repo slice writes no production
  Base row; F6 seed and diff-report evidence remain an explicit operator gate.

## 75. 2026-07-31: Connector and UPS Timing Move to Page Values (Workstream W / Stage 5 item 5a)

What changed:

- Replaced four literal `DC8020` connector spans in each of eight shared
  charging-method templates with `|DC_INPUT_CONNECTOR|`.
- Replaced the positive UPS transfer time in each shared-language UPS template
  with `|UPS_TRANSFER_TIME|`; the separate zero-millisecond incompatibility
  cautions remain authored prose.
- Added semantic fixture rows, charging/UPS page contracts, and sixteen
  pre-migration SHA-256 characterization locks.

Why it mattered:

- Model-specific connector and transfer-time changes now have one structured
  source per target instead of repeated prose edits across eight languages.
- Missing target data fails closed while rendered RST remains byte-identical.
  Production Base seed and diff-report evidence remain an F6 operator gate.

## 76. 2026-07-31: InDesign Finalize Uses a Native JSX Batch Loop (Workstream W / Stage 4a item 12)

What changed:

- Kept the existing `indesign-finalize-jobs/v1` manifest and explicit print
  contract, but grouped jobs by their declared InDesign application.
- Added one ExtendScript outer loop per application group. It invokes the
  existing one-document finalizer sequentially, catches an unexpected failure
  around each document, and writes a transport report without aborting later
  jobs.
- Preserved independent INDD/PDF/preflight outputs, Python-side PDF/X
  validation, aggregate ordering, version-pin checks, and single-job behavior.

Why it mattered:

- Multi-target design-host runs no longer pay one AppleScript/InDesign dispatch
  per document while one bad document still cannot hide or cancel its siblings.
- CI now locks grouping, manifest-order preservation, and the JSX isolation
  structure. A pinned design Mac also processed two documents in one dispatch;
  the evidence and fixture limitations are recorded in
  [`tests/indesign_finalize_batch_acceptance_2026-07-31.md`](tests/indesign_finalize_batch_acceptance_2026-07-31.md),
  without claiming production parity or release approval.
## 77. 2026-07-31: Review-Branch Propagation Design Approved (Workstream V / K15)

What changed:

- Recorded a live inventory of 15 open review branches/PRs: 14 already own only
  `docs/_review/**` deltas, one carries four historical `_build` images, and the
  fleet is 295–624 commits behind current `main`.
- Drafted the K15 contract for derivative-only branch ownership, an exact
  advanceable shared-source pin, reproducible three-way classification,
  per-target bump PRs with rendered evidence, fail-visible migration, and a
  propagation-lag ledger.
- Recorded the operator's 2026-07-31 approval of the design boundaries. The
  design still does not mutate a review branch, change a workflow, or authorize
  propagation writers by itself; those remain bounded implementation slices.

Why it mattered:

- The design treats branch ancestry and the existing `merge_params` behavior as
  insufficient proof, so scale-out cannot silently overwrite reviewer edits or
  label an unreachable branch inventory clean.
- Workstream V now has approved boundaries and bounded follow-on slices rather
  than a one-shot rewrite; the one-family pilot can proceed after its registered
  implementation prerequisites are present.

## 78. 2026-07-31: Versioned Publish Freezes Its Phase2 Snapshot (Workstream W / E1-PR1)

What changed:

- Added path-utils-backed release snapshot paths under
  `reports/releases/<model>/<region>/<lang>/versions/<version>/snapshot/`.
- Versioned `release-manifest` now copies the complete valid phase2 root,
  including attachments, and records an immutable identity with the file
  inventory/content hash, source-manifest revision, freeze time, and target
  matrix. Its JSON/CSV paths resolve against the archive, not live data.
- Queue Publish passes its version into the manifest step and stages both the
  frozen snapshot and timestamped manifests out of the disposable build
  worktree. Identical retries are idempotent; rebind or archive drift fails.

Why it mattered:

- A published version no longer loses its data inputs when the worker removes
  its temporary worktree or when `data/phase2` is synchronized again.
- This closes E1's archive/binding slice without overstating the remaining
  end-to-end rebuild-equivalence proof, which stays in E1-PR2.

## 79. 2026-07-31: Archived Releases Rebuild Byte-for-Byte (Workstream W / E1-PR2)

What changed:

- Versioned Publish now starts from a clean tracked worktree and derives
  `SOURCE_DATE_EPOCH` from its full Git commit. Staged image names use content
  hashes, while release DOCX files receive canonical metadata, image
  descriptions, ZIP timestamps, and ZIP metadata.
- Release manifests record the reproducibility policy, source epoch, and the
  DOCX/Markdown/PDF byte-equivalence artifact set. Full Git SHA and immutable
  snapshot bindings are mandatory for a versioned manifest.
- Added `build.py release-rebuild-verify --manifest ...`: it checks the exact
  toolchain and archived snapshot, republishes in an isolated detached worktree,
  compares all three artifact hashes, and writes a version-sidecar verification
  report without changing the snapshot.

Why it mattered:

- A release can now prove that the same repository commit plus its archived
  phase2 input reproduces the shipped DOCX, Markdown, and PDF bytes instead of
  merely naming those inputs.
- Path, timestamp, toolchain, snapshot, and artifact drift all fail closed, so
  Workstream J's traceability exit criteria are complete.

## 80. 2026-07-31: Queue Dispatch Uses a Verified Claim Lease (Workstream W / Stage 4b item 1)

What changed:

- Added a two-hour `claim_token` / `claim_expires_at` lease to the existing
  `构建结果` RUNNING transition, without adding a live Base column.
- Queue workers now write the claim across a row group, refetch outside the
  pending view, and start sync/build only when every row still has the same
  unexpired token. Active claims are skipped and expired claims are reclaimable.
- Added overlapping-dispatch fixtures proving that only the latest verified
  token proceeds, plus parsing, expiry, pending-selection, and group-writeback
  coverage.

Why it mattered:

- A failed RUNNING writeback can no longer degrade into an unclaimed build, and
  the common overlapping-dispatch race now has an explicit ownership gate.
- The contract records that Feishu upsert has no compare-and-swap primitive:
  this K12-min slice is a verified lease, while shared workflow concurrency and
  full stale-claim recovery remain separate follow-on work.

## 81. 2026-07-31: Queue Workflows Share Record Domains and a Vercel Mutex (Workstream W / Stage 4b item 2)

What changed:

- Build Draft Package and Publish now share one GitHub Actions concurrency
  domain per Document_link record; conservative batch dispatches share the
  `batch` slot, while Start Review uses its own review-init record domain.
- Publish processing and site staging remain record-scoped. The staged site is
  handed to a separate job, where one global concurrency group serializes the
  Vercel production build, deployment, and `HTML_link` writeback.
- Added workflow-structure tests for the shared keys, non-cancelling policy,
  run-scoped artifact handoff, independent TeX smoke slot, and global Vercel
  mutex.

Why it mattered:

- Different document records no longer wait behind one repository-wide build
  lock, while Draft and Publish cannot race on the same Document_link row.
- The single mutable Vercel production project still has exactly one publisher
  at a time, and the verified Feishu claim lease remains the backstop for
  targeted-versus-batch overlap.

## 82. 2026-07-31: Queue Review Overlay Is Target-Scoped (Workstream W / Stage 4b acceptance follow-up)

What changed:

- Queue builds now replace only `docs/_review/<model>/<region>` in the clean
  `origin/main` build worktree instead of replacing the complete review tree.
- Added a regression fixture where the selected review branch contains stale
  content for a sibling region; the sibling on `main` must remain byte-for-byte
  unchanged while the selected target is overlaid.
- A review ref that lacks the selected target now fails with the exact missing
  model/region in the error instead of accepting any unrelated `_review` tree.

Why it mattered:

- The Stage 4b live two-record acceptance run exposed a JP Publish failure when
  unrelated US review drift made the versioned release worktree dirty.
- Target-scoped overlay preserves the current-main toolchain and selected review
  content without cross-target contamination, which is required before safely
  exercising independent queue records concurrently.

## 83. 2026-07-31: Queue Artifacts Are Selective and Time-Bounded (Workstream W / Stage 4b item 3)

What changed:

- Added an explicit retention window to every GitHub Actions artifact upload:
  1 day for the Vercel deployment handoff, 7 days for Draft/Start Review/
  preview/OpenClaw inspection artifacts, and 14 days for Publish release
  artifacts. The phase2 content backup keeps its independent 90-day window.
- Removed broad queue uploads of bare `docs/_build`, `docs/_review`, and
  `reports/releases`. Draft now retains final Word/Markdown surfaces, Start
  Review retains the review bundle components, and Publish retains only
  version/latest/manifest release surfaces plus phase2 identity files.
- Added a workflow policy test that fails when an upload omits retention or
  when the queue artifact path contract broadens again.

Why it mattered:

- Generated RST trees, duplicate Vercel inputs, and timestamped release trees
  no longer consume artifact quota for the platform default retention period.
- Deployment still receives the exact static site it consumes, operators keep
  the final delivery/diagnostic files needed for review, and restore retention
  remains governed by the backup contract rather than the CI quota policy.

## 84. 2026-07-31: Skipped Raw Becomes an Approved Baseline (Workstream W / Stage 5 item 1)

What changed:

- Approved reference-layout plans now require a non-negative
  `idml_contract.max_skipped_raw` baseline; the JE-1000F/US approved plan pins
  the observed accepted value at zero.
- Production resolves the page plan before applying the skipped-raw gate, then
  rejects approved targets only when the current total exceeds that frozen
  baseline. The error names every affected Manual IR page and count.
- Ordinary/fallback targets retain the Stage 0 report-only sensor, while the
  standalone `manual-ir --strict` command remains an explicit zero-tolerance
  check.

Why it mattered:

- The previous production path rejected any skipped raw before loading the
  approved plan, which was stricter than the operator-approved policy but not
  represented in a reviewable contract.
- Acceptance is now visible, target-bound, and hash-covered by the approved
  plan instead of being an undocumented exporter side effect.

## 85. 2026-07-31: Strict IDML Rejects Unknown Languages (Workstream W / Stage 5 item 2)

What changed:

- Strict Manual IR validation now checks the top-level build language, frozen
  manifest-declared languages, and every page language against the shared
  language registry, reporting the exact source location for each unknown
  token.
- Approved-reference plan validation applies the same gate before production
  composition. Ordinary/fallback export keeps its prior permissive behavior.
- Registered historical aliases remain valid, and the non-content `cover` and
  `toc` page roles are excluded from language registration checks.

Why it mattered:

- An unregistered page language previously reached localized IDML loaders and
  could silently inherit English symbol copy or skip governed layout behavior.
- Strict production now fails at the contract boundary, while exploratory and
  legacy fallback builds retain their existing compatibility path.

## 86. 2026-07-31: Capability Selection Reaches Every Manual Family (Workstream W / Stage 5 item 3)

What changed:

- Added `capability: UPS功能` to every existing `06_ups_mode` page entry across
  all 17 family manifests, covering 24 single-language and multilingual page
  occurrences.
- Refreshed the deterministic family diff carriers so both anchors plus all 15
  folded manifests continue to reconstruct with canonical byte identity.
- Added a repository-wide contract test that rejects a family manifest whose
  UPS page is missing or misstates its capability annotation.

Why it mattered:

- Assembly-time capability selection was previously effective only for the US
  multilingual manifest even though JP, KR, EU, and other families carried the
  same semantic UPS page.
- Every current configured target retains the exact same materialized page
  sequence, while future models whose `UPS功能` value is false can now drop the
  chapter consistently without a family-specific code path.

## 87. 2026-07-31: Editable IDML CJK Text Gets Explicit Font Runs (Workstream W / Stage 5 item 10)

What changed:

- Added `CJK_FONT_FAMILY_TOKEN` as the single renderer authority for
  `idml_font_family_cjk`, centralizing the existing Arial Unicode MS font
  resource and delivery row without changing their generated bytes.
- Routed Han, Kana, Hangul, CJK punctuation, and fullwidth/halfwidth forms to
  explicit editable character runs, while preserving exact symbol-font
  mappings as the higher-priority rule.
- Made heading and LCD component font-style overrides compose safely with
  fallback runs instead of emitting duplicate XML attributes.
- Re-baselined only the localized Japanese and Korean Story XML golden parts;
  English and French packages remain byte-identical.

Why it mattered:

- CJK text previously inherited the Gilroy paragraph family even though that
  family does not provide the required glyphs, leaving substitution to the
  opening InDesign workstation.
- The fallback family is now explicit, testable, and visible in each affected
  Story XML without conflating font delivery with page geometry. Approved
  reference-layout hashes therefore remain stable and do not need a rebind.

## 88. 2026-07-31: IDML Height Budgets Understand East Asian Width (Workstream W / Stage 5 item 11)

What changed:

- Added one font-file-independent `line_metrics.py` contract for portable text
  width and wrapped-line estimates.
- Migrated generic story, flow, symbol-table, warning/FCC, operation/LCD,
  key-combination, troubleshooting, H1, and emphasis estimates from duplicated
  character-count arithmetic to that shared contract.
- Preserved each consumer's existing narrow-glyph ratio and minimum capacity;
  `W`/`F` characters now occupy one em, combining marks occupy zero width, and
  ambiguous-width characters remain narrow.
- Added direct Unicode-width and production-story budget tests. All four
  EN/FR/JA/KO composed golden IDML packages remain byte-identical.

Why it mattered:

- CJK fallback runs made glyph selection explicit, but the surrounding frame
  budgets still treated one ideograph like one average 0.52-em Latin glyph.
- Future localized copy now reserves conservative space before InDesign opens,
  without making build results depend on a workstation font installation or
  disturbing existing approved Latin layouts.
