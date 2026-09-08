"""Turn a verified standalone release into a portable, immutable archive tree."""
from __future__ import annotations

import hashlib
import json
import shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from tools.safe_copy import assert_source_tree_no_symlinks
from tools.web_manual_package import file_inventory, safe_segment, write_json


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_file(root: Path, value: str) -> Path:
    if not value or "\\" in value or any(p in ("", ".", "..") for p in value.split("/")):
        raise ValueError("Invalid archive relative path")
    path = root / value
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Archive input is missing or outside its root")
    return path


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.links.extend(value for key, value in attrs if value and key in {"src", "href"})


def validate_links(root: Path) -> None:
    for html in root.rglob("*.html"):
        parser = _Links()
        parser.feed(html.read_text(encoding="utf-8"))
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (html.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file():
                raise ValueError(f"Broken local archive link in {html.name}: {link}")


def package_archive(source: Path, destination: Path) -> Path:
    """Read a web-package-release/v1, preserve body content and adapt only paths."""
    assert_source_tree_no_symlinks(source, label="Archive input")
    metadata = json.loads((source / "release.json").read_text(encoding="utf-8"))
    if metadata.get("schema_version") != "web-package-release/v1":
        raise ValueError("Archive requires a standalone release manifest")
    model, region, version = (safe_segment(metadata[k]) for k in ("model", "region", "version"))
    packages = metadata["packages"]
    if not packages or not isinstance(packages, dict):
        raise ValueError("Archive requires explicit languages")
    for lang, package in packages.items():
        safe_segment(lang)
        records = package["files"]
        actual = file_inventory(source / lang)
        if len({r['path'] for r in records}) != len(records) or actual != records:
            raise ValueError("Standalone input differs from its release manifest")
        for record in records:
            relative_file(source / lang, record["path"])
    if destination.exists() or destination.resolve().is_relative_to(source.resolve()):
        raise ValueError("Archive destination must be new and outside input")
    release = destination / "site" / "products" / model / "releases" / version
    for lang in packages:
        target = release / lang / "user-manual"
        shutil.copytree(source / lang, target)
        pdfs = list(target.glob("*.pdf"))
        if len(pdfs) != 1:
            raise ValueError("Each standalone manual needs exactly one PDF")
        old_pdf = pdfs[0].name
        pdf_name = f"{model}-user-manual-{lang}-digital-{version}.pdf"
        pdfs[0].rename(target / pdf_name)
        for html in target.rglob("*.html"):
            text = html.read_text(encoding="utf-8")
            for language in packages:
                text = text.replace(f"../{language}/index.html", f"../../{language}/user-manual/index.html")
            html.write_text(text.replace(old_pdf, pdf_name), encoding="utf-8")
    validate_links(release)
    manifest = {
        "schema_version": "web-oss-archive/v1", "model": model, "region": region,
        "version": version, "languages": list(packages), "document": "user-manual",
        "source_revision": metadata["source_revision"], "review_git_ref": metadata.get("review_git_ref", ""),
        "source_release_sha256": digest(source / "release.json"), "files": file_inventory(release),
    }
    write_json(release / "release-manifest.json", manifest)
    write_json(destination / "release-manifest.json", manifest)
    (destination / "release-note.md").write_text(
        f"# {model} / {region} / {version}\n\nOSS archive only. IT owns public links and latest.\n",
        encoding="utf-8",
    )
    return release
