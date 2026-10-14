# Orchestration module map: build entrypoint modules (§2)

Status: active · Part of the [orchestration module map](../orchestration_module_map.md); its index lists the other
module families. Update this page in the same PR that moves a boundary here; do not add
module notes to the hub.

## 2. Build Entrypoint Modules

[`tools/rtd/publication_catalog.py`](../../../tools/rtd/publication_catalog.py) groups
frozen publication metadata for the portal; it is a read model, not a source of
content. [Language navigation](../rtd_locale_navigation.md) stays in the Web adapter.

[`tools/publish_locale_identity.py`](../../../tools/publish_locale_identity.py)
owns locale identity/stored-source migration; publish assembly owns candidate
transactions and RTD redirects. See [contract](../web_locale_publication_identity.md).

Read-only release artifact preflight lives in
[`tools/manual_operations_health.py`](../../../tools/manual_operations_health.py);
it neither probes deployment nor collects visitor metrics.
[`tools/manual_operations_online_health.py`](../../../tools/manual_operations_online_health.py)
reuses frozen portal discovery for bounded same-origin HTTPS HEAD checks.
HTTP accessibility is separate from deployment identity and translation coverage;
see [online check scope](../manual_operations_online_health.md).

[`tools/rtd/deployment_receipt.py`](../../../tools/rtd/deployment_receipt.py) owns
the frozen-source fingerprint, Sphinx build-finished output receipt and bounded
read-only served HTML/resource hash verification. `rtd_portal.setup` registers
its callback; queue, publication assembly and link writers are not callers.
See the [Git-only receipt contract](../rtd_deployment_receipt.md).

[`tools/rtd/product_learning.py`](../../../tools/rtd/product_learning.py) binds the
product knowledge list to actual published manual identities.
[`tools/rtd/market_policy.py`](../../../tools/rtd/market_policy.py) reads and validates
the business-owned policy snapshot; the portal renders its list and copies source
images. Neither module calls Feishu or runs publication. See
[knowledge and policy pages](../rtd_manual_portal.md#产品知识本地预览).

[`tools/manual_knowledge/`](../../../tools/manual_knowledge/) owns the rendered EU
manual reading model: semantic HTML/table extraction and the bounded JSON export.
`rtd_portal` runs its writer after HTML and before the deployment receipt.
The existing [OpenClaw control plugin](../../../integrations/openclaw/auto-manual-control-layer/)
owns receipt verification, search and paginated evidence reads; it does not call
build/publish workers for a query. See [EU query contract](../eu_manual_query.md).

[`tools/rtd/workspace_revision.py`](../../../tools/rtd/workspace_revision.py) owns only
the system page's checkout identity and successful-build version receipt.
`rtd_portal` supplies that context and registers the writer before the deployment
receipt. Browser refresh probes the served same-origin receipt; it neither queries
GitHub nor changes publication/source authority. See
[published workspace version](../rtd_manual_portal/system-workspace.md#published-version-and-refresh).

[`tools/rtd/system_evolution.py`](../../../tools/rtd/system_evolution.py) owns the
system page's read-only evolution summary. It reads the marked public story
from the architecture history registered in `source_registry.yaml`;
`system_workspace` supplies its view and authoring findings, while the existing
shell owns tab navigation. It neither writes history nor infers execution status.
See [system workspace](../rtd_manual_portal/system-workspace.md#system-workspace-page).

[`tools/rtd/design_system.py`](../../../tools/rtd/design_system.py) owns the
read-only 设计规范 page context and its build-finished writer. Each reader
covers one source:

- [`design_system_css.py`](../../../tools/rtd/design_system_css.py) reads the live
  `web_manual.css`, assembled exactly as `tools/web/stylesheets.py` does.
- [`design_assets.py`](../../../tools/rtd/design_assets.py) lists the shared asset
  manifests and folders.
- [`design_print.py`](../../../tools/rtd/design_print.py) reads
  `data/layout_params.csv` through `tools.render_contract`.

[`design_content.py`](../../../tools/rtd/design_content.py) holds the committed
notes loader and the shared error. `rtd_portal` only registers the page and the
writer. Nothing here writes a stylesheet, an asset, a manifest or the token
table. See [design system page](../rtd_manual_portal/knowledge-pages.md#design-system-page).

[`tools/rtd/system_data.py`](../../../tools/rtd/system_data.py) owns the read-only
系统数据 page context: it reads the publish manifest, the capability, language
and asset CSVs, the review page counts and the line counts of the files
`git ls-files` lists, and hands the rows to the page as
JSON for `_static/system-data.js` to filter. `rtd_portal` only registers the
page. See [system data page](../rtd_manual_portal/knowledge-pages.md#system-data-page).

[`tools/rtd/product_matrix.py`](../../../tools/rtd/product_matrix.py) owns the
read-only 产品矩阵 page context: it reads the publish manifest, the spec table
of each model's published manual, the catalog names and navigation groups, the
capability CSV and the curated `tools/rtd_portal_assets/product_matrix.json`.
`rtd_portal` only registers the page. See
[product matrix page](../rtd_manual_portal/knowledge-pages.md#product-matrix-page).

Internal frozen Web language projection lives in
[`tools/web/language_bundle.py`](../../../tools/web/language_bundle.py); it projects
explicit source language before rendering, not by slicing generated HTML.
`build_docs_export` selects this path only for Web plus an explicit language;
`build_docs_bundle.prepare_web_language_source_bundle` preserves complete source
scope, then the projection helper replaces canonical RST for check/Markdown/HTML.
See [scope and integration boundary](../web_language_projection.md).

[`tools/web/language_release_evidence.py`](../../../tools/web/language_release_evidence.py)
owns capture, sealing and shared verification of language release evidence.
Queue execution records the three successful actions; staging seals the
immutable candidate, and metadata/assembly/stored replay verify at their own
boundaries. See [receipt and acceptance limits](../web_language_release_evidence.md).

Optional manual feedback affordances are kept in
[`tools/rtd/feedback.py`](../../../tools/rtd/feedback.py). It validates fixed
HTTPS channel configuration and renders only local copyable context from the
frozen publication identity; an empty channel list produces no markup.

Product suggestion HTML and endpoint validation live in
[`tools/rtd/product_voc.py`](../../../tools/rtd/product_voc.py). The append-only
receiver and fixed bot adapter are isolated under
[`integrations/product_voc/`](../../../integrations/product_voc/); neither the build
nor frozen publication assembly performs a live write.
The manual Mac lifecycle wrapper is `scripts/voc_mac_receiver.py`; optional
post-intake analysis lives in `integrations/product_voc/openclaw_handoff.py`.
It uses the designated local `main` agent in a separate VOC session and produces
local review candidates. See [VOC](../product_voc.md).

Optional visit analytics lives in
[`tools/rtd/analytics.py`](../../../tools/rtd/analytics.py). It validates the
fixed-shape Cloudflare Web Analytics beacon token and renders the beacon
script tag; an empty token keeps every page byte-identical to the
analytics-free output.

Derived page head metadata lives in
[`tools/rtd/page_metadata.py`](../../../tools/rtd/page_metadata.py). It builds
title/description/canonical/hreflang/OG strictly from the frozen publication
identity plus the validated `site_base_url` origin; an empty origin omits
every absolute URL.

Root-alias entry behavior lives in
[`tools/rtd/alias_entry.py`](../../../tools/rtd/alias_entry.py). It maps alias
page names to nested canonical routes, emits their noindex/canonical head,
and swaps the generated instant forward for a beacon send window only when
analytics is configured; unknown alias shapes pass through unchanged.

[`build.py`](../../../build.py) should stay thin and delegate to these helper modules:

- [`tools/build_main.py`](../../../tools/build_main.py)
  - CLI bootstrap and top-level error boundary for `build.py`
- [`tools/local_env.py`](../../../tools/local_env.py)
  - loads `~/.auto-manual-phase2.env` into the environment at startup (non-overriding, no-op when absent); called once by `build_main.run_main` so `sync-data`/review run without a manual `source`
- [`tools/build_cli.py`](../../../tools/build_cli.py)
  - argument parsing
- [`tools/build_dispatch.py`](../../../tools/build_dispatch.py)
  - registered top-level action routing for explicit non-build actions
  - fallback routing for standard build actions such as `rst`, `word`, `pdf`, `preview`, and `fast`
- [`tools/build_paths.py`](../../../tools/build_paths.py)
  - config loading
  - config-driven docs_dir / layout-params resolution
  - staging-root resolution (CLI arg / env coupling)
  - review/build/release root selection
  - thin adapter: delegates all path-segment construction to [`tools/utils/path_utils.py`](../../../tools/utils/path_utils.py)
- [`tools/utils/path_utils.py`](../../../tools/utils/path_utils.py)
  - single source of truth for repo-relative path segments (`PathSegments`)
  - repo-root-anchored and config-anchored `Paths`, plus `*_of(base)` suffix helpers
  - consumed by `build_paths.py` and path-building sites across `tools/`
- [`tools/build_entry_commands.py`](../../../tools/build_entry_commands.py)
  - CLI command assembly for build/check/review/sync/release/queue entrypoints
- [`tools/build_runtime.py`](../../../tools/build_runtime.py)
  - validate/check/pre-build runtime helpers
  - review auto-sync and cleanup helpers
- [`tools/build_reports.py`](../../../tools/build_reports.py)
  - diff-report target resolution
  - tracked-root/report-dir helpers
  - diff-report command assembly
- [`tools/build_publish.py`](../../../tools/build_publish.py)
  - deterministic publish orchestration over `check -> diff-report -> word -> pdf -> md -> release-manifest`
  - versioned publish enters the Git-commit-derived reproducibility environment before any release work
  - approved-reference targets keep every print renderer on the frozen `review-asis` source; other targets retain review parameter sync
- [`tools/build_doctor.py`](../../../tools/build_doctor.py)
  - environment and dependency diagnostics
  - doctor target/pdf/reference-doc resolution
  - doctor finding collection
- [`tools/env_preflight.py`](../../../tools/env_preflight.py)
  - advisory `env.python` / `env.lock` rows: running Python versus the `pyproject.toml` pin, installed packages versus `requirements.lock`
  - shared by `build.py doctor`, its own CLI, and the one-line-per-drift banner that `tests/__init__.py` prints before a test run; `OK`/`WARN` only, never blocking
- [`tools/asset_commands.py`](../../../tools/asset_commands.py)
  - single `build.py` command facade for `asset-check` and `asset-intake`
  - fail-closed validation of the public AI-intake argument contract
- [`tools/asset_registry.py`](../../../tools/asset_registry.py)
  - canonical asset-registry validation and target-scoped approved-export resolution
  - immutable CSV-byte parsing plus approved/temporary/missing/quarantined status contract
  - the export files each row names (`registered_exports`), resolved exactly as `asset-check` verifies them
- [`tools/asset_usage.py`](../../../tools/asset_usage.py)
  - target-bound `asset:` resolution, safe-format selection, frozen-byte staging, and legacy-path accounting
  - deterministic `asset_usage_manifest.json` plus exact `asset_registry_snapshot.csv` emission
- [`tools/contract_assets.py`](../../../tools/contract_assets.py)
  - shared legacy-path / `asset:` resolver used by both contract checking and bundle materialization
- [`tools/asset_rewrites.py`](../../../tools/asset_rewrites.py)
  - semantic `asset:` restoration from finalized-bundle rewrite provenance when review content is seeded or re-finalized
- [`tools/asset_intake.py`](../../../tools/asset_intake.py)
  - repo-root-aware adapter from public CLI arguments to the deterministic intake pipeline
- [`tools/asset_pipeline/recipe.py`](../../../tools/asset_pipeline/recipe.py)
  - strict recipe-schema parsing and extraction-contract validation
- [`tools/asset_pipeline/extract.py`](../../../tools/asset_pipeline/extract.py)
  - source inspection, private-marker checks, page normalization, previews, and semantic exports
- [`tools/asset_pipeline/package.py`](../../../tools/asset_pipeline/package.py)
  - private source snapshot, manifest/CSV assembly, deterministic ZIP, and atomic publication
- [`tools/asset_pipeline/models.py`](../../../tools/asset_pipeline/models.py)
  - immutable recipe, artifact, inspection, and intake-result contracts
- [`tools/asset_pipeline/base_inventory.py`](../../../tools/asset_pipeline/base_inventory.py)
  - read-only dry run staging the four Git production-art folders as `04_资产*` rows; never calls Feishu ([design](../asset_base_inventory.md))
  - identity from the shared manifests, registry paths and Web illustration manifests, plus a preview of the `sync-data` registry merge
- [`tools/asset_pipeline/base_reconcile.py`](../../../tools/asset_pipeline/base_reconcile.py)
  - reads a saved lark-cli snapshot of the three live tables and gives each staged row its action (create / keep / fill / update-file / propose)
  - reports Base-versus-repository disagreements (stale attachments, drifted or Base-only definitions) without overwriting either side
