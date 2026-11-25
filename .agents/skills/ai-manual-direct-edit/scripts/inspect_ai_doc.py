#!/usr/bin/env python3
"""Generate and optionally run a pure-ASCII Illustrator inspection script."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_illustrator_jsx import check_pure_ascii, run_in_illustrator  # noqa: E402


def js_escape(value: str) -> str:
    """Encode a string as a strictly ASCII JavaScript string literal."""
    return json.dumps(value, ensure_ascii=True)


def load_page_boxes(path: Path) -> list[dict[str, Any]]:
    """Load [{"name": "...", "rect": [left, top, right, bottom]}, ...] from JSON."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("page-boxes JSON must be a non-empty list of {name, rect} objects")
    boxes: list[dict[str, Any]] = []
    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict) or "rect" not in entry:
            raise ValueError(f"page-boxes[{idx}] must be an object with 'rect'")
        rect = entry["rect"]
        if not isinstance(rect, list) or len(rect) != 4:
            raise ValueError(f"page-boxes[{idx}].rect must be [left, top, right, bottom]")
        name = str(entry.get("name") or f"Page_{idx + 1:02d}")
        boxes.append({"name": name, "rect": [float(v) for v in rect]})
    return boxes


def build_inspect_jsx(
    source_path: Path,
    report_path: Path,
    dump_frames_path: Path | None = None,
    page_boxes: list[dict[str, Any]] | None = None,
    max_artboards: int | None = None,
) -> str:
    """Build a strictly pure-ASCII ExtendScript that inspects artboards and text frames."""
    lines: list[str] = [
        "#target illustrator",
        "app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;",
        f"var SRC_PATH = {js_escape(str(source_path.resolve()))};",
        f"var REPORT_PATH = {js_escape(str(report_path.resolve()))};",
        f"var FRAMES_PATH = {js_escape(str(dump_frames_path.resolve())) if dump_frames_path else 'null'};",
        f"var CUSTOM_BOXES = {json.dumps(page_boxes, ensure_ascii=True) if page_boxes else 'null'};",
        f"var MAX_AB = {max_artboards if max_artboards is not None else 'null'};",
        "",
        "var doc = app.open(new File(SRC_PATH));",
        "var rep = new File(REPORT_PATH);",
        'rep.encoding = "UTF-8";',
        'rep.open("w");',
        'rep.writeln("Name: " + doc.name);',
        'rep.writeln("ColorSpace: " + doc.documentColorSpace);',
        'rep.writeln("Artboards: " + doc.artboards.length);',
        'rep.writeln("Layers: " + doc.layers.length);',
        'rep.writeln("TextFrames: " + doc.textFrames.length);',
        'rep.writeln("");',
        "for (var li = 0; li < doc.layers.length; li++) {",
        "    var lay = doc.layers[li];",
        '    rep.writeln("Layer[" + li + "]: " + lay.name + " visible=" + lay.visible + " locked=" + lay.locked + " items=" + lay.pageItems.length);',
        "}",
        'rep.writeln("");',
        "for (var ai = 0; ai < doc.artboards.length; ai++) {",
        "    var ab = doc.artboards[ai];",
        "    var r = ab.artboardRect;",
        "    var w = (r[2] - r[0]).toFixed(1);",
        "    var h = (r[1] - r[3]).toFixed(1);",
        '    rep.writeln("AB[" + ai + "] name=" + ab.name + " rect=[" + r[0].toFixed(1) + "," + r[1].toFixed(1) + "," + r[2].toFixed(1) + "," + r[3].toFixed(1) + "] size=" + w + "x" + h);',
        "}",
        "rep.close();",
        "",
        "if (FRAMES_PATH) {",
        "    var boxes = [];",
        "    if (CUSTOM_BOXES) {",
        "        boxes = CUSTOM_BOXES;",
        "    } else {",
        "        var limit = MAX_AB ? Math.min(MAX_AB, doc.artboards.length) : doc.artboards.length;",
        "        for (var bi = 0; bi < limit; bi++) {",
        "            boxes.push({ name: doc.artboards[bi].name, rect: doc.artboards[bi].artboardRect });",
        "        }",
        "    }",
        "    var out = new File(FRAMES_PATH);",
        '    out.encoding = "UTF-8";',
        '    out.open("w");',
        "    for (var pi = 0; pi < boxes.length; pi++) {",
        "        var bx = boxes[pi];",
        "        var rect = bx.rect;",
        '        out.writeln("================ " + bx.name + " [" + rect[0].toFixed(1) + "," + rect[1].toFixed(1) + "," + rect[2].toFixed(1) + "," + rect[3].toFixed(1) + "] ================");',
        "        for (var ti = 0; ti < doc.textFrames.length; ti++) {",
        "            var tf = doc.textFrames[ti];",
        "            var gb = tf.geometricBounds;",
        "            var cx = (gb[0] + gb[2]) / 2.0;",
        "            var cy = (gb[1] + gb[3]) / 2.0;",
        "            if (cx >= rect[0] - 2 && cx <= rect[2] + 2 && cy <= rect[1] + 2 && cy >= rect[3] - 2) {",
        "                var px = (gb[0] - rect[0]).toFixed(1);",
        "                var py = (rect[1] - gb[1]).toFixed(1);",
        "                var fw = (gb[2] - gb[0]).toFixed(1);",
        "                var fh = (gb[1] - gb[3]).toFixed(1);",
        '                var kind = (tf.kind == TextType.AREATEXT) ? "AREA" : ((tf.kind == TextType.POINTTEXT) ? "PT  " : "PATH");',
        '                var fontInfo = "?";',
        "                try {",
        "                    var ca = tf.textRange.characterAttributes;",
        '                    fontInfo = ca.textFont.name + "/" + ca.size.toFixed(1);',
        "                } catch (e) {}",
        '                var txt = tf.contents.replace(/\\r/g, "\\\\r").replace(/\\n/g, "\\\\n");',
        '                out.writeln("  TF[" + ti + "] " + kind + " x=" + px + " y=" + py + " w=" + fw + " h=" + fh + " " + fontInfo + " | " + txt);',
        "            }",
        "        }",
        "    }",
        "    out.close();",
        "}",
        "doc.close(SaveOptions.DONOTSAVECHANGES);",
        '"OK";',
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect artboards, layers, and native TextFrames in an Illustrator .ai/.pdf."
    )
    parser.add_argument("--source", required=True, type=Path, help="Path to scratch .ai or .pdf copy.")
    parser.add_argument("--out-report", required=True, type=Path, help="Path for artboard/layer report.")
    parser.add_argument(
        "--dump-frames",
        type=Path,
        default=None,
        help="Optional path to dump page-relative TextFrame coordinates and contents.",
    )
    parser.add_argument(
        "--page-boxes",
        type=Path,
        default=None,
        help="Optional JSON list of {name, rect:[l,t,r,b]} boxes for single-sheet imposition masters.",
    )
    parser.add_argument(
        "--max-artboards",
        type=int,
        default=None,
        help="Optional cap on artboards dumped when --page-boxes is omitted.",
    )
    parser.add_argument(
        "--emit-jsx",
        type=Path,
        default=None,
        help="Write generated ExtendScript to this path without launching Illustrator.",
    )
    parser.add_argument(
        "--app",
        default="Adobe Illustrator",
        help='macOS application name for osascript (default: "Adobe Illustrator").',
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    page_boxes = load_page_boxes(args.page_boxes) if args.page_boxes is not None else None
    jsx = build_inspect_jsx(
        source_path=args.source,
        report_path=args.out_report,
        dump_frames_path=args.dump_frames,
        page_boxes=page_boxes,
        max_artboards=args.max_artboards,
    )
    ascii_errors = check_pure_ascii(jsx, label="inspect_ai_doc")
    if ascii_errors:
        for err in ascii_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    if args.emit_jsx is not None:
        args.emit_jsx.parent.mkdir(parents=True, exist_ok=True)
        args.emit_jsx.write_text(jsx, encoding="ascii")
        print(f"Wrote pure-ASCII inspection script: {args.emit_jsx}")
        return 0

    if not args.source.is_file():
        print(f"ERROR: source file not found: {args.source}", file=sys.stderr)
        return 2

    args.out_report.parent.mkdir(parents=True, exist_ok=True)
    if args.dump_frames is not None:
        args.dump_frames.parent.mkdir(parents=True, exist_ok=True)

    fd, raw_tmp = tempfile.mkstemp(prefix="ai_inspect_", suffix=".jsx")
    os.close(fd)
    tmp_jsx = Path(raw_tmp)
    try:
        tmp_jsx.write_text(jsx, encoding="ascii")
        rc, stdout, stderr = run_in_illustrator(tmp_jsx, app_name=args.app)
    finally:
        if tmp_jsx.exists():
            tmp_jsx.unlink()

    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    if rc != 0:
        return rc

    if args.out_report.is_file():
        print(args.out_report.read_text(encoding="utf-8", errors="replace"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
