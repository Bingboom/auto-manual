from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from tools.language_aliases import normalize_language
from tools.utils.path_utils import (
    PathSegments,
    docs_build_dir_of,
    release_manifests_of,
    release_snapshot_of,
)
from tools.web_language_release_evidence import (
    RECEIPT_FILENAME,
    ProjectionCapture,
    require_consistent_captures,
    seal_release_evidence,
    verify_release_evidence,
)


def _stage_markdown_source_sidecars(*, built_md_output_path: Path, staged_md_output_path: Path) -> None:
    source_dir = built_md_output_path.parent
    staged_dir = staged_md_output_path.parent
    source_assets_dir = source_dir / "assets"
    if source_assets_dir.exists() and source_assets_dir.is_dir():
        shutil.copytree(source_assets_dir, staged_dir / "assets", dirs_exist_ok=True)
    for source_name in ("conf.py", "index.md"):
        source_path = source_dir / source_name
        if source_path.exists() and source_path.is_file():
            target_path = staged_dir / source_name
            shutil.copy2(source_path, target_path)
            if source_name == "index.md" and built_md_output_path.stem != staged_md_output_path.stem:
                text = target_path.read_text(encoding="utf-8")
                target_path.write_text(
                    text.replace(built_md_output_path.stem, staged_md_output_path.stem),
                    encoding="utf-8",
                )


def resolve_docs_dir_for_config(
    *,
    config_path: Path,
    repo_root: Path,
    cfg: dict[str, Any] | None = None,
    config_loader: Callable[[Path], dict[str, Any]],
) -> Path:
    resolved_config_path = config_path if config_path.is_absolute() else (repo_root / config_path)
    loaded_cfg = cfg if cfg is not None else config_loader(resolved_config_path)
    paths_cfg_raw = loaded_cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("docs_dir")
    if isinstance(raw, str) and raw.strip():
        candidate = Path(raw.strip())
        return candidate if candidate.is_absolute() else (_config_repo_root(resolved_config_path) / candidate)
    return _config_repo_root(resolved_config_path) / PathSegments.DOCS


def _config_repo_root(config_path: Path) -> Path:
    if config_path.parent.name == PathSegments.CONFIGS:
        return config_path.parent.parent
    return config_path.parent


def resolve_word_output_path_for_target(
    *,
    config_path: Path,
    model: str,
    region: str,
    lang: str | None = None,
    repo_root: Path,
    config_loader: Callable[[Path], dict[str, Any]],
    build_languages: Callable[[dict[str, Any]], list[str]],
    resolve_output_lang: Callable[[dict[str, Any]], str | None],
    build_root_for_target: Callable[..., Path],
    render_build_template: Callable[..., str],
    resolve_output_path: Callable[[Path, str], Path],
) -> Path:
    cfg = config_loader(config_path)
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    docs_dir = resolve_docs_dir_for_config(
        config_path=config_path,
        repo_root=repo_root,
        cfg=cfg,
        config_loader=config_loader,
    )
    supported_langs = build_languages(cfg)
    selected_lang = normalize_language(lang, supported=supported_langs) if (lang or "").strip() else ""
    primary_lang = selected_lang or supported_langs[0]
    output_lang = selected_lang or resolve_output_lang(cfg)
    build_root = build_root_for_target(
        model,
        region,
        lang=output_lang,
        docs_build_dir=docs_build_dir_of(docs_dir),
    )
    word_output_name = render_build_template(
        str(build_cfg.get("word_output", "manual_demo.docx")),
        model=model,
        region=region,
        lang=primary_lang,
    )
    return resolve_output_path(build_root / "word", word_output_name)


def resolve_pdf_output_path_for_target(
    *,
    config_path: Path,
    model: str,
    region: str,
    lang: str | None = None,
    repo_root: Path,
    config_loader: Callable[[Path], dict[str, Any]],
    build_languages: Callable[[dict[str, Any]], list[str]],
    resolve_output_lang: Callable[[dict[str, Any]], str | None],
    build_root_for_target: Callable[..., Path],
    render_build_template: Callable[..., str],
    resolve_output_path: Callable[[Path, str], Path],
) -> Path:
    cfg = config_loader(config_path)
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    docs_dir = resolve_docs_dir_for_config(
        config_path=config_path,
        repo_root=repo_root,
        cfg=cfg,
        config_loader=config_loader,
    )
    supported_langs = build_languages(cfg)
    selected_lang = normalize_language(lang, supported=supported_langs) if (lang or "").strip() else ""
    primary_lang = selected_lang or supported_langs[0]
    output_lang = selected_lang or resolve_output_lang(cfg)
    build_root = build_root_for_target(
        model,
        region,
        lang=output_lang,
        docs_build_dir=docs_build_dir_of(docs_dir),
    )
    pdf_output_name = render_build_template(
        str(build_cfg.get("output_pdf", "manual_demo.pdf")),
        model=model,
        region=region,
        lang=primary_lang,
    )
    return resolve_output_path(build_root / "pdf", pdf_output_name)


def resolve_md_output_path_for_target(
    *,
    config_path: Path,
    model: str,
    region: str,
    lang: str | None = None,
    repo_root: Path,
    config_loader: Callable[[Path], dict[str, Any]],
    build_languages: Callable[[dict[str, Any]], list[str]],
    resolve_output_lang: Callable[[dict[str, Any]], str | None],
    build_root_for_target: Callable[..., Path],
    render_build_template: Callable[..., str],
    resolve_output_path: Callable[[Path, str], Path],
) -> Path:
    cfg = config_loader(config_path)
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    docs_dir = resolve_docs_dir_for_config(
        config_path=config_path,
        repo_root=repo_root,
        cfg=cfg,
        config_loader=config_loader,
    )
    supported_langs = build_languages(cfg)
    selected_lang = normalize_language(lang, supported=supported_langs) if (lang or "").strip() else ""
    primary_lang = selected_lang or supported_langs[0]
    output_lang = selected_lang or resolve_output_lang(cfg)
    build_root = build_root_for_target(
        model,
        region,
        lang=output_lang,
        docs_build_dir=docs_build_dir_of(docs_dir),
    )
    word_output_name = render_build_template(
        str(build_cfg.get("word_output", "manual_demo.docx")),
        model=model,
        region=region,
        lang=primary_lang,
    )
    md_output_template = build_cfg.get("md_output")
    if isinstance(md_output_template, str) and md_output_template.strip():
        md_output_name = render_build_template(
            md_output_template,
            model=model,
            region=region,
            lang=primary_lang,
        )
    else:
        md_output_name = Path(word_output_name).with_suffix(".md").as_posix()
    return resolve_output_path(build_root / "md", md_output_name)


def resolve_html_output_dir_for_target(
    *,
    config_path: Path,
    model: str,
    region: str,
    lang: str | None = None,
    repo_root: Path,
    config_loader: Callable[[Path], dict[str, Any]],
    build_languages: Callable[[dict[str, Any]], list[str]],
    resolve_output_lang: Callable[[dict[str, Any]], str | None],
    build_root_for_target: Callable[..., Path],
) -> Path:
    cfg = config_loader(config_path)
    docs_dir = resolve_docs_dir_for_config(
        config_path=config_path,
        repo_root=repo_root,
        cfg=cfg,
        config_loader=config_loader,
    )
    supported_langs = build_languages(cfg)
    selected_lang = normalize_language(lang, supported=supported_langs) if (lang or "").strip() else ""
    output_lang = selected_lang or resolve_output_lang(cfg)
    build_root = build_root_for_target(
        model,
        region,
        lang=output_lang,
        docs_build_dir=docs_build_dir_of(docs_dir),
    )
    return build_root / "html"


def _versioned_release_output_path(
    output_path: Path,
    *,
    version: str,
    doc_phase: str | None,
    normalize_release_token: Callable[[str], str],
    normalize_workflow_action: Callable[[Any], str | None],
) -> Path:
    normalized_doc_phase = normalize_workflow_action(doc_phase)
    version_token = normalize_release_token(version)
    suffix_parts: list[str] = []
    if normalized_doc_phase == "publish":
        suffix_parts.append("publish")
    elif normalized_doc_phase == "web_publish":
        suffix_parts.append("web_publish")
    if version_token:
        suffix_parts.append(version_token)
    if not suffix_parts:
        return output_path
    return output_path.with_name(
        f"{output_path.stem}_{'_'.join(suffix_parts)}{output_path.suffix}"
    )


def versioned_word_output_path(
    word_output_path: Path,
    *,
    version: str,
    doc_phase: str | None,
    normalize_release_token: Callable[[str], str],
    normalize_workflow_action: Callable[[Any], str | None],
) -> Path:
    return _versioned_release_output_path(
        word_output_path,
        version=version,
        doc_phase=doc_phase,
        normalize_release_token=normalize_release_token,
        normalize_workflow_action=normalize_workflow_action,
    )


def versioned_pdf_output_path(
    pdf_output_path: Path,
    *,
    version: str,
    doc_phase: str | None,
    normalize_release_token: Callable[[str], str],
    normalize_workflow_action: Callable[[Any], str | None],
) -> Path:
    return _versioned_release_output_path(
        pdf_output_path,
        version=version,
        doc_phase=doc_phase,
        normalize_release_token=normalize_release_token,
        normalize_workflow_action=normalize_workflow_action,
    )


def versioned_md_output_path(
    md_output_path: Path,
    *,
    version: str,
    doc_phase: str | None,
    normalize_release_token: Callable[[str], str],
    normalize_workflow_action: Callable[[Any], str | None],
) -> Path:
    return _versioned_release_output_path(
        md_output_path,
        version=version,
        doc_phase=doc_phase,
        normalize_release_token=normalize_release_token,
        normalize_workflow_action=normalize_workflow_action,
    )


def config_path_in_repo_root(config_path: Path, *, repo_root: Path) -> Path:
    if config_path.parent.name == PathSegments.CONFIGS:
        return repo_root / PathSegments.CONFIGS / config_path.name
    if not config_path.is_absolute() and config_path.parent != Path("."):
        return repo_root / config_path
    return repo_root / config_path.name


def repo_relative(path: Path, *, repo_root: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix()
    except ValueError:
        return path.resolve(strict=False).as_posix()


def publish_release_root_for_target(
    *,
    repo_root: Path,
    config_path: Path,
    model: str,
    region: str,
    config_loader: Callable[[Path], dict[str, Any]],
    release_root_for_target: Callable[..., Path],
    lang: str | None = None,
) -> Path:
    cfg = config_loader(config_path)
    return release_root_for_target(
        repo_root=repo_root,
        config_path=config_path,
        model=model,
        region=region,
        cfg=cfg,
        lang=lang,
    )


def publish_release_version_dir_for_target(
    *,
    repo_root: Path,
    config_path: Path,
    model: str,
    region: str,
    version: str,
    config_loader: Callable[[Path], dict[str, Any]],
    release_version_dir_for_target: Callable[..., Path],
    lang: str | None = None,
) -> Path:
    cfg = config_loader(config_path)
    return release_version_dir_for_target(
        repo_root=repo_root,
        config_path=config_path,
        model=model,
        region=region,
        version=version,
        cfg=cfg,
        lang=lang,
    )


def publish_release_latest_dir_for_target(
    *,
    repo_root: Path,
    config_path: Path,
    model: str,
    region: str,
    config_loader: Callable[[Path], dict[str, Any]],
    release_latest_dir_for_target: Callable[..., Path],
    lang: str | None = None,
) -> Path:
    cfg = config_loader(config_path)
    return release_latest_dir_for_target(
        repo_root=repo_root,
        config_path=config_path,
        model=model,
        region=region,
        cfg=cfg,
        lang=lang,
    )


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _files_by_relative_path(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"release traceability cannot stage symlink: {path}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def copy_immutable_tree(src: Path, dst: Path) -> None:
    if src.is_symlink() or not src.is_dir():
        raise RuntimeError(f"release traceability directory was not created: {src}")
    source_files = _files_by_relative_path(src)
    if dst.exists():
        if dst.is_symlink() or not dst.is_dir() or _files_by_relative_path(dst) != source_files:
            raise RuntimeError(f"release traceability is immutable and destination differs: {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    temporary_parent = Path(tempfile.mkdtemp(prefix=f".{dst.name}.", dir=dst.parent))
    temporary_tree = temporary_parent / "tree"
    try:
        shutil.copytree(src, temporary_tree)
        if _files_by_relative_path(temporary_tree) != source_files:
            raise RuntimeError(f"release traceability copy verification failed: {dst}")
        try:
            temporary_tree.replace(dst)
        except OSError:
            if dst.is_symlink() or not dst.is_dir() or _files_by_relative_path(dst) != source_files:
                raise RuntimeError(
                    f"release traceability is immutable and destination differs: {dst}"
                ) from None
    finally:
        shutil.rmtree(temporary_parent, ignore_errors=True)


def copy_immutable_files(src_dir: Path, dst_dir: Path) -> None:
    if not src_dir.is_dir():
        raise RuntimeError(f"release manifest directory was not created: {src_dir}")
    source_files = [path for path in sorted(src_dir.iterdir()) if path.is_file()]
    if not source_files:
        raise RuntimeError(f"release manifest directory is empty: {src_dir}")
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src in source_files:
        dst = dst_dir / src.name
        if dst.exists():
            source_sha = hashlib.sha256(src.read_bytes()).digest()
            destination_sha = hashlib.sha256(dst.read_bytes()).digest() if dst.is_file() else b""
            if destination_sha != source_sha:
                raise RuntimeError(f"release manifest is immutable and destination differs: {dst}")
            continue
        shutil.copy2(src, dst)


def stage_draft_word_output_to_host_repo(
    *,
    built_word_output_path: Path,
    host_config_path: Path,
    model: str,
    region: str,
    version: str,
    doc_phase: str | None,
    lang: str | None = None,
    resolve_word_output_path_for_target: Callable[..., Path],
    versioned_word_output_path: Callable[..., Path],
) -> Path:
    host_output_path = resolve_word_output_path_for_target(
        config_path=host_config_path,
        model=model,
        region=region,
        lang=lang,
    )
    staged_output_path = versioned_word_output_path(
        host_output_path,
        version=version,
        doc_phase=doc_phase,
    )
    staged_output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built_word_output_path, staged_output_path)
    return staged_output_path


def stage_draft_md_output_to_host_repo(
    *,
    built_md_output_path: Path,
    host_config_path: Path,
    model: str,
    region: str,
    version: str,
    doc_phase: str | None,
    lang: str | None = None,
    resolve_md_output_path_for_target: Callable[..., Path],
    versioned_md_output_path: Callable[..., Path],
) -> Path:
    host_output_path = resolve_md_output_path_for_target(
        config_path=host_config_path,
        model=model,
        region=region,
        lang=lang,
    )
    staged_output_path = versioned_md_output_path(
        host_output_path,
        version=version,
        doc_phase=doc_phase,
    )
    staged_output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built_md_output_path, staged_output_path)
    _stage_markdown_source_sidecars(
        built_md_output_path=built_md_output_path,
        staged_md_output_path=staged_output_path,
    )
    return staged_output_path


def stage_publish_assets_to_host_repo(
    *,
    built_word_output_path: Path,
    built_pdf_output_path: Path,
    built_md_output_path: Path,
    built_idml_output_path: Path,
    built_latex_dir: Path,
    host_config_path: Path,
    model: str,
    region: str,
    version: str,
    built_release_snapshot_dir: Path,
    built_release_manifests_dir: Path,
    publish_release_version_dir_for_target: Callable[..., Path],
    publish_release_latest_dir_for_target: Callable[..., Path],
    copy_tree: Callable[[Path, Path], None],
) -> tuple[Path, Path, Path, Path, Path]:
    version_dir = publish_release_version_dir_for_target(
        config_path=host_config_path,
        model=model,
        region=region,
        version=version,
    )
    latest_dir = publish_release_latest_dir_for_target(
        config_path=host_config_path,
        model=model,
        region=region,
    )
    version_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)
    staged_word_output_path = version_dir / built_word_output_path.name
    shutil.copy2(built_word_output_path, staged_word_output_path)
    staged_pdf_output_path = version_dir / built_pdf_output_path.name
    shutil.copy2(built_pdf_output_path, staged_pdf_output_path)
    staged_md_output_path = version_dir / built_md_output_path.name
    shutil.copy2(built_md_output_path, staged_md_output_path)
    _stage_markdown_source_sidecars(
        built_md_output_path=built_md_output_path,
        staged_md_output_path=staged_md_output_path,
    )
    staged_idml_output_path = version_dir / built_idml_output_path.name
    shutil.copy2(built_idml_output_path, staged_idml_output_path)
    staged_latex_dir = version_dir / PathSegments.LATEX
    copy_tree(built_latex_dir, staged_latex_dir)
    copy_immutable_tree(
        built_release_snapshot_dir,
        release_snapshot_of(version_dir),
    )
    copy_immutable_files(
        built_release_manifests_dir,
        release_manifests_of(version_dir.parent.parent),
    )
    return (
        staged_word_output_path,
        staged_pdf_output_path,
        staged_md_output_path,
        staged_latex_dir,
        staged_idml_output_path,
    )


def _validate_web_publish_sources(*, built_md_output_path: Path, built_html_dir: Path) -> None:
    markdown_dir = built_md_output_path.parent
    if markdown_dir.is_symlink() or built_md_output_path.is_symlink():
        raise RuntimeError(f"Web Publish cannot stage symlink: {built_md_output_path}")
    if not built_md_output_path.is_file():
        raise RuntimeError(f"Web Publish Markdown output was not created: {built_md_output_path}")
    for source_name in ("conf.py", "index.md"):
        source_path = markdown_dir / source_name
        if source_path.is_symlink():
            raise RuntimeError(f"Web Publish cannot stage symlink: {source_path}")
        if source_path.exists() and not source_path.is_file():
            raise RuntimeError(f"Web Publish sidecar must be a file: {source_path}")
    source_assets_dir = markdown_dir / "assets"
    if source_assets_dir.is_symlink():
        raise RuntimeError(f"Web Publish cannot stage symlink: {source_assets_dir}")
    if source_assets_dir.exists():
        if not source_assets_dir.is_dir():
            raise RuntimeError(f"Web Publish assets must be a directory: {source_assets_dir}")
        _files_by_relative_path(source_assets_dir)
    if built_html_dir.is_symlink() or not built_html_dir.is_dir():
        raise RuntimeError(f"Web Publish HTML output must be a real directory: {built_html_dir}")
    # Validate even the excluded Sphinx cache so no input symlink is silently
    # dereferenced while the release candidate is assembled.
    _files_by_relative_path(built_html_dir)


def stage_web_publish_assets_to_host_repo(
    *,
    built_md_output_path: Path,
    built_html_dir: Path,
    host_config_path: Path,
    model: str,
    region: str,
    version: str,
    publish_release_version_dir_for_target: Callable[..., Path],
    projection_captures: tuple[ProjectionCapture, ...] = (),
    git_ref: str = "",
    target_lang: str | None = None,
) -> tuple[Path, Path]:
    if bool((target_lang or "").strip()) != bool(projection_captures):
        raise RuntimeError(
            "Web Publish explicit target_lang and projection captures must be provided together"
        )
    checked_captures: tuple[ProjectionCapture, ...] = ()
    if projection_captures:
        checked_captures = require_consistent_captures(projection_captures)
        capture = checked_captures[-1]
        expected_identity = (model, region, normalize_language(target_lang))
        actual_identity = (capture.model, capture.region, capture.language)
        if actual_identity != expected_identity:
            raise RuntimeError(
                "Web language projection capture identity mismatch before staging: "
                f"expected {expected_identity}, got {actual_identity}"
            )
    _validate_web_publish_sources(
        built_md_output_path=built_md_output_path,
        built_html_dir=built_html_dir,
    )
    version_dir = publish_release_version_dir_for_target(
        config_path=host_config_path,
        model=model,
        region=region,
        version=version,
        lang=target_lang,
    )
    if version_dir.is_symlink():
        raise RuntimeError(f"Web Publish version directory must not be a symlink: {version_dir}")
    web_dir = version_dir / PathSegments.WEB
    if web_dir.is_symlink():
        raise RuntimeError(f"Web Publish destination must not be a symlink: {web_dir}")
    version_dir.mkdir(parents=True, exist_ok=True)
    candidate_parent = Path(tempfile.mkdtemp(prefix=".web-candidate.", dir=version_dir))
    candidate_web_dir = candidate_parent / PathSegments.WEB
    try:
        md_dir = candidate_web_dir / PathSegments.MD
        html_dir = candidate_web_dir / PathSegments.HTML
        md_dir.mkdir(parents=True, exist_ok=True)
        candidate_md_output_path = md_dir / built_md_output_path.name
        shutil.copy2(built_md_output_path, candidate_md_output_path)
        _stage_markdown_source_sidecars(
            built_md_output_path=built_md_output_path,
            staged_md_output_path=candidate_md_output_path,
        )
        # Sphinx's .doctrees directory is a local incremental-build cache, not
        # shipped Web content. Everything else under the HTML output is sealed.
        shutil.copytree(
            built_html_dir,
            html_dir,
            ignore=shutil.ignore_patterns(".doctrees"),
        )
        if checked_captures:
            seal_release_evidence(
                captures=checked_captures,
                markdown_dir=md_dir,
                markdown_name=candidate_md_output_path.name,
                html_dir=html_dir,
                evidence_dir=candidate_web_dir / PathSegments.EVIDENCE,
                version=version,
                git_ref=git_ref,
            )
        copy_immutable_tree(candidate_web_dir, web_dir)
    finally:
        shutil.rmtree(candidate_parent, ignore_errors=True)
    return (
        web_dir / PathSegments.MD / built_md_output_path.name,
        web_dir / PathSegments.HTML,
    )


def _atomic_replace_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise RuntimeError(f"Web Publish metadata destination must not be a symlink: {path}")
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return
    file_descriptor, raw_temporary_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(raw_temporary_path)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _write_immutable_text(path: Path, text: str) -> str:
    if path.is_symlink():
        raise RuntimeError(f"Web Publish metadata destination must not be a symlink: {path}")
    if path.exists():
        if not path.is_file():
            raise RuntimeError(f"Web Publish metadata destination must be a file: {path}")
        existing = path.read_text(encoding="utf-8")
        if existing != text:
            raise RuntimeError(f"Web Publish metadata is immutable and destination differs: {path}")
        return existing
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, raw_temporary_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(raw_temporary_path)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError:
            if path.is_symlink():
                raise RuntimeError(
                    f"Web Publish metadata destination must not be a symlink: {path}"
                ) from None
            existing = path.read_text(encoding="utf-8") if path.is_file() else ""
            if existing != text:
                raise RuntimeError(
                    f"Web Publish metadata is immutable and destination differs: {path}"
                ) from None
            return existing
        return text
    finally:
        temporary_path.unlink(missing_ok=True)


def write_publish_release_metadata(
    *,
    config_path: Path,
    model: str,
    region: str,
    version: str,
    git_ref: str,
    built_at: datetime,
    word_output_path: Path,
    pdf_output_path: Path,
    md_output_path: Path | None = None,
    handoff_package_path: Path | None = None,
    latex_dir: Path | None = None,
    html_dir: Path | None,
    document_link_url: str,
    queue_record_ids: tuple[str, ...] = (),
    release_tag: str = "",
    publish_release_version_dir_for_target: Callable[..., Path],
    publish_release_latest_dir_for_target: Callable[..., Path],
    release_lang_for_config: Callable[[Path], str | None],
    repo_relative: Callable[[Path], str],
) -> Path:
    version_dir = publish_release_version_dir_for_target(
        config_path=config_path,
        model=model,
        region=region,
        version=version,
    )
    latest_dir = publish_release_latest_dir_for_target(
        config_path=config_path,
        model=model,
        region=region,
    )
    payload = {
        "model": model,
        "region": region,
        "lang": release_lang_for_config(config_path),
        "version": version,
        "release_tag": release_tag,
        "git_ref": git_ref.strip(),
        "doc_phase": "publish",
        "built_at": built_at.isoformat(timespec="seconds"),
        "word_output_path": repo_relative(word_output_path),
        "pdf_output_path": repo_relative(pdf_output_path),
        "md_output_path": repo_relative(md_output_path) if md_output_path is not None else "",
        # The InDesign handoff package (IDML + Links/ + font manifest) is
        # already staged next to these outputs; name it so the release
        # record points at the print deliverable, not only the PDF.
        "handoff_package_path": (
            repo_relative(handoff_package_path) if handoff_package_path is not None else ""
        ),
        "latex_dir": repo_relative(latex_dir) if latex_dir is not None else "",
        "document_link_url": document_link_url.strip(),
        "queue_record_ids": [record_id.strip() for record_id in queue_record_ids if record_id.strip()],
    }
    if html_dir is not None:
        payload["html_dir"] = repo_relative(html_dir)
        payload["html_index"] = repo_relative(html_dir / "index.html")
    version_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)
    version_meta_path = version_dir / "publish_meta.json"
    latest_meta_path = latest_dir / "publish_meta.json"
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    version_meta_path.write_text(text, encoding="utf-8")
    latest_meta_path.write_text(text, encoding="utf-8")
    return latest_meta_path


def write_web_publish_metadata(
    *,
    config_path: Path,
    model: str,
    region: str,
    version: str,
    git_ref: str,
    built_at: datetime,
    md_output_path: Path,
    html_dir: Path,
    queue_record_ids: tuple[str, ...] = (),
    target_lang: str | None = None,
    language_projection_evidence_path: Path | None = None,
    publish_release_version_dir_for_target: Callable[..., Path],
    publish_release_latest_dir_for_target: Callable[..., Path],
    release_lang_for_config: Callable[[Path], str | None],
    repo_relative: Callable[[Path], str],
) -> Path:
    has_target_lang = bool((target_lang or "").strip())
    has_evidence = language_projection_evidence_path is not None
    if has_target_lang != has_evidence:
        raise RuntimeError(
            "Web Publish explicit target_lang and language projection evidence must be provided together"
        )
    version_dir = publish_release_version_dir_for_target(
        config_path=config_path,
        model=model,
        region=region,
        version=version,
        lang=target_lang,
    )
    latest_dir = publish_release_latest_dir_for_target(
        config_path=config_path,
        model=model,
        region=region,
        lang=target_lang,
    )
    if version_dir.is_symlink():
        raise RuntimeError(f"Web Publish version directory must not be a symlink: {version_dir}")
    if latest_dir.is_symlink():
        raise RuntimeError(f"Web Publish latest directory must not be a symlink: {latest_dir}")
    latest_web_dir = latest_dir / PathSegments.WEB
    if latest_web_dir.is_symlink():
        raise RuntimeError(f"Web Publish latest Web directory must not be a symlink: {latest_web_dir}")
    release_lang = (target_lang or "").strip() or release_lang_for_config(config_path)
    payload = {
        "schema_version": "auto-manual-web-publish/v1",
        "model": model,
        "region": region,
        "lang": release_lang,
        "version": version,
        "git_ref": git_ref.strip(),
        "workflow_action": "Web Publish",
        "built_at": built_at.isoformat(timespec="seconds"),
        "md_output_path": repo_relative(md_output_path),
        "html_dir": repo_relative(html_dir),
        "html_index": repo_relative(html_dir / "index.html"),
        "queue_record_ids": [record_id.strip() for record_id in queue_record_ids if record_id.strip()],
    }
    if language_projection_evidence_path is not None:
        expected_md_dir = version_dir / PathSegments.WEB / PathSegments.MD
        expected_html_dir = version_dir / PathSegments.WEB / PathSegments.HTML
        if md_output_path.parent.resolve(strict=False) != expected_md_dir.resolve(strict=False):
            raise RuntimeError(
                "Web Publish Markdown is outside the versioned Web directory: "
                f"{md_output_path}"
            )
        if html_dir.resolve(strict=False) != expected_html_dir.resolve(strict=False):
            raise RuntimeError(
                "Web Publish HTML is outside the versioned Web directory: "
                f"{html_dir}"
            )
        expected_evidence_path = (
            version_dir
            / PathSegments.WEB
            / PathSegments.EVIDENCE
            / RECEIPT_FILENAME
        )
        if language_projection_evidence_path.resolve(strict=False) != expected_evidence_path.resolve(strict=False):
            raise RuntimeError(
                "Web language release evidence is outside the versioned Web evidence directory: "
                f"{language_projection_evidence_path}"
            )
        evidence = verify_release_evidence(
            language_projection_evidence_path,
            expected_sha256=None,
            model=model,
            region=region,
            language=release_lang,
            version=version,
            git_ref=git_ref,
            markdown_dir=md_output_path.parent,
            markdown_name=md_output_path.name,
            html_dir=html_dir,
        )
        payload.update(
            language_scope="single",
            language_projection_evidence_path=repo_relative(evidence.path),
            language_projection_evidence_sha256=evidence.sha256,
        )
    version_metadata_path = version_dir / "web_publish_meta.json"
    latest_metadata_path = latest_web_dir / PathSegments.PUBLISH_META_JSON
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if version_metadata_path.is_symlink():
        raise RuntimeError(
            f"Web Publish metadata destination must not be a symlink: {version_metadata_path}"
        )
    if version_metadata_path.exists():
        existing_payload = json.loads(version_metadata_path.read_text(encoding="utf-8"))
        candidate_without_time = {key: value for key, value in payload.items() if key != "built_at"}
        existing_without_time = {
            key: value for key, value in existing_payload.items() if key != "built_at"
        } if isinstance(existing_payload, dict) else {}
        if existing_without_time != candidate_without_time:
            raise RuntimeError(
                f"Web Publish metadata is immutable and destination differs: {version_metadata_path}"
            )
        text = version_metadata_path.read_text(encoding="utf-8")
    _write_immutable_text(version_metadata_path, text)
    _atomic_replace_text(latest_metadata_path, text)
    return latest_metadata_path
