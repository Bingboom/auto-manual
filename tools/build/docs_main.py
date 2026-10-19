from __future__ import annotations

import argparse
from typing import Any, Callable


def run_main(
    argv: list[str] | None = None,
    *,
    parse_args: Callable[[list[str] | None], argparse.Namespace],
    run_build: Callable[..., None],
    paths: Any,
    load_config: Callable[..., dict],
    validate_loaded_config: Callable[[dict], None],
    validate_layout_csv: Callable[..., None],
    resolve_build_targets: Callable[..., list[Any]],
    config_uses_model_token: Callable[[dict], bool],
    config_uses_region_token: Callable[[dict], bool],
    clean_build_targets: Callable[..., None],
    resolve_requested_formats: Callable[[dict, str | None], set[str] | list[str]],
    resolve_pdf_mode: Callable[[dict, str | None], str],
    build_target: Callable[..., None],
    write_docs_root_index_for_targets: Callable[[list[Any]], None],
) -> None:
    args = parse_args(argv)
    run_build(
        args,
        paths=paths,
        load_config=load_config,
        validate_loaded_config=validate_loaded_config,
        validate_layout_csv=validate_layout_csv,
        resolve_build_targets=resolve_build_targets,
        config_uses_model_token=config_uses_model_token,
        config_uses_region_token=config_uses_region_token,
        clean_build_targets=clean_build_targets,
        resolve_requested_formats=resolve_requested_formats,
        resolve_pdf_mode=resolve_pdf_mode,
        build_target=build_target,
        write_docs_root_index_for_targets=write_docs_root_index_for_targets,
    )
