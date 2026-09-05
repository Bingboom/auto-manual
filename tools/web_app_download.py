"""Public IR consumer for App download store/QR columns."""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from tools.manual_ir import ManualIR, build_manual_ir_from_source
from tools.manual_ir.web_app_download import decode_download_ir, load_web_download_source


def render_download_ir(ir: ManualIR) -> str:
    payload = decode_download_ir(ir)
    soup = BeautifulSoup(payload["semantic_image_html"], "html.parser")
    image = soup.img
    copy_markup = [column["html"] for column in payload["columns"]]
    composition = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-app-download-composition",
            "aria-label": payload["label"],
        },
    )
    image["class"] = [*image.get("class", []), "hb-app-download-semantic-art"]

    copy_grid = soup.new_tag("div", attrs={"class": "hb-app-download-grid"})
    for column_id, markup in zip(("store", "qr"), copy_markup, strict=True):
        column = soup.new_tag(
            "div",
            attrs={
                "class": ["hb-app-download-column", f"hb-app-download-column-{column_id}"],
            },
        )
        art_frame = soup.new_tag("div", attrs={"class": "hb-app-download-art-frame"})
        art = soup.new_tag(
            "img",
            attrs={
                "class": ["hb-app-download-art", f"hb-app-download-art-{column_id}"],
                "src": payload["artwork"][column_id],
                "alt": "",
                "aria-hidden": "true",
                "loading": "lazy",
            },
        )
        art_frame.append(art)
        column.append(art_frame)
        copy = soup.new_tag(
            "div",
            attrs={"class": ["hb-app-download-copy", f"hb-app-download-copy-{column_id}"]},
        )
        paragraph = soup.new_tag("p")
        parsed = BeautifulSoup(markup, "html.parser")
        for child in list(parsed.contents):
            paragraph.append(child.extract())
        copy.append(paragraph)
        column.append(copy)
        copy_grid.append(column)
    composition.append(copy_grid)
    semantic = soup.new_tag("div", attrs={"class": "hb-app-download-semantic"})
    semantic.append(image)
    composition.append(semantic)
    return str(composition)


def transform_app_download(
    soup: BeautifulSoup, *, source_path: Path, config: dict,
    error_type: type[Exception], language: str | None = None,
    model: str | None = None, region: str | None = None,
) -> None:
    try:
        source = load_web_download_source(
            str(soup), source_path=source_path, config=config,
            language=language, model=model, region=region,
        )
        rendered = render_download_ir(build_manual_ir_from_source(source))
    except ValueError as exc:
        raise error_type(str(exc)) from exc
    # Match the validated boundary; do not reparse source copy or mutate early.
    original = source.pages[0].blocks[0][1]["semantic_image_html"]
    image = next(image for image in soup.find_all("img") if str(image) == original)
    paragraphs = image.find_parent("section").find_all("p", recursive=False)
    image.replace_with(BeautifulSoup(rendered, "html.parser").figure)
    for paragraph in paragraphs:
        paragraph.decompose()
