from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from tools.language_aliases import normalize_language
from tools.utils.path_utils import PathSegments, docs_build_dir_of


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
        return candidate if candidate.is_absolute() else (resolved_config_path.parent / candidate)
    return resolved_config_path.parent / PathSegments.DOCS


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
) -> Path:
    cfg = config_loader(config_path)
    return release_root_for_target(
        repo_root=repo_root,
        config_path=config_path,
        model=model,
        region=region,
        cfg=cfg,
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
) -> Path:
    cfg = config_loader(config_path)
    return release_version_dir_for_target(
        repo_root=repo_root,
        config_path=config_path,
        model=model,
        region=region,
        version=version,
        cfg=cfg,
    )


def publish_release_latest_dir_for_target(
    *,
    repo_root: Path,
    config_path: Path,
    model: str,
    region: str,
    config_loader: Callable[[Path], dict[str, Any]],
    release_latest_dir_for_target: Callable[..., Path],
) -> Path:
    cfg = config_loader(config_path)
    return release_latest_dir_for_target(
        repo_root=repo_root,
        config_path=config_path,
        model=model,
        region=region,
        cfg=cfg,
    )


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


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
    built_html_dir: Path,
    host_config_path: Path,
    model: str,
    region: str,
    version: str,
    publish_release_version_dir_for_target: Callable[..., Path],
    publish_release_latest_dir_for_target: Callable[..., Path],
    copy_tree: Callable[[Path, Path], None],
) -> tuple[Path, Path, Path, Path]:
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
    latest_html_dir = latest_dir / "html"
    copy_tree(built_html_dir, latest_html_dir)
    return staged_word_output_path, staged_pdf_output_path, staged_md_output_path, latest_html_dir


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
    html_dir: Path,
    document_link_url: str,
    queue_record_ids: tuple[str, ...] = (),
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
        "git_ref": git_ref.strip(),
        "doc_phase": "publish",
        "built_at": built_at.isoformat(timespec="seconds"),
        "word_output_path": repo_relative(word_output_path),
        "pdf_output_path": repo_relative(pdf_output_path),
        "md_output_path": repo_relative(md_output_path) if md_output_path is not None else "",
        "html_dir": repo_relative(html_dir),
        "html_index": repo_relative(html_dir / "index.html"),
        "document_link_url": document_link_url.strip(),
        "queue_record_ids": [record_id.strip() for record_id in queue_record_ids if record_id.strip()],
    }
    version_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)
    version_meta_path = version_dir / "publish_meta.json"
    latest_meta_path = latest_dir / "publish_meta.json"
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    version_meta_path.write_text(text, encoding="utf-8")
    latest_meta_path.write_text(text, encoding="utf-8")
    return latest_meta_path
