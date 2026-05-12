from __future__ import annotations

import argparse


def parse_args(
    argv: list[str] | None = None,
    *,
    default_config: str,
    build_actions: tuple[str, ...],
    staging_root_env: str,
) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Cross-platform build entrypoint for Auto-Manual.",
    )
    ap.add_argument(
        "action",
        choices=(
            "validate",
            "doctor",
            *build_actions,
            "review",
            "check",
            "sync-review",
            "sync-data",
            "translation-memory",
            "queue-query",
            "queue-resolve-action",
            "queue-execute",
            "process-review-start-queue",
            "process-build-queue",
            "listen-build-queue",
            "listen-message-control",
            "publish",
            "clean",
            "diff-report",
            "release-manifest",
            "preview",
            "fast",
            "message-control-dry-run",
        ),
        help="Action to run",
    )
    ap.add_argument("--config", default=default_config, help="Config YAML path, relative to repo root by default")
    ap.add_argument("--model", default=None, help="Build a single model instead of build.targets")
    ap.add_argument("--region", default=None, help="Build a single region instead of build.targets")
    ap.add_argument(
        "--lang",
        default=None,
        help="Optional language selector for translation-memory, queue-query, queue-resolve-action, message-control-dry-run, or other target-aware flows",
    )
    ap.add_argument(
        "--staging-root",
        default=None,
        help=f"Isolate generated verification/build outputs under this root (or set {staging_root_env})",
    )
    ap.add_argument(
        "--source",
        choices=("auto", "runtime", "review"),
        default="auto",
        help="Content source for build actions: auto, runtime, or review",
    )
    ap.add_argument("--data-root", default=None, help="Override structured content snapshot root")
    ap.add_argument("--pdf-mode", choices=("latex", "word"), default=None, help="Override PDF backend")
    ap.add_argument("--open", action="store_true", help="Allow opening generated artifacts after build")
    ap.add_argument("--no-clean", action="store_true", help="Skip cleaning current target outputs before build")
    ap.add_argument(
        "--skip-root-index",
        action="store_true",
        help="Do not rewrite docs/index.rst when materializing the target bundle",
    )
    ap.add_argument(
        "--refresh-review",
        action="store_true",
        help="Refresh an existing review bundle from the runtime template/data output",
    )
    ap.add_argument(
        "--sync-scope",
        choices=("generated", "params"),
        default="params",
        help="For sync-review: generated = generated csv/draft pages only; params = generated plus parameter-driven page refresh without resetting manual review prose",
    )
    ap.add_argument(
        "--page-file",
        action="append",
        default=[],
        help="For sync-review: extra review page file name to sync from runtime/page",
    )
    ap.add_argument("--page", default=None, help="For preview: exact page selector to materialize")
    ap.add_argument("--tracked-root", default=None, help="Tracked subtree for diff-report")
    ap.add_argument("--from-ref", default="HEAD~1", help="Git from ref for diff-report")
    ap.add_argument("--to-ref", default="HEAD", help="Git to ref for diff-report")
    ap.set_defaults(ignore_initial_adds=True)
    ap.add_argument(
        "--ignore-initial-adds",
        dest="ignore_initial_adds",
        action="store_true",
        help="Ignore initial all-Added rows when the tracked subtree is first introduced (default for diff-report)",
    )
    ap.add_argument(
        "--include-initial-adds",
        dest="ignore_initial_adds",
        action="store_false",
        help="Include initial all-Added rows when the tracked subtree is first introduced",
    )
    ap.add_argument(
        "--report-dir",
        default=None,
        help="Output directory for diff-report CSV/HTML",
    )
    ap.add_argument("--table", action="append", default=[], help="For sync-data or translation-memory: logical table id")
    ap.add_argument("--section", default=None, help="For translation-memory: exact section/title filter")
    ap.add_argument("--row-key", default=None, help="For translation-memory: exact Row_key filter")
    ap.add_argument("--message", default=None, help="For message-control-dry-run: raw incoming user message")
    ap.add_argument(
        "--document-id",
        default=None,
        help="For queue-query, queue-resolve-action, or message-control-dry-run: exact Document_ID filter or hint",
    )
    ap.add_argument(
        "--task-id",
        default=None,
        help="For queue-query or queue-resolve-action: exact Task_id filter, usually Document_ID plus Workflow_action",
    )
    ap.add_argument(
        "--task-id-prefix",
        default=None,
        help="For queue-query or queue-resolve-action: Task_id prefix filter, useful for bounded batch asks such as one model/market",
    )
    ap.add_argument(
        "--document-key",
        default=None,
        help="For queue-query, queue-resolve-action, or message-control-dry-run: exact Document_Key filter or hint",
    )
    ap.add_argument(
        "--build-family",
        default=None,
        help="For queue-query, queue-resolve-action, process-build-queue, or message-control-dry-run: exact Build_family filter or hint",
    )
    ap.add_argument("--git-ref", default=None, help="For message-control-dry-run: explicit Git_ref hint")
    ap.add_argument("--version", default=None, help="For message-control-dry-run: explicit version hint")
    ap.add_argument("--confirmed", action="store_true", help="For message-control-dry-run: confirm publish intent")
    ap.add_argument(
        "--queue-scope",
        choices=("document-link", "review-init", "all"),
        default="all",
        help="For queue-query or queue-resolve-action: which Feishu queue surface to search",
    )
    ap.add_argument(
        "--query-text",
        default=None,
        help="For queue-query or queue-resolve-action: raw natural-language text to parse with document_id-first resolution",
    )
    ap.add_argument(
        "--langs",
        default=None,
        help="For queue-query or queue-resolve-action: comma-separated language filters, such as en,fr",
    )
    ap.add_argument(
        "--fresh-since",
        default=None,
        help="For queue-query, queue-resolve-action, or queue-execute: mark writeback results fresh only after this ISO time or epoch",
    )
    ap.add_argument("--document-version", default=None, help="For queue-query or queue-resolve-action: exact Version filter")
    ap.add_argument(
        "--market-group",
        default=None,
        help="For queue-query or queue-resolve-action: exact Market_Group/Market filter, such as EU or US",
    )
    ap.add_argument(
        "--query-workflow-action",
        default=None,
        help="For queue-query or queue-resolve-action: start-review | build-draft-package | publish",
    )
    ap.add_argument("--git-ref-contains", default=None, help="For queue-query or queue-resolve-action: substring match against Git_ref")
    ap.add_argument("--result-contains", default=None, help="For queue-query or queue-resolve-action: substring match against 构建结果")
    ap.add_argument(
        "--latest-per-document-key",
        action="store_true",
        help="For queue-query or queue-resolve-action: collapse Document_link rows to the latest version per Document_Key",
    )
    ap.add_argument(
        "--allow-multiple",
        action="store_true",
        help="For queue-resolve-action: allow natural-language batch actions when multiple queue rows match",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=10,
        help="For translation-memory, queue-query, or queue-resolve-action: maximum rows to return",
    )
    ap.add_argument("--json", action="store_true", help="For queue-query or queue-resolve-action: emit machine-readable JSON")
    ap.set_defaults(wait_for_completion=True)
    ap.add_argument(
        "--no-wait",
        dest="wait_for_completion",
        action="store_false",
        help="For queue-execute: return after workflow dispatch without waiting for GitHub completion",
    )
    ap.add_argument(
        "--wait-timeout-seconds",
        type=int,
        default=420,
        help="For queue-execute: maximum time to wait for GitHub workflow completion",
    )
    ap.add_argument(
        "--status-poll-seconds",
        type=float,
        default=3.0,
        help="For queue-execute: polling interval while waiting for GitHub workflow completion",
    )
    ap.add_argument(
        "--confirm-publish",
        action="store_true",
        help="For queue-execute: explicitly confirm Publish dispatches after row resolution",
    )
    ap.add_argument(
        "--workflow-action",
        choices=("build-draft-package", "publish"),
        default=None,
        help="For process-build-queue: only consume one normalized Workflow_action (Build Draft Package or Publish)",
    )
    ap.add_argument(
        "--doc-phase",
        choices=("draft", "publish"),
        default=None,
        help="Unsupported legacy alias; use --workflow-action and keep queue rows on Workflow_action only",
    )
    ap.add_argument(
        "--record-id",
        default=None,
        help="For process-build-queue or process-review-start-queue: only consume one table record_id",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="For sync-data, process-build-queue, or process-review-start-queue: validate/report without writing files",
    )
    ap.add_argument(
        "--refresh-data",
        action="store_true",
        help="For process-build-queue: sync the latest phase2 snapshot before building each queue group",
    )
    return ap.parse_args(argv)
