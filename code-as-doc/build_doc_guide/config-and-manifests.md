# Build guide: config families, manifests and snapshots

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

- `tools/manifest_lint.py --json` is a report-only inventory sentinel for config-backed page manifests. It scans every `configs/config*.yaml` reference and every `docs/manifests/*.yaml` file, reporting orphan manifests, invalid/missing sources, and config/manifest language-set drift without blocking a build.

- `tools/manifest_family.py` is the non-mutating family-manifest pilot. Use `diff --base <base.yaml> --target <target.yaml> --output <diff.json>` to create the deterministic `family-manifest-diff/v1` carrier, then use `roundtrip` with the same base, target, and diff to assert `"byte_identical": true`. This pilot does not rewrite `docs/manifests/`; checked-in generation is a later stage.
- `python -m tools.manifest_family fold --root . --index docs/manifests/family/index.yaml` checks the family index: four anchor YAML manifests plus 16 carrier diffs cover all 20 current YAML goldens with canonical byte identity. The two battery-pack cells own separate anchors (`manual_bp-us.yaml` for `BP@INTL`, target-neutral `manual_bp-jp.yaml` for `BP@JP`). Add `--write` only to refresh the tracked diff carriers; it never edits a YAML manifest.
- `tools/skeleton_resolve.py` keeps the public `emit` / `verify` / `plan` CLI surface unchanged. Its Python `resolve_plan(..., product_plan=...)` API now accepts target-owned `house_style_version`, `enabled_optional_slots`, and `terminal_slots` selections; when a blueprint declares order profiles, load and pass both carrier maps with `load_slot_template_catalog(...)` so a version cannot silently lose its safety/warranty variant. Blueprints declare the complete slot universe and named order profiles; optional front/body slots are opt-in, back slots have the single `terminal_slots` selector, and calls without a product plan still resolve the required/capability core. BP@INTL continues to use the legacy region-profile terminal selector and remains byte-identical. Do not put a model/title/file/page conditional in the resolver; R3c and later targets supply only plan/config/source/asset data.
- Family manifests carry capability annotations at the page entry, not in a target-specific side table. All current `06_ups_mode` entries declare `capability: UPS功能`, so JP/KR/EU and the other current families use the same assembly-time keep/drop decision as US. When adding a capability-governed page to another family, add the same annotation there and refresh the fold carriers with `fold --write`.
- `.github/workflows/manifest-regenerate-diff.yml` runs that fold check on pull requests touching configs, manifests, or carrier code; this is the CI red gate for a manually edited generated manifest. It also runs `manifest_lint` as a report-only inventory.

## 2. Config Rule

Do not create one config file per model.

Current shared config families:

- [`configs/config.us.yaml`](../../configs/config.us.yaml): shared EN / US template family
- [`configs/config.us-en.yaml`](../../configs/config.us-en.yaml): canonical US English single-language review / CI / explicit review-preview landing target
- [`configs/config.ja.yaml`](../../configs/config.ja.yaml): shared JP template family
- [`configs/config.zh.yaml`](../../configs/config.zh.yaml): shared CN zh template family backed by [`docs/manifests/manual_zh.yaml`](../../docs/manifests/manual_zh.yaml)
- [`configs/config.eu.yaml`](../../configs/config.eu.yaml): shared EU merged family backed by [`docs/manifests/manual_eu.yaml`](../../docs/manifests/manual_eu.yaml)
- [`configs/config.eu-en.yaml`](../../configs/config.eu-en.yaml), [`configs/config.eu-fr.yaml`](../../configs/config.eu-fr.yaml), [`configs/config.eu-es.yaml`](../../configs/config.eu-es.yaml), [`configs/config.eu-de.yaml`](../../configs/config.eu-de.yaml), [`configs/config.eu-it.yaml`](../../configs/config.eu-it.yaml), and [`configs/config.eu-uk.yaml`](../../configs/config.eu-uk.yaml): explicit EU single-language entrypoints backed by [`../docs/manifests/manual_eu-en.yaml`](../../docs/manifests/manual_eu-en.yaml) plus the corresponding [`../docs/manifests/manual_eu-single-*.yaml`](../../docs/manifests) stacks
- [`configs/config.us-en.yaml`](../../configs/config.us-en.yaml), [`configs/config.us-es.yaml`](../../configs/config.us-es.yaml), [`configs/config.us-fr.yaml`](../../configs/config.us-fr.yaml), and [`configs/config.pt-br.yaml`](../../configs/config.pt-br.yaml) now inherit shared single-language US defaults from [`../configs/config-bases/us-single-language-base.yaml`](../../configs/config-bases/us-single-language-base.yaml); keep shared defaults there and keep language-specific page stacks in [`../docs/manifests/manual_us-single-en.yaml`](../../docs/manifests/manual_us-single-en.yaml), [`../docs/manifests/manual_us-single-es.yaml`](../../docs/manifests/manual_us-single-es.yaml), [`../docs/manifests/manual_us-single-fr.yaml`](../../docs/manifests/manual_us-single-fr.yaml), and [`../docs/manifests/manual_pt-br.yaml`](../../docs/manifests/manual_pt-br.yaml)

Page-stack note:

- shared config families may resolve their page stack through `paths.page_manifest`
- keep manifest-driven page order changes under [`docs/manifests/`](../../docs/manifests)
- for a genuine model-only generated-page layout exception, keep the family manifest and declare `model_overrides.<MODEL>.recipe` / `template` on that `generated_page`; the default recipe/template remains the path for every other model
- keep merged-language and single-language preface components separate: `manual_au-en.yaml` uses the English-only `page_shared/en/00_preface_single_language.rst`; the US en/fr/es document manifests intentionally keep the trilingual `page_shared/en/00_preface.rst` for IDML/Word/PDF
- Web-only single-language projection is declared under `build.web_language_block_pages`; do not add `lang_blocks` to the US en/fr/es manifests, because that would also trim the document outputs

Pass target differences through:

- `--model`
- `--region`
- `build.targets`
- generated `data/phase2/*.csv` snapshots

Mirror repository sync rule:

- [`../.github/workflows/sync-hello-docs.yml`](../../.github/workflows/sync-hello-docs.yml) runs only in `Bingboom/auto-manual` on `main` pushes or manual dispatches from `main`
- the workflow imports the exact source Git tree into `Bingboom/Hello-Docs` and creates a mirror commit from that tree, so checkout attributes cannot rewrite blobs such as mixed-line-ending CSV files; it does not copy repository Secrets or Variables
- configure `HELLO_DOCS_SYNC_TOKEN` in the source repo with write access to `Bingboom/Hello-Docs` contents and workflows, because the mirrored tree includes `.github/workflows/**`
- keep code changes in `Bingboom/auto-manual`; keep the alternate Feishu Base IDs, Feishu app credentials, OpenClaw credentials, and queue/runtime toggles as GitHub Secrets / Variables in `Bingboom/Hello-Docs`
- set the mirror repo variable `FEISHU_BUILD_QUEUE_PAUSED=true` until the alternate Feishu credentials and table/view bindings are present; Feishu runtime workflows such as `feishu-build-queue.yml`, `feishu-draft-build-queue.yml`, `feishu-start-review.yml`, and `cred-health-check.yml` skip only in `Bingboom/Hello-Docs` while this mirror variable is true, so a same-named variable in `Bingboom/auto-manual` does not change the source repo behavior
- copy [`../scripts/hello_docs_binding.env.example`](../../scripts/hello_docs_binding.env.example) to a gitignored local file such as `.tmp/hello-docs-binding/env.sh`, fill the alternate Feishu/OpenClaw values there, then run [`../scripts/configure_hello_docs_binding.sh --env-file .tmp/hello-docs-binding/env.sh --dry-run`](../../scripts/configure_hello_docs_binding.sh) first and rerun without `--dry-run`; add `--include-optional` when the env file also has mirror-only Vercel, DingTalk, Feishu IM, Cloudflare tunnel, or OpenClaw adapter variables, and add `--unpause` only when the audit should also flip `FEISHU_BUILD_QUEUE_PAUSED=false`
- run [`../scripts/audit_hello_docs_binding.sh --report-only`](../../scripts/audit_hello_docs_binding.sh) to check source/mirror tree parity, the source sync token, mirror variables, required mirror secret names, the Actions PR-creation permission, and optional Feishu IM / OpenClaw entries without exposing secret values
- enable Actions PR creation on the mirror repo, otherwise `feishu-start-review.yml` pushes the review branch but the PR step fails with `403 "GitHub Actions is not permitted to create or approve pull requests."` — the workflow already declares `pull-requests: write`, but the account/repo toggle `can_approve_pull_request_reviews` must also be on. Turn it on with `gh api -X PUT /repos/Bingboom/Hello-Docs/actions/permissions/workflow -f default_workflow_permissions=read -F can_approve_pull_request_reviews=true` (the audit reports this as `Mirror Actions PR-creation permission`)
- before unpausing `Bingboom/Hello-Docs`, configure its own repository secrets for the remote Feishu workers: `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_PHASE2_BASE_TOKEN`, `FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID`, `FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID`, `FEISHU_PHASE2_SPEC_ROWS_SOURCE_VIEW_ID`, `FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_TABLE_ID`, `FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_VIEW_ID`, `FEISHU_PHASE2_SPEC_FOOTNOTES_TABLE_ID`, `FEISHU_PHASE2_SPEC_FOOTNOTES_VIEW_ID`, `FEISHU_PHASE2_SPEC_NOTES_TABLE_ID`, `FEISHU_PHASE2_SPEC_NOTES_VIEW_ID`, `FEISHU_TRANSLATION_MEMORY_BASE_TOKEN`, `FEISHU_TRANSLATION_MEMORY_TABLE_ID`, `FEISHU_TRANSLATION_MEMORY_VIEW_ID`, `FEISHU_PHASE2_SYMBOLS_BLOCKS_TABLE_ID`, `FEISHU_PHASE2_SYMBOLS_BLOCKS_VIEW_ID`, `FEISHU_PHASE2_LCD_ICONS_TABLE_ID`, `FEISHU_PHASE2_LCD_ICONS_VIEW_ID`, `FEISHU_PHASE2_TROUBLESHOOTING_TABLE_ID`, `FEISHU_PHASE2_TROUBLESHOOTING_VIEW_ID`, `FEISHU_PHASE2_VARIABLE_DEFAULTS_TABLE_ID`, `FEISHU_PHASE2_VARIABLE_DEFAULTS_VIEW_ID`, `FEISHU_PHASE2_VARIABLE_LANG_OVERRIDES_TABLE_ID`, `FEISHU_PHASE2_VARIABLE_LANG_OVERRIDES_VIEW_ID`, `FEISHU_PHASE2_MANUAL_COPY_SOURCE_TABLE_ID`, `FEISHU_PHASE2_MANUAL_COPY_SOURCE_VIEW_ID`, `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID`, and `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID`; add `FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN` only when the mirror should force a specific wiki parent
- configure optional mirror-only repository secrets as needed: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` for publish HTML deploys; DingTalk secrets plus `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session` only if the mirror should also sync DingTalk artifacts; Feishu IM adapter secrets such as `FEISHU_IM_APP_ID`, `FEISHU_IM_APP_SECRET`, `FEISHU_IM_VERIFICATION_TOKEN`, `FEISHU_IM_ENCRYPT_KEY`, optional `FEISHU_MANUAL_INDEX_BASE_TOKEN`, and `CLOUDFLARED_TUNNEL_TOKEN` only if that adapter is deployed for the mirror
- when OpenClaw dispatches into the mirror, point the OpenClaw runtime or gateway environment at `Bingboom/Hello-Docs` through `AUTO_MANUAL_GITHUB_REPO_OWNER=Bingboom` and `AUTO_MANUAL_GITHUB_REPO_NAME=Hello-Docs` or by running it from a `Hello-Docs` checkout; use the new Feishu app values for `FEISHU_IM_APP_ID` / `FEISHU_IM_APP_SECRET` when the Feishu IM adapter is deployed for the mirror, and keep the OpenClaw plugin GitHub token in the OpenClaw plugin config or runtime environment because repository secrets are not readable by a local gateway unless explicitly exported

Phase2 snapshot rule:

- keep the shared config families, but use a valid generated [`../data/phase2/`](../../data/phase2) snapshot as the default build/review/publish source when it exists
- `data/phase2/` is gitignored local snapshot output; mirror repositories should sync their own Feishu Base into this path instead of committing tenant-specific CSVs or attachments
- the one exception is [`../data/phase2/page_registry.csv`](../../data/phase2/page_registry.csv): it is the repo-maintained page-structure input that `sync-data` copies into the snapshot, so it stays tracked; without it a fresh checkout (including the CI cred health check) cannot sync at all
- [`../tests/fixtures/phase2`](../../tests/fixtures/phase2) is the committed CI/test fixture snapshot; do not treat it as a live authoring source or mirror-specific Base export
- the automatic phase2 default requires a complete manifest-backed core snapshot: `spec_master`, `spec_footnotes`, `spec_notes`, `symbols_blocks`, `troubleshooting`, `lcd_icons`, `variable_defaults`, `variable_lang_overrides`, and `manual_copy_source` must all appear as requested/synced tables in `snapshot_manifest.json`; derived `row_key_mapping`, `spec_titles.csv`, `Localized_Copy.csv`, and `Status_Words.csv` must also be recorded; partial `sync-data --table ...` runs are allowed, but they are treated as explicit experiment snapshots unless you pass them through `--data-root`
- explicit `--data-root` still overrides the default, so you can point `rst`, `check`, `diff-report`, `release-manifest`, `publish`, and `process-build-queue` at a different root when needed
- `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2` is still the explicit refresh step for the phase2 snapshot
- static legal/support placeholders such as `WARRANTY_EMAIL` and `LEGAL_COMPANY_NAME` are injected from `build.rst_substitutions` in the active config; keep US values in US configs and override EU / pt-BR values there instead of hardcoding region-specific names in shared templates
- for the review-init worker, use an isolated snapshot root such as `.tmp/review-start/phase2`; the worker syncs fresh data there before it seeds `docs/_review`
- `python scripts/local_build.py check|diff-report|release-manifest|publish ...` keeps generated verification/build outputs under `.tmp/staging/docs/_build`, `.tmp/staging/reports/version_tracking`, and `.tmp/staging/reports/releases` without making the operator remember `--staging-root`
- `review` still writes the real repo `docs/_review` tree and does not accept `--staging-root`, so it is intentionally excluded from `local_build.py`
- [`../data/phase2/page_registry.csv`](../../data/phase2/page_registry.csv) remains repo-maintained; `sync-data` copies it into isolated `--data-root` snapshots such as `.tmp/review-start/phase2` so runtime builds use the same page registry there
- page selection/applicability and [`../data/layout_params.csv`](../../data/layout_params.csv) remain repo-maintained inputs

Only create a new config when one of these really changes:

- page stack
- template family
- output convention
- language family
- Word reference template
