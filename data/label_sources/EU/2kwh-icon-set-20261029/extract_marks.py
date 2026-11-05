"""Re-derive the label-sourced shared Web symbols from the label PDFs in this folder.

Run from the repository root:

    python data/label_sources/EU/2kwh-icon-set-20261029/extract_marks.py --check
    python data/label_sources/EU/2kwh-icon-set-20261029/extract_marks.py --output <unused dir>

Every ``shared/symbols/manifest.json`` entry whose ``provenance.source`` lives in
this folder is replayed. ``native_symbol_svg`` keeps exactly the recorded
drawings inside the recorded glyph box (``native_sha256``). Paths listed in
``hidden_fill_ordinals`` are drawn in the label background colour straight on
the background, so the label never shows them; they keep ``fill="none"``. The
recorded ``ink_map`` then replaces only the label colours (the operator-approved
exception of 2026-11-02, see README.md), giving the library bytes (``sha256``).
``--check`` compares both hashes and the library file; ``--output`` writes the
native and inked SVGs for review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

SOURCE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = next(p for p in SOURCE_ROOT.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO_ROOT))

import fitz  # noqa: E402

from tools.asset_pipeline.native_svg import native_symbol_svg  # noqa: E402

LIBRARY = REPO_ROOT / "docs/renderers/web/assets/shared/symbols"
COLOUR = re.compile(r'((?:fill|stroke)=")(#[0-9a-f]{6})(")')
FILLED_PATH = re.compile(r'<path\b[^>]*\bfill="#[0-9a-f]{6}"[^>]*>')


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ink(native: bytes, ink_map: dict[str, str], hidden: list[int]) -> bytes:
    """Unfill the hidden paths, then swap label colours; the map must cover exactly the rest."""
    text = native.decode("utf-8")
    tags = list(FILLED_PATH.finditer(text))
    if any(not 0 <= i < len(tags) for i in hidden):
        raise ValueError("hidden path ordinal out of range")
    for i in sorted(hidden, reverse=True):
        tag = tags[i]
        text = text[:tag.start()] + re.sub(r'\bfill="#[0-9a-f]{6}"', 'fill="none"', tag[0], count=1) + text[tag.end():]
    used = {colour for _, colour, _ in COLOUR.findall(text)}
    if used != ink_map.keys():
        raise ValueError("ink_map must cover exactly the label colours " + ", ".join(sorted(used)))
    return COLOUR.sub(lambda m: m[1] + ink_map[m[2]] + m[3], text).encode("utf-8")


def label_entries() -> list[dict]:
    manifest = json.loads((LIBRARY / "manifest.json").read_text(encoding="utf-8"))
    folder = SOURCE_ROOT.relative_to(REPO_ROOT).as_posix() + "/"
    return [a for a in manifest["assets"] if a.get("provenance", {}).get("source", "").startswith(folder)]


def replay(entry: dict) -> tuple[bytes, bytes]:
    provenance = entry["provenance"]
    source = REPO_ROOT / provenance["source"]
    if sha256(source.read_bytes()) != provenance["source_sha256"]:
        raise ValueError(entry["key"] + ": source label changed")
    with fitz.open(source) as document:
        page = document[provenance["physical_page"] - 1]
        native = native_symbol_svg(page, provenance["drawing_indices"], provenance["glyph_bbox"])
    return native, ink(native, provenance["ink_map"], provenance.get("hidden_fill_ordinals", []))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="compare replayed bytes with the manifest")
    mode.add_argument("--output", type=Path, help="unused directory for the native and inked SVGs")
    args = parser.parse_args()
    entries = label_entries()
    if not entries:
        raise SystemExit("no manifest entries point at this folder")
    if args.output:
        if args.output.exists():
            raise SystemExit("use an unused output directory")
        args.output.mkdir(parents=True)
    failures = 0
    for entry in entries:
        native, inked = replay(entry)
        name = Path(entry["path"]).name
        if args.output:
            (args.output / name.replace(".svg", ".native.svg")).write_bytes(native)
            (args.output / name).write_bytes(inked)
            print(f"wrote {name}")
            continue
        library = (LIBRARY / entry["path"]).read_bytes()
        problems = [label for label, ok in (
            ("native", sha256(native) == entry["provenance"]["native_sha256"]),
            ("inked", sha256(inked) == entry["sha256"]),
            ("library file", sha256(library) == entry["sha256"]),
        ) if not ok]
        failures += bool(problems)
        print(f"{'FAIL' if problems else 'ok  '} {entry['key']}" + (f" ({', '.join(problems)} differ)" if problems else ""))
    if failures:
        print(f"PyMuPDF {fitz.VersionBind} / MuPDF {fitz.VersionFitz}: native bytes were recorded with 1.28.0 / 1.29.0")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
