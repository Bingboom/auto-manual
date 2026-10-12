"""Export the pinned native intake package; keep rasterization outside MuPDF SVG."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import fitz
from lxml import etree


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--recipe", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    recipe = json.loads(args.recipe.read_text())
    assert sha(args.master) == recipe["source"]["expected_sha256"], "Master changed"
    args.scratch.mkdir(parents=True, exist_ok=True)
    removals = json.loads(Path(__file__).with_name("backdrop_paths.json").read_text())
    master = fitz.open(args.master)
    receipt = []
    for asset in recipe["assets"]:
        name = asset["asset_key"].rsplit("/", 1)[1]
        pdf_path = Path(asset["outputs"][0]["path"])
        pdf = args.package / "artifacts" / pdf_path
        target = args.output / pdf_path.with_suffix(".png")
        target.parent.mkdir(parents=True, exist_ok=True)
        box = asset["transforms"][0]["bbox_pt"]
        row = {
            "name": target.stem,
            "source_page": asset["page"],
            "bbox_pt": box,
            "path": pdf_path.with_suffix(".png").as_posix(),
            "recipe_pdf_sha256": sha(pdf),
            "source_master_sha256": sha(args.master),
        }
        if "/shared/" in asset["asset_key"]:
            doc = fitz.open(pdf)
            svg = etree.fromstring(doc[0].get_svg_image().encode())
            removed = []
            expected = removals[name]
            for element in list(svg.iter()):
                attributes = dict(element.attrib)
                if attributes in expected:
                    removed.append(attributes)
                    element.getparent().remove(element)
            assert removed == expected, f"Backdrop paths changed: {name}"
            svg_path = args.scratch / f"{name}.svg"
            svg_path.write_bytes(etree.tostring(svg))
            row.update(
                svg_sha256=sha(svg_path),
                removed_backdrop_paths=removed,
                export_engine="Chromium SVG rasterization; native clip paths preserved",
            )
        else:
            # Render the original crop to preserve the published pixel alignment.
            master[asset["page"] - 1].get_pixmap(
                matrix=fitz.Matrix(4, 4), clip=fitz.Rect(box), alpha=True
            ).save(target)
            row.update(
                png_sha256=sha(target),
                export_engine="PyMuPDF native page clip, 4x alpha",
            )
        receipt.append(row)
    (args.scratch / "export_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
