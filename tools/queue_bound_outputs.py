from __future__ import annotations

from pathlib import Path
from typing import Any

_DEFAULT_ROOT = Path(__file__).resolve().parents[1]
_repo_root_provider = lambda: _DEFAULT_ROOT

from tools.build_docs import build_root_for_target, render_build_template, resolve_output_path  # noqa: E402
from tools.document_link_actions import normalize_workflow_action  # noqa: E402
from tools.queue_config_resolution import build_languages as _build_languages  # noqa: E402
from tools.queue_outputs import (  # noqa: E402
    copy_tree as _copy_tree_impl,
    publish_release_latest_dir_for_target as _publish_release_latest_dir_for_target_impl,
    publish_release_root_for_target as _publish_release_root_for_target_impl,
    publish_release_version_dir_for_target as _publish_release_version_dir_for_target_impl,
    repo_relative as _repo_relative_impl,
    resolve_docs_dir_for_config as _resolve_docs_dir_for_config_impl,
    resolve_html_output_dir_for_target as _resolve_html_output_dir_for_target_impl,
    resolve_md_output_path_for_target as _resolve_md_output_path_for_target_impl,
    resolve_pdf_output_path_for_target as _resolve_pdf_output_path_for_target_impl,
    resolve_word_output_path_for_target as _resolve_word_output_path_for_target_impl,
    stage_draft_md_output_to_host_repo as _stage_draft_md_output_to_host_repo_impl,
    stage_draft_word_output_to_host_repo as _stage_draft_word_output_to_host_repo_impl,
    stage_publish_assets_to_host_repo as _stage_publish_assets_to_host_repo_impl,
    versioned_md_output_path as _versioned_md_output_path_impl,
    versioned_pdf_output_path as _versioned_pdf_output_path_impl,
    versioned_word_output_path as _versioned_word_output_path_impl,
    write_publish_release_metadata as _write_publish_release_metadata_impl,
)
from tools.release_contract import (  # noqa: E402
    normalize_release_token,
    release_lang_for_config,
    release_latest_dir_for_target,
    release_root_for_target,
    release_version_dir_for_target,
)
from tools.sync_data import load_config  # noqa: E402
from tools.utils.targets import resolve_output_lang  # noqa: E402


def set_repo_root_provider(provider: Any) -> None:
    global _repo_root_provider
    _repo_root_provider = provider


def _repo_root() -> Path:
    return Path(_repo_root_provider())


def resolve_docs_dir_for_config(config_path: Path, cfg: dict[str, Any] | None = None) -> Path:
    return _resolve_docs_dir_for_config_impl(
        config_path=config_path,
        repo_root=_repo_root(),
        cfg=cfg,
        config_loader=load_config,
    )


def resolve_word_output_path_for_target(*, config_path: Path, model: str, region: str) -> Path:
    return _resolve_word_output_path_for_target_impl(
        config_path=config_path,
        model=model,
        region=region,
        repo_root=_repo_root(),
        config_loader=load_config,
        build_languages=_build_languages,
        resolve_output_lang=resolve_output_lang,
        build_root_for_target=build_root_for_target,
        render_build_template=render_build_template,
        resolve_output_path=resolve_output_path,
    )


def resolve_pdf_output_path_for_target(*, config_path: Path, model: str, region: str) -> Path:
    return _resolve_pdf_output_path_for_target_impl(
        config_path=config_path,
        model=model,
        region=region,
        repo_root=_repo_root(),
        config_loader=load_config,
        build_languages=_build_languages,
        resolve_output_lang=resolve_output_lang,
        build_root_for_target=build_root_for_target,
        render_build_template=render_build_template,
        resolve_output_path=resolve_output_path,
    )


def resolve_md_output_path_for_target(*, config_path: Path, model: str, region: str) -> Path:
    return _resolve_md_output_path_for_target_impl(
        config_path=config_path,
        model=model,
        region=region,
        repo_root=_repo_root(),
        config_loader=load_config,
        build_languages=_build_languages,
        resolve_output_lang=resolve_output_lang,
        build_root_for_target=build_root_for_target,
        render_build_template=render_build_template,
        resolve_output_path=resolve_output_path,
    )


def resolve_html_output_dir_for_target(*, config_path: Path, model: str, region: str) -> Path:
    return _resolve_html_output_dir_for_target_impl(
        config_path=config_path,
        model=model,
        region=region,
        repo_root=_repo_root(),
        config_loader=load_config,
        resolve_output_lang=resolve_output_lang,
        build_root_for_target=build_root_for_target,
    )


def versioned_word_output_path(word_output_path: Path, *, version: str, doc_phase: str | None = None) -> Path:
    return _versioned_word_output_path_impl(
        word_output_path,
        version=version,
        doc_phase=doc_phase,
        normalize_release_token=normalize_release_token,
        normalize_workflow_action=normalize_workflow_action,
    )


def versioned_pdf_output_path(pdf_output_path: Path, *, version: str, doc_phase: str | None = None) -> Path:
    return _versioned_pdf_output_path_impl(
        pdf_output_path,
        version=version,
        doc_phase=doc_phase,
        normalize_release_token=normalize_release_token,
        normalize_workflow_action=normalize_workflow_action,
    )


def versioned_md_output_path(md_output_path: Path, *, version: str, doc_phase: str | None = None) -> Path:
    return _versioned_md_output_path_impl(
        md_output_path,
        version=version,
        doc_phase=doc_phase,
        normalize_release_token=normalize_release_token,
        normalize_workflow_action=normalize_workflow_action,
    )


def repo_relative(path: Path) -> str:
    return _repo_relative_impl(path, repo_root=_repo_root())


def publish_release_root_for_target(*, config_path: Path, model: str, region: str) -> Path:
    return _publish_release_root_for_target_impl(
        repo_root=_repo_root(),
        config_path=config_path,
        model=model,
        region=region,
        config_loader=load_config,
        release_root_for_target=release_root_for_target,
    )


def publish_release_version_dir_for_target(*, config_path: Path, model: str, region: str, version: str) -> Path:
    return _publish_release_version_dir_for_target_impl(
        repo_root=_repo_root(),
        config_path=config_path,
        model=model,
        region=region,
        version=version,
        config_loader=load_config,
        release_version_dir_for_target=release_version_dir_for_target,
    )


def publish_release_latest_dir_for_target(*, config_path: Path, model: str, region: str) -> Path:
    return _publish_release_latest_dir_for_target_impl(
        repo_root=_repo_root(),
        config_path=config_path,
        model=model,
        region=region,
        config_loader=load_config,
        release_latest_dir_for_target=release_latest_dir_for_target,
    )


def stage_draft_word_output_to_host_repo(
    *,
    built_word_output_path: Path,
    host_config_path: Path,
    model: str,
    region: str,
    version: str,
    doc_phase: str | None,
) -> Path:
    return _stage_draft_word_output_to_host_repo_impl(
        built_word_output_path=built_word_output_path,
        host_config_path=host_config_path,
        model=model,
        region=region,
        version=version,
        doc_phase=doc_phase,
        resolve_word_output_path_for_target=resolve_word_output_path_for_target,
        versioned_word_output_path=versioned_word_output_path,
    )


def stage_draft_md_output_to_host_repo(
    *,
    built_md_output_path: Path,
    host_config_path: Path,
    model: str,
    region: str,
    version: str,
    doc_phase: str | None,
) -> Path:
    return _stage_draft_md_output_to_host_repo_impl(
        built_md_output_path=built_md_output_path,
        host_config_path=host_config_path,
        model=model,
        region=region,
        version=version,
        doc_phase=doc_phase,
        resolve_md_output_path_for_target=resolve_md_output_path_for_target,
        versioned_md_output_path=versioned_md_output_path,
    )


def stage_publish_assets_to_host_repo(
    *,
    built_word_output_path: Path,
    built_pdf_output_path: Path,
    built_md_output_path: Path,
    built_html_dir: Path,
    host_config_path: Path,
    model: str,
    region: str,
    version: str,
) -> tuple[Path, Path, Path, Path]:
    return _stage_publish_assets_to_host_repo_impl(
        built_word_output_path=built_word_output_path,
        built_pdf_output_path=built_pdf_output_path,
        built_md_output_path=built_md_output_path,
        built_html_dir=built_html_dir,
        host_config_path=host_config_path,
        model=model,
        region=region,
        version=version,
        publish_release_version_dir_for_target=publish_release_version_dir_for_target,
        publish_release_latest_dir_for_target=publish_release_latest_dir_for_target,
        copy_tree=_copy_tree_impl,
    )


def write_publish_release_metadata(
    *,
    config_path: Path,
    model: str,
    region: str,
    version: str,
    git_ref: str,
    built_at: Any,
    word_output_path: Path,
    pdf_output_path: Path,
    md_output_path: Path | None = None,
    html_dir: Path,
    document_link_url: str,
    queue_record_ids: tuple[str, ...] = (),
) -> Path:
    return _write_publish_release_metadata_impl(
        config_path=config_path,
        model=model,
        region=region,
        version=version,
        git_ref=git_ref,
        built_at=built_at,
        word_output_path=word_output_path,
        pdf_output_path=pdf_output_path,
        md_output_path=md_output_path,
        html_dir=html_dir,
        document_link_url=document_link_url,
        queue_record_ids=queue_record_ids,
        publish_release_version_dir_for_target=publish_release_version_dir_for_target,
        publish_release_latest_dir_for_target=publish_release_latest_dir_for_target,
        release_lang_for_config=release_lang_for_config,
        repo_relative=repo_relative,
    )
