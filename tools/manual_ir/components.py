"""ComponentSpec nodes embedded in renderer-neutral manual flow."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.registry import require_valid_component_spec


_COMPONENT_SPEC_FIELDS = frozenset(
    {
        "schema_version",
        "component_id",
        "variant",
        "source_ref",
        "language",
        "slots",
        "assets",
        "token_roles",
        "metadata",
    }
)


def _component_spec(payload: Any, *, location: str) -> ComponentSpec:
    if not isinstance(payload, Mapping):
        raise ComponentSpecError(f"{location}: expected a mapping")
    extra = set(payload) - _COMPONENT_SPEC_FIELDS
    missing = _COMPONENT_SPEC_FIELDS - set(payload)
    if extra or missing:
        details = []
        if missing:
            details.append("missing " + ", ".join(sorted(missing)))
        if extra:
            details.append("unknown " + ", ".join(sorted(map(str, extra))))
        raise ComponentSpecError(f"{location}: invalid shape ({'; '.join(details)})")
    return require_valid_component_spec(ComponentSpec.from_dict(payload))


def _nested_carrier_node(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("component carrier flow entries must be mappings")
    node = deepcopy(dict(value))
    node.pop("schema_version", None)
    return node


def component_flow_node(
    spec: ComponentSpec,
    *,
    carrier_flow: Sequence[Mapping[str, Any]] = (),
    root: bool = False,
) -> dict[str, Any]:
    """Return one validated v2 flow leaf for a ComponentSpec instance."""

    from tools.manual_ir.flow import FLOW_V2_SCHEMA_VERSION, validate_flow_node

    require_valid_component_spec(spec)
    node: dict[str, Any] = {
        "kind": "component",
        "component_spec": spec.to_dict(),
    }
    if carrier_flow:
        node["carrier_flow"] = [
            _nested_carrier_node(candidate) for candidate in carrier_flow
        ]
    if root:
        node = {"schema_version": FLOW_V2_SCHEMA_VERSION, **node}
        issues = validate_flow_node(node)
        if issues:
            raise ValueError("invalid component flow root: " + "; ".join(issues))
    return node


def validate_component_flow_node(
    node: Mapping[str, Any], *, location: str = "$"
) -> list[str]:
    """Return strict semantic and carrier issues for one component leaf."""

    issues: list[str] = []
    try:
        _component_spec(
            node.get("component_spec"),
            location=f"{location}.component_spec",
        )
    except (ComponentSpecError, TypeError, ValueError) as exc:
        issues.append(str(exc))

    carrier = node.get("carrier_flow")
    if carrier is not None:
        if not isinstance(carrier, (list, tuple)):
            issues.append(f"{location}.carrier_flow: expected an ordered list")
        else:
            from tools.manual_ir.flow import FLOW_V2_SCHEMA_VERSION, _validate_node

            for index, candidate in enumerate(carrier):
                candidate_location = f"{location}.carrier_flow[{index}]"
                candidate_issues = _validate_node(
                    candidate,
                    location=candidate_location,
                    root=False,
                    flow_version=FLOW_V2_SCHEMA_VERSION,
                )
                issues.extend(candidate_issues)
                if isinstance(candidate, Mapping) and candidate.get("kind") == "component":
                    issues.append(
                        f"{candidate_location}: component carrier cannot contain components"
                    )
    return issues


def _walk(nodes: Iterable[Mapping[str, Any]]) -> Iterable[Mapping[str, Any]]:
    for node in nodes:
        yield node
        children = node.get("children")
        if isinstance(children, (list, tuple)):
            yield from _walk(
                child for child in children if isinstance(child, Mapping)
            )


def component_specs_in_flow(
    nodes: Sequence[Mapping[str, Any]],
) -> tuple[ComponentSpec, ...]:
    """Decode embedded ComponentSpecs in deterministic document order."""

    specs: list[ComponentSpec] = []
    source_refs: set[str] = set()
    for node in _walk(nodes):
        if node.get("kind") != "component":
            continue
        spec = _component_spec(node.get("component_spec"), location="component_spec")
        if spec.source_ref in source_refs:
            raise ComponentSpecError(
                f"duplicate embedded component source_ref {spec.source_ref!r}"
            )
        source_refs.add(spec.source_ref)
        specs.append(spec)
    return tuple(specs)


def component_spec_from_flow_node(node: Mapping[str, Any]) -> ComponentSpec:
    """Decode and validate the semantic authority of one component node."""

    if node.get("kind") != "component":
        raise ComponentSpecError("expected a component flow node")
    return _component_spec(node.get("component_spec"), location="component_spec")


__all__ = [
    "component_flow_node",
    "component_spec_from_flow_node",
    "component_specs_in_flow",
    "validate_component_flow_node",
]
