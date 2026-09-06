"""Structure-first HTML source adapter for the hybrid LCD Mode table."""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.component_specs.lcd_mode import lcd_mode_component_spec


def _matches_image(image: Tag, image_key: str) -> bool:
    normalized = str(image.get("src") or "").replace("\\", "/").casefold()
    normalized_key = image_key.replace("\\", "/").casefold()
    return (
        normalized_key in normalized
        or normalized_key.rsplit("/", 1)[-1] in normalized
    )


def _cell_content(cell: Tag, prefix: str) -> dict[str, str]:
    return {
        f"{prefix}_html": cell.decode_contents().strip(),
        f"{prefix}_text": cell.get_text(" ", strip=True),
    }


def parse_lcd_mode_html(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    image_key: str,
    expected_body_rows: int,
    language: str,
) -> tuple[object, Tag, Tag]:
    images = [
        image for image in soup.find_all("img")
        if isinstance(image, Tag)
        and _matches_image(image, image_key)
    ]
    if len(images) != 1:
        raise ValueError(
            f"{source_path}: LCD Mode needs one governed artwork; found {len(images)}"
        )
    image = images[0]
    table = image.find_parent("table")
    if not isinstance(table, Tag):
        raise ValueError(f"{source_path}: LCD Mode artwork has no table")
    rows = [row for row in table.find_all("tr") if isinstance(row, Tag)]
    cells = [
        [cell for cell in row.find_all("td", recursive=False) if isinstance(cell, Tag)]
        for row in rows
    ]
    if len(rows) != expected_body_rows or [len(row) for row in cells] != [4, 2, 2, 3, 2, 2]:
        raise ValueError(f"{source_path}: LCD Mode geometry changed")
    if str(cells[0][0].get("rowspan") or "") != str(expected_body_rows):
        raise ValueError(f"{source_path}: LCD Mode artwork lost its row span")

    groups = []
    for start in (0, 3):
        state_cell = cells[start][1 if start == 0 else 0]
        action_offset = 2 if start == 0 else 1
        actions = []
        for row_index in range(start, start + 3):
            row_cells = cells[row_index]
            offset = action_offset if row_index == start else 0
            actions.append(
                {
                    **_cell_content(row_cells[offset], "action"),
                    **_cell_content(row_cells[offset + 1], "description"),
                }
            )
        groups.append(
            {
                **_cell_content(state_cell, "state"),
                "actions": actions,
            }
        )
    spec = lcd_mode_component_spec(
        accessibility_label=str(image.get("alt") or "LCD display mode"),
        groups=groups,
        artwork_ref=str(image.get("src") or ""),
        source_ref=f"{source_path}#lcd-mode",
        language=language,
    )
    return spec, table, image


__all__ = ["parse_lcd_mode_html"]
