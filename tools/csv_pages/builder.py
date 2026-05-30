#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=2)

try:
    from .renderers import get_renderer
except ImportError:  # pragma: no cover - direct script execution fallback
    from tools.csv_pages.renderers import get_renderer

from tools.utils.spec_master import resolve_product_name_from_spec_master
from tools.utils.path_utils import Paths
from tools.data_snapshot import STRUCTURED_DATA_DEFAULT_DIR


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows: list[dict[str, str]] = []
        for lineno, row in enumerate(reader, start=2):
            row["__line__"] = str(lineno)
            rows.append(row)
        return rows


def _parse_langs(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(",") if x.strip()]


def _parse_order(value: str) -> float:
    try:
        return float((value or "").strip())
    except Exception:
        return 0.0


def _is_enabled(value: str) -> bool:
    return (value or "1").strip().lower() in {"1", "true"}


def _csv_set(value: str | None) -> set[str] | None:
    if not value:
        return None
    values = {x.strip() for x in value.split(",") if x.strip()}
    return values or None


@dataclass(frozen=True)
class BuildPaths:
    root: Path
    page_registry: Path
    page_blocks_dir: Path
    template_dir: Path
    output_dir: Path
    spec_master_csv: Path
    spec_footnotes_csv: Path | None = None
    spec_notes_csv: Path | None = None
    spec_titles_csv: Path | None = None
    localized_copy_csv: Path | None = None

    @classmethod
    def from_root(cls, root: Path) -> "BuildPaths":
        data_root = root / STRUCTURED_DATA_DEFAULT_DIR
        paths = Paths(root=root)
        return cls(
            root=root,
            page_registry=data_root / "page_registry.csv",
            page_blocks_dir=data_root,
            template_dir=paths.templates_dir,
            output_dir=paths.docs_dir / "generated",
            spec_master_csv=data_root / "Spec_Master.csv",
            spec_footnotes_csv=data_root / "Spec_Footnotes.csv",
            spec_notes_csv=data_root / "Spec_Notes.csv",
            spec_titles_csv=data_root / "spec_titles.csv",
            localized_copy_csv=data_root / "Localized_Copy.csv",
        )


@dataclass(frozen=True)
class BuildSelector:
    models: set[str] | None = None
    regions: set[str] | None = None
    pages: set[str] | None = None
    langs: set[str] | None = None

    @classmethod
    def from_args(
        cls,
        models: str | None = None,
        regions: str | None = None,
        pages: str | None = None,
        langs: str | None = None,
    ) -> "BuildSelector":
        return cls(
            models=_csv_set(models),
            regions=_csv_set(regions),
            pages=_csv_set(pages),
            langs=_csv_set(langs),
        )


@dataclass
class BuildResult:
    written_files: list[Path]
    skipped_pages: list[str]

    @property
    def write_count(self) -> int:
        return len(self.written_files)


@dataclass(frozen=True)
class PageSpec:
    page_id: str
    page_type: str
    order: float
    sku_scope: str
    langs: list[str]
    template: str
    enabled: bool


class CsvPageBuilder:
    def __init__(self, paths: BuildPaths):
        self.paths = paths

    @staticmethod
    def _pick_model_from_vars(vars_map: dict[str, str]) -> str:
        for key in ("model", "product_model", "model_no", "model_number", "Model"):
            value = (vars_map.get(key) or "").strip()
            if value:
                return value
        return ""

    @staticmethod
    def _pick_region_from_vars(vars_map: dict[str, str]) -> str:
        for key in ("region", "Region"):
            value = (vars_map.get(key) or "").strip()
            if value:
                return value
        return ""

    @staticmethod
    def _single_selector_value(values: set[str] | None) -> str:
        if not values or len(values) != 1:
            return ""
        return next(iter(values))

    @staticmethod
    def _safe_output_key(value: str) -> str:
        text = (value or "").strip()
        if not text:
            return ""
        return text.replace("/", "_").replace("\\", "_")

    @staticmethod
    def _template_lang_dir(lang: str) -> str:
        normalized = (lang or "").strip()
        if normalized.casefold() in {"ja", "jp"}:
            return "page_jp"
        if normalized.casefold() == "zh":
            return "page_zh"
        return f"page_shared/{normalized}"

    @staticmethod
    def _looks_like_spec_master_rows(rows: list[dict[str, str]]) -> bool:
        if not rows:
            return False
        headers = set(rows[0].keys())
        required = {"Section", "Row_key", "Line_order"}
        return "block_type" not in headers and required.issubset(headers)

    @staticmethod
    def _load_optional_csv(path: Path | None) -> list[dict[str, str]]:
        if path is None or not path.exists():
            return []
        return _read_csv(path)

    @staticmethod
    def _normalize_spec_trailer_kind(value: str, *, default: str) -> str:
        normalized = (value or "").strip().casefold()
        if normalized == "note":
            return "note"
        if normalized == "footnote":
            return "footnote"
        return default

    @staticmethod
    def _localized_text_value(row: dict[str, str], lang: str) -> str:
        raw = (lang or "").strip()
        candidates = [
            f"Text_{raw}",
            f"text_{raw}",
            f"Text_{raw.casefold()}",
            f"text_{raw.casefold()}",
            f"Text_{raw.replace('-', '_')}",
            f"text_{raw.replace('-', '_')}",
            f"Text_{raw.casefold().replace('-', '_')}",
            f"text_{raw.casefold().replace('-', '_')}",
        ]
        if raw.casefold() in {"br", "pt-br", "pt_br"}:
            candidates.extend(["Text_br", "text_br", "Text_pt-BR", "text_pt-BR", "pt-BR", "br"])
        return next((row.get(key, "") or "" for key in dict.fromkeys(candidates) if row.get(key, "")), "")

    @staticmethod
    def _trailer_text_fields(row: dict[str, str], *, kind: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        for suffix in ("en", "fr", "es", "ja", "jp", "de", "it", "uk", "pt-BR", "br"):
            text = CsvPageBuilder._localized_text_value(row, suffix)
            if not text:
                continue
            fields[f"{kind}_text_{suffix}"] = text
            paired_kind = "note" if kind == "footnote" else "footnote"
            fields[f"{paired_kind}_text_{suffix}"] = text
        return fields

    @staticmethod
    def _normalize_spec_footnote_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
        if not rows:
            return []
        headers = set(rows[0].keys())
        if "Footnote_id" not in headers and "footnote_id" not in headers:
            return rows

        normalized: list[dict[str, str]] = []
        for row in rows:
            order = (row.get("Footnote_order") or row.get("footnote_order") or "").strip()
            trailer_kind = CsvPageBuilder._normalize_spec_trailer_kind(
                (row.get("Type") or row.get("type") or "").strip(),
                default="footnote",
            )
            normalized_row = {
                "__line__": row.get("__line__", ""),
                "Region": (row.get("Region") or row.get("region") or "").strip(),
                "Model": (row.get("Model") or row.get("model") or "").strip(),
                "Source_lang": (row.get("Source_lang") or row.get("source_lang") or "").strip(),
                "Is_Latest": (row.get("Is_Latest") or row.get("is_latest") or "TRUE").strip(),
                "Page": (row.get("Page") or row.get("page") or "specifications").strip(),
                "row_kind": trailer_kind,
                "kind": trailer_kind,
                "row_order": order,
                "footnote_id": (row.get("Footnote_id") or row.get("footnote_id") or "").strip(),
                "footnote_order": order,
                "type": (row.get("Type") or row.get("type") or "").strip(),
                "enabled": (row.get("Enabled") or row.get("enabled") or "TRUE").strip(),
            }
            normalized_row.update(CsvPageBuilder._trailer_text_fields(row, kind="footnote"))
            normalized.append(normalized_row)
        return normalized

    @staticmethod
    def _normalize_spec_note_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
        if not rows:
            return []

        normalized: list[dict[str, str]] = []
        for row in rows:
            order = (row.get("Note_order") or row.get("note_order") or "").strip()
            trailer_kind = CsvPageBuilder._normalize_spec_trailer_kind(
                (row.get("Type") or row.get("type") or "").strip(),
                default="note",
            )
            normalized_row = {
                "__line__": row.get("__line__", ""),
                "Region": (row.get("Region") or row.get("region") or "").strip(),
                "Model": (row.get("Model") or row.get("model") or "").strip(),
                "Source_lang": (row.get("Source_lang") or row.get("source_lang") or "").strip(),
                "Is_Latest": (row.get("Is_Latest") or row.get("is_latest") or "TRUE").strip(),
                "Page": (row.get("Page") or row.get("page") or "specifications").strip(),
                "row_kind": trailer_kind,
                "kind": trailer_kind,
                "row_order": order,
                "note_id": (row.get("Note_id") or row.get("note_id") or "").strip(),
                "note_order": order,
                "type": (row.get("Type") or row.get("type") or "").strip(),
                "enabled": (row.get("Enabled") or row.get("enabled") or "TRUE").strip(),
            }
            normalized_row.update(CsvPageBuilder._trailer_text_fields(row, kind="note"))
            normalized.append(normalized_row)
        return normalized

    def _load_pages(self) -> list[PageSpec]:
        rows = _read_csv(self.paths.page_registry)
        pages: list[PageSpec] = []

        for row in rows:
            page_id = (row.get("page_id") or "").strip()
            if not page_id:
                continue
            pages.append(
                PageSpec(
                    page_id=page_id,
                    page_type=(row.get("page_type") or "").strip(),
                    order=_parse_order(row.get("order") or "0"),
                    sku_scope=(row.get("sku_scope") or "ALL").strip(),
                    langs=_parse_langs(row.get("langs") or ""),
                    template=(row.get("template") or "").strip(),
                    enabled=_is_enabled(row.get("enabled", "1")),
                )
            )
        pages.sort(key=lambda p: p.order)
        return pages

    def _select_targets(
        self,
        selector: BuildSelector,
    ) -> list[tuple[str, dict[str, str]]]:
        targets: list[tuple[str, dict[str, str]]] = []
        selected_region = self._single_selector_value(selector.regions)

        if selector.models:
            for model in sorted(selector.models):
                vars_map = {"model": model}
                if selected_region:
                    vars_map["region"] = selected_region
                targets.append((model, vars_map))
            return targets

        if selector.regions:
            for region in sorted(selector.regions):
                targets.append((region, {"region": region}))
            return targets

        return [("default", {})]

    def _inject_product_name(
        self,
        render_vars: dict[str, str],
        *,
        lang: str,
    ) -> None:
        model_value = self._pick_model_from_vars(render_vars)
        if not model_value:
            return
        region_value = self._pick_region_from_vars(render_vars) or None
        match = resolve_product_name_from_spec_master(
            self.paths.spec_master_csv,
            model=model_value,
            region=region_value,
            lang=lang,
        )
        if not match:
            return
        render_vars["product_name"] = match.product_name
        if match.region and not region_value:
            render_vars["region"] = match.region

    def _resolve_template(self, page: PageSpec, *, lang: str | None = None) -> Path:
        raw = page.template or f"{page.page_id}_template.rst"
        if lang:
            raw = raw.replace("{lang}", lang)
            raw = raw.replace("{template_lang_dir}", self._template_lang_dir(lang))
        candidate = Path(raw)
        if candidate.is_absolute():
            return candidate

        if "/" in raw or "\\" in raw:
            return self.paths.root / candidate
        return self.paths.template_dir / candidate

    def _load_page_blocks(self, page_id: str) -> list[dict[str, str]]:
        if page_id == "spec":
            spec_master_csv = self.paths.spec_master_csv
            if not spec_master_csv.exists():
                raise FileNotFoundError(
                    "Spec master source not found. "
                    f"Expected at: {spec_master_csv}. "
                    "Configure paths.spec_master_csv in configs/config.us.yaml."
                )

            rows = _read_csv(spec_master_csv)
            if not rows:
                raise RuntimeError(f"Spec master source is empty: {spec_master_csv}")
            if not self._looks_like_spec_master_rows(rows):
                raise ValueError(
                    "Spec master source does not match Spec_Master schema "
                    f"(requires Section, Row_key, Line_order): {spec_master_csv}"
                )

            aux_footnote_rows = self._normalize_spec_footnote_rows(
                self._load_optional_csv(self.paths.spec_footnotes_csv)
            )
            if aux_footnote_rows:
                rows.extend(aux_footnote_rows)
            aux_note_rows = self._normalize_spec_note_rows(
                self._load_optional_csv(self.paths.spec_notes_csv)
            )
            if aux_note_rows:
                rows.extend(aux_note_rows)
            return rows

        per_page_csv = self.paths.page_blocks_dir / f"{page_id}_blocks.csv"
        if not per_page_csv.exists():
            return []

        rows = _read_csv(per_page_csv)
        if not rows:
            return []

        if page_id in {"lcd_icons", "troubleshooting"}:
            return rows

        headers = set(rows[0].keys())
        if "block_type" not in headers:
            raise ValueError(
                f"Unsupported schema in {per_page_csv}: missing required column 'block_type'"
            )
        else:
            # Canonical schema for page-level csv can omit page_id; we set it explicitly.
            for row in rows:
                row_page = (row.get("page_id") or "").strip()
                if not row_page:
                    row["page_id"] = page_id
                elif row_page != page_id:
                    line = (row.get("__line__") or "?").strip()
                    raise ValueError(
                        f"{per_page_csv} line {line}: page_id='{row_page}' does not match target page_id='{page_id}'"
                    )

        return [b for b in rows if (b.get("page_id") or "").strip() == page_id]

    def build(self, selector: BuildSelector, strict_renderer: bool = True) -> BuildResult:
        pages = self._load_pages()
        targets = self._select_targets(selector)
        selected_model = self._single_selector_value(selector.models)
        selected_region = self._single_selector_value(selector.regions)

        written: list[Path] = []
        skipped: list[str] = []

        for page in pages:
            if not page.enabled:
                continue
            if page.page_type != "csv_page":
                continue
            if selector.pages and page.page_id not in selector.pages:
                continue

            renderer = get_renderer(page.page_id)
            if not renderer:
                msg = f"missing renderer for page_id='{page.page_id}'"
                if strict_renderer:
                    raise RuntimeError(msg)
                skipped.append(msg)
                continue

            page_blocks = self._load_page_blocks(page.page_id)
            if not page_blocks:
                raise RuntimeError(f"No content blocks for page_id='{page.page_id}'")

            for sku_id, sku_vars in targets:
                model_value = self._pick_model_from_vars(sku_vars) or selected_model
                region_value = self._pick_region_from_vars(sku_vars) or selected_region

                if selector.models:
                    if not model_value or model_value not in selector.models:
                        continue
                if selector.regions:
                    if not region_value or region_value not in selector.regions:
                        continue

                out_key = sku_id
                if selector.models:
                    out_key = self._safe_output_key(model_value or sku_id) or sku_id
                out_dir = self.paths.output_dir / out_key
                out_dir.mkdir(parents=True, exist_ok=True)

                for lang in page.langs:
                    if selector.langs and lang not in selector.langs:
                        continue
                    template_path = self._resolve_template(page, lang=lang)
                    if not template_path.exists():
                        raise FileNotFoundError(f"Missing template for page '{page.page_id}' lang='{lang}': {template_path}")
                    template = template_path.read_text(encoding="utf-8")
                    render_vars = dict(sku_vars)
                    if model_value and not self._pick_model_from_vars(render_vars):
                        render_vars["model"] = model_value
                    if region_value and not self._pick_region_from_vars(render_vars):
                        render_vars["region"] = region_value
                    render_vars["lang"] = lang
                    render_vars["localized_copy_csv"] = str(
                        self.paths.localized_copy_csv or self.paths.page_blocks_dir / "Localized_Copy.csv"
                    )
                    if page.page_id == "spec" and self.paths.spec_titles_csv is not None:
                        render_vars["spec_titles_csv"] = str(self.paths.spec_titles_csv)
                    if page.page_id == "lcd_icons":
                        render_vars["variable_defaults_csv"] = str(
                            self.paths.page_blocks_dir / "Variable_Defaults.csv"
                        )
                        render_vars["variable_lang_overrides_csv"] = str(
                            self.paths.page_blocks_dir / "Variable_Lang_Overrides.csv"
                        )
                    self._inject_product_name(render_vars, lang=lang)
                    render_sku = (render_vars.get("sku_id") or render_vars.get("sku") or "").strip()
                    rst = renderer(template, page_blocks, render_sku, lang, render_vars)
                    out_path = out_dir / f"{page.page_id}_{lang}.rst"
                    out_path.write_text(rst, encoding="utf-8")
                    written.append(out_path)

        return BuildResult(written_files=written, skipped_pages=skipped)


def _main() -> None:
    raise SystemExit(
        "tools/csv_pages/builder.py is a library module. "
        "Use: python tools/csv_page_build.py [--model ...] [--region ...] [--page ...] [--lang ...]"
    )


if __name__ == "__main__":
    _main()
