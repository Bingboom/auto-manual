from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from tools.utils.path_utils import Paths


def resolve_docs_dir(
    cfg: dict,
    *,
    repo_root: Path,
) -> Path:
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("docs_dir")
    if isinstance(raw, str) and raw.strip():
        path = Path(raw.strip())
        return path if path.is_absolute() else (repo_root / path)
    return Paths(root=repo_root).docs_dir


def build_langs(cfg: dict) -> list[str]:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    langs = build_cfg.get("languages", ["en"])
    return [str(item).strip() for item in langs if str(item).strip()] or ["en"]


def checks_cfg(cfg: dict) -> dict:
    checks_cfg_raw = cfg.get("checks", {})
    return checks_cfg_raw if isinstance(checks_cfg_raw, dict) else {}


def repo_relative(path: Path | None, *, repo_root: Path) -> str:
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def collect_check_issues(
    *,
    cfg_path: Path,
    model: str | None,
    region: str | None,
    lang: str | None,
    all_targets: bool,
    data_root: str | None,
    docs_build_dir: Path | None,
    issue_cls: type[Any],
    repo_root: Path,
    load_config: Callable[[Path], dict],
    resolve_docs_dir: Callable[[dict], Path],
    build_langs: Callable[[dict], list[str]],
    resolve_page_manifest_path: Callable[..., Path | None],
    resolve_build_targets: Callable[..., list[Any]],
    bundle_dir_for_target: Callable[..., Path],
    collect_target_identity_issues: Callable[..., list[Any]],
    collect_page_contract_issues: Callable[..., list[Any]],
    collect_generated_page_issues: Callable[..., list[Any]],
    collect_bundle_issues: Callable[..., list[Any]],
    collect_identity_drift_issues: Callable[..., list[Any]],
    collect_duplicate_render_text_issues: Callable[..., list[Any]],
    collect_capability_issues: Callable[..., list[Any]] | None = None,
    collect_lang_parity_issues: Callable[..., list[Any]] | None = None,
) -> list[Any]:
    cfg = load_config(cfg_path)
    docs_dir = resolve_docs_dir(cfg)
    langs = build_langs(cfg)
    manifest_path = resolve_page_manifest_path(cfg, root=repo_root, model=model, region=region)
    targets = resolve_build_targets(
        cfg,
        arg_model=model,
        arg_region=region,
        arg_lang=lang,
        all_targets=all_targets,
    )

    issues: list[Any] = []
    if manifest_path is not None and not manifest_path.exists():
        issues.append(
            issue_cls(
                code="MISSING_PAGE_MANIFEST",
                message=f"Configured page manifest not found: {manifest_path}",
                model=model,
                region=region,
                path=manifest_path,
            )
        )
    for target in targets:
        target_langs = [target.lang] if (target.lang or "").strip() else langs
        bundle_dir = bundle_dir_for_target(
            docs_dir=docs_dir,
            docs_build_dir=docs_build_dir,
            model=target.model,
            region=target.region,
            lang=target.lang,
        )
        issues.extend(
            collect_target_identity_issues(
                cfg,
                target=target,
                langs=target_langs,
                data_root=data_root,
            )
        )
        issues.extend(
            collect_page_contract_issues(
                cfg,
                docs_dir=docs_dir,
                target=target,
                langs=target_langs,
                data_root=data_root,
            )
        )
        issues.extend(
            collect_generated_page_issues(
                cfg,
                docs_dir=docs_dir,
                target=target,
                langs=target_langs,
                data_root=data_root,
            )
        )
        issues.extend(
            collect_bundle_issues(
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                model=target.model,
                region=target.region,
            )
        )
        issues.extend(
            collect_duplicate_render_text_issues(
                docs_dir=docs_dir,
                bundle_dir=bundle_dir,
                model=target.model,
                region=target.region,
            )
        )
        issues.extend(
            collect_identity_drift_issues(
                cfg,
                bundle_dir=bundle_dir,
                target=target,
                langs=target_langs,
                data_root=data_root,
            )
        )
        if collect_capability_issues is not None:
            issues.extend(
                collect_capability_issues(
                    bundle_dir=bundle_dir,
                    docs_dir=docs_dir,
                    model=target.model,
                    region=target.region,
                )
            )
        if collect_lang_parity_issues is not None:
            issues.extend(
                collect_lang_parity_issues(
                    bundle_dir=bundle_dir,
                    docs_dir=docs_dir,
                    langs=target_langs,
                    model=target.model,
                    region=target.region,
                )
            )
    return issues
