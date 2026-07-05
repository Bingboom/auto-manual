"""FCC component fallback for localized pages that only contain prose."""
from __future__ import annotations

import json

FCC_RIGHT_COLUMN_MARKERS = (
    "if this equipment does cause",
    "si cet équipement trouble",
    "si cet equipement trouble",
    "si cet appareil provoque",
    "si este aparato causa",
    "si este equipo causa",
    "si este dispositivo causa",
)


def component_spec(blocks: list[tuple[str, str]], component_kind: str) -> dict | None:
    for kind, text in blocks:
        if kind != "component":
            continue
        spec = json.loads(text)
        if spec.get("kind") == component_kind:
            return spec
    return None


def split_fcc_prose(parts: list[str]) -> tuple[str, str]:
    left: list[str] = []
    right: list[str] = []
    in_right = False
    for part in parts:
        searchable = part.lower()
        marker_pos = -1
        for marker in FCC_RIGHT_COLUMN_MARKERS:
            marker_pos = searchable.find(marker)
            if marker_pos != -1:
                break
        if marker_pos != -1 and not in_right:
            prefix = part[:marker_pos].strip()
            suffix = part[marker_pos:].strip()
            if prefix:
                left.append(prefix)
            if suffix:
                right.append(suffix)
            in_right = True
        elif in_right:
            right.append(part)
        else:
            left.append(part)

    if not right and len(left) > 1:
        split_at = max(1, (len(left) + 1) // 2)
        right = left[split_at:]
        left = left[:split_at]
    return "\n".join(left).strip(), "\n".join(right).strip()


def fcc_spec_from_blocks(blocks: list[tuple[str, str]]) -> dict:
    spec = component_spec(blocks, "fcc")
    if spec is not None:
        return spec
    prose = [
        text.strip()
        for kind, text in blocks
        if kind in {"body", "list"} and text.strip()
    ]
    left, right = split_fcc_prose(prose)
    return {"kind": "fcc", "texts": [left, right]}
