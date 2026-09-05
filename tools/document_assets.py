"""Shared local image resolution/staging; no source reader or build imports."""
from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path

from tools.word_bundle_html_images import _IMG_SRC_RE


def resolve_fragment_asset_path(src: str, source_path: Path, search_roots: tuple[Path, ...]) -> Path | None:
    candidate = src.strip()
    if not candidate or candidate.startswith(("http://", "https://", "data:", "file:", "#")):
        return None

    raw_path = Path(candidate)
    probe_paths: list[Path] = []
    if raw_path.is_absolute():
        probe_paths.append(raw_path)
    else:
        probe_paths.extend(
            [
                source_path.parent / raw_path,
                source_path.parent.parent / raw_path,
                *(root / raw_path for root in search_roots),
            ]
        )

    for probe in probe_paths:
        if probe.exists() and probe.is_file():
            return probe.resolve()
    return None


def stage_fragment_assets(fragment: str, source_path: Path, bundle_dir: Path, search_roots: tuple[Path, ...]) -> str:
    assets_dir = bundle_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    staged: dict[str, str] = {}

    def replace_src(match: re.Match[str]) -> str:
        prefix, src, suffix = match.groups()
        resolved = resolve_fragment_asset_path(src, source_path, search_roots)
        if resolved is None:
            return match.group(0)

        key = str(resolved)
        staged_name = staged.get(key)
        if staged_name is None:
            # The bundle may be materialized in a disposable worktree or an
            # isolated staging root.  A path-derived suffix made the shipped
            # Markdown (and the DOCX image descriptions generated from this
            # HTML) change even when the source bytes were identical.  Bind
            # the staged name to the asset content instead so the same frozen
            # input has the same release representation everywhere.
            digest = hashlib.sha256(resolved.read_bytes()).hexdigest()[:12]
            staged_name = f"{resolved.stem}_{digest}{resolved.suffix}"
            shutil.copy2(resolved, assets_dir / staged_name)
            staged[key] = staged_name

        return f"{prefix}{(assets_dir / staged_name).resolve().as_uri()}{suffix}"

    return _IMG_SRC_RE.sub(replace_src, fragment)

