"""审核稿 rows for 网页说明书进度: the manuals still in review, beside what is online.

``read_reviews`` reads the 审核稿（工作台输出） table of the 发布文档管理 Base
(read-only) for the ``web_progress`` export: one row per draft line, with its
version, date, status, the number of questions open with R&D, and the links to
the draft and its review page on the private review site. The operator chose on
2026-10-23 to show these rows on the 交付物 tab, unpublished models included, so
they are committed with the snapshot to the public Hello-Docs. The drafts
themselves stay in the private review repository.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

from tools.workspace_snapshot import complete_rows

ASSETS = Path(__file__).resolve().parents[1] / "rtd_portal_assets"

# 审核稿 table columns.
FIELDS = {"model": "型号", "name": "商品名称", "market": "市场", "language": "语言", "version": "当前版本",
          "date": "更新日期", "status": "状态", "open": "待研发确认", "draft": "审核稿", "page": "审核页"}

_TABLES = json.loads((ASSETS / "web_progress.json").read_text(encoding="utf-8"))
MARKETS: tuple[str, ...] = tuple(_TABLES["markets"])
MARKET_NAMES: dict[str, str] = dict(_TABLES["market_names"])
# Feishu stores a date as the epoch milliseconds of midnight in the tenant's time zone.
TENANT_TZ = dt.timezone(dt.timedelta(hours=8))

_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_URL = re.compile(r"https://[^\s\]\)\"'<>]+")
_RECORD = re.compile(r"rec[A-Za-z0-9]+")
_KEYS = {"record", "model", "name", "market", "market_label", "language", "version", "date", "status", "open",
         "draft", "page"}


def _segments(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        return [text for key in ("text", "link", "name") for text in _segments(value.get(key))][:1]
    if isinstance(value, list):
        return [text for item in value for text in _segments(item)]
    return [str(value)]


def text_of(value: object) -> str:
    """A text cell as one string, whether plain or rich-text segments."""
    return "".join(_segments(value)).strip()


def link_of(value: object) -> str:
    """The first https address in a hyperlink cell, else ""."""
    parts = [value.get("link"), value.get("text")] if isinstance(value, dict) else _segments(value)
    for part in parts:
        match = _URL.search(str(part or ""))
        if match:
            return match.group(0)
    return ""


def day_of(value: object) -> str:
    """An ISO date from a date cell: epoch milliseconds or a date string."""
    if isinstance(value, list):
        value = value[0] if value else None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return dt.datetime.fromtimestamp(value / 1000, TENANT_TZ).date().isoformat()
    text = str(value or "").strip()
    if text.isdigit():
        return day_of(int(text))
    try:
        return dt.date.fromisoformat(text[:10].replace("/", "-")).isoformat()
    except ValueError:
        return ""


def count_of(value: object) -> int:
    try:
        return max(0, int(float(text_of(value) or 0)))
    except ValueError:
        return 0


def read_reviews(run, base_token: str, table_id: str) -> list[dict[str, Any]]:
    """Every 审核稿 row with a model, sorted by model, market and language; read-only."""
    header, records = complete_rows(run, base_token, table_id)
    missing = [name for name in FIELDS.values() if name not in header]
    if missing:
        raise RuntimeError(f"table {table_id} is missing columns {missing}")
    reviews = []
    for record, row in records:
        model = text_of(row.get(FIELDS["model"]))
        if not model:
            continue
        if not _MODEL.fullmatch(model):
            raise RuntimeError("a 审核稿 row has a 型号 that is not a model code")
        label = text_of(row.get(FIELDS["market"]))
        reviews.append({
            "record": record, "model": model, "name": text_of(row.get(FIELDS["name"])),
            "market": MARKET_NAMES.get(label, ""), "market_label": label,
            "language": text_of(row.get(FIELDS["language"])), "version": text_of(row.get(FIELDS["version"])),
            "date": day_of(row.get(FIELDS["date"])), "status": text_of(row.get(FIELDS["status"])),
            "open": count_of(row.get(FIELDS["open"])),
            "draft": link_of(row.get(FIELDS["draft"])), "page": link_of(row.get(FIELDS["page"])),
        })
    return sorted(reviews, key=lambda r: (r["model"], _rank(r["market"]), r["language"], r["record"]))


def _rank(market: str) -> int:
    return MARKETS.index(market) if market in MARKETS else len(MARKETS)


def _review_problems(row: object, where: str) -> list[str]:
    if not isinstance(row, dict) or set(row) != _KEYS:
        return [f"{where} needs exactly {sorted(_KEYS)}"]
    problems = []
    if not _MODEL.fullmatch(str(row["model"])) or not _RECORD.fullmatch(str(row["record"])):
        problems.append(f"{where} needs a model code and a record id")
    if row["market"] not in (*MARKETS, ""):
        problems.append(f"{where} has an unknown market {row['market']!r}")
    if row["date"]:
        try:
            dt.date.fromisoformat(str(row["date"]))
        except ValueError:
            problems.append(f"{where} has no ISO date")
    if type(row["open"]) is not int or row["open"] < 0:
        problems.append(f"{where} needs a whole 待研发确认 count")
    if any(row[key] and not str(row[key]).startswith("https://") for key in ("draft", "page")):
        problems.append(f"{where} links must be https addresses")
    texts = ("name", "market_label", "language", "version", "status")
    if not all(isinstance(row[key], str) for key in texts):
        problems.append(f"{where} text fields must be strings")
    return problems


def reviews_problems(reviews: object) -> list[str]:
    if not isinstance(reviews, list):
        return ["reviews is not a list"]
    return [problem for index, row in enumerate(reviews) for problem in _review_problems(row, f"reviews[{index}]")]


def feishu_problems(feishu: object, *, reviews: bool) -> list[str]:
    """``feishu`` holds the two tables' addresses (reviews "" without 审核稿 rows); a record link appends ``&record=<id>``."""
    def sound(url: object) -> bool:
        return isinstance(url, str) and url.startswith("https://") and "?table=" in url

    if not isinstance(feishu, dict) or set(feishu) != {"web", "reviews"} or not sound(feishu["web"]) \
            or not (sound(feishu["reviews"]) if reviews else feishu["reviews"] == ""):
        return ["feishu must give the web and reviews table addresses"]
    return []


def table_url(base_url: str, table_id: str) -> str:
    return f"{base_url.split('?', 1)[0]}?table={table_id}"


def record_url(table: str, record: str) -> str:
    return f"{table}&record={record}" if table and record else ""


def review_view(reviews: list[dict[str, Any]], table: str, labels: dict[str, str]) -> list[dict[str, Any]]:
    """The 审核中 rows, newest first, each with its market label and Feishu record link."""
    rows = [{**row, "market_text": labels.get(row["market"], row["market_label"] or row["market"]),
             "feishu": record_url(table, row["record"])} for row in sorted(reviews, key=lambda r: r["model"])]
    return sorted(rows, key=lambda r: r["date"] or "", reverse=True)
