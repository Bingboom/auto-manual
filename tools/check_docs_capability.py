"""Capability -> chapter consistency check.

The build table's feature checkboxes (mirrored to
``data/model_capabilities.csv``) drive which chapters a manual must and
must not carry. ``data/capability_page_rules.csv`` maps each capability
to a page stem (scope=page: the bundle must/must not contain the page)
or to a regex inside a page (scope=section). Enforcement is data-driven
per rule via required_when_true / forbidden_when_false so noisy rules
can stay recorded but inert until their wording is unified.

Targets without a capability row are skipped: absence of inventory data
is not a defect, and legacy lines must keep passing check.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CAPABILITIES_CSV = "model_capabilities.csv"
RULES_CSV = "capability_page_rules.csv"


def load_capabilities(data_dir: Path) -> dict[str, dict[str, bool]]:
    """Document_key -> {capability: bool}."""
    path = data_dir / CAPABILITIES_CSV
    if not path.exists():
        return {}
    out: dict[str, dict[str, bool]] = {}
    for row in csv.DictReader(path.open(encoding="utf-8")):
        key = (row.get("Document_key") or "").strip()
        if not key:
            continue
        out[key] = {
            k: v.strip().upper() == "TRUE"
            for k, v in row.items()
            if k not in ("Document_key", "Project") and v is not None
        }
    return out


def load_rules(data_dir: Path) -> list[dict[str, str]]:
    path = data_dir / RULES_CSV
    if not path.exists():
        return []
    return [
        {k: (v or "").strip() for k, v in row.items()}
        for row in csv.DictReader(path.open(encoding="utf-8"))
        if (row.get("capability") or "").strip()
    ]


def _pages_matching(bundle_dir: Path, stem_pattern: str) -> list[Path]:
    page_dir = bundle_dir / "page"
    if not page_dir.is_dir():
        return []
    stems = [s for s in stem_pattern.split("|") if s]
    return sorted(
        p for p in page_dir.glob("*.rst")
        if any(s in p.stem for s in stems)
    )


def collect_capability_issues(*, bundle_dir: Path, model: str, region: str,
                              data_dir: Path, issue_cls) -> list:
    caps = load_capabilities(data_dir).get(f"{model}_{region}")
    if caps is None:
        return []
    issues: list = []
    for rule in load_rules(data_dir):
        cap_name = rule["capability"]
        if cap_name not in caps:
            continue
        has_cap = caps[cap_name]
        require = has_cap and rule.get("required_when_true") == "Y"
        forbid = (not has_cap) and rule.get("forbidden_when_false") == "Y"
        if not (require or forbid):
            continue
        pages = _pages_matching(bundle_dir, rule["page_stem"])
        if rule.get("scope") == "section":
            regex = re.compile(rule.get("match_regex") or r"(?!)")
            pages = [p for p in pages
                     if regex.search(p.read_text(encoding="utf-8", errors="replace"))]
        found = bool(pages)
        if require and not found:
            issues.append(issue_cls(
                code="CAPABILITY_CONTENT_MISSING",
                message=(f"capability '{cap_name}' is TRUE for {model}_{region} "
                         f"but no bundle {rule['scope']} matches "
                         f"'{rule['page_stem']}'"
                         + (f" ~ /{rule['match_regex']}/" if rule.get("scope") == "section" else "")),
                model=model, region=region, path=bundle_dir / "page",
            ))
        elif forbid and found:
            issues.append(issue_cls(
                code="CAPABILITY_CONTENT_UNEXPECTED",
                message=(f"capability '{cap_name}' is FALSE for {model}_{region} "
                         f"but the bundle carries {', '.join(p.name for p in pages)}"),
                model=model, region=region, path=pages[0],
            ))
    return issues
