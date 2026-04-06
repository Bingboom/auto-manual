from __future__ import annotations

import csv
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


def latest_report_prefix(report_root: Path) -> str:
    candidates = sorted(report_root.glob("*_index.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No diff-report index html found under {report_root}")
    return candidates[0].name[: -len("_index.html")]


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def rewrite_report_html_for_preview(html_text: str, *, mapping: dict[str, str]) -> str:
    rewritten = html_text
    for src_name, dst_name in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        rewritten = rewritten.replace(src_name, dst_name)
    return rewritten


def copy_report_set(report_root: Path, prefix: str, changes_dir: Path, *, relative_dir: str) -> dict[str, str]:
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
        html_text = src.read_text(encoding="utf-8")
        rewritten = rewrite_report_html_for_preview(html_text, mapping=mapping)
        (changes_dir / dst_name).write_text(rewritten, encoding="utf-8")
        copied[dst_name] = f"{relative_dir}/{dst_name}"
    if missing_sources:
        joined = ", ".join(sorted(missing_sources))
        raise FileNotFoundError(f"Review preview requires diff-report HTML outputs under {report_root}: {joined}")
    return copied


def copy_report_csvs(report_root: Path, prefix: str, downloads_dir: Path, *, relative_dir: str) -> dict[str, str]:
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
        copied[dst_name] = f"{relative_dir}/{dst_name}"
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


def build_change_workbook(downloads_dir: Path, csv_files: dict[str, str], *, relative_path: str) -> str | None:
    sheet_mapping = [
        ("changes-summary.csv", "Summary"),
        ("changes-pages.csv", "Pages"),
        ("changes-fields.csv", "Fields"),
        ("changes-files.csv", "Files"),
    ]
    sheets: list[tuple[str, list[list[str]]]] = []
    for file_name, sheet_name in sheet_mapping:
        if file_name not in csv_files:
            continue
        csv_path = downloads_dir / file_name
        if csv_path.exists():
            sheets.append((sheet_name, read_csv_rows(csv_path)))
    if not sheets:
        return None

    workbook_path = downloads_dir / "change-report.xlsx"
    build_workbook_xlsx(workbook_path, sheets)
    return relative_path


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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def read_json_if_exists(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}
