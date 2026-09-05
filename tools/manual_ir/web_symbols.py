"""Prepared symbol-table sources and their owned public IR contracts."""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.manual_ir import ManualIR, ManualIRValidationError, validate_manual_ir
from tools.manual_ir.hashing import file_sha256, value_sha256
from tools.manual_ir.source import ManualSource
from tools.manual_ir.web_source import make_web_source
from tools.utils.path_utils import get_paths


def decode_signal_table(soup: BeautifulSoup, *, source_path: Path, expected_body_rows: int):
    """Select the original governed table and validate all labels before rendering."""
    error_type = ValueError
    if isinstance(expected_body_rows, bool) or not isinstance(expected_body_rows, int) or expected_body_rows < 1:
        raise ValueError(f"{source_path}: expected body-row count must be a positive integer")
    candidates: list[tuple[Tag, list[Tag], list[Tag]]] = []
    for table in soup.find_all("table"):
        if not isinstance(table, Tag):
            continue
        header_rows = table.select("thead > tr")
        body_rows = table.select("tbody > tr")
        if len(header_rows) != 1 or len(body_rows) != expected_body_rows:
            continue
        headers = [
            cell
            for cell in header_rows[0].find_all("th", recursive=False)
            if isinstance(cell, Tag)
        ]
        rows = [
            [
                cell
                for cell in row.find_all("td", recursive=False)
                if isinstance(cell, Tag)
            ]
            for row in body_rows
        ]
        if (
            len(headers) == 2
            and all(header.get_text(" ", strip=True) for header in headers)
            and all(len(row) == 2 for row in rows)
            and all(row[0].select_one(".hb-warning-lockup") for row in rows)
            and all(row[1].get_text(" ", strip=True) for row in rows)
        ):
            candidates.append((table, headers, body_rows))

    if len(candidates) != 1:
        raise error_type(
            f"{source_path}: expected one governed {expected_body_rows}-row signal table, "
            f"found {len(candidates)}"
        )

    table, headers, body_rows = candidates[0]
    rows = [*table.select("thead > tr"), *body_rows]
    if (table.find("table") or len(table.find_all("tr")) != len(rows)
            or len(table.find_all("thead", recursive=False)) != 1
            or len(table.find_all("tbody", recursive=False)) != 1
            or table.find("tfoot")
            or any(len(row.find_all(["th", "td"], recursive=False)) != 2 for row in rows)
            or any(str(cell.get(attr, "1")) != "1" for row in rows
                   for cell in row.find_all(["th", "td"], recursive=False)
                   for attr in ("rowspan", "colspan"))):
        raise ValueError(f"{source_path}: signal table requires complete unspanned two-cell rows")
    labels = []
    for row_index, row in enumerate(body_rows, start=1):
        label_cell = row.find_all("td", recursive=False)[0]
        source_badge = label_cell.select_one(".hb-warning-lockup")
        visible_labels = (
            [
                node
                for node in source_badge.find_all("span")
                if isinstance(node, Tag)
                and not node.has_attr("aria-hidden")
                and node.get_text(" ", strip=True)
            ]
            if isinstance(source_badge, Tag)
            else []
        )
        if len(visible_labels) != 1:
            raise error_type(
                f"{source_path}: signal row {row_index} must contain one localized label"
            )
        localized_label = visible_labels[0].get_text(" ", strip=True)

        labels.append(localized_label)
    payload = {
        "expected_body_rows": expected_body_rows,
        "headers": [header.get_text(" ", strip=True) for header in headers],
        "labels": labels,
        "meanings": [row.find_all("td", recursive=False)[1].get_text(" ", strip=True) for row in body_rows],
        "table_html": str(table),
        "assets": [{"src": str(image["src"])} for image in table.select("img[src]") if image["src"]],
    }
    return payload, table, headers, body_rows


def load_web_signal_source(
    html: str, *, source_path: Path, expected_body_rows: int,
    language: str | None = None, model: str | None = None, region: str | None = None,
) -> ManualSource:
    payload, *_ = decode_signal_table(
        BeautifulSoup(html, "html.parser"), source_path=source_path, expected_body_rows=expected_body_rows,
    )
    return _symbol_source(
        html, payload=payload, source_path=source_path, language=language, model=model, region=region,
        kind="web_signal_table", projection="web-symbol-signals", shape={"expected_body_rows": expected_body_rows},
    )


def _symbol_source(html, *, payload, source_path, language, model, region, kind, projection, shape):
    contracts = get_paths().renderer_contracts_dir
    return make_web_source(
        html, source_path=source_path, blocks=((kind, payload),),
        projection=projection, language=language, model=model, region=region,
        style_contract_sha256=value_sha256({
            **shape,
            "symbols_stylesheet": file_sha256(contracts / "web_symbols_fcc_components.css"),
            "manual_stylesheet": file_sha256(contracts / "web_manual.css"),
        }),
    )


def _symbol_ir_payload(ir: ManualIR, *, projection: str, kind: str):
    issues = validate_manual_ir(ir, require_zero_skipped_raw=True)
    if issues:
        raise ManualIRValidationError(ir.source, issues)
    if (ir.metadata.get("projection") != projection or len(ir.pages) != 1
            or len(ir.pages[0].blocks) != 1):
        raise ValueError(f"expected a single-block {projection} projection")
    block = ir.pages[0].blocks[0]
    payload = block.payload
    if (block.kind != kind or not isinstance(payload, dict)
            or not isinstance(payload.get("table_html"), str)):
        raise ValueError(f"{block.source_ref}: incomplete {kind} payload")
    return payload


def decode_signal_ir(ir: ManualIR):
    payload = _symbol_ir_payload(ir, projection="web-symbol-signals", kind="web_signal_table")
    soup = BeautifulSoup(payload["table_html"], "html.parser")
    decoded, table, headers, rows = decode_signal_table(
        soup, source_path=Path(ir.pages[0].source_ref), expected_body_rows=payload.get("expected_body_rows"),
    )
    if decoded != payload:
        raise ValueError(f"{ir.pages[0].source_ref}: signal semantics/assets do not match retained markup")
    return soup, table, headers, rows, payload["labels"]


def decode_pair_table(soup: BeautifulSoup, *, source_path: Path):
    """Keep the existing matrix contract while rejecting dropped/ambiguous cells."""
    candidates: list[tuple[Tag, list[list[Tag]]]] = []
    for table in soup.find_all("table"):
        if not isinstance(table, Tag):
            continue
        rows = [row.find_all(["th", "td"], recursive=False) for row in table.find_all("tr")]
        if len(rows) != 7 or not all(len(row) == 4 for row in rows):
            continue
        header, *body_rows = rows
        if not all(cell.get_text(" ", strip=True) for cell in header):
            continue
        if not all(
            row[0].find("img")
            and row[1].get_text(" ", strip=True)
            and (
                bool(row[2].find("img"))
                == bool(row[3].get_text(" ", strip=True))
            )
            for row in body_rows
        ):
            continue
        candidates.append((table, rows))

    if len(candidates) != 1:
        raise ValueError(
            f"{source_path}: expected one governed four-column symbol table, "
            f"found {len(candidates)}"
        )

    source_table, rows = candidates[0]
    header, *body_rows = rows
    populated_right_rows = [
        row for row in body_rows if row[2].find("img")
    ]
    if len(body_rows) != 6 or len(populated_right_rows) != 5:
        raise ValueError(
            f"{source_path}: symbol panel row contract changed: "
            f"left={len(body_rows)}, right={len(populated_right_rows)}"
        )

    if (source_table.find("table") or source_table.find_parent("table")
            or any(str(cell.get(attr, "1")) != "1" for row in rows for cell in row
                   for attr in ("rowspan", "colspan"))):
        raise ValueError(f"{source_path}: symbol matrix requires unspanned four-cell rows")
    panels = []
    for offset in (0, 2):
        pairs = []
        for row in body_rows:
            icon_cell, meaning_cell = row[offset:offset + 2]
            images = icon_cell.find_all("img")
            if not images:
                if icon_cell.get_text(" ", strip=True) or meaning_cell.get_text(" ", strip=True) or meaning_cell.find("img"):
                    raise ValueError(f"{source_path}: empty symbol pair must not contain discarded content")
                continue
            if len(images) != 1 or not str(images[0].get("src") or "").strip():
                raise ValueError(f"{source_path}: symbol pair requires exactly one nonempty icon source")
            pairs.append({
                "icon": str(images[0]["src"]), "alt": str(images[0].get("alt") or ""),
                "meaning": meaning_cell.get_text(" ", strip=True),
            })
        panels.append(pairs)
    return {
        "headers": [cell.get_text(" ", strip=True) for cell in header],
        "panels": panels, "table_html": str(source_table),
        "assets": [{"src": str(image["src"])} for image in source_table.select("img[src]") if image["src"]],
    }, source_table, header, body_rows


def load_web_pair_source(
    html: str, *, source_path: Path, language: str | None = None,
    model: str | None = None, region: str | None = None,
) -> ManualSource:
    payload, *_ = decode_pair_table(BeautifulSoup(html, "html.parser"), source_path=source_path)
    return _symbol_source(
        html, payload=payload, source_path=source_path, language=language, model=model, region=region,
        kind="web_symbol_pairs", projection="web-symbol-pairs", shape={"panel_rows": [6, 5]},
    )


def decode_pair_ir(ir: ManualIR):
    payload = _symbol_ir_payload(ir, projection="web-symbol-pairs", kind="web_symbol_pairs")
    soup = BeautifulSoup(payload["table_html"], "html.parser")
    decoded, table, header, rows = decode_pair_table(soup, source_path=Path(ir.pages[0].source_ref))
    if decoded != payload:
        raise ValueError(f"{ir.pages[0].source_ref}: symbol pairs/assets do not match retained markup")
    return soup, table, header, rows
