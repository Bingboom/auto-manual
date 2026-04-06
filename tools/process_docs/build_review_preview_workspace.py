from __future__ import annotations

import os
import shutil
import subprocess
from argparse import Namespace
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

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
from tools.process_docs.build_review_preview_render import (
    derive_product_name,
    display_text,
    format_generated_at,
    preview_language_label,
    workspace_title,
)
from tools.process_docs.build_review_preview_targets import (
    FAMILY_ORDER,
    WorkspaceTarget,
    build_diff_command,
    build_export_command,
    build_spec_for_target,
    diff_config_for_family,
    path_for_display,
    target_sort_key,
    tracked_root_for_target,
)


def build_target_specs(
    args: Namespace,
    workspace_targets: list[WorkspaceTarget],
    *,
    requested_target: WorkspaceTarget,
    review_availability: set[tuple[str, str, str | None]],
    docs_dir: Path,
) -> dict[str, dict[str, object]]:
    return {
        target.label: build_spec_for_target(
            args,
            target,
            requested_target=requested_target,
            review_availability=review_availability,
            docs_dir=docs_dir,
        )
        for target in workspace_targets
    }


def export_workspace_targets(
    args: Namespace,
    workspace_targets: list[WorkspaceTarget],
    *,
    target_specs: dict[str, dict[str, object]],
    run_command: Callable[[list[str]], None],
) -> None:
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
            run_command(
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


def assemble_family_payloads(
    args: Namespace,
    workspace_targets: list[WorkspaceTarget],
    *,
    all_workspace_targets: list[WorkspaceTarget],
    target_specs: dict[str, dict[str, object]],
    root: Path,
    changed_files: list[str],
    manual_root: Path,
    changes_root: Path,
    downloads_root: Path,
    run_command: Callable[[list[str]], None],
    rewrite_manual_tree_for_preview_func: Callable[..., None],
    classify_changes_func: Callable[[list[str], str, str], list[dict[str, object]]],
    review_pages_for_family_func: Callable[[list[str], str, str], list[str]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    grouped_targets: dict[tuple[str, str], list[WorkspaceTarget]] = {}
    for target in workspace_targets:
        grouped_targets.setdefault((target.family, target.model), []).append(target)

    families_payload_by_name: dict[str, dict[str, object]] = {}
    changes_by_family: dict[str, object] = {}

    for family, model in sorted(
        grouped_targets,
        key=lambda item: (FAMILY_ORDER.index(item[0]) if item[0] in FAMILY_ORDER else len(FAMILY_ORDER), item[1]),
    ):
        targets = sorted(grouped_targets[(family, model)], key=target_sort_key)
        representative = targets[0]
        tracked_root = tracked_root_for_target(args, representative)

        if not args.skip_diff:
            try:
                run_command(build_diff_command(args=args, target=representative, tracked_root=tracked_root))
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(f"Review preview failed to build the diff-report set for {model}/{family}.") from exc

        report_root = root / "reports" / "version_tracking" / model / family
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
            rewrite_manual_tree_for_preview_func(
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
            "review_pages": review_pages_for_family_func(changed_files, model, family),
            "areas": classify_changes_func(changed_files, model, family),
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
    return families_payload, changes_by_family


def build_workspace_documents(
    args: Namespace,
    families_payload: list[dict[str, object]],
    changes_by_family: dict[str, object],
    *,
    requested_target: WorkspaceTarget,
    git_value_func: Callable[[str, list[str]], str],
) -> tuple[dict[str, object], dict[str, object], dict[str, object], str]:
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

    commit_sha = git_value_func("VERCEL_GIT_COMMIT_SHA", ["git", "rev-parse", "HEAD"])
    commit_message = git_value_func("VERCEL_GIT_COMMIT_MESSAGE", ["git", "log", "-1", "--pretty=%s"])
    branch = git_value_func("VERCEL_GIT_COMMIT_REF", ["git", "rev-parse", "--abbrev-ref", "HEAD"])
    author = git_value_func("VERCEL_GIT_COMMIT_AUTHOR_NAME", ["git", "log", "-1", "--pretty=%an"])
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
    return meta, workspace, changes, default_manual_url


def write_workspace_outputs(
    output_dir: Path,
    *,
    manual_root: Path,
    changes_root: Path,
    generated_dir: Path,
    meta: dict[str, object],
    workspace: dict[str, object],
    changes: dict[str, object],
    families_payload: list[dict[str, object]],
    default_manual_url: str,
) -> None:
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
        family_changes = changes.get("families", {}).get(family_name, {}) if isinstance(changes.get("families"), dict) else {}
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
