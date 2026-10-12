"""Re-export reviewed complete native panels without ordinal path loss.

The source geometry and frame exclusions are reviewed data. Shared native_svg
retains original PDF path ancestors, clips, alpha and embedded images. Fixed
markings are selected again from the authoritative PDF's glyph outlines.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import fitz

PACKAGE = Path(__file__).resolve().parents[1]
REPO = next(p for p in PACKAGE.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
from tools.asset_pipeline.native_svg import native_art_svg  # noqa: E402

SVG = "{http://www.w3.org/2000/svg}"
HREF = "{http://www.w3.org/1999/xlink}href"


def export():
    figures = json.loads((PACKAGE / "source/figures.json").read_text())
    decisions = json.loads((PACKAGE / "source/asset_decisions.json").read_text())
    preserved_rejections = {
        d["slot"] for d in decisions if "prior_candidate_sha256" in d
    }
    markings = json.loads((PACKAGE / "source/fixed_markings.json").read_text())
    with fitz.open(next(PACKAGE.glob("*.pdf"))) as doc:
        assert (
            hashlib.sha256(next(PACKAGE.glob("*.pdf")).read_bytes()).hexdigest()
            == "477dfbd75e15c4f5cf0ef1cfb16142467027b8ab272bec04dfd92371d2d4fdc0"
        )
        for figure in figures:
            if figure["id"] in ["app-qr", "reporting-qr"]:
                continue  # Original PNG image objects, already extracted unchanged.
            page = doc[figure["page"] - 1]
            figure["drawing_indices"] = [
                i
                for i in range(len(page.get_drawings()))
                if i not in figure["removed_drawing_indices"]
            ]
            figure["selection_policy"] = (
                "complete original page path set, source crop and explicit independent caption-frame exclusions; retain original occluders and clips"
            )
            decision = next(d for d in decisions if d["slot"] == figure["id"])
            original = PACKAGE / decision["final_path"]
            decision["selection_policy"] = figure["selection_policy"]
            old_sha = hashlib.sha256(original.read_bytes()).hexdigest()
            decision.setdefault("prior_candidate_sha256", old_sha)
            decision.setdefault(
                "prior_candidate_policy",
                "superseded-do-not-reuse: incomplete ordinal path selection",
            )
        # Persist reviewed decisions before producing any updated assets.
        (PACKAGE / "source/figures.json").write_text(
            json.dumps(figures, ensure_ascii=False, indent=2) + "\n"
        )
        (PACKAGE / "source/asset_decisions.json").write_text(
            json.dumps(decisions, ensure_ascii=False, indent=2) + "\n"
        )
        for figure in figures:
            if figure["id"] in ["app-qr", "reporting-qr"]:
                continue
            page = doc[figure["page"] - 1]
            root = ET.fromstring(
                native_art_svg(page, figure["drawing_indices"], figure["bbox"])
            )
            if figure["id"] in markings:
                source = ET.fromstring(page.get_svg_image(text_as_path=True))
                definitions = {e.get("id"): e for e in source.iter() if e.get("id")}
                defs, group = (
                    ET.Element(SVG + "defs"),
                    ET.Element(SVG + "g", {"data-native-fixed-markings": figure["id"]}),
                )
                required = set()
                for attrs in markings[figure["id"]]:
                    matches = [
                        e
                        for e in source.iter(SVG + "use")
                        if all(e.get(k) == v for k, v in attrs.items())
                    ]
                    if len(matches) != 1:
                        raise ValueError("native fixed glyph binding changed")
                    group.append(deepcopy(matches[0]))
                    required.add(attrs[HREF][1:])
                for identity in sorted(required):
                    defs.append(deepcopy(definitions[identity]))
                root.extend([defs, group])
            path = PACKAGE / "assets" / (figure["id"] + ".svg")
            raw = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            path.write_bytes(raw)
            decision = next(d for d in decisions if d["slot"] == figure["id"])
            decision["sha256"] = hashlib.sha256(raw).hexdigest()
            if (
                decision["slot"] not in preserved_rejections
                and decision["sha256"] == decision["prior_candidate_sha256"]
            ):
                decision.pop("prior_candidate_sha256")
                decision.pop("prior_candidate_policy")
        (PACKAGE / "source/asset_decisions.json").write_text(
            json.dumps(decisions, ensure_ascii=False, indent=2) + "\n"
        )


if __name__ == "__main__":
    export()
