from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=2)

from tools.build_docs import load_config
from tools.review_support import review_content_exists


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
    "generated/workspace.json",
)
FAMILY_ORDER = ("US", "JP", "CN")
FAMILY_DEFAULT_CONFIGS = {
    "US": "config.us.yaml",
    "JP": "config.ja.yaml",
    "CN": "config.zh.yaml",
}
LANGUAGE_LABELS = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "ja": "Japanese",
    "zh": "Chinese",
}
_MANUAL_SWITCHER_BLOCK_RE = re.compile(
    r"<!-- HB_MANUAL_SWITCHER_START -->.*?<!-- HB_MANUAL_SWITCHER_END -->\s*",
    re.DOTALL,
)


@dataclass(frozen=True)
class WorkspaceTarget:
    model: str
    family: str
    language: str
    config: str
    include_lang_in_output_path: bool

    @property
    def label(self) -> str:
        return f"{self.model}/{self.family}/{self.language}"

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.model, self.family, self.language)


@dataclass(frozen=True)
class WorkspaceTargetTemplate:
    family: str
    language: str
    config: str
    include_lang_in_output_path: bool


WORKSPACE_TARGET_CONFIGS: tuple[str, ...] = (
    "config.us-en.yaml",
    "config.us-es.yaml",
    "config.us-fr.yaml",
    "config.ja.yaml",
    "config.zh.yaml",
)
ReviewAvailability = set[tuple[str, str, str | None]]


def _load_workspace_target_template(config_name: str) -> WorkspaceTargetTemplate:
    config_path = (ROOT / config_name).resolve()
    cfg = load_config(config_path)
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    family = str(build_cfg.get("default_region") or "").strip().upper()
    if not family:
        raise RuntimeError(f"Review preview target config is missing build.default_region: {config_name}")
    raw_languages = build_cfg.get("languages")
    if not isinstance(raw_languages, list) or len(raw_languages) != 1:
        raise RuntimeError(
            f"Review preview target config must declare exactly one build language: {config_name}"
        )
    return WorkspaceTargetTemplate(
        family=family,
        language=str(raw_languages[0]).strip().lower(),
        config=config_name,
        include_lang_in_output_path=bool(build_cfg.get("include_lang_in_output_path", False)),
    )


def _load_workspace_target_templates() -> tuple[WorkspaceTargetTemplate, ...]:
    return tuple(_load_workspace_target_template(config_name) for config_name in WORKSPACE_TARGET_CONFIGS)


WORKSPACE_TARGET_TEMPLATES: tuple[WorkspaceTargetTemplate, ...] = _load_workspace_target_templates()


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Build the review handoff workspace package for Vercel or local sharing."
    )
    ap.add_argument(
        "--config",
        default=None,
        help="Primary family config YAML path. Defaults to the shared family config for --region.",
    )
    ap.add_argument("--model", required=True, help="Target model, for example JE-1000F.")
    ap.add_argument("--region", required=True, help="Preferred default family, for example US.")
    ap.add_argument(
        "--source",
        default="review",
        choices=("auto", "runtime", "review"),
        help="Bundle source passed to build.py html/word. Default keeps the workspace tied to review content.",
    )
    ap.add_argument(
        "--tracked-root",
        default=None,
        help="Tracked subtree for diff-report on the preferred family. Defaults to docs/_review/<model>/<region>.",
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
        help="Allow the first export per family to clean its target output first.",
    )
    ap.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip build.py html exports and reuse existing HTML bundles.",
    )
    ap.add_argument(
        "--skip-diff",
        action="store_true",
        help="Skip diff-report generation and reuse the latest report set for each family.",
    )
    ap.add_argument(
        "--skip-word",
        action="store_true",
        help="Skip the optional Word export step.",
    )
    ap.add_argument(
        "--all-review-models",
        action="store_true",
        help="Include every existing docs/_review/<model>/ target in the workspace, plus the requested default target.",
    )
    return ap.parse_args()


def resolve_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def default_family_config_for_region(region: str) -> str:
    config_name = FAMILY_DEFAULT_CONFIGS.get((region or "").strip().upper())
    if config_name is None:
        raise RuntimeError(
            "Review preview requires --config when --region is outside the supported family defaults (US, JP, CN)."
        )
    return config_name


def resolved_primary_config_path(args: argparse.Namespace) -> Path:
    raw_config = getattr(args, "config", None)
    if isinstance(raw_config, str) and raw_config.strip():
        return resolve_path(raw_config)
    return resolve_path(default_family_config_for_region(str(getattr(args, "region", ""))))


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
        ("Structured Data", lambda p: p.startswith("data/phase1/") or p.startswith("data/phase2/")),
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


def review_pages_for_family(changed_files: list[str], model: str, family: str) -> list[str]:
    prefix = f"docs/_review/{model}/{family}/"
    return [
        path.removeprefix(prefix)
        for path in changed_files
        if path.startswith(f"{prefix}page/") or path.startswith(f"{prefix}generated/")
    ]


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


def display_text(value: object, fallback: str = "Not available") -> str:
    text = str(value or "").strip()
    return text or fallback


def format_generated_at(value: str) -> str:
    text = value.strip()
    if not text:
        return "Not available"
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def preview_language_label(code: str) -> str:
    token = code.strip().lower()
    if not token:
        return "Not available"
    return LANGUAGE_LABELS.get(token, token.upper())


def derive_product_name(manual_title: str, fallback: str) -> str:
    text = manual_title.strip()
    if not text:
        return fallback
    for suffix in (
        " User Manual",
        " Manual de usuario",
        " Manuel d'utilisation",
        " Benutzerhandbuch",
        " 取扱説明書",
        " Manual",
    ):
        if text.endswith(suffix):
            candidate = text[: -len(suffix)].strip()
            if candidate:
                return candidate
    return text


def path_for_display(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def workspace_title(model: str) -> str:
    return f"{model} Review Preview"


def family_change_title(model: str, family: str) -> str:
    return f"{model} {family} Family Change Report"


def render_list(items: list[str], empty_text: str) -> str:
    if not items:
        return f"<li>{escape(empty_text)}</li>"
    return "".join(f"<li><code>{escape(item)}</code></li>" for item in items)


def render_link_list(items: list[tuple[str, str]]) -> str:
    if not items:
        return "<li>No downloads available for this review round.</li>"
    return "".join(f'<li><a href="{escape(target)}">{escape(label)}</a></li>' for label, target in items)


def render_areas(areas: list[dict[str, object]]) -> str:
    if not areas:
        return "<article class=\"card\"><h2>Change Areas</h2><p>No grouped changes were detected.</p></article>"
    blocks: list[str] = []
    for area in areas:
        files = area.get("files", [])
        if not isinstance(files, list):
            continue
        blocks.append(
            "<article class=\"card\">"
            f"<h2>{escape(str(area['name']))}</h2>"
            "<ul>"
            + "".join(f"<li><code>{escape(str(item))}</code></li>" for item in files)
            + "</ul>"
            "</article>"
        )
    return "".join(blocks)


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


def workspace_css() -> str:
    return """
:root {
  --bg: #f4efe4;
  --panel: rgba(255, 252, 246, 0.96);
  --ink: #172b4d;
  --muted: #5b6777;
  --line: #d9cfbf;
  --accent: #1f5eff;
  --accent-dark: #12335f;
  --accent-soft: #eaf0ff;
  --chip: #f4f7ff;
  --chip-line: #d7e2ff;
  --shadow: 0 22px 48px rgba(23, 43, 77, 0.10);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Aptos", "Segoe UI", "Noto Sans", sans-serif;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, rgba(31, 94, 255, 0.10), transparent 30%),
    radial-gradient(circle at top right, rgba(18, 51, 95, 0.08), transparent 26%),
    linear-gradient(180deg, #f8f4ea 0%, #eee7db 100%);
}
a {
  color: var(--accent);
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}
.workspace-shell {
  max-width: 1180px;
  margin: 0 auto;
  padding: 40px 24px 56px;
}
.workspace-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 28px;
  padding: 32px;
  box-shadow: var(--shadow);
}
.eyebrow {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.92fr);
  gap: 22px;
  align-items: start;
}
.hero-copy {
  padding-top: 4px;
}
h1 {
  margin: 16px 0 10px;
  font-size: 44px;
  line-height: 1.06;
}
.product-line {
  margin: 0;
  color: var(--accent);
  font-size: 18px;
  font-weight: 800;
}
.lede {
  margin: 18px 0 0;
  color: var(--muted);
  font-size: 17px;
  line-height: 1.7;
  max-width: 700px;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 24px;
}
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 188px;
  padding: 12px 18px;
  border-radius: 999px;
  font-weight: 800;
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
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  color: white;
}
.detail-link {
  margin: 22px 0 0;
  color: var(--muted);
  font-size: 16px;
  min-height: 24px;
}
.identity-card {
  background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(248,243,234,0.98));
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 22px;
}
.label {
  display: block;
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.identity-card h2 {
  margin: 0;
  font-size: 18px;
  line-height: 1.3;
}
.identity-title {
  margin: 10px 0 0;
  color: var(--muted);
  font-size: 15px;
  line-height: 1.55;
}
.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}
.pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: var(--chip);
  border: 1px solid var(--chip-line);
  color: #20438f;
  font-size: 12px;
  font-weight: 800;
}
.switch-group {
  margin-top: 16px;
}
.switch-label {
  display: block;
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.switch-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}
.switch-pill {
  border: 1px solid var(--chip-line);
  background: var(--chip);
  color: #20438f;
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}
.switch-pill.is-active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}
.error-card {
  text-align: center;
}
@media (max-width: 960px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 720px) {
  .workspace-shell {
    padding: 24px 16px 40px;
  }
  .workspace-card {
    padding: 22px;
  }
  h1 {
    font-size: 34px;
  }
  .identity-card h2 {
    font-size: 18px;
  }
  .button {
    width: 100%;
  }
}
"""


def base_css() -> str:
    return """
:root {
  --bg: #f4efe4;
  --panel: rgba(255, 252, 246, 0.96);
  --ink: #172b4d;
  --muted: #5b6777;
  --line: #d9cfbf;
  --accent: #1f5eff;
  --accent-dark: #12335f;
  --accent-soft: #eaf0ff;
  --callout-bg: #fff6e8;
  --callout-line: #efd19d;
  --callout-ink: #7a4b04;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Aptos", "Segoe UI", "Noto Sans", sans-serif;
  color: var(--ink);
  background:
    radial-gradient(circle at top right, rgba(31, 94, 255, 0.10), transparent 28%),
    linear-gradient(180deg, #f8f4ea 0%, #eee7db 100%);
}
a {
  color: var(--accent);
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}
.shell {
  max-width: 1140px;
  margin: 0 auto;
  padding: 40px 24px 56px;
}
.hero,
.card,
.redirect-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 24px;
  padding: 28px;
  box-shadow: 0 18px 42px rgba(23, 43, 77, 0.10);
}
.eyebrow {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
h1 {
  margin: 14px 0 10px;
  font-size: 40px;
  line-height: 1.08;
}
.lede,
.note,
.redirect-copy {
  margin: 0;
  color: var(--muted);
  font-size: 18px;
  line-height: 1.7;
}
.note {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 18px;
  background: var(--callout-bg);
  border: 1px solid var(--callout-line);
  color: var(--callout-ink);
  font-size: 15px;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 24px;
}
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 188px;
  padding: 12px 18px;
  border-radius: 999px;
  font-weight: 800;
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
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  color: white;
}
.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}
.pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: #f4f7ff;
  border: 1px solid #d7e2ff;
  color: #20438f;
  font-size: 12px;
  font-weight: 800;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
  margin-top: 22px;
}
.card h2 {
  margin: 0 0 12px;
  font-size: 24px;
}
.card ul {
  margin: 0;
  padding-left: 20px;
}
.card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}
.redirect-card {
  max-width: 760px;
  margin: 72px auto;
}
code {
  font-family: "Cascadia Code", "Consolas", monospace;
  font-size: 0.95em;
}
@media (max-width: 720px) {
  .shell {
    padding: 24px 16px 40px;
  }
  .hero,
  .card,
  .redirect-card {
    padding: 22px;
  }
  h1 {
    font-size: 32px;
  }
  .button {
    width: 100%;
  }
}
"""


def render_workspace_html(title: str) -> str:
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"  <title>{escape(title)}</title>\n"
        f"  <style>{workspace_css()}</style>\n"
        "</head>\n"
        "<body>\n"
        "  <main class=\"workspace-shell\">\n"
        "    <div id=\"workspace-app\">Loading review preview...</div>\n"
        "  </main>\n"
        "  <script>\n"
        "const app = document.getElementById('workspace-app');\n"
        "function asArray(value) { return Array.isArray(value) ? value : []; }\n"
        "function normalizeToken(value) { return typeof value === 'string' ? value.trim() : ''; }\n"
        "function valueOr(value, fallback = 'Not available') { const text = normalizeToken(value == null ? '' : String(value)); return text || fallback; }\n"
        "function escapeHtml(value) {\n"
        "  return String(value == null ? '' : value).replace(/[&<>\"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;', \"'\": '&#39;' }[char]));\n"
        "}\n"
        "function readQuery() {\n"
        "  const params = new URLSearchParams(window.location.search);\n"
        "  return {\n"
        "    family: normalizeToken(params.get('family')).toUpperCase(),\n"
        "    model: normalizeToken(params.get('model')),\n"
        "    lang: normalizeToken(params.get('lang')).toLowerCase(),\n"
        "  };\n"
        "}\n"
        "function findFamily(workspace, family) {\n"
        "  return asArray(workspace.families).find((item) => normalizeToken(item.family).toUpperCase() === normalizeToken(family).toUpperCase());\n"
        "}\n"
        "function findModel(familyEntry, model) {\n"
        "  return asArray(familyEntry.models).find((item) => normalizeToken(item.model) === normalizeToken(model));\n"
        "}\n"
        "function findLanguage(modelEntry, lang) {\n"
        "  return asArray(modelEntry.languages).find((item) => normalizeToken(item.lang).toLowerCase() === normalizeToken(lang).toLowerCase());\n"
        "}\n"
        "function normalizeSelection(workspace, requested) {\n"
        "  const families = asArray(workspace.families);\n"
        "  if (!families.length) {\n"
        "    throw new Error('No families available in generated/workspace.json.');\n"
        "  }\n"
        "  const defaults = workspace.defaults || {};\n"
        "  const familyEntry = findFamily(workspace, requested.family) || findFamily(workspace, defaults.family) || families[0];\n"
        "  const models = asArray(familyEntry.models);\n"
        "  if (!models.length) {\n"
        "    throw new Error(`No model groups are available for family ${familyEntry.family}.`);\n"
        "  }\n"
        "  const modelEntry = findModel(familyEntry, requested.model) || findModel(familyEntry, defaults.model) || models[0];\n"
        "  const languages = asArray(modelEntry.languages);\n"
        "  if (!languages.length) {\n"
        "    throw new Error(`No languages are available for model ${modelEntry.model}.`);\n"
        "  }\n"
        "  const languageEntry = findLanguage(modelEntry, requested.lang) || findLanguage(modelEntry, defaults.lang) || languages[0];\n"
        "  return {\n"
        "    family: String(familyEntry.family),\n"
        "    model: String(modelEntry.model),\n"
        "    lang: String(languageEntry.lang),\n"
        "    familyEntry,\n"
        "    modelEntry,\n"
        "    languageEntry,\n"
        "  };\n"
        "}\n"
        "function writeUrl(selection, mode) {\n"
        "  const params = new URLSearchParams(window.location.search);\n"
        "  params.set('family', selection.family);\n"
        "  params.set('model', selection.model);\n"
        "  params.set('lang', selection.lang);\n"
        "  const next = `${window.location.pathname}?${params.toString()}`;\n"
        "  const method = mode === 'push' ? 'pushState' : 'replaceState';\n"
        "  window.history[method]({ family: selection.family, model: selection.model, lang: selection.lang }, '', next);\n"
        "}\n"
        "function actionButton(label, href, className, downloadName) {\n"
        "  if (!href) {\n"
        "    return '';\n"
        "  }\n"
        "  const downloadAttr = downloadName ? ` download=\"${escapeHtml(downloadName)}\"` : '';\n"
        "  return `<a class=\"button ${className}\" href=\"${escapeHtml(href)}\"${downloadAttr}>${escapeHtml(label)}</a>`;\n"
        "}\n"
        "function bindEvents(workspace, currentSelection) {\n"
        "  document.querySelectorAll('[data-family-tab]').forEach((button) => {\n"
        "    button.addEventListener('click', () => {\n"
        "      const family = normalizeToken(button.getAttribute('data-family-tab')).toUpperCase();\n"
        "      const familyEntry = findFamily(workspace, family);\n"
        "      if (!familyEntry) {\n"
        "        return;\n"
        "      }\n"
        "      const modelEntry = asArray(familyEntry.models)[0];\n"
        "      const languageEntry = modelEntry && asArray(modelEntry.languages)[0];\n"
        "      if (!modelEntry || !languageEntry) {\n"
        "        return;\n"
        "      }\n"
        "      const selection = normalizeSelection(workspace, { family: familyEntry.family, model: currentSelection.model, lang: currentSelection.lang });\n"
        "      writeUrl(selection, 'push');\n"
        "      render(selection, workspace);\n"
        "    });\n"
        "  });\n"
        "  document.querySelectorAll('[data-model-tab]').forEach((button) => {\n"
        "    button.addEventListener('click', () => {\n"
        "      const model = normalizeToken(button.getAttribute('data-model-tab'));\n"
        "      const selection = normalizeSelection(workspace, { family: currentSelection.family, model, lang: currentSelection.lang });\n"
        "      writeUrl(selection, 'push');\n"
        "      render(selection, workspace);\n"
        "    });\n"
        "  });\n"
        "  document.querySelectorAll('[data-lang-tab]').forEach((button) => {\n"
        "    button.addEventListener('click', () => {\n"
        "      const lang = normalizeToken(button.getAttribute('data-lang-tab')).toLowerCase();\n"
        "      const selection = normalizeSelection(workspace, { family: currentSelection.family, model: currentSelection.model, lang });\n"
        "      writeUrl(selection, 'push');\n"
        "      render(selection, workspace);\n"
        "    });\n"
        "  });\n"
        "}\n"
        "function render(selection, workspace) {\n"
        "  const productName = valueOr(selection.languageEntry.product_name, selection.modelEntry.product_name || selection.model);\n"
        "  const manualTitle = valueOr(selection.languageEntry.manual_title, selection.modelEntry.manual_title || workspace.title);\n"
        "  const familyTabs = asArray(workspace.families).map((familyEntry) => {\n"
        "    const active = familyEntry.family === selection.family;\n"
        "    return `<button type=\"button\" class=\"switch-pill ${active ? 'is-active' : ''}\" data-family-tab=\"${escapeHtml(familyEntry.family)}\">${escapeHtml(familyEntry.family)}</button>`;\n"
        "  }).join('');\n"
        "  const modelTabs = asArray(selection.familyEntry.models).map((modelEntry) => {\n"
        "    const active = modelEntry.model === selection.model;\n"
        "    return `<button type=\"button\" class=\"switch-pill ${active ? 'is-active' : ''}\" data-model-tab=\"${escapeHtml(modelEntry.model)}\">${escapeHtml(modelEntry.model)}</button>`;\n"
        "  }).join('');\n"
        "  const languageTabs = asArray(selection.modelEntry.languages).map((languageEntry) => {\n"
        "    const active = languageEntry.lang === selection.lang;\n"
        "    const label = valueOr(languageEntry.language_label, languageEntry.lang.toUpperCase());\n"
        "    return `<button type=\"button\" class=\"switch-pill ${active ? 'is-active' : ''}\" data-lang-tab=\"${escapeHtml(languageEntry.lang)}\">${escapeHtml(label)}</button>`;\n"
        "  }).join('');\n"
        "  const actions = [\n"
        "    actionButton('Open Review HTML', selection.languageEntry.manual_url, 'primary', ''),\n"
        "    actionButton('Download Word', selection.languageEntry.word_url, 'download', 'review-manual.docx'),\n"
        "    actionButton('Download Change Workbook', selection.modelEntry.change_workbook_url, 'download', 'change-report.xlsx'),\n"
        "  ].join('');\n"
        "  const changeReportLink = selection.modelEntry.change_index_url ? `<a href=\"${escapeHtml(selection.modelEntry.change_index_url)}\">Open Change Report.</a>` : '';\n"
        "  app.innerHTML = `<section class=\"workspace-card\"><div class=\"hero-grid\"><section class=\"hero-copy\"><span class=\"eyebrow\">Review Preview</span><h1>${escapeHtml(selection.model)} Review Preview</h1><p class=\"product-line\">Product Name: ${escapeHtml(productName)}</p><p class=\"lede\">Open the current review HTML, download the Word handoff, and use the change package to brief design on this round.</p><div class=\"actions\">${actions}</div><p class=\"detail-link\">${changeReportLink ? `Need the detailed diff? ${changeReportLink}` : ''}</p></section><aside class=\"identity-card\"><span class=\"label\">Document Identity</span><h2>${escapeHtml(productName)}</h2><p class=\"identity-title\">${escapeHtml(manualTitle)}</p><div class=\"pill-row\"><span class=\"pill\">Model ${escapeHtml(selection.model)}</span><span class=\"pill\">Family ${escapeHtml(selection.family)}</span></div><div class=\"switch-group\"><span class=\"switch-label\">Region</span><div class=\"switch-row\">${familyTabs}</div></div><div class=\"switch-group\"><span class=\"switch-label\">Model</span><div class=\"switch-row\">${modelTabs}</div></div><div class=\"switch-group\"><span class=\"switch-label\">Language</span><div class=\"switch-row\">${languageTabs}</div></div></aside></div></section>`;\n"
        "  document.title = `${selection.model} / ${selection.family} / ${selection.lang.toUpperCase()} Review Preview`;\n"
        "  bindEvents(workspace, selection);\n"
        "}\n"
        "async function boot() {\n"
        "  try {\n"
        "    const response = await fetch('./generated/workspace.json', { cache: 'no-store' });\n"
        "    if (!response.ok) {\n"
        "      throw new Error(`Failed to load generated/workspace.json (${response.status}).`);\n"
        "    }\n"
        "    const workspace = await response.json();\n"
        "    const selection = normalizeSelection(workspace, readQuery());\n"
        "    writeUrl(selection, 'replace');\n"
        "    render(selection, workspace);\n"
        "    window.addEventListener('popstate', () => {\n"
        "      const nextSelection = normalizeSelection(workspace, readQuery());\n"
        "      writeUrl(nextSelection, 'replace');\n"
        "      render(nextSelection, workspace);\n"
        "    });\n"
        "  } catch (error) {\n"
        "    const message = error && error.message ? error.message : 'Unable to load workspace data.';\n"
        "    app.innerHTML = `<section class=\"workspace-card error-card\"><span class=\"eyebrow\">Preview Error</span><h1>Workspace data is not available</h1><p class=\"lede\">${escapeHtml(message)}</p></section>`;\n"
        "  }\n"
        "}\n"
        "boot();\n"
        "  </script>\n"
        "</body>\n"
        "</html>\n"
    )


def render_redirect_html(*, title: str, target: str, heading: str, copy: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url={escape(target)}">
  <title>{escape(title)}</title>
  <style>{base_css()}</style>
</head>
<body>
  <main class="shell">
    <section class="redirect-card">
      <span class="eyebrow">Redirecting</span>
      <h1>{escape(heading)}</h1>
      <p class="redirect-copy">{escape(copy)}</p>
      <div class="actions">
        <a class="button primary" href="{escape(target)}">Open default entry</a>
        <a class="button secondary" href="../index.html">Back to workspace</a>
      </div>
    </section>
  </main>
</body>
</html>
"""


def render_model_changes_html(
    meta: dict[str, object],
    family_entry: dict[str, object],
    model_entry: dict[str, object],
    model_changes: dict[str, object],
) -> str:
    family = display_text(family_entry.get("family"))
    model = display_text(model_entry.get("model"), display_text(meta.get("model")))
    default_lang = display_text(model_entry.get("default_lang"), "en").lower()
    manual_url = display_text(model_entry.get("default_manual_url"), "")
    downloads = model_changes.get("downloads", {})
    if not isinstance(downloads, dict):
        downloads = {}
    report_files = model_changes.get("report_files", {})
    if not isinstance(report_files, dict):
        report_files = {}
    areas = model_changes.get("areas", [])
    if not isinstance(areas, list):
        areas = []
    review_pages = model_changes.get("review_pages", [])
    if not isinstance(review_pages, list):
        review_pages = []

    report_links = []
    for label, key in (
        ("Report overview", "report-index.html"),
        ("Field diff", "report-fields.html"),
        ("Page diff", "report-pages.html"),
        ("File diff", "report-files.html"),
        ("Raw summary", "report-summary.html"),
    ):
        target = report_files.get(key)
        if isinstance(target, str):
            report_links.append((label, f"../../{target}"))
    download_links = build_download_links(downloads, prefix="../../")
    workspace_back_link = f"../../index.html?family={escape(family)}&model={escape(model)}&lang={escape(default_lang)}"
    shared_languages = model_entry.get("shared_language_labels", [])
    language_copy = ", ".join(str(item) for item in shared_languages if str(item).strip())
    manual_href = f"../../{manual_url}" if manual_url else "../../manual/index.html"
    workbook_href = downloads.get("change_workbook")
    workbook_button = (
        f'<a class="button download" href="../../{escape(str(workbook_href))}" download="change-report.xlsx">Download Change Workbook</a>'
        if isinstance(workbook_href, str)
        else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(family_change_title(model, family))}</title>
  <style>{base_css()}</style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">{escape(family)} / {escape(model)} Diff</span>
      <h1>{escape(model)} change report</h1>
      <p class="lede">Use this page to brief design on the packaged diff for {escape(model)} in {escape(family)}. The change report, workbook, and CSV exports are shared across this model's language variants{escape(': ' + language_copy) if language_copy else ''}.</p>
      <div class="pill-row">
        <span class="pill">Model {escape(model)}</span>
        <span class="pill">Family {escape(family)}</span>
        <span class="pill">Diff scope Model-level</span>
      </div>
      <div class="actions">
        <a class="button primary" href="{manual_href}">Open default review HTML</a>
        <a class="button secondary" href="{workspace_back_link}">Back to workspace</a>
        {workbook_button}
      </div>
      <p class="note">Language switching happens in the workspace entry page. The diff package on this page stays shared across the {escape(model)} language set for {escape(family)}.</p>
    </section>

    <section class="grid">
      <article class="card">
        <h2>Diff Links</h2>
        <ul>{render_link_list(report_links)}</ul>
      </article>
      <article class="card">
        <h2>Downloads</h2>
        <ul>{render_link_list(download_links)}</ul>
      </article>
    </section>

    <section class="grid">
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
        <p>Open <strong>Field diff</strong> for text or value deltas and <strong>Page diff</strong> for page-level impact. Use the workbook when design needs one offline handoff file for this model.</p>
      </article>
    </section>

    <section class="grid">
      {render_areas([item for item in areas if isinstance(item, dict)])}
    </section>
  </main>
</body>
</html>
"""


def render_family_changes_html(meta: dict[str, object], family_entry: dict[str, object]) -> str:
    family = display_text(family_entry.get("family"))
    cards: list[str] = []
    models = family_entry.get("models", [])
    if not isinstance(models, list):
        models = []
    for model_entry in models:
        if not isinstance(model_entry, dict):
            continue
        model = display_text(model_entry.get("model"))
        language_labels = model_entry.get("shared_language_labels", [])
        if not isinstance(language_labels, list):
            language_labels = []
        languages = ", ".join(str(item) for item in language_labels if str(item).strip())
        default_manual_url = display_text(model_entry.get("default_manual_url"), "")
        change_index_url = display_text(model_entry.get("change_index_url"), "")
        workbook_url = display_text(model_entry.get("change_workbook_url"), "")
        workbook_button = (
            f'<a class="button download" href="../../{escape(workbook_url)}" download="change-report.xlsx">Download workbook</a>'
            if workbook_url
            else ""
        )
        cards.append(
            f"""<article class="card">
        <h2>{escape(model)}</h2>
        <p class="muted">Languages: {escape(languages or "Not available")}</p>
        <div class="actions">
          <a class="button primary" href="../../{escape(change_index_url)}">Open model change report</a>
          <a class="button secondary" href="../../{escape(default_manual_url)}">Open default review HTML</a>
          {workbook_button}
        </div>
      </article>"""
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(family)} change reports</title>
  <style>{base_css()}</style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">{escape(family)} Family</span>
      <h1>{escape(family)} change reports</h1>
      <p class="lede">Choose the model-specific diff package you want to inspect for {escape(family)}.</p>
      <div class="actions">
        <a class="button secondary" href="../index.html">Back to families</a>
        <a class="button secondary" href="../../index.html">Back to workspace</a>
      </div>
    </section>

    <section class="grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""


def render_changes_home_html(meta: dict[str, object], families_payload: list[dict[str, object]]) -> str:
    cards: list[str] = []
    for family_entry in families_payload:
        family = display_text(family_entry.get("family"))
        models = family_entry.get("models", [])
        if not isinstance(models, list):
            models = []
        language_labels = family_entry.get("shared_language_labels", [])
        if not isinstance(language_labels, list):
            language_labels = []
        default_manual_url = display_text(family_entry.get("default_manual_url"), "")
        change_index_url = display_text(family_entry.get("change_index_url"), "")
        model_names = ", ".join(display_text(item.get("model")) for item in models if isinstance(item, dict))
        language_names = ", ".join(str(item) for item in language_labels if str(item).strip())
        cards.append(
            f"""<article class="card">
        <h2>{escape(family)} family</h2>
        <p class="muted">Models: {escape(model_names or display_text(meta.get("model")))}</p>
        <p class="muted">Languages: {escape(language_names or "Not available")}</p>
        <div class="actions">
          <a class="button primary" href="../{escape(change_index_url)}">Open {escape(family)} change report</a>
          <a class="button secondary" href="../{escape(default_manual_url)}">Open default review HTML</a>
        </div>
      </article>"""
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(display_text(meta.get("model")))} change reports</title>
  <style>{base_css()}</style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">Change Reports</span>
      <h1>{escape(display_text(meta.get("model")))} review diff workspace</h1>
      <p class="lede">Choose the family report you want to inspect. Each family keeps its own diff pages, workbook, and CSV exports so region-specific review changes stay easy to trace.</p>
      <div class="pill-row">
        <span class="pill">Families {escape(str(len(families_payload)))}</span>
        <span class="pill">Model {escape(display_text(meta.get("model")))}</span>
      </div>
      <div class="actions">
        <a class="button secondary" href="../index.html">Back to workspace</a>
      </div>
    </section>

    <section class="grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""


def output_root_for_target(model: str, target: WorkspaceTarget) -> Path:
    root = ROOT / "docs" / "_build" / model / target.family
    if target.include_lang_in_output_path:
        root = root / target.language
    return root


def html_root_for_target(model: str, target: WorkspaceTarget) -> Path:
    return output_root_for_target(model, target) / "html"


def word_root_for_target(model: str, target: WorkspaceTarget) -> Path:
    return output_root_for_target(model, target) / "word"


def tracked_root_for_target(args: argparse.Namespace, target: WorkspaceTarget) -> Path:
    if args.tracked_root and target.family == args.region and target.model == args.model:
        return resolve_path(args.tracked_root)
    return (ROOT / "docs" / "_review" / target.model / target.family).resolve()


def diff_config_for_family(args: argparse.Namespace, family: str) -> Path:
    if family == args.region:
        return resolved_primary_config_path(args)
    return resolve_path(default_family_config_for_region(family))


def target_templates_for_family(family: str) -> list[WorkspaceTargetTemplate]:
    return [template for template in WORKSPACE_TARGET_TEMPLATES if template.family == family]


def build_workspace_target(model: str, template: WorkspaceTargetTemplate) -> WorkspaceTarget:
    return WorkspaceTarget(
        model=model,
        family=template.family,
        language=template.language,
        config=template.config,
        include_lang_in_output_path=template.include_lang_in_output_path,
    )


def target_sort_key(target: WorkspaceTarget) -> tuple[int, str, str]:
    family_rank = FAMILY_ORDER.index(target.family) if target.family in FAMILY_ORDER else len(FAMILY_ORDER)
    return (family_rank, target.model, target.language)


def review_models() -> list[str]:
    review_root = ROOT / "docs" / "_review"
    if not review_root.exists():
        return []
    return sorted(path.name for path in review_root.iterdir() if path.is_dir())


def config_template_for_path(config_path: Path) -> WorkspaceTargetTemplate | None:
    resolved = config_path.resolve()
    for template in WORKSPACE_TARGET_TEMPLATES:
        if resolve_path(template.config) == resolved:
            return template
    return None


def requested_workspace_target(args: argparse.Namespace) -> WorkspaceTarget:
    config_path = resolved_primary_config_path(args)
    matched_template = config_template_for_path(config_path)
    if matched_template is not None:
        return build_workspace_target(args.model, matched_template)

    cfg = load_config(config_path)
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    languages = build_cfg.get("languages", [])
    if not isinstance(languages, list) or not languages:
        raise RuntimeError(f"Review preview could not infer a workspace language from config: {config_path}")
    language = str(languages[0]).strip().lower()
    include_lang = bool(build_cfg.get("include_lang_in_output_path", False))
    return WorkspaceTarget(
        model=args.model,
        family=args.region,
        language=language,
        config=path_for_display(config_path),
        include_lang_in_output_path=include_lang,
    )


def workspace_families_for_request(args: argparse.Namespace) -> tuple[str, ...]:
    preferred_family = (args.region or "").strip().upper()
    if preferred_family == "CN":
        return ("CN",)
    return FAMILY_ORDER


def _review_availability_keys_for_target(target: WorkspaceTarget) -> tuple[tuple[str, str, str | None], ...]:
    keys: list[tuple[str, str, str | None]] = [(target.model, target.family, target.language)]
    if (target.language or "").strip():
        keys.append((target.model, target.family, None))
    return tuple(keys)


def collect_review_availability(*, docs_dir: Path, targets: list[WorkspaceTarget]) -> ReviewAvailability:
    availability: ReviewAvailability = set()
    candidates: set[tuple[str, str, str | None]] = set()
    for target in targets:
        candidates.update(_review_availability_keys_for_target(target))
    for model, family, lang in sorted(candidates, key=lambda item: (item[0], item[1], item[2] or "")):
        if review_content_exists(
            docs_dir=docs_dir,
            model=model,
            region=family,
            lang=lang,
        ):
            availability.add((model, family, lang))
    return availability


def target_has_review_bundle(
    target: WorkspaceTarget,
    *,
    review_availability: ReviewAvailability | None = None,
    docs_dir: Path | None = None,
) -> bool:
    if review_availability is None:
        actual_docs_dir = docs_dir or (ROOT / "docs")
        review_availability = collect_review_availability(docs_dir=actual_docs_dir, targets=[target])
    return any(key in review_availability for key in _review_availability_keys_for_target(target))


def collect_workspace_target_candidates(
    args: argparse.Namespace,
    *,
    requested_target: WorkspaceTarget | None = None,
) -> list[WorkspaceTarget]:
    actual_requested_target = requested_target or requested_workspace_target(args)
    targets_by_key: dict[tuple[str, str, str], WorkspaceTarget] = {actual_requested_target.key: actual_requested_target}

    if args.all_review_models:
        for model in review_models():
            for template in WORKSPACE_TARGET_TEMPLATES:
                target = build_workspace_target(model, template)
                targets_by_key[target.key] = target
    else:
        for family in workspace_families_for_request(args):
            for template in target_templates_for_family(family):
                target = build_workspace_target(args.model, template)
                targets_by_key[target.key] = target

    return sorted(targets_by_key.values(), key=target_sort_key)


def build_spec_for_target(
    args: argparse.Namespace,
    target: WorkspaceTarget,
    *,
    requested_target: WorkspaceTarget,
    review_availability: ReviewAvailability | None = None,
    docs_dir: Path | None = None,
) -> dict[str, object]:
    config_path = resolve_path(target.config)
    output_root = output_root_for_target(target.model, target)
    source_mode = (
        "review"
        if target_has_review_bundle(target, review_availability=review_availability, docs_dir=docs_dir)
        else "runtime"
    )
    source_label = source_mode
    if target.key == requested_target.key:
        source_mode = args.source
        source_label = args.source

    return {
        "config_path": config_path,
        "source_mode": source_mode,
        "source_label": source_label,
        "output_root": output_root,
    }


def build_export_command(
    *,
    action: str,
    model: str,
    config_path: Path,
    family: str,
    source_mode: str,
    no_clean: bool,
) -> list[str]:
    cmd = [
        sys.executable,
        str(ROOT / "build.py"),
        action,
        "--config",
        str(config_path),
        "--model",
        model,
        "--region",
        family,
        "--source",
        source_mode,
    ]
    if no_clean:
        cmd.append("--no-clean")
    return cmd


def build_diff_command(*, args: argparse.Namespace, target: WorkspaceTarget, tracked_root: Path) -> list[str]:
    return [
        sys.executable,
        str(ROOT / "build.py"),
        "diff-report",
        "--config",
        str(diff_config_for_family(args, target.family)),
        "--model",
        target.model,
        "--region",
        target.family,
        "--tracked-root",
        str(tracked_root),
        "--from-ref",
        args.from_ref,
        "--to-ref",
        args.to_ref,
    ]


def rewrite_manual_switcher_links(
    text: str,
    *,
    model: str,
    current_target: WorkspaceTarget,
    current_relative_path: Path,
    all_targets: list[WorkspaceTarget],
) -> str:
    match = _MANUAL_SWITCHER_BLOCK_RE.search(text)
    if match is None:
        return text

    current_source_html = html_root_for_target(current_target.model, current_target) / current_relative_path
    source_start = current_source_html.parent
    preview_current = (
        Path("manual")
        / current_target.family
        / current_target.model
        / current_target.language
        / current_relative_path
    )
    preview_start = preview_current.parent
    rewritten = match.group(0)

    for target in all_targets:
        if target == current_target:
            continue

        target_source_root = html_root_for_target(target.model, target)
        target_page = current_relative_path if (target_source_root / current_relative_path).exists() else Path("index.html")
        source_target = target_source_root / target_page
        preview_target = Path("manual") / target.family / target.model / target.language / target_page

        source_href = Path(os.path.relpath(source_target, start=source_start)).as_posix()
        preview_href = Path(os.path.relpath(preview_target, start=preview_start)).as_posix()
        rewritten = rewritten.replace(f'href="{escape(source_href)}"', f'href="{escape(preview_href)}"')

    return text[: match.start()] + rewritten + text[match.end() :]


def rewrite_manual_tree_for_preview(
    manual_dir: Path,
    *,
    current_target: WorkspaceTarget,
    all_targets: list[WorkspaceTarget],
) -> None:
    for html_file in manual_dir.rglob("*.html"):
        try:
            text = html_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        html_file.write_text(
            rewrite_manual_switcher_links(
                text,
                model=current_target.model,
                current_target=current_target,
                current_relative_path=html_file.relative_to(manual_dir),
                all_targets=all_targets,
            ),
            encoding="utf-8",
        )


def discover_workspace_targets(
    args: argparse.Namespace,
    *,
    requested_target: WorkspaceTarget | None = None,
    review_availability: ReviewAvailability | None = None,
    docs_dir: Path | None = None,
) -> list[WorkspaceTarget]:
    actual_requested_target = requested_target or requested_workspace_target(args)
    target_candidates = collect_workspace_target_candidates(args, requested_target=actual_requested_target)
    actual_docs_dir = docs_dir or (ROOT / "docs")
    actual_review_availability = review_availability
    if actual_review_availability is None:
        actual_review_availability = collect_review_availability(
            docs_dir=actual_docs_dir,
            targets=target_candidates,
        )

    selected: list[WorkspaceTarget] = []
    for target in target_candidates:
        if target.key != actual_requested_target.key and args.source == "review":
            if not target_has_review_bundle(target, review_availability=actual_review_availability):
                continue
        selected.append(target)
    return selected


def assert_preview_output_contract(output_dir: Path, workspace: dict[str, object], *, require_word: bool) -> None:
    missing: list[str] = []

    for relative_path in REQUIRED_PREVIEW_FILES:
        if not (output_dir / relative_path).exists():
            missing.append(relative_path)

    defaults = workspace.get("defaults", {})
    if not isinstance(defaults, dict):
        missing.append("generated/workspace.json#defaults")
    else:
        for key in ("manual_url", "change_url"):
            target = defaults.get(key)
            if not isinstance(target, str) or not (output_dir / target).exists():
                missing.append(f"generated/workspace.json#defaults.{key}")

    families = workspace.get("families", [])
    if not isinstance(families, list) or not families:
        missing.append("generated/workspace.json#families")
    else:
        for family_entry in families:
            if not isinstance(family_entry, dict):
                missing.append("generated/workspace.json#families[]")
                continue
            family = display_text(family_entry.get("family"), "")
            if not family:
                missing.append("generated/workspace.json#families[].family")
                continue
            change_index_url = family_entry.get("change_index_url")
            if not isinstance(change_index_url, str) or not (output_dir / change_index_url).exists():
                missing.append(f"changes/{family}/index.html")

            models = family_entry.get("models", [])
            if not isinstance(models, list) or not models:
                missing.append(f"generated/workspace.json#families[{family}]#models")
                continue
            for model_entry in models:
                if not isinstance(model_entry, dict):
                    missing.append(f"generated/workspace.json#families[{family}]#models[]")
                    continue
                model_name = display_text(model_entry.get("model"), "")
                if not model_name:
                    missing.append(f"generated/workspace.json#families[{family}]#models[].model")
                    continue
                change_index_url = model_entry.get("change_index_url")
                if not isinstance(change_index_url, str) or not (output_dir / change_index_url).exists():
                    missing.append(f"changes/{family}/{model_name}/index.html")
                change_workbook = model_entry.get("change_workbook_url")
                if not isinstance(change_workbook, str) or not (output_dir / change_workbook).exists():
                    missing.append(f"downloads/{family}/{model_name}/change-report.xlsx")
                csv_urls = model_entry.get("csv_urls")
                if not isinstance(csv_urls, dict):
                    missing.extend(f"downloads/{family}/{model_name}/{name}" for name in REQUIRED_DOWNLOAD_CSVS)
                else:
                    for file_name in REQUIRED_DOWNLOAD_CSVS:
                        target = csv_urls.get(file_name)
                        if not isinstance(target, str) or not (output_dir / target).exists():
                            missing.append(f"downloads/{family}/{model_name}/{file_name}")
                report_files = model_entry.get("report_files")
                if not isinstance(report_files, dict):
                    missing.extend(f"changes/{family}/{model_name}/{name}" for name in REQUIRED_CHANGE_REPORT_FILES)
                else:
                    for file_name in REQUIRED_CHANGE_REPORT_FILES:
                        target = report_files.get(file_name)
                        if not isinstance(target, str) or not (output_dir / target).exists():
                            missing.append(f"changes/{family}/{model_name}/{file_name}")
                languages = model_entry.get("languages", [])
                if not isinstance(languages, list) or not languages:
                    missing.append(f"generated/workspace.json#families[{family}]#models[{model_name}]#languages")
                    continue
                for language_entry in languages:
                    if not isinstance(language_entry, dict):
                        missing.append(f"generated/workspace.json#families[{family}]#languages[]")
                        continue
                    manual_url = language_entry.get("manual_url")
                    if not isinstance(manual_url, str) or not (output_dir / manual_url).exists():
                        missing.append(
                            f"manual/{family}/{model_name}/{display_text(language_entry.get('lang'), '').lower()}/index.html"
                        )
                    word_url = language_entry.get("word_url")
                    if require_word and (not isinstance(word_url, str) or not (output_dir / word_url).exists()):
                        missing.append(
                            f"downloads/{family}/{model_name}/{display_text(language_entry.get('lang'), '').lower()}/review-manual.docx"
                        )

    if missing:
        raise RuntimeError("Review preview output contract is incomplete: " + ", ".join(sorted(set(missing))))


def main() -> int:
    args = parse_args()
    output_dir = resolve_path(args.output_dir)
    changed_files = collect_changed_files(args.from_ref, args.to_ref)
    requested_target = requested_workspace_target(args)
    workspace_target_candidates = collect_workspace_target_candidates(args, requested_target=requested_target)
    review_availability = collect_review_availability(
        docs_dir=ROOT / "docs",
        targets=workspace_target_candidates,
    )
    workspace_targets = discover_workspace_targets(
        args,
        requested_target=requested_target,
        review_availability=review_availability,
        docs_dir=ROOT / "docs",
    )

    if not workspace_targets:
        if args.source == "review" and args.all_review_models:
            raise FileNotFoundError("No review preview targets are available under docs/_review/.")
        if args.source == "review":
            raise FileNotFoundError(f"No review preview targets are available under docs/_review/{args.model}/.")
        raise RuntimeError("No workspace families were resolved for the review preview build.")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    manual_root = output_dir / "manual"
    changes_root = output_dir / "changes"
    downloads_root = output_dir / "downloads"
    generated_dir = output_dir / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    families_payload: list[dict[str, object]] = []
    changes_by_family: dict[str, object] = {}
    all_workspace_targets = list(workspace_targets)
    target_specs = {
        target.label: build_spec_for_target(
            args,
            target,
            requested_target=requested_target,
            review_availability=review_availability,
            docs_dir=ROOT / "docs",
        )
        for target in workspace_targets
    }

    export_plan: list[tuple[str, WorkspaceTarget]] = []
    if not args.skip_build:
        export_plan.extend(("html", target) for target in workspace_targets)
    if not args.skip_word:
        export_plan.extend(("word", target) for target in workspace_targets)

    cleaned_output_roots: set[Path] = set()
    for action, target in export_plan:
        spec = target_specs[target.label]
        output_root = Path(spec["output_root"]).resolve()
        no_clean = (not args.clean_build) or (output_root in cleaned_output_roots)
        try:
            run(
                build_export_command(
                    action=action,
                    model=target.model,
                    config_path=Path(spec["config_path"]),
                    family=target.family,
                    source_mode=str(spec["source_mode"]),
                    no_clean=no_clean,
                )
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Review preview failed to build {action.upper()} for {target.label}.") from exc
        cleaned_output_roots.add(output_root)

    grouped_targets: dict[tuple[str, str], list[WorkspaceTarget]] = {}
    for target in workspace_targets:
        grouped_targets.setdefault((target.family, target.model), []).append(target)

    families_payload_by_name: dict[str, dict[str, object]] = {}
    for family, model in sorted(grouped_targets, key=lambda item: (FAMILY_ORDER.index(item[0]) if item[0] in FAMILY_ORDER else len(FAMILY_ORDER), item[1])):
        targets = sorted(grouped_targets[(family, model)], key=target_sort_key)
        representative = targets[0]
        tracked_root = tracked_root_for_target(args, representative)

        if not args.skip_diff:
            try:
                run(build_diff_command(args=args, target=representative, tracked_root=tracked_root))
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(f"Review preview failed to build the diff-report set for {model}/{family}.") from exc

        report_root = ROOT / "reports" / "version_tracking" / model / family
        prefix = latest_report_prefix(report_root)
        model_changes_dir = changes_root / family / model
        model_downloads_dir = downloads_root / family / model

        report_files = copy_report_set(
            report_root,
            prefix,
            model_changes_dir,
            relative_dir=f"changes/{family}/{model}",
        )
        csv_files = copy_report_csvs(
            report_root,
            prefix,
            model_downloads_dir,
            relative_dir=f"downloads/{family}/{model}",
        )
        workbook_path = build_change_workbook(
            model_downloads_dir,
            csv_files,
            relative_path=f"downloads/{family}/{model}/change-report.xlsx",
        )
        if workbook_path is None:
            raise RuntimeError(f"Review preview failed to build the required change workbook for {model}/{family}.")

        language_payloads: list[dict[str, object]] = []
        shared_language_labels: list[str] = []
        default_manual_url = ""
        default_lang = ""
        model_product_name = model
        model_manual_title = f"{model} User Manual"

        for target in targets:
            spec = target_specs[target.label]
            output_root = Path(spec["output_root"])
            html_root = output_root / "html"
            if not html_root.exists():
                raise FileNotFoundError(f"HTML output not found for {target.label}: {html_root}")

            manual_dest = manual_root / family / model / target.language
            copy_tree(html_root, manual_dest)
            rewrite_manual_tree_for_preview(
                manual_dest,
                current_target=target,
                all_targets=all_workspace_targets,
            )

            manual_meta = read_json_if_exists(html_root / "manual_meta.json")
            manual_title = display_text(manual_meta.get("title"), f"{model} User Manual")
            manual_lang = str(manual_meta.get("lang") or target.language).strip().lower() or target.language
            product_name = derive_product_name(manual_title, model)
            model_product_name = product_name
            model_manual_title = manual_title

            word_path: str | None = None
            if not args.skip_word:
                latest_docx = locate_latest_docx(output_root / "word")
                if latest_docx is None:
                    raise FileNotFoundError(
                        f"Review preview Word export finished but no DOCX was found for {target.label}."
                    )
                language_download_dir = downloads_root / family / model / target.language
                language_download_dir.mkdir(parents=True, exist_ok=True)
                copied_docx = language_download_dir / "review-manual.docx"
                shutil.copy2(latest_docx, copied_docx)
                word_path = f"downloads/{family}/{model}/{target.language}/review-manual.docx"

            language_label = preview_language_label(manual_lang)
            if language_label not in shared_language_labels:
                shared_language_labels.append(language_label)

            language_entry = {
                "lang": manual_lang,
                "language_label": language_label,
                "manual_url": f"manual/{family}/{model}/{target.language}/index.html",
                "word_url": word_path,
                "product_name": product_name,
                "manual_title": manual_title,
                "region": family,
                "model": model,
                "config": path_for_display(Path(spec["config_path"])),
                "manual_source": str(spec["source_label"]),
                "tracked_root": path_for_display(tracked_root),
            }
            language_payloads.append(language_entry)
            if not default_manual_url:
                default_manual_url = str(language_entry["manual_url"])
                default_lang = manual_lang

        model_payload = {
            "model": model,
            "product_name": model_product_name,
            "manual_title": model_manual_title,
            "tracked_root": path_for_display(tracked_root),
            "diff_config": path_for_display(diff_config_for_family(args, family)),
            "change_index_url": f"changes/{family}/{model}/index.html",
            "change_workbook_url": workbook_path,
            "csv_urls": dict(csv_files),
            "report_files": dict(report_files),
            "shared_language_labels": shared_language_labels,
            "default_lang": default_lang or "en",
            "default_manual_url": default_manual_url,
            "languages": language_payloads,
        }

        family_payload = families_payload_by_name.setdefault(
            family,
            {
                "family": family,
                "change_index_url": f"changes/{family}/index.html",
                "shared_language_labels": [],
                "models": [],
            },
        )
        family_payload["models"].append(model_payload)
        family_shared_labels = family_payload["shared_language_labels"]
        if isinstance(family_shared_labels, list):
            for label in shared_language_labels:
                if label not in family_shared_labels:
                    family_shared_labels.append(label)

        family_changes = changes_by_family.setdefault(
            family,
            {
                "family": family,
                "models": {},
            },
        )
        family_changes_models = family_changes.get("models")
        if not isinstance(family_changes_models, dict):
            family_changes_models = {}
            family_changes["models"] = family_changes_models
        family_changes_models[model] = {
            "model": model,
            "family": family,
            "from_ref": args.from_ref,
            "to_ref": args.to_ref,
            "changed_files": changed_files,
            "review_pages": review_pages_for_family(changed_files, model, family),
            "areas": classify_changes(changed_files, model, family),
            "report_prefix": prefix,
            "report_files": report_files,
            "downloads": build_downloads_metadata(
                word_path=None,
                workbook_path=workbook_path,
                csv_files=csv_files,
            ),
        }

    families_payload = [
        families_payload_by_name[name]
        for name in sorted(
            families_payload_by_name,
            key=lambda family: FAMILY_ORDER.index(family) if family in FAMILY_ORDER else len(FAMILY_ORDER),
        )
    ]

    for family_entry in families_payload:
        models = family_entry.get("models", [])
        if not isinstance(models, list) or not models:
            continue
        preferred_model = next(
            (item for item in models if isinstance(item, dict) and display_text(item.get("model")) == args.model),
            models[0],
        )
        if isinstance(preferred_model, dict):
            family_entry["default_model"] = display_text(preferred_model.get("model"), args.model)
            family_entry["default_lang"] = display_text(preferred_model.get("default_lang"), requested_target.language)
            family_entry["default_manual_url"] = display_text(preferred_model.get("default_manual_url"), "")

    default_family_entry = next(
        (item for item in families_payload if display_text(item.get("family")) == args.region),
        families_payload[0],
    )
    default_models = default_family_entry.get("models", [])
    if not isinstance(default_models, list) or not default_models:
        raise RuntimeError("Review preview workspace has no model entries to render.")
    default_model_entry = next(
        (item for item in default_models if isinstance(item, dict) and display_text(item.get("model")) == args.model),
        default_models[0],
    )
    if not isinstance(default_model_entry, dict):
        raise RuntimeError("Review preview workspace default model entry is invalid.")
    default_languages = default_model_entry.get("languages", [])
    if not isinstance(default_languages, list) or not default_languages:
        raise RuntimeError("Review preview workspace default language entry is missing.")
    default_language_entry = next(
        (
            item
            for item in default_languages
            if isinstance(item, dict) and display_text(item.get("lang"), "").lower() == requested_target.language
        ),
        default_languages[0],
    )
    if not isinstance(default_language_entry, dict):
        raise RuntimeError("Review preview workspace default language entry is invalid.")
    default_model = display_text(default_model_entry.get("model"), args.model)
    default_lang = display_text(default_language_entry.get("lang"), requested_target.language).lower()
    default_manual_url = display_text(default_language_entry.get("manual_url"), "")
    default_change_url = display_text(default_model_entry.get("change_index_url"), "changes/index.html")

    commit_sha = git_value("VERCEL_GIT_COMMIT_SHA", ["git", "rev-parse", "HEAD"])
    commit_message = git_value("VERCEL_GIT_COMMIT_MESSAGE", ["git", "log", "-1", "--pretty=%s"])
    branch = git_value("VERCEL_GIT_COMMIT_REF", ["git", "rev-parse", "--abbrev-ref", "HEAD"])
    author = git_value("VERCEL_GIT_COMMIT_AUTHOR_NAME", ["git", "log", "-1", "--pretty=%an"])
    pr_id = os.environ.get("VERCEL_GIT_PULL_REQUEST_ID", "").strip()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    meta = {
        "title": workspace_title(args.model),
        "model": args.model,
        "source": args.source,
        "requested_family": args.region,
        "default_family": display_text(default_family_entry.get("family"), args.region),
        "default_model": default_model,
        "default_lang": default_lang,
        "default_manual_url": default_manual_url,
        "default_change_url": default_change_url,
        "available_families": [display_text(item.get("family")) for item in families_payload],
        "family_count": len(families_payload),
        "available_models": sorted(
            {
                display_text(model_entry.get("model"))
                for family_entry in families_payload
                for model_entry in (family_entry.get("models", []) if isinstance(family_entry.get("models", []), list) else [])
                if isinstance(model_entry, dict)
            }
        ),
        "from_ref": args.from_ref,
        "to_ref": args.to_ref,
        "branch": branch,
        "commit_sha": commit_sha,
        "commit_sha_short": commit_sha[:7],
        "commit_message": commit_message,
        "author": author,
        "pr_id": pr_id,
        "generated_at": generated_at,
        "generated_at_display": format_generated_at(generated_at),
        "vercel_env": os.environ.get("VERCEL_ENV", "").strip(),
        "vercel_url": os.environ.get("VERCEL_URL", "").strip(),
    }
    workspace = {
        **meta,
        "defaults": {
            "family": display_text(default_family_entry.get("family"), args.region),
            "model": default_model,
            "lang": default_lang,
            "manual_url": default_manual_url,
            "change_url": default_change_url,
        },
        "families": families_payload,
    }
    changes = {
        "from_ref": args.from_ref,
        "to_ref": args.to_ref,
        "defaults": dict(workspace["defaults"]),
        "families": changes_by_family,
    }

    for family_entry in families_payload:
        family_name = display_text(family_entry.get("family"))
        family_models = family_entry.get("models", [])
        if not isinstance(family_models, list):
            family_models = []
        (changes_root / family_name / "index.html").parent.mkdir(parents=True, exist_ok=True)
        (changes_root / family_name / "index.html").write_text(
            render_family_changes_html(meta, family_entry),
            encoding="utf-8",
        )
        family_changes = changes_by_family.get(family_name, {})
        family_changes_models = family_changes.get("models", {}) if isinstance(family_changes, dict) else {}
        if not isinstance(family_changes_models, dict):
            family_changes_models = {}
        for model_entry in family_models:
            if not isinstance(model_entry, dict):
                continue
            model_name = display_text(model_entry.get("model"))
            model_changes = family_changes_models.get(model_name, {})
            if not isinstance(model_changes, dict):
                model_changes = {}
            model_change_path = changes_root / family_name / model_name / "index.html"
            model_change_path.parent.mkdir(parents=True, exist_ok=True)
            model_change_path.write_text(
                render_model_changes_html(meta, family_entry, model_entry, model_changes),
                encoding="utf-8",
            )

    write_json(generated_dir / "meta.json", meta)
    write_json(generated_dir / "workspace.json", workspace)
    write_json(generated_dir / "changes.json", changes)
    (output_dir / "index.html").write_text(render_workspace_html(display_text(meta.get("title"))), encoding="utf-8")
    (manual_root / "index.html").parent.mkdir(parents=True, exist_ok=True)
    (manual_root / "index.html").write_text(
        render_redirect_html(
            title=f"{display_text(meta.get('title'))} - Manual",
            target=f"./{default_manual_url.removeprefix('manual/')}",
            heading="Open the default review HTML",
            copy="This compatibility entry now redirects to the default manual inside the review handoff workspace.",
        ),
        encoding="utf-8",
    )
    (changes_root / "index.html").parent.mkdir(parents=True, exist_ok=True)
    (changes_root / "index.html").write_text(
        render_changes_home_html(meta, families_payload),
        encoding="utf-8",
    )

    assert_preview_output_contract(output_dir, workspace, require_word=not args.skip_word)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
