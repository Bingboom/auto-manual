"""Family-scope check for backport classification (Milestone F, PR F3).

Distinguish a **target-local (R)** prose delta from one **shared across the
family (T)** by checking whether the reviewer's old span appears identically in
sibling target sources.

A span that is identical across the family is template-origin shared content. Per
the backport design (``Feishu_Cloud_Doc_Backport_Design.md`` §5.1 R5), such a
span is **flagged for a human decision** (shared template change vs intentional
target-local override) with its blast radius — it is not auto-routed.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_WS_RE = re.compile(r"\s+")


def _normalize(text: str | None) -> str:
    return _WS_RE.sub(" ", (text or "").strip())


def build_family_index(sibling_files: "dict[str, Any] | list[Any]") -> dict[str, list[str]]:
    """Index each normalized non-empty line of every sibling source to its labels.

    ``sibling_files`` is a mapping ``label -> path`` or a list of paths (the path
    string is then the label). A label identifies a sibling target for blast-radius
    reporting.
    """

    if isinstance(sibling_files, dict):
        items = list(sibling_files.items())
    else:
        items = [(str(path), path) for path in sibling_files]

    index: dict[str, set[str]] = {}
    for label, path in items:
        file_path = Path(path)
        if not file_path.exists():
            continue
        for line in file_path.read_text(encoding="utf-8").splitlines():
            key = _normalize(line)
            if not key:
                continue
            index.setdefault(key, set()).add(str(label))
    return {key: sorted(labels) for key, labels in index.items()}


def classify_family_scope(
    text: str | None, family_index: dict[str, list[str]] | None
) -> dict[str, Any] | None:
    """Return ``{"shared": True, "targets": [...]}`` if the span is shared, else None."""

    if not family_index:
        return None
    targets = family_index.get(_normalize(text))
    if not targets:
        return None
    return {"shared": True, "targets": list(targets)}
