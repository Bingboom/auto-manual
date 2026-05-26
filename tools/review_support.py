#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from functools import lru_cache
import json
from pathlib import Path
import re

from tools.gen_index_bundle_assets import rewrite_rst_asset_paths


ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER_RE = re.compile(r"\|([A-Z0-9][A-Z0-9_]+)\|")
REVIEW_DUPLICATE_PREFIX_RE = re.compile(r"^p\d+_")


@dataclass(frozen=True)
class SyncPlanEntry:
    relative_path: Path
    mode: str = "copy"
    template_path: Path | None = None
    source_relative_path: Path | None = None


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


def resolve_existing_review_bundle_dir(
    *,
    docs_dir: Path,
    model: str | None,
    region: str | None,
    lang: str | None = None,
) -> Path | None:
    candidates: list[str | None] = [lang]
    if (lang or "").strip():
        candidates.append(None)

    seen: set[Path] = set()
    for candidate_lang in candidates:
        review_dir = review_dir_for_target(
            docs_dir=docs_dir,
            model=model,
            region=region,
            lang=candidate_lang,
        )
        if review_dir in seen:
            continue
        seen.add(review_dir)
        if review_bundle_exists(
            docs_dir=docs_dir,
            model=model,
            region=region,
            lang=candidate_lang,
        ):
            return review_dir
    return None


def review_content_exists(*, docs_dir: Path, model: str | None, region: str | None, lang: str | None = None) -> bool:
    if review_bundle_exists(docs_dir=docs_dir, model=model, region=region, lang=lang):
        return True
    review_dir = review_dir_for_target(docs_dir=docs_dir, model=model, region=region, lang=lang)
    return (
        (review_dir / "index.rst").exists()
        or (review_dir / "page").is_dir()
        or (review_dir / "generated").is_dir()
        or (review_dir / "overrides").is_dir()
    )


def _normalized_materialized_page_name(file_name: str) -> str:
    return REVIEW_DUPLICATE_PREFIX_RE.sub("", file_name, count=1)


def _review_manifest(review_dir: Path) -> dict[str, object]:
    manifest_path = review_dir / "manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return raw if isinstance(raw, dict) else {}


def _resolve_repo_path(value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value.strip())
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def _family_page_manifest_path(*, model: str | None, region: str | None) -> tuple[Path | None, Path | None]:
    from tools.config_loader import load_config_mapping
    from tools.page_manifest import resolve_page_manifest_path
    from tools.target_defaults import FAMILY_DEFAULT_CONFIGS

    config_name = FAMILY_DEFAULT_CONFIGS.get((region or "").strip().upper())
    if config_name is None:
        return None, None
    config_path = (ROOT / config_name).resolve()
    cfg = load_config_mapping(config_path)
    return resolve_page_manifest_path(cfg, root=ROOT, model=model, region=region), config_path


def _target_config_path_for_review_mapping(*, region: str | None, lang: str) -> Path | None:
    from tools.config_loader import load_config_mapping
    from tools.queue_config_resolution import resolve_config_path_for_task

    normalized_region = (region or "").strip().upper()
    normalized_lang = lang.strip().lower()
    if not normalized_region or not normalized_lang:
        return None
    return resolve_config_path_for_task(
        repo_root=ROOT,
        region=normalized_region,
        lang=normalized_lang,
        config_loader=load_config_mapping,
    ).resolve()


@lru_cache(maxsize=None)
def _shared_review_page_path_pairs(
    *,
    family_config_path: str,
    target_config_path: str,
    model: str | None,
    region: str | None,
) -> tuple[tuple[str, str], ...]:
    from tools.config_loader import load_config_mapping
    from tools.gen_index_bundle import plan_materialized_pages

    family_cfg = load_config_mapping(Path(family_config_path))
    target_cfg = load_config_mapping(Path(target_config_path))

    family_pages = plan_materialized_pages(family_cfg, model=model, region=region, root=ROOT)
    target_pages = plan_materialized_pages(target_cfg, model=model, region=region, root=ROOT)

    family_by_key: dict[tuple[str, str], list[str]] = {}
    for planned in family_pages:
        key = ((planned.lang or "").strip().lower(), _normalized_materialized_page_name(planned.file_name))
        family_by_key.setdefault(key, []).append(planned.file_name)

    mapped_pairs: list[tuple[str, str]] = []
    for planned in target_pages:
        key = ((planned.lang or "").strip().lower(), _normalized_materialized_page_name(planned.file_name))
        shared_names = family_by_key.get(key)
        if not shared_names:
            continue
        mapped_pairs.append(
            (
                (Path("page") / planned.file_name).as_posix(),
                (Path("page") / shared_names.pop(0)).as_posix(),
            )
        )
    return tuple(mapped_pairs)


def resolve_review_page_path_map(
    *,
    review_dir: Path,
    model: str | None,
    region: str | None,
    target_lang: str | None,
) -> dict[Path, Path]:
    normalized_target_lang = (target_lang or "").strip().lower()
    if not normalized_target_lang:
        return {}

    review_manifest = _review_manifest(review_dir)
    manifest_lang = str(review_manifest.get("lang") or "").strip().lower()
    if manifest_lang:
        return {}

    review_manifest_path = _resolve_repo_path(review_manifest.get("page_manifest"))
    family_manifest_path, family_config_path = _family_page_manifest_path(model=model, region=region)
    if review_manifest_path is None or family_manifest_path is None or family_config_path is None:
        return {}
    if review_manifest_path != family_manifest_path.resolve():
        return {}

    target_config_path = _target_config_path_for_review_mapping(region=region, lang=normalized_target_lang)
    if target_config_path is None:
        return {}

    from tools.config_loader import load_config_mapping
    from tools.page_manifest import resolve_page_manifest_path

    target_cfg = load_config_mapping(target_config_path)
    target_manifest_path = resolve_page_manifest_path(target_cfg, root=ROOT, model=model, region=region)
    if target_manifest_path is None or target_manifest_path.resolve() == family_manifest_path.resolve():
        return {}

    return {
        Path(target_relative): Path(review_relative)
        for target_relative, review_relative in _shared_review_page_path_pairs(
            family_config_path=family_config_path.as_posix(),
            target_config_path=target_config_path.as_posix(),
            model=model,
            region=region,
        )
    }


def _overlay_file_tree(src_dir: Path, dst_dir: Path, pattern: str = "*") -> None:
    if not src_dir.exists():
        return
    for src_file in sorted(path for path in src_dir.rglob(pattern) if path.is_file()):
        target_path = dst_dir / src_file.relative_to(src_dir)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, target_path)


def _overlay_selected_relative_files(
    *,
    src_root: Path,
    dst_root: Path,
    relative_path_pairs: tuple[tuple[Path, Path], ...],
) -> bool:
    copied = False
    for src_relative_path, dst_relative_path in relative_path_pairs:
        src_path = src_root / src_relative_path
        if not src_path.is_file():
            continue
        target_path = dst_root / dst_relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, target_path)
        copied = True
    return copied


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


def overlay_review_content_onto_bundle(
    *,
    bundle_dir: Path,
    docs_dir: Path,
    model: str | None,
    region: str | None,
    lang: str | None = None,
    target_lang: str | None = None,
    allowed_relative_paths: tuple[Path, ...] | None = None,
    allow_index: bool = True,
) -> Path | None:
    review_dir = review_dir_for_target(docs_dir=docs_dir, model=model, region=region, lang=lang)
    if not review_content_exists(docs_dir=docs_dir, model=model, region=region, lang=lang):
        return None

    index_src = review_dir / "index.rst"
    page_src = review_dir / "page"
    generated_src = review_dir / "generated"
    overrides_src = review_dir / "overrides"
    applied = False

    if allow_index and index_src.exists():
        shutil.copy2(index_src, bundle_dir / "index.rst")
        applied = True

    page_relative_path_map = (
        resolve_review_page_path_map(
            review_dir=review_dir,
            model=model,
            region=region,
            target_lang=target_lang,
        )
        if allowed_relative_paths is not None
        else {}
    )
    selected_page_paths = (
        tuple(path.relative_to("page") for path in allowed_relative_paths if path.parts and path.parts[0] == "page")
        if allowed_relative_paths is not None
        else None
    )
    page_dst = bundle_dir / "page"
    if page_src.is_dir():
        page_dst.mkdir(parents=True, exist_ok=True)
        if selected_page_paths is None:
            _overlay_file_tree(page_src, page_dst, "*.rst")
            applied = True
        else:
            selected_page_pairs: list[tuple[Path, Path]] = []
            for dst_relative_path in selected_page_paths:
                target_relative_path = Path("page") / dst_relative_path
                if page_relative_path_map:
                    mapped_source_path = page_relative_path_map.get(target_relative_path)
                    if mapped_source_path is None or not mapped_source_path.parts or mapped_source_path.parts[0] != "page":
                        continue
                    src_relative_path = mapped_source_path.relative_to("page")
                else:
                    src_relative_path = dst_relative_path
                selected_page_pairs.append((src_relative_path, dst_relative_path))
            if _overlay_selected_relative_files(
                src_root=page_src,
                dst_root=page_dst,
                relative_path_pairs=tuple(selected_page_pairs),
            ):
                applied = True

    selected_generated_paths = (
        tuple(
            path.relative_to("generated")
            for path in allowed_relative_paths
            if path.parts and path.parts[0] == "generated"
        )
        if allowed_relative_paths is not None
        else None
    )
    generated_dst = bundle_dir / "generated"
    if generated_src.is_dir():
        generated_dst.mkdir(parents=True, exist_ok=True)
        if selected_generated_paths is None:
            _overlay_file_tree(generated_src, generated_dst, "*.rst")
            applied = True
        elif _overlay_selected_relative_files(
            src_root=generated_src,
            dst_root=generated_dst,
            relative_path_pairs=tuple((relative_path, relative_path) for relative_path in selected_generated_paths),
        ):
            applied = True

    if overrides_src.is_dir():
        _overlay_override_assets(overrides_src, bundle_dir)
        applied = True

    return review_dir if applied else None


def _copy_relative_file(
    src_root: Path,
    dst_root: Path,
    *,
    src_relative_path: Path,
    dst_relative_path: Path,
) -> Path:
    src_path = src_root / src_relative_path
    dst_path = dst_root / dst_relative_path
    if not src_path.exists():
        raise RuntimeError(f"Sync source file not found: {src_path}")
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst_path)
    return dst_path


def _rewrite_review_rst_asset_paths(path: Path, *, review_dir: Path) -> Path:
    if path.suffix.lower() != ".rst" or not path.exists():
        return path
    text = path.read_text(encoding="utf-8")
    rewritten = rewrite_rst_asset_paths(
        text,
        source_path=path,
        target_path=path,
        bundle_dir=review_dir,
        docs_dir=ROOT / "docs",
        repo_root=ROOT,
    )
    if rewritten != text:
        path.write_text(rewritten, encoding="utf-8")
    return path


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
        src_relative_path = entry.source_relative_path or entry.relative_path
        src_path = runtime_bundle_dir / src_relative_path
        dst_path = review_dir / entry.relative_path
        if entry.mode == "copy":
            copied.append(
                _rewrite_review_rst_asset_paths(
                    _copy_relative_file(
                        runtime_bundle_dir,
                        review_dir,
                        src_relative_path=src_relative_path,
                        dst_relative_path=entry.relative_path,
                    ),
                    review_dir=review_dir,
                )
            )
            continue
        if entry.mode == "merge_params":
            if entry.template_path is None:
                raise RuntimeError(f"Missing template path for merge_params sync: {entry.relative_path}")
            copied.append(
                _rewrite_review_rst_asset_paths(
                    _merge_parameter_lines(template_path=entry.template_path, src_path=src_path, dst_path=dst_path),
                    review_dir=review_dir,
                )
            )
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
