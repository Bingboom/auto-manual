"""Web projection of the shared App QR-only download variant."""
from bs4 import BeautifulSoup

from tools.component_specs.app_adapters import web_app_projection


def render_qr_download(spec, carrier_html):
    payload = web_app_projection(spec)
    soup = BeautifulSoup(carrier_html, "html.parser")
    images, paragraphs = soup.find_all("img"), soup.find_all("p")
    if (len(images) != 1 or len(paragraphs) != 1
            or images[0].get("src") != payload["source_art"]
            or paragraphs[0].get_text(" ", strip=True) != payload["paragraph"]["text"]):
        raise ValueError(f"{spec.source_ref}: App QR carrier disagrees with source slots")
    figure = soup.new_tag("figure", attrs={
        "class": "hb-app-download-composition hb-app-download-qr-only",
        "data-component-id": spec.component_id,
        "aria-label": payload["accessibility_label"],
    })
    copy = paragraphs[0]
    copy["class"] = "hb-app-download-copy"
    figure.append(copy.extract())
    image = images[0]
    for attribute in ("width", "height", "style"):
        image.attrs.pop(attribute, None)
    image["class"] = "hb-app-download-art-qr"
    figure.append(image.extract())
    return str(figure)
