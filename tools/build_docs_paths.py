from __future__ import annotations

from pathlib import Path
from typing import Any


def target_component(value: str | None, fallback: str) -> str:
    text = (value or "").strip() or fallback
    return text.replace("/", "_").replace("\\", "_").replace(":", "_")


def discover_existing_bundle_targets(
    *,
    docs_dir: Path,
    build_target_cls: type[Any],
) -> list[Any]:
    build_root = docs_dir / "_build"
    if not build_root.exists():
        return []

    targets: list[Any] = []
    for model_dir in sorted(path for path in build_root.iterdir() if path.is_dir()):
        for region_dir in sorted(path for path in model_dir.iterdir() if path.is_dir()):
            if (region_dir / "rst" / "index.rst").exists():
                targets.append(build_target_cls(model=model_dir.name, region=region_dir.name))
            for lang_dir in sorted(path for path in region_dir.iterdir() if path.is_dir()):
                if (lang_dir / "rst" / "index.rst").exists():
                    targets.append(build_target_cls(model=model_dir.name, region=region_dir.name, lang=lang_dir.name))
    return targets


def build_root_for_target(
    model: str | None,
    region: str | None,
    lang: str | None = None,
    *,
    docs_build_dir: Path,
    preview_name: str | None = None,
    target_component: Any,
) -> Path:
    target_root = docs_build_dir / target_component(model, "_shared") / target_component(region, "_default")
    if preview_name:
        return target_root / "preview" / target_component(preview_name, "_preview")
    if (lang or "").strip():
        return target_root / target_component(lang, "_default")
    return target_root
