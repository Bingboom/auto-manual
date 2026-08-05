"""Token bundle for the standard editable safety-warning panel."""
from __future__ import annotations

from dataclasses import dataclass

from ..params import param_pt


@dataclass(frozen=True)
class SafetyWarningStyle:
    icon_column_width: float
    icon_max_width: float
    panel_min_height: float

    @classmethod
    def from_params(
        cls,
        params: dict[str, tuple[str, str]],
    ) -> SafetyWarningStyle:
        return cls(
            icon_column_width=param_pt(
                params,
                "idml_safety_warning_icon_column_width",
                24.0,
            ),
            icon_max_width=param_pt(
                params,
                "idml_safety_warning_icon_max_width",
                18.0,
            ),
            panel_min_height=param_pt(
                params,
                "idml_safety_warning_panel_min_height",
                28.0,
            ),
        )
