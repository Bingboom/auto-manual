"""Standalone Sphinx consumer and local release archives for one-language MyST."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from tools.safe_copy import assert_source_tree_no_symlinks
from tools.utils.path_utils import Paths, renderer_contracts_of, repo_root, static_dir_of

PACKAGE_UI = json.loads(
    (renderer_contracts_of(Paths(repo_root()).docs_dir) / "web_package" / "labels.json").read_text(encoding="utf-8")
)


def safe_segment(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value):
        raise ValueError(f"Expected a single portable path segment: {value!r}")
    return value


def build_package_site(
    markdown: Path, *, title: str, language: str, languages: tuple[str, ...],
    pdf_name: str, source_dir: Path, output_dir: Path,
) -> Path:
    """Use a new Sphinx source with only the current manual as its root document."""
    if language not in languages or any(lang not in PACKAGE_UI for lang in languages):
        raise ValueError("Package UI needs a supported, declared language")
    safe_segment(pdf_name)
    if source_dir.exists() or output_dir.exists():
        raise ValueError("Package source and output directories must be new")
    assert_source_tree_no_symlinks(markdown.parent, label="Package MyST source")
    source_dir.mkdir(parents=True)
    shutil.copy2(markdown, source_dir / "index.md")
    for name in ("assets", "_static"):
        if (markdown.parent / name).exists():
            shutil.copytree(markdown.parent / name, source_dir / name)
    contracts = renderer_contracts_of(Paths(repo_root()).docs_dir) / "web_package"
    templates = source_dir / "_templates"
    templates.mkdir()
    shutil.copy2(contracts / "page.html", templates / "page.html")
    static = static_dir_of(source_dir)
    static.mkdir(exist_ok=True)
    for name in ("package.css", "package.js"):
        shutil.copy2(contracts / name, static / name)
    context = {
        "package_ui": PACKAGE_UI[language], "package_pdf": pdf_name,
        "package_languages": [{"code": lang, "label": PACKAGE_UI[lang]["label"]} for lang in languages],
    }
    conf = f'''project = {title!r}
html_title = project
language = {language!r}
extensions = ["myst_parser"]
source_suffix = {{".md": "markdown"}}
root_doc = "index"
html_theme = "furo"
html_context = {context!r}
templates_path = ["_templates"]
html_static_path = ["_static"]
html_css_files = ["web_manual.css", "package.css"]
html_js_files = ["package.js"]
html_copy_source = False
html_show_sourcelink = False
html_show_sphinx = False
html_show_copyright = False
html_use_index = False
myst_heading_anchors = 3
suppress_warnings = ["myst.header"]
exclude_patterns = ["assets/**"]

from pathlib import Path
from shutil import copytree
def copy_assets(app, exception):
    source = Path(app.srcdir) / "assets"
    if exception is None and source.exists():
        copytree(source, Path(app.outdir) / "assets", dirs_exist_ok=True)
def setup(app):
    app.connect("build-finished", copy_assets)
'''
    (source_dir / "conf.py").write_text(conf, encoding="utf-8")
    subprocess.run([
        sys.executable, "-m", "sphinx", "-W", "--keep-going", "-b", "html",
        "-d", str(source_dir / ".doctrees"), str(source_dir), str(output_dir),
    ], check=True)
    return output_dir / "index.html"


def print_package_pdf(html: Path, pdf: Path, *, node: str, browser: str | None = None) -> None:
    script = Paths(repo_root()).root / "scripts" / "print_web_manual.cjs"
    command = [node, str(script), str(html.resolve()), str(pdf.resolve())]
    if browser:
        command.append(browser)
    subprocess.run(command, check=True, timeout=180)
    if not pdf.is_file() or not pdf.read_bytes().startswith(b"%PDF-"):
        raise ValueError("Browser did not produce a PDF")


def file_inventory(root: Path) -> list[dict[str, object]]:
    assert_source_tree_no_symlinks(root, label="Package release")
    return [
        {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted(root.rglob("*")) if path.is_file()
    ]


def archive_package(package: Path, archive: Path) -> dict[str, object]:
    """Stable ZIP bytes for identical input bytes; never include paths above root."""
    if archive.exists() or archive.resolve().is_relative_to(package.resolve()):
        raise ValueError("Archive must be new and outside its package")
    inventory = file_inventory(package)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for item in inventory:
            relative = str(item["path"])
            entry = zipfile.ZipInfo(f"{package.name}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            zip_file.writestr(entry, (package / relative).read_bytes())
    return {"archive": archive.name, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "bytes": archive.stat().st_size, "files": inventory}


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
