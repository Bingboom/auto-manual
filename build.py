#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import shutil
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
    message_control_dry_run_command as _message_control_dry_run_command_impl,
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
    run_doctor as _run_doctor_impl,
    slug_token as _slug_token_impl,
)
from tools.build_cli import parse_args as _parse_args_impl
from tools.build_dispatch import dispatch_action as _dispatch_action_impl
from tools.build_main import run_main as _run_main_impl
from tools.message_control_runtime import resolve_message_control as _resolve_message_control_impl
from tools.queue_execute import run_queue_execute as _run_queue_execute_impl
from tools.queue_query import run_queue_query as _run_queue_query_impl
from tools.queue_resolve_action import run_queue_resolve_action as _run_queue_resolve_action_impl
from tools.build_reports import (
    default_report_dir_for_tracked_root as _default_report_dir_for_tracked_root_impl,
    diff_report_command as _diff_report_command,
    publish_target_components as _publish_target_components_impl,
    report_dir_for_target as _report_dir_for_target_impl,
    require_explicit_target as _require_explicit_target_impl,
    resolve_diff_report_targets as _resolve_diff_report_targets_impl,
    tracked_root_for_target as _tracked_root_for_target_impl,
)
from tools.build_publish import (
    run_diff_report as _run_diff_report_impl,
    run_diff_report_with_paths as _run_diff_report_with_paths_impl,
    run_publish as _run_publish_impl,
)
from tools.build_runtime import (
    clean_build_artifacts as _clean_build_artifacts_impl,
    collect_legacy_docs_output_dirs as _collect_legacy_docs_output_dirs_impl,
    format_command as _format_command_impl,
    is_legacy_bundle_dir as _is_legacy_bundle_dir_impl,
    maybe_sync_review_before_build as _maybe_sync_review_before_build_impl,
    path_component as _path_component_impl,
    preview_output_root as _preview_output_root_impl,
    review_sync_target_args as _review_sync_target_args_impl,
    run_check as _run_check_impl,
    run_checked as _run_checked_impl,
    run_validate as _run_validate_impl,
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
    return _parse_args_impl(
        argv,
        default_config=DEFAULT_CONFIG,
        build_actions=BUILD_ACTIONS,
        staging_root_env=STAGING_ROOT_ENV,
    )


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
    return _path_component_impl(value)


def _preview_output_root(
    config_path: Path,
    *,
    model: str,
    region: str,
    page: str,
    docs_build_dir: Path | None = None,
) -> Path:
    return _preview_output_root_impl(
        config_path,
        model=model,
        region=region,
        page=page,
        docs_build_dir=docs_build_dir,
        resolve_docs_dir=resolve_docs_dir,
    )


def is_legacy_bundle_dir(path: Path) -> bool:
    return _is_legacy_bundle_dir_impl(path)


def collect_legacy_docs_output_dirs(docs_dir: Path) -> list[Path]:
    return _collect_legacy_docs_output_dirs_impl(docs_dir)


def format_command(cmd: list[str]) -> str:
    return _format_command_impl(cmd)


def run_checked(cmd: list[str]) -> None:
    return _run_checked_impl(cmd, repo_root=ROOT)


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

    return _review_sync_target_args_impl(
        args,
        resolve_path_from_root=resolve_path_from_root,
        load_config=load_config,
        resolve_docs_dir=resolve_docs_dir,
        resolve_build_targets=resolve_build_targets,
        review_bundle_exists=review_bundle_exists,
    )


def maybe_sync_review_before_build(args: argparse.Namespace, *, source_override: str = "auto") -> None:
    return _maybe_sync_review_before_build_impl(
        args,
        source_override=source_override,
        effective_source=lambda parsed_args: _effective_source(parsed_args, source_override="auto"),
        review_sync_target_args=_review_sync_target_args,
        run_checked=run_checked,
        build_docs_command=build_docs_command,
        sync_review_command=sync_review_command,
    )


def sync_data_command(args: argparse.Namespace) -> list[str]:
    return _sync_data_command_impl(
        args,
        repo_root=ROOT,
        resolve_path_from_root=resolve_path_from_root,
    )


def message_control_dry_run_command(args: argparse.Namespace) -> list[str]:
    return _message_control_dry_run_command_impl(
        args,
        repo_root=ROOT,
        resolve_path_from_root=resolve_path_from_root,
    )


def run_message_control_dry_run(args: argparse.Namespace) -> None:
    config_path = resolve_path_from_root(args.config)
    load_config(config_path)
    result = _resolve_message_control_impl(
        raw_message=str(args.message or ""),
        repo_root=ROOT,
        config_loader=load_config,
        record_id=str(args.record_id or ""),
        document_id=str(args.document_id or ""),
        document_key=str(args.document_key or ""),
        model=str(args.model or ""),
        region=str(args.region or ""),
        lang=str(args.lang or ""),
        build_family=str(args.build_family or ""),
        git_ref=str(args.git_ref or ""),
        version=str(args.version or ""),
        confirmed=bool(args.confirmed),
    )
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False, sort_keys=True))


def run_queue_query(args: argparse.Namespace) -> None:
    return _run_queue_query_impl(args, config_path=resolve_path_from_root(args.config))


def run_queue_resolve_action(args: argparse.Namespace) -> None:
    return _run_queue_resolve_action_impl(args, config_path=resolve_path_from_root(args.config))


def run_queue_execute(args: argparse.Namespace) -> None:
    return _run_queue_execute_impl(
        args,
        config_path=resolve_path_from_root(args.config),
        repo_root=ROOT,
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
    return _run_validate_impl(
        config_path,
        repo_root=ROOT,
        resolve_layout_params_csv=resolve_layout_params_csv,
        run_checked=run_checked,
        data_root=data_root,
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
    return _run_doctor_impl(
        args,
        collect_doctor_findings=_collect_doctor_findings,
        render_finding=_doctor_render_finding,
    )


def run_diff_report(args: argparse.Namespace) -> None:
    return _run_diff_report_impl(
        args,
        resolve_path_from_root=resolve_path_from_root,
        resolve_staging_root=resolve_staging_root,
        default_report_dir_for_tracked_root=lambda config_path, tracked_root: _default_report_dir_for_tracked_root(
            config_path,
            tracked_root,
            base_root=resolve_staging_root(args),
        ),
        run_diff_report_with_paths=run_diff_report_with_paths,
        resolve_diff_report_targets=_resolve_diff_report_targets,
        tracked_root_for_target=lambda config_path, model, region, lang: _tracked_root_for_target(
            config_path,
            model=model,
            region=region,
            lang=lang,
        ),
        report_dir_for_target=lambda model, region, lang, base_root: _report_dir_for_target(
            model,
            region,
            lang=lang,
            base_root=base_root,
        ),
    )


def run_diff_report_with_paths(
    args: argparse.Namespace,
    *,
    tracked_root: Path,
    report_dir: Path,
) -> None:
    return _run_diff_report_with_paths_impl(
        args,
        run_checked=run_checked,
        diff_report_command=lambda parsed_args, current_tracked_root, current_report_dir: _diff_report_command(
            repo_root=ROOT,
            config_path=resolve_path_from_root(parsed_args.config),
            tracked_root=current_tracked_root,
            report_dir=current_report_dir,
            from_ref=parsed_args.from_ref,
            to_ref=parsed_args.to_ref,
            data_root=parsed_args.data_root,
            ignore_initial_adds=parsed_args.ignore_initial_adds,
        ),
        tracked_root=tracked_root,
        report_dir=report_dir,
    )


def run_check(args: argparse.Namespace, *, source_override: str = "auto") -> None:
    return _run_check_impl(
        args,
        source_override=source_override,
        resolve_path_from_root=resolve_path_from_root,
        run_validate=run_validate,
        effective_source=lambda parsed_args: _effective_source(parsed_args, source_override="auto"),
        maybe_sync_review_before_build=maybe_sync_review_before_build,
        run_checked=run_checked,
        build_docs_command=build_docs_command,
        check_docs_command=check_docs_command,
    )


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
    return _run_publish_impl(
        args,
        publish_tracked_root=_publish_tracked_root,
        publish_report_dir=_publish_report_dir,
        run_check=run_check,
        run_diff_report_with_paths=run_diff_report_with_paths,
        run_checked=run_checked,
        build_docs_command=build_docs_command,
        release_manifest_command=release_manifest_command,
    )


def clean_build_artifacts(config_path: Path, *, remove_params_tex: bool = True) -> None:
    return _clean_build_artifacts_impl(
        config_path,
        clean_targets_for_config=clean_targets_for_config,
        review_root_for_config=review_root_for_config,
        resolve_docs_dir=resolve_docs_dir,
        collect_legacy_docs_output_dirs=collect_legacy_docs_output_dirs,
        remove_params_tex=remove_params_tex,
    )


def main(argv: list[str] | None = None) -> int:
    return _run_main_impl(
        argv,
        parse_args=parse_args,
        resolve_path_from_root=resolve_path_from_root,
        dispatch_action=_dispatch_action_impl,
        ensure_supported_staging_action=ensure_supported_staging_action,
        run_validate=run_validate,
        run_doctor=run_doctor,
        run_checked=run_checked,
        build_docs_command=build_docs_command,
        review_bundle_command=review_bundle_command,
        run_check=run_check,
        sync_review_command=sync_review_command,
        sync_data_command=sync_data_command,
        run_message_control_dry_run=run_message_control_dry_run,
        run_queue_query=run_queue_query,
        run_queue_resolve_action=run_queue_resolve_action,
        run_queue_execute=run_queue_execute,
        process_review_start_queue_command=process_review_start_queue_command,
        process_build_queue_command=process_build_queue_command,
        listen_build_queue_command=listen_build_queue_command,
        run_publish=run_publish,
        run_diff_report=run_diff_report,
        release_manifest_command=release_manifest_command,
        clean_build_artifacts=clean_build_artifacts,
        maybe_sync_review_before_build=maybe_sync_review_before_build,
    )


if __name__ == "__main__":
    raise SystemExit(main())
