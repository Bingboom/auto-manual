"""Target-declared corner radii for composed chrome.

Every corner radius in the IDML renderer is read language-neutrally -- through
``param_pt`` / ``component_param_pt`` on a shared ``comp_*`` row, or, more
often, by falling through to a helper's own default. None of them consults a
``lang_<code>_`` key, so a ``lang_jp_comp_inbox_card_arc`` row would be a dead
row that silently changes nothing. That left a book whose approved master
rounds a panel differently with no way to say so: the only lever was the shared
value, which moves every book in every language.

A target's own composition data is the tightest scope available, because the
contract file belongs to one target and nothing else reads it. So a composition
may carry a ``corner_radii`` map from a named piece of chrome to its radius in
points, and the chrome that supports it asks here. Declaring nothing keeps the
shared default, which is what every contract written before this does.

The names are per composition and deliberately describe the chrome rather than
the parameter behind it, so a later move of the shared default does not
invalidate a declaration.
"""
from __future__ import annotations

from collections.abc import Mapping

__all__ = ("declared_radius", "declared_radii")


def declared_radii(composition: Mapping | None) -> dict[str, float]:
    """Return the radii a composition declares, keyed by chrome name."""

    declared = (composition or {}).get("corner_radii") or {}
    if not isinstance(declared, Mapping):
        raise ValueError("corner_radii must be a mapping of chrome name to pt")
    return {str(name): float(value) for name, value in declared.items()}


def declared_radius(
    composition: Mapping | None, role: str, default: float
) -> float:
    """Return the declared radius for ``role``, else the shared ``default``."""

    value = declared_radii(composition).get(role)
    return default if value is None else value
