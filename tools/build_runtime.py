from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


def path_component(value: str) -> str:
    text = value.strip()
    return text.replace("/", "_").replace("\\", "_").replace(":", "_")


def preview_output_root(
    config_path: Path,
    *,
    model: str,
    region: str,
    page: str,
    docs_build_dir: Path | None = None,
    resolve_docs_dir: Callable[[Path], Path],
) -> Path:
    actual_docs_build_dir = docs_build_dir or (resolve_docs_dir(config_path) / "_build")
    return actual_docs_build_dir / path_component(model) / path_component(region) / "preview" / path_component(page)


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


def run_checked(cmd: list[str], *, repo_root: Path) -> None:
    print(f"[build.py] {format_command(cmd)}")
    subprocess.run(cmd, cwd=str(repo_root), check=True)


def review_sync_target_args(
    args: argparse.Namespace,
    *,
    resolve_path_from_root: Callable[[str], Path],
    load_config: Callable[[Path], dict[str, Any]],
    resolve_docs_dir: Callable[[Path], Path],
    resolve_build_targets: Callable[..., list[Any]],
    resolve_existing_review_bundle_dir: Callable[..., Path | None],
) -> list[argparse.Namespace]:
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
        if resolve_existing_review_bundle_dir(
            docs_dir=docs_dir,
            model=target.model,
            region=target.region,
            lang=target.lang,
        ) is None:
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


def maybe_sync_review_before_build(
    args: argparse.Namespace,
    *,
    source_override: str,
    effective_source: Callable[[argparse.Namespace], str],
    review_sync_target_args: Callable[[argparse.Namespace], list[argparse.Namespace]],
    run_checked: Callable[[list[str]], None],
    build_docs_command: Callable[..., list[str]],
    sync_review_command: Callable[[argparse.Namespace], list[str]],
) -> None:
    current_effective_source = effective_source(args)
    if source_override != "auto":
        current_effective_source = source_override
    if current_effective_source not in {"auto", "review"}:
        return
    for sync_args in review_sync_target_args(args):
        run_checked(build_docs_command(sync_args, action_override="rst", source_override="runtime"))
        run_checked(sync_review_command(sync_args))


def run_validate(
    config_path: Path,
    *,
    repo_root: Path,
    resolve_layout_params_csv: Callable[[Path], Path],
    run_checked: Callable[[list[str]], None],
    data_root: str | None = None,
    model: str | None = None,
    region: str | None = None,
) -> None:
    run_checked(
        [
            sys.executable,
            str(repo_root / "tools" / "validate_config.py"),
            "--config",
            str(config_path),
        ]
    )
    run_checked(
        [
            sys.executable,
            str(repo_root / "tools" / "validate_layout_params.py"),
            "--csv",
            str(resolve_layout_params_csv(config_path)),
        ]
    )
    run_checked(
        [
            sys.executable,
            str(repo_root / "tools" / "validate_spec_master.py"),
            "--config",
            str(config_path),
            *(
                ["--model", model.strip()]
                if isinstance(model, str) and model.strip()
                else []
            ),
            *(
                ["--region", region.strip()]
                if isinstance(region, str) and region.strip()
                else []
            ),
            *(
                ["--data-root", data_root.strip()]
                if isinstance(data_root, str) and data_root.strip()
                else []
            ),
        ]
    )


def run_check(
    args: argparse.Namespace,
    *,
    source_override: str,
    resolve_path_from_root: Callable[[str], Path],
    run_validate: Callable[..., None],
    effective_source: Callable[[argparse.Namespace], str],
    maybe_sync_review_before_build: Callable[..., None],
    run_checked: Callable[[list[str]], None],
    build_docs_command: Callable[..., list[str]],
    check_docs_command: Callable[[argparse.Namespace], list[str]],
) -> None:
    config_path = resolve_path_from_root(args.config)
    if isinstance(args.data_root, str) and args.data_root.strip():
        run_validate(
            config_path,
            data_root=args.data_root,
            model=args.model,
            region=args.region,
        )
    else:
        run_validate(
            config_path,
            model=args.model,
            region=args.region,
        )
    current_effective_source = effective_source(args)
    if source_override != "auto":
        current_effective_source = source_override
    maybe_sync_review_before_build(args, source_override=current_effective_source)
    run_checked(build_docs_command(args, action_override="rst", source_override=current_effective_source))
    run_checked(check_docs_command(args))


def clean_build_artifacts(
    config_path: Path,
    *,
    clean_targets_for_config: Callable[[Path], tuple[Path, Path]],
    review_root_for_config: Callable[[Path], Path],
    resolve_docs_dir: Callable[[Path], Path],
    collect_legacy_docs_output_dirs: Callable[[Path], list[Path]],
    remove_params_tex: bool = True,
) -> None:
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
