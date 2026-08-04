"""Capability-conditional page and section selection at assembly time.

A family manifest declares the superset of pages; entries carrying a
``capability:`` key are kept or dropped per target using the same
``data/model_capabilities.csv`` mirror the check gate reads. Targets
without a capability row keep every page — missing inventory data must
never change what an existing line builds.

Page granularity is not always enough: one region's template set serves
several models, and a feature can be present on one of them and absent on
another (JE-1000F_EU has AC/DC output resume, JE-2000F_EU does not, and
both build from ``page_eu-*``). Templates therefore also mark individual
sections with a pair of sentinel comments::

    .. hb-capability-begin: AC/DC输出记忆恢复

    AC and DC Output Resume Function
    --------------------------------

    ...body...

    .. hb-capability-end:

The markers are RST comments, so an unprocessed template still parses and
renders its body — the failure mode is a visible leftover marker, never a
silently missing section. ``strip_capability_sections`` drops the marked
span when the capability is FALSE and drops only the two marker lines when
it is TRUE, so pages of lines that do have the feature keep their exact
bytes (and their pinned reference-layout digests).

This is the assembly-side half of the loop; check_docs_capability is
the verification-side half (a page the filter dropped but a stray
template still ships, or vice versa, fails check).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tools.check_docs_capability import load_capabilities

SECTION_BEGIN_RE = re.compile(r"^\.\.[ \t]+hb-capability-begin:[ \t]*(?P<name>\S.*?)[ \t]*$")
SECTION_END_RE = re.compile(r"^\.\.[ \t]+hb-capability-end:[ \t]*$")
_MARKER_HINT_RE = re.compile(r"hb-capability-(begin|end)")


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


def _marked_spans(lines: list[str], *, label: str) -> list[tuple[int, int, str]]:
    """Returns (begin_index, end_index_inclusive, capability) per marked span."""
    spans: list[tuple[int, int, str]] = []
    open_at: int | None = None
    capability = ""
    for index, line in enumerate(lines):
        begin = SECTION_BEGIN_RE.match(line)
        if begin:
            if open_at is not None:
                raise RuntimeError(
                    f"{label}: nested hb-capability-begin at line {index + 1} "
                    f"(previous still open at line {open_at + 1})"
                )
            open_at, capability = index, begin.group("name")
            continue
        if SECTION_END_RE.match(line):
            if open_at is None:
                raise RuntimeError(
                    f"{label}: hb-capability-end without a matching begin at line {index + 1}"
                )
            spans.append((open_at, index, capability))
            open_at = None
            continue
        if _MARKER_HINT_RE.search(line) and not line.lstrip().startswith(".."):
            continue
    if open_at is not None:
        raise RuntimeError(
            f"{label}: hb-capability-begin at line {open_at + 1} is never closed"
        )
    return spans


def strip_capability_sections(
    text: str,
    *,
    model: str | None,
    region: str | None,
    data_dir: Path,
    label: str = "template",
) -> tuple[str, list[str]]:
    """Resolve hb-capability section markers for one target.

    Returns (text, drop_notes). A FALSE capability drops the whole marked
    span; anything else drops only the two marker lines, leaving the body
    byte-identical to a template that was never marked. Fail-open on missing
    target context or a missing capability row, matching the page filter:
    absent inventory data must not change what an existing line ships.
    """
    if not _MARKER_HINT_RE.search(text):
        return text, []
    lines = text.splitlines(keepends=True)
    spans = _marked_spans([line.rstrip("\n") for line in lines], label=label)
    if not spans:
        return text, []

    caps: dict[str, bool] | None = None
    if model and region:
        caps = load_capabilities(data_dir).get(f"{model}_{region}")

    drop_line = [False] * len(lines)
    notes: list[str] = []
    for begin, end, capability in spans:
        is_false = caps is not None and capability in caps and not caps[capability]
        if is_false:
            for index in range(begin, end + 1):
                drop_line[index] = True
            notes.append(
                f"capability '{capability}' is FALSE for {model}_{region}: "
                f"dropped a marked section in {label}"
            )
        else:
            drop_line[begin] = True
            drop_line[end] = True
    kept = [line for index, line in enumerate(lines) if not drop_line[index]]
    return "".join(kept), notes
