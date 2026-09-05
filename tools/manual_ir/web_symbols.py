"""Prepared signal-word legend source and its owned public IR contract."""
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
    contracts = get_paths().renderer_contracts_dir
    return make_web_source(
        html, source_path=source_path, blocks=(("web_signal_table", payload),),
        projection="web-symbol-signals", language=language, model=model, region=region,
        style_contract_sha256=value_sha256({
            "expected_body_rows": expected_body_rows,
            "symbols_stylesheet": file_sha256(contracts / "web_symbols_fcc_components.css"),
            "manual_stylesheet": file_sha256(contracts / "web_manual.css"),
        }),
    )


def decode_signal_ir(ir: ManualIR):
    issues = validate_manual_ir(ir, require_zero_skipped_raw=True)
    if issues:
        raise ManualIRValidationError(ir.source, issues)
    if (ir.metadata.get("projection") != "web-symbol-signals" or len(ir.pages) != 1
            or len(ir.pages[0].blocks) != 1):
        raise ValueError("expected a single-block web-symbol-signals projection")
    block = ir.pages[0].blocks[0]
    payload = block.payload
    if (block.kind != "web_signal_table" or not isinstance(payload, dict)
            or not isinstance(payload.get("table_html"), str)):
        raise ValueError(f"{block.source_ref}: incomplete signal-table payload")
    soup = BeautifulSoup(payload["table_html"], "html.parser")
    decoded, table, headers, rows = decode_signal_table(
        soup, source_path=Path(ir.pages[0].source_ref), expected_body_rows=payload.get("expected_body_rows"),
    )
    if decoded != payload:
        raise ValueError(f"{block.source_ref}: signal semantics/assets do not match retained markup")
    return soup, table, headers, rows, payload["labels"]
