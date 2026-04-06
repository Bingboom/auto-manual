from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=2)

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
    requested_workspace_target,
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


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Build the review handoff workspace package for Vercel or local sharing."
    )
    ap.add_argument(
        "--config",
        default=None,
        help="Primary family config YAML path. Defaults to the shared family config for --region.",
    )
    ap.add_argument("--model", required=True, help="Target model, for example JE-1000F.")
    ap.add_argument("--region", required=True, help="Preferred default family, for example US.")
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


def classify_changes(changed_files: list[str], model: str, region: str) -> list[dict[str, object]]:
    review_prefix = f"docs/_review/{model}/{region}/"
    groups = [
        ("Review Bundle", lambda p: p.startswith(review_prefix)),
        ("Shared Templates", lambda p: p.startswith("docs/templates/")),
        ("Structured Data", lambda p: p.startswith("data/phase1/") or p.startswith("data/phase2/")),
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
    prefix = f"docs/_review/{model}/{family}/"
    return [
        path.removeprefix(prefix)
        for path in changed_files
        if path.startswith(f"{prefix}page/") or path.startswith(f"{prefix}generated/")
    ]


def rewrite_manual_switcher_links(
    text: str,
    *,
    model: str,
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
    requested_target = requested_workspace_target(args)
    workspace_target_candidates = collect_workspace_target_candidates(args, requested_target=requested_target)
    review_availability = collect_review_availability(
        docs_dir=ROOT / "docs",
        targets=workspace_target_candidates,
    )
    workspace_targets = discover_workspace_targets(
        args,
        requested_target=requested_target,
        review_availability=review_availability,
        docs_dir=ROOT / "docs",
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

    families_payload: list[dict[str, object]] = []
    changes_by_family: dict[str, object] = {}
    all_workspace_targets = list(workspace_targets)
    target_specs = {
        target.label: build_spec_for_target(
            args,
            target,
            requested_target=requested_target,
            review_availability=review_availability,
            docs_dir=ROOT / "docs",
        )
        for target in workspace_targets
    }

    export_plan: list[tuple[str, WorkspaceTarget]] = []
    if not args.skip_build:
        export_plan.extend(("html", target) for target in workspace_targets)
    if not args.skip_word:
        export_plan.extend(("word", target) for target in workspace_targets)

    cleaned_output_roots: set[Path] = set()
    for action, target in export_plan:
        spec = target_specs[target.label]
        output_root = Path(spec["output_root"]).resolve()
        no_clean = (not args.clean_build) or (output_root in cleaned_output_roots)
        try:
            run(
                build_export_command(
                    action=action,
                    model=target.model,
                    config_path=Path(spec["config_path"]),
                    family=target.family,
                    source_mode=str(spec["source_mode"]),
                    no_clean=no_clean,
                )
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Review preview failed to build {action.upper()} for {target.label}.") from exc
        cleaned_output_roots.add(output_root)

    grouped_targets: dict[tuple[str, str], list[WorkspaceTarget]] = {}
    for target in workspace_targets:
        grouped_targets.setdefault((target.family, target.model), []).append(target)

    families_payload_by_name: dict[str, dict[str, object]] = {}
    for family, model in sorted(grouped_targets, key=lambda item: (FAMILY_ORDER.index(item[0]) if item[0] in FAMILY_ORDER else len(FAMILY_ORDER), item[1])):
        targets = sorted(grouped_targets[(family, model)], key=target_sort_key)
        representative = targets[0]
        tracked_root = tracked_root_for_target(args, representative)

        if not args.skip_diff:
            try:
                run(build_diff_command(args=args, target=representative, tracked_root=tracked_root))
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(f"Review preview failed to build the diff-report set for {model}/{family}.") from exc

        report_root = ROOT / "reports" / "version_tracking" / model / family
        prefix = latest_report_prefix(report_root)
        model_changes_dir = changes_root / family / model
        model_downloads_dir = downloads_root / family / model

        report_files = copy_report_set(
            report_root,
            prefix,
            model_changes_dir,
            relative_dir=f"changes/{family}/{model}",
        )
        csv_files = copy_report_csvs(
            report_root,
            prefix,
            model_downloads_dir,
            relative_dir=f"downloads/{family}/{model}",
        )
        workbook_path = build_change_workbook(
            model_downloads_dir,
            csv_files,
            relative_path=f"downloads/{family}/{model}/change-report.xlsx",
        )
        if workbook_path is None:
            raise RuntimeError(f"Review preview failed to build the required change workbook for {model}/{family}.")

        language_payloads: list[dict[str, object]] = []
        shared_language_labels: list[str] = []
        default_manual_url = ""
        default_lang = ""
        model_product_name = model
        model_manual_title = f"{model} User Manual"

        for target in targets:
            spec = target_specs[target.label]
            output_root = Path(spec["output_root"])
            html_root = output_root / "html"
            if not html_root.exists():
                raise FileNotFoundError(f"HTML output not found for {target.label}: {html_root}")

            manual_dest = manual_root / family / model / target.language
            copy_tree(html_root, manual_dest)
            rewrite_manual_tree_for_preview(
                manual_dest,
                current_target=target,
                all_targets=all_workspace_targets,
            )

            manual_meta = read_json_if_exists(html_root / "manual_meta.json")
            manual_title = display_text(manual_meta.get("title"), f"{model} User Manual")
            manual_lang = str(manual_meta.get("lang") or target.language).strip().lower() or target.language
            product_name = derive_product_name(manual_title, model)
            model_product_name = product_name
            model_manual_title = manual_title

            word_path: str | None = None
            if not args.skip_word:
                latest_docx = locate_latest_docx(output_root / "word")
                if latest_docx is None:
                    raise FileNotFoundError(
                        f"Review preview Word export finished but no DOCX was found for {target.label}."
                    )
                language_download_dir = downloads_root / family / model / target.language
                language_download_dir.mkdir(parents=True, exist_ok=True)
                copied_docx = language_download_dir / "review-manual.docx"
                shutil.copy2(latest_docx, copied_docx)
                word_path = f"downloads/{family}/{model}/{target.language}/review-manual.docx"

            language_label = preview_language_label(manual_lang)
            if language_label not in shared_language_labels:
                shared_language_labels.append(language_label)

            language_entry = {
                "lang": manual_lang,
                "language_label": language_label,
                "manual_url": f"manual/{family}/{model}/{target.language}/index.html",
                "word_url": word_path,
                "product_name": product_name,
                "manual_title": manual_title,
                "region": family,
                "model": model,
                "config": path_for_display(Path(spec["config_path"])),
                "manual_source": str(spec["source_label"]),
                "tracked_root": path_for_display(tracked_root),
            }
            language_payloads.append(language_entry)
            if not default_manual_url:
                default_manual_url = str(language_entry["manual_url"])
                default_lang = manual_lang

        model_payload = {
            "model": model,
            "product_name": model_product_name,
            "manual_title": model_manual_title,
            "tracked_root": path_for_display(tracked_root),
            "diff_config": path_for_display(diff_config_for_family(args, family)),
            "change_index_url": f"changes/{family}/{model}/index.html",
            "change_workbook_url": workbook_path,
            "csv_urls": dict(csv_files),
            "report_files": dict(report_files),
            "shared_language_labels": shared_language_labels,
            "default_lang": default_lang or "en",
            "default_manual_url": default_manual_url,
            "languages": language_payloads,
        }

        family_payload = families_payload_by_name.setdefault(
            family,
            {
                "family": family,
                "change_index_url": f"changes/{family}/index.html",
                "shared_language_labels": [],
                "models": [],
            },
        )
        family_payload["models"].append(model_payload)
        family_shared_labels = family_payload["shared_language_labels"]
        if isinstance(family_shared_labels, list):
            for label in shared_language_labels:
                if label not in family_shared_labels:
                    family_shared_labels.append(label)

        family_changes = changes_by_family.setdefault(
            family,
            {
                "family": family,
                "models": {},
            },
        )
        family_changes_models = family_changes.get("models")
        if not isinstance(family_changes_models, dict):
            family_changes_models = {}
            family_changes["models"] = family_changes_models
        family_changes_models[model] = {
            "model": model,
            "family": family,
            "from_ref": args.from_ref,
            "to_ref": args.to_ref,
            "changed_files": changed_files,
            "review_pages": review_pages_for_family(changed_files, model, family),
            "areas": classify_changes(changed_files, model, family),
            "report_prefix": prefix,
            "report_files": report_files,
            "downloads": build_downloads_metadata(
                word_path=None,
                workbook_path=workbook_path,
                csv_files=csv_files,
            ),
        }

    families_payload = [
        families_payload_by_name[name]
        for name in sorted(
            families_payload_by_name,
            key=lambda family: FAMILY_ORDER.index(family) if family in FAMILY_ORDER else len(FAMILY_ORDER),
        )
    ]

    for family_entry in families_payload:
        models = family_entry.get("models", [])
        if not isinstance(models, list) or not models:
            continue
        preferred_model = next(
            (item for item in models if isinstance(item, dict) and display_text(item.get("model")) == args.model),
            models[0],
        )
        if isinstance(preferred_model, dict):
            family_entry["default_model"] = display_text(preferred_model.get("model"), args.model)
            family_entry["default_lang"] = display_text(preferred_model.get("default_lang"), requested_target.language)
            family_entry["default_manual_url"] = display_text(preferred_model.get("default_manual_url"), "")

    default_family_entry = next(
        (item for item in families_payload if display_text(item.get("family")) == args.region),
        families_payload[0],
    )
    default_models = default_family_entry.get("models", [])
    if not isinstance(default_models, list) or not default_models:
        raise RuntimeError("Review preview workspace has no model entries to render.")
    default_model_entry = next(
        (item for item in default_models if isinstance(item, dict) and display_text(item.get("model")) == args.model),
        default_models[0],
    )
    if not isinstance(default_model_entry, dict):
        raise RuntimeError("Review preview workspace default model entry is invalid.")
    default_languages = default_model_entry.get("languages", [])
    if not isinstance(default_languages, list) or not default_languages:
        raise RuntimeError("Review preview workspace default language entry is missing.")
    default_language_entry = next(
        (
            item
            for item in default_languages
            if isinstance(item, dict) and display_text(item.get("lang"), "").lower() == requested_target.language
        ),
        default_languages[0],
    )
    if not isinstance(default_language_entry, dict):
        raise RuntimeError("Review preview workspace default language entry is invalid.")
    default_model = display_text(default_model_entry.get("model"), args.model)
    default_lang = display_text(default_language_entry.get("lang"), requested_target.language).lower()
    default_manual_url = display_text(default_language_entry.get("manual_url"), "")
    default_change_url = display_text(default_model_entry.get("change_index_url"), "changes/index.html")

    commit_sha = git_value("VERCEL_GIT_COMMIT_SHA", ["git", "rev-parse", "HEAD"])
    commit_message = git_value("VERCEL_GIT_COMMIT_MESSAGE", ["git", "log", "-1", "--pretty=%s"])
    branch = git_value("VERCEL_GIT_COMMIT_REF", ["git", "rev-parse", "--abbrev-ref", "HEAD"])
    author = git_value("VERCEL_GIT_COMMIT_AUTHOR_NAME", ["git", "log", "-1", "--pretty=%an"])
    pr_id = os.environ.get("VERCEL_GIT_PULL_REQUEST_ID", "").strip()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    meta = {
        "title": workspace_title(args.model),
        "model": args.model,
        "source": args.source,
        "requested_family": args.region,
        "default_family": display_text(default_family_entry.get("family"), args.region),
        "default_model": default_model,
        "default_lang": default_lang,
        "default_manual_url": default_manual_url,
        "default_change_url": default_change_url,
        "available_families": [display_text(item.get("family")) for item in families_payload],
        "family_count": len(families_payload),
        "available_models": sorted(
            {
                display_text(model_entry.get("model"))
                for family_entry in families_payload
                for model_entry in (family_entry.get("models", []) if isinstance(family_entry.get("models", []), list) else [])
                if isinstance(model_entry, dict)
            }
        ),
        "from_ref": args.from_ref,
        "to_ref": args.to_ref,
        "branch": branch,
        "commit_sha": commit_sha,
        "commit_sha_short": commit_sha[:7],
        "commit_message": commit_message,
        "author": author,
        "pr_id": pr_id,
        "generated_at": generated_at,
        "generated_at_display": format_generated_at(generated_at),
        "vercel_env": os.environ.get("VERCEL_ENV", "").strip(),
        "vercel_url": os.environ.get("VERCEL_URL", "").strip(),
    }
    workspace = {
        **meta,
        "defaults": {
            "family": display_text(default_family_entry.get("family"), args.region),
            "model": default_model,
            "lang": default_lang,
            "manual_url": default_manual_url,
            "change_url": default_change_url,
        },
        "families": families_payload,
    }
    changes = {
        "from_ref": args.from_ref,
        "to_ref": args.to_ref,
        "defaults": dict(workspace["defaults"]),
        "families": changes_by_family,
    }

    for family_entry in families_payload:
        family_name = display_text(family_entry.get("family"))
        family_models = family_entry.get("models", [])
        if not isinstance(family_models, list):
            family_models = []
        (changes_root / family_name / "index.html").parent.mkdir(parents=True, exist_ok=True)
        (changes_root / family_name / "index.html").write_text(
            render_family_changes_html(meta, family_entry),
            encoding="utf-8",
        )
        family_changes = changes_by_family.get(family_name, {})
        family_changes_models = family_changes.get("models", {}) if isinstance(family_changes, dict) else {}
        if not isinstance(family_changes_models, dict):
            family_changes_models = {}
        for model_entry in family_models:
            if not isinstance(model_entry, dict):
                continue
            model_name = display_text(model_entry.get("model"))
            model_changes = family_changes_models.get(model_name, {})
            if not isinstance(model_changes, dict):
                model_changes = {}
            model_change_path = changes_root / family_name / model_name / "index.html"
            model_change_path.parent.mkdir(parents=True, exist_ok=True)
            model_change_path.write_text(
                render_model_changes_html(meta, family_entry, model_entry, model_changes),
                encoding="utf-8",
            )

    write_json(generated_dir / "meta.json", meta)
    write_json(generated_dir / "workspace.json", workspace)
    write_json(generated_dir / "changes.json", changes)
    (output_dir / "index.html").write_text(render_workspace_html(display_text(meta.get("title"))), encoding="utf-8")
    (manual_root / "index.html").parent.mkdir(parents=True, exist_ok=True)
    (manual_root / "index.html").write_text(
        render_redirect_html(
            title=f"{display_text(meta.get('title'))} - Manual",
            target=f"./{default_manual_url.removeprefix('manual/')}",
            heading="Open the default review HTML",
            copy="This compatibility entry now redirects to the default manual inside the review handoff workspace.",
        ),
        encoding="utf-8",
    )
    (changes_root / "index.html").parent.mkdir(parents=True, exist_ok=True)
    (changes_root / "index.html").write_text(
        render_changes_home_html(meta, families_payload),
        encoding="utf-8",
    )

    assert_preview_output_contract(
        output_dir,
        workspace,
        require_word=not args.skip_word,
        required_preview_files=REQUIRED_PREVIEW_FILES,
        required_download_csvs=REQUIRED_DOWNLOAD_CSVS,
        required_change_report_files=REQUIRED_CHANGE_REPORT_FILES,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
