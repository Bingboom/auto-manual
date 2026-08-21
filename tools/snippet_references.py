#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repo-wide snippet reference discovery for the section-module layer."""

from __future__ import annotations

from pathlib import Path


def repo_wide_snippet_references(docs_dir: Path) -> set[str]:
    """Snippet ids referenced anywhere in the template tree.

    The registry is one global table shared by every line, so orphan-hood is a
    repo-wide property: a snippet the battery-pack line consumes is not an
    orphan just because the JP host target does not use it. Two reference
    forms count — a `{{snippet:<id>}}` token in any template (include pages
    name the id directly) and a recipe's `snippet_slots` binding.
    """

    from tools.draft_engine import SNIPPET_TOKEN_PREFIX, SNIPPET_TOKEN_SUFFIX

    referenced: set[str] = set()
    templates_dir = docs_dir / "templates"
    if not templates_dir.exists():
        return referenced

    for path in templates_dir.rglob("*.rst"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if SNIPPET_TOKEN_PREFIX not in text:
            continue
        cursor = 0
        while True:
            start = text.find(SNIPPET_TOKEN_PREFIX, cursor)
            if start < 0:
                break
            name_start = start + len(SNIPPET_TOKEN_PREFIX)
            end = text.find(SNIPPET_TOKEN_SUFFIX, name_start)
            if end < 0:
                break
            name = text[name_start:end].strip()
            if name:
                referenced.add(name)
            cursor = end + len(SNIPPET_TOKEN_SUFFIX)

    recipes_dir = templates_dir / "recipes"
    if recipes_dir.exists():
        try:
            import yaml
        except ImportError:  # pragma: no cover
            return referenced
        for path in recipes_dir.rglob("*.y*ml"):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            slots = data.get("snippet_slots") if isinstance(data, dict) else None
            if isinstance(slots, dict):
                referenced.update(
                    str(value).strip() for value in slots.values() if str(value).strip()
                )
    return referenced
