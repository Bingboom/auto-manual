"""Deprecated-terminology scan over a built bundle.

The Style Guide fixes one preferred wording per concept per language (main
power button, indicator, grid power, …).  Once a term is retired its old
form can still reappear: a template edit copied from an older manual, a
source-table row that was never re-synced, a hand edit in a review page.
This check reads ``data/terminology_rules.csv`` and reports every surviving
occurrence in the bundle's own language pages, so the drift surfaces at
build time instead of during a manual read-through.

Findings are reported as ``TERMINOLOGY_DEPRECATED`` — a warning code, so a
new rule can be registered without blocking builds while its hits are being
cleaned up.  Each rule may carry ``allow_regex`` for the contexts where the
old wording is deliberate (an intentional first-mention gloss, a
placeholder token), and those spans are removed before matching.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

RULES_CSV = "terminology_rules.csv"

# The bundle keeps one page directory per language; ``page`` holds the
# default-language pages and ``generated`` the data-driven ones.
_PAGE_DIRS = ("page", "generated")


def load_rules(data_dir: Path) -> list[dict[str, str]]:
    """Read the rule table; an absent file simply disables the check."""
    path = data_dir / RULES_CSV
    if not path.exists():
        return []
    rules: list[dict[str, str]] = []
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rule_id = (row.get("rule_id") or "").strip()
            pattern = (row.get("deprecated_regex") or "").strip()
            if not rule_id or not pattern:
                continue
            rules.append(
                {
                    "rule_id": rule_id,
                    "lang": (row.get("lang") or "").strip(),
                    "deprecated_regex": pattern,
                    "preferred": (row.get("preferred") or "").strip(),
                    "allow_regex": (row.get("allow_regex") or "").strip(),
                    "note": (row.get("note") or "").strip(),
                }
            )
    return rules


def page_language(path: Path, *, default_lang: str | None) -> str | None:
    """Infer a page's language from its filename suffix.

    Generated pages are named ``<stem>_<lang>.rst``; authored pages carry no
    suffix and belong to the target's own language.
    """
    stem = path.stem
    if "_" in stem:
        suffix = stem.rsplit("_", 1)[1]
        if re.fullmatch(r"[a-z]{2}(-[a-zA-Z]{2,4})?", suffix):
            return suffix
    return default_lang


def scan_text(text: str, rule: dict[str, str]) -> list[str]:
    """Return the deprecated spans in ``text`` that the rule does not allow."""
    allow = rule.get("allow_regex") or ""
    if allow:
        text = re.sub(allow, " ", text)
    return re.findall(rule["deprecated_regex"], text, flags=re.MULTILINE)


def collect_terminology_issues(
    *,
    bundle_dir: Path,
    data_dir: Path,
    model: str | None,
    region: str | None,
    lang: str | None = None,
    issue_cls: type[Any],
) -> list[Any]:
    rules = load_rules(data_dir)
    if not rules:
        return []
    by_lang: dict[str, list[dict[str, str]]] = {}
    for rule in rules:
        by_lang.setdefault(rule["lang"], []).append(rule)

    issues: list[Any] = []
    for page_dir_name in _PAGE_DIRS:
        page_dir = bundle_dir / page_dir_name
        if not page_dir.is_dir():
            continue
        for path in sorted(page_dir.rglob("*.rst")):
            page_lang = page_language(path, default_lang=lang)
            if not page_lang:
                continue
            applicable = by_lang.get(page_lang)
            if not applicable:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for rule in applicable:
                hits = scan_text(text, rule)
                if not hits:
                    continue
                sample = hits[0] if isinstance(hits[0], str) else "".join(hits[0])
                preferred = rule["preferred"]
                advice = f"; use {preferred}" if preferred else ""
                issues.append(
                    issue_cls(
                        code="TERMINOLOGY_DEPRECATED",
                        message=(
                            f"rule {rule['rule_id']} matched {len(hits)} time(s) "
                            f"in {path.name} (first: '{sample}'){advice}"
                        ),
                        model=model,
                        region=region,
                        lang=page_lang,
                        path=path,
                    )
                )
    return issues
