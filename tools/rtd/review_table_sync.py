"""Sync each working review draft's derived state to its row in 审核稿（工作台输出）.

The private review site (``tools.rtd.review_site``) is the source of a draft
line's state; the Feishu 审核稿（工作台输出） table of the 发布文档管理 Base
mirrors it for the public 交付物 tab (``tools.rtd.web_reviews`` reads it into
the daily ``web_progress`` snapshot, which is committed to the public
Hello-Docs). This tool keeps the two from drifting::

    python -m tools.rtd.review_table_sync <drafts_dir> [--line MODEL/REGION ...] [--write]

A line matches the one row whose 审核页 link ends in ``/<MODEL>/<REGION>.html``
and whose 型号 is the model; rows are created by hand. Only the owned fields
(``OWNED``) are ever written: 型号, 商品名称, 市场 and 语言 are identity fields
set when the row is created, and every other column belongs to someone else.
Because the row is public, a line whose draft.json ``nameplate_model`` or
``sales_model`` appears in any public cell, current or planned, is refused and
nothing is written for it. Dry-run by default; ``--write`` writes the changed
fields only, reads the record back and compares every owned field.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from tools.rtd import review_site
from tools.rtd.web_reviews import FIELDS, count_of, day_of, link_of, text_of
from tools.workspace_snapshot import complete_rows

DEFAULT_TABLE = "审核稿（工作台输出）"
BASE_ENV = "FEISHU_PUBLISHED_DOCS_BASE_TOKEN"
TABLE_ENV = "FEISHU_PUBLISHED_DOCS_REVIEW_TABLE_ID"
WORKBENCH = review_site.ASSETS / "manual_workbench.html"
# Fields this tool owns, in write order; FIELDS keys from web_reviews.
OWNED = ("version", "date", "status", "open", "draft", "page")
# Public text cells checked for unreleased model codes (links are checked separately).
PUBLIC = ("model", "name", "market", "language", "version", "status")
CODE_KEYS = ("nameplate_model", "sales_model")
_MARKDOWN_LINK = re.compile(r"^\[(.*)\]\((https://[^)\s]+)\)$", re.S)
_REVIEW_SITE = re.compile(r"\{% set review_site = '([^']*)' %\}")


def review_site_url(workbench: Path = WORKBENCH) -> str:
    """The private review site's URL, set once in the workbench template."""
    found = _REVIEW_SITE.findall(workbench.read_text(encoding="utf-8"))
    if len(found) != 1 or not found[0].startswith("https://"):
        raise RuntimeError(f"{workbench}: expected one https review_site setting")
    return found[0].rstrip("/")


def link_cell(value: object) -> tuple[str, str]:
    """A hyperlink cell as (text, link): a {link, text} object or the markdown string lark-cli reads."""
    if isinstance(value, list):
        value = value[0] if value else None
    if isinstance(value, dict):
        return text_of(value.get("text")), link_of(value)
    match = _MARKDOWN_LINK.match(text_of(value))
    return (match.group(1), match.group(2)) if match else (text_of(value), link_of(value))


def markdown_link(text: str, url: str) -> str:
    return f"[{text}]({url})"


def current_values(row: dict) -> dict[str, Any]:
    """The owned fields of a row, normalised to the planned values' shapes."""
    open_cell = text_of(row.get(FIELDS["open"]))
    return {
        "version": text_of(row.get(FIELDS["version"])),
        "date": day_of(row.get(FIELDS["date"])),
        "status": text_of(row.get(FIELDS["status"])),
        "open": count_of(row.get(FIELDS["open"])) if open_cell else None,
        "draft": link_cell(row.get(FIELDS["draft"])),
        "page": link_cell(row.get(FIELDS["page"])),
    }


def planned_values(line: dict, site: str) -> dict[str, Any]:
    draft, model, region = line["current"], line["model"], line["region"]
    return {
        "version": draft["version"],
        "date": draft["date"],
        "status": draft["status"],
        "open": len(draft["rd_open"]),
        "draft": (f"{model} {region} {draft['version']} 审核稿", f"{site}/{draft['url']}"),
        "page": (f"{model} {region} 审核页", f"{site}/{line['page']}"),
    }


def cell_value(key: str, value: Any) -> Any:
    """A planned value as lark-cli writes it."""
    if key == "date":
        return f"{value} 00:00:00"
    if key in ("draft", "page"):
        return markdown_link(*value)
    return value


def shown(key: str, value: Any) -> str:
    if value is None or value == "":
        return "(empty)"
    return markdown_link(*value) if key in ("draft", "page") else str(value)


def model_codes(manifest: dict, model: str) -> list[str]:
    """Unreleased model codes from draft.json; a code inside the public model code itself is not secret."""
    codes = [manifest.get(key) for key in CODE_KEYS]
    return [code for code in codes if isinstance(code, str) and code.strip()
            and code.strip().lower() not in model.lower()]


def leaks(codes: list[str], row: dict, current: dict, planned: dict) -> list[str]:
    texts = {FIELDS[key]: text_of(row.get(FIELDS[key])) for key in PUBLIC}
    for key in ("draft", "page"):
        texts[f"{FIELDS[key]} (current)"] = " ".join(current[key])
        texts[f"{FIELDS[key]} (planned)"] = " ".join(planned[key])
    for key in ("version", "status"):
        texts[f"{FIELDS[key]} (planned)"] = str(planned[key])
    return [f"{name} contains a model code from draft.json {CODE_KEYS}" for name, text in texts.items()
            if any(code.strip().lower() in text.lower() for code in codes)]


def match_row(line: dict, records: list[tuple[str, dict]]) -> tuple[str, dict]:
    suffix = f"/{line['model']}/{line['region']}.html"
    hits = [(record, row) for record, row in records
            if urlsplit(link_of(row.get(FIELDS["page"]))).path.endswith(suffix)]
    name = f"{line['model']}/{line['region']}"
    if not hits:
        raise LookupError(f"{name}: no {DEFAULT_TABLE} row whose {FIELDS['page']} link ends in {suffix}; "
                          "create the row by hand (型号, 商品名称, 市场, 语言 and the 审核页 link), then rerun")
    if len(hits) > 1:
        raise LookupError(f"{name}: {len(hits)} rows link {suffix} ({', '.join(r for r, _ in hits)}); keep one")
    record, row = hits[0]
    if text_of(row.get(FIELDS["model"])) != line["model"]:
        raise LookupError(f"{name}: row {record} has 型号 {text_of(row.get(FIELDS['model']))!r}, "
                          f"not {line['model']!r}")
    return record, row


def read_record(run, base_token: str, table_id: str, record: str) -> dict:
    payload = run(["base", "+record-get", "--base-token", base_token, "--table-id", table_id,
                   "--record-id", record, "--format", "json"])
    data = payload.get("data") if isinstance(payload, dict) and payload.get("code", 0) in (0, "0") else None
    rows = data.get("data") if isinstance(data, dict) else None
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(data.get("fields"), list):
        raise RuntimeError(f"record {record}: read-back returned no record")
    names = [str(f.get("field_name") or f.get("name") or "") if isinstance(f, dict) else str(f)
             for f in data["fields"]]
    return dict(zip(names, rows[0], strict=False))


def sync_line(line: dict, manifest: dict, records: list[tuple[str, dict]], *, run, base_token: str,
              table_id: str, site: str, write: bool, sleep: Callable[[float], None], out) -> bool:
    """Plan (and with ``write`` apply and verify) one line; True when it ended clean."""
    name = f"{line['model']}/{line['region']}"
    try:
        record, row = match_row(line, records)
    except LookupError as error:
        print(f"ERROR {error}", file=out)
        return False
    current, planned = current_values(row), planned_values(line, site)
    found = leaks(model_codes(manifest, line["model"]), row, current, planned)
    if found:
        for problem in found:
            print(f"ERROR {name} {record}: {problem}; nothing written", file=out)
        return False
    changed = [key for key in OWNED if current[key] != planned[key]]
    if not changed:
        print(f"{name} {record}: up to date", file=out)
        return True
    print(f"{name} {record}: {len(changed)} change(s){'' if write else ' (dry run)'}", file=out)
    for key in changed:
        print(f"  {FIELDS[key]}: {shown(key, current[key])} → {shown(key, planned[key])}", file=out)
    if not write:
        return True
    fields = {FIELDS[key]: cell_value(key, planned[key]) for key in changed}
    run(["base", "+record-upsert", "--base-token", base_token, "--table-id", table_id, "--record-id", record,
         "--json", json.dumps(fields, ensure_ascii=False)])
    sleep(2)
    after = current_values(read_record(run, base_token, table_id, record))
    clean = True
    for key in OWNED:
        print(f"{record} {FIELDS[key]}={shown(key, after[key])}", file=out)
        if after[key] != planned[key]:
            print(f"ERROR {name} {record}: {FIELDS[key]} read back {shown(key, after[key])}, "
                  f"expected {shown(key, planned[key])}", file=out)
            clean = False
    return clean


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m tools.rtd.review_table_sync", description=__doc__.split("\n")[0])
    parser.add_argument("drafts_dir", type=Path)
    parser.add_argument("--line", action="append", default=[], metavar="MODEL/REGION")
    parser.add_argument("--write", action="store_true", help="write the changed fields and read them back")
    parser.add_argument("--base-token", default=os.environ.get(BASE_ENV, ""))
    parser.add_argument("--table-id", default=os.environ.get(TABLE_ENV) or DEFAULT_TABLE)
    parser.add_argument("--cli-bin", default="lark-cli")
    parser.add_argument("--as", dest="identity", default="bot")
    parser.add_argument("--site-url", default="")
    return parser.parse_args(argv)


def main(argv: list[str], *, run=None, sleep: Callable[[float], None] = time.sleep, out=sys.stdout) -> int:
    args = parse_args(argv)
    if not args.base_token:
        print(f"ERROR no Base token: pass --base-token or set {BASE_ENV}", file=out)
        return 1
    try:
        lines, warnings = review_site.load_drafts(args.drafts_dir)
    except (ValueError, OSError) as error:
        print(f"ERROR {error}", file=out)
        return 1
    for warning in warnings:
        print(f"WARNING {warning}", file=out)
    wanted = set(args.line)
    unknown = wanted - {f"{line['model']}/{line['region']}" for line in lines}
    if unknown:
        print(f"ERROR no working draft for {sorted(unknown)}", file=out)
        return 1
    lines = [line for line in lines if not wanted or f"{line['model']}/{line['region']}" in wanted]
    site = (args.site_url or review_site_url()).rstrip("/")
    if run is None:
        from tools.rtd.system_workspace import lark_runner
        run = lark_runner(args.cli_bin, args.identity)
    try:
        header, records = complete_rows(run, args.base_token, args.table_id)
    except RuntimeError as error:
        print(f"ERROR reading {args.table_id}: {error}", file=out)
        return 1
    missing = [FIELDS[key] for key in (*PUBLIC, *OWNED) if FIELDS[key] not in header]
    if missing:
        print(f"ERROR table {args.table_id} is missing columns {missing}", file=out)
        return 1
    clean = True
    for line in lines:
        manifest = json.loads((args.drafts_dir / line["model"] / line["region"] / review_site.MANIFEST)
                              .read_text(encoding="utf-8"))
        clean &= sync_line(line, manifest, records, run=run, base_token=args.base_token, table_id=args.table_id,
                           site=site, write=args.write, sleep=sleep, out=out)
    return 0 if clean else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
