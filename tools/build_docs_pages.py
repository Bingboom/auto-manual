from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable


def render_csv_pages(
    cfg: dict,
    model: str | None,
    region: str | None,
    *,
    data_root: str | None = None,
    csv_page_cls: type[Any],
    resolve_config_pages_or_raise: Callable[..., Any],
    resolve_data_snapshot_paths: Callable[..., Any],
    run: Callable[..., None],
    repo_root: Path,
) -> None:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    pages = resolve_config_pages_or_raise(
        cfg,
        default_languages=list(build_cfg.get("languages", [])),
        root=repo_root,
        model=model,
        region=region,
        error_prefix="config.pages",
    ).pages
    build_langs = cfg.get("build", {}).get("languages", [])
    snapshot_paths = resolve_data_snapshot_paths(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    )

    csv_pages: set[str] = set()
    csv_langs: set[str] = set()

    for page in pages:
        if not isinstance(page, csv_page_cls):
            continue

        page_name = page.page
        source = page.source
        if source != "phase2":
            raise RuntimeError(f"Unsupported csv_page source='{source}' for page='{page_name}' (phase2-only)")

        csv_pages.add(page_name)
        langs = list(page.langs) or build_langs
        for lang in langs:
            csv_langs.add(str(lang))

    if csv_pages:
        cmd = [sys.executable, "tools/csv_page_build.py"]
        cmd += ["--page", ",".join(sorted(csv_pages))]
        if csv_langs:
            cmd += ["--lang", ",".join(sorted(csv_langs))]
        if model:
            cmd += ["--model", model]
        if region:
            cmd += ["--region", region]
        if isinstance(data_root, str) and data_root.strip():
            cmd += ["--data-root", data_root.strip()]
        cmd += ["--page-registry", str(snapshot_paths.page_registry_csv)]
        cmd += ["--page-blocks-dir", str(snapshot_paths.page_blocks_dir)]
        cmd += ["--spec-master-csv", str(snapshot_paths.spec_master_csv)]
        cmd += ["--spec-footnotes-csv", str(snapshot_paths.spec_footnotes_csv)]
        cmd += ["--spec-notes-csv", str(snapshot_paths.spec_notes_csv)]
        cmd += ["--spec-titles-csv", str(snapshot_paths.spec_titles_csv)]
        run(cmd, cwd=repo_root)
