"""Semantic Web projections for localized manual symbol components."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag


def transform_symbol_signal_table(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    expected_body_rows: int,
    error_type: type[RuntimeError],
) -> None:
    """Project the localized signal legend into the shared PDF-like Web table."""
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
    for colgroup in table.find_all("colgroup", recursive=False):
        colgroup.decompose()
    table.attrs.pop("style", None)
    table["class"] = ["hb-symbol-signal-table"]

    colgroup = soup.new_tag("colgroup")
    colgroup.append(
        soup.new_tag("col", attrs={"class": "hb-symbol-signal-col-label"})
    )
    colgroup.append(
        soup.new_tag("col", attrs={"class": "hb-symbol-signal-col-meaning"})
    )
    table.insert(0, colgroup)

    for index, header in enumerate(headers):
        header.attrs.pop("style", None)
        header["scope"] = "col"
        header["class"] = [
            "hb-symbol-signal-label-heading"
            if index == 0
            else "hb-symbol-signal-meaning-heading"
        ]

    for row_index, row in enumerate(body_rows, start=1):
        label_cell, meaning_cell = [
            cell
            for cell in row.find_all("td", recursive=False)
            if isinstance(cell, Tag)
        ]
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

        label_cell.clear()
        label_cell.attrs.pop("style", None)
        label_cell["class"] = ["hb-symbol-signal-label-cell"]
        meaning_cell.attrs.pop("style", None)
        meaning_cell["class"] = ["hb-symbol-signal-meaning-cell"]

        badge = soup.new_tag(
            "span",
            attrs={
                "class": "hb-signal-badge",
                "aria-label": localized_label,
            },
        )
        icon = soup.new_tag(
            "span",
            attrs={"class": "hb-signal-icon", "aria-hidden": "true"},
        )
        icon.string = "⚠"
        label = soup.new_tag("span", attrs={"class": "hb-signal-label"})
        label.string = localized_label
        badge.append(icon)
        badge.append(label)
        label_cell.append(badge)

    composition = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-symbol-signal-composition",
            "aria-label": " / ".join(
                header.get_text(" ", strip=True) for header in headers
            ),
        },
    )
    table.replace_with(composition)
    composition.append(table)


__all__ = ["transform_symbol_signal_table"]
