"""Explicit RST table declarations into existing and text-reference components."""
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.component_specs.manual_tables import symbol_signal_component_spec
from tools.component_specs.reference_table import reference_table_component_spec, VARIANTS


DECLARATIONS = {f"hb-source-{variant}": variant for variant in VARIANTS}


def _cell(cell):
    if cell.find(["img", "table", "script", "style"]):
        raise ValueError("authored text table contains unsupported cell markup")
    return {"html": cell.decode_contents().strip(), "text": cell.get_text("\n", strip=True)}


def _rows(table, columns, has_headers, source_path):
    if table.find("table") or table.select("[rowspan], [colspan]"):
        raise ValueError(f"{source_path}: authored table cannot contain nested tables or spans")
    rows = table.find_all("tr")
    values = []
    for row in rows:
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) != columns:
            raise ValueError(f"{source_path}: expected {columns} authored table columns")
        values.append([_cell(cell) for cell in cells])
    header_rows = table.select("thead > tr")
    if len(header_rows) != int(has_headers) or (has_headers and rows[0] is not header_rows[0]):
        raise ValueError(f"{source_path}: authored table header policy mismatch")
    return (values[0], values[1:]) if has_headers else ([], values)


def normalize_declared_specifications(soup: BeautifulSoup, source_path: Path):
    for table in soup.select("table.hb-source-specification"):
        heading = table.find_previous_sibling()
        if not isinstance(heading, Tag) or heading.name != "h2":
            raise ValueError(f"{source_path}: specification requires adjacent authored H2")
        heading["class"] = list(dict.fromkeys([*heading.get("class", []), "hb-spec-section"]))
        if heading.select_one(".hb-spec-section-text") is None:
            title = soup.new_tag("span", attrs={"class": "hb-spec-section-text"})
            for node in list(heading.contents):
                title.append(node.extract())
            heading.append(title)
        table["class"] = list(dict.fromkeys([*table.get("class", []), "hb-spec-table"]))


def parse_authored_tables(soup: BeautifulSoup, *, source_path: Path, language: str):
    claims = []
    for index, table in enumerate(soup.find_all("table"), start=1):
        declarations = set(table.get("class", [])) & (set(DECLARATIONS) | {"hb-source-signals"})
        if not declarations:
            continue
        if len(declarations) != 1:
            raise ValueError(f"{source_path}: table has conflicting semantic declarations")
        declaration = declarations.pop()
        heading = table.find_previous(["h1", "h2"])
        if heading is None:
            raise ValueError(f"{source_path}: authored table has no accessible heading")
        source_ref = f"{source_path}#authored-table-{index}"
        if declaration == "hb-source-signals":
            headers, rows = _rows(table, 2, True, source_path)
            spec = symbol_signal_component_spec(
                accessibility_label=heading.get_text(" ", strip=True),
                headers=[{"content_html": c["html"], "content_text": c["text"]} for c in headers],
                rows=[{"label": row[0]["text"], "meaning_html": row[1]["html"],
                       "meaning_text": row[1]["text"]} for row in rows],
                source_ref=source_ref, language=language,
            )
        else:
            variant = DECLARATIONS[declaration]
            headers, rows = _rows(table, *VARIANTS[variant], source_path)
            spec = reference_table_component_spec(
                variant=variant, label=heading.get_text(" ", strip=True),
                headers=headers, rows=rows, source_ref=source_ref, language=language,
            )
        claims.append((spec, table))
    return tuple(claims)
