#!/usr/bin/env python3
"""Build-time Deliverables page: one row per model and region, a link per format; no network.

``/workspace/deliverables/`` lists what the pipeline has delivered, grouped by
model, one row per region and one column per format:

- 网页 (Web): every target in ``docs/publish/publish_manifest.json``, linked to
  its page on this site. It is read at build time, so it is always current.
- 印刷交付包 (the Publish handoff ZIP: the IDML plus its reference PDF) and
  Word 云文档 (the Draft Word output imported as a Feishu cloud doc): the
  latest version per model, region and language in the Feishu build table
  (文档构建表). RTD never reads Feishu, so ``export`` writes these links into the
  committed snapshot ``deliverables_snapshot.json``, refreshed through a PR like
  the corpus snapshot. The links open only for signed-in Feishu users; the
  operator chose to list them on this public page anyway (2026-09-25).

Missing inputs never break the build: without a publish manifest the web
column is empty, and an unreadable or unsound snapshot empties the Feishu
columns with a Sphinx warning. A snapshot older than ``STALE_AFTER_DAYS``
renders as 待复核.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.queue_contract import (  # noqa: E402
    DOCUMENT_KEY_FIELD,
    DOCUMENT_LINK_FIELD,
    FEISHU_CLOUD_DOC_FIELD,
    LANG_FIELD,
    VERSION_FIELD,
)
from tools.rtd_system_workspace import (  # noqa: E402
    CONTRACT_NAME,
    ContractError,
    lark_runner,
    load_contract,
    publication_facts,
)
from tools.utils.path_utils import PathSegments  # noqa: E402

DELIVERABLES_PAGE = "workspace/deliverables/index"
DELIVERABLES_TEMPLATE = "deliverables.html"
SNAPSHOT_NAME = "deliverables_snapshot.json"
DEFAULT_SNAPSHOT = Path(__file__).with_name("rtd_portal_assets") / SNAPSHOT_NAME
SNAPSHOT_SCHEMA = "hello-docs-deliverables/v1"
STALE_AFTER_DAYS = 45

# Build-table column per Feishu-held format. The Publish ZIP link lives in the
# column the queue calls DOCUMENT_LINK_FIELD ("idml_file").
FEISHU_FORMATS = {"print": DOCUMENT_LINK_FIELD, "word": FEISHU_CLOUD_DOC_FIELD}
FORMAT_LABELS = {"web": "网页", "print": "印刷交付包", "word": "Word 云文档"}
# The Document_key table's key text, "<model>_<region>" (e.g. "JE-1000F_US").
KEY_TEXT_FIELD = "Document_key"
FEISHU_HOSTS = ("feishu.cn", "larksuite.com")
WHOLE_BOOK = "整本"

_URL = re.compile(r"https://[^\s\]\)\"'<>]+")


# --- cell reading ---------------------------------------------------------------


def _text(value: object) -> str:
    """Every string inside a cell (hyperlink objects, lists), joined."""
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(_text(value.get(key)) for key in ("link", "url", "text", "name") if value.get(key))
    if isinstance(value, list):
        return " ".join(_text(part) for part in value)
    return str(value)


def _cell(value: object) -> str:
    """A text or select cell as plain text: ``["0.5"]`` -> ``"0.5"``, null -> ``""``."""
    if isinstance(value, list):
        value = value[0] if value else ""
    if isinstance(value, dict):
        value = value.get("text") or value.get("name") or ""
    return str(value).strip() if value is not None else ""


def feishu_url(value: object) -> str:
    """The first https Feishu/Lark link in a cell, else "".

    The build table stores links as ``[url](url)`` text or as hyperlink
    objects. Anything that is not an https link on a Feishu or Lark host is
    refused: these links are printed on a public page.
    """
    for match in _URL.finditer(_text(value)):
        url = match.group(0)
        host = (urlsplit(url).hostname or "").lower()
        if any(host == allowed or host.endswith("." + allowed) for allowed in FEISHU_HOSTS):
            return url
    return ""


def version_key(version: str) -> tuple[tuple[int, ...], str]:
    """Numeric order for versions like "0.5", "1.2", "2026-05-25.3"."""
    return tuple(int(part) for part in re.findall(r"\d+", version)), version


# --- export (the only Feishu read) --------------------------------------------------


def _field_name(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("field_name") or item.get("name") or "")
    return str(item)


def _records(run, base_token: str, table_id: str, required: tuple[str, ...]) -> list[tuple[str, dict[str, Any]]]:
    """Every ``(record_id, {field: value})`` of one table; ``+record-list`` caps a page at 200."""
    records: list[tuple[str, dict[str, Any]]] = []
    header: list[str] = []
    offset = 0
    while True:
        payload = run(["base", "+record-list", "--base-token", base_token, "--table-id", table_id,
                       "--format", "json", "--limit", "200", "--offset", str(offset)])
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise RuntimeError(f"record-list returned no data payload for {table_id}")
        names = [_field_name(item) for item in data.get("fields") or []]
        header = header or names
        page = data.get("data") or []
        ids = data.get("record_id_list") or []
        for index, row in enumerate(page):
            if isinstance(row, list):
                records.append((str(ids[index]) if index < len(ids) else "", dict(zip(names, row))))
        if len(page) < 200:
            break
        offset += 200
    missing = [name for name in required if name not in header]
    if missing:
        raise RuntimeError(f"table {table_id} is missing columns {missing}")
    return records


def export_snapshot(*, run, base_token: str, build_table: str, key_table: str, today: dt.date) -> dict[str, Any]:
    """The latest link per model, region, language and format; read-only.

    A build-table row names its document through the ``Document_Key`` link;
    the key table turns that into ``<model>_<region>``. Rows without a
    resolvable key or without a Feishu link are skipped. An empty ``Lang``
    means the whole book (all languages in one document).

    The key table's product names are not carried: some are wrong or empty
    there, and the page takes names from the manual center instead.
    """
    keys: dict[str, str] = {}
    for record_id, row in _records(run, base_token, key_table, (KEY_TEXT_FIELD,)):
        key = _cell(row.get(KEY_TEXT_FIELD))
        if record_id and key:
            keys[record_id] = key

    required = (DOCUMENT_KEY_FIELD, LANG_FIELD, VERSION_FIELD, *FEISHU_FORMATS.values())
    best: dict[tuple[str, str, str], tuple[tuple[tuple[int, ...], str], str, str]] = {}
    for _, row in _records(run, base_token, build_table, required):
        link = row.get(DOCUMENT_KEY_FIELD)
        record_id = link[0].get("id") if isinstance(link, list) and link and isinstance(link[0], dict) else ""
        if record_id not in keys:
            continue
        key = keys[record_id]
        lang, version = _cell(row.get(LANG_FIELD)), _cell(row.get(VERSION_FIELD))
        for fmt, field in FEISHU_FORMATS.items():
            url = feishu_url(row.get(field))
            if not url:
                continue
            slot = (key, lang, fmt)
            if slot not in best or version_key(version) > best[slot][0]:
                best[slot] = (version_key(version), version, url)

    documents: dict[tuple[str, str], dict[str, Any]] = {}
    for (key, lang, fmt), (_, version, url) in best.items():
        model, _, region = key.rpartition("_")
        document = documents.setdefault((key, lang), {
            "key": key, "model": model or key, "region": region if model else "", "lang": lang, "formats": {},
        })
        document["formats"][fmt] = {"version": version, "url": url}
    return {"schema": SNAPSHOT_SCHEMA, "exported_at": today.isoformat(),
            "documents": [documents[slot] for slot in sorted(documents)]}


# --- snapshot -----------------------------------------------------------------------


def snapshot_problems(data: object) -> list[str]:
    """Why a snapshot cannot be shown; empty when it is sound."""
    if not isinstance(data, dict):
        return ["the snapshot is not a JSON object"]
    problems = []
    if data.get("schema") != SNAPSHOT_SCHEMA:
        problems.append(f"schema is {data.get('schema')!r}, expected {SNAPSHOT_SCHEMA!r}")
    try:
        dt.date.fromisoformat(str(data.get("exported_at")))
    except ValueError:
        problems.append(f"exported_at {data.get('exported_at')!r} is not an ISO date")
    documents = data.get("documents")
    if not isinstance(documents, list):
        return [*problems, "documents is not a list"]
    seen: set[tuple[object, object]] = set()
    for index, document in enumerate(documents):
        where = f"documents[{index}]"
        if not isinstance(document, dict):
            problems.append(f"{where} is not an object")
            continue
        if not document.get("model") or not isinstance(document.get("lang", ""), str):
            problems.append(f"{where} needs a model and a text lang")
        slot = (document.get("key"), document.get("lang"))
        if slot in seen:
            problems.append(f"{where} repeats {slot}")
        seen.add(slot)
        formats = document.get("formats")
        if not isinstance(formats, dict) or not formats:
            problems.append(f"{where} has no formats")
            continue
        for fmt, entry in formats.items():
            if fmt not in FEISHU_FORMATS:
                problems.append(f"{where} has unknown format {fmt!r}")
            elif not isinstance(entry, dict) or not entry.get("url") or feishu_url(entry["url"]) != entry["url"]:
                problems.append(f"{where}.{fmt} is not an https Feishu link")
    return problems


def load_snapshot(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """The committed snapshot, or None with the reasons it cannot be shown."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, [f"cannot read {path.name}: {exc}"]
    problems = snapshot_problems(data)
    return (None if problems else data), problems


def region_labels(assets: Path) -> dict[str, str]:
    """Region labels from the system page's contract, the one place they are named."""
    try:
        regions = (load_contract(assets / CONTRACT_NAME).get("focus") or {}).get("regions") or {}
    except ContractError:
        return {}
    return {str(code): str(label) for code, label in regions.items()} if isinstance(regions, dict) else {}


# --- view ---------------------------------------------------------------------------


def region_code(region: str, labels: dict[str, str]) -> str:
    """The labelled region a key names; a locale-style key region such as ``pt-BR`` reads as ``BR``."""
    if region in labels:
        return region
    tail = region.rsplit("-", 1)[-1]
    return tail if tail in labels else region


def deliverables_view(targets: list[dict[str, Any]] | None, snapshot: dict[str, Any] | None, *,
                      names: dict[tuple[str, str], str], labels: dict[str, str],
                      language_order: Sequence[str], today: dt.date) -> dict[str, Any]:
    """Context for the page: models, each with one row per region and a cell per format.

    ``targets`` is None when the publish manifest cannot be read, ``snapshot``
    is None when the Feishu snapshot cannot be shown; either only empties its
    own columns. ``names`` maps ``(model, region)`` to the manual center's
    product name; a model the manual center does not list shows its code only.
    Chips follow ``language_order`` (the manual center's), whole books first.
    """
    cells: dict[tuple[str, str], dict[str, list[dict[str, str]]]] = {}

    def cell(model: str, region: str, fmt: str) -> list[dict[str, str]]:
        return cells.setdefault((model, region), {"web": [], "print": [], "word": []})[fmt]

    for target in targets or []:
        if not all(target.get(k) for k in ("model", "region", "route", "manual")):
            continue
        cell(target["model"], target["region"], "web").append({
            "lang": str(target.get("lang") or ""), "version": str(target.get("version") or ""),
            "docname": f"{target['route']}/{PurePosixPath(target['manual']).stem}",
            "date": str(target.get("built_at") or "")[:10],
        })
    for document in (snapshot or {}).get("documents") or []:
        for fmt, entry in document["formats"].items():
            cell(document["model"], document.get("region") or "", fmt).append({
                "lang": document.get("lang") or "", "version": entry.get("version") or "", "url": entry["url"],
            })

    region_order = list(labels)
    languages = list(language_order)

    def region_label(region: str) -> str:
        return labels.get(region_code(region, labels), region or "未标区域")

    def region_rank(region: str) -> tuple[int, str]:
        code = region_code(region, labels)
        return (region_order.index(code) if code in region_order else len(region_order)), region

    def language_rank(lang: str) -> tuple[int, str]:
        if not lang:
            return -1, ""
        return (languages.index(lang) if lang in languages else len(languages)), lang

    def chips(items: list[dict[str, str]], label: str) -> list[dict[str, str]]:
        shown = []
        for item in sorted(items, key=lambda i: language_rank(i["lang"])):
            lang = item["lang"].upper() or WHOLE_BOOK
            title = f"{label} · {lang} · 版本 {item['version'] or '未标注'}"
            if item.get("date"):
                title += f" · 发布于 {item['date']}"
            shown.append({**item, "label": lang, "title": title})
        return shown

    models: dict[str, dict[str, Any]] = {}
    for (model, region) in sorted(cells, key=lambda slot: (slot[0], region_rank(slot[1]))):
        label = region_label(region)
        entry = models.setdefault(model, {"model": model, "name": "", "rows": []})
        entry["name"] = entry["name"] or names.get((model, region), "")
        entry["rows"].append({
            "region": region, "region_label": label,
            **{fmt: chips(items, label) for fmt, items in cells[(model, region)].items()},
        })

    rows = [row for entry in models.values() for row in entry["rows"]]

    def coverage(fmt: str) -> dict[str, str]:
        count = sum(len(row[fmt]) for row in rows)
        covered = sum(1 for row in rows if row[fmt])
        return {"label": FORMAT_LABELS[fmt], "value": str(count), "sub": f"覆盖 {covered} 个型号 × 区域"}

    stale: list[str] = []
    exported = ""
    if snapshot is not None:
        exported_on = dt.date.fromisoformat(snapshot["exported_at"])
        exported = exported_on.isoformat()
        if (today - exported_on).days > STALE_AFTER_DAYS:
            stale = [f"飞书链接快照已超过 {STALE_AFTER_DAYS} 天（导出于 {exported}）"]
    built = sorted(item["date"] for row in rows for item in row["web"] if item["date"])
    return {
        "models": list(models.values()),
        "tiles": [{"label": "型号", "value": str(len(models)), "sub": f"{len(rows)} 个型号 × 区域"},
                  coverage("web"), coverage("print"), coverage("word")],
        "regions": [{"code": region, "label": region_label(region)}
                    for region in sorted({row["region"] for row in rows}, key=region_rank)],
        "snapshot_date": exported,
        "stale": stale,
        "web_missing": targets is None,
        "feishu_missing": snapshot is None,
        "last_published": built[-1] if built else "",
        "build_date": today.isoformat(),
    }


def _utc_today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).date()


def deliverables_page_context(app, assets: Path, names: dict[tuple[str, str], str],
                              language_order: Sequence[str]) -> dict[str, Any]:
    """Context for DELIVERABLES_PAGE; the page always renders, missing inputs show as 无数据."""
    from sphinx.util import logging as sphinx_logging

    logger = sphinx_logging.getLogger(__name__)
    today = _utc_today()
    configured = str(app.config.rtd_system_workspace_date or "")
    if configured:
        try:
            today = dt.date.fromisoformat(configured)
        except ValueError:
            logger.warning("rtd_system_workspace_date %r is not an ISO date; using %s", configured, today)
    facts = publication_facts(Path(app.srcdir).parent / PathSegments.PUBLISH_MANIFEST_JSON)
    snapshot, problems = load_snapshot(assets / SNAPSHOT_NAME)
    if problems:
        logger.warning("Deliverables page shows no Feishu links: %s", "; ".join(problems[:3]))
    return deliverables_view(facts["targets"] if facts else None, snapshot, names=names,
                             labels=region_labels(assets), language_order=language_order, today=today)


# --- CLI ----------------------------------------------------------------------------


def _iso_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an ISO date: {value!r}") from None


def _summary(snapshot: dict[str, Any]) -> str:
    documents = snapshot["documents"]
    counts = {fmt: sum(1 for d in documents if fmt in d["formats"]) for fmt in FEISHU_FORMATS}
    return (f"{len(documents)} documents across {len({d['model'] for d in documents})} models; "
            + ", ".join(f"{FORMAT_LABELS[fmt]} {count}" for fmt, count in counts.items()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export or check the Deliverables page's Feishu link snapshot.")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="validate the committed snapshot and report its coverage")
    check.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    check.add_argument("--today", type=_iso_date, default=None, help="ISO date used for staleness (default: today, UTC)")
    export = commands.add_parser("export", help="write the snapshot from the Feishu build table (read-only)")
    export.add_argument("--output", type=Path, default=DEFAULT_SNAPSHOT)
    export.add_argument("--base-token", default=os.environ.get("FEISHU_PHASE2_BASE_TOKEN", ""),
                        help="文档构建 base token (default: $FEISHU_PHASE2_BASE_TOKEN)")
    export.add_argument("--build-table", default=os.environ.get("FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID", ""),
                        help="文档构建表 (default: $FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID)")
    export.add_argument("--key-table", default=os.environ.get("FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID", ""),
                        help="the Document_key table (default: $FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID, the same table)")
    export.add_argument("--cli-bin", default="lark-cli", help='lark-cli command, e.g. "lark-cli --profile prod"')
    export.add_argument("--as", dest="identity", default=os.environ.get("FEISHU_PHASE2_IDENTITY", ""),
                        help="lark-cli identity (default: $FEISHU_PHASE2_IDENTITY)")
    export.add_argument("--today", type=_iso_date, default=None, help="export date to record (default: today, UTC)")
    args = parser.parse_args(argv)

    if args.command == "export":
        missing = [flag for flag, value in (("--base-token", args.base_token), ("--build-table", args.build_table),
                                            ("--key-table", args.key_table)) if not value]
        if missing:
            print(f"ERROR   need {', '.join(missing)} (or the matching FEISHU_PHASE2_* variables)")
            return 1
        try:
            snapshot = export_snapshot(run=lark_runner(args.cli_bin, args.identity), base_token=args.base_token,
                                       build_table=args.build_table, key_table=args.key_table,
                                       today=args.today or _utc_today())
        except RuntimeError as exc:
            print(f"ERROR   {exc}")
            return 1
        problems = snapshot_problems(snapshot)
        if problems:
            print("ERROR   " + "; ".join(problems[:5]))
            return 1
        args.output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.output}: {_summary(snapshot)}; exported {snapshot['exported_at']}")
        return 0

    snapshot, problems = load_snapshot(args.snapshot)
    for problem in problems:
        print(f"ERROR   {args.snapshot.name}: {problem}")
    if snapshot is None:
        return 1
    today = args.today or _utc_today()
    age = (today - dt.date.fromisoformat(snapshot["exported_at"])).days
    if age > STALE_AFTER_DAYS:
        print(f"WARNING {args.snapshot.name}: exported {snapshot['exported_at']}, {age} days ago "
              f"(over {STALE_AFTER_DAYS}); the page marks it 待复核 — rerun export")
    print(f"deliverables snapshot: exported {snapshot['exported_at']}; {_summary(snapshot)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
