"""Check native copy coverage, consumed artwork and frozen replay parity."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from bs4 import BeautifulSoup

PACKAGE = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value: str) -> str:
    return re.sub(r"\W", "", unicodedata.normalize("NFKC", value).lower())


def validate(language: str, output: Path) -> dict:
    offset = {"en": 0, "fr": 16, "es": 32}[language]
    filename = f"manual_jbp1000bsil_us_{language}"
    html_path = output / (filename + ".html")
    markup = (html_path if html_path.exists() else output / (filename + ".md")).read_text()
    soup = BeautifulSoup(markup, "html.parser")
    main = soup.select_one("[role=main]") if html_path.exists() else soup
    corpus = normalized(main.get_text(" "))
    pages = json.loads((PACKAGE / "source/native_blocks.json").read_text())
    preface = {"en": 0, "fr": 5, "es": 10}[language]
    ids = [(p, i) for p in range(4 + offset, 20 + offset)
           for i in range(len(pages[p - 1]["blocks"]))]
    ids += [(2, i) for i in range(preface, preface + 5)] + [(52, i) for i in range(3)]
    covered = 0
    failures = []
    heading = main.select_one("h1.hb-preface-heading")
    expected_heading = {"en": "US IMPORTANT", "fr": "FR IMPORTANT", "es": "ES IMPORTANTE"}[language]
    if heading is None or heading.get_text(" ", strip=True).removesuffix("¶").strip() != expected_heading:
        failures.append("native preface heading or region badge missing")
    fcc = main.select_one('[data-component-id="HB-SPECIAL-FCC"]')
    if fcc is None or len(fcc.select("ul > li")) != 4 or fcc.select_one('img[src="assets/fcc-mark.svg"]') is None:
        failures.append("FCC component, transparent mark or four measures missing")
    elif len(fcc.select("strong")) != 2:
        failures.append("FCC NOTE/MODIFICATION native labels must remain bold")
    for page, index in ids:
        block = pages[page - 1]["blocks"][index]
        if block["bbox"][1] >= 500:  # Printed footer is outside the Web body.
            continue
        for line in block["text"].splitlines():
            # Native ordered markers are rendered by HTML <ol>, not text nodes.
            value = re.sub(r"^\s*\d+\.\s+", "", line)
            token = normalized(value)
            if len(token) < 3 or value.strip().isnumeric():
                continue
            if token in corpus:
                covered += 1
                continue
            if (language, page, index, line.strip()) == (
                "en", 5, 6, "cause harmful interference to radio communications. occur"
            ):
                # Native extraction moved the second column's 'occur' to column one.
                if all(normalized(part) in corpus for part in (
                    "cause harmful interference to radio communications.",
                    "occur in a particular installation. If this",
                )):
                    covered += 1
                    continue
            failures.append((page, index, line))
    asset_root = output / "assets"
    for asset in (PACKAGE / "assets").iterdir():
        candidate = asset_root / asset.name
        if not candidate.exists() or digest(candidate) != digest(asset):
            failures.append(("artwork changed", asset.name))
    retired = json.loads((PACKAGE / "source/retired_assets.json").read_text())
    active_hashes = {digest(p) for p in asset_root.iterdir() if p.is_file()}
    if any(row["sha256"] in active_hashes for row in retired):
        failures.append("retired raster artwork reintroduced")
    if html_path.exists():
        ff = next(row for row in soup.select("tr")
                  if row.find("td") and row.find("td").get_text(strip=True) == "FF")
        if [len(lst.find_all("li", recursive=False)) for lst in ff.find_all("ol")] != [4, 5]:
            failures.append("FF corrective steps incomplete")
    else:
        frozen = PACKAGE / "web" / language
        for path in frozen.rglob("*"):
            if path.is_file() and digest(path) != digest(output / path.relative_to(frozen)):
                failures.append(("frozen replay differs", path.relative_to(frozen).as_posix()))
    if failures:
        raise ValueError(f"source coverage or frozen output failed: {failures}")
    return {"language": language, "covered_native_lines": covered,
            "artwork": len(list((PACKAGE / "assets").iterdir())), "failures": []}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=["en", "fr", "es"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.language, args.output), indent=2))
