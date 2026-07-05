"""Structural validation of a built .idml package (componentization P1)."""
from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .params import MIMETYPE


def check_idml(path: Path) -> list[str]:
    issues: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        duplicates = sorted({name for name in names if names.count(name) > 1})
        for name in duplicates:
            issues.append(f"duplicate package part: {name}")
        if names[0] != "mimetype":
            issues.append("mimetype is not the first zip entry")
        info = zf.getinfo("mimetype")
        if info.compress_type != zipfile.ZIP_STORED:
            issues.append("mimetype entry is compressed (must be STORED)")
        if zf.read("mimetype").decode() != MIMETYPE:
            issues.append("mimetype content mismatch")
        for name in names:
            if name.endswith(".xml"):
                try:
                    ET.fromstring(zf.read(name))
                except ET.ParseError as exc:
                    issues.append(f"{name}: XML parse error: {exc}")
        # designmap references must resolve
        dm = zf.read("designmap.xml").decode("utf-8")
        root = ET.fromstring(dm)
        for el in root.iter():
            src = el.attrib.get("src")
            if src and src not in names:
                issues.append(f"designmap references missing part: {src}")
        # spline items must carry PathGeometry — a GeometricBounds
        # attribute is silently ignored by InDesign and yields invisible
        # frames ("opens fine but blank pages")
        for name in names:
            if not name.startswith("Spreads/"):
                continue
            spread = ET.fromstring(zf.read(name))
            for frame in spread.iter("TextFrame"):
                if "GeometricBounds" in frame.attrib:
                    issues.append(f"{name}: TextFrame {frame.get('Self')} uses "
                                  "GeometricBounds (ignored by InDesign; use PathGeometry)")
                if frame.find("./Properties/PathGeometry") is None:
                    issues.append(f"{name}: TextFrame {frame.get('Self')} has no PathGeometry")
    return issues
