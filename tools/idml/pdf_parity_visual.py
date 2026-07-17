"""Visual comparison and content-occupancy helpers for IDML PDF parity."""
from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageFilter

from tools.idml.pdf_parity_contract import _sha256


DEFAULT_DISPLAY_ICC = Path("/System/Library/ColorSync/Profiles/sRGB Profile.icc")


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


def _render_page(
    pdf: Path,
    page: int,
    dpi: int,
    target: Path,
    *,
    pixel_size: tuple[int, int] | None = None,
    display_icc: Path | None = None,
) -> Path:
    command = [
        "pdftoppm", "-png", "-r", str(dpi),
        "-f", str(page), "-l", str(page), "-singlefile",
    ]
    if pixel_size is not None:
        command.extend([
            "-scale-to-x", str(pixel_size[0]),
            "-scale-to-y", str(pixel_size[1]),
        ])
    if display_icc is not None:
        command.extend(["-displayprofile", str(display_icc)])
    command.extend([str(pdf), str(target.with_suffix(""))])
    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    return target


def _visual_metrics(
    first: Path,
    second: Path,
    *,
    blur_radius: float = 0,
    changed_channel_threshold: int = 16,
    max_rgb_mad: float | None = None,
    max_changed_pixel_ratio: float | None = None,
    expected_pixel_size: tuple[int, int] | None = None,
) -> dict[str, Any]:
    with Image.open(first) as left_image, Image.open(second) as right_image:
        left = left_image.convert("RGB")
        right = right_image.convert("RGB")
        actual_size = left.size
        expected_size_match = (
            expected_pixel_size is None
            or (left.size == expected_pixel_size and right.size == expected_pixel_size)
        )
        if left.size != right.size or not expected_size_match:
            return {
                "same_pixel_size": left.size == right.size,
                "expected_pixel_size": list(expected_pixel_size)
                if expected_pixel_size else None,
                "reference_pixels": list(left.size),
                "indesign_pixels": list(right.size),
                "pass": False,
            }
        if blur_radius:
            blur = ImageFilter.GaussianBlur(radius=blur_radius)
            left = left.filter(blur)
            right = right.filter(blur)
        difference = ImageChops.difference(left, right)
        channel_histograms = [channel.histogram() for channel in difference.split()]
        pixels = left.width * left.height
        absolute = sum(
            level * count
            for histogram in channel_histograms
            for level, count in enumerate(histogram)
        )
        max_channel = ImageChops.lighter(
            ImageChops.lighter(
                difference.getchannel("R"), difference.getchannel("G"),
            ),
            difference.getchannel("B"),
        )
        changed = sum(max_channel.histogram()[changed_channel_threshold:])
        raw_rgb_mad = absolute / pixels / 3 / 255.0
        raw_changed_ratio = changed / pixels
        rgb_mad = round(raw_rgb_mad, 6)
        changed_ratio = round(raw_changed_ratio, 6)
        mad_pass = max_rgb_mad is None or raw_rgb_mad <= max_rgb_mad
        changed_pass = (
            max_changed_pixel_ratio is None
            or raw_changed_ratio <= max_changed_pixel_ratio
        )
        return {
            "same_pixel_size": True,
            "pixel_size": list(actual_size),
            "rgb_mad": rgb_mad,
            # Compatibility alias for existing report consumers.
            "mean_absolute_difference": rgb_mad,
            "max_rgb_mad": max_rgb_mad,
            "rgb_mad_pass": mad_pass,
            "changed_channel_threshold": changed_channel_threshold,
            "changed_pixel_ratio": changed_ratio,
            "max_changed_pixel_ratio": max_changed_pixel_ratio,
            "changed_pixel_ratio_pass": changed_pass,
            "pass": mad_pass and changed_pass,
        }


def _visual_report(
    reference_pdf: Path,
    indesign_pdf: Path,
    pages: list[int],
    *,
    expected_page_count: int,
    settings: dict[str, Any],
    render_page: Any = None,
) -> dict[str, Any]:
    renderer = render_page or _render_page
    metrics = []
    pixel_size = settings.get("pixel_size")
    expected_pixel_size = tuple(pixel_size) if pixel_size else None
    with tempfile.TemporaryDirectory(prefix="idml-pdf-parity-") as td:
        root = Path(td)
        for page in pages:
            reference_png = renderer(
                reference_pdf,
                page,
                settings["dpi"],
                root / f"reference-{page}.png",
                pixel_size=expected_pixel_size,
                display_icc=settings.get("display_icc"),
            )
            indesign_png = renderer(
                indesign_pdf,
                page,
                settings["dpi"],
                root / f"indesign-{page}.png",
                pixel_size=expected_pixel_size,
                display_icc=settings.get("display_icc"),
            )
            metrics.append({
                "page": page,
                **_visual_metrics(
                    reference_png,
                    indesign_png,
                    blur_radius=settings["gaussian_blur_px"],
                    changed_channel_threshold=settings["changed_channel_threshold"],
                    max_rgb_mad=settings.get("max_rgb_mad"),
                    max_changed_pixel_ratio=settings.get("max_changed_pixel_ratio"),
                    expected_pixel_size=expected_pixel_size,
                ),
            })
    comparable = [item for item in metrics if "rgb_mad" in item]
    expected_pages = list(range(1, expected_page_count + 1))
    all_pages_compared = pages == expected_pages
    failed_pages = [item["page"] for item in metrics if not item["pass"]]
    enforced = bool(settings["enforced"])
    visual_pass = all_pages_compared and not failed_pages if enforced else True
    return {
        "enforced": enforced,
        "dpi": settings["dpi"],
        "pixel_size": list(expected_pixel_size) if expected_pixel_size else None,
        "display_icc": str(settings["display_icc"].resolve())
        if settings.get("display_icc") else None,
        "display_icc_sha256": settings.get("display_icc_sha256"),
        "gaussian_blur_px": settings["gaussian_blur_px"],
        "changed_channel_threshold": settings["changed_channel_threshold"],
        "max_rgb_mad": settings.get("max_rgb_mad"),
        "max_changed_pixel_ratio": settings.get("max_changed_pixel_ratio"),
        "expected_page_count": expected_page_count,
        "compared_page_count": len(metrics),
        "all_pages_compared": all_pages_compared,
        "failed_pages": failed_pages,
        "pages": metrics,
        "mean_rgb_mad": round(
            sum(item["rgb_mad"] for item in comparable) / max(1, len(comparable)), 6,
        ),
        "mean_absolute_difference": round(
            sum(item["rgb_mad"] for item in comparable) / max(1, len(comparable)), 6,
        ),
        "mean_changed_pixel_ratio": round(
            sum(item["changed_pixel_ratio"] for item in comparable)
            / max(1, len(comparable)),
            6,
        ),
        "pass": visual_pass,
    }


def _page_text_counts(pdf: Path) -> list[int]:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    pages = result.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return [len(re.sub(r"\s+", "", page)) for page in pages]


def _occupancy_report(
    reference_counts: list[int],
    indesign_counts: list[int],
    reference_min: int = 80,
    target_min: int = 20,
) -> dict[str, Any]:
    missing = [
        {"page": index + 1, "reference_chars": left, "indesign_chars": right}
        for index, (left, right) in enumerate(
            zip(reference_counts, indesign_counts, strict=False),
        )
        if left >= reference_min and right < target_min
    ]
    return {
        "reference_min_chars": reference_min,
        "target_min_chars": target_min,
        "missing_content_pages": missing,
        "pass": not missing,
    }


def _render_settings(
    args: argparse.Namespace,
    plan: dict[str, Any] | None,
) -> dict[str, Any]:
    if plan is not None:
        contract = plan["render_contract"]
        guarded_options = {
            "dpi": contract["dpi"],
            "raster_width": contract["raster_width_px"],
            "raster_height": contract["raster_height_px"],
            "gaussian_blur": contract["gaussian_blur_px"],
            "max_rgb_mad": contract["max_rgb_mad"],
            "max_changed_pixel_ratio": contract["max_changed_pixel_ratio"],
            "changed_channel_threshold": contract["changed_channel_threshold"],
        }
        for argument, expected in guarded_options.items():
            supplied = getattr(args, argument)
            if supplied is not None and supplied != expected:
                raise ValueError(
                    f"--{argument.replace('_', '-')}={supplied} cannot override "
                    f"approved value {expected}",
                )
        display_icc = Path(args.display_icc) if args.display_icc else DEFAULT_DISPLAY_ICC
        if not display_icc.is_file():
            raise FileNotFoundError(f"display ICC profile not found: {display_icc}")
        actual_icc_sha = _sha256(display_icc)
        expected_icc_sha = contract["display_icc_sha256"]
        if actual_icc_sha != expected_icc_sha:
            raise ValueError(
                f"display ICC SHA-256 mismatch: {actual_icc_sha} != {expected_icc_sha}",
            )
        return {
            "enforced": True,
            "dpi": contract["dpi"],
            "pixel_size": (
                contract["raster_width_px"], contract["raster_height_px"],
            ),
            "display_icc": display_icc,
            "display_icc_sha256": actual_icc_sha,
            "gaussian_blur_px": contract["gaussian_blur_px"],
            "max_rgb_mad": contract["max_rgb_mad"],
            "max_changed_pixel_ratio": contract["max_changed_pixel_ratio"],
            "changed_channel_threshold": contract["changed_channel_threshold"],
        }
    display_icc = Path(args.display_icc) if args.display_icc else None
    return {
        "enforced": args.max_rgb_mad is not None
        or args.max_changed_pixel_ratio is not None,
        "dpi": args.dpi if args.dpi is not None else 72,
        "pixel_size": (
            (args.raster_width, args.raster_height)
            if args.raster_width is not None and args.raster_height is not None
            else None
        ),
        "display_icc": display_icc,
        "display_icc_sha256": _sha256(display_icc)
        if display_icc and display_icc.is_file() else None,
        "gaussian_blur_px": args.gaussian_blur or 0,
        "max_rgb_mad": args.max_rgb_mad,
        "max_changed_pixel_ratio": args.max_changed_pixel_ratio,
        "changed_channel_threshold": args.changed_channel_threshold or 16,
    }
