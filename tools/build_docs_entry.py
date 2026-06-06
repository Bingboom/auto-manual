from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable


def _resolve_optional_root(raw_path: str | None, *, repo_root: Path) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    resolved = Path(raw_path.strip())
    if not resolved.is_absolute():
        resolved = repo_root / resolved
    return resolved


def run_build(
    args: argparse.Namespace,
    *,
    paths: Any,
    load_config: Callable[[Path], dict],
    validate_loaded_config: Callable[[dict], None],
    validate_layout_csv: Callable[[Path], None],
    resolve_build_targets: Callable[..., list[Any]],
    config_uses_model_token: Callable[[dict], bool],
    config_uses_region_token: Callable[[dict], bool],
    clean_build_targets: Callable[..., None],
    resolve_requested_formats: Callable[[dict, str | None], set[str]],
    resolve_pdf_mode: Callable[[dict, str | None], str],
    build_target: Callable[..., None],
    write_docs_root_index_for_targets: Callable[[list[Any]], None],
) -> None:
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = paths.root / cfg_path

    cfg = load_config(cfg_path)
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    tools_cfg_raw = cfg.get("tools", {})
    tools_cfg = tools_cfg_raw if isinstance(tools_cfg_raw, dict) else {}
    output_root = _resolve_optional_root(args.output_root, repo_root=paths.root)
    output_base_root = _resolve_optional_root(args.output_base_root, repo_root=paths.root)
    if output_root is not None and output_base_root is not None:
        raise RuntimeError("Use either --output-root or --output-base-root, not both")

    print("[build] validating config...")
    validate_loaded_config(cfg)

    print("[build] validating layout params...")
    layout_csv = cfg.get("paths", {}).get("layout_params_csv")
    if not layout_csv:
        raise RuntimeError("config missing paths.layout_params_csv")
    validate_layout_csv(paths.root / layout_csv)

    targets = resolve_build_targets(
        cfg,
        arg_model=args.model,
        arg_region=args.region,
        arg_lang=args.lang,
        all_targets=args.all_targets,
    )
    if config_uses_model_token(cfg) and any(not target.model for target in targets):
        raise RuntimeError("config uses '{model}' but no --model was provided and build.default_model is empty")
    if config_uses_region_token(cfg) and any(not target.region for target in targets):
        raise RuntimeError("config uses '{region}' but no --region was provided and build.default_region is empty")

    if args.clean:
        if output_base_root is not None:
            clean_build_targets(targets, docs_dir=output_base_root.parent)
        else:
            clean_build_targets(targets, preview_name=args.page_selector if output_root else None)

    requested_formats = resolve_requested_formats(cfg, args.formats)
    pdf_mode = resolve_pdf_mode(cfg, args.pdf_mode) if "pdf" in requested_formats else "latex"
    for target in targets:
        print(
            "[build] target: "
            f"model='{target.model or ''}', region='{target.region or ''}', lang='{target.lang or ''}'"
        )
        build_target(
            cfg,
            target_model=target.model,
            target_region=target.region,
            target_lang=target.lang,
            requested_formats=requested_formats if not args.prepare_only else [],
            pdf_mode=pdf_mode,
            build_cfg=build_cfg,
            tools_cfg=tools_cfg,
            no_open=args.no_open,
            source_mode=args.source,
            data_root=args.data_root,
            page_selector=args.page_selector,
            output_root=output_root,
            output_base_root=output_base_root,
            write_wrapper_index=not args.skip_root_index,
            draft_placeholders=getattr(args, "draft_placeholders", False),
        )

    if not args.skip_root_index:
        write_docs_root_index_for_targets(targets)
