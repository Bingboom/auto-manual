"""Reconstruct and compare every LCD glyph in Chromium, including SVG clipping."""
from __future__ import annotations

import argparse
import base64
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

import fitz
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright

SOURCE = Path(__file__).resolve().parent
REPO = next(p for p in SOURCE.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
from tools.asset_pipeline.native_svg import native_symbol_svg  # noqa: E402
from tools.web.symbol_asset_admission import _normalized  # noqa: E402


def render(page, data, suffix):
    mime = "image/svg+xml" if suffix == ".svg" else "image/png"
    page.set_content(
        '<style>html,body{margin:0;background:transparent}img{width:256px;height:256px;object-fit:contain}</style>'
        '<img src="data:' + mime + ';base64,' + base64.b64encode(data).decode() + '">'
    )
    page.wait_for_function("document.images[0].complete && document.images[0].naturalWidth>0")
    png = page.locator("img").screenshot(omit_background=True)
    image = Image.open(BytesIO(png)).convert("RGBA")
    # Normalize physical glyph size even for smaller legacy PNG candidates.
    image = image.resize((image.width * 4, image.height * 4), Image.Resampling.LANCZOS)
    return _normalized(image), png


def validate(output, evidence):
    evidence.mkdir(parents=True, exist_ok=False)
    rows = json.loads((SOURCE / "source/lcd_provenance.json").read_text())
    refs = json.loads((SOURCE / "source/lcd_refs.json").read_text())
    if len(rows) != 26 or [r["asset_ref"] for r in rows] != refs:
        raise ValueError("LCD provenance does not cover all ordered glossary rows")
    report = []
    with fitz.open(SOURCE / "Jackery HomePower 5000 Plus.pdf") as doc, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 256, "height": 256})
        for row in rows:
            native = native_symbol_svg(doc[row["physical_page"] - 1], row["drawing_indices"], row["glyph_bbox"])
            asset = output / row["asset_ref"]
            if (hashlib.sha256(native).hexdigest() != row["reference_sha256"]
                    or hashlib.sha256(asset.read_bytes()).hexdigest() != row["asset_sha256"]):
                raise ValueError("LCD native reference or consumed asset changed")
            reference, native_png = render(page, native, ".svg")
            candidate, candidate_png = render(page, asset.read_bytes(), asset.suffix)
            error = max(ImageStat.Stat(ImageChops.difference(reference, candidate)).mean) / 255
            if error > .02:
                raise ValueError("LCD graphic differs from source: " + row["asset_ref"])
            number = row["row_index"] + 1
            (evidence / f"native-{number:02}.png").write_bytes(native_png)
            (evidence / f"candidate-{number:02}.png").write_bytes(candidate_png)
            report.append({"row": number, "asset_ref": row["asset_ref"], "max_mean_channel_error": round(error, 6)})
        browser.close()
    (evidence / "lcd_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"lcd_glyphs": len(report), "transparent": True, "maximum_error": max(r["max_mean_channel_error"] for r in report)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    validate(args.output.resolve(), args.evidence_dir.resolve())
