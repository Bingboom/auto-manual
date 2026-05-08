# Code Optimization Log

Updated: 2026-05-07

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
- added config `extends` support and moved shared US single-language defaults into [`config-bases/us-single-language-base.yaml`](../config-bases/us-single-language-base.yaml) so `config.us-en/es/fr.yaml` became thin overrides with manifest-owned page stacks

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
- added shared target/config defaults in [`tools/target_defaults.py`](../tools/target_defaults.py) and rewired [`scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py) plus [`scripts/build_us_manuals.ps1`](../scripts/build_us_manuals.ps1) to derive matrix targets from shared metadata instead of duplicating literals
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
- updated [`next_optimization_checklist.md`](next_optimization_checklist.md), [`optimization_project.md`](../optimization_project.md), [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md), and [`architecture/Hello_Docs_Architecture.md`](architecture/Hello_Docs_Architecture.md) to match the closed milestone

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
- refreshed [`../optimization_project.md`](../optimization_project.md), [`next_optimization_checklist.md`](next_optimization_checklist.md), and [`dev/orchestration_module_map.md`](dev/orchestration_module_map.md) so roadmap, checklist, and module ownership match the current baseline

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

## 32. 2026-05-08: Topic Map Fixture Contract and Adapter

Main outcomes:

- added fixture-backed topic map tables under [`../tests/fixtures/topic_map/`](../tests/fixtures/topic_map/) for topic registry, fields, assets, rules, page topic map, manual page map, and topic content
- added [`../tools/topic_map_contract.py`](../tools/topic_map_contract.py) so topic map exports can fail on schema drift, unknown topic types, missing linked topics, missing templates/assets, missing fallback language, invalid rules, and invalid page/manual ordering
- added [`../tools/topic_map_adapter.py`](../tools/topic_map_adapter.py) to convert topic map fixture rows into the existing `content_assembly` CSV shape without changing the live build path
- documented local validator and adapter commands in [`dev/topic_map_assembly_plan.md`](dev/topic_map_assembly_plan.md)
- added tests that validate the topic-map fixture contract and prove the adapter output can still satisfy the current `03_product_overview` assembly contract

Why it mattered:

- topic map management can now be modeled in Feishu/Lark Base without making the PDF/HTML build depend on live Base reads
- the first adapter preserves the existing assembly boundary while allowing topic ids, topic fields, and page topic ordering to become the future source of truth
- future template splitting can move one page at a time from block fixtures toward topic-map fixtures with a fixture-backed drift gate
