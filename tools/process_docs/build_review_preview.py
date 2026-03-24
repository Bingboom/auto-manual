from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_CHANGE_REPORT_FILES = (
    "report-index.html",
    "report-summary.html",
    "report-fields.html",
    "report-pages.html",
    "report-files.html",
)
REQUIRED_DOWNLOAD_CSVS = (
    "changes-summary.csv",
    "changes-pages.csv",
    "changes-fields.csv",
    "changes-files.csv",
)
REQUIRED_PREVIEW_FILES = (
    "index.html",
    "manual/index.html",
    "changes/index.html",
    "generated/meta.json",
    "generated/changes.json",
)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Build a review-first HTML preview package for Vercel or local sharing."
    )
    ap.add_argument("--config", default="config.yaml", help="Config YAML path, relative to repo root by default.")
    ap.add_argument("--model", required=True, help="Target model, for example JE-1000F.")
    ap.add_argument("--region", required=True, help="Target region, for example US.")
    ap.add_argument(
        "--source",
        default="review",
        choices=("auto", "runtime", "review"),
        help="Bundle source passed to build.py html. Default keeps the preview tied to review content.",
    )
    ap.add_argument(
        "--tracked-root",
        default=None,
        help="Tracked subtree for diff-report. Defaults to docs/_review/<model>/<region>.",
    )
    ap.add_argument("--from-ref", default="HEAD~1", help="Git from ref for diff-report.")
    ap.add_argument("--to-ref", default="HEAD", help="Git to ref for diff-report.")
    ap.add_argument(
        "--output-dir",
        default="site/review-preview/dist",
        help="Static site output directory, relative to repo root by default.",
    )
    ap.add_argument(
        "--clean-build",
        action="store_true",
        help="Allow build.py exports to clean the current target output first.",
    )
    ap.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip build.py html and reuse an existing HTML bundle.",
    )
    ap.add_argument(
        "--skip-diff",
        action="store_true",
        help="Skip diff-report generation and reuse the latest report set.",
    )
    ap.add_argument(
        "--skip-word",
        action="store_true",
        help="Skip the optional Word export step.",
    )
    return ap.parse_args()


def resolve_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def capture(cmd: list[str]) -> str:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def git_value(env_name: str, fallback_cmd: list[str]) -> str:
    value = os.environ.get(env_name, "").strip()
    if value:
        return value
    return capture(fallback_cmd)


def collect_changed_files(from_ref: str, to_ref: str) -> list[str]:
    raw = capture(["git", "diff", "--name-only", "--diff-filter=ACMRT", from_ref, to_ref])
    return [line.strip() for line in raw.splitlines() if line.strip()]


def classify_changes(changed_files: list[str], model: str, region: str) -> list[dict[str, object]]:
    review_prefix = f"docs/_review/{model}/{region}/"
    groups = [
        ("Review Bundle", lambda p: p.startswith(review_prefix)),
        ("Shared Templates", lambda p: p.startswith("docs/templates/")),
        ("Structured Data", lambda p: p.startswith("data/phase1/")),
        ("Automation And Build", lambda p: p == "build.py" or p.startswith("tools/") or p.startswith(".github/workflows/")),
        ("Maintainer Docs", lambda p: p == "README.md" or p.startswith("code-as-doc/") or p.startswith("user-guide/")),
    ]
    areas: list[dict[str, object]] = []
    assigned: set[str] = set()
    for name, matcher in groups:
        files = [path for path in changed_files if matcher(path)]
        if files:
            assigned.update(files)
            areas.append({"name": name, "files": files})
    other = [path for path in changed_files if path not in assigned]
    if other:
        areas.append({"name": "Other", "files": other})
    return areas


def latest_report_prefix(report_root: Path) -> str:
    candidates = sorted(report_root.glob("*_index.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No diff-report index html found under {report_root}")
    return candidates[0].name[: -len("_index.html")]


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def copy_report_set(report_root: Path, prefix: str, changes_dir: Path) -> dict[str, str]:
    mapping = {
        f"{prefix}_index.html": "report-index.html",
        f"{prefix}.html": "report-summary.html",
        f"{prefix}_fields.html": "report-fields.html",
        f"{prefix}_pages.html": "report-pages.html",
        f"{prefix}_files.html": "report-files.html",
    }
    copied: dict[str, str] = {}
    changes_dir.mkdir(parents=True, exist_ok=True)
    missing_sources: list[str] = []
    for src_name, dst_name in mapping.items():
        src = report_root / src_name
        if not src.exists():
            missing_sources.append(src_name)
            continue
        shutil.copy2(src, changes_dir / dst_name)
        copied[dst_name] = dst_name
    if missing_sources:
        joined = ", ".join(sorted(missing_sources))
        raise FileNotFoundError(f"Review preview requires diff-report HTML outputs under {report_root}: {joined}")
    return copied


def copy_report_csvs(report_root: Path, prefix: str, downloads_dir: Path) -> dict[str, str]:
    mapping = {
        f"{prefix}.csv": "changes-summary.csv",
        f"{prefix}_pages.csv": "changes-pages.csv",
        f"{prefix}_fields.csv": "changes-fields.csv",
        f"{prefix}_files.csv": "changes-files.csv",
    }
    copied: dict[str, str] = {}
    downloads_dir.mkdir(parents=True, exist_ok=True)
    missing_sources: list[str] = []
    for src_name, dst_name in mapping.items():
        src = report_root / src_name
        if not src.exists():
            missing_sources.append(src_name)
            continue
        shutil.copy2(src, downloads_dir / dst_name)
        copied[dst_name] = f"downloads/{dst_name}"
    if missing_sources:
        joined = ", ".join(sorted(missing_sources))
        raise FileNotFoundError(f"Review preview requires diff-report CSV outputs under {report_root}: {joined}")
    return copied


def locate_latest_docx(word_root: Path) -> Path | None:
    if not word_root.exists():
        return None
    docx_files = [path for path in word_root.rglob("*.docx") if path.is_file()]
    if not docx_files:
        return None
    return max(docx_files, key=lambda path: path.stat().st_mtime)


def build_word_download(
    *,
    args: argparse.Namespace,
    config_path: Path,
    downloads_dir: Path,
) -> str | None:
    if args.skip_word:
        return None

    word_root = ROOT / "docs" / "_build" / args.model / args.region / "word"
    cmd = [
        sys.executable,
        str(ROOT / "build.py"),
        "word",
        "--config",
        str(config_path),
        "--model",
        args.model,
        "--region",
        args.region,
        "--source",
        args.source,
    ]
    if not args.clean_build:
        cmd.append("--no-clean")

    try:
        run(cmd)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("Review preview failed to build the required Word download.") from exc

    latest_docx = locate_latest_docx(word_root)
    if latest_docx is None:
        raise FileNotFoundError(f"Review preview Word export finished but no DOCX was found under {word_root}")

    target = downloads_dir / "review-manual.docx"
    shutil.copy2(latest_docx, target)
    return "downloads/review-manual.docx"


def read_csv_rows(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.reader(handle)]


def xlsx_column_name(index: int) -> str:
    result = ""
    value = index
    while value > 0:
        value, remainder = divmod(value - 1, 26)
        result = chr(65 + remainder) + result
    return result


def make_cell(ref: str, value: str) -> str:
    safe = xml_escape(value)
    if value.startswith(" ") or value.endswith(" ") or "\n" in value:
        return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{safe}</t></is></c>'
    return f'<c r="{ref}" t="inlineStr"><is><t>{safe}</t></is></c>'


def build_sheet_xml(rows: list[list[str]]) -> str:
    xml_rows: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row, start=1):
            ref = f"{xlsx_column_name(column_index)}{row_index}"
            cells.append(make_cell(ref, value))
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        + "".join(xml_rows)
        + "</sheetData></worksheet>"
    )


def build_workbook_xlsx(path: Path, sheets: list[tuple[str, list[list[str]]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook_sheets = []
    workbook_rels = []
    content_type_overrides = []
    app_sheet_names = []

    for index, (sheet_name, _rows) in enumerate(sheets, start=1):
        worksheet_path = f"xl/worksheets/sheet{index}.xml"
        workbook_sheets.append(
            f'<sheet name="{xml_escape(sheet_name)}" sheetId="{index}" r:id="rId{index}"/>'
        )
        workbook_rels.append(
            f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        )
        content_type_overrides.append(
            f'<Override PartName="/{worksheet_path}" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
        app_sheet_names.append(f"<vt:lpstr>{xml_escape(sheet_name)}</vt:lpstr>")

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheets>"
        + "".join(workbook_sheets)
        + "</sheets></workbook>"
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(workbook_rels)
        + '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        + "</Relationships>"
    )
    root_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        + "".join(content_type_overrides)
        + "</Types>"
    )
    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        "</styleSheet>"
    )
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    core_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<dc:title>Review Preview Change Report</dc:title>"
        "<dc:creator>auto-manual</dc:creator>"
        "<cp:lastModifiedBy>auto-manual</cp:lastModifiedBy>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>'
        "</cp:coreProperties>"
    )
    app_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>auto-manual</Application>"
        f"<TitlesOfParts><vt:vector size=\"{len(sheets)}\" baseType=\"lpstr\">{''.join(app_sheet_names)}</vt:vector></TitlesOfParts>"
        f"<HeadingPairs><vt:vector size=\"2\" baseType=\"variant\"><vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>{len(sheets)}</vt:i4></vt:variant></vt:vector></HeadingPairs>"
        "</Properties>"
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("[Content_Types].xml", content_types_xml)
        bundle.writestr("_rels/.rels", root_rels_xml)
        bundle.writestr("docProps/core.xml", core_xml)
        bundle.writestr("docProps/app.xml", app_xml)
        bundle.writestr("xl/workbook.xml", workbook_xml)
        bundle.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        bundle.writestr("xl/styles.xml", styles_xml)
        for index, (_name, rows) in enumerate(sheets, start=1):
            bundle.writestr(f"xl/worksheets/sheet{index}.xml", build_sheet_xml(rows))


def build_change_workbook(downloads_dir: Path, csv_files: dict[str, str]) -> str | None:
    sheet_mapping = [
        ("changes-summary.csv", "Summary"),
        ("changes-pages.csv", "Pages"),
        ("changes-fields.csv", "Fields"),
        ("changes-files.csv", "Files"),
    ]
    sheets: list[tuple[str, list[list[str]]]] = []
    for file_name, sheet_name in sheet_mapping:
        csv_name = csv_files.get(file_name)
        if not csv_name:
            continue
        csv_path = ROOT / csv_name if Path(csv_name).is_absolute() else ROOT / csv_name
        if not csv_path.exists():
            csv_path = downloads_dir / file_name
        if csv_path.exists():
            sheets.append((sheet_name, read_csv_rows(csv_path)))
    if not sheets:
        return None

    workbook_path = downloads_dir / "change-report.xlsx"
    build_workbook_xlsx(workbook_path, sheets)
    return "downloads/change-report.xlsx"


def build_downloads_metadata(
    *,
    word_path: str | None,
    workbook_path: str | None,
    csv_files: dict[str, str],
) -> dict[str, object]:
    return {
        "word_docx": word_path,
        "change_workbook": workbook_path,
        "csv_reports": dict(csv_files),
    }


def assert_preview_output_contract(output_dir: Path, downloads: dict[str, object], *, require_word: bool) -> None:
    missing: list[str] = []

    for relative_path in REQUIRED_PREVIEW_FILES:
        if not (output_dir / relative_path).exists():
            missing.append(relative_path)

    for relative_path in REQUIRED_CHANGE_REPORT_FILES:
        if not (output_dir / "changes" / relative_path).exists():
            missing.append(f"changes/{relative_path}")

    csv_reports = downloads.get("csv_reports")
    if not isinstance(csv_reports, dict):
        missing.extend(f"downloads/{name}" for name in REQUIRED_DOWNLOAD_CSVS)
    else:
        for file_name in REQUIRED_DOWNLOAD_CSVS:
            target = csv_reports.get(file_name)
            if not isinstance(target, str) or not (output_dir / target).exists():
                missing.append(f"downloads/{file_name}")

    workbook_path = downloads.get("change_workbook")
    if not isinstance(workbook_path, str) or not (output_dir / workbook_path).exists():
        missing.append("downloads/change-report.xlsx")

    word_path = downloads.get("word_docx")
    if require_word and (not isinstance(word_path, str) or not (output_dir / word_path).exists()):
        missing.append("downloads/review-manual.docx")

    if missing:
        raise RuntimeError("Review preview output contract is incomplete: " + ", ".join(sorted(set(missing))))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def render_list(items: list[str], empty_text: str) -> str:
    if not items:
        return f"<li>{escape(empty_text)}</li>"
    return "".join(f"<li><code>{escape(item)}</code></li>" for item in items)


def render_link_list(items: list[tuple[str, str]]) -> str:
    if not items:
        return "<li>No downloads available for this review round.</li>"
    return "".join(f'<li><a href="{escape(target)}">{escape(label)}</a></li>' for label, target in items)


def summarize_items(items: list[str], *, limit: int = 5) -> str:
    if not items:
        return "None"
    visible = [str(item) for item in items[:limit]]
    if len(items) > limit:
        visible.append(f"+{len(items) - limit} more")
    return ", ".join(escape(item) for item in visible)


def render_areas(areas: list[dict[str, object]]) -> str:
    if not areas:
        return "<p>No grouped changes were detected.</p>"
    blocks: list[str] = []
    for area in areas:
        files = area.get("files", [])
        if not isinstance(files, list):
            continue
        blocks.append(
            "<section class=\"card\">"
            f"<h3>{escape(str(area['name']))}</h3>"
            "<ul>"
            + "".join(f"<li><code>{escape(str(item))}</code></li>" for item in files)
            + "</ul>"
            "</section>"
        )
    return "".join(blocks)


def page_title(model: str, region: str) -> str:
    return f"{model} / {region} Review Preview"


def base_css() -> str:
    return """
:root {
  --bg: #f5f1e8;
  --panel: #fffdf8;
  --ink: #1f2933;
  --muted: #52606d;
  --line: #d9d1c3;
  --accent: #1f5eff;
  --accent-soft: #e8efff;
  --success: #1f845a;
  --warning: #b54708;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Segoe UI", "Noto Sans", sans-serif;
  background:
    radial-gradient(circle at top right, rgba(31,94,255,0.08), transparent 28%),
    linear-gradient(180deg, #f7f3ea 0%, #efe8db 100%);
  color: var(--ink);
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.shell {
  max-width: 1120px;
  margin: 0 auto;
  padding: 40px 24px 56px;
}
.hero {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 24px;
  padding: 28px;
  box-shadow: 0 16px 40px rgba(31, 41, 51, 0.08);
}
.eyebrow {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
h1 {
  margin: 14px 0 10px;
  font-size: 40px;
  line-height: 1.1;
}
.lede {
  margin: 0;
  color: var(--muted);
  font-size: 18px;
  line-height: 1.7;
}
.banner {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 18px;
  background: #fff8ec;
  border: 1px solid #f3d4a5;
  color: #7a4f04;
  font-size: 14px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 18px;
  margin-top: 22px;
}
.card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 18px 20px;
}
.card h2, .card h3 {
  margin: 0 0 12px;
}
.card ul {
  margin: 0;
  padding-left: 20px;
}
.actions, .downloads {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 22px;
}
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 180px;
  padding: 12px 18px;
  border-radius: 999px;
  font-weight: 700;
  border: 1px solid var(--accent);
}
.button.primary {
  background: var(--accent);
  color: white;
}
.button.secondary {
  background: white;
  color: var(--accent);
}
.button.download {
  background: #12335f;
  border-color: #12335f;
  color: white;
}
.meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 24px;
}
.meta-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255,255,255,0.72);
  border: 1px solid var(--line);
}
.label {
  display: block;
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 4px;
}
.foot {
  margin-top: 24px;
  color: var(--muted);
  font-size: 14px;
}
.state {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 18px;
  padding: 10px 12px;
  border-radius: 999px;
  background: #effaf4;
  color: var(--success);
  font-weight: 700;
}
.state.warning {
  background: #fff4e5;
  color: var(--warning);
}
code {
  font-family: "Cascadia Code", "Consolas", monospace;
  font-size: 0.95em;
}
"""


def build_download_links(downloads: dict[str, object], *, prefix: str) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    word_path = downloads.get("word_docx")
    workbook_path = downloads.get("change_workbook")
    csv_reports = downloads.get("csv_reports", {})
    if isinstance(word_path, str):
        links.append(("Download Word", f"{prefix}{word_path}"))
    if isinstance(workbook_path, str):
        links.append(("Download Change Workbook", f"{prefix}{workbook_path}"))
    if isinstance(csv_reports, dict):
        for file_name, label in (
            ("changes-summary.csv", "Download Summary CSV"),
            ("changes-pages.csv", "Download Page CSV"),
            ("changes-fields.csv", "Download Field CSV"),
            ("changes-files.csv", "Download File CSV"),
        ):
            target = csv_reports.get(file_name)
            if isinstance(target, str):
                links.append((label, f"{prefix}{target}"))
    return links


def render_index_html(meta: dict[str, object], changes: dict[str, object]) -> str:
    top_pages = changes.get("review_pages", [])
    if not isinstance(top_pages, list):
        top_pages = []
    changed_files = changes.get("changed_files", [])
    if not isinstance(changed_files, list):
        changed_files = []
    downloads = changes.get("downloads", {})
    if not isinstance(downloads, dict):
        downloads = {}
    download_links = build_download_links(downloads, prefix="./")
    word_download = next((target for label, target in download_links if label == "Download Word"), None)
    workbook_download = next((target for label, target in download_links if label == "Download Change Workbook"), None)
    page_state = "No review page changes detected in the selected diff range."
    if top_pages:
        page_state = f"{len(top_pages)} review page(s) changed in this round."
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(str(meta['title']))}</title>
  <style>{base_css()}</style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">Review Preview</span>
      <h1>{escape(str(meta['title']))}</h1>
      <p class="lede">Open the current review HTML, download the Word handoff, and use the change package to brief design on this round.</p>
      <div class="actions">
        <a class="button primary" href="./manual/index.html">Open Review HTML</a>
        {f'<a class="button download" href="{escape(word_download)}">Download Word</a>' if word_download else ''}
        {f'<a class="button download" href="{escape(workbook_download)}">Download Change Workbook</a>' if workbook_download else ''}
      </div>
      <p class="foot">Need the detailed diff? <a href="./changes/index.html">Open Change Report</a>.</p>
    </section>

    <section class="grid">
      <article class="card">
        <h2>What Changed</h2>
        <ul>
          <li><strong>Model:</strong> {escape(str(meta['model']))} / {escape(str(meta['region']))}</li>
          <li><strong>Source:</strong> {escape(str(meta['source']))}</li>
          <li><strong>Branch:</strong> <code>{escape(str(meta['branch']))}</code></li>
          <li><strong>Commit:</strong> <code>{escape(str(meta['commit_sha_short']))}</code></li>
          <li><strong>Generated:</strong> {escape(str(meta['generated_at']))}</li>
          <li><strong>Review pages:</strong> {escape(page_state)}</li>
          <li><strong>Touched pages:</strong> {summarize_items([str(item) for item in top_pages])}</li>
          <li><strong>Changed files:</strong> {summarize_items([str(item) for item in changed_files], limit=6)}</li>
        </ul>
        <p class="foot">Use the Excel workbook for an offline handoff, or open the change report for the full page and field diff.</p>
      </article>
    </section>
  </main>
</body>
</html>
"""


def render_changes_html(meta: dict[str, object], changes: dict[str, object]) -> str:
    areas = changes.get("areas", [])
    if not isinstance(areas, list):
        areas = []
    review_pages = changes.get("review_pages", [])
    if not isinstance(review_pages, list):
        review_pages = []
    reports = changes.get("report_files", {})
    if not isinstance(reports, dict):
        reports = {}
    downloads = changes.get("downloads", {})
    if not isinstance(downloads, dict):
        downloads = {}
    report_links = []
    for label, target in (
        ("Report overview", reports.get("report-index.html")),
        ("Field diff", reports.get("report-fields.html")),
        ("Page diff", reports.get("report-pages.html")),
        ("File diff", reports.get("report-files.html")),
        ("Raw summary", reports.get("report-summary.html")),
    ):
        if target:
            report_links.append((label, f"./{str(target)}"))
    download_links = build_download_links(downloads, prefix="../")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(str(meta['title']))} - Changes</title>
  <style>{base_css()}</style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">Change Report</span>
      <h1>{escape(str(meta['title']))}</h1>
      <p class="lede">Use this page to brief design on what changed in the current review round before they open the rendered manual or download a change handoff package.</p>
      <div class="actions">
        <a class="button primary" href="../manual/index.html">Open Review HTML</a>
        <a class="button secondary" href="../index.html">Back To Summary</a>
      </div>
      <div class="downloads">
        {''.join(f'<a class="button download" href="{escape(target)}">{escape(label)}</a>' for label, target in download_links[:2])}
      </div>
    </section>

    <section class="grid">
      <article class="card">
        <h2>Diff Links</h2>
        <ul>{render_link_list(report_links)}</ul>
      </article>
      <article class="card">
        <h2>Downloadables</h2>
        <ul>{render_link_list(download_links)}</ul>
      </article>
    </section>

    <section class="grid">
      <article class="card">
        <h2>Review Pages Touched</h2>
        <ul>{render_list([str(item) for item in review_pages], "No review pages changed in the selected diff range.")}</ul>
      </article>
      <article class="card">
        <h2>Review Context</h2>
        <p>Open <strong>Field diff</strong> for text or value deltas and <strong>Page diff</strong> for page-level impact. Use the Excel workbook for a single-file handoff.</p>
      </article>
    </section>

    <section class="grid">
      {render_areas([item for item in areas if isinstance(item, dict)])}
    </section>
  </main>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    config_path = resolve_path(args.config)
    tracked_root = resolve_path(args.tracked_root) if args.tracked_root else ROOT / "docs" / "_review" / args.model / args.region
    tracked_root = tracked_root.resolve()
    output_dir = resolve_path(args.output_dir)
    html_root = ROOT / "docs" / "_build" / args.model / args.region / "html"
    report_root = ROOT / "reports" / "version_tracking" / args.model / args.region

    if args.source == "review" and not tracked_root.exists():
        raise FileNotFoundError(f"Review root not found: {tracked_root}")

    if not args.skip_build:
        cmd = [
            sys.executable,
            str(ROOT / "build.py"),
            "html",
            "--config",
            str(config_path),
            "--model",
            args.model,
            "--region",
            args.region,
            "--source",
            args.source,
        ]
        if not args.clean_build:
            cmd.append("--no-clean")
        run(cmd)

    if not html_root.exists():
        raise FileNotFoundError(f"HTML output not found: {html_root}")

    if not args.skip_diff:
        cmd = [
            sys.executable,
            str(ROOT / "build.py"),
            "diff-report",
            "--config",
            str(config_path),
            "--model",
            args.model,
            "--region",
            args.region,
            "--tracked-root",
            str(tracked_root),
            "--from-ref",
            args.from_ref,
            "--to-ref",
            args.to_ref,
        ]
        run(cmd)

    prefix = latest_report_prefix(report_root)
    changed_files = collect_changed_files(args.from_ref, args.to_ref)
    review_pages = [
        path.removeprefix(f"docs/_review/{args.model}/{args.region}/")
        for path in changed_files
        if path.startswith(f"docs/_review/{args.model}/{args.region}/page/")
        or path.startswith(f"docs/_review/{args.model}/{args.region}/generated/")
    ]
    areas = classify_changes(changed_files, args.model, args.region)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    manual_dir = output_dir / "manual"
    changes_dir = output_dir / "changes"
    downloads_dir = output_dir / "downloads"
    generated_dir = output_dir / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    copy_tree(html_root, manual_dir)
    report_files = copy_report_set(report_root, prefix, changes_dir)
    csv_files = copy_report_csvs(report_root, prefix, downloads_dir)
    workbook_path = build_change_workbook(downloads_dir, csv_files)
    word_path = build_word_download(args=args, config_path=config_path, downloads_dir=downloads_dir)

    commit_sha = git_value("VERCEL_GIT_COMMIT_SHA", ["git", "rev-parse", "HEAD"])
    commit_message = git_value("VERCEL_GIT_COMMIT_MESSAGE", ["git", "log", "-1", "--pretty=%s"])
    branch = git_value("VERCEL_GIT_COMMIT_REF", ["git", "rev-parse", "--abbrev-ref", "HEAD"])
    author = git_value("VERCEL_GIT_COMMIT_AUTHOR_NAME", ["git", "log", "-1", "--pretty=%an"])
    pr_id = os.environ.get("VERCEL_GIT_PULL_REQUEST_ID", "").strip()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    if workbook_path is None:
        raise RuntimeError("Review preview failed to build the required change-report workbook.")

    downloads = build_downloads_metadata(
        word_path=word_path,
        workbook_path=workbook_path,
        csv_files=csv_files,
    )
    meta = {
        "title": page_title(args.model, args.region),
        "model": args.model,
        "region": args.region,
        "source": args.source,
        "config": str(config_path.relative_to(ROOT)),
        "tracked_root": str(tracked_root.relative_to(ROOT)),
        "branch": branch,
        "commit_sha": commit_sha,
        "commit_sha_short": commit_sha[:7],
        "commit_message": commit_message,
        "author": author,
        "pr_id": pr_id,
        "generated_at": generated_at,
        "vercel_env": os.environ.get("VERCEL_ENV", "").strip(),
        "vercel_url": os.environ.get("VERCEL_URL", "").strip(),
        "downloads": downloads,
    }
    changes = {
        "from_ref": args.from_ref,
        "to_ref": args.to_ref,
        "changed_files": changed_files,
        "review_pages": review_pages,
        "areas": areas,
        "report_prefix": prefix,
        "report_files": report_files,
        "downloads": downloads,
    }

    write_json(generated_dir / "meta.json", meta)
    write_json(generated_dir / "changes.json", changes)
    (output_dir / "index.html").write_text(render_index_html(meta, changes), encoding="utf-8")
    (changes_dir / "index.html").write_text(render_changes_html(meta, changes), encoding="utf-8")
    assert_preview_output_contract(output_dir, downloads, require_word=not args.skip_word)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
