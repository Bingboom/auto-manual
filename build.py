#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path

from tools.build_paths import (
    clean_targets_for_config as _clean_targets_for_config,
    load_config as _load_config,
    resolve_docs_dir as _resolve_docs_dir,
    resolve_layout_params_csv as _resolve_layout_params_csv,
    resolve_path_from_root as _resolve_path_from_root,
    resolve_staging_root as _resolve_staging_root,
    review_root_for_config as _review_root_for_config,
    staging_docs_build_dir as _staging_docs_build_dir,
    staging_releases_root as _staging_releases_root,
    staging_version_tracking_root as _staging_version_tracking_root,
    version_tracking_root as _version_tracking_root,
)
from tools.build_entry_commands import (
    append_data_root_arg as _append_data_root_arg_impl,
    append_target_args as _append_target_args_impl,
    build_docs_command as _build_docs_command_impl,
    check_docs_command as _check_docs_command_impl,
    effective_source as _effective_source_impl,
    listen_build_queue_command as _listen_build_queue_command_impl,
    normalize_cli_build_queue_action as _normalize_cli_build_queue_action_impl,
    process_build_queue_command as _process_build_queue_command_impl,
    process_review_start_queue_command as _process_review_start_queue_command_impl,
    release_manifest_command as _release_manifest_command_impl,
    review_bundle_command as _review_bundle_command_impl,
    sync_data_command as _sync_data_command_impl,
    sync_review_command as _sync_review_command_impl,
)
from tools.build_doctor import (
    check_word_com_available as _check_word_com_available_impl,
    collect_doctor_findings as _collect_doctor_findings_impl,
    doctor_import as _doctor_import_impl,
    find_xelatex as _find_xelatex_impl,
    is_windows_platform as _is_windows_platform_impl,
    render_config_tokenized_value as _render_config_tokenized_value_impl,
    render_finding as _doctor_render_finding_impl,
    resolve_doctor_pdf_mode as _resolve_doctor_pdf_mode_impl,
    resolve_doctor_target as _resolve_doctor_target_impl,
    resolve_reference_doc_status as _resolve_reference_doc_status_impl,
    slug_token as _slug_token_impl,
)
from tools.build_reports import (
    default_report_dir_for_tracked_root as _default_report_dir_for_tracked_root_impl,
    diff_report_command as _diff_report_command,
    publish_target_components as _publish_target_components_impl,
    report_dir_for_target as _report_dir_for_target_impl,
    require_explicit_target as _require_explicit_target_impl,
    resolve_diff_report_targets as _resolve_diff_report_targets_impl,
    tracked_root_for_target as _tracked_root_for_target_impl,
)

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = "config.us.yaml"
BUILD_ACTIONS = ("rst", "word", "html", "pdf", "all")
ALL_OUTPUT_FORMATS = "html,word,pdf"
VALID_PDF_MODES = {"latex", "word"}
STAGING_ROOT_ENV = "AUTO_MANUAL_STAGING_ROOT"


@dataclass
class DoctorFinding:
    level: str
    area: str
    message: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Cross-platform build entrypoint for Auto-Manual.",
    )
    ap.add_argument(
        "action",
        choices=(
            "validate",
            "doctor",
            *BUILD_ACTIONS,
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
    ap.add_argument("--config", default=DEFAULT_CONFIG, help="Config YAML path, relative to repo root by default")
    ap.add_argument("--model", default=None, help="Build a single model instead of build.targets")
    ap.add_argument("--region", default=None, help="Build a single region instead of build.targets")
    ap.add_argument(
        "--staging-root",
        default=None,
        help=f"Isolate generated verification/build outputs under this root (or set {STAGING_ROOT_ENV})",
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


def resolve_path_from_root(raw_path: str) -> Path:
    return _resolve_path_from_root(ROOT, raw_path)


def resolve_staging_root(args: argparse.Namespace) -> Path | None:
    return _resolve_staging_root(repo_root=ROOT, args=args, env_var=STAGING_ROOT_ENV)


def staging_docs_build_dir(args: argparse.Namespace) -> Path | None:
    return _staging_docs_build_dir(repo_root=ROOT, args=args, env_var=STAGING_ROOT_ENV)


def staging_version_tracking_root(args: argparse.Namespace) -> Path | None:
    return _staging_version_tracking_root(repo_root=ROOT, args=args, env_var=STAGING_ROOT_ENV)


def staging_releases_root(args: argparse.Namespace) -> Path | None:
    return _staging_releases_root(repo_root=ROOT, args=args, env_var=STAGING_ROOT_ENV)


def load_config(config_path: Path) -> dict:
    return _load_config(config_path)


def resolve_layout_params_csv(config_path: Path) -> Path:
    return _resolve_layout_params_csv(config_path, repo_root=ROOT, config_loader=load_config)


def resolve_docs_dir(config_path: Path) -> Path:
    return _resolve_docs_dir(config_path, repo_root=ROOT, config_loader=load_config)


def clean_targets_for_config(config_path: Path) -> tuple[Path, Path]:
    return _clean_targets_for_config(config_path, repo_root=ROOT, config_loader=load_config)


def review_root_for_config(config_path: Path) -> Path:
    return _review_root_for_config(config_path, repo_root=ROOT, config_loader=load_config)


def version_tracking_root(*, base_root: Path | None = None) -> Path:
    return _version_tracking_root(repo_root=ROOT, base_root=base_root)


def _path_component(value: str) -> str:
    text = value.strip()
    return text.replace("/", "_").replace("\\", "_").replace(":", "_")


def _preview_output_root(
    config_path: Path,
    *,
    model: str,
    region: str,
    page: str,
    docs_build_dir: Path | None = None,
) -> Path:
    actual_docs_build_dir = docs_build_dir or (resolve_docs_dir(config_path) / "_build")
    return actual_docs_build_dir / _path_component(model) / _path_component(region) / "preview" / _path_component(page)


def is_legacy_bundle_dir(path: Path) -> bool:
    return path.is_dir() and (path / "index.rst").exists() and (path / "page").is_dir()


def collect_legacy_docs_output_dirs(docs_dir: Path) -> list[Path]:
    if not docs_dir.exists():
        return []

    legacy_dirs: list[Path] = []
    generated_dir = docs_dir / "generated"
    if generated_dir.exists():
        legacy_dirs.append(generated_dir)

    reserved = {"_build", "_static", "renderers", "templates", "__pycache__"}
    for child in docs_dir.iterdir():
        if not child.is_dir() or child.name in reserved or child == generated_dir:
            continue
        if is_legacy_bundle_dir(child):
            legacy_dirs.append(child)
            continue
        subdirs = [item for item in child.iterdir() if item.is_dir()]
        if subdirs and all(is_legacy_bundle_dir(item) for item in subdirs):
            legacy_dirs.append(child)
    return legacy_dirs


def format_command(cmd: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in cmd])


def run_checked(cmd: list[str]) -> None:
    print(f"[build.py] {format_command(cmd)}")
    subprocess.run(cmd, cwd=str(ROOT), check=True)


def ensure_supported_staging_action(args: argparse.Namespace) -> None:
    if resolve_staging_root(args) is None:
        return
    if args.action == "review":
        raise RuntimeError("review does not support --staging-root because it seeds docs/_review from the repo runtime bundle")


def normalize_cli_build_queue_action(workflow_action: str | None = None, doc_phase: str | None = None) -> str | None:
    return _normalize_cli_build_queue_action_impl(workflow_action, doc_phase)


def _effective_source(args: argparse.Namespace, *, source_override: str = "auto") -> str:
    return _effective_source_impl(args, source_override=source_override)


def _append_target_args(cmd: list[str], args: argparse.Namespace) -> list[str]:
    return _append_target_args_impl(cmd, args)


def _append_data_root_arg(cmd: list[str], args: argparse.Namespace) -> list[str]:
    return _append_data_root_arg_impl(cmd, args)


def build_docs_command(
    args: argparse.Namespace,
    *,
    action_override: str | None = None,
    source_override: str | None = None,
) -> list[str]:
    return _build_docs_command_impl(
        args,
        repo_root=ROOT,
        build_actions=BUILD_ACTIONS,
        all_output_formats=ALL_OUTPUT_FORMATS,
        resolve_path_from_root=resolve_path_from_root,
        staging_docs_build_dir=staging_docs_build_dir,
        preview_output_root=_preview_output_root,
        require_explicit_target=lambda parsed_args, action_name: _require_explicit_target(
            parsed_args,
            action_name=action_name,
        ),
        action_override=action_override,
        source_override=source_override,
    )


def review_bundle_command(args: argparse.Namespace) -> list[str]:
    return _review_bundle_command_impl(
        args,
        repo_root=ROOT,
        resolve_path_from_root=resolve_path_from_root,
        staging_docs_build_dir=staging_docs_build_dir,
    )


def check_docs_command(args: argparse.Namespace) -> list[str]:
    return _check_docs_command_impl(
        args,
        repo_root=ROOT,
        resolve_path_from_root=resolve_path_from_root,
        staging_docs_build_dir=staging_docs_build_dir,
    )


def sync_review_command(args: argparse.Namespace) -> list[str]:
    return _sync_review_command_impl(
        args,
        repo_root=ROOT,
        resolve_path_from_root=resolve_path_from_root,
        staging_docs_build_dir=staging_docs_build_dir,
    )


def _review_sync_target_args(args: argparse.Namespace) -> list[argparse.Namespace]:
    from tools.build_docs import resolve_build_targets
    from tools.review_support import review_bundle_exists

    config_path = resolve_path_from_root(args.config)
    cfg = load_config(config_path)
    docs_dir = resolve_docs_dir(config_path)
    targets = resolve_build_targets(
        cfg,
        arg_model=args.model,
        arg_region=args.region,
        all_targets=not (args.model or args.region),
    )

    seen: set[tuple[str, str]] = set()
    sync_args_list: list[argparse.Namespace] = []
    for target in targets:
        if not review_bundle_exists(
            docs_dir=docs_dir,
            model=target.model,
            region=target.region,
            lang=target.lang,
        ):
            continue
        key = (str(target.model or ""), str(target.region or ""))
        if key in seen:
            continue
        seen.add(key)
        cloned = argparse.Namespace(**vars(args))
        cloned.config = str(config_path)
        cloned.model = target.model
        cloned.region = target.region
        cloned.sync_scope = "params"
        cloned.page_file = []
        sync_args_list.append(cloned)
    return sync_args_list


def maybe_sync_review_before_build(args: argparse.Namespace, *, source_override: str = "auto") -> None:
    effective_source = _effective_source(args, source_override=source_override)
    if effective_source not in {"auto", "review"}:
        return
    for sync_args in _review_sync_target_args(args):
        run_checked(build_docs_command(sync_args, action_override="rst", source_override="runtime"))
        run_checked(sync_review_command(sync_args))


def sync_data_command(args: argparse.Namespace) -> list[str]:
    return _sync_data_command_impl(
        args,
        repo_root=ROOT,
        resolve_path_from_root=resolve_path_from_root,
    )


def release_manifest_command(args: argparse.Namespace) -> list[str]:
    return _release_manifest_command_impl(
        args,
        repo_root=ROOT,
        require_explicit_target=lambda parsed_args, action_name: _require_explicit_target(
            parsed_args,
            action_name=action_name,
        ),
        resolve_path_from_root=resolve_path_from_root,
        staging_docs_build_dir=staging_docs_build_dir,
        staging_releases_root=staging_releases_root,
    )


def process_build_queue_command(args: argparse.Namespace) -> list[str]:
    if (args.doc_phase or "").strip() and not (args.workflow_action or "").strip():
        warnings.warn(
            "--doc-phase is deprecated; use --workflow-action instead.",
            UserWarning,
            stacklevel=2,
        )
    return _process_build_queue_command_impl(
        args,
        repo_root=ROOT,
        resolve_path_from_root=resolve_path_from_root,
        normalize_cli_build_queue_action=normalize_cli_build_queue_action,
    )


def process_review_start_queue_command(args: argparse.Namespace) -> list[str]:
    return _process_review_start_queue_command_impl(
        args,
        repo_root=ROOT,
        resolve_path_from_root=resolve_path_from_root,
    )


def listen_build_queue_command(args: argparse.Namespace) -> list[str]:
    return _listen_build_queue_command_impl(
        args,
        repo_root=ROOT,
        resolve_path_from_root=resolve_path_from_root,
    )


def run_validate(config_path: Path, *, data_root: str | None = None) -> None:
    run_checked(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_config.py"),
            "--config",
            str(config_path),
        ]
    )
    run_checked(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_layout_params.py"),
            "--csv",
            str(resolve_layout_params_csv(config_path)),
        ]
    )
    run_checked(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_spec_master.py"),
            "--config",
            str(config_path),
            *(
                ["--data-root", data_root.strip()]
                if isinstance(data_root, str) and data_root.strip()
                else []
            ),
        ]
    )


def _doctor_add(findings: list[DoctorFinding], level: str, area: str, message: str) -> None:
    findings.append(DoctorFinding(level=level, area=area, message=message))


def _doctor_render_finding(finding: DoctorFinding) -> str:
    return _doctor_render_finding_impl(finding)


def _doctor_import(module_name: str) -> tuple[bool, str]:
    return _doctor_import_impl(module_name)


def _slug_token(value: str | None) -> str:
    return _slug_token_impl(value)


def _render_config_tokenized_value(value: str, model: str | None, region: str | None) -> str:
    return _render_config_tokenized_value_impl(value, model, region)


def _is_windows_platform() -> bool:
    return _is_windows_platform_impl()


def _find_xelatex() -> str | None:
    from tools.utils.process_utils import find_exe

    return _find_xelatex_impl(find_exe=find_exe)


def _check_word_com_available() -> tuple[bool, str]:
    return _check_word_com_available_impl(repo_root=ROOT, is_windows_platform=_is_windows_platform)


def _resolve_doctor_target(cfg: dict, args: argparse.Namespace) -> tuple[str | None, str | None]:
    from tools.utils.targets import resolve_build_model, resolve_build_region

    return _resolve_doctor_target_impl(
        cfg,
        args,
        resolve_build_model=resolve_build_model,
        resolve_build_region=resolve_build_region,
    )


def _resolve_doctor_pdf_mode(cfg: dict, cli_pdf_mode: str | None) -> str:
    return _resolve_doctor_pdf_mode_impl(cfg, cli_pdf_mode, valid_pdf_modes=VALID_PDF_MODES)


def _resolve_reference_doc_status(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
) -> DoctorFinding | None:
    return _resolve_reference_doc_status_impl(
        cfg,
        model=model,
        region=region,
        repo_root=ROOT,
        finding_cls=DoctorFinding,
        render_config_tokenized_value=_render_config_tokenized_value,
    )


def _collect_doctor_findings(args: argparse.Namespace) -> list[DoctorFinding]:
    from tools.validate_config import load_yaml as load_validate_yaml
    from tools.validate_config import validate as validate_cfg
    from tools.validate_layout_params import validate as validate_layout

    return _collect_doctor_findings_impl(
        args,
        finding_cls=DoctorFinding,
        resolve_path_from_root=resolve_path_from_root,
        load_validate_yaml=load_validate_yaml,
        validate_cfg=validate_cfg,
        validate_layout=validate_layout,
        resolve_layout_params_csv=resolve_layout_params_csv,
        doctor_add=_doctor_add,
        doctor_import=_doctor_import,
        resolve_doctor_target=_resolve_doctor_target,
        resolve_reference_doc_status=_resolve_reference_doc_status,
        is_windows_platform=_is_windows_platform,
        check_word_com_available=_check_word_com_available,
        find_xelatex=_find_xelatex,
        resolve_doctor_pdf_mode=_resolve_doctor_pdf_mode,
        clean_targets_for_config=clean_targets_for_config,
    )


def run_doctor(args: argparse.Namespace) -> None:
    findings = _collect_doctor_findings(args)
    for finding in findings:
        print(_doctor_render_finding(finding))

    errors = sum(1 for finding in findings if finding.level == "ERROR")
    warnings = sum(1 for finding in findings if finding.level == "WARN")
    print(f"[doctor] SUMMARY errors={errors} warnings={warnings}")
    if errors:
        raise RuntimeError(f"doctor found {errors} blocking issue(s)")


def run_diff_report(args: argparse.Namespace) -> None:
    config_path = resolve_path_from_root(args.config)
    tracked_root_explicit = args.tracked_root is not None
    report_dir_explicit = args.report_dir is not None
    staging_root = resolve_staging_root(args)

    if tracked_root_explicit:
        tracked_root = resolve_path_from_root(args.tracked_root)
        if report_dir_explicit:
            report_dir = resolve_path_from_root(args.report_dir)
        else:
            report_dir = _default_report_dir_for_tracked_root(config_path, tracked_root, base_root=staging_root)
        run_diff_report_with_paths(args, tracked_root=tracked_root, report_dir=report_dir)
        return

    targets = _resolve_diff_report_targets(args)
    if report_dir_explicit and len(targets) != 1:
        raise RuntimeError("diff-report with explicit --report-dir requires a single resolved target or explicit --tracked-root")

    for target in targets:
        if len(target) == 2:
            model, region = target
            lang = None
        else:
            model, region, lang = target
        tracked_root = _tracked_root_for_target(config_path, model=model, region=region, lang=lang)
        report_dir = (
            resolve_path_from_root(args.report_dir)
            if report_dir_explicit
            else _report_dir_for_target(model, region, lang=lang, base_root=staging_root)
        )
        run_diff_report_with_paths(args, tracked_root=tracked_root, report_dir=report_dir)


def run_diff_report_with_paths(
    args: argparse.Namespace,
    *,
    tracked_root: Path,
    report_dir: Path,
) -> None:
    cmd = _diff_report_command(
        repo_root=ROOT,
        config_path=resolve_path_from_root(args.config),
        tracked_root=tracked_root,
        report_dir=report_dir,
        from_ref=args.from_ref,
        to_ref=args.to_ref,
        data_root=args.data_root,
        ignore_initial_adds=args.ignore_initial_adds,
    )
    run_checked(cmd)


def run_check(args: argparse.Namespace, *, source_override: str = "auto") -> None:
    config_path = resolve_path_from_root(args.config)
    if isinstance(args.data_root, str) and args.data_root.strip():
        run_validate(config_path, data_root=args.data_root)
    else:
        run_validate(config_path)
    effective_source = _effective_source(args, source_override=source_override)
    maybe_sync_review_before_build(args, source_override=effective_source)
    run_checked(build_docs_command(args, action_override="rst", source_override=effective_source))
    run_checked(check_docs_command(args))


def _publish_target_components(args: argparse.Namespace) -> tuple[str, str, str | None]:
    from tools.utils.targets import resolve_output_lang

    return _publish_target_components_impl(
        config_path=resolve_path_from_root(args.config),
        model=args.model,
        region=args.region,
        action_name="publish",
        config_loader=load_config,
        resolve_output_lang=resolve_output_lang,
    )


def _require_explicit_target(args: argparse.Namespace, *, action_name: str) -> tuple[str, str]:
    return _require_explicit_target_impl(model=args.model, region=args.region, action_name=action_name)


def _publish_tracked_root(args: argparse.Namespace) -> Path:
    model, region, lang = _publish_target_components(args)
    if args.tracked_root is not None:
        return resolve_path_from_root(args.tracked_root)
    return _tracked_root_for_target(resolve_path_from_root(args.config), model=model, region=region, lang=lang)


def _publish_report_dir(args: argparse.Namespace) -> Path:
    model, region, lang = _publish_target_components(args)
    if args.report_dir is not None:
        return resolve_path_from_root(args.report_dir)
    return _report_dir_for_target(model, region, lang=lang, base_root=resolve_staging_root(args))


def _tracked_root_for_target(
    config_path: Path,
    *,
    model: str | None,
    region: str | None,
    lang: str | None = None,
) -> Path:
    return _tracked_root_for_target_impl(
        config_path=config_path,
        model=model,
        region=region,
        lang=lang,
        review_root_for_config=review_root_for_config,
    )


def _report_dir_for_target(
    model: str | None,
    region: str | None,
    *,
    lang: str | None = None,
    base_root: Path | None = None,
) -> Path:
    return _report_dir_for_target_impl(
        model=model,
        region=region,
        lang=lang,
        version_tracking_root=version_tracking_root,
        base_root=base_root,
    )


def _default_report_dir_for_tracked_root(config_path: Path, tracked_root: Path, *, base_root: Path | None = None) -> Path:
    return _default_report_dir_for_tracked_root_impl(
        config_path=config_path,
        tracked_root=tracked_root,
        review_root_for_config=review_root_for_config,
        version_tracking_root=version_tracking_root,
        base_root=base_root,
    )


def _resolve_diff_report_targets(args: argparse.Namespace) -> list[tuple[str | None, str | None, str | None]]:
    from tools.build_docs import resolve_build_targets

    return _resolve_diff_report_targets_impl(
        config_path=resolve_path_from_root(args.config),
        config_loader=load_config,
        resolve_build_targets=resolve_build_targets,
        model=args.model,
        region=args.region,
    )


def run_publish(args: argparse.Namespace) -> None:
    tracked_root = _publish_tracked_root(args)
    report_dir = _publish_report_dir(args)
    run_check(args, source_override="review")
    run_diff_report_with_paths(args, tracked_root=tracked_root, report_dir=report_dir)
    run_checked(build_docs_command(args, action_override="word", source_override="review"))
    run_checked(release_manifest_command(args))


def clean_build_artifacts(config_path: Path, *, remove_params_tex: bool = True) -> None:
    build_dir, params_tex = clean_targets_for_config(config_path)
    review_dir = review_root_for_config(config_path)
    docs_dir = resolve_docs_dir(config_path)
    print(f"[build.py] remove {build_dir}")
    shutil.rmtree(build_dir, ignore_errors=True)
    print(f"[build.py] remove {review_dir}")
    shutil.rmtree(review_dir, ignore_errors=True)
    if remove_params_tex:
        print(f"[build.py] remove {params_tex}")
        params_tex.unlink(missing_ok=True)
    for legacy_dir in collect_legacy_docs_output_dirs(docs_dir):
        print(f"[build.py] remove {legacy_dir}")
        shutil.rmtree(legacy_dir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = resolve_path_from_root(args.config)

    try:
        ensure_supported_staging_action(args)
        if args.action == "validate":
            run_validate(config_path, data_root=args.data_root)
        elif args.action == "doctor":
            run_doctor(args)
        elif args.action == "review":
            run_checked(build_docs_command(args, action_override="rst", source_override="runtime"))
            run_checked(review_bundle_command(args))
        elif args.action == "check":
            run_check(args)
        elif args.action == "sync-review":
            run_checked(build_docs_command(args, action_override="rst", source_override="runtime"))
            run_checked(sync_review_command(args))
        elif args.action == "sync-data":
            run_checked(sync_data_command(args))
        elif args.action == "process-review-start-queue":
            run_checked(process_review_start_queue_command(args))
        elif args.action == "process-build-queue":
            run_checked(process_build_queue_command(args))
        elif args.action == "listen-build-queue":
            run_checked(listen_build_queue_command(args))
        elif args.action == "publish":
            run_publish(args)
        elif args.action == "diff-report":
            run_diff_report(args)
        elif args.action == "release-manifest":
            run_checked(release_manifest_command(args))
        elif args.action == "clean":
            clean_build_artifacts(config_path)
        else:
            maybe_sync_review_before_build(args)
            run_checked(build_docs_command(args))
    except subprocess.CalledProcessError as exc:
        return exc.returncode or 1
    except RuntimeError as exc:
        print(f"[build.py] ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
