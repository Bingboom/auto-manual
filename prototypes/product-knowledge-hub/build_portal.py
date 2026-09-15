"""Read frozen publications and emit a separate portal; never mutate publish."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
import shutil
import sys
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.rtd_portal import ASSETS, catalog  # noqa: E402
from tools.utils.path_utils import PathSegments  # noqa: E402

CATEGORIES = {"Power stations": "便携储能", "Battery packs": "加电包", "Solar panels": "太阳能板", "Accessories": "配件"}


def read_practices(path: Path, audience: str) -> list[dict]:
    entries = json.loads(path.read_text(encoding="utf-8"))["practices"]
    result = []
    for item in entries:
        if audience == "public" and item.get("visibility") != "public":
            continue
        url = urlsplit(item["url"])
        if url.scheme != "https" or url.hostname != "alidocs.dingtalk.com" or url.username or url.password or url.port not in (None, 443):
            raise ValueError("Practice links must use https://alidocs.dingtalk.com")
        if not item.get("title", "").strip() or not isinstance(item.get("tags", []), list):
            raise ValueError("Practice title and tag list are required")
        date = item.get("updated_at", "")
        if date:
            datetime.fromisoformat(date)
        result.append({"title": item["title"], "summary": item.get("summary", ""),
                       "tags": item.get("tags", []), "url": item["url"], "updated_at": date})
    return result


def build(publish: Path, output: Path, base_url: str, links: Path, audience: str) -> dict:
    publish, output = publish.resolve(), output.resolve()
    if output.is_relative_to(publish) or publish.is_relative_to(output):
        raise ValueError("Portal output must be separate from publish")
    assets = Path(__file__).resolve().parent
    if output.is_relative_to(assets) or assets.is_relative_to(output):
        raise ValueError("Portal output must be separate from prototype source")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use an empty output directory to avoid stale internal content")
    url = urlsplit(base_url)
    if url.scheme != "https" or not url.netloc or url.query or url.fragment or url.username or url.password:
        raise ValueError("A public HTTPS manual base URL is required")
    base_url = base_url.rstrip('/') + '/'
    web = publish / PathSegments.WEB
    if not (web / "index.md").is_file():
        raise ValueError("Missing frozen publication index")
    manifest_path = publish / "publish_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    targets = {(t["route"], t["manual"]): t for t in manifest["targets"]}
    settings = json.loads((ASSETS / "settings.json").read_text(encoding="utf-8"))
    products, updates, copies = [], [], []
    for product in catalog(web, settings):
        image = ""
        if product["image"]:
            source = web / product["image"]
            image = "assets/" + hashlib.sha256(source.read_bytes()).hexdigest()[:20] + source.suffix
            copies.append((source, image))
        products.append({
            "model": product["model"], "name": product["name"], "region": product["region"],
            "edition": product["edition"], "category": CATEGORIES.get(product["category"], product["category"]),
            "image": image, "url": urljoin(base_url, product["url"]),
            "languages": [{"label": a["label"], "code": a["code"], "url": urljoin(base_url, a["url"])}
                          for a in product["language_options"] if a["url"]],
        })
        for publication in product["publications"]:
            path = Path(publication["url"])
            target = targets.get((path.parent.as_posix(), path.with_suffix('.md').name), {})
            date = target.get("built_at")
            if not date:
                continue
            datetime.fromisoformat(date)
            updates.append({"kind": "product", "model": product["model"], "region": product["region"],
                            "title": product["name"], "summary": f'{product["model"]} / {product["edition"]} · {publication.get("version") or ""}',
                            "date": date, "dateLabel": "发布包构建于", "url": urljoin(base_url, publication["url"])})
    practices = read_practices(links, audience)
    for item in practices:
        if item["updated_at"]:
            updates.append({"kind": "practice", "title": item["title"], "summary": item["summary"],
                            "date": item["updated_at"], "dateLabel": "文档更新于", "url": item["url"]})
    updates.sort(key=lambda a: a["date"][:10], reverse=True)
    output.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "styles.css", "app.js"):
        shutil.copyfile(assets / name, output / name)
    for source, relative in copies:
        destination = output / relative
        destination.parent.mkdir(exist_ok=True)
        shutil.copyfile(source, destination)
    resources = {"audience": audience, "practices": practices, "updates": updates}
    for name, value in (("products.json", products), ("resources.json", resources)):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding="utf-8")
    receipt = {"products": len(products), "practices": len(practices), "audience": audience,
               "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest()}
    (output / "portal-source.json").write_text(json.dumps(receipt, indent=2) + '\n', encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manual-base-url", required=True)
    parser.add_argument("--links", type=Path, default=Path(__file__).with_name("practice-links.json"))
    parser.add_argument("--audience", choices=("internal", "public"), default="internal")
    args = parser.parse_args()
    print(json.dumps(build(args.publish_root, args.output, args.manual_base_url, args.links, args.audience)))
