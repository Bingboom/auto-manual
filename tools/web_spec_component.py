"""Project explicitly declared specification HTML through HB-TABLE-SPEC.

Source nodes retain rich inline copy; the public ComponentSpec adapter owns
grouping and classes. No filename, target, title vocabulary or artwork grant
is evidence that an ordinary table is a specification component.
"""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.component_specs.model import ComponentSpecError
from tools.component_specs.spec_table import (
    spec_table_component_spec,
    web_spec_table_projection,
)
from tools.component_specs.web_source import superscript_circled_references


def _source_rows(
    table: Tag, *, source_ref: str, error_type: type[Exception]
) -> list[list[Tag]]:
    """Decode existing HTML spans, without discarding or manufacturing cells."""
    if table.find("thead") or table.find("table") or len(table.find_all("tbody")) != 1:
        raise error_type(
            f"{source_ref}: specification requires one headerless table body"
        )
    rows = [
        row.find_all(["th", "td"], recursive=False)
        for row in table.select("tbody > tr")
    ]
    remaining = 0
    for cells in rows:
        if any(str(cell.get("colspan", "1")) != "1" for cell in cells):
            raise error_type(f"{source_ref}: specification cells cannot span columns")
        if len(cells) == 2 and remaining == 0:
            try:
                span = int(str(cells[0].get("rowspan", "1")))
            except ValueError as exc:
                raise error_type(
                    f"{source_ref}: invalid specification label rowspan"
                ) from exc
            if span < 1:
                raise error_type(
                    f"{source_ref}: specification label rowspan must be positive"
                )
            remaining = span - 1
        elif len(cells) == 1 and remaining > 0:
            remaining -= 1
        else:
            raise error_type(
                f"{source_ref}: specification lost its two-column row geometry"
            )
        if str(cells[-1].get("rowspan", "1")) != "1":
            raise error_type(f"{source_ref}: specification values cannot span rows")
    if not rows or remaining:
        raise error_type(
            f"{source_ref}: specification has missing rows for its label span"
        )
    return rows


def _add_classes(tag: Tag, classes: str) -> None:
    tag["class"] = list(dict.fromkeys([*tag.get("class", []), *classes.split()]))


def transform_specification_tables(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    language: str | None,
    error_type: type[Exception],
) -> bool:
    """Render declared sections anywhere; return whether a section was found."""
    headings = soup.select("h2.hb-spec-section")
    for index, heading in enumerate(headings):
        source_ref = f"{source_path}#specification-{index + 1}"
        title = heading.select_one(".hb-spec-section-text")
        if title is None:
            raise error_type(
                f"{source_ref}: specification heading lost its localized title span"
            )
        table = heading.find_next_sibling()
        if (
            not isinstance(table, Tag)
            or table.name != "table"
            or not {"hb-spec-table", "manual-spec-table"}.intersection(
                table.get("class", [])
            )
        ):
            raise error_type(
                f"{source_ref}: declared specification must be followed by its governed table"
            )
        source_rows = _source_rows(table, source_ref=source_ref, error_type=error_type)
        try:
            spec = spec_table_component_spec(
                section_title=title.get_text(" ", strip=True),
                rows=[
                    (
                        cells[0].get_text("\n", strip=True) if len(cells) == 2 else "",
                        cells[-1].get_text("\n", strip=True),
                    )
                    for cells in source_rows
                ],
                source_ref=source_ref,
                language=str(table.get("lang") or language or "und"),
            )
            projection = web_spec_table_projection(spec)
        except ComponentSpecError as exc:
            raise error_type(f"{source_ref}: {exc}") from exc

        # Only the declared decorative marker goes away. Links/emphasis and
        # any other authored heading content stay in the document outline.
        for bullet in heading.select(".hb-spec-bullet"):
            bullet.decompose()
        title.unwrap()
        heading["class"] = [
            value for value in heading.get("class", []) if value != "hb-spec-section"
        ]
        if not heading["class"]:
            del heading["class"]

        for colgroup in table.find_all("colgroup", recursive=False):
            colgroup.decompose()
        colgroup = soup.new_tag("colgroup")
        for role in ("label", "value"):
            colgroup.append(soup.new_tag("col", attrs={"class": f"hb-spec-col-{role}"}))
        table.insert(0, colgroup)
        table.attrs.pop("style", None)
        _add_classes(table, projection["table_classes"])

        row_index = 0
        for group in projection["groups"]:
            label = source_rows[row_index][0]
            label.name = "th"
            label["scope"] = "row"
            label.attrs.pop("style", None)
            _add_classes(label, projection["label_classes"])
            span = group["label_rowspan"]
            if span > 1:
                label["rowspan"] = str(span)
            superscript_circled_references(soup, label)
            for offset, _value in enumerate(group["values"]):
                cells = source_rows[row_index + offset]
                if offset and len(cells) == 2:
                    # The registered blank-label continuation now has a real
                    # rowspan; only its empty placeholder cell is removed.
                    cells[0].decompose()
                value = cells[-1]
                value.name = "td"
                value.attrs.pop("style", None)
                _add_classes(value, projection["value_classes"])
                superscript_circled_references(soup, value)
            row_index += span

        composition = soup.new_tag(
            "figure",
            attrs={
                "class": projection["composition_class"],
                "aria-label": str(spec.slot("section_title").content),
            },
        )
        table.replace_with(composition)
        composition.append(table)
    return bool(headings)
