#!/usr/bin/env python3
"""Compute and apply deterministic diffs between page-manifest documents.

The family-manifest rollout keeps the current YAML files as the compatibility
surface while it introduces a small, reviewable diff carrier. A diff is a JSON
document with JSON-Pointer paths and ``add``/``remove``/``replace`` operations.
It is deliberately report/write-to-a-file only: applying a diff returns an
in-memory document and never edits a repository manifest.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency is in requirements
    raise RuntimeError("PyYAML is required for manifest diff operations") from exc


SCHEMA_VERSION = "family-manifest-diff/v1"


class ManifestDiffError(ValueError):
    """Raised when a manifest or diff is structurally invalid."""


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ManifestDiffError(f"cannot read manifest {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ManifestDiffError(f"invalid YAML in manifest {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ManifestDiffError(f"manifest root must be a mapping: {path}")
    pages = raw.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ManifestDiffError(f"manifest pages must be a non-empty list: {path}")
    return raw


def _validate_document(document: dict[str, Any], *, label: str) -> None:
    if not isinstance(document, dict):
        raise ManifestDiffError(f"{label} must be a mapping")
    pages = document.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ManifestDiffError(f"{label}.pages must be a non-empty list")


def load_manifest(path: Path) -> dict[str, Any]:
    """Load and validate a YAML page manifest."""

    return _load_yaml(path)


def canonical_manifest_bytes(document: dict[str, Any]) -> bytes:
    """Return the stable byte representation used by round-trip checks.

    The source of truth remains YAML for compatibility. Canonical JSON is used
    only as a comparison envelope so YAML whitespace/comments do not make an
    otherwise identical manifest look different.
    """

    _validate_document(document, label="manifest")
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            separators=(",", ": "),
        ).encode("utf-8")
        + b"\n"
    )


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _pointer_unescape(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")


def _pointer(parts: tuple[str, ...]) -> str:
    return "/" + "/".join(_pointer_escape(part) for part in parts)


def _diff_values(base: Any, target: Any, path: tuple[str, ...]) -> list[dict[str, Any]]:
    if isinstance(base, dict) and isinstance(target, dict):
        operations: list[dict[str, Any]] = []
        for key in sorted(set(base) - set(target)):
            operations.append({"op": "remove", "path": _pointer((*path, str(key)))})
        for key in sorted(set(target) - set(base)):
            operations.append(
                {"op": "add", "path": _pointer((*path, str(key))), "value": target[key]}
            )
        for key in sorted(set(base) & set(target)):
            operations.extend(_diff_values(base[key], target[key], (*path, str(key))))
        return operations

    if isinstance(base, list) and isinstance(target, list):
        # Page order is part of the composition contract. Same-length lists
        # get stable item-level paths; a length change is one explicit replace
        # so a reviewer sees the composition change as one operation.
        if len(base) != len(target):
            return [{"op": "replace", "path": _pointer(path), "value": target}]
        operations: list[dict[str, Any]] = []
        for index, (old, new) in enumerate(zip(base, target)):
            operations.extend(_diff_values(old, new, (*path, str(index))))
        return operations

    if base != target:
        return [{"op": "replace", "path": _pointer(path), "value": target}]
    return []


def build_manifest_diff(base: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic ``family-manifest-diff/v1`` document."""

    _validate_document(base, label="base manifest")
    _validate_document(target, label="target manifest")
    base_id = str(base.get("manifest_id") or "").strip()
    target_id = str(target.get("manifest_id") or "").strip()
    if not base_id or not target_id:
        raise ManifestDiffError("base and target manifests require manifest_id")

    return {
        "schema_version": SCHEMA_VERSION,
        "base_manifest_id": base_id,
        "target_manifest_id": target_id,
        "operations": _diff_values(base, target, ()),
    }


def _resolve_parent(document: Any, path: str) -> tuple[Any, str]:
    if not isinstance(path, str) or not path.startswith("/"):
        raise ManifestDiffError(f"operation path must be a JSON Pointer: {path!r}")
    parts = [_pointer_unescape(part) for part in path[1:].split("/")]
    if not parts or any(part == "" for part in parts):
        raise ManifestDiffError(f"operation path contains an empty segment: {path!r}")
    parent = document
    for part in parts[:-1]:
        if isinstance(parent, list):
            try:
                parent = parent[int(part)]
            except (ValueError, IndexError) as exc:
                raise ManifestDiffError(f"operation path is not addressable: {path!r}") from exc
        elif isinstance(parent, dict) and part in parent:
            parent = parent[part]
        else:
            raise ManifestDiffError(f"operation path is not addressable: {path!r}")
    return parent, parts[-1]


def _apply_operation(document: dict[str, Any], operation: dict[str, Any]) -> None:
    op = operation.get("op")
    parent, key = _resolve_parent(document, operation.get("path"))
    if isinstance(parent, list):
        try:
            index = int(key)
        except ValueError as exc:
            raise ManifestDiffError(f"list operation index is invalid: {key!r}") from exc
        if op == "add" and index == len(parent):
            parent.append(copy.deepcopy(operation.get("value")))
        elif op == "replace" and 0 <= index < len(parent):
            parent[index] = copy.deepcopy(operation.get("value"))
        elif op == "remove" and 0 <= index < len(parent):
            parent.pop(index)
        else:
            raise ManifestDiffError(f"operation cannot address list index {key!r}")
        return

    if not isinstance(parent, dict):
        raise ManifestDiffError(f"operation parent is not a mapping or list: {key!r}")
    if op == "add":
        if key in parent:
            raise ManifestDiffError(f"add operation would overwrite existing key: {key!r}")
        parent[key] = copy.deepcopy(operation.get("value"))
    elif op == "replace":
        if key not in parent:
            raise ManifestDiffError(f"replace operation cannot find key: {key!r}")
        parent[key] = copy.deepcopy(operation.get("value"))
    elif op == "remove":
        if key not in parent:
            raise ManifestDiffError(f"remove operation cannot find key: {key!r}")
        del parent[key]
    else:
        raise ManifestDiffError(f"unsupported diff operation: {op!r}")


def apply_manifest_diff(base: dict[str, Any], diff: dict[str, Any]) -> dict[str, Any]:
    """Apply a validated diff to a copy of ``base`` without writing files."""

    _validate_document(base, label="base manifest")
    if diff.get("schema_version") != SCHEMA_VERSION:
        raise ManifestDiffError(f"unsupported diff schema: {diff.get('schema_version')!r}")
    base_id = str(base.get("manifest_id") or "").strip()
    if diff.get("base_manifest_id") != base_id:
        raise ManifestDiffError(
            f"diff base id {diff.get('base_manifest_id')!r} does not match {base_id!r}"
        )
    operations = diff.get("operations")
    if not isinstance(operations, list) or not all(isinstance(item, dict) for item in operations):
        raise ManifestDiffError("diff operations must be a list of mappings")

    result = copy.deepcopy(base)
    for operation in operations:
        _apply_operation(result, operation)
    _validate_document(result, label="rebuilt manifest")
    target_id = str(result.get("manifest_id") or "").strip()
    if diff.get("target_manifest_id") != target_id:
        raise ManifestDiffError(
            f"rebuilt manifest id {target_id!r} does not match diff target "
            f"{diff.get('target_manifest_id')!r}"
        )
    return result


def roundtrip_report(
    base: dict[str, Any], target: dict[str, Any], diff: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Return the machine-readable pilot round-trip result."""

    actual_diff = diff if diff is not None else build_manifest_diff(base, target)
    rebuilt = apply_manifest_diff(base, actual_diff)
    rebuilt_bytes = canonical_manifest_bytes(rebuilt)
    target_bytes = canonical_manifest_bytes(target)
    return {
        "schema_version": "family-manifest-roundtrip/v1",
        "base_manifest_id": base.get("manifest_id"),
        "target_manifest_id": target.get("manifest_id"),
        "operation_count": len(actual_diff["operations"]),
        "canonical_sha256": hashlib.sha256(target_bytes).hexdigest(),
        "byte_identical": rebuilt_bytes == target_bytes,
    }


def _write_json(payload: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is None:
        print(text, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    diff_parser = subparsers.add_parser("diff", help="build a deterministic manifest diff")
    diff_parser.add_argument("--base", type=Path, required=True)
    diff_parser.add_argument("--target", type=Path, required=True)
    diff_parser.add_argument("--output", type=Path)

    roundtrip_parser = subparsers.add_parser(
        "roundtrip", help="apply a diff and assert canonical byte identity"
    )
    roundtrip_parser.add_argument("--base", type=Path, required=True)
    roundtrip_parser.add_argument("--target", type=Path, required=True)
    roundtrip_parser.add_argument("--diff", type=Path)

    args = parser.parse_args(argv)
    try:
        base = load_manifest(args.base)
        target = load_manifest(args.target)
        if args.command == "diff":
            _write_json(build_manifest_diff(base, target), args.output)
            return 0

        diff = None
        if args.diff is not None:
            diff = json.loads(args.diff.read_text(encoding="utf-8"))
        report = roundtrip_report(base, target, diff)
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if report["byte_identical"] else 1
    except (ManifestDiffError, OSError, json.JSONDecodeError) as exc:
        print(f"manifest_family: ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
