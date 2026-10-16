"""Shared-style admission for prepared-document Web packages.

A prepared-document package (``source: prepared-document``) is replayed from
reviewed flow content, not from a native importer's semantic chapters, so the
native coverage gate (``frozen_web_component_coverage``) does not apply to it.
This gate covers the same risk from the other side: a package may not draw
its own styles.

- Every class on a flow node outside a shared component must be defined by the
  shared Web theme (``docs/renderers/contracts/*.css``) or be a generic
  docutils/Sphinx structure class.
- No flow node outside a shared component carries an inline ``style``.
- A table outside a shared component is declared in the package manifest
  (``shared_component_exceptions``) with the reason no shared component fits.
- The package's own stylesheet (``source_stylesheet``) holds geometry only:
  no colour, background, border, fill, stroke, shadow or outline.

Registered components own their slot and carrier markup and are validated by
their own contracts, so their subtrees are not inspected here.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from functools import lru_cache
import hashlib
from pathlib import Path
import re
from typing import Any

from tools.utils.path_utils import PathSegments, get_paths

PROFILE = "prepared-document-shared-styles/v1"
PREPARED_SOURCE = "prepared-document"

# Structure classes docutils/Sphinx or the shared flow renderer put on plain
# flow; none of them carries a source-specific look.
GENERIC_CLASSES = frozenset({
    "arabic", "container", "docutils", "external", "head", "line", "line-block",
    "loweralpha", "lowerroman", "reference", "rubric", "simple", "table-wrapper",
    "upperalpha", "upperroman",
})
_PAINT_PROPERTY = re.compile(
    r"(?i)(?:^|[;{\s])(color|background(?:-[a-z]+)*|border(?:-[a-z]+)*|fill|stroke(?:-[a-z]+)*"
    r"|box-shadow|outline(?:-[a-z]+)*|text-shadow|text-decoration-color)\s*:"
)
_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_CLASS_SELECTOR = re.compile(r"\.([A-Za-z_][\w-]*)")


@lru_cache(maxsize=1)
def shared_classes() -> frozenset[str]:
    """Class names the shared Web theme defines."""
    contracts = get_paths().renderer_contracts_dir
    names: set[str] = set()
    for path in sorted(contracts.rglob("*.css")):
        names.update(_CLASS_SELECTOR.findall(_COMMENT.sub("", path.read_text(encoding="utf-8"))))
    return frozenset(names)


def _classes(attributes: Mapping[str, Any]) -> list[str]:
    value = attributes.get("class")
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return str(value or "").split()


def _plain(node: Any) -> str:
    if isinstance(node, Mapping):
        return str(node.get("text", "")) + "".join(_plain(child) for child in node.get("children", []))
    if isinstance(node, list):
        return "".join(_plain(child) for child in node)
    return ""


def table_text_sha256(table: Mapping[str, Any]) -> str:
    """Whitespace-insensitive identity of a table's copy, for exception declarations."""
    return hashlib.sha256("".join(_plain(table).split()).encode("utf-8")).hexdigest()


def paint_properties(stylesheet: str) -> list[str]:
    """Paint declarations in a source stylesheet (comments ignored)."""
    return [match.group(1).lower() for match in _PAINT_PROPERTY.finditer(_COMMENT.sub("", stylesheet))]


def audit_prepared_document_styles(
    raw: Mapping[str, Any],
    *,
    stylesheet: str = "",
    exceptions: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Inspect actual flow nodes and the source stylesheet of one prepared-document IR."""
    if raw.get("source") != PREPARED_SOURCE:
        return {"profile": PROFILE, "applicable": False, "issues": []}
    language = raw.get("language")
    declared = {
        (row.get("page_id"), row.get("text_sha256")): row for row in exceptions
        if row.get("kind") == "table" and row.get("language") == language
    }
    for row in declared.values():
        if not str(row.get("reason", "")).strip():
            raise ValueError(f"shared_component_exceptions: {row.get('page_id')} needs a reason")
    known = shared_classes() | GENERIC_CLASSES
    issues: list[str] = []
    used: set[tuple[Any, Any]] = set()

    def visit(node: Any, location: str, page_id: Any) -> None:
        if not isinstance(node, Mapping):
            return
        if node.get("kind") == "component":
            return  # the component's own contract governs its carrier and slots
        attributes = ((node.get("presentation") or {}).get("html") or {}).get("attributes") or {}
        if "style" in attributes:
            issues.append(f"{location}: inline style; put geometry in the source stylesheet")
        for name in _classes(attributes):
            if name not in known:
                issues.append(f"{location}: class {name!r} is not a shared Web theme class")
        if node.get("kind") == "table":
            key = (page_id, table_text_sha256(node))
            if key in declared:
                used.add(key)
            else:
                issues.append(f"{location}: table outside a shared component "
                              f"(declare it in shared_component_exceptions, text_sha256 {key[1]})")
        for index, child in enumerate(node.get("children", [])):
            visit(child, f"{location}/children[{index}]", page_id)

    for page in raw.get("pages", []):
        page_id = page.get("page_id")
        for block in page.get("blocks", []):
            visit(block.get("payload"), str(block.get("block_id") or page_id), page_id)
    for key in sorted(set(declared) - used, key=str):
        issues.append(f"shared_component_exceptions: {key[0]} table {key[1]} does not occur")
    for name in sorted(set(paint_properties(stylesheet))):
        issues.append(f"source stylesheet: {name} is paint, not geometry; the shared theme owns it")
    return {"profile": PROFILE, "applicable": True, "model": raw.get("model"), "region": raw.get("region"),
            "language": language, "declared_tables": len(used), "issues": issues}


def audit_prepared_package_locale(package: Path, web_root: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Audit one frozen locale of a package from its sealed IR and stylesheet."""
    import json

    raw = json.loads((web_root / PathSegments.MANUAL_IR_JSON).read_text(encoding="utf-8"))
    sheet = ((raw.get("metadata") or {}).get("source_stylesheet") or {}).get("path")
    stylesheet = (web_root / sheet).read_text(encoding="utf-8") if sheet and (web_root / sheet).is_file() else ""
    return audit_prepared_document_styles(raw, stylesheet=stylesheet,
                                          exceptions=manifest.get("shared_component_exceptions", ()))


def require_prepared_document_styles(raw: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Fail closed when a prepared-document package draws its own styles."""
    report = audit_prepared_document_styles(raw, **kwargs)
    if report["issues"]:
        target = "/".join(str(raw.get(key, "?")) for key in ("model", "region", "language"))
        raise ValueError(f"shared style admission failed for {target}: " + "; ".join(report["issues"][:12])
                         + (f"; … {len(report['issues']) - 12} more" if len(report["issues"]) > 12 else ""))
    return report


BASELINE_FILENAME = "prepared_style_baseline.json"
BASELINE_SCHEMA = "auto-manual-prepared-style-baseline/v1"


def baseline_path() -> Path:
    return get_paths().renderer_contracts_dir / BASELINE_FILENAME


def load_baseline() -> dict[str, Any]:
    """Locales frozen before this gate, bound to their exact IR content hash."""
    import json

    data = json.loads(baseline_path().read_text(encoding="utf-8"))
    if data.get("schema_version") != BASELINE_SCHEMA or not isinstance(data.get("entries"), list):
        raise ValueError("unsupported prepared-document style baseline")
    return data


def require_prepared_style_admission(markdown_dir: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Seal-time gate: a prepared-document locale passes, or is an unchanged pre-gate baseline entry."""
    import json

    ir_path = Path(markdown_dir) / PathSegments.MANUAL_IR_JSON
    if not ir_path.is_file():
        return {"profile": PROFILE, "applicable": False, "issues": []}
    raw = json.loads(ir_path.read_text(encoding="utf-8"))
    if raw.get("source") != PREPARED_SOURCE:
        return {"profile": PROFILE, "applicable": False, "issues": []}
    baseline = {row.get("ir_content_sha256") for row in load_baseline()["entries"]}
    if raw.get("content_sha256") in baseline:
        return {"profile": PROFILE, "applicable": True, "baseline": True, "issues": []}
    report = audit_prepared_package_locale(Path(markdown_dir).parent.parent, Path(markdown_dir), manifest)
    if report["issues"]:
        target = "/".join(str(raw.get(key, "?")) for key in ("model", "region", "language"))
        raise RuntimeError(f"shared style admission failed for {target}: " + "; ".join(report["issues"][:12]))
    return report
