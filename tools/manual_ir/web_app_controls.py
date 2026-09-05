"""Prepared App control paragraphs and their owned public IR contract."""
from __future__ import annotations

from pathlib import Path
import re

from bs4 import BeautifulSoup, Tag

from tools.manual_ir import ManualIR, ManualIRValidationError, validate_manual_ir
from tools.manual_ir.hashing import file_sha256, value_sha256
from tools.manual_ir.source import ManualSource
from tools.manual_ir.web_source import make_web_source
from tools.utils.path_utils import get_paths


def _control_payload(paragraph_html):
    if not isinstance(paragraph_html, str):
        raise ValueError("App add-device paragraph must be HTML")
    soup = BeautifulSoup(paragraph_html, "html.parser")
    paragraph = soup.p
    if not isinstance(paragraph, Tag) or str(paragraph) != paragraph_html:
        raise ValueError("App add-device requires exactly one retained paragraph")
    labels = paragraph.find_all("strong")
    if len(labels) != 1:
        raise ValueError("App add-device paragraph must contain exactly one visible label")
    label = labels[0].get_text(" ", strip=True)
    if not label or labels[0].find(["img", "svg"]):
        raise ValueError("App add-device label must be nonempty text without discarded artwork")
    assets = []
    for image in paragraph.find_all("img"):
        if not str(image.get("src") or "").strip():
            raise ValueError("App add-device paragraph image is missing its source")
        assets.append({"src": str(image["src"])})
    return {"paragraph_html": paragraph_html, "label": label, "assets": assets}


def load_web_control_source(
    html: str, *, source_path: Path, config: dict,
    language: str | None = None, model: str | None = None, region: str | None = None,
) -> ManualSource:
    prefix = config.get("add_device_paragraph_prefix")
    terms = config.get("button_terms")
    if (not isinstance(prefix, str) or not prefix.strip() or not isinstance(terms, list)
            or not terms or any(not isinstance(t, str) or not t.strip() for t in terms)):
        raise ValueError(f"{source_path}: App control requires a prefix and button vocabulary")
    soup = BeautifulSoup(html, "html.parser")
    candidates = [p for p in soup.find_all("p") if p.get_text(" ", strip=True).startswith(prefix)]
    if len(candidates) != 1:
        raise ValueError(f"{source_path}: expected one {prefix} add-device paragraph, found {len(candidates)}")
    paragraph = candidates[0]
    pattern = rf"\b(?:{'|'.join(re.escape(t) for t in terms)})\b"
    if not re.search(pattern, paragraph.get_text(" ", strip=True), flags=re.IGNORECASE):
        raise ValueError(f"{source_path}: App setup {prefix} paragraph has no localized button term")
    payload = _control_payload(str(paragraph))
    contracts = get_paths().renderer_contracts_dir
    return make_web_source(
        html, source_path=source_path, blocks=(("web_app_control", payload),),
        projection="web-app-control", language=language, model=model, region=region,
        style_contract_sha256=value_sha256({
            "config": config,
            "app_stylesheet": file_sha256(contracts / "web_app_components.css"),
            "manual_stylesheet": file_sha256(contracts / "web_manual.css"),
        }),
    )


def decode_control_ir(ir: ManualIR) -> dict:
    issues = validate_manual_ir(ir, require_zero_skipped_raw=True)
    if issues:
        raise ManualIRValidationError(ir.source, issues)
    if (ir.metadata.get("projection") != "web-app-control" or len(ir.pages) != 1
            or len(ir.pages[0].blocks) != 1):
        raise ValueError("expected a single-block web-app-control projection")
    block = ir.pages[0].blocks[0]
    payload = block.payload
    if block.kind != "web_app_control" or not isinstance(payload, dict):
        raise ValueError(f"{block.source_ref}: incomplete App control payload")
    if _control_payload(payload.get("paragraph_html")) != payload:
        raise ValueError(f"{block.source_ref}: App control label/assets disagree with retained markup")
    return payload
