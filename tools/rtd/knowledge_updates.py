"""The 知识库首页's 最近更新 list: curated, dated knowledge-page changes.

``tools/rtd_portal_assets/knowledge_updates.yaml`` (schema
``hello-docs-knowledge-updates/v1``) holds one entry per change a reader should
notice: ``date`` (the merge day), ``title``, ``note``, ``page`` (a key of
:data:`PAGES`), an optional ``anchor`` on that page, and ``evidence``
(``pr:<repo>#<n>``) for reviewers, which is never rendered.

No build-time source carries per-page change dates, so the list is curated and
a PR that adds or changes a knowledge page adds its entry. A bad entry is
dropped and an undated one is listed last as 日期未记录; the build only warns
and never substitutes the build date.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

import yaml

UPDATES_NAME = "knowledge_updates.yaml"
UPDATES_SCHEMA = "hello-docs-knowledge-updates/v1"
# Page key -> docname. The share package is not a Sphinx page: the home page links it.
PAGES: dict[str, str | None] = {
    "share": None,
    "product-knowledge": "products/knowledge",
    "product-matrix": "products/matrix",
    "market-policy": "market/policy",
    "deliverables": "workspace/deliverables/index",
    "system": "workspace/system/index",
    "design-system": "workspace/design/index",
    "system-data": "workspace/data/index",
}
_ANCHOR = re.compile(r"[a-z][a-z0-9-]*")


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _entry_problems(raw: dict, where: str) -> list[str]:
    """Why an entry cannot be shown at all; empty when it can."""
    problems = [f"{where}: needs {field}" for field in ("title", "note") if not _text(raw.get(field))]
    page = raw.get("page")
    if not isinstance(page, str) or page not in PAGES:
        problems.append(f"{where}: unknown page {page!r}; use one of {', '.join(PAGES)}")
    anchor = raw.get("anchor")
    if anchor is not None and not (isinstance(anchor, str) and _ANCHOR.fullmatch(anchor)):
        problems.append(f"{where}: anchor {anchor!r} is not a lower-case id")
    return problems


def _entry(raw: object, index: int) -> tuple[dict[str, str] | None, list[str]]:
    """The entry as the view reads it, or None when it is dropped; with the reasons to warn."""
    if not isinstance(raw, dict):
        return None, [f"updates[{index}] is not a mapping"]
    title = _text(raw.get("title"))
    where = f"updates[{index}] ({title})" if title else f"updates[{index}]"
    problems = _entry_problems(raw, where)
    if problems:
        return None, problems
    date = raw.get("date")
    # YAML reads an unquoted YYYY-MM-DD as a date; a timestamp or text is not a merge day.
    dated = type(date) is dt.date
    entry = {"date": date.isoformat() if dated else "", "title": title, "note": _text(raw["note"]),
             "page": raw["page"], "anchor": raw.get("anchor") or ""}
    if dated:
        return entry, []
    return entry, [f"{where}: date {date!r} is not an unquoted YYYY-MM-DD, so it shows 日期未记录"]


def load_updates(assets: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Entries in file order and the problems to warn about.

    An entry with an unknown page key, an empty title or note, or a bad anchor
    is dropped; one without a valid date is kept with ``date=""``. A file that
    cannot be read or names another schema gives no entries and one reason.
    """
    try:
        data = yaml.safe_load((assets / UPDATES_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [], [f"cannot read {UPDATES_NAME}: {exc}"]
    schema = data.get("schema") if isinstance(data, dict) else None
    if schema != UPDATES_SCHEMA:
        return [], [f"{UPDATES_NAME}: schema is {schema!r}, expected {UPDATES_SCHEMA!r}"]
    if not isinstance(data.get("updates"), list):
        return [], [f"{UPDATES_NAME}: updates must be a list"]
    entries: list[dict[str, str]] = []
    problems: list[str] = []
    for index, raw in enumerate(data["updates"]):
        entry, reasons = _entry(raw, index)
        problems += reasons
        if entry is not None:
            entries.append(entry)
    return entries, problems


def updates_view(entries: list[dict[str, str]], built: dict[str, bool], limit: int = 8) -> list[dict[str, Any]]:
    """The newest ``limit`` entries whose page this build made.

    ``built`` maps a page key to whether its page (for ``share``, the sharing
    package) is in this build. Newest first; a tie keeps file order and an
    undated entry sorts after every dated one. Each row carries its docname.
    """
    shown = [entry for entry in entries if built.get(entry["page"])]
    # ISO dates sort as text; the stable sort keeps file order on ties, and "" sorts last.
    shown.sort(key=lambda entry: entry["date"], reverse=True)
    return [{**entry, "docname": PAGES[entry["page"]]} for entry in shown[:limit]]
