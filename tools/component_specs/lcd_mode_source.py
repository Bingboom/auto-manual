"""Preserve authored headers in a standalone LCD image and action matrix."""
from bs4 import Tag

from tools.component_specs.reference_table import reference_table_component_spec


def standalone_lcd_actions(image, *, source_path, expected_body_rows, language):
    table = image.find_next_sibling()
    if not isinstance(table, Tag) or table.name != "table":
        raise ValueError(f"{source_path}: standalone LCD artwork requires an adjacent table")
    rows = [row.find_all(["th", "td"], recursive=False) for row in table.find_all("tr")]
    if (len(rows) != expected_body_rows + 1 or any(len(row) != 4 for row in rows)
            or table.select("[rowspan], [colspan], img, table")
            or any(row[0].get_text(strip=True) for row in rows)
            or not all(cell.name == "th" for cell in rows[0])
            or not all(cell.get_text(strip=True) for cell in rows[0][1:])):
        raise ValueError(f"{source_path}: standalone LCD matrix geometry changed")
    cells = lambda row: [{"html": c.decode_contents().strip(),
                          "text": c.get_text(" ", strip=True)} for c in row[1:]]
    spec = reference_table_component_spec(
        variant="lcd-actions", label=str(image.get("alt") or "LCD display mode"),
        headers=cells(rows[0]), rows=[cells(row) for row in rows[1:]],
        source_ref=f"{source_path}#lcd-mode", language=language,
    )
    return spec, table, image
