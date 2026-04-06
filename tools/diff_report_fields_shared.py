from __future__ import annotations

import csv
import re
from pathlib import Path

from tools.config_loader import try_load_config_mapping
from tools.data_snapshot import resolve_data_snapshot_paths
from tools.utils.spec_master import source_language_for_row

INLINE_MARKUP_RE = re.compile(r"(\*\*|`|:raw-latex:|:raw-html:)")
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def load_config(config_path: Path) -> dict:
    return try_load_config_mapping(config_path)


def resolve_data_path(repo_root: Path, raw_path: object, fallback: Path) -> Path:
    if isinstance(raw_path, str) and raw_path.strip():
        path = Path(raw_path.strip())
        return path if path.is_absolute() else (repo_root / path)
    return fallback


def resolve_spec_paths(
    repo_root: Path,
    *,
    config_path: Path | None,
    data_root: str | None = None,
) -> tuple[Path, Path | None]:
    cfg = load_config(config_path) if config_path is not None else {}
    snapshot_paths = resolve_data_snapshot_paths(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
    )
    spec_master = snapshot_paths.spec_master_csv
    spec_titles = snapshot_paths.spec_titles_csv
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
    source_lang = source_language_for_row(row)
    normalized_lang = (lang or "").strip().lower()
    if base in {"Row_label", "Param", "Value"} and (normalized_lang == "en" or (source_lang and normalized_lang == source_lang)):
        keys = [f"{base}_source", f"{base.lower()}_source", base]
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
