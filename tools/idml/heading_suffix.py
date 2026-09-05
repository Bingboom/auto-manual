"""Promote target-declared H2 suffixes into reusable component specs."""
from __future__ import annotations

import json
import re
from collections.abc import Iterable

Block = tuple[str, str]

# Latin copy writes `Solar Charging (Sold Separately)`: a space, then ASCII
# brackets.  Japanese writes `ソーラー充電（別売）` with full-width brackets and
# no space, which is correct CJK typography and what the shipped JP book prints.
# The two forms stay separate alternatives so the Latin branch matches exactly
# what it matched before, and a mixed pair such as `（x)` is still refused.
#
# The full-width branch keeps its brackets in the pill copy: the shipped JP book
# sets `（別売）` inside the pill, brackets included, where the Latin convention
# drops them and sets `Sold Separately` bare.
_TRAILING_PARENTHETICAL = re.compile(
    r"^(?P<heading>.+?)"
    r"(?:\s+\((?P<ascii_pill>[^()]+)\)"
    r"|\s*(?P<fullwidth_pill>（[^（）]+）))"
    r"\s*$",
    re.S,
)


def split_trailing_parenthetical(text: str) -> tuple[str, str] | None:
    """Return visible heading and final parenthetical copy when unambiguous."""

    match = _TRAILING_PARENTHETICAL.fullmatch(str(text or "").strip())
    if match is None:
        return None
    heading = match.group("heading").strip()
    pill = (
        match.group("ascii_pill") or match.group("fullwidth_pill") or ""
    ).strip()
    if not heading or not pill:
        return None
    return heading, pill


def promote_h2_suffix_pills(
    blocks: list[Block],
    indices: Iterable[int],
    *,
    variant: str | None = None,
) -> list[Block]:
    """Promote zero-based H2 ordinals without matching localized wording."""

    selected = list(indices)
    if any(
        isinstance(index, bool) or not isinstance(index, int) or index < 0
        for index in selected
    ):
        raise ValueError("H2 suffix-pill indices must be non-negative integers")
    if len(set(selected)) != len(selected):
        raise ValueError("H2 suffix-pill indices must be unique")

    selected_set = set(selected)
    promoted: set[int] = set()
    output: list[Block] = []
    h2_index = 0
    for kind, text in blocks:
        if kind != "h2":
            output.append((kind, text))
            continue
        if h2_index not in selected_set:
            output.append((kind, text))
            h2_index += 1
            continue
        split = split_trailing_parenthetical(text)
        if split is None:
            raise ValueError(
                f"H2 suffix-pill index {h2_index} requires a trailing "
                "parenthetical"
            )
        heading, pill = split
        spec = {
            "kind": "headingpill",
            "heading": heading,
            "pill": pill,
        }
        if variant:
            spec["variant"] = variant
        output.append((
            "component",
            json.dumps(spec, ensure_ascii=False),
        ))
        promoted.add(h2_index)
        h2_index += 1

    missing = sorted(selected_set - promoted)
    if missing:
        raise ValueError(
            "H2 suffix-pill indices are outside the source headings: "
            + ", ".join(str(index) for index in missing)
        )
    return output


__all__ = ("promote_h2_suffix_pills", "split_trailing_parenthetical")
