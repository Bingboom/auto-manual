"""Prune externalized raw binary residuals from transitional mirror overlays.

When ``auto-manual`` externalizes a large source binary (``.pdf``, ``.ai``,
``.bin``) to Feishu and replaces it with an ``external-source-pointer/v1``
pointer file, ``MIRROR_OVERLAY_PATHS`` would otherwise retain the deleted raw
binary downstream in ``Hello-Docs`` forever because overlay mode preserves
mirror-only files.

This module identifies mirror-only overlay candidates that are absent from
upstream ``auto-manual`` AND superseded by a validated upstream pointer (either
a direct ``<path>.source-pointer.json`` sidecar or split ``archive_parts``
referenced by upstream package metadata alongside a matching pointer) so they
can be pruned before committing to ``Hello-Docs``, while keeping all
non-externalized mirror-only files and all upstream-present files intact.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys

from tools.web import external_source_store as store

_MANIFEST_FILENAMES = (
    "manifest.json",
    "source_manifest.json",
    "frozen_source_manifest.json",
    "pdf-identity.json",
)
_PACKAGE_MANIFEST_NAMES = frozenset(
    {"manifest.json", "source_manifest.json", "frozen_source_manifest.json"}
)


@dataclass(frozen=True)
class PrunePlan:
    """Dry-run partition of mirror-only overlay paths."""

    superseded_paths: frozenset[str]
    pruned_paths: tuple[str, ...]
    kept_paths: tuple[str, ...]


def _normalize_relpath(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    cleaned = raw.strip().replace("\\", "/")
    if not cleaned or cleaned.startswith("/"):
        return None
    parts = cleaned.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None
    return cleaned


def _normalize_overlay_prefixes(overlay_paths: Iterable[str]) -> tuple[str, ...]:
    prefixes: list[str] = []
    for raw in overlay_paths:
        cleaned = _normalize_relpath(raw)
        if cleaned and cleaned not in prefixes:
            prefixes.append(cleaned)
    return tuple(prefixes)


def _scan_roots_for(source_root: Path, overlay_prefixes: tuple[str, ...]) -> tuple[Path, ...]:
    if not overlay_prefixes:
        return (source_root,) if source_root.is_dir() else ()
    roots: list[Path] = []
    for prefix in overlay_prefixes:
        candidate = source_root / prefix
        if candidate.is_dir():
            roots.append(candidate)
    return tuple(roots)


def _resolve_overlay_relpath(
    source_root: Path,
    base_dir: Path,
    raw_path: object,
    overlay_prefixes: tuple[str, ...],
) -> str | None:
    cleaned = _normalize_relpath(raw_path)
    if cleaned is None:
        return None
    if any(cleaned == prefix or cleaned.startswith(f"{prefix}/") for prefix in overlay_prefixes):
        return cleaned
    root_resolved = source_root.resolve()
    target_resolved = (base_dir / cleaned).resolve()
    if not target_resolved.is_relative_to(root_resolved):
        return None
    rel = target_resolved.relative_to(root_resolved).as_posix()
    return None if rel == "." else rel


def _scan_valid_pointers(
    source_root: Path,
    scan_roots: tuple[Path, ...],
) -> tuple[dict[str, store.ExternalSourcePointer], dict[str, set[str]]]:
    valid_pointers: dict[str, store.ExternalSourcePointer] = {}
    pointers_by_sha: dict[str, set[str]] = {}
    root_resolved = source_root.resolve()
    for scan_root in scan_roots:
        for ptr_path in sorted(scan_root.rglob(f"*{store.POINTER_SUFFIX}")):
            if not ptr_path.is_file() or ptr_path.is_symlink():
                continue
            try:
                pointer = store.load_pointer_file(ptr_path)
            except ValueError:
                continue
            rel_ptr = ptr_path.resolve().relative_to(root_resolved).as_posix()
            valid_pointers[rel_ptr] = pointer
            pointers_by_sha.setdefault(pointer.sha256, set()).add(rel_ptr)
    return valid_pointers, pointers_by_sha


def _read_json_mapping(path: Path) -> Mapping[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, Mapping) else None


def _find_package_dir(meta_path: Path, scan_root: Path) -> Path:
    if meta_path.name in _PACKAGE_MANIFEST_NAMES:
        return meta_path.parent
    current = meta_path.parent
    while True:
        if (current / "source_manifest.json").is_file() or (current / "manifest.json").is_file():
            return current
        if current == scan_root or current.parent == current:
            return meta_path.parent
        current = current.parent


def _package_source_pointer_ref(pkg_dir: Path) -> str | None:
    for name in ("source_manifest.json", "manifest.json"):
        payload = _read_json_mapping(pkg_dir / name)
        if payload is None:
            continue
        orig = payload.get("original_source")
        if isinstance(orig, Mapping) and isinstance(orig.get("source_pointer"), str):
            return orig["source_pointer"]
    return None


def _is_descriptor_superseded(
    desc: Mapping[str, object],
    *,
    pkg_dir: Path,
    source_root: Path,
    overlay_prefixes: tuple[str, ...],
    valid_pointers: Mapping[str, store.ExternalSourcePointer],
    pointers_by_sha: Mapping[str, set[str]],
    fallback_ptr_ref: str | None,
) -> bool:
    target_sha = str(desc.get("sha256") or "").strip()
    raw_ref = desc.get("source_pointer")
    ptr_ref = raw_ref if isinstance(raw_ref, str) else fallback_ptr_ref
    if ptr_ref:
        ptr_rel = _resolve_overlay_relpath(source_root, pkg_dir, ptr_ref, overlay_prefixes)
        if ptr_rel and ptr_rel in valid_pointers:
            if not target_sha or valid_pointers[ptr_rel].sha256 == target_sha:
                return True
    if target_sha and target_sha in pointers_by_sha:
        return True
    filename = desc.get("filename")
    if isinstance(filename, str) and filename.strip() and not target_sha:
        pkg_rel = pkg_dir.resolve().relative_to(source_root.resolve()).as_posix()
        pkg_prefix = "" if pkg_rel == "." else f"{pkg_rel}/"
        return any(
            rel.startswith(pkg_prefix) and ptr.file_name == filename.strip()
            for rel, ptr in valid_pointers.items()
        )
    return False


def _descriptors_from_metadata(name: str, payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    descriptors: list[Mapping[str, object]] = []
    orig = payload.get("original_source")
    if isinstance(orig, Mapping):
        descriptors.append(orig)
    if name == "pdf-identity.json" and isinstance(payload.get("archive_parts"), list):
        descriptors.append(payload)
    return descriptors


def _collect_split_archive_paths(
    source_root: Path,
    scan_roots: tuple[Path, ...],
    overlay_prefixes: tuple[str, ...],
    valid_pointers: Mapping[str, store.ExternalSourcePointer],
    pointers_by_sha: Mapping[str, set[str]],
) -> set[str]:
    superseded_parts: set[str] = set()
    for scan_root in scan_roots:
        for name in _MANIFEST_FILENAMES:
            for meta_path in sorted(scan_root.rglob(name)):
                payload = _read_json_mapping(meta_path)
                if payload is None:
                    continue
                pkg_dir = _find_package_dir(meta_path, scan_root)
                fallback_ptr_ref = _package_source_pointer_ref(pkg_dir)
                for desc in _descriptors_from_metadata(name, payload):
                    parts = desc.get("archive_parts")
                    if not isinstance(parts, list) or not parts:
                        continue
                    if not _is_descriptor_superseded(
                        desc,
                        pkg_dir=pkg_dir,
                        source_root=source_root,
                        overlay_prefixes=overlay_prefixes,
                        valid_pointers=valid_pointers,
                        pointers_by_sha=pointers_by_sha,
                        fallback_ptr_ref=fallback_ptr_ref,
                    ):
                        continue
                    for part in parts:
                        raw_part = part.get("path") if isinstance(part, Mapping) else part
                        resolved = _resolve_overlay_relpath(
                            source_root, pkg_dir, raw_part, overlay_prefixes
                        )
                        if resolved:
                            superseded_parts.add(resolved)
    return superseded_parts


def collect_superseded_overlay_paths(
    source_root: Path,
    overlay_paths: Iterable[str] = (),
) -> frozenset[str]:
    """Return repo-relative paths superseded by validated upstream pointers."""
    overlay_prefixes = _normalize_overlay_prefixes(overlay_paths)
    scan_roots = _scan_roots_for(source_root, overlay_prefixes)
    if not scan_roots:
        return frozenset()
    valid_pointers, pointers_by_sha = _scan_valid_pointers(source_root, scan_roots)
    superseded = {
        rel_ptr[: -len(store.POINTER_SUFFIX)] for rel_ptr in valid_pointers
    }
    superseded.update(
        _collect_split_archive_paths(
            source_root,
            scan_roots,
            overlay_prefixes,
            valid_pointers,
            pointers_by_sha,
        )
    )
    return frozenset(superseded)


def should_prune_overlay_path(
    rel_path: str,
    source_root: Path,
    superseded_paths: Iterable[str],
) -> bool:
    """True iff ``rel_path`` is superseded upstream AND absent from ``source_root``."""
    superseded_set = (
        superseded_paths
        if isinstance(superseded_paths, (set, frozenset))
        else frozenset(superseded_paths)
    )
    if rel_path not in superseded_set:
        return False
    return not os.path.lexists(source_root / rel_path)


def filter_nul_ls_tree(
    raw_bytes: bytes,
    source_root: Path,
    superseded_paths: Iterable[str],
) -> tuple[bytes, int, int]:
    """Filter NUL-separated ``git ls-tree -z`` records, dropping superseded entries."""
    superseded_set = (
        superseded_paths
        if isinstance(superseded_paths, (set, frozenset))
        else frozenset(superseded_paths)
    )
    kept_records: list[bytes] = []
    pruned_count = 0
    for record in raw_bytes.split(b"\0"):
        if not record:
            continue
        _, sep, raw_path = record.partition(b"\t")
        if not sep:
            kept_records.append(record)
            continue
        rel_path = raw_path.decode("utf-8", errors="surrogateescape")
        if should_prune_overlay_path(rel_path, source_root, superseded_set):
            pruned_count += 1
            continue
        kept_records.append(record)
    output_bytes = b"\0".join(kept_records) + (b"\0" if kept_records else b"")
    return output_bytes, len(kept_records), pruned_count


def plan_prune(
    source_root: Path,
    mirror_only_paths: Iterable[str],
    overlay_paths: Iterable[str] = (),
) -> PrunePlan:
    """Partition ``mirror_only_paths`` into pruned vs kept paths."""
    superseded = collect_superseded_overlay_paths(source_root, overlay_paths)
    pruned: list[str] = []
    kept: list[str] = []
    for rel_path in sorted(set(mirror_only_paths)):
        if should_prune_overlay_path(rel_path, source_root, superseded):
            pruned.append(rel_path)
        else:
            kept.append(rel_path)
    return PrunePlan(
        superseded_paths=superseded,
        pruned_paths=tuple(pruned),
        kept_paths=tuple(kept),
    )


def _load_mirror_blobs_from_json(
    json_path: Path,
    source_root: Path,
    overlay_prefixes: tuple[str, ...],
) -> dict[str, int]:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{json_path}: expected JSON object mapping overlay root -> tree entries")
    mirror_only: dict[str, int] = {}
    for root_rel, entries in payload.items():
        if overlay_prefixes and root_rel not in overlay_prefixes:
            continue
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, Mapping) or entry.get("type") != "blob":
                continue
            rel_path = f"{root_rel}/{entry['path']}"
            if not os.path.lexists(source_root / rel_path):
                mirror_only[rel_path] = int(entry.get("size") or 0)
    return mirror_only


def _load_mirror_blobs_from_repo(
    mirror_repo: Path,
    mirror_ref: str,
    source_root: Path,
    overlay_prefixes: tuple[str, ...],
) -> dict[str, int]:
    args = ["git", "-C", str(mirror_repo), "ls-tree", "-r", "-z", "--full-tree", mirror_ref]
    if overlay_prefixes:
        args.extend(["--", *overlay_prefixes])
    raw = subprocess.check_output(args)
    mirror_only: dict[str, int] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        _, _, raw_path = record.partition(b"\t")
        rel_path = raw_path.decode("utf-8", errors="surrogateescape")
        if not os.path.lexists(source_root / rel_path):
            mirror_only[rel_path] = 0
    return mirror_only


def _run_filter_ls_tree(args: argparse.Namespace) -> int:
    source_root = args.source_root.resolve()
    overlay_paths = [part for chunk in args.overlay_paths for part in chunk.split() if part]
    superseded = collect_superseded_overlay_paths(source_root, overlay_paths)
    raw_bytes = (
        sys.stdin.buffer.read()
        if args.input == "-"
        else Path(args.input).read_bytes()
    )
    filtered, kept_count, pruned_count = filter_nul_ls_tree(
        raw_bytes, source_root, superseded
    )
    if args.output == "-":
        sys.stdout.buffer.write(filtered)
    else:
        Path(args.output).write_bytes(filtered)
    if args.stats_file:
        Path(args.stats_file).write_text(f"{kept_count} {pruned_count}\n", encoding="utf-8")
    return 0


def _run_dry_run(args: argparse.Namespace) -> int:
    source_root = args.source_root.resolve()
    overlay_prefixes = _normalize_overlay_prefixes(
        part for chunk in args.overlay_paths for part in chunk.split() if part
    )
    if args.mirror_tree_json:
        mirror_only = _load_mirror_blobs_from_json(
            Path(args.mirror_tree_json), source_root, overlay_prefixes
        )
    else:
        mirror_only = _load_mirror_blobs_from_repo(
            Path(args.mirror_repo), args.mirror_ref, source_root, overlay_prefixes
        )
    plan = plan_prune(source_root, mirror_only.keys(), overlay_prefixes)
    by_suffix: dict[str, list[int]] = {}
    total_bytes = 0
    for path in plan.pruned_paths:
        size = mirror_only.get(path, 0)
        total_bytes += size
        ext = Path(path).suffix.lower() or "(noext)"
        bucket = by_suffix.setdefault(ext, [0, 0])
        bucket[0] += 1
        bucket[1] += size
    summary = {
        "superseded_targets": len(plan.superseded_paths),
        "mirror_only_total": len(mirror_only),
        "pruned_count": len(plan.pruned_paths),
        "pruned_bytes": total_bytes,
        "pruned_mib": round(total_bytes / (1024 * 1024), 2),
        "pruned_by_suffix": {
            ext: {"count": cnt, "bytes": sz, "mib": round(sz / (1024 * 1024), 2)}
            for ext, (cnt, sz) in sorted(by_suffix.items())
        },
        "kept_count": len(plan.kept_paths),
        "kept_paths": list(plan.kept_paths),
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(
            f"[mirror-overlay-prune] mirror_only={summary['mirror_only_total']} "
            f"pruned={summary['pruned_count']} ({summary['pruned_mib']:.2f} MiB) "
            f"kept={summary['kept_count']}"
        )
        for ext, stats in summary["pruned_by_suffix"].items():
            print(f"  {ext}: {stats['count']} file(s), {stats['mib']:.2f} MiB")
        for path in plan.kept_paths:
            print(f"  kept: {path}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    flt = sub.add_parser(
        "filter-ls-tree",
        help="filter NUL-separated git ls-tree entries against upstream external pointers",
    )
    flt.add_argument("--source-root", type=Path, required=True)
    flt.add_argument("--overlay-paths", action="append", default=[])
    flt.add_argument("--input", default="-")
    flt.add_argument("--output", default="-")
    flt.add_argument("--stats-file")

    dry = sub.add_parser(
        "dry-run",
        help="simulate pruning against a mirror tree JSON or mirror git repo",
    )
    dry.add_argument("--source-root", type=Path, required=True)
    dry.add_argument("--overlay-paths", action="append", default=[])
    group = dry.add_mutually_exclusive_group(required=True)
    group.add_argument("--mirror-tree-json")
    group.add_argument("--mirror-repo")
    dry.add_argument("--mirror-ref", default="HEAD")
    dry.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "filter-ls-tree":
        return _run_filter_ls_tree(args)
    return _run_dry_run(args)


if __name__ == "__main__":
    raise SystemExit(main())
