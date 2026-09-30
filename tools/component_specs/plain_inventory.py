"""Shared semantics for source-authored text-only packing inventories."""
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.component_specs.model import ComponentSpec
from tools.component_specs.reference_table import reference_table_component_spec


def is_plain_inventory(soup: BeautifulSoup) -> bool:
    """A text-only inventory has no illustrated-card or adjacent tip semantics."""
    heading = soup.find("h1")
    table = heading.find_next_sibling() if isinstance(heading, Tag) else None
    if (not isinstance(table, Tag) or table.name != "table"
            or table.find(["img", "table", "script", "style", "thead"])
            or table.select("[rowspan], [colspan]")):
        return False
    rows = table.find_all("tr")
    cells = rows[0].find_all(["td", "th"], recursive=False) if len(rows) == 1 else []
    following = table.find_next_sibling()
    return (
        len(cells) == 3
        and all(cell.get_text(" ", strip=True) for cell in cells)
        and (following is None or following.name != "table")
    )


def plain_inventory_spec(soup: BeautifulSoup, *, source_path: Path, language: str) -> ComponentSpec:
    """Project an authored text-only inventory without inventing illustrations."""
    if not is_plain_inventory(soup):
        raise ValueError(f"{source_path}: expected a complete plain inventory")
    heading = soup.find("h1")
    table = heading.find_next_sibling()
    return reference_table_component_spec(
        variant="plain-inventory", label=heading.get_text(" ", strip=True), headers=[],
        rows=[[{"html": cell.decode_contents().strip(), "text": cell.get_text("\n", strip=True)}
               for cell in table.find_all(["td", "th"])]],
        source_ref=source_path.as_posix(), language=language,
    )
