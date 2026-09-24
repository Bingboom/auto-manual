"""Stage files in a bundle whose usage manifest records governed rewrites."""
from __future__ import annotations

import json
import shutil
from pathlib import Path


def write_bundle_with_rewrites(
    bundle_root: Path,
    rewrites: list[tuple[str, str, str, Path]],
    *,
    model: str = "JE-1000F",
    region: str = "US",
) -> Path:
    """Stage each ``(staged_path, logical_key, asset_key, source)`` and record it.

    The manifest carries what ``manifest_asset_slot`` reads: the schema, the
    target and one rewrite per staged file, as a finalized bundle writes them.
    """

    rows = []
    for staged_path, logical_key, asset_key, source in rewrites:
        destination = bundle_root / staged_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        rows.append({
            "asset_key": asset_key,
            "original_value": f"asset:{logical_key}",
            "reference_kind": "registry-uri",
            "reference_path": "page/fixture.rst",
            "rendered_value": staged_path,
            "staged_path": staged_path,
        })
    (bundle_root / "asset_usage_manifest.json").write_text(
        json.dumps({
            "schema_version": 2,
            "target": {"model": model, "region": region, "language": None},
            "assets": [],
            "rewrites": rows,
        }),
        encoding="utf-8",
    )
    return bundle_root
