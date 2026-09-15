"""Public portal data derived from canonical publications and explicit links."""
from __future__ import annotations

import json
from pathlib import Path

from tools.rtd_hub_links import read_practices

CATEGORY_LABELS = {"Power stations": "便携储能", "Battery packs": "加电包", "Solar panels": "太阳能板", "Accessories": "配件"}


def hub_context(root: Path, products: list[dict], assets: Path) -> dict:
    manifest = root.parent / "publish_manifest.json"
    targets = {}
    if manifest.is_file():
        targets = {(t["route"], t["manual"]): t for t in json.loads(manifest.read_text(encoding="utf-8"))["targets"]}
    result, updates = [], []
    for product in products:
        result.append({
            "model": product["model"], "name": product["name"], "region": product["region"],
            "edition": product["edition"], "category": CATEGORY_LABELS.get(product["category"], product["category"]),
            "image": product["image"], "url": product["url"],
            "languages": [{"code": item["code"], "label": item["label"], "url": item["url"]}
                          for item in product["language_options"] if item["url"]],
        })
        for publication in product["publications"]:
            path = Path(publication["url"])
            target = targets.get((path.parent.as_posix(), path.with_suffix('.md').name), {})
            if target.get("built_at"):
                updates.append({"kind": "product", "model": product["model"], "region": product["region"],
                                "title": product["name"], "summary": f'{product["model"]} / {product["edition"]} · {publication.get("lang") or "语言范围未核验"} · {publication.get("version") or ""}',
                                "url": publication["url"], "date": target["built_at"], "dateLabel": "发布包构建于"})
    practices = read_practices(assets / "practice-links.json", "public")
    for item in practices:
        if item["updated_at"]:
            updates.append({"kind": "practice", "title": item["title"], "summary": item["summary"],
                            "url": item["url"], "date": item["updated_at"], "dateLabel": "文档更新于"})
    updates.sort(key=lambda item: item["date"], reverse=True)
    return {"products": result, "practices": practices, "updates": updates}
