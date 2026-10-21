"""Extract declared source-native illustration candidates; never writes online registries."""

from pathlib import Path
import hashlib
import json
import fitz

ROOT = Path(__file__).resolve().parents[1]
SVG = "{http://www.w3.org/2000/svg}"


def authority():
    identity = json.loads((ROOT / "source/pdf-identity.json").read_text())
    data = b"".join(
        (ROOT / row["path"]).read_bytes() for row in identity["archive_parts"]
    )
    if hashlib.sha256(data).hexdigest() != identity["sha256"]:
        raise ValueError("source PDF identity changed")
    return fitz.open(stream=data, filetype="pdf")


def extract():
    target = ROOT / "assets"
    target.mkdir(exist_ok=True)
    inventory = []
    with authority() as source:
        for recipe in json.loads((ROOT / "source/artwork-recipes.json").read_text()):
            doc = fitz.open()
            doc.insert_pdf(
                source, from_page=recipe["page"] - 1, to_page=recipe["page"] - 1
            )
            page = doc[0]
            crop = fitz.Rect(recipe["crop"])
            keep_all = recipe["mode"] in {
                "dense-labeled-diagram",
                "numbered-display-map",
                "display-art",
                "store-badges",
                "qr",
                "ui-screenshot",
            }
            removed = []
            if not keep_all:
                for block in page.get_text(
                    "dict", flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES
                )["blocks"]:
                    for line in block.get("lines", []):
                        for span in line["spans"]:
                            if (
                                span["size"] > 4
                                and span["text"].strip()
                                not in recipe.get("keep_text", [])
                                and crop.intersects(fitz.Rect(span["bbox"]))
                            ):
                                x0, y = span["origin"]
                                box = fitz.Rect(
                                    span["bbox"][0] - 0.1,
                                    y - span["size"] * 0.95,
                                    span["bbox"][2] + 0.1,
                                    y + span["size"] * 0.2,
                                )
                                page.add_redact_annot(box, fill=False)
                                removed.append(span["text"])
                for box in recipe.get("drop_text", []):
                    page.add_redact_annot(fitz.Rect(box), fill=False)
                page.apply_redactions(
                    images=fitz.PDF_REDACT_IMAGE_NONE,
                    graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                )
                for box in recipe.get("drop_frames", []):
                    page.add_redact_annot(fitz.Rect(box), fill=False)
                if recipe.get("drop_frames"):
                    page.apply_redactions(
                        images=fitz.PDF_REDACT_IMAGE_NONE,
                        graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
                        text=fitz.PDF_REDACT_TEXT_NONE,
                    )
            # Rasterize the isolated illustration, never a body/table/page. MuPDF's
            # SVG export drops clipping for this Illustrator source's reused XObjects.
            # The native PDF renderer preserves their transforms and complete frames.
            raw = page.get_pixmap(
                clip=crop, matrix=fitz.Matrix(4, 4), alpha=False
            ).tobytes("png")
            path = target / (recipe["key"] + ".png")
            path.write_bytes(raw)
            inventory.append(
                {
                    **recipe,
                    "path": "assets/" + path.name,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "size": len(raw),
                    "removed_external_text": removed,
                }
            )
            doc.close()
    (ROOT / "source/extracted-artwork.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n"
    )
    print("extracted", len(inventory), "illustrations")


if __name__ == "__main__":
    extract()
