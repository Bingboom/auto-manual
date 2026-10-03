"""Public IR consumer for the live App add-device inline control."""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from tools.manual_ir import ManualIR, build_manual_ir_from_source
from tools.manual_ir.web_app_controls import decode_control_ir, load_web_control_source


def render_control_ir(ir: ManualIR) -> str:
    payload = decode_control_ir(ir)
    soup = BeautifulSoup(payload["paragraph_html"], "html.parser")
    icon = soup.new_tag(
        "span",
        attrs={
            "class": "hb-inline-add-device-icon",
            "role": "img",
            "aria-label": payload["label"],
        },
    )
    icon.string = "+"
    soup.strong.replace_with(icon)
    return str(soup.p)


def transform_app_control(
    soup: BeautifulSoup, *, source_path: Path, config: dict,
    error_type: type[Exception], language: str | None = None,
    model: str | None = None, region: str | None = None,
) -> None:
    try:
        source = load_web_control_source(
            str(soup), source_path=source_path, config=config,
            language=language, model=model, region=region,
        )
        rendered = render_control_ir(build_manual_ir_from_source(source))
    except ValueError as exc:
        raise error_type(str(exc)) from exc
    original = source.pages[0].blocks[0][1]["paragraph_html"]
    paragraph = next(p for p in soup.find_all("p") if str(p) == original)
    paragraph.replace_with(BeautifulSoup(rendered, "html.parser").p)
