"""Read every published Web manual into specification rows and candidate facts for the product matrix base.

``read_publication(root)`` walks every edition the publish manifest lists (every model, market and language), keeps
every specification and specification-like table row with its printed label and value, section path and anchor,
maps each row to an attribute (``labels``), and assembles one candidate value per model × market × attribute from
the primary edition, plus component values and derived figures (``facts``). A row no rule claims is kept and listed
under ``unmapped``. The result is internal product data: callers write it only outside any git work tree.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from tools.product_matrix_base.reader.facts import assign_blocks, map_rows, read_facts
from tools.product_matrix_base.reader.labels import UNMAPPED
from tools.product_matrix_base.reader.walk import read_manual
from tools.rtd.production_evidence import read_publications
from tools.utils.path_utils import Paths, PathSegments, docs_publish_of, docs_publish_web_of

SCHEMA = "hello-docs-matrix-reading/v1"


class ReadingError(ValueError):
    """The publication cannot be read."""


def source_key(target: dict[str, Any]) -> str:
    return f"web/{target['model']}/{target['region']}/{target['lang']}/{target.get('version') or 'unversioned'}"


def _edition(web: Path, target: dict[str, Any], problems: list[str]) -> tuple[dict[str, Any], str]:
    path = (web / target["route"] / target["manual"]).resolve()
    data = path.read_bytes() if path.is_relative_to(web.resolve()) and path.is_file() else None
    if data is None:
        problems.append(f"{target['model']}/{target['region']}/{target['lang']}: published manual is not readable")
    route = f"{target['route']}/{target['manual']}"
    return ({"model": target["model"], "market": target["region"], "language": target["lang"],
             "version": target.get("version") or None, "built_at": target.get("built_at") or None,
             "source_key": source_key(target), "source_file": route,
             "page": f"{target['route']}/{PurePosixPath(target['manual']).stem}.html",
             "sha256": hashlib.sha256(data).hexdigest() if data else None},
            data.decode("utf-8", errors="replace") if data else "")


def _unmapped(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if row.get("attribute_key") != UNMAPPED:
            continue
        entry = found.setdefault((row["language"], row["row_label_clean"]), {
            "language": row["language"], "label": row["row_label_clean"], "rows": 0, "notes": Counter()})
        entry["rows"] += 1
        entry["notes"][row["mapping_note"]] += 1
    return [{**e, "notes": dict(e["notes"])} for e in sorted(found.values(), key=lambda e: (-e["rows"], e["label"]))]


def catalog_names(root: Path, problems: list[str]) -> dict[tuple[str, str], str]:
    """Each model and market's name in the portal's manual catalog (the names the 产品矩阵 shows), if readable."""
    settings_path = Path(__file__).resolve().parents[2] / "rtd_portal_assets" / "settings.json"
    try:
        from tools.rtd.portal import catalog

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        products = catalog(docs_publish_web_of(Paths(root).docs_dir), settings)
    except (ImportError, OSError, ValueError, KeyError) as exc:
        problems.append(f"portal manual catalog unreadable, product names left empty: {exc}")
        return {}
    names: dict[tuple[str, str], str] = {}
    for product in products:
        names.setdefault((product["model"], product["region"]), product.get("name") or "")
    return names


def inside_git_work_tree(path: Path) -> bool:
    """Whether a path would land inside any git work tree (product data never may)."""
    probe = path.resolve()
    return any((parent / ".git").exists() for parent in [probe, *probe.parents])


def read_publication(root: Path) -> dict[str, Any]:
    """Rows, facts, component facts and editions of the Web publication under ``root``'s docs directory."""
    docs = Paths(root).docs_dir
    manifest = docs_publish_of(docs) / PathSegments.PUBLISH_MANIFEST_JSON
    targets, built_at = read_publications(manifest)
    if targets is None:
        raise ReadingError(f"{manifest} is missing or malformed")
    web = docs_publish_web_of(docs)
    problems: list[str] = []
    editions, rows = [], []
    for target in targets:
        edition, text = _edition(web, target, problems)
        captured, spec_seen = read_manual(text, {"model": edition["model"], "region": edition["market"],
                                                 "language": edition["language"],
                                                 "source_file": edition["source_file"]})
        edition.update({"rows": len(captured), "spec_heading": spec_seen})
        if text and not captured:
            problems.append(f"{edition['model']}/{edition['market']}/{edition['language']}: no specification table")
        editions.append(edition)
        rows += captured
    map_rows(rows)
    assign_blocks(rows)
    found = read_facts(rows, editions)
    summary = {"editions": len(editions), "markets": len({(e["model"], e["market"]) for e in editions}),
               "rows": len(rows), "facts": len(found["facts"]), "components": len(found["components"]),
               "unmapped_rows": sum(1 for r in rows if r.get("attribute_key") == UNMAPPED), "problems": len(problems)}
    names = catalog_names(root, problems)
    return {"schema": SCHEMA, "built_at": built_at or None, "names": [[m, k, n] for (m, k), n in sorted(names.items())],
            "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(), "editions": editions,
            "rows": rows, **found, "unmapped": _unmapped(rows), "problems": problems, "summary": summary}


__all__ = ["ReadingError", "SCHEMA", "catalog_names", "inside_git_work_tree", "read_publication", "source_key"]
