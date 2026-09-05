"""Prepared App download copy/art bindings and their public IR contract."""
from __future__ import annotations

from pathlib import Path
import re

from bs4 import BeautifulSoup, Tag

from tools.manual_ir import ManualIR, ManualIRValidationError, validate_manual_ir
from tools.manual_ir.hashing import file_sha256, value_sha256
from tools.manual_ir.source import ManualSource
from tools.manual_ir.web_source import make_web_source
from tools.utils.path_utils import get_paths


def _download_payload(label, image_html, copies, artwork):
    """Canonicalize only the owned data, never consult source/config on replay."""
    if not isinstance(label, str) or not label.strip():
        raise ValueError("App download section requires a nonempty heading")
    if (not isinstance(artwork, dict) or set(artwork) != {"store", "qr"}
            or any(not isinstance(x, str) or not x.strip() for x in artwork.values())):
        raise ValueError("App download requires nonempty store and QR artwork bindings")
    if not isinstance(image_html, str):
        raise ValueError("App download semantic image must be HTML")
    image_soup = BeautifulSoup(image_html, "html.parser")
    image = image_soup.img
    if not isinstance(image, Tag) or str(image) != image_html or not str(image.get("src") or "").strip():
        raise ValueError("App download requires exactly one semantic image with a source")
    if not isinstance(copies, list) or len(copies) != 2 or any(not isinstance(c, str) for c in copies):
        raise ValueError("App download requires two column copies")
    columns = []
    assets = [{"src": str(image["src"])}]
    for role, markup in zip(("store", "qr"), copies, strict=True):
        copy = BeautifulSoup(markup, "html.parser")
        text = copy.get_text(" ", strip=True)
        if not text:
            raise ValueError("App download column copy is incomplete")
        columns.append({"role": role, "html": markup, "text": text})
        assets.append({"src": artwork[role]})
        for img in copy.find_all("img"):
            if not str(img.get("src") or "").strip():
                raise ValueError("App download copy image is missing its source")
            assets.append({"src": str(img["src"])})
    return {"label": label, "semantic_image_html": image_html, "columns": columns,
            "artwork": dict(artwork), "assets": assets}


def load_web_download_source(
    html: str, *, source_path: Path, config: dict,
    language: str | None = None, model: str | None = None, region: str | None = None,
) -> ManualSource:
    soup = BeautifulSoup(html, "html.parser")
    key = config.get("image_key")
    if not isinstance(key, str) or not key.strip():
        raise ValueError(f"{source_path}: App download requires a governed image key")
    key = key.replace("\\", "/").lower()
    candidates = [image for image in soup.find_all("img")
                  if any(part in str(image.get("src", "")).replace("\\", "/").lower()
                         for part in (key, key.rsplit("/", 1)[-1]))]
    if len(candidates) != 1:
        raise ValueError(f"{source_path}: App download expected one governed image, found {len(candidates)}")
    image = candidates[0]
    section = image.find_parent("section")
    if not isinstance(section, Tag):
        raise ValueError(f"{source_path}: App download image has no section")
    headings = section.find_all("h2", recursive=False)
    if len(headings) != 1:
        raise ValueError(f"{source_path}: App download section requires exactly one H2")
    paragraphs = section.find_all("p", recursive=False)
    if any(paragraph is image.parent or paragraph in image.parents for paragraph in paragraphs):
        raise ValueError(f"{source_path}: App download image must be separate from column copy")
    if len(paragraphs) == 2:
        copies = [p.decode_contents().strip() for p in paragraphs]
    elif len(paragraphs) == 1:
        copies = [p.strip() for p in re.split(r"\s*\n+\s*", paragraphs[0].decode_contents().strip(), maxsplit=1)]
    else:
        raise ValueError(f"{source_path}: App download expected one split paragraph or two column paragraphs")
    payload = _download_payload(headings[0].get_text(" ", strip=True), str(image), copies, config.get("artwork"))
    contracts = get_paths().renderer_contracts_dir
    return make_web_source(
        html, source_path=source_path, blocks=(("web_app_download", payload),),
        projection="web-app-download", language=language, model=model, region=region,
        style_contract_sha256=value_sha256({
            "config": config,
            "app_stylesheet": file_sha256(contracts / "web_app_components.css"),
            "manual_stylesheet": file_sha256(contracts / "web_manual.css"),
        }),
    )


def decode_download_ir(ir: ManualIR) -> dict:
    issues = validate_manual_ir(ir, require_zero_skipped_raw=True)
    if issues:
        raise ManualIRValidationError(ir.source, issues)
    if (ir.metadata.get("projection") != "web-app-download" or len(ir.pages) != 1
            or len(ir.pages[0].blocks) != 1):
        raise ValueError("expected a single-block web-app-download projection")
    block = ir.pages[0].blocks[0]
    payload = block.payload
    if (block.kind != "web_app_download" or not isinstance(payload, dict)
            or not isinstance(payload.get("columns"), list)
            or any(not isinstance(c, dict) for c in payload["columns"])):
        raise ValueError(f"{block.source_ref}: incomplete App download payload")
    canonical = _download_payload(
        payload.get("label"), payload.get("semantic_image_html"),
        [c.get("html") for c in payload["columns"]], payload.get("artwork"),
    )
    if canonical != payload:
        raise ValueError(f"{block.source_ref}: App download copy/assets disagree with retained markup")
    return payload
