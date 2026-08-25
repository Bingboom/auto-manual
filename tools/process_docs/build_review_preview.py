from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=2)

from tools.utils.path_utils import Paths, PathSegments
from tools.build_docs import load_config
from tools.process_docs.build_review_preview_data import (
    build_change_workbook,
    build_downloads_metadata,
    copy_report_csvs,
    copy_report_set,
    copy_tree,
    latest_report_prefix,
    locate_latest_docx,
    read_json_if_exists,
    write_json,
)
from tools.process_docs.build_review_preview_pages import (
    render_changes_home_html,
    render_family_changes_html,
    render_model_changes_html,
    render_redirect_html,
    render_workspace_html,
)
from tools.process_docs.build_review_preview_postprocess import (
    assert_preview_output_contract as _assert_preview_output_contract,
    rewrite_manual_switcher_links as _rewrite_manual_switcher_links,
    rewrite_manual_tree_for_preview as _rewrite_manual_tree_for_preview,
)
from tools.process_docs.build_review_preview_render import (
    derive_product_name,
    display_text,
    format_generated_at,
    preview_language_label,
    workspace_title,
)
from tools.process_docs.build_review_preview_workspace import (
    assemble_family_payloads,
    build_target_specs,
    build_workspace_documents,
    export_workspace_targets,
    write_workspace_outputs,
)
from tools.process_docs.build_review_preview_targets import (
    FAMILY_ORDER,
    WORKSPACE_TARGET_TEMPLATES,
    ReviewAvailability,
    WorkspaceTarget,
    WorkspaceTargetTemplate,
    build_diff_command,
    build_export_command,
    build_spec_for_target,
    collect_review_availability,
    collect_workspace_target_candidates,
    default_family_config_for_region,
    diff_config_for_family,
    discover_workspace_targets,
    html_root_for_target,
    output_root_for_target,
    path_for_display,
    registered_workspace_targets_for_model,
    requested_workspace_target,
    resolve_preview_target_config_path,
    resolve_path,
    resolved_primary_config_path,
    target_has_review_bundle,
    target_sort_key,
    tracked_root_for_target,
)


REQUIRED_CHANGE_REPORT_FILES = (
    "report-index.html",
    "report-summary.html",
    "report-fields.html",
    "report-pages.html",
    "report-files.html",
)
REQUIRED_DOWNLOAD_CSVS = (
    "changes-summary.csv",
    "changes-pages.csv",
    "changes-fields.csv",
    "changes-files.csv",
)
REQUIRED_PREVIEW_FILES = (
    "index.html",
    "manual/index.html",
    "changes/index.html",
    "generated/meta.json",
    "generated/changes.json",
    "generated/workspace.json",
)

# Keep the facade's stable import/patch surface explicit. Tests and sibling
# entry scripts still import helpers from this module while the implementation
# lives in narrower helper modules.
__all__ = [
    "FAMILY_ORDER",
    "REQUIRED_CHANGE_REPORT_FILES",
    "REQUIRED_DOWNLOAD_CSVS",
    "REQUIRED_PREVIEW_FILES",
    "ReviewAvailability",
    "WORKSPACE_TARGET_TEMPLATES",
    "WorkspaceTarget",
    "WorkspaceTargetTemplate",
    "assert_preview_output_contract",
    "build_change_workbook",
    "build_diff_command",
    "build_downloads_metadata",
    "build_export_command",
    "build_spec_for_target",
    "capture",
    "classify_changes",
    "collect_changed_files",
    "collect_review_availability",
    "collect_workspace_target_candidates",
    "copy_report_csvs",
    "copy_report_set",
    "copy_tree",
    "default_family_config_for_region",
    "derive_product_name",
    "diff_config_for_family",
    "discover_workspace_targets",
    "display_text",
    "format_generated_at",
    "git_value",
    "html_root_for_target",
    "latest_report_prefix",
    "locate_latest_docx",
    "main",
    "output_root_for_target",
    "parse_args",
    "path_for_display",
    "preview_language_label",
    "read_json_if_exists",
    "registered_workspace_targets_for_model",
    "render_changes_home_html",
    "render_family_changes_html",
    "render_model_changes_html",
    "render_redirect_html",
    "render_workspace_html",
    "requested_workspace_target",
    "resolve_preview_request_args",
    "resolve_preview_target_config_path",
    "resolve_path",
    "resolved_primary_config_path",
    "review_pages_for_family",
    "rewrite_manual_switcher_links",
    "rewrite_manual_tree_for_preview",
    "run",
    "target_has_review_bundle",
    "target_sort_key",
    "tracked_root_for_target",
    "workspace_title",
    "write_json",
]

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Build the review handoff workspace package for Vercel or local sharing."
    )
    ap.add_argument(
        "--config",
        default=None,
        help="Primary family config YAML path. Defaults to the shared family config for --region.",
    )
    ap.add_argument(
        "--model",
        default=None,
        help="Target model. When omitted, infer it from the changed review bundle or existing review tree.",
    )
    ap.add_argument(
        "--region",
        default=None,
        help="Preferred default family. When omitted, infer it with --model.",
    )
    ap.add_argument(
        "--source",
        default="review",
        choices=("auto", "runtime", "review"),
        help="Bundle source passed to build.py html/word. Default keeps the workspace tied to review content.",
    )
    ap.add_argument(
        "--tracked-root",
        default=None,
        help="Tracked subtree for diff-report on the preferred family. Defaults to docs/_review/<model>/<region>.",
    )
    ap.add_argument(
        "--data-root",
        default=None,
        help="Structured data snapshot root passed through to build.py exports and diff-report.",
    )
    ap.add_argument("--from-ref", default="HEAD~1", help="Git from ref for diff-report.")
    ap.add_argument("--to-ref", default="HEAD", help="Git to ref for diff-report.")
    ap.add_argument(
        "--output-dir",
        default="site/review-preview/dist",
        help="Static site output directory, relative to repo root by default.",
    )
    ap.add_argument(
        "--clean-build",
        action="store_true",
        help="Allow the first export per family to clean its target output first.",
    )
    ap.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip build.py html exports and reuse existing HTML bundles.",
    )
    ap.add_argument(
        "--skip-diff",
        action="store_true",
        help="Skip diff-report generation and reuse the latest report set for each family.",
    )
    ap.add_argument(
        "--skip-word",
        action="store_true",
        help="Skip the optional Word export step.",
    )
    ap.add_argument(
        "--all-review-models",
        action="store_true",
        help="Include every existing docs/_review/<model>/ target in the workspace, plus the requested default target.",
    )
    return ap.parse_args()


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def capture(cmd: list[str]) -> str:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def git_value(env_name: str, fallback_cmd: list[str]) -> str:
    value = os.environ.get(env_name, "").strip()
    if value:
        return value
    return capture(fallback_cmd)


def collect_changed_files(from_ref: str, to_ref: str) -> list[str]:
    raw = capture(["git", "diff", "--name-only", "--diff-filter=ACMRT", from_ref, to_ref])
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _changed_review_coordinates(changed_files: list[str]) -> list[tuple[str, str]]:
    coordinates: set[tuple[str, str]] = set()
    for file_name in changed_files:
        parts = Path(file_name).parts
        if len(parts) >= 4 and parts[:2] == (PathSegments.DOCS, PathSegments.REVIEW):
            coordinates.add((parts[2], parts[3].upper()))
    return sorted(coordinates)


def _existing_review_coordinates(docs_dir: Path) -> list[tuple[str, str]]:
    review_root = docs_dir / PathSegments.REVIEW
    if not review_root.exists():
        return []
    coordinates: list[tuple[str, str]] = []
    for model_dir in sorted(path for path in review_root.iterdir() if path.is_dir()):
        for family_dir in sorted(path for path in model_dir.iterdir() if path.is_dir()):
            if resolve_preview_target_config_path(
                model=model_dir.name,
                family=family_dir.name,
                language=None,
            ) is not None:
                coordinates.append((model_dir.name, family_dir.name.upper()))
    return coordinates


def _is_cn_runtime_change(file_name: str) -> bool:
    return file_name in {"configs/config.zh.yaml", "docs/manifests/manual_zh.yaml"} or file_name.startswith(
        ("docs/templates/page_zh/", "docs/templates/recipes/zh/")
    )


def resolve_preview_request_args(
    args: argparse.Namespace,
    *,
    changed_files: list[str],
    docs_dir: Path,
) -> argparse.Namespace:
    model = str(getattr(args, "model", "") or "").strip()
    region = str(getattr(args, "region", "") or "").strip().upper()
    if bool(model) != bool(region):
        raise RuntimeError("Review preview requires --model and --region together when either is explicit.")
    if model and region:
        args.model = model
        args.region = region
        return args

    changed_coordinates = _changed_review_coordinates(changed_files)
    if changed_coordinates:
        args.model, args.region = changed_coordinates[0]
        return args

    if any(_is_cn_runtime_change(file_name) for file_name in changed_files):
        config_path = resolve_path(default_family_config_for_region("CN"))
        cfg = load_config(config_path)
        build_cfg_raw = cfg.get("build", {})
        build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
        args.model = str(build_cfg.get("default_model") or "").strip()
        args.region = str(build_cfg.get("default_region") or "CN").strip().upper()
        args.config = path_for_display(config_path)
        args.source = "runtime"
        if not args.model:
            raise RuntimeError(f"Review preview config is missing build.default_model: {config_path}")
        return args

    existing_coordinates = _existing_review_coordinates(docs_dir)
    if existing_coordinates:
        args.model, args.region = existing_coordinates[0]
        return args
    raise FileNotFoundError("Review preview could not infer a target from the diff or docs/_review/.")


def classify_changes(changed_files: list[str], model: str, region: str) -> list[dict[str, object]]:
    review_prefix = f"{PathSegments.DOCS}/{PathSegments.REVIEW}/{model}/{region}/"
    groups = [
        ("Review Bundle", lambda p: p.startswith(review_prefix)),
        ("Shared Templates", lambda p: p.startswith("docs/templates/")),
        ("Structured Data", lambda p: p.startswith("data/phase2/")),
        ("Automation And Build", lambda p: p == "build.py" or p.startswith("tools/") or p.startswith(".github/workflows/")),
        ("Maintainer Docs", lambda p: p == "README.md" or p.startswith("code-as-doc/") or p.startswith("user-guide/")),
    ]
    areas: list[dict[str, object]] = []
    assigned: set[str] = set()
    for name, matcher in groups:
        files = [path for path in changed_files if matcher(path)]
        if files:
            assigned.update(files)
            areas.append({"name": name, "files": files})
    other = [path for path in changed_files if path not in assigned]
    if other:
        areas.append({"name": "Other", "files": other})
    return areas


def review_pages_for_family(changed_files: list[str], model: str, family: str) -> list[str]:
    prefix = f"{PathSegments.DOCS}/{PathSegments.REVIEW}/{model}/{family}/"
    return [
        path.removeprefix(prefix)
        for path in changed_files
        if path.startswith(f"{prefix}page/") or path.startswith(f"{prefix}generated/")
    ]


def rewrite_manual_switcher_links(
    text: str,
    *,
    model: str | None = None,
    current_target: WorkspaceTarget,
    current_relative_path: Path,
    all_targets: list[WorkspaceTarget],
) -> str:
    return _rewrite_manual_switcher_links(
        text,
        current_target=current_target,
        current_relative_path=current_relative_path,
        all_targets=all_targets,
        html_root_for_target_func=html_root_for_target,
    )


def rewrite_manual_tree_for_preview(
    manual_dir: Path,
    *,
    current_target: WorkspaceTarget,
    all_targets: list[WorkspaceTarget],
) -> None:
    _rewrite_manual_tree_for_preview(
        manual_dir,
        current_target=current_target,
        all_targets=all_targets,
        rewrite_manual_switcher_links_func=rewrite_manual_switcher_links,
    )


def assert_preview_output_contract(output_dir: Path, workspace: dict[str, object], *, require_word: bool) -> None:
    _assert_preview_output_contract(
        output_dir,
        workspace,
        require_word=require_word,
        required_preview_files=REQUIRED_PREVIEW_FILES,
        required_download_csvs=REQUIRED_DOWNLOAD_CSVS,
        required_change_report_files=REQUIRED_CHANGE_REPORT_FILES,
    )


def main() -> int:
    args = parse_args()
    output_dir = resolve_path(args.output_dir)
    changed_files = collect_changed_files(args.from_ref, args.to_ref)
    docs_dir = Paths(root=ROOT).docs_dir
    resolve_preview_request_args(args, changed_files=changed_files, docs_dir=docs_dir)
    requested_target = requested_workspace_target(args)
    workspace_target_candidates = collect_workspace_target_candidates(args, requested_target=requested_target)
    review_availability = collect_review_availability(
        docs_dir=docs_dir,
        targets=workspace_target_candidates,
    )
    workspace_targets = discover_workspace_targets(
        args,
        requested_target=requested_target,
        review_availability=review_availability,
        docs_dir=docs_dir,
    )

    if not workspace_targets:
        if args.source == "review" and args.all_review_models:
            raise FileNotFoundError("No review preview targets are available under docs/_review/.")
        if args.source == "review":
            raise FileNotFoundError(f"No review preview targets are available under docs/_review/{args.model}/.")
        raise RuntimeError("No workspace families were resolved for the review preview build.")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    manual_root = output_dir / "manual"
    changes_root = output_dir / "changes"
    downloads_root = output_dir / "downloads"
    generated_dir = output_dir / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_workspace_targets = list(workspace_targets)
    target_specs = build_target_specs(
        args,
        workspace_targets,
        requested_target=requested_target,
        review_availability=review_availability,
        docs_dir=docs_dir,
    )
    export_workspace_targets(
        args,
        workspace_targets,
        target_specs=target_specs,
        run_command=run,
    )
    families_payload, changes_by_family = assemble_family_payloads(
        args,
        workspace_targets,
        all_workspace_targets=all_workspace_targets,
        target_specs=target_specs,
        root=ROOT,
        changed_files=changed_files,
        manual_root=manual_root,
        changes_root=changes_root,
        downloads_root=downloads_root,
        run_command=run,
        rewrite_manual_tree_for_preview_func=rewrite_manual_tree_for_preview,
        classify_changes_func=classify_changes,
        review_pages_for_family_func=review_pages_for_family,
    )
    meta, workspace, changes, default_manual_url = build_workspace_documents(
        args,
        families_payload,
        changes_by_family,
        requested_target=requested_target,
        git_value_func=git_value,
    )
    write_workspace_outputs(
        output_dir,
        manual_root=manual_root,
        changes_root=changes_root,
        generated_dir=generated_dir,
        meta=meta,
        workspace=workspace,
        changes=changes,
        families_payload=families_payload,
        default_manual_url=default_manual_url,
    )

    assert_preview_output_contract(
        output_dir,
        workspace,
        require_word=not args.skip_word,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
