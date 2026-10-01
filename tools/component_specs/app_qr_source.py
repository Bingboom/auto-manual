"""Adapt a declared QR-only source to the shared App component."""
from bs4 import Tag

from tools.component_specs.app import app_qr_download_component_spec


def parse_app_qr_download_html(soup, *, config, source_path, language):
    key = str(config.get("image_key") or "").strip()
    images = [im for im in soup.find_all("img") if key and key in str(im.get("src", ""))]
    if len(images) != 1:
        raise ValueError(f"{source_path}: App QR download needs one governed image")
    image = images[0]
    paragraph = image.find_next_sibling()
    if not isinstance(paragraph, Tag) or paragraph.name != "p" or paragraph.find(["img", "svg"]):
        raise ValueError(f"{source_path}: App QR download needs adjacent text-only copy")
    label = str(image.get("alt") or "")
    spec = app_qr_download_component_spec(
        label=label, paragraph={"text": paragraph.get_text(" ", strip=True),
                               "html": paragraph.decode_contents()},
        image_ref=str(image["src"]), source_ref=f"{source_path}#app-download",
        language=language,
    )
    return spec, (image, paragraph), (("source_art", image),), ()
