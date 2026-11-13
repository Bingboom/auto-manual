"""Reproduce reviewed source crops and byte-identical shared artwork bindings.

The source is an image-only PDF: every page is one embedded 300-dpi raster.
Crops are cut from that raster at native pixels (no re-rendering/resampling).
"""

from pathlib import Path
import argparse
import hashlib
import io
import json
import shutil

import fitz
from PIL import Image, ImageDraw

P = Path(__file__).resolve().parent
R = next(p for p in P.parents if (p / "build.py").is_file())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page_raster(doc, number):
    page = doc[number - 1]
    images = page.get_images(full=True)
    if len(images) != 1:
        raise ValueError(f"page {number}: expected one page raster")
    pix = fitz.Pixmap(doc, images[0][0])
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


def derive(output_root=None, write_decisions=True):
    data = json.loads((P / "source/asset_decisions.json").read_text())
    recipe = json.loads((P / "source/asset_recipes.json").read_text())
    pdf = P / "source/original.pdf"
    if sha(pdf) != recipe["source_sha256"]:
        raise ValueError("source PDF changed")
    base = output_root or P
    doc = fitz.open(pdf)
    rows = {}
    for key, entry in recipe["assets"].items():
        target = base / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if entry["mode"] == "shared-reuse":
            source = R / entry["repo_path"]
            if sha(source) != entry["repo_sha256"]:
                raise ValueError("shared artwork changed: " + key)
            shutil.copyfile(source, target)
        elif entry["mode"] == "source-crop":
            image = page_raster(doc, entry["physical_page"])
            for box in entry.get("whiteout_px", []):
                ImageDraw.Draw(image).rectangle(
                    [box[0], box[1], box[2] - 1, box[3] - 1], fill=(255, 255, 255)
                )
            image.crop(tuple(entry["image_px_box"])).save(target, format="PNG")
        else:
            raise ValueError("unknown artwork decision: " + key)
        rows[key] = {**entry, "sha256": sha(target), "bytes": target.stat().st_size}
    if write_decisions:
        data["assets"] = rows
        (P / "source/asset_decisions.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        )
    else:
        for key, row in rows.items():
            if data["assets"][key]["sha256"] != row["sha256"]:
                raise ValueError("candidate artwork bytes differ: " + key)
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="verify into an unused scratch directory instead of rewriting the package",
    )
    args = parser.parse_args()
    if args.output:
        out = args.output.resolve()
        if out.exists() or out.is_relative_to(P):
            raise SystemExit("use an unused scratch directory outside the package")
        rows = derive(out, write_decisions=False)
        print(json.dumps({"assets_verified": len(rows), "output": str(out)}))
    else:
        rows = derive()
        print(f"{P}: {len(rows)} reviewed artwork bindings")
