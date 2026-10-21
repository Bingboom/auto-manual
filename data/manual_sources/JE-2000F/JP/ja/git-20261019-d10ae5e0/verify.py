"""Verify source identity, native-copy coverage, shared styles, resource closure and cold replay."""

from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET

P = Path(__file__).resolve().parent
R = next(p for p in P.parents if (p / "build.py").is_file())
sys.path.insert(0, str(R))
from bs4 import BeautifulSoup  # noqa: E402
from PIL import Image  # noqa: E402
from tools.manual_ir import read_manual_ir  # noqa: E402
from tools.web.document_ir import render_document_fragments  # noqa: E402
from tools.web.prepared_style_audit import require_prepared_style_admission  # noqa: E402


def inventory(root):
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


def verify(html_root=None):
    from source.extract_artwork import authority

    native = json.loads((P / "source/native-pages.json").read_text())
    ledger = json.loads((P / "source/line-ledger.json").read_text())
    with authority() as pdf:
        assert len(pdf) == 28
        for page, recorded in zip(pdf, native, strict=True):
            assert page.get_text() == recorded["text"], recorded["page"]
    expected = {
        (page["page"], line["id"]): line["text"]
        for page in native
        for line in page["lines"]
    }
    selected = {(row["page"], row["id"]): row["text"] for row in ledger}
    assert expected == selected and len(selected) == len(ledger), (
        "missing/duplicate native source lines"
    )
    assert json.loads((P / "source/unmapped.json").read_text()) == []
    web = P / "web/ja"
    ir = read_manual_ir(web / "manual.ir.json")
    assert (ir.model, ir.region, ir.language) == ("JE-2000F", "JP", "ja")
    assert ir.metadata["publication_eligible"] is False
    soup = BeautifulSoup(
        "".join(render_document_fragments(ir, package_root=web)), "html.parser"
    )
    normal = lambda value: re.sub(r"\s+", "", value)
    visible = normal(soup.get_text(" ", strip=True))
    missing = []
    for row in ledger:
        if not row["role"].startswith("live-copy"):
            continue
        value = normal(row["text"]).lstrip("•・◦■")
        haystack = (
            visible.replace("+", "")
            if row["role"] == "live-copy/inline-plus-gap"
            else visible
        )
        if value and value not in haystack:
            missing.append([row["page"], row["id"], row["text"]])
    assert not missing, missing
    assert len(soup.select("h1")) == 13
    assert len(soup.select(".hb-key-button-pair")) == 4
    assert len(soup.select(".hb-app-download-composition")) == 1
    assert len(soup.select(".hb-inline-add-device-icon")) == 1
    notes = [
        n
        for n in soup.select(".manual-callout-table")
        if n.get_text(" ", strip=True).startswith("備考")
    ]
    assert len(notes) == 3
    assert notes[0].select_one("ul") and len(notes[0].select("li")) == 2
    assert not soup.find("style"), "source-authored paint must not enter the manual"
    assert len(ir.pages) == 13
    style = require_prepared_style_admission(
        web, json.loads((P / "source_manifest.json").read_text())
    )
    for path in (P / "assets").iterdir():
        if path.suffix == ".png":
            with Image.open(path) as image:
                image.verify()
        elif path.suffix == ".svg":
            ET.parse(path)
    # A copied shared icon/button must remain byte-identical to the reviewed library.
    reused = json.loads((P / "source/reused-assets.json").read_text())
    for row in reused:
        assert (P / row["path"]).read_bytes() == (R / row["source_path"]).read_bytes()
        assert (
            hashlib.sha256((P / row["path"]).read_bytes()).hexdigest() == row["sha256"]
        )
    resource_count = 0
    for tag in soup.find_all(["img", "a"]):
        relative = tag.get("src") if tag.name == "img" else tag.get("href")
        if not relative or relative.startswith(
            ("#", "data:", "http:", "https:", "mailto:")
        ):
            continue
        path = Path(unquote(urlparse(relative).path))
        path = path if path.is_absolute() else web / path
        assert path.is_file(), str(path)
        resource_count += 1
    # Cold import independently reuses the declared source geometry and library inputs.
    (R / ".tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="je2000f-verify-", dir=R / ".tmp") as temp:
        import shutil

        cold = Path(temp) / "source"
        shutil.copytree(P, cold, ignore=shutil.ignore_patterns("web", "__pycache__"))
        subprocess.run(
            [sys.executable, str(cold / "source/intake.py")],
            check=True,
            capture_output=True,
        )
        for rel in [
            "source/ja/content.json",
            "source/line-ledger.json",
            "source/reused-assets.json",
            "source/unmapped.json",
        ]:
            assert (cold / rel).read_bytes() == (P / rel).read_bytes(), rel
        out = Path(temp) / "replay"
        subprocess.run(
            [sys.executable, str(P / "rebuild.py"), "--output", str(out)],
            check=True,
            capture_output=True,
        )
        assert inventory(out) == inventory(web), "cold replay differs from frozen Web"
    html_report = None
    if html_root:
        page = Path(html_root) / "manual_je2000f_jp_ja.html"
        public = BeautifulSoup(page.read_text(), "html.parser")
        body = public.select_one("article")
        assert len(body.select("h1")) == 13
        for image in body.find_all("img"):
            assert (page.parent / unquote(urlparse(image["src"]).path)).is_file(), (
                image["src"]
            )
        html_report = {
            "chapters": 13,
            "images": len(body.find_all("img")),
            "missing_image_files": [],
        }
    report = {
        "model": "JE-2000F",
        "region": "JP",
        "language": "ja",
        "source_pages": 28,
        "web_chapters": 13,
        "source_lines": len(ledger),
        "live_copy_lines": sum(r["role"].startswith("live-copy") for r in ledger),
        "unmapped_source_lines": [],
        "missing_live_copy_lines": [],
        "source_line_roles": dict(Counter(r["role"].split("/")[0] for r in ledger)),
        "shared_asset_reuses": len(reused),
        "extracted_source_illustrations": 20,
        "shared_style_issues": style["issues"],
        "cold_import_equal": True,
        "cold_replay_equal": True,
        "bound_resource_references": resource_count,
        "strict_html": html_report,
        "browser_visual_qa": {
            "status": "unverified",
            "viewports": [1280, 390],
            "reason": "Browser denied localhost navigation because the admin-enforced policy could not be verified; no bypass attempted.",
        },
        "publication": "candidate only; no merge or publication authorization",
    }
    (P / "validation").mkdir(exist_ok=True)
    (P / "validation/report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html-root", type=Path)
    verify(parser.parse_args().html_root)
