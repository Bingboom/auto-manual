#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import html
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.utils.spec_master import is_page_value_row, page_value_matches, page_value_role, resolve_legacy_page_value_key

HEADING_UNDERLINE_RE = re.compile(r"^[=\-~^\"`:#*+]{3,}$")
SPEC_SECTION_RE = re.compile(r"\\specsectiontitle\{(.+?)\}")
HTML_SPEC_SECTION_RE = re.compile(r'<h2[^>]*>(.+?)</h2>', re.IGNORECASE)
PLAIN_COLON_FIELD_RE = re.compile(r"^\s*([A-Za-z0-9][^:]{0,120}?):\s+(.+?)\s*$")
BOLD_COLON_FIELD_RE = re.compile(r"^\s*\*\*(.+?)\*\*\s*(.*)$")
BOLD_FIELD_RE = re.compile(r"\*\*(.+?)\*\*")
ROW_START_RE = re.compile(r"^(?P<indent>\s*)\*\s-\s+(?P<value>.*)$")
CELL_START_RE = re.compile(r"^(?P<indent>\s*)-\s+(?P<value>.*)$")
INLINE_MARKUP_RE = re.compile(r"(\*\*|`|:raw-latex:|:raw-html:)")
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class DiffRow:
    tracked_root: str
    model: str
    region: str
    artifact: str
    section: str
    page_key: str
    file_name: str
    relative_path: str
    change_type: str
    insertions: str
    deletions: str
    old_path: str
    new_path: str
    from_ref: str
    to_ref: str


@dataclass(frozen=True)
class PageDiffRow:
    tracked_root: str
    model: str
    region: str
    artifact: str
    section: str
    page_key: str
    file_count: str
    change_types: str
    insertions: str
    deletions: str
    fields_changed: str
    relative_paths: str
    from_ref: str
    to_ref: str


@dataclass(frozen=True)
class FieldEntry:
    section_title: str
    field_key: str
    field_value: str


@dataclass(frozen=True)
class SpecFieldSource:
    section_title: str
    field_key: str
    source_section_key: str
    source_row_key: str
    source_line_order: str
    source_csv_line: str


@dataclass(frozen=True)
class PlaceholderValueSource:
    match_value: str
    source_section_key: str
    source_row_key: str
    source_line_order: str
    source_csv_line: str


@dataclass(frozen=True)
class FieldDiffRow:
    tracked_root: str
    model: str
    region: str
    artifact: str
    section: str
    page_key: str
    file_name: str
    relative_path: str
    section_title: str
    field_key: str
    change_type: str
    old_value: str
    new_value: str
    source_section_key: str
    source_row_key: str
    source_line_order: str
    source_csv_line: str
    from_ref: str
    to_ref: str


@dataclass(frozen=True)
class ResolvedFieldEntry:
    section_title: str
    field_key: str
    field_value: str
    source_section_key: str
    source_row_key: str
    source_line_order: str
    source_csv_line: str
    section_order: int


@dataclass(frozen=True)
class GeneratedReports:
    index_html: Path
    files_csv: Path
    files_html: Path
    pages_csv: Path
    pages_html: Path
    fields_csv: Path
    fields_html: Path
    legacy_csv: Path
    legacy_html: Path


def resolve_path_from_root(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (ROOT / path)


def sanitize_token(value: str) -> str:
    out = []
    for ch in value.strip():
        if ch.isalnum() or ch in {"-", "_", "."}:
            out.append(ch)
        else:
            out.append("_")
    text = "".join(out).strip("._")
    return text or "value"


def run_git(args: list[str], *, cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout


def git_tree_has_entries(repo_root: Path, *, ref: str, pathspec: str) -> bool:
    output = run_git(["ls-tree", "-r", "--name-only", ref, "--", pathspec], cwd=repo_root)
    return bool(output.strip())


def pathspec_from_root(repo_root: Path, tracked_root: Path) -> str:
    try:
        return tracked_root.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return tracked_root.as_posix()


def detect_initial_baseline(
    *,
    repo_root: Path,
    tracked_root: Path,
    from_ref: str,
    to_ref: str,
    file_rows: list[DiffRow],
) -> bool:
    if not file_rows:
        return False

    pathspec = pathspec_from_root(repo_root, tracked_root)
    if git_tree_has_entries(repo_root, ref=from_ref, pathspec=pathspec):
        return False
    if not git_tree_has_entries(repo_root, ref=to_ref, pathspec=pathspec):
        return False
    return all(row.change_type == "A" and not row.old_path for row in file_rows)


def parse_name_status(output: str) -> dict[str, tuple[str, str, str]]:
    rows: dict[str, tuple[str, str, str]] = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0].strip()
        kind = status[:1]
        if kind in {"R", "C"} and len(parts) >= 3:
            old_path = parts[1].strip()
            new_path = parts[2].strip()
        elif len(parts) >= 2:
            old_path = ""
            new_path = parts[1].strip()
        else:
            continue
        rows[new_path or old_path] = (kind, old_path, new_path)
    return rows


def parse_numstat(output: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        insertions = parts[0].strip()
        deletions = parts[1].strip()
        path = parts[-1].strip()
        rows[path] = (insertions, deletions)
    return rows


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    try:
        import yaml  # type: ignore
    except ImportError:
        return {}
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def resolve_data_path(repo_root: Path, raw_path: object, fallback: Path) -> Path:
    if isinstance(raw_path, str) and raw_path.strip():
        path = Path(raw_path.strip())
        return path if path.is_absolute() else (repo_root / path)
    return fallback


def resolve_spec_paths(repo_root: Path, *, config_path: Path | None) -> tuple[Path, Path | None]:
    cfg = load_config(config_path) if config_path is not None else {}
    paths_cfg = cfg.get("paths", {}) if isinstance(cfg.get("paths", {}), dict) else {}
    spec_master = resolve_data_path(repo_root, paths_cfg.get("spec_master_csv"), repo_root / "data" / "phase1" / "Spec_Master.csv")
    spec_titles_raw = paths_cfg.get("spec_titles_csv")
    spec_titles = resolve_data_path(repo_root, spec_titles_raw, repo_root / "data" / "phase1" / "spec_titles.csv")
    if not spec_titles.exists():
        spec_titles = None
    return spec_master, spec_titles


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for line_num, row in enumerate(csv.DictReader(handle), start=2):
            row["__line__"] = str(line_num)
            rows.append({str(key): str(value or "") for key, value in row.items() if key is not None})
    return rows


def first_non_empty(row: dict[str, str], keys: list[str]) -> str:
    for key in keys:
        value = (row.get(key) or "").strip()
        if value:
            return value
    return ""


def pick_lang_value(row: dict[str, str], base: str, lang: str, *, default_keys: list[str] | None = None) -> str:
    region = first_non_empty(row, ["Region", "region"]).strip().upper()
    source_lang = {"US": "en", "USA": "en", "EU": "en", "JP": "ja", "JAPAN": "ja", "CN": "zh", "CHINA": "zh", "ZH": "zh"}.get(region, "")
    normalized_lang = (lang or "").strip().lower()
    if base in {"Row_label", "Param", "Value"} and (normalized_lang == "en" or (source_lang and normalized_lang == source_lang)):
        keys = [
            f"{base}_source",
            f"{base.lower()}_source",
            base,
        ]
    else:
        keys = [
            f"{base}_{lang}",
            f"{base}_{lang.lower()}",
            f"{base}_{lang.upper()}",
            f"{base}_source",
            f"{base.lower()}_source",
            base,
        ]
    if default_keys:
        keys.extend(default_keys)
    return first_non_empty(row, keys)


def is_truthy(value: str) -> bool:
    text = (value or "").strip().lower()
    if not text:
        return True
    return text in {"1", "true", "yes", "y"}


def normalize_title_lang(lang: str) -> str:
    lowered = (lang or "").strip().lower()
    if lowered in {"ja", "jp"}:
        return "jp"
    if lowered.startswith("zh"):
        return "zh"
    return "en"


def load_spec_title_map(spec_titles_csv: Path | None, *, lang: str) -> dict[str, str]:
    if spec_titles_csv is None or not spec_titles_csv.exists():
        return {}
    rows = read_csv_rows(spec_titles_csv)
    if not rows:
        return {}
    target_col = f"title_{normalize_title_lang(lang)}"
    out: dict[str, str] = {}
    for row in rows:
        title_en = first_non_empty(row, ["title_en"])
        if not title_en:
            continue
        out[_clean_field_text(title_en)] = _clean_field_text(first_non_empty(row, [target_col]) or title_en)
    return out


def derive_lang_from_page_key(page_key: str) -> str:
    parts = page_key.rsplit("_", 1)
    if len(parts) == 2 and parts[1]:
        return parts[1].lower()
    return "en"


def derive_short_product_name(name: str) -> str:
    text = (name or "").strip()
    if not text:
        return ""
    prefix = "Jackery "
    if text.startswith(prefix):
        return text[len(prefix) :].strip()
    return text


def derive_label_lower(value: str) -> str:
    tokens = value.split()
    lowered: list[str] = []
    for token in tokens:
        if token.upper() == "BUTTON":
            lowered.append("button")
            continue
        if token.isupper():
            lowered.append(token)
            continue
        lowered.append(token.lower())
    return " ".join(lowered)


def extract_bundle_fields(path_text: str) -> tuple[str, str, str, str, str, str]:
    pure = PurePosixPath(path_text)
    parts = pure.parts
    try:
        if "_build" in parts:
            root_idx = parts.index("_build")
            model = parts[root_idx + 1]
            region = parts[root_idx + 2]
            artifact = parts[root_idx + 3]
            tail = parts[root_idx + 4 :]
        elif "_review" in parts:
            root_idx = parts.index("_review")
            model = parts[root_idx + 1]
            region = parts[root_idx + 2]
            artifact = "review"
            tail = parts[root_idx + 3 :]
        else:
            return "", "", "", "", pure.name, pure.stem
    except IndexError:
        return "", "", "", "", pure.name, pure.stem

    section = tail[0] if len(tail) > 1 else ""
    file_name = pure.name
    page_key = PurePosixPath(file_name).stem
    relative_path = "/".join(tail) if tail else file_name
    return model, region, artifact, section, relative_path, page_key


def collect_diff_rows(
    *,
    repo_root: Path,
    tracked_root: Path,
    from_ref: str,
    to_ref: str,
) -> list[DiffRow]:
    pathspec = pathspec_from_root(repo_root, tracked_root)
    name_status = parse_name_status(
        run_git(
            ["diff", "--name-status", "--find-renames", from_ref, to_ref, "--", pathspec],
            cwd=repo_root,
        )
    )
    numstat = parse_numstat(
        run_git(
            ["diff", "--numstat", "--find-renames", from_ref, to_ref, "--", pathspec],
            cwd=repo_root,
        )
    )

    rows: list[DiffRow] = []
    for key in sorted(name_status):
        change_type, old_path, new_path = name_status[key]
        stats = numstat.get(new_path) or numstat.get(old_path) or ("", "")
        chosen_path = new_path or old_path
        model, region, artifact, section, relative_path, page_key = extract_bundle_fields(chosen_path)
        rows.append(
            DiffRow(
                tracked_root=pathspec,
                model=model,
                region=region,
                artifact=artifact,
                section=section,
                page_key=page_key,
                file_name=PurePosixPath(chosen_path).name,
                relative_path=relative_path,
                change_type=change_type,
                insertions=stats[0],
                deletions=stats[1],
                old_path=old_path,
                new_path=new_path or old_path,
                from_ref=from_ref,
                to_ref=to_ref,
            )
        )
    return rows


def git_show_text(repo_root: Path, *, ref: str, path_text: str) -> str:
    if not path_text:
        return ""
    try:
        return run_git(["show", f"{ref}:{path_text}"], cwd=repo_root)
    except subprocess.CalledProcessError:
        return ""


def _clean_field_text(raw: str) -> str:
    text = raw.strip()
    if not text:
        return ""
    text = INLINE_MARKUP_RE.sub("", text)
    text = text.replace("\\textasciitilde{}", "~")
    text = TAG_RE.sub("", text)
    text = text.replace("|", " ")
    text = SPACE_RE.sub(" ", text)
    return text.strip(" -")


def _looks_like_heading(lines: list[str], idx: int) -> bool:
    if idx + 1 >= len(lines):
        return False
    title = lines[idx].rstrip()
    underline = lines[idx + 1].strip()
    return bool(title.strip()) and bool(HEADING_UNDERLINE_RE.fullmatch(underline)) and len(underline) >= len(title.strip())


def _consume_list_table(lines: list[str], start_idx: int) -> tuple[list[list[str]], int]:
    table_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    idx = start_idx + 1
    rows: list[list[str]] = []
    current_row: list[list[str]] | None = None
    current_cell_idx: int | None = None

    def flush_row() -> None:
        nonlocal current_row, current_cell_idx
        if current_row is None:
            return
        rendered = [" ".join(part for part in cell if part).strip() for cell in current_row]
        rows.append(rendered)
        current_row = None
        current_cell_idx = None

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        if stripped and indent <= table_indent and not stripped.startswith(":"):
            break

        row_match = ROW_START_RE.match(line)
        if row_match and len(row_match.group("indent")) > table_indent:
            flush_row()
            current_row = [[row_match.group("value").strip()]]
            current_cell_idx = 0
            idx += 1
            continue

        cell_match = CELL_START_RE.match(line)
        if cell_match and len(cell_match.group("indent")) > table_indent and current_row is not None:
            current_row.append([cell_match.group("value").strip()])
            current_cell_idx = len(current_row) - 1
            idx += 1
            continue

        if stripped and current_row is not None and current_cell_idx is not None:
            current_row[current_cell_idx].append(stripped)
        idx += 1

    flush_row()
    return rows, idx


def _build_field_entries(section_title: str, key: str, value: str, *, seen: dict[tuple[str, str], int]) -> FieldEntry | None:
    field_key = _clean_field_text(key)
    field_value = _clean_field_text(value)
    normalized_section = _clean_field_text(section_title)
    if not field_key:
        return None

    base = (normalized_section, field_key)
    count = seen.get(base, 0) + 1
    seen[base] = count
    if count > 1:
        field_key = f"{field_key} #{count}"
    return FieldEntry(section_title=normalized_section, field_key=field_key, field_value=field_value)


def build_spec_source_lookup(
    *,
    spec_master_csv: Path,
    spec_titles_csv: Path | None,
    model: str,
    region: str,
    lang: str,
) -> dict[tuple[str, str], SpecFieldSource]:
    rows = read_csv_rows(spec_master_csv)
    if not rows:
        return {}

    title_map = load_spec_title_map(spec_titles_csv, lang=lang)
    filtered: list[dict[str, str]] = []
    for row in rows:
        if not is_truthy(first_non_empty(row, ["enabled", "Enabled"])):
            continue
        if not is_truthy(first_non_empty(row, ["Is_Latest", "is_latest"])):
            continue
        page = first_non_empty(row, ["Page", "page"])
        if not page_value_matches(page, ("spec", "specifications")):
            continue
        row_model = first_non_empty(row, ["Model", "model", "Product_Model", "product_model", "Model_No", "model_no"])
        row_region = first_non_empty(row, ["Region", "region"])
        if model and row_model and row_model != model:
            continue
        if region and row_region and row_region != region:
            continue
        row_key = first_non_empty(row, ["Row_key", "row_key"])
        section_key = first_non_empty(row, ["Section", "section"])
        if not row_key or not section_key:
            continue
        if is_page_value_row(row) or section_key.strip().lower() == "template vars":
            continue
        filtered.append(row)

    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for idx, row in enumerate(filtered):
        section_key = first_non_empty(row, ["Section", "section"])
        row_key = first_non_empty(row, ["Row_key", "row_key"])
        section_title = pick_lang_value(
            row,
            "section_title",
            lang,
            default_keys=[f"Section_{lang}", "Section_en", "Section"],
        ) or section_key
        rendered_section_title = title_map.get(_clean_field_text(section_title), _clean_field_text(section_title))
        row_label = pick_lang_value(row, "Row_label", lang, default_keys=["Row_label_source", "Row_key"]) or row_key

        value = pick_lang_value(row, "line_text", lang)
        if not value:
            param = pick_lang_value(row, "Param", lang, default_keys=["Param_source", "Param_name"])
            spec_value = pick_lang_value(row, "Value", lang, default_keys=["Value_source", "Spec_Value"])
            sep = pick_lang_value(row, "param_value_sep", lang, default_keys=["param_value_sep"]) or ": "
            if sep == ":":
                sep = ": "
            if param and spec_value:
                value = f"{param}{sep}{spec_value}"
            else:
                value = spec_value or param
        if not value:
            continue

        key = (section_key, row_key)
        entry = grouped.setdefault(
            key,
            {
                "section_title": rendered_section_title,
                "field_key": _clean_field_text(row_label),
                "source_section_key": section_key,
                "source_row_key": row_key,
                "source_csv_line": first_non_empty(row, ["__line__"]),
                "values": [],
            },
        )
        values = entry["values"]
        assert isinstance(values, list)
        line_order = first_non_empty(row, ["Line_order", "line_order"]) or str(idx + 1)
        values.append((float(line_order.replace(",", ".")) if re.fullmatch(r"[0-9.]+", line_order) else float(idx + 1), line_order, _clean_field_text(value)))

    seen: dict[tuple[str, str], int] = {}
    lookup: dict[tuple[str, str], SpecFieldSource] = {}
    for section_key, row_key in sorted(grouped, key=lambda item: (str(item[0]), str(item[1]))):
        entry = grouped[(section_key, row_key)]
        values = entry["values"]
        assert isinstance(values, list)
        sorted_values = [item[2] for item in sorted(values, key=lambda item: item[0])]
        line_orders = [item[1] for item in sorted(values, key=lambda item: item[0])]
        field_entry = _build_field_entries(
            str(entry["section_title"]),
            str(entry["field_key"]),
            " / ".join(value for value in sorted_values if value),
            seen=seen,
        )
        if field_entry is None:
            continue
        lookup[(field_entry.section_title, field_entry.field_key)] = SpecFieldSource(
            section_title=field_entry.section_title,
            field_key=field_entry.field_key,
            source_section_key=str(entry["source_section_key"]),
            source_row_key=str(entry["source_row_key"]),
            source_line_order="|".join(line_orders),
            source_csv_line=str(entry["source_csv_line"]),
        )
    return lookup


def build_placeholder_source_lookup(
    *,
    spec_master_csv: Path,
    model: str,
    region: str,
    lang: str,
) -> dict[str, list[PlaceholderValueSource]]:
    rows = read_csv_rows(spec_master_csv)
    if not rows:
        return {}

    lookup: dict[str, list[PlaceholderValueSource]] = {}
    for idx, row in enumerate(rows):
        if not is_truthy(first_non_empty(row, ["enabled", "Enabled"])):
            continue
        if not is_truthy(first_non_empty(row, ["Is_Latest", "is_latest"])):
            continue
        row_model = first_non_empty(row, ["Model", "model", "Product_Model", "product_model", "Model_No", "model_no"])
        row_region = first_non_empty(row, ["Region", "region"])
        if model and row_model and row_model != model:
            continue
        if region and row_region and row_region != region:
            continue

        row_key = first_non_empty(row, ["Row_key", "row_key"])
        if not row_key:
            continue
        if row_key.lower() not in {"product_name", "model_no"} and not is_page_value_row(row):
            continue

        raw_value = pick_lang_value(row, "Value", lang, default_keys=["Value_source", "Spec_Value"])
        if not raw_value:
            continue

        line_order = first_non_empty(row, ["Line_order", "line_order"]) or str(idx + 1)
        source_row_key = resolve_legacy_page_value_key(row) or row_key
        base_source = PlaceholderValueSource(
            match_value="",
            source_section_key=first_non_empty(row, ["Section", "section"]),
            source_row_key=source_row_key,
            source_line_order=line_order,
            source_csv_line=first_non_empty(row, ["__line__"]),
        )

        candidate_values = [raw_value]
        lowered_row_key = row_key.lower()
        if lowered_row_key == "product_name":
            short_name = derive_short_product_name(raw_value)
            if short_name and short_name != raw_value:
                candidate_values.append(short_name)
        if page_value_role(row) == "label":
            lower_value = derive_label_lower(raw_value)
            if lower_value and lower_value != raw_value:
                candidate_values.append(lower_value)

        for candidate in candidate_values:
            normalized = _clean_field_text(candidate).lower()
            if not normalized:
                continue
            entry = PlaceholderValueSource(
                match_value=normalized,
                source_section_key=base_source.source_section_key,
                source_row_key=base_source.source_row_key,
                source_line_order=base_source.source_line_order,
                source_csv_line=base_source.source_csv_line,
            )
            existing = lookup.setdefault(normalized, [])
            if entry not in existing:
                existing.append(entry)
    return lookup


def extract_field_entries(rst_text: str) -> list[FieldEntry]:
    lines = rst_text.splitlines()
    entries: list[FieldEntry] = []
    current_heading = ""
    idx = 0
    seen: dict[tuple[str, str], int] = {}

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        if _looks_like_heading(lines, idx):
            current_heading = _clean_field_text(lines[idx])
            idx += 2
            continue

        spec_match = SPEC_SECTION_RE.search(line)
        if spec_match:
            current_heading = _clean_field_text(spec_match.group(1))
            idx += 1
            continue

        html_spec_match = HTML_SPEC_SECTION_RE.search(line)
        if html_spec_match:
            current_heading = _clean_field_text(html_spec_match.group(1))
            idx += 1
            continue

        if stripped.startswith(".. list-table::"):
            rows, next_idx = _consume_list_table(lines, idx)
            header_rows = 0
            for probe_idx in range(idx + 1, min(next_idx, idx + 8)):
                option = lines[probe_idx].strip()
                if option.startswith(":header-rows:"):
                    try:
                        header_rows = int(option.split(":", 2)[-1].strip())
                    except ValueError:
                        header_rows = 0
                    break

            for row in rows[header_rows:]:
                cleaned_cells = [_clean_field_text(cell) for cell in row]
                cleaned_cells = [cell for cell in cleaned_cells if cell]
                if not cleaned_cells:
                    continue
                if len(cleaned_cells) == 1:
                    raw_cell = row[0]
                    bold_match = BOLD_FIELD_RE.search(raw_cell)
                    if bold_match:
                        key = bold_match.group(1)
                        value = raw_cell.replace(bold_match.group(0), "", 1)
                    else:
                        key = cleaned_cells[0]
                        value = ""
                else:
                    key = " / ".join(cleaned_cells[:-1])
                    value = cleaned_cells[-1]
                entry = _build_field_entries(current_heading, key, value, seen=seen)
                if entry is not None:
                    entries.append(entry)
            idx = next_idx
            continue

        bold_colon_match = BOLD_COLON_FIELD_RE.match(line)
        if bold_colon_match:
            raw_key = bold_colon_match.group(1).strip()
            remainder = bold_colon_match.group(2).strip()
            if raw_key.endswith(":"):
                entry = _build_field_entries(
                    current_heading,
                    raw_key[:-1].strip(),
                    remainder.lstrip(":").strip(),
                    seen=seen,
                )
                if entry is not None:
                    entries.append(entry)
                idx += 1
                continue
            if remainder.startswith(":"):
                entry = _build_field_entries(
                    current_heading,
                    raw_key,
                    remainder[1:].strip(),
                    seen=seen,
                )
                if entry is not None:
                    entries.append(entry)
                idx += 1
                continue

        colon_match = PLAIN_COLON_FIELD_RE.match(line)
        if colon_match:
            entry = _build_field_entries(current_heading, colon_match.group(1), colon_match.group(2), seen=seen)
            if entry is not None:
                entries.append(entry)

        idx += 1

    return entries


def match_placeholder_sources(
    *,
    field_key: str,
    old_value: str,
    new_value: str,
    placeholder_lookup: dict[str, list[PlaceholderValueSource]],
) -> list[PlaceholderValueSource]:
    search_texts = [
        _clean_field_text(field_key).lower(),
        _clean_field_text(old_value).lower(),
        _clean_field_text(new_value).lower(),
    ]
    matches: list[tuple[int, PlaceholderValueSource]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for normalized_value, sources in placeholder_lookup.items():
        if not normalized_value:
            continue
        if not any(normalized_value in text for text in search_texts if text):
            continue
        for source in sources:
            dedupe_key = (
                source.source_section_key,
                source.source_row_key,
                source.source_line_order,
                source.source_csv_line,
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            matches.append((len(normalized_value), source))

    matches.sort(
        key=lambda item: (
            -item[0],
            item[1].source_section_key,
            item[1].source_row_key,
            item[1].source_line_order,
            item[1].source_csv_line,
        )
    )
    return [item[1] for item in matches]


def merge_sources(sources: list[PlaceholderValueSource | SpecFieldSource]) -> tuple[str, str, str, str]:
    if not sources:
        return "", "", "", ""

    section_keys: list[str] = []
    row_keys: list[str] = []
    line_orders: list[str] = []
    csv_lines: list[str] = []
    seen_sections: set[str] = set()
    seen_rows: set[str] = set()
    seen_line_orders: set[str] = set()
    seen_csv_lines: set[str] = set()

    for source in sources:
        if source.source_section_key and source.source_section_key not in seen_sections:
            seen_sections.add(source.source_section_key)
            section_keys.append(source.source_section_key)
        if source.source_row_key and source.source_row_key not in seen_rows:
            seen_rows.add(source.source_row_key)
            row_keys.append(source.source_row_key)
        if source.source_line_order and source.source_line_order not in seen_line_orders:
            seen_line_orders.add(source.source_line_order)
            line_orders.append(source.source_line_order)
        if source.source_csv_line and source.source_csv_line not in seen_csv_lines:
            seen_csv_lines.add(source.source_csv_line)
            csv_lines.append(source.source_csv_line)

    return "; ".join(section_keys), "; ".join(row_keys), "; ".join(line_orders), "; ".join(csv_lines)


def _resolve_entry_sources(
    *,
    entry: FieldEntry,
    spec_lookup: dict[tuple[str, str], SpecFieldSource],
    placeholder_lookup: dict[str, list[PlaceholderValueSource]],
) -> tuple[str, str, str, str]:
    source = spec_lookup.get((entry.section_title, entry.field_key))
    if source is not None:
        return merge_sources([source])
    matched_sources = match_placeholder_sources(
        field_key=entry.field_key,
        old_value="",
        new_value=entry.field_value,
        placeholder_lookup=placeholder_lookup,
    )
    return merge_sources(matched_sources)


def _annotate_field_entries(
    entries: list[FieldEntry],
    *,
    spec_lookup: dict[tuple[str, str], SpecFieldSource],
    placeholder_lookup: dict[str, list[PlaceholderValueSource]],
) -> list[ResolvedFieldEntry]:
    section_counts: dict[str, int] = {}
    resolved: list[ResolvedFieldEntry] = []
    for entry in entries:
        section_counts[entry.section_title] = section_counts.get(entry.section_title, 0) + 1
        source_section_key, source_row_key, source_line_order, source_csv_line = _resolve_entry_sources(
            entry=entry,
            spec_lookup=spec_lookup,
            placeholder_lookup=placeholder_lookup,
        )
        resolved.append(
            ResolvedFieldEntry(
                section_title=entry.section_title,
                field_key=entry.field_key,
                field_value=entry.field_value,
                source_section_key=source_section_key,
                source_row_key=source_row_key,
                source_line_order=source_line_order,
                source_csv_line=source_csv_line,
                section_order=section_counts[entry.section_title],
            )
        )
    return resolved


def _merge_resolved_sources(entries: list[ResolvedFieldEntry]) -> tuple[str, str, str, str]:
    section_keys: list[str] = []
    row_keys: list[str] = []
    line_orders: list[str] = []
    csv_lines: list[str] = []
    seen_sections: set[str] = set()
    seen_rows: set[str] = set()
    seen_line_orders: set[str] = set()
    seen_csv_lines: set[str] = set()

    for entry in entries:
        if entry.source_section_key and entry.source_section_key not in seen_sections:
            seen_sections.add(entry.source_section_key)
            section_keys.append(entry.source_section_key)
        if entry.source_row_key and entry.source_row_key not in seen_rows:
            seen_rows.add(entry.source_row_key)
            row_keys.append(entry.source_row_key)
        if entry.source_line_order and entry.source_line_order not in seen_line_orders:
            seen_line_orders.add(entry.source_line_order)
            line_orders.append(entry.source_line_order)
        if entry.source_csv_line and entry.source_csv_line not in seen_csv_lines:
            seen_csv_lines.add(entry.source_csv_line)
            csv_lines.append(entry.source_csv_line)

    return "; ".join(section_keys), "; ".join(row_keys), "; ".join(line_orders), "; ".join(csv_lines)


def _format_field_key(old_entry: ResolvedFieldEntry | None, new_entry: ResolvedFieldEntry | None) -> str:
    if old_entry is not None and new_entry is not None:
        if old_entry.field_key == new_entry.field_key:
            return new_entry.field_key
        if old_entry.field_key and new_entry.field_key:
            return f"{old_entry.field_key} -> {new_entry.field_key}"
    if new_entry is not None:
        return new_entry.field_key
    if old_entry is not None:
        return old_entry.field_key
    return ""


def _build_field_diff_row(
    *,
    file_row: DiffRow,
    old_entry: ResolvedFieldEntry | None,
    new_entry: ResolvedFieldEntry | None,
) -> FieldDiffRow | None:
    if old_entry is None and new_entry is None:
        return None

    if old_entry is not None and new_entry is not None:
        change_type = "M"
        if old_entry.field_key == new_entry.field_key and old_entry.field_value == new_entry.field_value:
            return None
    elif new_entry is not None:
        change_type = "A"
    else:
        change_type = "D"

    section_title = (
        new_entry.section_title
        if new_entry is not None
        else old_entry.section_title if old_entry is not None else ""
    )
    field_key = _format_field_key(old_entry, new_entry)
    old_value = old_entry.field_value if old_entry is not None else ""
    new_value = new_entry.field_value if new_entry is not None else ""
    source_section_key, source_row_key, source_line_order, source_csv_line = _merge_resolved_sources(
        [entry for entry in (old_entry, new_entry) if entry is not None]
    )
    return FieldDiffRow(
        tracked_root=file_row.tracked_root,
        model=file_row.model,
        region=file_row.region,
        artifact=file_row.artifact,
        section=file_row.section,
        page_key=file_row.page_key,
        file_name=file_row.file_name,
        relative_path=file_row.relative_path,
        section_title=section_title,
        field_key=field_key,
        change_type=change_type,
        old_value=old_value,
        new_value=new_value,
        source_section_key=source_section_key,
        source_row_key=source_row_key,
        source_line_order=source_line_order,
        source_csv_line=source_csv_line,
        from_ref=file_row.from_ref,
        to_ref=file_row.to_ref,
    )


def collect_field_diff_rows(
    *,
    repo_root: Path,
    file_rows: list[DiffRow],
    config_path: Path | None = None,
) -> list[FieldDiffRow]:
    rows: list[FieldDiffRow] = []
    spec_master_csv, spec_titles_csv = resolve_spec_paths(repo_root, config_path=config_path)
    spec_lookup_cache: dict[tuple[str, str, str], dict[tuple[str, str], SpecFieldSource]] = {}
    placeholder_lookup_cache: dict[tuple[str, str, str], dict[str, list[PlaceholderValueSource]]] = {}
    for file_row in file_rows:
        chosen_path = file_row.new_path or file_row.old_path
        if not chosen_path.endswith(".rst"):
            continue

        old_text = git_show_text(repo_root, ref=file_row.from_ref, path_text=file_row.old_path or chosen_path)
        new_text = git_show_text(repo_root, ref=file_row.to_ref, path_text=file_row.new_path or chosen_path)
        spec_lookup: dict[tuple[str, str], SpecFieldSource] = {}
        lang = derive_lang_from_page_key(file_row.page_key)
        if file_row.page_key.startswith("spec_") and spec_master_csv.exists():
            cache_key = (file_row.model, file_row.region, lang)
            spec_lookup = spec_lookup_cache.get(cache_key, {})
            if not spec_lookup:
                spec_lookup = build_spec_source_lookup(
                    spec_master_csv=spec_master_csv,
                    spec_titles_csv=spec_titles_csv,
                    model=file_row.model,
                    region=file_row.region,
                    lang=lang,
                )
                spec_lookup_cache[cache_key] = spec_lookup
        placeholder_lookup: dict[str, list[PlaceholderValueSource]] = {}
        if spec_master_csv.exists():
            cache_key = (file_row.model, file_row.region, lang)
            placeholder_lookup = placeholder_lookup_cache.get(cache_key, {})
            if not placeholder_lookup:
                placeholder_lookup = build_placeholder_source_lookup(
                    spec_master_csv=spec_master_csv,
                    model=file_row.model,
                    region=file_row.region,
                    lang=lang,
                )
                placeholder_lookup_cache[cache_key] = placeholder_lookup
        old_entries = _annotate_field_entries(
            extract_field_entries(old_text),
            spec_lookup=spec_lookup,
            placeholder_lookup=placeholder_lookup,
        )
        new_entries = _annotate_field_entries(
            extract_field_entries(new_text),
            spec_lookup=spec_lookup,
            placeholder_lookup=placeholder_lookup,
        )

        matched_old: set[int] = set()
        matched_new: set[int] = set()

        def append_pair(old_index: int | None, new_index: int | None) -> None:
            if old_index is not None:
                matched_old.add(old_index)
            if new_index is not None:
                matched_new.add(new_index)
            row = _build_field_diff_row(
                file_row=file_row,
                old_entry=old_entries[old_index] if old_index is not None else None,
                new_entry=new_entries[new_index] if new_index is not None else None,
            )
            if row is not None:
                rows.append(row)

        old_by_key: dict[tuple[str, str], list[int]] = {}
        new_by_key: dict[tuple[str, str], list[int]] = {}
        for index, entry in enumerate(old_entries):
            old_by_key.setdefault((entry.section_title, entry.field_key), []).append(index)
        for index, entry in enumerate(new_entries):
            new_by_key.setdefault((entry.section_title, entry.field_key), []).append(index)

        for key in sorted(set(old_by_key) | set(new_by_key)):
            old_indexes = old_by_key.get(key, [])
            new_indexes = new_by_key.get(key, [])
            while old_indexes and new_indexes:
                append_pair(old_indexes.pop(0), new_indexes.pop(0))

        old_by_source: dict[tuple[str, str], list[int]] = {}
        new_by_source: dict[tuple[str, str], list[int]] = {}
        for index, entry in enumerate(old_entries):
            if index in matched_old or not entry.source_row_key:
                continue
            old_by_source.setdefault((entry.section_title, entry.source_row_key), []).append(index)
        for index, entry in enumerate(new_entries):
            if index in matched_new or not entry.source_row_key:
                continue
            new_by_source.setdefault((entry.section_title, entry.source_row_key), []).append(index)

        for key in sorted(set(old_by_source) & set(new_by_source)):
            old_indexes = old_by_source.get(key, [])
            new_indexes = new_by_source.get(key, [])
            while old_indexes and new_indexes:
                append_pair(old_indexes.pop(0), new_indexes.pop(0))

        section_names = sorted(
            {
                entry.section_title
                for index, entry in enumerate(old_entries)
                if index not in matched_old
            }
            | {
                entry.section_title
                for index, entry in enumerate(new_entries)
                if index not in matched_new
            }
        )
        for section_title in section_names:
            old_indexes = [
                index
                for index, entry in enumerate(old_entries)
                if index not in matched_old and entry.section_title == section_title
            ]
            new_indexes = [
                index
                for index, entry in enumerate(new_entries)
                if index not in matched_new and entry.section_title == section_title
            ]
            if not old_indexes or len(old_indexes) != len(new_indexes):
                continue
            for old_index, new_index in zip(old_indexes, new_indexes):
                append_pair(old_index, new_index)

        for index, _entry in enumerate(old_entries):
            if index not in matched_old:
                append_pair(index, None)
        for index, _entry in enumerate(new_entries):
            if index not in matched_new:
                append_pair(None, index)
    return rows


def _safe_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def collect_page_diff_rows(file_rows: list[DiffRow], field_rows: list[FieldDiffRow]) -> list[PageDiffRow]:
    field_counts: dict[tuple[str, str, str, str, str, str], int] = {}
    for row in field_rows:
        key = (row.tracked_root, row.model, row.region, row.artifact, row.section, row.page_key)
        field_counts[key] = field_counts.get(key, 0) + 1

    grouped: dict[tuple[str, str, str, str, str, str], list[DiffRow]] = {}
    for row in file_rows:
        key = (row.tracked_root, row.model, row.region, row.artifact, row.section, row.page_key)
        grouped.setdefault(key, []).append(row)

    pages: list[PageDiffRow] = []
    for key in sorted(grouped):
        group = grouped[key]
        change_types = ",".join(sorted({row.change_type for row in group}))
        relative_paths = "; ".join(sorted(row.relative_path for row in group))
        pages.append(
            PageDiffRow(
                tracked_root=key[0],
                model=key[1],
                region=key[2],
                artifact=key[3],
                section=key[4],
                page_key=key[5],
                file_count=str(len(group)),
                change_types=change_types,
                insertions=str(sum(_safe_int(row.insertions) for row in group)),
                deletions=str(sum(_safe_int(row.deletions) for row in group)),
                fields_changed=str(field_counts.get(key, 0)),
                relative_paths=relative_paths,
                from_ref=group[0].from_ref,
                to_ref=group[0].to_ref,
            )
        )
    return pages


def write_csv_report(rows: list[object], csv_path: Path, fieldnames: list[str]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: asdict(row).get(name, "") for name in fieldnames})


def write_html_report(
    rows: list[object],
    html_path: Path,
    *,
    title: str,
    headers: list[str],
    summary_cards: list[tuple[str, str]],
    from_ref: str,
    to_ref: str,
    filter_columns: list[str] | None = None,
    enable_text_search: bool = False,
    notices: list[str] | None = None,
) -> None:
    html_path.parent.mkdir(parents=True, exist_ok=True)
    table_head = "".join(f"<th>{html.escape(col)}</th>" for col in headers)
    table_rows = []
    active_filter_columns = filter_columns or []
    filter_tokens = {column: sanitize_token(column).replace(".", "_") for column in active_filter_columns}
    for row in rows:
        row_dict = asdict(row)
        attrs: list[str] = ['data-report-row="1"']
        if enable_text_search:
            search_text = " ".join(str(row_dict.get(col, "")) for col in headers).lower()
            attrs.append(f'data-search="{html.escape(search_text, quote=True)}"')
        for column, token in filter_tokens.items():
            attrs.append(f'data-filter-{token}="{html.escape(str(row_dict.get(column, "")), quote=True)}"')
        cols = "".join(f"<td>{html.escape(str(row_dict.get(col, '')))}</td>" for col in headers)
        table_rows.append(f"<tr {' '.join(attrs)}>{cols}</tr>")

    cards_html = "".join(
        f'<div class="card"><strong>{html.escape(value)}</strong><div class="muted">{html.escape(label)}</div></div>'
        for label, value in summary_cards
    )
    filter_controls: list[str] = []
    if enable_text_search:
        filter_controls.append(
            '<label class="filter-item"><span>Search</span><input id="filter-search" type="search" placeholder="Search rows" /></label>'
        )
    for column in active_filter_columns:
        token = filter_tokens[column]
        values = sorted(
            {
                str(asdict(row).get(column, "")).strip()
                for row in rows
                if str(asdict(row).get(column, "")).strip()
            }
        )
        options = ['<option value="">All</option>'] + [
            f'<option value="{html.escape(value, quote=True)}">{html.escape(value)}</option>' for value in values
        ]
        filter_controls.append(
            f'<label class="filter-item"><span>{html.escape(column)}</span><select id="filter-{token}" data-filter-token="{token}">{"".join(options)}</select></label>'
        )
    filter_bar_html = ""
    filter_script = ""
    notice_html = ""
    notice_items = [item.strip() for item in (notices or []) if item.strip()]
    if notice_items:
        notice_html = "\n".join(
            [
                '  <div class="notices">',
                *[f'    <div class="notice">{html.escape(item)}</div>' for item in notice_items],
                "  </div>",
            ]
        )
    if filter_controls:
        filter_bar_html = "\n".join(
            [
                '  <div class="filters">',
                '    <div class="filters-grid">',
                *[f"      {item}" for item in filter_controls],
                "    </div>",
                '    <div class="muted" id="filter-result-count"></div>',
                "  </div>",
            ]
        )
        filter_script = "\n".join(
            [
                "  <script>",
                "    (function () {",
                "      const rows = Array.from(document.querySelectorAll('tr[data-report-row=\"1\"]'));",
                "      const searchInput = document.getElementById('filter-search');",
                "      const selects = Array.from(document.querySelectorAll('select[data-filter-token]'));",
                "      const resultCount = document.getElementById('filter-result-count');",
                "      const params = new URLSearchParams(window.location.search);",
                "      function syncQueryString() {",
                "        const next = new URLSearchParams();",
                "        if (searchInput && searchInput.value.trim()) {",
                "          next.set('search', searchInput.value.trim());",
                "        }",
                "        selects.forEach((select) => {",
                "          const token = select.getAttribute('data-filter-token');",
                "          if (token && select.value) {",
                "            next.set(token, select.value);",
                "          }",
                "        });",
                "        const query = next.toString();",
                "        const target = `${window.location.pathname}${query ? '?' + query : ''}${window.location.hash}`;",
                "        window.history.replaceState(null, '', target);",
                "      }",
                "      function applyFilters() {",
                "        const search = searchInput ? searchInput.value.trim().toLowerCase() : '';",
                "        let visible = 0;",
                "        rows.forEach((row) => {",
                "          let ok = true;",
                "          if (search) {",
                "            const haystack = (row.getAttribute('data-search') || '').toLowerCase();",
                "            ok = haystack.includes(search);",
                "          }",
                "          if (ok) {",
                "            selects.forEach((select) => {",
                "              const token = select.getAttribute('data-filter-token');",
                "              const wanted = select.value;",
                "              if (!wanted) {",
                "                return;",
                "              }",
                "              const actual = row.getAttribute('data-filter-' + token) || '';",
                "              if (actual !== wanted) {",
                "                ok = false;",
                "              }",
                "            });",
                "          }",
                "          row.hidden = !ok;",
                "          if (ok) {",
                "            visible += 1;",
                "          }",
                "        });",
                "        if (resultCount) {",
                "          resultCount.textContent = `${visible} / ${rows.length} rows visible`;",
                "        }",
                "      }",
                "      if (searchInput) {",
                "        const initialSearch = params.get('search') || '';",
                "        if (initialSearch) {",
                "          searchInput.value = initialSearch;",
                "        }",
                "      }",
                "      selects.forEach((select) => {",
                "        const token = select.getAttribute('data-filter-token');",
                "        if (!token) {",
                "          return;",
                "        }",
                "        const wanted = params.get(token);",
                "        if (!wanted) {",
                "          return;",
                "        }",
                "        const option = Array.from(select.options).find((item) => item.value === wanted);",
                "        if (option) {",
                "          select.value = wanted;",
                "        }",
                "      });",
                "      if (searchInput) {",
                "        searchInput.addEventListener('input', () => { syncQueryString(); applyFilters(); });",
                "      }",
                "      selects.forEach((select) => select.addEventListener('change', () => { syncQueryString(); applyFilters(); }));",
                "      applyFilters();",
                "    }());",
                "  </script>",
            ]
        )
    html_text = "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8" />',
            f"  <title>{html.escape(title)}</title>",
            "  <style>",
            "    body { font-family: Segoe UI, Arial, sans-serif; margin: 24px; }",
            "    table { border-collapse: collapse; width: 100%; font-size: 13px; }",
            "    th, td { border: 1px solid #d0d7de; padding: 6px 8px; text-align: left; vertical-align: top; }",
            "    th { background: #f6f8fa; position: sticky; top: 0; }",
            "    .summary { display: flex; gap: 16px; margin: 16px 0; flex-wrap: wrap; }",
            "    .card { border: 1px solid #d0d7de; border-radius: 8px; padding: 10px 12px; min-width: 120px; }",
            "    .notices { display: grid; gap: 10px; margin: 16px 0; }",
            "    .notice { border: 1px solid #d8b566; background: #fff8c5; border-radius: 8px; padding: 12px 14px; color: #5c4700; }",
            "    .filters { border: 1px solid #d0d7de; border-radius: 8px; padding: 12px; margin: 16px 0; background: #f6f8fa; }",
            "    .filters-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }",
            "    .filter-item { display: flex; flex-direction: column; gap: 6px; font-size: 12px; }",
            "    .filter-item input, .filter-item select { border: 1px solid #d0d7de; border-radius: 6px; padding: 8px 10px; font-size: 13px; background: #fff; }",
            "    .muted { color: #57606a; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>{html.escape(title)}</h1>",
            f"  <p class=\"muted\">{html.escape(from_ref)} -> {html.escape(to_ref)}</p>",
            f"  <div class=\"summary\">{cards_html}</div>",
            notice_html,
            filter_bar_html,
            "  <table>",
            f"    <thead><tr>{table_head}</tr></thead>",
            f"    <tbody>{''.join(table_rows)}</tbody>",
            "  </table>",
            filter_script,
            "</body>",
            "</html>",
        ]
    )
    html_path.write_text(html_text, encoding="utf-8")


def _build_relative_report_link(path: Path, filters: dict[str, str] | None = None) -> str:
    query = ""
    if filters:
        clean_filters = {key: value for key, value in filters.items() if value}
        if clean_filters:
            query = "?" + urlencode(clean_filters)
    return f"{path.name}{query}"


def write_index_report(
    *,
    reports: GeneratedReports,
    file_rows: list[DiffRow],
    page_rows: list[PageDiffRow],
    field_rows: list[FieldDiffRow],
    html_path: Path,
    tracked_root: Path,
    from_ref: str,
    to_ref: str,
    notices: list[str] | None = None,
) -> None:
    html_path.parent.mkdir(parents=True, exist_ok=True)

    targets: dict[tuple[str, str], dict[str, int]] = {}
    for row in file_rows:
        key = (row.model, row.region)
        target = targets.setdefault(key, {"files": 0, "pages": 0, "fields": 0})
        target["files"] += 1
    for row in page_rows:
        key = (row.model, row.region)
        target = targets.setdefault(key, {"files": 0, "pages": 0, "fields": 0})
        target["pages"] += 1
    for row in field_rows:
        key = (row.model, row.region)
        target = targets.setdefault(key, {"files": 0, "pages": 0, "fields": 0})
        target["fields"] += 1

    overview_cards = [
        ("tracked root", tracked_root.as_posix()),
        ("targets", str(len(targets))),
        ("files", str(len(file_rows))),
        ("pages", str(len(page_rows))),
        ("field changes", str(len(field_rows))),
    ]
    overview_html = "".join(
        f'<div class="card"><strong>{html.escape(value)}</strong><div class="muted">{html.escape(label)}</div></div>'
        for label, value in overview_cards
    )
    notice_items = [item.strip() for item in (notices or []) if item.strip()]
    notice_html = ""
    if notice_items:
        notice_html = "\n".join(
            [
                '  <div class="notices">',
                *[f'    <div class="notice">{html.escape(item)}</div>' for item in notice_items],
                "  </div>",
            ]
        )

    report_cards = [
        ("Files", "File-level diff table with insertions and deletions.", reports.files_html.name, len(file_rows)),
        ("Pages", "Page-level rollup with fields_changed counts.", reports.pages_html.name, len(page_rows)),
        ("Fields", "Structured field diff with source_row_key back-mapping.", reports.fields_html.name, len(field_rows)),
    ]
    report_links_html = "".join(
        [
            "\n".join(
                [
                    '<a class="nav-card" href="{href}">'.format(href=html.escape(path)),
                    f'  <div class="nav-title">{html.escape(title)}</div>',
                    f'  <div class="muted">{html.escape(description)}</div>',
                    f'  <div class="nav-meta">{count} rows</div>',
                    "</a>",
                ]
            )
            for title, description, path, count in report_cards
        ]
    )

    target_rows: list[str] = []
    for model, region in sorted(targets):
        stats = targets[(model, region)]
        filters = {"model": model, "region": region}
        target_rows.append(
            "\n".join(
                [
                    "<tr>",
                    f"  <td><strong>{html.escape(model)}/{html.escape(region)}</strong></td>",
                    f"  <td>{stats['files']}</td>",
                    f"  <td>{stats['pages']}</td>",
                    f"  <td>{stats['fields']}</td>",
                    "  <td>",
                    f'    <a href="{html.escape(_build_relative_report_link(reports.files_html, filters))}">files</a> | ',
                    f'    <a href="{html.escape(_build_relative_report_link(reports.pages_html, filters))}">pages</a> | ',
                    f'    <a href="{html.escape(_build_relative_report_link(reports.fields_html, filters))}">fields</a>',
                    "  </td>",
                    "</tr>",
                ]
            )
        )

    html_text = "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8" />',
            "  <title>RST Diff Report - Index</title>",
            "  <style>",
            "    body { font-family: Segoe UI, Arial, sans-serif; margin: 24px; }",
            "    a { color: #0969da; text-decoration: none; }",
            "    a:hover { text-decoration: underline; }",
            "    .summary { display: flex; gap: 16px; margin: 16px 0 24px; flex-wrap: wrap; }",
            "    .card { border: 1px solid #d0d7de; border-radius: 8px; padding: 10px 12px; min-width: 140px; background: #fff; }",
            "    .notices { display: grid; gap: 10px; margin: 16px 0; }",
            "    .notice { border: 1px solid #d8b566; background: #fff8c5; border-radius: 8px; padding: 12px 14px; color: #5c4700; }",
            "    .nav-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 16px 0 24px; }",
            "    .nav-card { display: block; border: 1px solid #d0d7de; border-radius: 10px; padding: 14px; background: #f6f8fa; }",
            "    .nav-title { font-weight: 600; margin-bottom: 6px; }",
            "    .nav-meta { margin-top: 8px; color: #24292f; font-size: 12px; }",
            "    table { border-collapse: collapse; width: 100%; font-size: 13px; margin-top: 16px; }",
            "    th, td { border: 1px solid #d0d7de; padding: 8px 10px; text-align: left; vertical-align: top; }",
            "    th { background: #f6f8fa; }",
            "    .muted { color: #57606a; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <h1>RST Diff Report - Index</h1>",
            f"  <p class=\"muted\">{html.escape(from_ref)} -> {html.escape(to_ref)}</p>",
            f"  <div class=\"summary\">{overview_html}</div>",
            notice_html,
            "  <h2>Report Views</h2>",
            "  <div class=\"nav-grid\">",
            report_links_html,
            "  </div>",
            "  <h2>Jump by Target</h2>",
            "  <p class=\"muted\">These links open the report pages with model/region filters pre-applied.</p>",
            "  <table>",
            "    <thead><tr><th>Target</th><th>Files</th><th>Pages</th><th>Field Changes</th><th>Links</th></tr></thead>",
            f"    <tbody>{''.join(target_rows)}</tbody>",
            "  </table>",
            "</body>",
            "</html>",
        ]
    )
    html_path.write_text(html_text, encoding="utf-8")


def build_report_base_name(tracked_root: Path, from_ref: str, to_ref: str) -> str:
    scope_name = tracked_root.name or "tracked_root"
    return f"{sanitize_token(scope_name)}_{sanitize_token(from_ref)}_to_{sanitize_token(to_ref)}"


def generate_diff_report(
    *,
    repo_root: Path,
    tracked_root: Path,
    from_ref: str,
    to_ref: str,
    output_dir: Path,
    config_path: Path | None = None,
    ignore_initial_adds: bool = True,
) -> tuple[Path, Path]:
    raw_file_rows = collect_diff_rows(
        repo_root=repo_root,
        tracked_root=tracked_root,
        from_ref=from_ref,
        to_ref=to_ref,
    )
    is_initial_baseline = detect_initial_baseline(
        repo_root=repo_root,
        tracked_root=tracked_root,
        from_ref=from_ref,
        to_ref=to_ref,
        file_rows=raw_file_rows,
    )
    notices: list[str] = []
    if is_initial_baseline:
        notices.append(
            "Initial baseline detected for this tracked root. All Added rows are expected because the subtree did not exist at the from-ref."
        )
    if is_initial_baseline and ignore_initial_adds:
        notices.append(
            "Initial Added rows were excluded by default. Pass --include-initial-adds to keep them."
        )
        file_rows: list[DiffRow] = []
    else:
        file_rows = raw_file_rows

    field_rows = collect_field_diff_rows(repo_root=repo_root, file_rows=file_rows, config_path=config_path)
    page_rows = collect_page_diff_rows(file_rows, field_rows)

    base_name = build_report_base_name(tracked_root, from_ref, to_ref)
    reports = GeneratedReports(
        index_html=output_dir / f"{base_name}_index.html",
        files_csv=output_dir / f"{base_name}_files.csv",
        files_html=output_dir / f"{base_name}_files.html",
        pages_csv=output_dir / f"{base_name}_pages.csv",
        pages_html=output_dir / f"{base_name}_pages.html",
        fields_csv=output_dir / f"{base_name}_fields.csv",
        fields_html=output_dir / f"{base_name}_fields.html",
        legacy_csv=output_dir / f"{base_name}.csv",
        legacy_html=output_dir / f"{base_name}.html",
    )

    file_headers = [
        "tracked_root",
        "model",
        "region",
        "artifact",
        "section",
        "page_key",
        "file_name",
        "relative_path",
        "change_type",
        "insertions",
        "deletions",
        "old_path",
        "new_path",
        "from_ref",
        "to_ref",
    ]
    page_headers = [
        "tracked_root",
        "model",
        "region",
        "artifact",
        "section",
        "page_key",
        "file_count",
        "change_types",
        "insertions",
        "deletions",
        "fields_changed",
        "relative_paths",
        "from_ref",
        "to_ref",
    ]
    field_headers = [
        "tracked_root",
        "model",
        "region",
        "artifact",
        "section",
        "page_key",
        "file_name",
        "relative_path",
        "section_title",
        "field_key",
        "change_type",
        "old_value",
        "new_value",
        "source_section_key",
        "source_row_key",
        "source_line_order",
        "source_csv_line",
        "from_ref",
        "to_ref",
    ]

    write_csv_report(file_rows, reports.files_csv, file_headers)
    write_csv_report(file_rows, reports.legacy_csv, file_headers)
    write_csv_report(page_rows, reports.pages_csv, page_headers)
    write_csv_report(field_rows, reports.fields_csv, field_headers)

    write_html_report(
        file_rows,
        reports.files_html,
        title="RST Diff Report - Files",
        headers=file_headers,
        summary_cards=[
            ("files", str(len(file_rows))),
            ("added", str(sum(1 for row in file_rows if row.change_type == "A"))),
            ("modified", str(sum(1 for row in file_rows if row.change_type == "M"))),
            ("deleted", str(sum(1 for row in file_rows if row.change_type == "D"))),
            ("renamed", str(sum(1 for row in file_rows if row.change_type == "R"))),
        ],
        from_ref=from_ref,
        to_ref=to_ref,
        filter_columns=["model", "region", "section", "change_type"],
        enable_text_search=True,
        notices=notices,
    )
    write_html_report(
        file_rows,
        reports.legacy_html,
        title="RST Diff Report - Files",
        headers=file_headers,
        summary_cards=[
            ("files", str(len(file_rows))),
            ("added", str(sum(1 for row in file_rows if row.change_type == "A"))),
            ("modified", str(sum(1 for row in file_rows if row.change_type == "M"))),
            ("deleted", str(sum(1 for row in file_rows if row.change_type == "D"))),
            ("renamed", str(sum(1 for row in file_rows if row.change_type == "R"))),
        ],
        from_ref=from_ref,
        to_ref=to_ref,
        filter_columns=["model", "region", "section", "change_type"],
        enable_text_search=True,
        notices=notices,
    )
    write_html_report(
        page_rows,
        reports.pages_html,
        title="RST Diff Report - Pages",
        headers=page_headers,
        summary_cards=[
            ("pages", str(len(page_rows))),
            ("files touched", str(len(file_rows))),
            ("field changes", str(len(field_rows))),
        ],
        from_ref=from_ref,
        to_ref=to_ref,
        filter_columns=["model", "region", "page_key", "change_types"],
        enable_text_search=True,
        notices=notices,
    )
    write_html_report(
        field_rows,
        reports.fields_html,
        title="RST Diff Report - Fields",
        headers=field_headers,
        summary_cards=[
            ("field changes", str(len(field_rows))),
            ("added", str(sum(1 for row in field_rows if row.change_type == "A"))),
            ("modified", str(sum(1 for row in field_rows if row.change_type == "M"))),
            ("deleted", str(sum(1 for row in field_rows if row.change_type == "D"))),
        ],
        from_ref=from_ref,
        to_ref=to_ref,
        filter_columns=["model", "region", "page_key", "source_row_key", "change_type"],
        enable_text_search=True,
        notices=notices,
    )
    write_index_report(
        reports=reports,
        file_rows=file_rows,
        page_rows=page_rows,
        field_rows=field_rows,
        html_path=reports.index_html,
        tracked_root=tracked_root,
        from_ref=from_ref,
        to_ref=to_ref,
        notices=notices,
    )
    return reports.legacy_csv, reports.legacy_html


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Export git diff under a tracked docs subtree to CSV/HTML.")
    ap.add_argument("--tracked-root", default="docs/_review/JE-1000F", help="Tracked subtree root")
    ap.add_argument("--config", default="config.yaml", help="Config YAML path for resolving source CSV metadata")
    ap.add_argument("--from-ref", default="HEAD~1", help="Git from ref")
    ap.add_argument("--to-ref", default="HEAD", help="Git to ref")
    ap.set_defaults(ignore_initial_adds=True)
    ap.add_argument(
        "--ignore-initial-adds",
        dest="ignore_initial_adds",
        action="store_true",
        help="When the tracked subtree is first introduced, ignore the initial all-Added diff rows in generated reports (default)",
    )
    ap.add_argument(
        "--include-initial-adds",
        dest="ignore_initial_adds",
        action="store_false",
        help="When the tracked subtree is first introduced, keep the initial all-Added diff rows in generated reports",
    )
    ap.add_argument(
        "--output-dir",
        default="reports/version_tracking/JE-1000F",
        help="Output directory for CSV/HTML reports",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    tracked_root = resolve_path_from_root(args.tracked_root)
    config_path = resolve_path_from_root(args.config)
    output_dir = resolve_path_from_root(args.output_dir)
    try:
        raw_file_rows = collect_diff_rows(
            repo_root=ROOT,
            tracked_root=tracked_root,
            from_ref=args.from_ref,
            to_ref=args.to_ref,
        )
        is_initial_baseline = detect_initial_baseline(
            repo_root=ROOT,
            tracked_root=tracked_root,
            from_ref=args.from_ref,
            to_ref=args.to_ref,
            file_rows=raw_file_rows,
        )
        legacy_csv, legacy_html = generate_diff_report(
            repo_root=ROOT,
            tracked_root=tracked_root,
            from_ref=args.from_ref,
            to_ref=args.to_ref,
            output_dir=output_dir,
            config_path=config_path,
            ignore_initial_adds=args.ignore_initial_adds,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stderr or str(exc), file=sys.stderr)
        return exc.returncode or 1

    base_name = build_report_base_name(tracked_root, args.from_ref, args.to_ref)
    if is_initial_baseline:
        print(
            "[diff_report] NOTE: Initial baseline detected under "
            f"{tracked_root}. All Added rows are expected because the subtree did not exist at {args.from_ref}."
        )
        if args.ignore_initial_adds:
            print("[diff_report] NOTE: Initial Added rows were excluded by default. Pass --include-initial-adds to keep them.")
    print(f"[diff_report] FILES CSV: {output_dir / f'{base_name}_files.csv'}")
    print(f"[diff_report] FILES HTML: {output_dir / f'{base_name}_files.html'}")
    print(f"[diff_report] PAGES CSV: {output_dir / f'{base_name}_pages.csv'}")
    print(f"[diff_report] PAGES HTML: {output_dir / f'{base_name}_pages.html'}")
    print(f"[diff_report] FIELDS CSV: {output_dir / f'{base_name}_fields.csv'}")
    print(f"[diff_report] FIELDS HTML: {output_dir / f'{base_name}_fields.html'}")
    print(f"[diff_report] INDEX HTML: {output_dir / f'{base_name}_index.html'}")
    print(f"[diff_report] CSV: {legacy_csv}")
    print(f"[diff_report] HTML: {legacy_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
