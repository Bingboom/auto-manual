"""Delivery packaging for the publish IDML handoff.

Turns the exporter's outputs (production IDML + flow outputs + handoff
reports) into one self-contained zip a designer can open offline. The
production IDML links images by absolute build-machine ``file://`` URIs
(see ``primitives.image_cell_content``) — dead the moment the build
worktree is gone. This module post-processes the built IDML: it collects
every linked image into a ``Links/`` folder beside the document and
rewrites each ``LinkResourceURI`` to ``file:Links/<name>``; InDesign also
searches the document folder and its ``Links/`` subfolder by filename
when a link is missing, so either path resolves.

Deliberately a post-process in a new module: ``tools/export_idml.py`` and
``tools/idml/primitives.py`` sit at their guardrail caps, and leaving the
directly-exported IDML byte-identical keeps the golden tests green — all
delivery-specific behavior lives (and is tested) here.
"""
from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse
from xml.sax.saxutils import escape, unescape

from .check import check_idml

_LINK_URI_RE = re.compile(r'LinkResourceURI="([^"]*)"')
_ATTR_ENTITIES = {'"': "&quot;"}
_UNESCAPE_ENTITIES = {"&quot;": '"'}
_FONT_EXTENSIONS = {".otf", ".ttf", ".ttc"}

# The fonts the IDML styles reference (styles.fonts_xml / primitives
# symbol fallbacks). None are redistributable from this repo: Gilroy is a
# commercial license, the others are system fonts.
_FONT_ROWS = (
    ("Gilroy", "Gilroy-Regular / Gilroy-Medium / Gilroy-SemiBold / Gilroy-Bold", "commercial (Radomir Tinkov)"),
    ("Arial Unicode MS", "ArialUnicodeMS", "system font (symbol fallback)"),
    ("Apple Symbols", "AppleSymbols", "system font (symbol fallback)"),
    ("Apple SD Gothic Neo", "AppleSDGothicNeo-Regular", "macOS system font (circled-number fallback)"),
)


@dataclass(frozen=True)
class DeliveryOutputs:
    zip_path: Path
    idml_arcname: str
    links: dict[str, str]
    missing_links: list[str]
    notes: list[str]


def _uri_to_path(uri: str) -> Path | None:
    parsed = urlparse(uri)
    if parsed.scheme != "file" or not parsed.path:
        return None
    return Path(unquote(parsed.path))


def _collect_link_uris(idml_path: Path) -> list[str]:
    """Unique LinkResourceURI values in first-seen part order."""
    if not zipfile.is_zipfile(idml_path):
        return []
    seen: list[str] = []
    with zipfile.ZipFile(idml_path) as zf:
        for name in zf.namelist():
            if not name.endswith(".xml"):
                continue
            text = zf.read(name).decode("utf-8")
            for match in _LINK_URI_RE.finditer(text):
                uri = unescape(match.group(1), _UNESCAPE_ENTITIES)
                if uri not in seen:
                    seen.append(uri)
    return seen


def _assign_link_names(uris: list[str]) -> tuple[dict[str, tuple[Path, str]], list[str]]:
    """Map resolvable URI -> (source path, unique Links/ basename)."""
    assigned: dict[str, tuple[Path, str]] = {}
    taken: set[str] = set()
    missing: list[str] = []
    for uri in uris:
        source = _uri_to_path(uri)
        if source is None or not source.is_file():
            missing.append(uri)
            continue
        candidate = source.name
        counter = 2
        while candidate in taken:
            candidate = f"{source.stem}__{counter}{source.suffix}"
            counter += 1
        taken.add(candidate)
        assigned[uri] = (source, candidate)
    return assigned, missing


def _rewrite_part(text: str, assigned: dict[str, tuple[Path, str]]) -> str:
    def replace(match: re.Match[str]) -> str:
        uri = unescape(match.group(1), _UNESCAPE_ENTITIES)
        entry = assigned.get(uri)
        if entry is None:
            return match.group(0)
        return f'LinkResourceURI="{escape(f"file:Links/{entry[1]}", _ATTR_ENTITIES)}"'

    return _LINK_URI_RE.sub(replace, text)


def _rewrite_idml(source: Path, assigned: dict[str, tuple[Path, str]], dest: Path) -> None:
    """Copy the IDML with rewritten URIs, preserving the zip contract
    (mimetype stays the first part, stored uncompressed)."""
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(dest, "w") as out:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "mimetype":
                out.writestr(zipfile.ZipInfo("mimetype"), data, compress_type=zipfile.ZIP_STORED)
                continue
            if info.filename.endswith(".xml"):
                data = _rewrite_part(data.decode("utf-8"), assigned).encode("utf-8")
            out.writestr(info.filename, data, compress_type=zipfile.ZIP_DEFLATED)


def _fonts_manifest(fonts_included: bool) -> str:
    lines = [
        "# Fonts Manifest",
        "",
        "Fonts referenced by the IDML styles:",
        "",
        "| Family | PostScript names | Licensing |",
        "|---|---|---|",
    ]
    lines.extend(f"| {family} | {names} | {license_} |" for family, names, license_ in _FONT_ROWS)
    lines.append("")
    if fonts_included:
        lines.append("Font files are included under `Document fonts/` (provisioned by the build operator; verify the embedding license covers your use).")
    else:
        lines.append("No font files are included in this package — install the fonts above (licensed) before opening the IDML, or InDesign will substitute them.")
    return "\n".join(lines) + "\n"


def _export_notes(notes: Iterable[str], missing: list[str]) -> str:
    lines = ["# Export Notes", ""]
    body = [f"- {note}" for note in notes]
    if missing:
        body.append(f"- {len(missing)} linked asset(s) could not be found at package time; their URIs were left untouched:")
        body.extend(f"  - `{uri}`" for uri in missing)
    if not body:
        body.append("- No warnings were reported for this export.")
    return "\n".join(lines + body) + "\n"


def _versioned_source_trace(handoff_root: Path, version: str | None) -> str | None:
    trace_path = handoff_root / "production" / "source_trace.json"
    if not trace_path.is_file():
        return None
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    if version:
        trace["version"] = version
    return json.dumps(trace, ensure_ascii=False, indent=2) + "\n"


def build_delivery_package(
    *,
    production_idml: Path,
    handoff_root: Path,
    out_zip: Path,
    idml_arcname: str | None = None,
    version: str | None = None,
    reference_pdf: Path | None = None,
    fonts_dir: Path | None = None,
    extra_notes: Iterable[str] = (),
) -> DeliveryOutputs:
    """Assemble the designer handoff zip for one publish target.

    ``handoff_root`` is the exporter's ``--idml-mode both`` output
    directory (``.../idml``) holding ``flow/``, the handoff reports, and
    ``production/source_trace.json``. Missing optional pieces degrade to
    notes instead of failing the package.
    """
    arcname = idml_arcname or production_idml.name
    flow_dir = handoff_root / "flow"
    flow_idml = flow_dir / "manual.flow.idml"
    idml_sources: list[tuple[Path, str]] = [(production_idml, arcname)]
    # Flow IDML used to be a text-only artifact, so older fixture/handoff
    # trees may contain a non-IDML placeholder.  Process a real flow package
    # when present and leave legacy placeholders untouched.
    flow_is_idml = flow_idml.is_file() and zipfile.is_zipfile(flow_idml)
    if flow_is_idml:
        idml_sources.append((flow_idml, "flow/manual.flow.idml"))
    uris: list[str] = []
    for source, _arcname in idml_sources:
        for uri in _collect_link_uris(source):
            if uri not in uris:
                uris.append(uri)
    assigned, missing = _assign_link_names(uris)

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    rewritten_paths: dict[str, Path] = {}
    for index, (source, target_arcname) in enumerate(idml_sources):
        rewritten = out_zip.parent / f".idml_{index}.rewrite.tmp"
        _rewrite_idml(source, assigned, rewritten)
        rewritten_paths[target_arcname] = rewritten
    try:
        for target_arcname, rewritten in rewritten_paths.items():
            issues = check_idml(rewritten)
            if issues:
                raise RuntimeError(
                    f"Rewritten IDML {target_arcname} failed self-check: "
                    + "; ".join(issues)
                )

        notes = list(extra_notes)
        notes.append(f"Collected {len(assigned)} linked asset(s) into Links/.")
        fonts: list[Path] = []
        if fonts_dir is not None and fonts_dir.is_dir():
            fonts = sorted(p for p in fonts_dir.iterdir() if p.suffix.lower() in _FONT_EXTENSIONS)
        if fonts:
            notes.append(f"Included {len(fonts)} font file(s) under Document fonts/.")
        else:
            notes.append("No font files provisioned; see fonts_manifest.md.")
        if missing:
            notes.append(f"{len(missing)} linked asset(s) missing at package time (see export_notes.md).")

        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(rewritten_paths[arcname], arcname)
            for source, link_name in assigned.values():
                zf.write(source, f"Links/{link_name}")
            if flow_dir.is_dir():
                for path in sorted(flow_dir.iterdir()):
                    if path.is_file() and (path != flow_idml or not flow_is_idml):
                        zf.write(path, f"flow/{path.name}")
                if flow_is_idml:
                    zf.write(
                        rewritten_paths["flow/manual.flow.idml"],
                        "flow/manual.flow.idml",
                    )
            for report in ("designer_checklist.md", "layout_feedback.md", "missing_assets_report.md"):
                report_path = handoff_root / report
                if report_path.is_file():
                    zf.write(report_path, report)
            trace = _versioned_source_trace(handoff_root, version)
            if trace is not None:
                zf.writestr("source_trace.json", trace)
            if reference_pdf is not None and reference_pdf.is_file():
                zf.write(reference_pdf, f"reference/{reference_pdf.name}")
            for font in fonts:
                zf.write(font, f"Document fonts/{font.name}")
            zf.writestr("fonts_manifest.md", _fonts_manifest(bool(fonts)))
            zf.writestr("export_notes.md", _export_notes(notes, missing))
    finally:
        for rewritten in rewritten_paths.values():
            rewritten.unlink(missing_ok=True)

    return DeliveryOutputs(
        zip_path=out_zip,
        idml_arcname=arcname,
        links={uri: str(source) for uri, (source, _) in assigned.items()},
        missing_links=missing,
        notes=notes,
    )
