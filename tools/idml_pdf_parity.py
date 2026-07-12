#!/usr/bin/env python3
"""Measure structural and visual parity between LaTeX and InDesign PDFs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_pdfinfo(text: str) -> dict[str, Any]:
    pages = re.search(r"(?m)^Pages:\s+(\d+)", text)
    size = re.search(r"(?m)^Page size:\s+([\d.]+) x ([\d.]+) pts", text)
    if not pages or not size:
        raise ValueError("pdfinfo output is missing page count or page size")
    return {
        "page_count": int(pages.group(1)),
        "page_width_pt": float(size.group(1)),
        "page_height_pt": float(size.group(2)),
    }


def _pdf_info(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["pdfinfo", str(path)], check=True, capture_output=True, text=True)
    return {"path": str(path.resolve()), "sha256": _sha256(path),
            **_parse_pdfinfo(result.stdout)}


def _selected_pages(value: str, count: int) -> list[int]:
    if value.strip().lower() == "all":
        return list(range(1, count + 1))
    selected = []
    for item in value.split(","):
        item = item.strip().lower()
        page = count if item == "last" else int(item)
        if page < 1 or page > count:
            raise ValueError(f"page {page} is outside 1-{count}")
        if page not in selected:
            selected.append(page)
    return selected


def _render_page(pdf: Path, page: int, dpi: int, target: Path) -> Path:
    subprocess.run(
        ["pdftoppm", "-png", "-r", str(dpi), "-f", str(page), "-l", str(page),
         "-singlefile", str(pdf), str(target.with_suffix(""))],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    return target


def _visual_metrics(first: Path, second: Path) -> dict[str, Any]:
    with Image.open(first) as left_image, Image.open(second) as right_image:
        left = left_image.convert("L")
        right = right_image.convert("L")
        if left.size != right.size:
            return {"same_pixel_size": False, "latex_pixels": list(left.size),
                    "indesign_pixels": list(right.size)}
        histogram = ImageChops.difference(left, right).histogram()
        pixels = left.width * left.height
        absolute = sum(level * count for level, count in enumerate(histogram))
        changed = sum(histogram[8:])
        return {
            "same_pixel_size": True,
            "pixel_size": [left.width, left.height],
            "mean_absolute_difference": round(absolute / pixels / 255.0, 6),
            "changed_pixel_ratio": round(changed / pixels, 6),
        }


def _visual_report(
    latex_pdf: Path, indesign_pdf: Path, pages: list[int], dpi: int,
) -> dict[str, Any]:
    metrics = []
    with tempfile.TemporaryDirectory(prefix="idml-pdf-parity-") as td:
        root = Path(td)
        for page in pages:
            latex_png = _render_page(latex_pdf, page, dpi, root / f"latex-{page}.png")
            indesign_png = _render_page(
                indesign_pdf, page, dpi, root / f"indesign-{page}.png")
            metrics.append({"page": page, **_visual_metrics(latex_png, indesign_png)})
    comparable = [item for item in metrics if item.get("same_pixel_size")]
    return {
        "dpi": dpi,
        "pages": metrics,
        "mean_absolute_difference": round(
            sum(item["mean_absolute_difference"] for item in comparable)
            / max(1, len(comparable)), 6),
        "mean_changed_pixel_ratio": round(
            sum(item["changed_pixel_ratio"] for item in comparable)
            / max(1, len(comparable)), 6),
    }


def _page_text_counts(pdf: Path) -> list[int]:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"], check=True,
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    pages = result.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return [len(re.sub(r"\s+", "", page)) for page in pages]


def _occupancy_report(latex_counts: list[int], indesign_counts: list[int],
                      reference_min: int = 80, target_min: int = 20) -> dict[str, Any]:
    missing = [
        {"page": index + 1, "latex_chars": left, "indesign_chars": right}
        for index, (left, right) in enumerate(zip(latex_counts, indesign_counts))
        if left >= reference_min and right < target_min
    ]
    return {"reference_min_chars": reference_min, "target_min_chars": target_min,
            "missing_content_pages": missing, "pass": not missing}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    latex_pdf = Path(args.latex_pdf)
    indesign_pdf = Path(args.indesign_pdf)
    latex = _pdf_info(latex_pdf)
    indesign = _pdf_info(indesign_pdf)
    count_match = latex["page_count"] == indesign["page_count"]
    size_delta = max(
        abs(latex["page_width_pt"] - indesign["page_width_pt"]),
        abs(latex["page_height_pt"] - indesign["page_height_pt"]),
    )
    preflight = json.loads(Path(args.preflight).read_text(encoding="utf-8"))
    manual_ir = json.loads(Path(args.manual_ir).read_text(encoding="utf-8"))
    pages = _selected_pages(args.pages, min(latex["page_count"], indesign["page_count"]))
    artifacts = {"latex_pdf": latex, "indesign_pdf": indesign}
    for key in ("idml", "indd"):
        value = getattr(args, key, None)
        if value:
            path = Path(value)
            artifacts[key] = {"path": str(path.resolve()), "sha256": _sha256(path)}
    structure_pass = count_match and size_delta <= args.page_size_tolerance
    preflight_pass = bool(preflight.get("success"))
    occupancy = _occupancy_report(
        _page_text_counts(latex_pdf), _page_text_counts(indesign_pdf))
    return {
        "schema_version": "same-source-parity/v1",
        "source_identity": {
            "content_sha256": manual_ir.get("content_sha256"),
            "bundle_sha256": manual_ir.get("bundle_sha256"),
            "style_contract_sha256": manual_ir.get("style_contract_sha256"),
        },
        "artifacts": artifacts,
        "structure": {
            "page_count_match": count_match,
            "page_size_delta_pt": round(size_delta, 6),
            "page_size_tolerance_pt": args.page_size_tolerance,
            "pass": structure_pass,
        },
        "indesign_preflight": preflight,
        "content_occupancy": occupancy,
        "visual_delta": _visual_report(latex_pdf, indesign_pdf, pages, args.dpi),
        "accepted": structure_pass and preflight_pass and occupancy["pass"],
    }


def _markdown(report: dict[str, Any]) -> str:
    visual = report["visual_delta"]
    ranked = sorted(
        visual["pages"], key=lambda item: item.get("mean_absolute_difference", -1),
        reverse=True)[:10]
    rows = "\n".join(
        f"| {item['page']} | {item.get('mean_absolute_difference', 'n/a')} | "
        f"{item.get('changed_pixel_ratio', 'n/a')} |" for item in ranked)
    return (
        "# LaTeX / InDesign Same-Source Parity\n\n"
        f"- Accepted: **{report['accepted']}**\n"
        f"- Page count match: {report['structure']['page_count_match']}\n"
        f"- Page size delta: {report['structure']['page_size_delta_pt']} pt\n"
        f"- InDesign preflight: {report['indesign_preflight'].get('success')}\n"
        f"- Content occupancy: {report['content_occupancy']['pass']}\n"
        f"- Mean visual difference: {visual['mean_absolute_difference']}\n"
        f"- Mean changed-pixel ratio: {visual['mean_changed_pixel_ratio']}\n\n"
        "Visual deltas are descriptive final-mile design differences, not a content gate.\n\n"
        "## Largest sampled visual deltas\n\n"
        "| Page | Mean absolute difference | Changed pixel ratio |\n"
        "| ---: | ---: | ---: |\n"
        f"{rows}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latex-pdf", required=True)
    parser.add_argument("--indesign-pdf", required=True)
    parser.add_argument("--preflight", required=True)
    parser.add_argument("--manual-ir", required=True)
    parser.add_argument("--idml")
    parser.add_argument("--indd")
    parser.add_argument("--pages", default="all")
    parser.add_argument("--dpi", type=int, default=72)
    parser.add_argument("--page-size-tolerance", type=float, default=0.02)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report = build_report(args)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output.with_suffix(".md").write_text(_markdown(report), encoding="utf-8")
    print(f"[idml-pdf-parity] {'OK' if report['accepted'] else 'FAIL'}: {output}")
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
