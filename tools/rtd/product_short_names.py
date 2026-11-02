"""Product short names (商品简称) that make the manual portal searchable by them.

The RTD build cannot reach Feishu, so the portal reads a repo snapshot,
``product_short_names.json`` beside ``settings.json``: one standard short name
per customer model (no colour variants, bundles, samples or custom editions).
A model the snapshot does not list keeps its current search text.

``refresh`` recomputes the snapshot read-only from the spec table named in the
snapshot's ``source`` block: rows whose 客户型号 equals the model exactly, minus
names containing an excluded marker, most frequent name wins (ties: first
seen). It never writes the live Base.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

SNAPSHOT = "product_short_names.json"


def load_short_names(assets: Path) -> dict[str, str]:
    """``{model: short name}``; a missing snapshot means no short names."""
    path = assets / SNAPSHOT
    if not path.is_file():
        return {}
    names = json.loads(path.read_text(encoding="utf-8")).get("short_names", {})
    if not isinstance(names, dict) or not all(
            isinstance(k, str) and isinstance(v, str) and k and v.strip() for k, v in names.items()):
        raise ValueError(f"{SNAPSHOT}: short_names must map model to a non-empty name")
    return {model: name.strip() for model, name in names.items()}


def attach_short_names(products: list[dict], names: dict[str, str]) -> list[dict]:
    """Give every product a ``short_name`` by exact model match ("" when unlisted)."""
    for product in products:
        product["short_name"] = names.get(product["model"], "")
    return products


def standard_name(candidates: list[str], exclude: list[str]) -> tuple[str, Counter]:
    """The most frequent candidate without an excluded marker, plus all counts."""
    counts = Counter(name for name in (c.strip() for c in candidates)
                     if name and not any(marker in name for marker in exclude))
    return (counts.most_common(1)[0][0] if counts else ""), counts


def short_names_from_rows(rows: list[dict], models: list[str], *, model_field: str,
                          name_field: str, exclude: list[str]) -> tuple[dict[str, str], dict[str, Counter]]:
    from tools.rtd.web_reviews import text_of

    by_model: dict[str, list[str]] = {}
    for row in rows:
        by_model.setdefault(text_of(row.get(model_field)), []).append(text_of(row.get(name_field)))
    names, ambiguous = {}, {}
    for model in models:
        name, counts = standard_name(by_model.get(model, []), exclude)
        if name:
            names[model] = name
        if len(counts) > 1:
            ambiguous[model] = counts
    return names, ambiguous


def main(argv: list[str] | None = None) -> int:
    from tools.rtd.portal import ASSETS

    parser = argparse.ArgumentParser(description="Refresh the portal's product short-name snapshot (read-only).")
    commands = parser.add_subparsers(dest="command", required=True)
    refresh = commands.add_parser("refresh", help="recompute the snapshot from the spec table")
    refresh.add_argument("--model", action="append", default=[],
                         help="also look up this customer model (repeatable); listed models are always refreshed")
    refresh.add_argument("--cli-bin", default="lark-cli", help='lark-cli command, e.g. "lark-cli --profile prod"')
    refresh.add_argument("--as", dest="identity", default=os.environ.get("FEISHU_PUBLISHED_DOCS_IDENTITY", "bot"),
                         help="lark-cli identity (default: $FEISHU_PUBLISHED_DOCS_IDENTITY or bot)")
    refresh.add_argument("--dry-run", action="store_true", help="print the result without writing the snapshot")
    args = parser.parse_args(argv)

    path = ASSETS / SNAPSHOT
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    source = snapshot["source"]
    models = sorted({*snapshot.get("short_names", {}), *args.model})
    from tools.rtd.system_workspace import lark_runner
    from tools.workspace_snapshot import complete_rows

    try:
        _, records = complete_rows(lark_runner(args.cli_bin, args.identity), source["base"], source["table"])
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR   read failed ({type(exc).__name__}: {exc}); snapshot unchanged")
        return 1
    names, ambiguous = short_names_from_rows(
        [fields for _, fields in records], models, model_field=source["model_field"],
        name_field=source["name_field"], exclude=source["exclude"])
    previous = snapshot.get("short_names", {})
    for model in models:
        old, new = previous.get(model, ""), names.get(model, "")
        if old != new:
            print(f"CHANGED {model}: {old or '-'} -> {new or '-'}")
    for model, counts in ambiguous.items():
        print(f"CHOSEN  {model}: " + ", ".join(f"{n} x{c}" for n, c in counts.most_common()))
    for model in models:
        if model not in names:
            print(f"MISSING {model}: no standard short name in the spec table")
    if args.dry_run:
        return 0
    snapshot["short_names"] = dict(sorted(names.items()))
    snapshot["source"]["refreshed"] = date.today().isoformat()
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.name}: {len(names)} models")
    return 0


if __name__ == "__main__":
    sys.exit(main())
