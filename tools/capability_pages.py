"""Capability-conditional page selection at bundle-plan time.

A family manifest declares the superset of pages; entries carrying a
``capability:`` key are kept or dropped per target using the same
``data/model_capabilities.csv`` mirror the check gate reads. Targets
without a capability row keep every page — missing inventory data must
never change what an existing line builds.

This is the assembly-side half of the loop; check_docs_capability is
the verification-side half (a page the filter dropped but a stray
template still ships, or vice versa, fails check).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.check_docs_capability import load_capabilities


def filter_pages_by_capability(
    pages: list[Any],
    *,
    model: str | None,
    region: str | None,
    data_dir: Path,
) -> tuple[list[Any], list[str]]:
    """Returns (kept_pages, drop_notes)."""
    if not model or not region:
        return list(pages), []
    caps = load_capabilities(data_dir).get(f"{model}_{region}")
    if caps is None:
        return list(pages), []
    kept: list[Any] = []
    notes: list[str] = []
    for page in pages:
        capability = getattr(page, "capability", None)
        if capability and capability in caps and not caps[capability]:
            label = (getattr(page, "file", None)
                     or getattr(page, "page", None)
                     or page.page_type)
            notes.append(
                f"capability '{capability}' is FALSE for {model}_{region}: "
                f"dropped {label}")
            continue
        kept.append(page)
    return kept, notes
