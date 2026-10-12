#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import struct
from pathlib import Path
from urllib.parse import unquote


_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_IMG_SRC_RE = re.compile(r'(<img\b[^>]*\bsrc=")([^"]+)(")', re.IGNORECASE)
_STYLE_ATTR_RE = re.compile(r'style="([^"]*)"', re.IGNORECASE)
_WIDTH_ATTR_RE = re.compile(r"\bwidth\s*=", re.IGNORECASE)
_HEIGHT_ATTR_RE = re.compile(r"\bheight\s*=", re.IGNORECASE)
_STYLE_WIDTH_RE = re.compile(r"\bwidth\s*:\s*([^;]+)", re.IGNORECASE)
_STYLE_HEIGHT_RE = re.compile(r"\bheight\s*:\s*([^;]+)", re.IGNORECASE)


def _normalize_css_size(value: str) -> str | None:
    token = value.strip()
    if not token:
        return None

    px_match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)px", token, re.IGNORECASE)
    if px_match:
        return str(int(round(float(px_match.group(1)))))

    pct_match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)%", token, re.IGNORECASE)
    if pct_match:
        number = float(pct_match.group(1))
        if number.is_integer():
            return f"{int(number)}%"
        return f"{number}%"

    return None


def _resolve_image_src_path(src: str) -> Path | None:
    candidate = src.strip()
    if not candidate:
        return None

    if candidate.lower().startswith("file://"):
        raw = unquote(candidate[7:])
        if raw.startswith("/") and len(raw) > 2 and raw[2] == ":":
            raw = raw[1:]
        path = Path(raw)
    else:
        path = Path(candidate)

    if path.exists() and path.is_file():
        return path.resolve()
    return None


def _read_png_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def _read_gif_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:10]
    if len(data) < 10 or data[:6] not in {b"GIF87a", b"GIF89a"}:
        return None
    width, height = struct.unpack("<HH", data[6:10])
    return width, height


def _read_bmp_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:26]
    if len(data) < 26 or data[:2] != b"BM":
        return None
    width, height = struct.unpack("<ii", data[18:26])
    return width, abs(height)


def _read_jpeg_dimensions(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as fh:
        if fh.read(2) != b"\xff\xd8":
            return None

        sof_markers = {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }

        while True:
            marker_start = fh.read(1)
            if not marker_start:
                return None
            if marker_start != b"\xff":
                continue

            marker = fh.read(1)
            while marker == b"\xff":
                marker = fh.read(1)
            if not marker:
                return None

            marker_code = marker[0]
            if marker_code in {0xD8, 0xD9}:
                continue

            length_bytes = fh.read(2)
            if len(length_bytes) != 2:
                return None
            segment_length = struct.unpack(">H", length_bytes)[0]
            if segment_length < 2:
                return None

            if marker_code in sof_markers:
                segment = fh.read(segment_length - 2)
                if len(segment) < 5:
                    return None
                height, width = struct.unpack(">HH", segment[1:5])
                return width, height

            fh.seek(segment_length - 2, 1)


def _read_image_dimensions(path: Path) -> tuple[int, int] | None:
    suffix = path.suffix.lower()
    try:
        if suffix == ".png":
            return _read_png_dimensions(path)
        if suffix == ".gif":
            return _read_gif_dimensions(path)
        if suffix == ".bmp":
            return _read_bmp_dimensions(path)
        if suffix in {".jpg", ".jpeg"}:
            return _read_jpeg_dimensions(path)
    except (OSError, struct.error, ValueError):
        return None
    return None


def _derive_height_from_width(src: str, width_value: str | None) -> str | None:
    if not width_value or width_value.endswith("%"):
        return None

    try:
        target_width = int(width_value)
    except ValueError:
        return None
    if target_width <= 0:
        return None

    img_path = _resolve_image_src_path(src)
    if img_path is None:
        return None

    dims = _read_image_dimensions(img_path)
    if not dims:
        return None

    src_width, src_height = dims
    if src_width <= 0 or src_height <= 0:
        return None

    target_height = max(1, int(round(src_height * target_width / src_width)))
    return str(target_height)


def _inject_img_dimensions(html_doc: str) -> str:
    def replace_tag(match: re.Match[str]) -> str:
        tag = match.group(0)
        style_match = _STYLE_ATTR_RE.search(tag)
        additions: list[str] = []
        width_value: str | None = None
        height_value: str | None = None
        src_match = _IMG_SRC_RE.search(tag)
        src_value = src_match.group(2) if src_match else ""

        if style_match:
            style = style_match.group(1)
            width_match = _STYLE_WIDTH_RE.search(style)
            if width_match:
                width_value = _normalize_css_size(width_match.group(1))
            height_match = _STYLE_HEIGHT_RE.search(style)
            if height_match:
                height_value = _normalize_css_size(height_match.group(1))

        if width_value and not _WIDTH_ATTR_RE.search(tag):
            additions.append(f'width="{width_value}"')

        if not _HEIGHT_ATTR_RE.search(tag):
            if not height_value:
                height_value = _derive_height_from_width(src_value, width_value)
            if height_value:
                additions.append(f'height="{height_value}"')

        if not additions:
            return tag

        if tag.endswith("/>"):
            return tag[:-2] + " " + " ".join(additions) + " />"
        return tag[:-1] + " " + " ".join(additions) + ">"

    return _IMG_TAG_RE.sub(replace_tag, html_doc)
