#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from .renderers import get_renderer
except ImportError:  # pragma: no cover - direct script execution fallback
    from tools.phase1.renderers import get_renderer


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _parse_langs(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(",") if x.strip()]


def _parse_order(value: str) -> float:
    try:
        return float((value or "").strip())
    except Exception:
        return 0.0


def _is_enabled(value: str) -> bool:
    return (value or "1").strip().lower() in {"1", "true"}


def _scope_allows(scope: str, sku_id: str) -> bool:
    s = (scope or "").strip()
    if not s or s.upper() == "ALL":
        return True
    allowed = {x.strip() for x in s.split("|") if x.strip()}
    return sku_id in allowed


def _csv_set(value: str | None) -> set[str] | None:
    if not value:
        return None
    values = {x.strip() for x in value.split(",") if x.strip()}
    return values or None


def _normalize_content_blocks(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Accept both schemas:
    1) phase1 canonical: block_id,page_id,order,block_type,sku_scope,text_*,meta_json,enabled
    2) compact safety:   id,part,text_*
    """
    if not rows:
        return rows

    if "page_id" in rows[0]:
        return rows

    required = {"id", "part"}
    if not required.issubset(rows[0].keys()):
        return rows

    part_to_type = {
        "lead_top": "lead_top",
        "save_title": "save_title",
        "title_main": "title_main",
        "warning_title": "warning_title",
        "title_operating": "title_operating",
        "top": "list_item",
        "bottom": "list_item",
    }

    out: list[dict[str, str]] = []
    for row in rows:
        part = (row.get("part") or "").strip()
        if not part:
            continue

        block_type = part_to_type.get(part, "")
        if not block_type:
            continue

        block: dict[str, str] = {
            "block_id": (row.get("id") or "").strip() or f"auto_{len(out) + 1}",
            "page_id": "safety",
            "order": (row.get("id") or "").strip() or "0",
            "block_type": block_type,
            "sku_scope": "ALL",
            "meta_json": "{}",
            "enabled": "1",
        }

        if part in {"top", "bottom"}:
            block["meta_json"] = json.dumps({"list_part": part}, ensure_ascii=False)

        for key, value in row.items():
            if key.startswith("text_"):
                block[key] = value or ""

        out.append(block)

    return out


@dataclass(frozen=True)
class BuildPaths:
    root: Path
    page_registry: Path
    content_blocks: Path
    product_variables: Path
    template_dir: Path
    output_dir: Path

    @classmethod
    def from_root(cls, root: Path) -> "BuildPaths":
        return cls(
            root=root,
            page_registry=root / "data" / "phase1" / "page_registry.csv",
            content_blocks=root / "data" / "phase1" / "content_blocks.csv",
            product_variables=root / "data" / "phase1" / "product_variables.csv",
            template_dir=root / "docs" / "templates",
            output_dir=root / "docs" / "generated",
        )


@dataclass(frozen=True)
class BuildSelector:
    skus: set[str] | None = None
    pages: set[str] | None = None
    langs: set[str] | None = None

    @classmethod
    def from_args(
        cls,
        skus: str | None = None,
        pages: str | None = None,
        langs: str | None = None,
    ) -> "BuildSelector":
        return cls(skus=_csv_set(skus), pages=_csv_set(pages), langs=_csv_set(langs))


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


class Phase1Builder:
    def __init__(self, paths: BuildPaths):
        self.paths = paths

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

    def _load_vars_by_sku(self) -> dict[str, dict[str, str]]:
        rows = _read_csv(self.paths.product_variables)
        out: dict[str, dict[str, str]] = {}
        for r in rows:
            sku = (r.get("sku_id") or "").strip()
            key = (r.get("var_key") or "").strip()
            value = r.get("var_value") or ""
            if not sku or not key:
                continue
            out.setdefault(sku, {})[key] = value
        return out

    def _resolve_template(self, page: PageSpec) -> Path:
        raw = page.template or f"{page.page_id}_template.rst"
        candidate = Path(raw)
        if candidate.is_absolute():
            return candidate

        if "/" in raw or "\\" in raw:
            return self.paths.root / candidate
        return self.paths.template_dir / candidate

    def build(self, selector: BuildSelector, strict_renderer: bool = True) -> BuildResult:
        pages = self._load_pages()
        vars_by_sku = self._load_vars_by_sku()
        blocks = _normalize_content_blocks(_read_csv(self.paths.content_blocks))

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

            template_path = self._resolve_template(page)
            if not template_path.exists():
                raise FileNotFoundError(f"Missing template for page '{page.page_id}': {template_path}")
            template = template_path.read_text(encoding="utf-8")

            page_blocks = [b for b in blocks if (b.get("page_id") or "").strip() == page.page_id]
            if not page_blocks:
                raise RuntimeError(f"No content blocks for page_id='{page.page_id}'")

            for sku_id, sku_vars in vars_by_sku.items():
                if selector.skus and sku_id not in selector.skus:
                    continue
                if not _scope_allows(page.sku_scope, sku_id):
                    continue

                out_dir = self.paths.output_dir / sku_id
                out_dir.mkdir(parents=True, exist_ok=True)

                for lang in page.langs:
                    if selector.langs and lang not in selector.langs:
                        continue
                    rst = renderer(template, page_blocks, sku_id, lang, sku_vars)
                    out_path = out_dir / f"{page.page_id}_{lang}.rst"
                    out_path.write_text(rst, encoding="utf-8")
                    written.append(out_path)

        return BuildResult(written_files=written, skipped_pages=skipped)


def _main() -> None:
    raise SystemExit(
        "tools/phase1/builder.py is a library module. "
        "Use: python tools/phase1_build.py [--sku ...] [--page ...] [--lang ...]"
    )


if __name__ == "__main__":
    _main()
