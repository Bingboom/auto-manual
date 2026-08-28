"""Shared public contract types for fixed editable panel components."""
from __future__ import annotations

from typing import Literal


FixedPanelDensity = Literal["standard", "compact"]
FrameRect = tuple[str, tuple[float, float, float, float]]


def normalize_language(language: str) -> str:
    return language.strip().casefold().replace("_", "-").split("-", 1)[0]


__all__ = ["FixedPanelDensity", "FrameRect", "normalize_language"]
