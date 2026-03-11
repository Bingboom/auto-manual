#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import shutil
from pathlib import Path


def _target_component(value: str | None, fallback: str) -> str:
    text = (value or "").strip() or fallback
    return text.replace("/", "_").replace("\\", "_").replace(":", "_")


def review_dir_for_target(*, docs_dir: Path, model: str | None, region: str | None) -> Path:
    return docs_dir / "_review" / _target_component(model, "_shared") / _target_component(region, "_default")


def review_bundle_exists(*, docs_dir: Path, model: str | None, region: str | None) -> bool:
    review_dir = review_dir_for_target(docs_dir=docs_dir, model=model, region=region)
    return (review_dir / "index.rst").exists() and (review_dir / "page").is_dir()


def overlay_review_onto_bundle(
    *,
    bundle_dir: Path,
    docs_dir: Path,
    model: str | None,
    region: str | None,
) -> Path | None:
    review_dir = review_dir_for_target(docs_dir=docs_dir, model=model, region=region)
    index_src = review_dir / "index.rst"
    page_src = review_dir / "page"
    generated_src = review_dir / "generated"
    overrides_src = review_dir / "overrides"

    if not review_dir.exists():
        return None
    if not index_src.exists() or not page_src.is_dir():
        raise RuntimeError(f"Review bundle is incomplete: {review_dir}")

    shutil.copy2(index_src, bundle_dir / "index.rst")

    page_dst = bundle_dir / "page"
    if page_dst.exists():
        shutil.rmtree(page_dst)
    shutil.copytree(page_src, page_dst)

    generated_dst = bundle_dir / "generated"
    if generated_src.exists():
        if generated_dst.exists():
            shutil.rmtree(generated_dst)
        shutil.copytree(generated_src, generated_dst)

    if overrides_src.exists():
        for src_file in sorted(path for path in overrides_src.rglob("*") if path.is_file()):
            target_path = bundle_dir / src_file.relative_to(overrides_src)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, target_path)

    return review_dir
