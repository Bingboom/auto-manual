"""Content-neutral Web IR summaries for reviewed language inheritance.

This is an auditor, not a renderer or a translator. Packaged image identity is
measured from bytes; prose and technical values are never copied or rewritten.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from tools.manual_ir.hashing import file_sha256, value_sha256 as digest


class _Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.shape: list = []

    def handle_starttag(self, tag, attrs):
        # Text, links and translated IDs are content. Geometry and table merges
        # are presentation. Assets are checked independently from real bytes.
        kept = {k: v for k, v in attrs if k in {"class", "style", "rowspan", "colspan", "width", "height"}}
        self.shape.append([tag, kept])

    def handle_endtag(self, tag):
        self.shape.append(["/" + tag])


_STRUCTURAL_VALUES = frozenset({
    "kind", "role", "id", "variant", "header", "rowspan", "colspan",
    "label_rowspan", "asset_index", "image_asset_role", "level", "columns",
    "column", "column_count", "column_roles", "layout", "alignment",
})


def _content_shape(value, key=""):
    if isinstance(value, dict):
        return {k: _content_shape(v, k) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_content_shape(v, key) for v in value]
    if key in _STRUCTURAL_VALUES:
        return value
    if key.endswith("html") and isinstance(value, str):
        parser = _Markup()
        parser.feed(value)
        return parser.shape
    return None


def _asset(ref: str, root: Path) -> str:
    path = root / ref
    if (not ref or Path(ref).is_absolute() or path.is_symlink()
            or not path.resolve().is_relative_to(root.resolve()) or not path.is_file()):
        raise ValueError(f"baseline asset is not a packaged file: {ref}")
    return file_sha256(path)


def _component(spec, root, component_map):
    assets = [{"role": a["role"], "locale_policy": a.get("locale_policy"),
               "sha256": _asset(a["asset_ref"], root)} for a in spec.get("assets", [])]
    slots = [{"role": s["role"], "content_kind": s["content_kind"],
              "shape": (s["content"] if s["role"] in {"operation_id", "reference_id", "geometry_ref"}
                        else _content_shape(s["content"]))} for s in spec.get("slots", [])]
    # Content hashes, source paths and translated titles are intentionally not
    # geometry. Pin the explicit artwork/layout decisions used by adapters.
    metadata = spec.get("metadata", {})
    presentation = {k: v for k, v in metadata.items() if k in {
        "presentation_mode", "content_mode", "base_art_layout", "captions_embedded",
        "caption_centers_pct", "preserve_frame", "text_owner", "frame_policy",
        "leader_policy", "layout", "columns", "column_roles",
    }}
    return {"kind": "component", "slot": component_map[component_reference(spec)],
            "component_id": spec["component_id"],
            "variant": spec.get("variant"), "token_roles": spec.get("token_roles", []),
            "slots": slots, "assets": assets, "presentation": presentation}


def _flow(node, root, component_map):
    kind = node.get("kind")
    if kind == "component":
        result = _component(node["component_spec"], root, component_map)
        result["carrier_layout"] = [v for n in node.get("carrier_flow", [])
                                    if (v := _flow(n, root, component_map)) is not None]
        return result
    children = [v for n in node.get("children", []) if (v := _flow(n, root, component_map)) is not None]
    if kind == "image":
        return {"kind": kind, "sha256": _asset(node["source"], root),
                "presentation": {k: v for k, v in node.get("presentation", {}).get("html", {}).get(
                    "attributes", {}).items() if k in {"style", "class", "width", "height"}}}
    if kind in {"table", "table_row", "table_cell", "table_head", "table_body",
                "column", "column_group", "heading", "line_break"}:
        result = {k: node[k] for k in ("kind", "header", "rowspan", "colspan", "level") if k in node}
        attrs = node.get("presentation", {}).get("html", {}).get("attributes", {})
        result["presentation"] = {k: v for k, v in attrs.items() if k in {"class", "style"}}
        result["children"] = children
        return result
    presentation = node.get("presentation", {}).get("html", {}).get("attributes", {})
    if children or presentation.get("style"):
        # Preserve geometry-bearing wrappers, but not translated text containers.
        return {"kind": kind, "layout": {k: v for k, v in presentation.items()
                                         if k in {"style", "class"}}, "children": children}
    return None


def component_reference(spec):
    """Normalize only the build directory; page+fragment is still explicit."""
    path, separator, fragment = spec["source_ref"].partition("#")
    return Path(path).name + separator + fragment


def component_references(raw):
    """Use source-carried component identities, not position-derived counters."""
    def visit(node):
        if node.get("kind") == "component":
            spec = node["component_spec"]
            if spec.get("language", "und") not in {"und", raw["language"]}:
                raise ValueError("component language differs from candidate language")
            yield component_reference(spec)
        for child in node.get("children", []) + node.get("carrier_flow", []):
            yield from visit(child)
    return [ref for page in raw["pages"] for block in page["blocks"]
            for ref in visit(block["payload"])]


def summarize_language_structure(raw: dict, package_root: Path, page_map: dict,
                                 component_map: dict) -> dict:
    """Summarize with a trusted exact page→semantic-slot map (no suffix guessing)."""
    ids = [p["page_id"] for p in raw["pages"]]
    if len(ids) != len(set(ids)) or set(ids) != set(page_map):
        raise ValueError("baseline page mapping must exactly cover the candidate pages")
    if (any(not isinstance(v, str) or not v.strip() for v in page_map.values())
            or len(set(page_map.values())) != len(page_map)):
        raise ValueError("baseline semantic page slots must be nonempty and unique")
    refs = component_references(raw)
    if len(refs) != len(set(refs)) or set(refs) != set(component_map):
        raise ValueError("baseline component mapping must exactly cover unique source references")
    if (any(not isinstance(v, str) or not v.strip() for v in component_map.values())
            or len(set(component_map.values())) != len(component_map)):
        raise ValueError("baseline semantic component slots must be nonempty and unique")
    pages = []
    for page in raw["pages"]:
        items = [v for b in page["blocks"] if (v := _flow(b["payload"], package_root, component_map)) is not None]
        pages.append({"slot": page_map[page["page_id"]], "items": items})
    return {"model": raw["model"], "region": raw["region"], "pages": pages,
            "style_contract_sha256": raw.get("style_contract_sha256"),
            "web_contract_sha256": digest(raw.get("metadata", {}).get("web_contract")),
            "component_registry_sha256": raw.get("metadata", {}).get("component_registry_sha256"),
            "manual_theme": raw.get("metadata", {}).get("manual_theme")}


def _differences(expected, actual, path="") -> list[dict]:
    """Exact leaf deltas; no wildcard/page-wide exception can mask later changes."""
    absent = {"$absent": True}
    if expected == actual:
        return []
    if isinstance(expected, dict) and isinstance(actual, dict) and absent not in (expected, actual):
        return [d for key in sorted(expected.keys() | actual.keys()) for d in _differences(
            expected.get(key, absent), actual.get(key, absent),
            path + "/" + key.replace("~", "~0").replace("/", "~1"))]
    if isinstance(expected, list) and isinstance(actual, list):
        return [d for index in range(max(len(expected), len(actual)))
                for d in _differences(
                    expected[index] if index < len(expected) else absent,
                    actual[index] if index < len(actual) else absent, path + "/" + str(index))]
    if expected == actual:
        return []
    return [{"path": path, "expected": expected, "actual": actual,
             "expected_sha256": digest(expected), "actual_sha256": digest(actual)}]


def structure_differences(expected, actual):
    """Report JSON pointers together with their reviewed chapter/component slot."""
    deltas = _differences(expected, actual)
    for delta in deltas:
        for tree in (actual, expected):
            node = tree
            for part in delta["path"].split("/")[1:]:
                try:
                    node = node[int(part)] if isinstance(node, list) else node[part.replace("~1", "/").replace("~0", "~")]
                except (KeyError, IndexError, TypeError, ValueError):
                    break
                if isinstance(node, dict) and "slot" in node:
                    field = "component_slot" if node.get("kind") == "component" else "chapter"
                    delta.setdefault(field, node["slot"])
    return deltas
