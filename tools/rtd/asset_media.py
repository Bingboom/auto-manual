"""视觉媒体's inventories: the asset registry and the shared symbols, read at build time from the repository.

- ``data/asset_registry.csv``: one row per registered asset. The page counts finished rows (状态 ends with 成品), rows
  without language-specific text (语言维度 中立) and rows every model uses (适用机型 ALL), and lists every row with
  its scope (category, models, regions, language) and the start of its content hash. The registry has no version
  column, so the page says so; 备注 holds source notes and stays off the page.
- the shared symbol manifest (``design_assets.REGISTRIES["symbols"]``): each symbol's key, status, SHA-256 and the
  source it was taken from. A symbol's use is counted from the published sources, without stored data: the publish
  step pools every manual asset under ``_static/manual-assets/_pool/<2>/<sha256>.<ext>``, so a manual page that shows
  a symbol names its hash. Only published single-language and legacy pages the portal catalog lists are read.

An unreadable source makes its part ``None``; the page then says 无数据 and the build goes on.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from tools.rtd.design_assets import REGISTRIES

ASSET_REGISTRY_CSV = "asset_registry.csv"
NEUTRAL = "中立"
EVERY_MODEL = "ALL"
# A pooled manual asset as a published page names it: _pool/<first two hex>/<sha256>.<ext>.
_POOLED = re.compile(r"_pool/[0-9a-f]{2}/([0-9a-f]{64})\.[A-Za-z0-9]+")
_HASH = re.compile(r"([0-9a-f]{64})")


def _split(value: object) -> list[str]:
    return [part.strip() for part in re.split(r"[|;,，、]", str(value or "")) if part.strip()]


def _short_hash(value: str) -> str:
    match = _HASH.search(value or "")
    return match.group(1)[:12] if match else ""


def _text(row: dict[str, Any], field: str, default: str = "") -> str:
    return str(row.get(field) or "").strip() or default


def _registry_item(row: dict[str, Any]) -> dict[str, Any]:
    status = _text(row, "状态")
    return {"key": _text(row, "asset_key"), "category": _text(row, "类别", "未注明"),
            "dimension": _text(row, "语言维度", "未注明"), "status": re.sub(r"^\W+", "", status) or "未注明",
            "finished": status.endswith("成品"), "models": _split(row.get("适用机型")),
            "regions": _split(row.get("适用区域")), "languages": _split(row.get("语言变体")),
            "hash": _short_hash(_text(row, "内容哈希"))}


def _filters(items: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {"category": sorted({item["category"] for item in items}),
            "model": sorted({m for item in items for m in item["models"]}),
            "region": sorted({r for item in items for r in item["regions"]}),
            "language": sorted({lang for item in items for lang in item["languages"]})}


def registry_view(path: Path) -> dict[str, Any] | None:
    """Counts, filter values and one row per registered asset; None when the registry is unreadable or empty."""
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            items = [_registry_item(row) for row in csv.DictReader(handle)]
    except (OSError, csv.Error, UnicodeDecodeError):
        return None
    if not items:
        return None
    return {
        "total": len(items), "finished": sum(item["finished"] for item in items),
        "neutral": sum(item["dimension"] == NEUTRAL for item in items),
        "every_model": sum(EVERY_MODEL in (m.upper() for m in item["models"]) for item in items),
        "hashed": sum(bool(item["hash"]) for item in items),
        "categories": Counter(item["category"] for item in items).most_common(),
        "filters": _filters(items),
        "items": sorted(items, key=lambda item: (not item["finished"], item["category"], item["key"])),
    }


def published_pages(srcdir: Path, publications: list[dict[str, Any]]) -> list[tuple[dict[str, Any], Path]]:
    """Each catalog publication with its Markdown source; a publication without one is left out."""
    pages = []
    for publication in publications:
        source = (srcdir / str(publication.get("url") or "")).with_suffix(".md")
        if source.is_file():
            pages.append((publication, source))
    return pages


def symbol_usage(pages: list[tuple[dict[str, Any], Path]], hashes: set[str]) -> dict[str, dict[str, int]] | None:
    """For each symbol hash, the published language versions and editions (model × market) that show it."""
    routes: dict[str, set[tuple[str, str, str]]] = {sha: set() for sha in hashes}
    try:
        for publication, source in pages:
            found = set(_POOLED.findall(source.read_text(encoding="utf-8"))) & hashes
            for sha in found:
                routes[sha].add((publication["model"], publication["region"], str(publication.get("lang") or "")))
    except (OSError, UnicodeDecodeError, KeyError):
        return None
    return {sha: {"versions": len(rows), "editions": len({(m, r) for m, r, _ in rows})} for sha, rows in routes.items()}


def _symbol_row(entry: dict[str, Any], usage: dict[str, dict[str, int]] | None) -> dict[str, Any]:
    sha = _text(entry, "sha256")
    raw_provenance = entry.get("provenance")
    provenance = raw_provenance if isinstance(raw_provenance, dict) else {}
    use = (usage or {}).get(sha) or {}
    return {"key": _text(entry, "key"), "file": Path(_text(entry, "path")).name, "status": _text(entry, "status"),
            "hash": sha[:12], "source": bool(provenance.get("source")),
            "versions": use.get("versions"), "editions": use.get("editions")}


def symbols_view(root: Path, srcdir: Path, publications: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The shared symbols with provenance, hash and use; None when the manifest is unreadable."""
    manifest_path = root / REGISTRIES["symbols"][0]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = [entry for entry in manifest["assets"] if isinstance(entry, dict)]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    pages = published_pages(srcdir, publications)
    usage = symbol_usage(pages, {str(entry.get("sha256") or "") for entry in entries}) if pages else None
    rows = [_symbol_row(entry, usage) for entry in entries]
    if usage is not None:
        rows.sort(key=lambda row: (-(row["versions"] or 0), row["key"]))
    return {
        "total": len(rows),
        "with_source": sum(row["source"] for row in rows),
        "withdrawn": len(manifest.get("withdrawn") or []),
        "counted": usage is not None, "pages": len(pages),
        "used": sum(bool(row["versions"]) for row in rows) if usage is not None else None,
        "rows": rows,
    }


def _label(note: str | None) -> str:
    """A tile's caption from its 用途 note: the plain text up to the first colon, without the closing 。."""
    text = re.sub(r"<[^>]+>", "", note or "").strip()
    return re.split(r"[：:]", text, maxsplit=1)[0].strip().rstrip("。").strip()


def front_view(library: dict[str, Any] | None, grounds: dict[str, str], symbols: dict[str, Any] | None,
               *, build_date: str) -> dict[str, Any] | None:
    """视觉媒体's front: the shared icons and illustrations by type, for colleagues to browse.

    It reads the 图标与素材 gallery the design page publishes (``design_assets.asset_gallery``), so a tile's image is
    that page's published copy. A caption is the meaning from the gallery notes; how many manuals show a symbol comes
    from ``symbols_view``. No keys, hashes, paths or statuses; None without the gallery.
    """
    if not library or not library.get("groups"):
        return None
    editions = {row["key"]: row["editions"] for row in (symbols or {}).get("rows") or [] if row.get("editions")}
    types, items = [], []
    for group in library["groups"]:
        types.append({"id": group["id"], "title": group["title"], "count": len(group["items"])})
        for item in group["items"]:
            label = _label(item.get("note"))
            items.append({"group": group["id"], "type": group["title"], "src": item["ref"], "label": label,
                          "background": grounds.get(item["ground"], "#ffffff"),
                          "editions": editions.get(item.get("key") or ""),
                          "search": f"{label} {group['title']}".lower()})
    return {"count": len(items), "types": types, "items": items, "updated": build_date}


__all__ = ["ASSET_REGISTRY_CSV", "front_view", "published_pages", "registry_view", "symbol_usage", "symbols_view"]
