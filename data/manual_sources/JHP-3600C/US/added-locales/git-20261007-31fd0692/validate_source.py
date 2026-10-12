"""Validate locale copy coverage and consumed asset decisions against frozen output."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from bs4 import BeautifulSoup

PACKAGE = Path(__file__).resolve().parent


def normalized(value: str) -> str:
    return re.sub(r"\W", "", unicodedata.normalize("NFKC", value).lower())


def validate(language: str, output: Path) -> dict:
    source = PACKAGE / "source" / language
    markup = next(output.glob("manual*.md")).read_text()
    corpus = normalized(BeautifulSoup(markup[markup.index("# Jackery"):], "html.parser").get_text(" "))
    decisions = json.loads((source / "asset_decisions.json").read_text())
    exceptions = json.loads((source / "illustrative_copy_exceptions.json").read_text())
    allowed = {(r["page"], r["block"], r["text"]): r["reason"] for r in exceptions}
    covered = 0
    illustrated = 0
    failures = []
    for page in json.loads((source / "native_pages.json").read_text()):
        rows = page["rows"]
        if page["page"] == 2:
            rows = rows[4:8] if language == "fr" else rows[8:12]
        for index, block in enumerate(rows):
            for line in block["lines"]:
                text = line["text"].strip()
                token = normalized(text)
                if len(token) < 3 or text.isnumeric():
                    continue
                if token in corpus:
                    covered += 1
                    continue
                box = line["bbox"]
                framed = any(
                    a.get("physical_page") == page["page"]
                    and a["bbox"][0] <= box[0] + 1
                    and a["bbox"][1] <= box[1] + 1
                    and a["bbox"][2] >= box[2] - 1
                    and a["bbox"][3] >= box[3] - 1
                    for a in decisions if "bbox" in a
                )
                if framed:
                    covered += 1
                elif (page["page"], index, text) in allowed:
                    illustrated += 1
                else:
                    failures.append((page["page"], index, text))
    for row in decisions:
        asset = output / row["final_path"]
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()
        if digest != row["sha256"]:
            failures.append(("asset changed", row["final_path"]))
        if row["decision"] == "reuse byte-identical":
            repo = next(p for p in PACKAGE.parents if (p / "build.py").is_file())
            original = repo / row["candidate"]
            if digest != hashlib.sha256(original.read_bytes()).hexdigest():
                failures.append(("reuse mismatch", row["final_path"]))
    if failures:
        raise ValueError(f"source coverage or assets failed: {failures}")
    return {"language": language, "covered_lines": covered,
            "illustrative_exceptions": illustrated, "assets": len(decisions), "failures": []}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=["fr", "es"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.language, args.output), indent=2))
