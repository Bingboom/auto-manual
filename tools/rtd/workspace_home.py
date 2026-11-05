"""知识库首页's data: the reusable assets every manual adds to, the main lines and what is being done now.

The home page opens with 「已积累的可复用资产」: four cards, each the amount built up so far and how much of it can be
reused now. Every figure is read from the source that owns it; an unreadable source shows its card as 无数据 and
never fails the build:

- 翻译语料: the translation-memory snapshot as 系统建设 shows it (句对, 术语, languages, approved share).
- 图片素材: ``data/asset_registry.csv``: finished assets (状态 成品), the share without language-specific text
  (语言维度 中立) and those every model uses (适用机型 ALL).
- 通用章节: the shared chapter templates under ``docs/templates/page_shared``, counted per language.
- 产品知识: the topics in ``product_knowledge.json``, with a growth line from each topic's ``added`` date.

Below them, 当前主线 lists the 系统建设 focus lanes marked ``now`` (titles only) and 正在做 comes from
``workspace_home.yaml``: plain-language copy that only this page shows.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

import yaml

from tools.utils.path_utils import Paths

HOME_COPY = "workspace_home.yaml"
SCHEMA = "hello-docs-workspace-home/v1"
ASSET_REGISTRY_CSV = "asset_registry.csv"
SHARED_PAGES = "page_shared"
# Shared chapters named on the 通用章节 card, in this order, when the templates have them.
CHAPTER_NAMES = (("11_warranty", "保修"), ("10_troubleshooting", "故障排除"), ("08_charging_methods", "充电方式"),
                 ("09_storage_and_maintenance", "存储与维护"))
# The growth line's box (an inline SVG viewBox): x runs over the dated span, y over the topic count.
SPARK_WIDTH, SPARK_HEIGHT, SPARK_PAD = 120, 32, 4


def load_home_copy(assets: Path) -> dict[str, Any]:
    """The note beside the asset cards and the 正在做 items; a malformed file raises ValueError."""
    data = yaml.safe_load((assets / HOME_COPY).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError(f"{HOME_COPY}: schema must be {SCHEMA}")
    note = str(data.get("assets_note") or "").strip()
    doing = data.get("doing")
    if not note or not isinstance(doing, list) or not doing:
        raise ValueError(f"{HOME_COPY}: needs assets_note and at least one doing item")
    items = []
    for item in doing:
        lead, text = (str(item.get(key) or "").strip() for key in ("lead", "text")) if isinstance(item, dict) else ("", "")
        if not lead or not text:
            raise ValueError(f"{HOME_COPY}: each doing item needs lead and text")
        items.append({"lead": lead, "text": text})
    return {"assets_note": note, "doing": items}


def _lanes(system: dict[str, Any] | None) -> list[dict[str, str]]:
    focus = (system or {}).get("focus") or {}
    for group in focus.get("groups") or []:
        if group.get("horizon") == "now":
            return [{"id": lane["id"], "title": lane["title"]} for lane in group.get("lanes") or []]
    return []


def now_view(system: dict[str, Any] | None, copy: dict[str, Any]) -> dict[str, Any]:
    """当前主线 (from 系统建设), 正在做 and the asset note (from the home copy)."""
    return {"lanes": _lanes(system), "doing": copy["doing"], "assets_note": copy["assets_note"],
            "system": system is not None}


def _card(card_id: str, title: str, icon: str, docname: str | None = None, anchor: str = "") -> dict[str, Any]:
    """A card with no figures yet; the template shows it as 无数据 until `stock` is filled."""
    return {"id": card_id, "title": title, "icon": icon, "docname": docname, "anchor": anchor,
            "stock": [], "bar": None, "chips": [], "spark": None, "caption": ""}


def _corpus_card(system: dict[str, Any] | None) -> dict[str, Any]:
    corpus = (system or {}).get("corpus") or {}
    card = _card("corpus", "翻译语料", "languages", "workspace/system/index" if system else None, "language-assets")
    tiles = {tile.get("key"): str(tile.get("value") or "") for tile in corpus.get("tiles") or []}
    if not tiles.get("pairs"):
        return card
    card["stock"] = [{"value": tiles["pairs"], "unit": "句对"}, {"value": tiles.get("terms") or "—", "unit": "术语"}]
    approved = tiles.get("approved", "")
    if approved.endswith("%") and approved[:-1].isdigit():
        card["bar"] = {"percent": int(approved[:-1]), "label": "句对已批准，可直接复用"}
    card["caption"] = f"{tiles.get('languages') or '—'} 种语言 · 快照 {corpus.get('exported_at') or '—'}"
    return card


def read_image_assets(registry: Path) -> dict[str, int] | None:
    """Finished assets, those without language-specific text and those every model uses; None when unreadable."""
    try:
        with registry.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, csv.Error, UnicodeDecodeError):
        return None
    finished = [row for row in rows if str(row.get("状态") or "").strip().endswith("成品")]
    if not finished:
        return None
    return {"finished": len(finished),
            "neutral": sum(1 for row in finished if str(row.get("语言维度") or "").strip() == "中立"),
            "every_model": sum(1 for row in finished if str(row.get("适用机型") or "").strip().upper() == "ALL")}


def _image_card(counts: dict[str, int] | None) -> dict[str, Any]:
    # The workbench 数据统计 tab lists the registry (素材登记).
    card = _card("images", "图片素材", "image", "workspace/deliverables/index", "statistics")
    if counts:
        card["stock"] = [{"value": f"{counts['finished']:,}", "unit": "张"}]
        card["bar"] = {"percent": round(100 * counts["neutral"] / counts["finished"]), "label": "不分语言，各语言版通用"}
        card["caption"] = f"{counts['every_model']:,} 张全型号共用"
    return card


def read_shared_chapters(templates: Path) -> dict[str, Any] | None:
    """Shared chapter pages and languages under page_shared, and the named chapters it has; None when absent."""
    root = templates / SHARED_PAGES
    try:
        found = {lang.name: {page.stem for page in lang.glob("*.rst")} for lang in root.iterdir() if lang.is_dir()}
    except OSError:
        return None
    found = {lang: stems for lang, stems in found.items() if stems}
    if not found:
        return None
    stems = set().union(*found.values())
    return {"pages": sum(len(stems_) for stems_ in found.values()), "languages": len(found),
            "names": [name for stem, name in CHAPTER_NAMES if stem in stems]}


def _chapter_card(chapters: dict[str, Any] | None) -> dict[str, Any]:
    card = _card("chapters", "通用章节", "chapters")
    if chapters:
        card["stock"] = [{"value": f"{chapters['pages']:,}", "unit": "篇"},
                         {"value": str(chapters["languages"]), "unit": "种语言"}]
        card["chips"] = chapters["names"]
        card["caption"] = "各型号共用，差异按区域、语言覆盖"
    return card


def _spark(points: list[tuple[dt.date, int]]) -> dict[str, Any]:
    """Polyline, area and end point of a cumulative count, scaled into the spark box."""
    (first_day, first_count), (last_day, last_count) = points[0], points[-1]
    span_x, span_y = max((last_day - first_day).days, 1), max(last_count - first_count, 1)
    top, bottom, width = SPARK_PAD + 2, SPARK_HEIGHT - SPARK_PAD - 2, SPARK_WIDTH - 2 * SPARK_PAD
    xy = [(SPARK_PAD + width * (day - first_day).days / span_x, bottom - (bottom - top) * (count - first_count) / span_y)
          for day, count in points]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
    base = SPARK_HEIGHT - 2
    return {"line": line, "area": f"{line} {xy[-1][0]:.1f},{base} {xy[0][0]:.1f},{base}",
            "x": f"{xy[-1][0]:.1f}", "y": f"{xy[-1][1]:.1f}", "width": SPARK_WIDTH, "height": SPARK_HEIGHT}


def knowledge_growth(assets: Path) -> dict[str, Any] | None:
    """Topic count, and a growth line when every topic carries its ``added`` date; None when unreadable."""
    try:
        topics = json.loads((assets / "product_knowledge.json").read_text(encoding="utf-8"))["topics"]
        added = [str(topic.get("added") or "") for topic in topics]
        days = sorted({dt.date.fromisoformat(day) for day in added}) if all(added) else []
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None
    growth: dict[str, Any] = {"total": len(topics), "spark": None, "since": "", "delta": 0}
    if len(days) >= 2:
        points, running = [], 0
        for day in days:
            running += added.count(day.isoformat())
            points.append((day, running))
        growth.update(spark=_spark(points), since=f"{days[0].month} 月 {days[0].day} 日",
                      delta=len(topics) - points[0][1])
    return growth if topics else None


def _knowledge_card(growth: dict[str, Any] | None) -> dict[str, Any]:
    card = _card("knowledge", "产品知识", "product", "products/knowledge")
    if growth:
        card["stock"] = [{"value": str(growth["total"]), "unit": "个主题"}]
        if growth["spark"]:
            card["spark"] = {**growth["spark"], "label": f"{growth['since']}以来", "value": f"+{growth['delta']}"}
        card["caption"] = "参数、电池、逆变、充电与备电"
    return card


def reusable_assets(system: dict[str, Any] | None, assets: Path, root: Path) -> list[dict[str, Any]]:
    """The four 「已积累的可复用资产」 cards, in display order."""
    paths = Paths(root)
    return [_corpus_card(system), _image_card(read_image_assets(paths.data_dir / ASSET_REGISTRY_CSV)),
            _chapter_card(read_shared_chapters(paths.templates_dir)), _knowledge_card(knowledge_growth(assets))]
