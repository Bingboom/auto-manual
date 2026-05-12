from __future__ import annotations

from dataclasses import dataclass
import shutil
import sys
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class BuiltDocumentOutputs:
    word_output_path: Path
    upload_output_path: Path
    md_output_path: Path | None = None
    pdf_output_path: Path | None = None
    html_output_dir: Path | None = None


def build_py_target_command(
    *,
    repo_root: Path,
    action: str,
    config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
    source: str | None = None,
    no_clean: bool = False,
) -> list[str]:
    cmd = [
        sys.executable,
        str(repo_root / "build.py"),
        action,
        "--config",
        str(config_path),
        "--model",
        model,
        "--region",
        region,
    ]
    if source:
        cmd += ["--source", source]
    if no_clean:
        cmd.append("--no-clean")
    if data_root:
        cmd += ["--data-root", data_root]
    return cmd


def build_py_sync_data_command(*, repo_root: Path, config_path: Path, data_root: str | None) -> list[str]:
    cmd = [
        sys.executable,
        str(repo_root / "build.py"),
        "sync-data",
        "--config",
        str(config_path),
    ]
    if data_root:
        cmd += ["--data-root", data_root]
    return cmd


def sync_phase2_snapshot_before_queue(
    *,
    repo_root: Path,
    config_path: Path,
    data_root: str | None,
    run_command: Callable[[list[str]], None],
    build_py_sync_data_command: Callable[..., list[str]],
) -> None:
    run_command(
        build_py_sync_data_command(
            repo_root=repo_root,
            config_path=config_path,
            data_root=data_root,
        )
    )


def _remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()


def _replace_path(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    _remove_path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return True


def _worktree_data_root(
    data_root: str,
    *,
    repo_root: Path,
    build_workspace: Path,
) -> tuple[Path, Path]:
    data_root_path = Path(data_root)
    if data_root_path.is_absolute():
        try:
            relative_data_root = data_root_path.resolve(strict=False).relative_to(repo_root.resolve(strict=False))
        except ValueError:
            relative_data_root = Path("data") / data_root_path.name
        return data_root_path, build_workspace / relative_data_root
    return repo_root / data_root_path, build_workspace / data_root_path


def build_document_for_task(
    *,
    repo_root: Path,
    config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
    doc_phase: str | None,
    version: str = "",
    git_ref: str = "",
    normalize_workflow_action: Callable[[str | None], str | None],
    prepare_git_ref_worktree: Callable[[str], Path],
    remove_worktree: Callable[[Path], None],
    config_path_in_repo_root: Callable[..., Path],
    run_command: Callable[..., None],
    build_py_target_command: Callable[..., list[str]],
    resolve_word_output_path_for_target: Callable[..., Path],
    resolve_pdf_output_path_for_target: Callable[..., Path],
    resolve_md_output_path_for_target: Callable[..., Path],
    versioned_pdf_output_path: Callable[..., Path],
    versioned_word_output_path: Callable[..., Path],
    versioned_md_output_path: Callable[..., Path],
    resolve_html_output_dir_for_target: Callable[..., Path],
    stage_publish_assets_to_host_repo: Callable[..., tuple[Path, Path, Path, Path]],
    stage_draft_word_output_to_host_repo: Callable[..., Path],
    stage_draft_md_output_to_host_repo: Callable[..., Path],
) -> BuiltDocumentOutputs:
    normalized_doc_phase = normalize_workflow_action(doc_phase)
    effective_repo_root = repo_root
    effective_config_path = config_path
    effective_data_root = data_root
    build_workspace: Path | None = None
    review_workspace: Path | None = None
    if git_ref.strip():
        build_workspace = prepare_git_ref_worktree("main")
        review_ref = git_ref.strip()
        review_workspace = build_workspace if review_ref == "main" else prepare_git_ref_worktree(review_ref)
        if not _replace_path(
            review_workspace / "docs" / "_review",
            build_workspace / "docs" / "_review",
        ):
            raise RuntimeError(
                f"Git_ref {review_ref} does not contain docs/_review; queue builds must render review content from the review branch."
            )
        if data_root:
            source_data_root, workspace_data_root = _worktree_data_root(
                data_root,
                repo_root=repo_root,
                build_workspace=build_workspace,
            )
            _replace_path(source_data_root, workspace_data_root)
            effective_data_root = str(workspace_data_root)
        effective_repo_root = build_workspace
        effective_config_path = config_path_in_repo_root(config_path, repo_root=build_workspace)

    try:
        if normalized_doc_phase == "draft":
            run_command(
                build_py_target_command(
                    repo_root=effective_repo_root,
                    action="check",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=effective_data_root,
                    source="review",
                ),
                cwd=effective_repo_root,
            )
            run_command(
                build_py_target_command(
                    repo_root=effective_repo_root,
                    action="word",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=effective_data_root,
                    source="review",
                    no_clean=True,
                ),
                cwd=effective_repo_root,
            )
            run_command(
                build_py_target_command(
                    repo_root=effective_repo_root,
                    action="md",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=effective_data_root,
                    source="review",
                    no_clean=True,
                ),
                cwd=effective_repo_root,
            )
        elif normalized_doc_phase == "publish":
            run_command(
                build_py_target_command(
                    repo_root=effective_repo_root,
                    action="publish",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=effective_data_root,
                ),
                cwd=effective_repo_root,
            )
            run_command(
                build_py_target_command(
                    repo_root=effective_repo_root,
                    action="html",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=effective_data_root,
                    source="review",
                    no_clean=True,
                ),
                cwd=effective_repo_root,
            )
        else:
            run_command(
                build_py_target_command(
                    repo_root=effective_repo_root,
                    action="check",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=effective_data_root,
                ),
                cwd=effective_repo_root,
            )
            run_command(
                build_py_target_command(
                    repo_root=effective_repo_root,
                    action="word",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=effective_data_root,
                    no_clean=True,
                ),
                cwd=effective_repo_root,
            )

        word_output_path = resolve_word_output_path_for_target(
            config_path=effective_config_path,
            model=model,
            region=region,
        )
        if not word_output_path.exists():
            raise RuntimeError(f"Word output was not created: {word_output_path}")
        versioned_path = versioned_word_output_path(
            word_output_path,
            version=version,
            doc_phase=normalized_doc_phase,
        )
        if versioned_path != word_output_path:
            versioned_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(word_output_path, versioned_path)
            word_output_path = versioned_path
        md_output_path: Path | None = None
        if normalized_doc_phase in {"draft", "publish"}:
            md_output_path = resolve_md_output_path_for_target(
                config_path=effective_config_path,
                model=model,
                region=region,
            )
            if not md_output_path.exists():
                raise RuntimeError(f"Markdown output was not created: {md_output_path}")
            versioned_md_path = versioned_md_output_path(
                md_output_path,
                version=version,
                doc_phase=normalized_doc_phase,
            )
            if versioned_md_path != md_output_path:
                versioned_md_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(md_output_path, versioned_md_path)
                md_output_path = versioned_md_path
        if normalized_doc_phase == "publish":
            pdf_output_path = resolve_pdf_output_path_for_target(
                config_path=effective_config_path,
                model=model,
                region=region,
            )
            if not pdf_output_path.exists():
                raise RuntimeError(f"PDF output was not created for publish: {pdf_output_path}")
            versioned_pdf_path = versioned_pdf_output_path(
                pdf_output_path,
                version=version,
                doc_phase=normalized_doc_phase,
            )
            if versioned_pdf_path != pdf_output_path:
                versioned_pdf_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(pdf_output_path, versioned_pdf_path)
                pdf_output_path = versioned_pdf_path
            html_output_dir = resolve_html_output_dir_for_target(
                config_path=effective_config_path,
                model=model,
                region=region,
            )
            if not html_output_dir.exists():
                raise RuntimeError(f"HTML output was not created for publish: {html_output_dir}")
            host_config_path = config_path_in_repo_root(config_path, repo_root=repo_root)
            if md_output_path is None:
                raise RuntimeError("Markdown output was not created for publish")
            staged_word_output_path, staged_pdf_output_path, staged_md_output_path, latest_html_dir = stage_publish_assets_to_host_repo(
                built_word_output_path=word_output_path,
                built_pdf_output_path=pdf_output_path,
                built_md_output_path=md_output_path,
                built_html_dir=html_output_dir,
                host_config_path=host_config_path,
                model=model,
                region=region,
                version=version,
            )
            return BuiltDocumentOutputs(
                word_output_path=staged_word_output_path,
                upload_output_path=staged_pdf_output_path,
                md_output_path=staged_md_output_path,
                pdf_output_path=staged_pdf_output_path,
                html_output_dir=latest_html_dir,
            )
        if effective_repo_root != repo_root:
            staged_word_output_path = stage_draft_word_output_to_host_repo(
                built_word_output_path=word_output_path,
                host_config_path=config_path_in_repo_root(config_path, repo_root=repo_root),
                model=model,
                region=region,
                version=version,
                doc_phase=normalized_doc_phase,
            )
            staged_md_output_path = (
                stage_draft_md_output_to_host_repo(
                    built_md_output_path=md_output_path,
                    host_config_path=config_path_in_repo_root(config_path, repo_root=repo_root),
                    model=model,
                    region=region,
                    version=version,
                    doc_phase=normalized_doc_phase,
                )
                if md_output_path is not None
                else None
            )
            return BuiltDocumentOutputs(
                word_output_path=staged_word_output_path,
                upload_output_path=staged_word_output_path,
                md_output_path=staged_md_output_path,
            )
        return BuiltDocumentOutputs(
            word_output_path=word_output_path,
            upload_output_path=word_output_path,
            md_output_path=md_output_path,
        )
    finally:
        cleaned_paths: set[Path] = set()
        for workspace in (review_workspace, build_workspace):
            if workspace is None or workspace in cleaned_paths:
                continue
            remove_worktree(workspace)
            cleaned_paths.add(workspace)
