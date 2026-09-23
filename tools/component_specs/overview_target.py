"""Optional exact-target lookup for governed Overview component instances."""
from __future__ import annotations

from typing import Any, Mapping

from tools.component_specs.model import ComponentSpecError
from tools.component_specs.overview_instance import (
    load_overview_instance_registry,
    resolve_overview_instance,
)


def find_overview_instance(
    *,
    model: str | None,
    region: str | None,
    registry: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Return one registered target instance without failing on no match."""
    active = dict(registry or load_overview_instance_registry())
    matches = []
    for instance_id in active["instances"]:
        instance = resolve_overview_instance(
            model=None,
            region=None,
            instance_id=str(instance_id),
            registry=active,
        )
        target = instance["target"]
        if (
            str(target["model"]).casefold() == str(model or "").casefold()
            and str(target["region"]).casefold() == str(region or "").casefold()
        ):
            matches.append(instance)
    if len(matches) > 1:
        raise ComponentSpecError(
            f"expected one overview instance for {model!r}/{region!r}; "
            f"found {len(matches)}"
        )
    return matches[0] if matches else None


__all__ = ["find_overview_instance"]
