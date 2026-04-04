#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
import json
from pathlib import Path
import re


PLACEHOLDER_RE = re.compile(r"\|([A-Z0-9][A-Z0-9_]+)\|")


@dataclass(frozen=True)
class SyncPlanEntry:
    relative_path: Path
    mode: str = "copy"
    template_path: Path | None = None


def _target_component(value: str | None, fallback: str) -> str:
    text = (value or "").strip() or fallback
    return text.replace("/", "_").replace("\\", "_").replace(":", "_")


def review_dir_for_target(*, docs_dir: Path, model: str | None, region: str | None, lang: str | None = None) -> Path:
    target_root = docs_dir / "_review" / _target_component(model, "_shared") / _target_component(region, "_default")
    if (lang or "").strip():
        return target_root / _target_component(lang, "_default")
    return target_root


def review_bundle_exists(*, docs_dir: Path, model: str | None, region: str | None, lang: str | None = None) -> bool:
    review_dir = review_dir_for_target(docs_dir=docs_dir, model=model, region=region, lang=lang)
    return (review_dir / "index.rst").exists() and (review_dir / "page").is_dir()


def _overlay_file_tree(src_dir: Path, dst_dir: Path, pattern: str = "*") -> None:
    if not src_dir.exists():
        return
    for src_file in sorted(path for path in src_dir.rglob(pattern) if path.is_file()):
        target_path = dst_dir / src_file.relative_to(src_dir)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, target_path)


def _overlay_override_assets(overrides_src: Path, bundle_dir: Path) -> None:
    for allowed_dir in ("_assets", "_static", "renderers"):
        src_dir = overrides_src / allowed_dir
        if not src_dir.exists():
            continue
        _overlay_file_tree(src_dir, bundle_dir / allowed_dir)


def overlay_review_onto_bundle(
    *,
    bundle_dir: Path,
    docs_dir: Path,
    model: str | None,
    region: str | None,
    lang: str | None = None,
) -> Path | None:
    review_dir = review_dir_for_target(docs_dir=docs_dir, model=model, region=region, lang=lang)
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
    page_dst.mkdir(parents=True, exist_ok=True)
    _overlay_file_tree(page_src, page_dst, "*.rst")

    generated_dst = bundle_dir / "generated"
    if generated_src.exists():
        generated_dst.mkdir(parents=True, exist_ok=True)
        _overlay_file_tree(generated_src, generated_dst, "*.rst")

    if overrides_src.exists():
        _overlay_override_assets(overrides_src, bundle_dir)

    return review_dir


def _copy_relative_file(src_root: Path, dst_root: Path, relative_path: Path) -> Path:
    src_path = src_root / relative_path
    dst_path = dst_root / relative_path
    if not src_path.exists():
        raise RuntimeError(f"Sync source file not found: {src_path}")
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst_path)
    return dst_path


def _map_source_to_target_lines(source_lines: list[str], target_lines: list[str]) -> dict[int, int | None]:
    mapping: dict[int, int | None] = {}
    matcher = SequenceMatcher(a=source_lines, b=target_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                mapping[i1 + offset] = j1 + offset
            continue
        if tag == "delete":
            for idx in range(i1, i2):
                mapping[idx] = None
            continue
        if tag == "insert":
            continue

        source_len = i2 - i1
        target_len = j2 - j1
        if target_len <= 0:
            for idx in range(i1, i2):
                mapping[idx] = None
            continue
        if source_len == target_len:
            for offset in range(source_len):
                mapping[i1 + offset] = j1 + offset
            continue
        if source_len == 1:
            mapping[i1] = j1
            continue
        for offset in range(source_len):
            fraction = offset / max(source_len - 1, 1)
            target_offset = round(fraction * max(target_len - 1, 0))
            mapping[i1 + offset] = j1 + target_offset
    return mapping


def _extract_placeholder_values(template_line: str, rendered_line: str) -> tuple[str, ...] | None:
    matches = tuple(PLACEHOLDER_RE.finditer(template_line))
    if not matches:
        return ()

    pattern_parts: list[str] = [r"\A"]
    last = 0
    for idx, match in enumerate(matches):
        pattern_parts.append(re.escape(template_line[last:match.start()]))
        pattern_parts.append(f"(?P<slot_{idx}>.*?)")
        last = match.end()
    pattern_parts.append(re.escape(template_line[last:]))
    pattern_parts.append(r"\Z")

    rendered_match = re.match("".join(pattern_parts), rendered_line, flags=re.DOTALL)
    if rendered_match is None:
        return None
    return tuple(rendered_match.group(f"slot_{idx}") for idx in range(len(matches)))


def _render_placeholder_values(template_line: str, values: tuple[str, ...]) -> str:
    matches = tuple(PLACEHOLDER_RE.finditer(template_line))
    if len(matches) != len(values):
        raise RuntimeError("Placeholder value count does not match template placeholder count")

    rendered_parts: list[str] = []
    last = 0
    for value, match in zip(values, matches):
        rendered_parts.append(template_line[last:match.start()])
        rendered_parts.append(value)
        last = match.end()
    rendered_parts.append(template_line[last:])
    return "".join(rendered_parts)


def _merge_parameter_lines(
    *,
    template_path: Path,
    src_path: Path,
    dst_path: Path,
) -> Path:
    if not template_path.exists():
        raise RuntimeError(f"Sync template file not found: {template_path}")
    if not src_path.exists():
        raise RuntimeError(f"Sync source file not found: {src_path}")

    if not dst_path.exists():
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)
        return dst_path

    template_lines = template_path.read_text(encoding="utf-8").splitlines(keepends=True)
    runtime_lines = src_path.read_text(encoding="utf-8").splitlines(keepends=True)
    review_lines = dst_path.read_text(encoding="utf-8").splitlines(keepends=True)

    merged_lines = list(review_lines)
    review_line_mapping = _map_source_to_target_lines(template_lines, review_lines)
    runtime_line_mapping = _map_source_to_target_lines(template_lines, runtime_lines)
    for template_idx, template_line in enumerate(template_lines):
        if not PLACEHOLDER_RE.search(template_line):
            continue
        runtime_idx = runtime_line_mapping.get(template_idx)
        if runtime_idx is None or runtime_idx >= len(runtime_lines):
            continue
        runtime_values = _extract_placeholder_values(template_line, runtime_lines[runtime_idx])
        if runtime_values is None:
            continue
        review_idx = review_line_mapping.get(template_idx)
        if review_idx is None or review_idx >= len(merged_lines):
            continue
        merged_lines[review_idx] = _render_placeholder_values(template_line, runtime_values)

    dst_path.write_text("".join(merged_lines), encoding="utf-8")
    return dst_path


def _iter_rst_files(root_dir: Path) -> tuple[Path, ...]:
    if not root_dir.exists():
        return ()
    return tuple(sorted(path for path in root_dir.rglob("*.rst") if path.is_file()))


def _generated_sync_paths(runtime_bundle_dir: Path) -> set[Path]:
    paths: set[Path] = set()
    generated_dir = runtime_bundle_dir / "generated"
    if generated_dir.exists():
        paths.update(path.relative_to(runtime_bundle_dir) for path in generated_dir.rglob("*.rst") if path.is_file())

    page_dir = runtime_bundle_dir / "page"
    if page_dir.exists():
        for path in page_dir.glob("*.rst"):
            name = path.name.lower()
            if name.startswith("spec_") or name.startswith("safety_"):
                paths.add(path.relative_to(runtime_bundle_dir))
    return paths


def _parameter_page_sync_paths(runtime_bundle_dir: Path) -> set[Path]:
    paths = _generated_sync_paths(runtime_bundle_dir)
    page_dir = runtime_bundle_dir / "page"
    if not page_dir.exists():
        return paths

    for path in page_dir.glob("*.rst"):
        name = path.name.lower()
        if "placeholder" in name or name.startswith("cover"):
            paths.add(path.relative_to(runtime_bundle_dir))
    return paths


def sync_review_from_runtime(
    *,
    runtime_bundle_dir: Path,
    review_dir: Path,
    scope: str,
    page_files: tuple[str, ...] = (),
) -> tuple[Path, ...]:
    if scope == "generated":
        relative_paths = _generated_sync_paths(runtime_bundle_dir)
    elif scope == "params":
        relative_paths = _parameter_page_sync_paths(runtime_bundle_dir)
    else:
        raise RuntimeError(f"Unsupported sync scope: {scope}")
    for file_name in page_files:
        relative_paths.add(Path("page") / file_name)
    return sync_review_paths(
        runtime_bundle_dir=runtime_bundle_dir,
        review_dir=review_dir,
        scope=scope,
        relative_paths=tuple(sorted(relative_paths)),
    )


def sync_review_paths(
    *,
    runtime_bundle_dir: Path,
    review_dir: Path,
    scope: str,
    relative_paths: tuple[Path, ...] = (),
    plan: tuple[SyncPlanEntry, ...] = (),
) -> tuple[Path, ...]:
    if not review_dir.exists():
        raise RuntimeError(f"Review bundle not found: {review_dir}")
    if not (review_dir / "index.rst").exists() or not (review_dir / "page").is_dir():
        raise RuntimeError(f"Review bundle is incomplete: {review_dir}")
    if relative_paths and plan:
        raise RuntimeError("sync_review_paths accepts either relative_paths or plan, not both")

    sync_plan = plan or tuple(SyncPlanEntry(relative_path=relative_path) for relative_path in relative_paths)

    copied: list[Path] = []
    for entry in sync_plan:
        src_path = runtime_bundle_dir / entry.relative_path
        dst_path = review_dir / entry.relative_path
        if entry.mode == "copy":
            copied.append(_copy_relative_file(runtime_bundle_dir, review_dir, entry.relative_path))
            continue
        if entry.mode == "merge_params":
            if entry.template_path is None:
                raise RuntimeError(f"Missing template path for merge_params sync: {entry.relative_path}")
            copied.append(_merge_parameter_lines(template_path=entry.template_path, src_path=src_path, dst_path=dst_path))
            continue
        raise RuntimeError(f"Unsupported sync mode: {entry.mode}")

    manifest_path = review_dir / "manifest.json"
    manifest: dict[str, object] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}

    manifest["last_synced_at"] = datetime.now(timezone.utc).isoformat()
    manifest["last_sync_scope"] = scope
    manifest["last_sync_files"] = [path.relative_to(review_dir).as_posix() for path in copied]
    manifest["page_files"] = [path.relative_to(review_dir).as_posix() for path in _iter_rst_files(review_dir / "page")]
    manifest["generated_files"] = [
        path.relative_to(review_dir).as_posix() for path in _iter_rst_files(review_dir / "generated")
    ]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return tuple(copied)
