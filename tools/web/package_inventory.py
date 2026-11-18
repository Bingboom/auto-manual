"""Inventory and classification of frozen manual source packages."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
import json
from pathlib import Path
import re
from typing import Any

from tools.utils.path_utils import PathSegments
from tools.web.external_source_store import count_package_external_sources
from tools.web.frozen_package_registry import (
    SOURCE_MANIFEST_JSON,
    frozen_source_roots_of,
)

LARGE_BINARY_THRESHOLD_BYTES = 1024 * 1024
LARGE_BINARY_SUFFIXES = frozenset({".pdf", ".ai"})
CUSTOM_SCRIPT_NAMES = ("rebuild.py", "render.py")
APPROVAL_REL_PATHS = ("source/approval.json", "source/release_approval.json")
_TOCTREE_RE = re.compile(r"^\.\.\s+toctree::\s*$")
_INCLUDE_RE = re.compile(r"^\.\.\s+include::\s+(.+?)\s*$")


def read_manifest(manifest_path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Load and validate that ``source_manifest.json`` is a JSON object."""
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"unreadable {SOURCE_MANIFEST_JSON}: {exc}"
    if not isinstance(raw, dict):
        return None, f"{SOURCE_MANIFEST_JSON} must contain a JSON object"
    return raw, None


def resolve_target_pair(manifest: Mapping[str, Any] | None) -> tuple[str | None, str | None]:
    """Return ``(model, region)`` from ``target`` or top-level manifest keys."""
    if not isinstance(manifest, Mapping):
        return None, None
    target = manifest.get("target")
    model: object = target.get("model") if isinstance(target, Mapping) else None
    region: object = target.get("region") if isinstance(target, Mapping) else None
    if not model:
        model = manifest.get("model")
    if not region:
        region = manifest.get("region")
    model_str = str(model).strip() if isinstance(model, str) and model.strip() else None
    region_str = str(region).strip() if isinstance(region, str) and region.strip() else None
    return model_str, region_str


def extract_rst_refs_from_index(index_path: Path) -> tuple[str, ...]:
    """Extract ordered page entries from an ``index.rst`` toctree or include list."""
    if not index_path.is_file():
        return ()
    lines = index_path.read_text(encoding="utf-8").splitlines()
    toctree_entries = _parse_toctree_entries(lines)
    if toctree_entries:
        return toctree_entries
    return _parse_include_entries(lines)


def _parse_toctree_entries(lines: list[str]) -> tuple[str, ...]:
    entries: list[str] = []
    in_toctree = False
    for line in lines:
        stripped = line.strip()
        if _TOCTREE_RE.match(stripped):
            in_toctree = True
            continue
        if not in_toctree:
            continue
        if not stripped:
            continue
        if not line[0].isspace():
            in_toctree = False
            continue
        if stripped.startswith(":"):
            continue
        entries.append(stripped)
    return tuple(entries)


def _parse_include_entries(lines: list[str]) -> tuple[str, ...]:
    entries: list[str] = []
    for line in lines:
        match = _INCLUDE_RE.match(line.strip())
        if match:
            entries.append(match.group(1).strip())
    return tuple(entries)


def _has_rst_files(directory: Path) -> bool:
    return directory.is_dir() and any(directory.rglob("*.rst"))


def _has_non_empty_pages(value: Any) -> bool:
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, Mapping):
        return any(isinstance(items, list) and len(items) > 0 for items in value.values())
    return False


def is_declarative_ready(package_dir: Path, manifest: Mapping[str, Any] | None) -> bool:
    """Return True when the package can build declaratively without custom Python."""
    source_dir = package_dir / "source"
    if not _has_rst_files(source_dir):
        return False
    if isinstance(manifest, Mapping):
        for key in ("declarative_build", "build"):
            section = manifest.get(key)
            if isinstance(section, Mapping) and (
                _has_non_empty_pages(section.get("pages"))
                or _has_non_empty_pages(section.get("page_order"))
            ):
                return True
        if _has_non_empty_pages(manifest.get("pages")) or _has_non_empty_pages(
            manifest.get("page_order")
        ):
            return True
    for child in sorted(source_dir.iterdir()):
        if child.is_dir() and extract_rst_refs_from_index(child / "index.rst"):
            return True
    return False


def discover_sealed_locales(package_dir: Path) -> list[str]:
    """Return sorted locale directory names under ``web/`` carrying ``manual.ir.json``."""
    web_dir = package_dir / "web"
    if not web_dir.is_dir():
        return []
    locales = [
        entry.parent.name
        for entry in web_dir.glob(f"*/{PathSegments.MANUAL_IR_JSON}")
        if entry.is_file()
    ]
    return sorted(locales)


def _measure_large_binaries(package_dir: Path) -> tuple[int, int]:
    total_bytes = 0
    count = 0
    for path in package_dir.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() not in LARGE_BINARY_SUFFIXES:
            continue
        size = path.stat().st_size
        if size > LARGE_BINARY_THRESHOLD_BYTES:
            total_bytes += size
            count += 1
    return total_bytes, count


def _measure_unpackaged_large_binaries(
    roots: tuple[Path, Path],
    package_dirs: set[Path],
) -> tuple[int, int]:
    total_bytes = 0
    count = 0
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in LARGE_BINARY_SUFFIXES:
                continue
            size = path.stat().st_size
            if size <= LARGE_BINARY_THRESHOLD_BYTES:
                continue
            resolved = path.resolve()
            if not any(resolved.is_relative_to(pkg) for pkg in package_dirs):
                total_bytes += size
                count += 1
    return total_bytes, count


def classify_package(
    package_dir: Path,
    repo_root: Path,
    root_kind: str,
) -> dict[str, Any]:
    """Classify a single frozen source package directory."""
    manifest, manifest_error = read_manifest(package_dir / SOURCE_MANIFEST_JSON)
    model, region = resolve_target_pair(manifest)
    custom_scripts = [
        name for name in CUSTOM_SCRIPT_NAMES if (package_dir / name).is_file()
    ]
    approved = any((package_dir / rel).is_file() for rel in APPROVAL_REL_PATHS)
    large_bytes, large_count = _measure_large_binaries(package_dir)
    external_count = count_package_external_sources(package_dir, manifest)
    return {
        "path": package_dir.relative_to(repo_root).as_posix(),
        "root_kind": root_kind,
        "model": model,
        "region": region,
        "has_custom_script": bool(custom_scripts),
        "custom_scripts": custom_scripts,
        "declarative_ready": is_declarative_ready(package_dir, manifest),
        "sealed_locales": discover_sealed_locales(package_dir),
        "approved": approved,
        "large_binary_bytes": large_bytes,
        "large_binary_count": large_count,
        "external_source_count": external_count,
        "has_external_source_pointers": external_count > 0,
        "manifest_error": manifest_error,
    }


def _find_dual_root_collisions(
    packages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, list[str]]] = defaultdict(
        lambda: {"manual_sources": [], "data/manual_sources": []}
    )
    for pkg in packages:
        model = pkg.get("model")
        region = pkg.get("region")
        if isinstance(model, str) and isinstance(region, str):
            grouped[(model, region)][pkg["root_kind"]].append(pkg["path"])
    collisions: list[dict[str, Any]] = []
    for (model, region), by_root in sorted(grouped.items()):
        if by_root["manual_sources"] and by_root["data/manual_sources"]:
            collisions.append(
                {
                    "model": model,
                    "region": region,
                    "manual_sources_paths": sorted(by_root["manual_sources"]),
                    "data_manual_sources_paths": sorted(by_root["data/manual_sources"]),
                }
            )
    return collisions


def collect_inventory(repo_root: Path) -> dict[str, Any]:
    """Scan both frozen source roots and summarize package readiness and bloat."""
    roots = frozen_source_roots_of(repo_root)
    root_pairs = (
        ("manual_sources", roots[0]),
        ("data/manual_sources", roots[1]),
    )
    packages: list[dict[str, Any]] = []
    package_dirs: set[Path] = set()
    by_root: dict[str, int] = {"manual_sources": 0, "data/manual_sources": 0}
    for root_kind, root in root_pairs:
        if not root.is_dir():
            continue
        for manifest_path in sorted(root.rglob(SOURCE_MANIFEST_JSON)):
            pkg_dir = manifest_path.parent
            package_dirs.add(pkg_dir.resolve())
            packages.append(classify_package(pkg_dir, repo_root, root_kind))
            by_root[root_kind] += 1

    pkg_binary_bytes = sum(int(p["large_binary_bytes"]) for p in packages)
    pkg_binary_count = sum(int(p["large_binary_count"]) for p in packages)
    unpackaged_bytes, unpackaged_count = _measure_unpackaged_large_binaries(
        roots, package_dirs
    )
    collisions = _find_dual_root_collisions(packages)
    return {
        "total_packages": len(packages),
        "by_root": by_root,
        "custom_script_count": sum(1 for p in packages if p["has_custom_script"]),
        "declarative_ready_count": sum(1 for p in packages if p["declarative_ready"]),
        "approved_count": sum(1 for p in packages if p["approved"]),
        "sealed_package_count": sum(1 for p in packages if p["sealed_locales"]),
        "dual_root_collisions": collisions,
        "large_binary_bytes": pkg_binary_bytes,
        "large_binary_mib": round(pkg_binary_bytes / LARGE_BINARY_THRESHOLD_BYTES, 2),
        "large_binary_count": pkg_binary_count,
        "unpackaged_large_binary_bytes": unpackaged_bytes,
        "unpackaged_large_binary_count": unpackaged_count,
        "total_root_large_binary_bytes": pkg_binary_bytes + unpackaged_bytes,
        "external_source_pointer_count": sum(
            int(p["external_source_count"]) for p in packages
        ),
        "external_source_package_count": sum(
            1 for p in packages if p["has_external_source_pointers"]
        ),
        "packages": packages,
    }


def format_inventory_text(report: Mapping[str, Any]) -> str:
    """Format an inventory report as concise human-readable text."""
    lines = [
        f"Packages: {report['total_packages']} "
        f"(manual_sources={report['by_root']['manual_sources']}, "
        f"data/manual_sources={report['by_root']['data/manual_sources']})",
        f"Custom scripts: {report['custom_script_count']}, "
        f"Declarative ready: {report['declarative_ready_count']}, "
        f"Approved: {report['approved_count']}, "
        f"Sealed: {report['sealed_package_count']}",
        f"Dual-root collisions: {len(report['dual_root_collisions'])}",
        f"Large binaries (>1 MiB .pdf/.ai): {report['large_binary_count']} files, "
        f"{report['large_binary_bytes']} bytes ({report['large_binary_mib']} MiB)",
        f"External source pointers: {report['external_source_pointer_count']} across "
        f"{report['external_source_package_count']} packages",
    ]
    for item in report["dual_root_collisions"]:
        lines.append(
            f"  collision {item['model']}/{item['region']}: "
            f"{len(item['manual_sources_paths'])} in manual_sources, "
            f"{len(item['data_manual_sources_paths'])} in data/manual_sources"
        )
    return "\n".join(lines)
