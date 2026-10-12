"""Audit source-native line coverage and bound artwork; not a visual-QC substitute."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

import fitz
from bs4 import BeautifulSoup

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO_ROOT))
from tools.manual_ir.flow import flow_nodes_to_html  # noqa: E402

PACKAGE = Path(__file__).resolve().parent


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    return re.sub(r"[^a-z0-9]", "", value)


def strings(value):
    if isinstance(value, str):
        yield normalize(value)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)
    elif isinstance(value, dict):
        for key, child in value.items():
            if key not in {"carrier_flow", "source_ref", "source", "source_path",
                           "anchor", "presentation"}:
                yield from strings(child)


def check_retired_artwork(content, decisions) -> None:
    """Retain obsolete bytes for traceability, but refuse a new binding."""
    def bound_images(value):
        if isinstance(value, dict):
            if value.get("kind") == "image":
                yield value["source"]
            for child in value.values():
                yield from bound_images(child)
        elif isinstance(value, list):
            for child in value:
                yield from bound_images(child)

    retired = {row["final_path"] for row in decisions
               if row.get("decision") == "superseded-do-not-reuse"}
    rejected = retired.intersection(bound_images(content))
    if rejected:
        raise ValueError("retired artwork cannot be rebound: " + ", ".join(sorted(rejected)))


def audit() -> dict:
    content = json.loads((PACKAGE / "source/content.json").read_text())
    decisions = json.loads((PACKAGE / "source/asset_decisions.json").read_text())
    omissions = json.loads((PACKAGE / "source/illustrative_detail_omissions.json").read_text())
    check_retired_artwork(content, decisions)
    # Native lines may span strong/emphasis children; audit the same joined
    # semantic paragraphs and list items that the shared flow API presents.
    paragraphs = BeautifulSoup(flow_nodes_to_html(tuple(
        node for chapter in content["chapters"] for node in chapter["nodes"]
        if node["kind"] in {"paragraph", "list"}
    )), "html.parser").find_all(["p", "li"])
    corpus = (*strings(content), *(normalize(p.get_text()) for p in paragraphs))
    pdf = next(PACKAGE.glob("*.pdf"))
    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == content["source_sha256"]
    for row in decisions:
        asset = PACKAGE / "web/en" / row["final_path"]
        assert hashlib.sha256(asset.read_bytes()).hexdigest() == row["sha256"]
    document = fitz.open(pdf)
    counts, unmatched = {}, []
    for physical in [2, *range(4, 35), 97]:
        counts[str(physical)] = {
            "semantic_copy_including_alt": 0, "finished_panel": 0,
            "illustrative_detail_omitted": 0, "lines": 0,
        }
        for block in document[physical - 1].get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                # The preface page contains three languages; only the top English region is authoritative.
                if physical == 2 and line["bbox"][1] >= 175:
                    continue
                text = "".join(span["text"] for span in line["spans"])
                key = normalize(re.sub(r"^(WARNING\s*–\s*|NOTE:\s*|MODIFICATION:\s*)", "", text))
                if len(key) < 4:
                    continue  # isolated furniture, short glyphs and row numbers are checked visually
                counts[str(physical)]["lines"] += 1
                if any(key in candidate for candidate in corpus):
                    counts[str(physical)]["semantic_copy_including_alt"] += 1
                    continue
                rect = fitz.Rect(line["bbox"])
                covered = any(
                    row.get("physical_page") == physical
                    and row.get("decision") != "superseded-do-not-reuse"
                    and (rect & fitz.Rect(row["bbox"])).get_area() > rect.get_area() * .90
                    and not any((rect & fitz.Rect(erase[0])).get_area() > rect.get_area() * .30
                                for erase in row.get("erase_regions", []))
                    for row in decisions
                )
                if covered:
                    counts[str(physical)]["finished_panel"] += 1
                elif any(row["physical_page"] == physical
                         and (rect & fitz.Rect(row["bbox"])).get_area() > rect.get_area() * .90
                         for row in omissions):
                    counts[str(physical)]["illustrative_detail_omitted"] += 1
                else:
                    unmatched.append({"physical_page": physical, "text": text, "bbox": line["bbox"]})
    return {"schema_version": "source-native-line-coverage/v1", "source_sha256": content["source_sha256"],
            "counts": counts, "unmatched": unmatched,
            "limitations": "Positioned extractable lines only; short glyphs, outlined symbols, image text, "
                           "reading order and visual cropping also require recorded PDF/browser inspection."}


if __name__ == "__main__":
    report = audit()
    (PACKAGE / "source/coverage_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if report["unmatched"]:
        raise SystemExit(1)
