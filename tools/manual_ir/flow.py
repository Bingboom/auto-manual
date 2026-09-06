"""Renderer-neutral document flow and rich-text nodes.

HTML is one source/consumer adapter, not the serialized semantic vocabulary.
The optional ``presentation.html.attributes`` payload preserves Web-only
classes and styles during migration; it never owns links, assets, anchors,
table spans or accessibility state.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Mapping, Sequence

from bs4 import BeautifulSoup, Comment, NavigableString, Tag


FLOW_V1_SCHEMA_VERSION = "manual-flow/v1"
FLOW_V2_SCHEMA_VERSION = "manual-flow/v2"
SUPPORTED_FLOW_SCHEMA_VERSIONS = frozenset(
    {FLOW_V1_SCHEMA_VERSION, FLOW_V2_SCHEMA_VERSION}
)

# Compatibility alias for callers that produce the historical flow carrier.
FLOW_SCHEMA_VERSION = FLOW_V1_SCHEMA_VERSION

_TAG_KIND = {
    "section": "section",
    "div": "group",
    "span": "inline_group",
    "p": "paragraph",
    "table": "table",
    "thead": "table_head",
    "tbody": "table_body",
    "tfoot": "table_foot",
    "tr": "table_row",
    "td": "table_cell",
    "th": "table_cell",
    "colgroup": "column_group",
    "col": "column",
    "img": "image",
    "figure": "figure",
    "figcaption": "caption",
    "caption": "caption",
    "a": "link",
    "ul": "list",
    "ol": "list",
    "li": "list_item",
    "dl": "definition_list",
    "dt": "definition_term",
    "dd": "definition_description",
    "strong": "strong",
    "b": "strong",
    "em": "emphasis",
    "i": "emphasis",
    "sup": "superscript",
    "sub": "subscript",
    "br": "line_break",
    "hr": "thematic_break",
    "blockquote": "quote",
    "pre": "preformatted",
    "code": "code",
    "small": "small_text",
    "abbr": "abbreviation",
    "aside": "group",
    "header": "group",
    "footer": "group",
}
for _level in range(1, 7):
    _TAG_KIND[f"h{_level}"] = "heading"

_GROUP_ROLES = frozenset({"container", "aside", "header", "footer"})
_LEAF_KINDS = frozenset(
    {"image", "column", "line_break", "thematic_break", "component"}
)
_TEXT_KINDS = frozenset({"text", "comment"})
FLOW_KINDS = frozenset({*_TAG_KIND.values(), *_TEXT_KINDS, "component"})

_BASE_FIELDS = frozenset({"schema_version", "kind"})
_ELEMENT_FIELDS = frozenset({"presentation", "anchor", "hidden"})
_KIND_FIELDS = {
    "text": frozenset({"text"}),
    "comment": frozenset({"text"}),
    "heading": frozenset({"level"}),
    "group": frozenset({"role"}),
    "list": frozenset({"ordered", "start", "reversed"}),
    "table_cell": frozenset(
        {"header", "row_span", "column_span", "scope"}
    ),
    "column": frozenset({"span"}),
    "image": frozenset({"source", "alt"}),
    "link": frozenset({"target"}),
    "abbreviation": frozenset({"expansion"}),
    "component": frozenset({"component_spec", "carrier_flow"}),
}
_SEMANTIC_HTML_ATTRIBUTES = frozenset(
    {
        "id",
        "aria-hidden",
        "href",
        "src",
        "alt",
        "rowspan",
        "colspan",
        "scope",
        "start",
        "reversed",
        "span",
    }
)


def _positive_int(value: Any, *, owner: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{owner} must be a positive integer")
    try:
        parsed = int(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{owner} must be a positive integer") from exc
    if parsed < 1:
        raise ValueError(f"{owner} must be a positive integer")
    return parsed


def _integer(value: Any, *, owner: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{owner} must be an integer")
    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{owner} must be an integer") from exc


def _hidden(value: Any) -> bool:
    normalized = str(value).strip().casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError("aria-hidden must be true or false")


def _presentation(attributes: Mapping[str, Any]) -> dict[str, Any] | None:
    if not attributes:
        return None
    return {"html": {"attributes": dict(attributes)}}


def _encode(node: Any, *, root: bool = False) -> dict[str, Any]:
    if isinstance(node, Comment):
        result: dict[str, Any] = {"kind": "comment", "text": str(node)}
    elif isinstance(node, NavigableString):
        result = {"kind": "text", "text": str(node)}
    elif isinstance(node, Tag):
        tag = str(node.name or "").casefold()
        kind = _TAG_KIND.get(tag)
        if kind is None:
            raise ValueError(f"unsupported document content: {node.name}")

        attributes = dict(node.attrs)
        result = {"kind": kind}

        anchor = attributes.pop("id", None)
        if anchor is not None:
            result["anchor"] = str(anchor)
        aria_hidden = attributes.pop("aria-hidden", None)
        if aria_hidden is not None:
            result["hidden"] = _hidden(aria_hidden)

        if kind == "heading":
            result["level"] = int(tag[1:])
        elif kind == "group":
            result["role"] = tag if tag in _GROUP_ROLES else "container"
        elif kind == "list":
            result["ordered"] = tag == "ol"
            if "start" in attributes:
                result["start"] = _integer(
                    attributes.pop("start"), owner="list start"
                )
            if "reversed" in attributes:
                raw_reversed = attributes.pop("reversed")
                result["reversed"] = raw_reversed is not False
        elif kind == "table_cell":
            result["header"] = tag == "th"
            if "rowspan" in attributes:
                result["row_span"] = _positive_int(
                    attributes.pop("rowspan"), owner="table row_span"
                )
            if "colspan" in attributes:
                result["column_span"] = _positive_int(
                    attributes.pop("colspan"), owner="table column_span"
                )
            if "scope" in attributes:
                result["scope"] = str(attributes.pop("scope"))
        elif kind == "column" and "span" in attributes:
            result["span"] = _positive_int(
                attributes.pop("span"), owner="column span"
            )
        elif kind == "image":
            source = str(attributes.pop("src", "")).strip()
            if not source:
                raise ValueError("document image requires src")
            result["source"] = source
            if "alt" in attributes:
                result["alt"] = str(attributes.pop("alt"))
        elif kind == "link":
            target = str(attributes.pop("href", "")).strip()
            if not target:
                raise ValueError("document link requires href")
            result["target"] = target
        elif kind == "abbreviation" and "title" in attributes:
            result["expansion"] = str(attributes.pop("title"))

        unexpected = set(attributes) & _SEMANTIC_HTML_ATTRIBUTES
        if unexpected:
            raise ValueError(
                f"semantic HTML attributes are invalid on {tag}: "
                + ", ".join(sorted(unexpected))
            )
        presentation = _presentation(attributes)
        if presentation is not None:
            result["presentation"] = presentation
        if kind not in _LEAF_KINDS:
            result["children"] = [_encode(child) for child in node.children]
    else:
        raise ValueError(
            f"unsupported document content: {getattr(node, 'name', type(node))}"
        )

    if root:
        result = {"schema_version": FLOW_SCHEMA_VERSION, **result}
    return result


def html_to_flow_nodes(markup: str) -> tuple[dict[str, Any], ...]:
    """Decode one prepared HTML fragment into ordered neutral flow roots."""

    soup = BeautifulSoup(markup, "html.parser")
    nodes = tuple(_encode(node, root=True) for node in soup.contents)
    # Keep a page-level block identity even when an adapter produces an empty
    # fragment. An empty text root renders back to exactly the empty string.
    if not nodes:
        nodes = ({
            "schema_version": FLOW_SCHEMA_VERSION,
            "kind": "text",
            "text": "",
        },)
    for index, node in enumerate(nodes):
        issues = validate_flow_node(node)
        if issues:
            raise ValueError(
                f"invalid neutral flow root {index}: " + "; ".join(issues)
            )
    return nodes


def _presentation_issues(
    value: Any, *, location: str, kind: str
) -> list[str]:
    if not isinstance(value, Mapping) or set(value) != {"html"}:
        return [f"{location}: presentation must contain only html"]
    html = value.get("html")
    if not isinstance(html, Mapping) or set(html) != {"attributes"}:
        return [f"{location}.html: must contain only attributes"]
    attributes = html.get("attributes")
    if not isinstance(attributes, Mapping) or not attributes:
        return [f"{location}.html.attributes: expected a non-empty object"]
    issues: list[str] = []
    for key, item in attributes.items():
        if not isinstance(key, str) or not key.strip():
            issues.append(f"{location}.html.attributes: keys must be non-empty strings")
            continue
        normalized_key = key.casefold()
        if key != normalized_key:
            issues.append(
                f"{location}.html.attributes.{key}: HTML attribute names must be lowercase"
            )
        semantic_attributes = _SEMANTIC_HTML_ATTRIBUTES | (
            {"title"} if kind == "abbreviation" else set()
        )
        if normalized_key in semantic_attributes:
            issues.append(
                f"{location}.html.attributes.{key}: semantic attribute must live in the flow node"
            )
        if not (
            isinstance(item, str)
            or isinstance(item, list)
            and all(isinstance(part, str) for part in item)
        ):
            issues.append(
                f"{location}.html.attributes.{key}: expected a string or string list"
            )
    return issues


def _validate_node(
    node: Any,
    *,
    location: str,
    root: bool,
    flow_version: str | None = None,
    component_registry: Mapping[str, Any] | None = None,
) -> list[str]:
    if not isinstance(node, Mapping):
        return [f"{location}: flow node must be an object"]
    issues: list[str] = []
    kind = node.get("kind")
    if kind not in FLOW_KINDS:
        return [f"{location}.kind: unknown kind {kind!r}"]

    expected_fields = _BASE_FIELDS | _KIND_FIELDS.get(str(kind), frozenset())
    if kind not in _TEXT_KINDS:
        expected_fields |= _ELEMENT_FIELDS
    if kind not in _TEXT_KINDS | _LEAF_KINDS:
        expected_fields |= {"children"}
    extra = set(node) - expected_fields
    if extra:
        issues.append(
            f"{location}: unknown field(s): " + ", ".join(sorted(map(str, extra)))
        )
    active_flow_version = flow_version
    if root:
        active_flow_version = node.get("schema_version")
        if active_flow_version not in SUPPORTED_FLOW_SCHEMA_VERSIONS:
            issues.append(
                f"{location}.schema_version: must be one of "
                f"{sorted(SUPPORTED_FLOW_SCHEMA_VERSIONS)!r}"
            )
    elif "schema_version" in node:
        issues.append(f"{location}.schema_version: allowed only on a flow root")

    if kind == "component":
        if active_flow_version != FLOW_V2_SCHEMA_VERSION:
            issues.append(
                f"{location}: component requires {FLOW_V2_SCHEMA_VERSION}"
            )
        try:
            from tools.manual_ir.components import validate_component_flow_node

            issues.extend(
                validate_component_flow_node(
                    node,
                    location=location,
                    component_registry=component_registry,
                )
            )
        except (ImportError, RuntimeError) as exc:
            issues.append(f"{location}.component_spec: cannot validate: {exc}")
    elif kind in _TEXT_KINDS:
        if not isinstance(node.get("text"), str):
            issues.append(f"{location}.text: expected a string")
        if "children" in node:
            issues.append(f"{location}.children: {kind} cannot have children")
    elif kind in _LEAF_KINDS:
        if "children" in node:
            issues.append(f"{location}.children: {kind} cannot have children")
    else:
        children = node.get("children")
        if not isinstance(children, (list, tuple)):
            issues.append(f"{location}.children: expected an ordered list")
        else:
            for index, child in enumerate(children):
                issues.extend(
                    _validate_node(
                        child,
                        location=f"{location}.children[{index}]",
                        root=False,
                        flow_version=active_flow_version,
                        component_registry=component_registry,
                    )
                )

    for field in ("anchor", "scope", "target", "source", "alt", "expansion"):
        if field in node and not isinstance(node[field], str):
            issues.append(f"{location}.{field}: expected a string")
    for field in ("hidden", "ordered", "reversed", "header"):
        if field in node and not isinstance(node[field], bool):
            issues.append(f"{location}.{field}: expected boolean")
    for field in ("level", "row_span", "column_span", "span"):
        if field in node and (
            type(node[field]) is not int or int(node[field]) < 1
        ):
            issues.append(f"{location}.{field}: expected a positive integer")
    if "start" in node and type(node["start"]) is not int:
        issues.append(f"{location}.start: expected an integer")

    if kind == "heading" and node.get("level") not in range(1, 7):
        issues.append(f"{location}.level: expected 1 through 6")
    if kind == "group" and node.get("role") not in _GROUP_ROLES:
        issues.append(f"{location}.role: unsupported group role {node.get('role')!r}")
    if kind == "list" and not isinstance(node.get("ordered"), bool):
        issues.append(f"{location}.ordered: required boolean")
    if kind == "table_cell" and not isinstance(node.get("header"), bool):
        issues.append(f"{location}.header: required boolean")
    if kind == "table_cell" and "scope" in node and node["scope"] not in {
        "row", "col", "rowgroup", "colgroup",
    }:
        issues.append(f"{location}.scope: unsupported table scope {node['scope']!r}")
    if kind == "image" and (
        not isinstance(node.get("source"), str) or not node["source"].strip()
    ):
        issues.append(f"{location}.source: required non-empty string")
    if kind == "link" and (
        not isinstance(node.get("target"), str) or not node["target"].strip()
    ):
        issues.append(f"{location}.target: required non-empty string")

    if "presentation" in node:
        issues.extend(
            _presentation_issues(
                node["presentation"],
                location=f"{location}.presentation",
                kind=str(kind),
            )
        )
    return issues


def validate_flow_node(
    node: Any,
    *,
    component_registry: Mapping[str, Any] | None = None,
) -> list[str]:
    """Return strict neutral-flow issues for one top-level block payload."""

    return _validate_node(
        node,
        location="$",
        root=True,
        component_registry=component_registry,
    )


def _tag_for(node: Mapping[str, Any], *, parent_kind: str | None) -> str:
    kind = str(node["kind"])
    if kind == "heading":
        return f"h{node['level']}"
    if kind == "group":
        role = str(node["role"])
        return "div" if role == "container" else role
    if kind == "list":
        return "ol" if node["ordered"] else "ul"
    if kind == "table_cell":
        return "th" if node["header"] else "td"
    if kind == "caption":
        return "caption" if parent_kind == "table" else "figcaption"
    return {
        "section": "section",
        "inline_group": "span",
        "paragraph": "p",
        "table": "table",
        "table_head": "thead",
        "table_body": "tbody",
        "table_foot": "tfoot",
        "table_row": "tr",
        "column_group": "colgroup",
        "column": "col",
        "image": "img",
        "figure": "figure",
        "link": "a",
        "list_item": "li",
        "definition_list": "dl",
        "definition_term": "dt",
        "definition_description": "dd",
        "strong": "strong",
        "emphasis": "em",
        "superscript": "sup",
        "subscript": "sub",
        "line_break": "br",
        "thematic_break": "hr",
        "quote": "blockquote",
        "preformatted": "pre",
        "code": "code",
        "small_text": "small",
        "abbreviation": "abbr",
    }[kind]


def _html_attributes(node: Mapping[str, Any]) -> dict[str, Any]:
    presentation = node.get("presentation")
    attributes = dict(
        presentation.get("html", {}).get("attributes", {})
        if isinstance(presentation, Mapping)
        else {}
    )
    if "anchor" in node:
        attributes["id"] = node["anchor"]
    if "hidden" in node:
        attributes["aria-hidden"] = "true" if node["hidden"] else "false"
    if node["kind"] == "link":
        attributes["href"] = node["target"]
    elif node["kind"] == "image":
        attributes["src"] = node["source"]
        if "alt" in node:
            attributes["alt"] = node["alt"]
    elif node["kind"] == "table_cell":
        if "row_span" in node:
            attributes["rowspan"] = str(node["row_span"])
        if "column_span" in node:
            attributes["colspan"] = str(node["column_span"])
        if "scope" in node:
            attributes["scope"] = node["scope"]
    elif node["kind"] == "list":
        if "start" in node:
            attributes["start"] = str(node["start"])
        if node.get("reversed"):
            attributes["reversed"] = ""
    elif node["kind"] == "column" and "span" in node:
        attributes["span"] = str(node["span"])
    elif node["kind"] == "abbreviation" and "expansion" in node:
        attributes["title"] = node["expansion"]
    return attributes


def _decode(
    node: Mapping[str, Any],
    soup: BeautifulSoup,
    *,
    parent_kind: str | None = None,
    component_renderer: Callable[[Mapping[str, Any]], str] | None = None,
    component_fragments: dict[str, str] | None = None,
):
    kind = str(node["kind"])
    if kind == "text":
        return NavigableString(str(node["text"]))
    if kind == "comment":
        return Comment(str(node["text"]))
    if kind == "component":
        if component_renderer is None:
            raise ValueError("component renderer is required for component flow")
        rendered = component_renderer(node)
        if not isinstance(rendered, str):
            raise ValueError("component renderer must return HTML text")
        if component_fragments is None:
            raise ValueError("component fragment collector is required")
        token = f"AUTOMANUALFLOWCOMPONENT{len(component_fragments) + 1:04d}"
        component_fragments[token] = rendered
        return Comment(token)
    tag = soup.new_tag(
        _tag_for(node, parent_kind=parent_kind), attrs=_html_attributes(node)
    )
    for child in node.get("children", []):
        decoded = _decode(
            child,
            soup,
            parent_kind=kind,
            component_renderer=component_renderer,
            component_fragments=component_fragments,
        )
        if isinstance(decoded, list):
            tag.extend(decoded)
        else:
            tag.append(decoded)
    return tag


def flow_nodes_to_html(
    nodes: Sequence[Mapping[str, Any]],
    *,
    component_renderer: Callable[[Mapping[str, Any]], str] | None = None,
    component_registry: Mapping[str, Any] | None = None,
) -> str:
    """Render neutral flow through the Web adapter.

    The neutral kind selects the element. Optional HTML attributes only restore
    presentation details; semantic attributes are rebuilt from neutral fields.
    """

    soup = BeautifulSoup("", "html.parser")
    component_fragments: dict[str, str] = {}
    for index, node in enumerate(nodes):
        issues = validate_flow_node(
            node,
            component_registry=component_registry,
        )
        if issues:
            raise ValueError(
                f"invalid neutral flow root {index}: " + "; ".join(issues)
            )
        decoded = _decode(
            node,
            soup,
            component_renderer=component_renderer,
            component_fragments=component_fragments,
        )
        if isinstance(decoded, list):
            soup.extend(decoded)
        else:
            soup.append(decoded)
    rendered = str(soup)
    for token, fragment in component_fragments.items():
        placeholder = f"<!--{token}-->"
        if rendered.count(placeholder) != 1:
            raise ValueError(f"component placeholder {token} must occur exactly once")
        rendered = rendered.replace(placeholder, fragment)
    return rendered


def strip_presentation_hints(value: Any) -> Any:
    """Return an independent semantic-only copy of nodes or one node."""

    if isinstance(value, (list, tuple)):
        return tuple(strip_presentation_hints(item) for item in value)
    if not isinstance(value, Mapping):
        return deepcopy(value)
    result = {
        key: strip_presentation_hints(item)
        for key, item in value.items()
        if key != "presentation"
    }
    return result


__all__ = [
    "FLOW_KINDS",
    "FLOW_SCHEMA_VERSION",
    "FLOW_V1_SCHEMA_VERSION",
    "FLOW_V2_SCHEMA_VERSION",
    "SUPPORTED_FLOW_SCHEMA_VERSIONS",
    "flow_nodes_to_html",
    "html_to_flow_nodes",
    "strip_presentation_hints",
    "validate_flow_node",
]
