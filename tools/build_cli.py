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
            "process-review-start-queue",
            "process-build-queue",
            "listen-build-queue",
            "publish",
            "clean",
            "diff-report",
            "release-manifest",
            "preview",
            "fast",
        ),
        help="Action to run",
    )
    ap.add_argument("--config", default=default_config, help="Config YAML path, relative to repo root by default")
    ap.add_argument("--model", default=None, help="Build a single model instead of build.targets")
    ap.add_argument("--region", default=None, help="Build a single region instead of build.targets")
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
    ap.add_argument("--table", action="append", default=[], help="For sync-data: logical table id to sync")
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
        help="Deprecated compatibility alias for --workflow-action",
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
    return ap.parse_args(argv)
