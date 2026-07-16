from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from tools.config_pages import ConfigPage, CsvPage, GeneratedPage


@dataclass(frozen=True)
class PlannedPage:
    page: ConfigPage
    lang: str | None
    file_name: str


@dataclass(frozen=True)
class MaterializedBundle:
    bundle_dir: Path
    page_dir: Path
    index_path: Path
    conf_path: Path
    conf_base_path: Path
    wrapper_index_path: Path
    page_paths: tuple[Path, ...]
    title: str
    reference_doc: Path | None
    model: str | None
    region: str | None
    lang: str | None
    manifest_path: Path | None = None
    page_manifest_path: Path | None = None
    recipe_ids: tuple[str, ...] = ()
    snippet_ids: tuple[str, ...] = ()
    asset_usage_manifest_path: Path | None = None
    asset_registry_snapshot_path: Path | None = None


def repo_relative(path: Path | None, *, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix()
    except ValueError:
        return path.as_posix()


def file_sha256(path: Path | None) -> str | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select_planned_pages(planned_pages: list[PlannedPage], page_selector: str | None) -> list[PlannedPage]:
    if not (page_selector or "").strip():
        return planned_pages

    selector = page_selector.strip()
    csv_matches = [planned for planned in planned_pages if isinstance(planned.page, CsvPage) and planned.page.page == selector]
    if csv_matches:
        return csv_matches

    generated_matches = [
        planned for planned in planned_pages if isinstance(planned.page, GeneratedPage) and planned.page.page == selector
    ]
    if generated_matches:
        return generated_matches

    stem_matches = [planned for planned in planned_pages if Path(planned.file_name).stem == selector]
    if not stem_matches:
        raise RuntimeError(f"Page selector did not match any materialized page: {selector}")
    if len(stem_matches) > 1:
        raise RuntimeError(f"Page selector matched multiple materialized pages: {selector}")
    return stem_matches
