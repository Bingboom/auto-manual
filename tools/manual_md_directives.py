"""Sphinx directives that compile semantic Markdown into manual components.

The intermediate state between a legacy document and the published look is
*intent*: a cloud export destroys it (a callout becomes a body-less table, a
spec block becomes one long grid, an icon legend loses its header row), and no
heuristic can reliably recover what the author meant. Declare the intent once
and this extension emits exactly the markup the web manual's stylesheet expects.

Authoring, in an ordinary ``.md`` file::

    ```{callout} WARNING
    Do not open the enclosure.

    - bullets work here, unlike inside a table cell
    ```

    ```{spec-table} INPUT PORTS
    1 × AC Input | Charge Mode: 100-120 V~ 60 Hz, 15 A max.
                 | Bypass Mode^①^: 12 A max.
    2 × DC8020 Ports | 11 V-16 V⎓8 A max.
    ```

A blank label continues the previous one, which is how a label spanning two
values is expressed; ``ARG`` becomes the composition's ``aria-label``.

Only a callout body is parsed as full Markdown, so its emphasis, links, and
lists render normally. Table-like directives deliberately accept a small,
escaped inline subset so their column and row-span semantics stay deterministic.
"""
from __future__ import annotations

import re
from typing import Any

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

from tools.component_specs.adapters import web_callout_classes
from tools.component_specs.callout import CALLOUT_VARIANTS, callout_component_spec
from tools.component_specs.spec_table import (
    spec_table_component_spec,
    web_spec_table_projection,
)

SIGNAL_WORDS = ("WARNING", "CAUTION", "NOTE", "TIP", "DANGER", "IMPORTANT", "NOTICE", "ATTENTION")
_SUP_RE = re.compile(r"\^([^\^\s][^\^]{0,24})\^")
_SUB_RE = re.compile(r"~([^~\s][^~]{0,24})~")
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
_LINE_SPLIT = " / "


def _cells(line: str) -> list[str]:
    """Split a manual row while treating an odd ``\\`` run as pipe escape."""
    cells: list[str] = []
    current: list[str] = []
    for character in line:
        if character != "|":
            current.append(character)
            continue
        slash_count = 0
        while current and current[-1] == "\\":
            current.pop()
            slash_count += 1
        current.extend("\\" for _ in range(slash_count // 2))
        if slash_count % 2:
            current.append("|")
            continue
        cells.append("".join(current).strip())
        current = []
    cells.append("".join(current).strip())
    return cells


def _troubleshooting_headers(value: str) -> tuple[str, str]:
    headers = _cells(value)
    if len(headers) != 2 or not all(headers):
        raise ValueError(
            "troubleshooting headers must contain two non-empty cells separated by |"
        )
    return headers[0], headers[1]


def _inline_html(text: str) -> str:
    """Escape, then honour the small inline set a manual cell carries."""
    out = nodes.Text(text).astext()
    out = (
        out.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = _SUP_RE.sub(r"<sup>\1</sup>", out)
    out = _SUB_RE.sub(r"<sub>\1</sub>", out)
    return out


def _image_html(cell: str, *, css_class: str) -> str:
    match = _IMAGE_RE.search(cell)
    if match:
        alt, src = match.group(1), match.group(2)
        return f'<img class="{css_class}" src="{src}" alt="{_inline_html(alt)}"/>'
    return _inline_html(cell)


def _line_block(text: str) -> str:
    """Multi-step cell content as the manual's line block, split on `` / ``."""
    parts = [part.strip() for part in text.split(_LINE_SPLIT) if part.strip()]
    if len(parts) < 2:
        return f"<p>{_inline_html(text)}</p>"
    lines = "".join(f'<div class="line">{_inline_html(part)}</div>' for part in parts)
    return f'<div class="line-block">{lines}</div>'


def _raw(text: str) -> nodes.raw:
    return nodes.raw("", text, format="html")


class _ManualDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec: dict[str, Any] = {}

    @property
    def label(self) -> str:
        return self.arguments[0].strip() if self.arguments else ""

    def rows(self) -> list[list[str]]:
        collected: list[list[str]] = []
        for line in self.content:
            if not line.strip():
                continue
            collected.append(_cells(line))
        return collected

    def aria(self) -> str:
        return f' aria-label="{_inline_html(self.label)}"' if self.label else ""


class CalloutDirective(_ManualDirective):
    """``{callout} LABEL`` — the manual's labelled notice box."""

    option_spec = {"variant": directives.unchanged}

    def run(self) -> list[nodes.Node]:
        label = self.label.upper() or "NOTE"
        declared_variant = str(self.options.get("variant") or "").strip().casefold()
        if declared_variant and declared_variant not in CALLOUT_VARIANTS:
            raise self.error(
                f"unknown callout variant {declared_variant!r}; expected one of "
                + ", ".join(sorted(CALLOUT_VARIANTS))
            )
        language = str(getattr(self.env.config, "language", None) or "und")
        spec = callout_component_spec(
            label=label,
            body="\n".join(self.content),
            source_ref=f"{self.env.docname}:{self.lineno}",
            language=language,
            variant=declared_variant or None,
        )
        classes = web_callout_classes(spec)
        container = nodes.container()
        container += _raw(
            f'<table class="{classes["table"]}"><tbody><tr>'
            f'<td class="{classes["label"]}"><p><strong>{_inline_html(label)}</strong></p></td>'
            f'<td class="{classes["body"]}">'
        )
        body = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, body)
        container += body.children
        container += _raw("</td></tr></tbody></table>")
        return [container]


class SpecTableDirective(_ManualDirective):
    """``{spec-table} SECTION`` — label/value rows, blank label continues the previous."""

    def run(self) -> list[nodes.Node]:
        language = str(getattr(self.env.config, "language", None) or "und")
        spec = spec_table_component_spec(
            section_title=self.label,
            rows=self.rows(),
            source_ref=f"{self.env.docname}:{self.lineno}",
            language=language,
        )
        projection = web_spec_table_projection(spec)
        body: list[str] = []
        for group in projection["groups"]:
            label = str(group["label"])
            values = group["values"]
            span = int(group["label_rowspan"])
            rowspan = f' rowspan="{span}"' if span > 1 else ""
            body.append(
                f'<tr><th class="{projection["label_classes"]}" scope="row"{rowspan}>'
                f"{_inline_html(label)}</th>"
                f'<td class="{projection["value_classes"]}">'
                f'{_inline_html(str(values[0]["text"]))}</td>'
                + "</tr>"
            )
            for value in values[1:]:
                body.append(
                    "<tr>"
                    f'<td class="{projection["value_classes"]}">'
                    f'{_inline_html(str(value["text"]))}</td>'
                    + "</tr>"
                )
        return [
            _raw(
                f'<figure{self.aria()} class="{projection["composition_class"]}">'
                f'<table class="{projection["table_classes"]}">'
                '<colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup>'
                f'<tbody>{"".join(body)}</tbody></table></figure>'
            )
        ]


class TroubleshootingDirective(_ManualDirective):
    """``{troubleshooting}`` — fault code beside its corrective measures."""

    option_spec = {"headers": _troubleshooting_headers}

    def run(self) -> list[nodes.Node]:
        header = self.options.get("headers") or (
            "Error Code",
            "Corrective Measures",
        )
        rows = "".join(
            f'<tr><td class="hb-troubleshooting-code">{_inline_html(row[0])}</td>'
            f'<td class="hb-troubleshooting-measures">{_line_block(row[1] if len(row) > 1 else "")}</td></tr>'
            for row in self.rows()
        )
        head = "".join(f'<th class="head">{_inline_html(cell)}</th>' for cell in header)
        return [
            _raw(
                f'<figure{self.aria()} class="hb-troubleshooting-composition">'
                '<table class="manual-table hb-troubleshooting-table">'
                '<colgroup><col class="hb-troubleshooting-col-code"/>'
                '<col class="hb-troubleshooting-col-measures"/></colgroup>'
                f"<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></figure>"
            )
        ]


class LcdIconsDirective(_ManualDirective):
    """``{lcd-icons}`` — index, icon, name, behaviour rows."""

    def run(self) -> list[nodes.Node]:
        rows = ""
        for row in self.rows():
            padded = row + [""] * (4 - len(row))
            number, icon, name, description = padded[:4]
            rows += (
                f'<tr><td class="hb-lcd-number">{_inline_html(number)}</td>'
                f'<td class="hb-lcd-icon">{_image_html(icon, css_class="hb-lcd-icon-art")}</td>'
                f'<td class="hb-lcd-name">{_inline_html(name)}</td>'
                f'<td class="hb-lcd-description">{_line_block(description)}</td></tr>'
            )
        return [
            _raw(
                f'<figure{self.aria()} class="hb-lcd-table-composition">'
                '<table class="manual-table hb-lcd-icon-table">'
                '<colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/>'
                '<col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup>'
                f"<tbody>{rows}</tbody></table></figure>"
            )
        ]


class SymbolsDirective(_ManualDirective):
    """``{symbols}`` — pictogram legend, laid out as the manual's paired panels."""

    def run(self) -> list[nodes.Node]:
        rows = self.rows()
        half = (len(rows) + 1) // 2
        panels = []
        for chunk in (rows[:half], rows[half:]):
            if not chunk:
                continue
            body = "".join(
                f'<tr><td class="hb-symbol-icon">{_image_html(row[0], css_class="hb-symbol-art")}</td>'
                f'<td class="hb-symbol-meaning">{_inline_html(row[1] if len(row) > 1 else "")}</td></tr>'
                for row in chunk
            )
            panels.append(
                '<div class="hb-symbol-panel">'
                '<table class="manual-table hb-symbol-panel-table">'
                f"<tbody>{body}</tbody></table></div>"
            )
        return [
            _raw(
                f'<figure{self.aria()} class="hb-symbol-pair-composition">'
                f'<div class="hb-symbol-pair-grid">{"".join(panels)}</div></figure>'
            )
        ]


def _merged_row(
    grid: list[list[str]],
    index: int,
    *,
    columns: int = 2,
    classes: tuple[str, ...] = (),
    renderer=None,
) -> str:
    """One table row where a blank cell means "merge with the cell above".

    That is what the source convention expresses whenever one column has fewer
    entries than another — a state covering three actions, a condition covering
    two exceptions. A pipe table has no rowspan, so every such blank renders as
    an empty box instead; this is the defect that fixes.
    """
    render = renderer or (lambda column, text: _inline_html(text))
    cells = ""
    for column in range(columns):
        value = grid[index][column] if column < len(grid[index]) else ""
        if not value.strip() and index > 0:
            continue  # absorbed by the rowspan of the cell above
        span = 1
        while index + span < len(grid) and not (
            grid[index + span][column] if column < len(grid[index + span]) else ""
        ).strip():
            span += 1
        rowspan = f' rowspan="{span}"' if span > 1 else ""
        css = f' class="{classes[column]}"' if column < len(classes) and classes[column] else ""
        cells += f"<td{css}{rowspan}>{render(column, value)}</td>"
    return f"<tr>{cells}</tr>"


class ComparisonDirective(_ManualDirective):
    """``{comparison} LEFT | RIGHT`` — a does / does-not table."""

    def run(self) -> list[nodes.Node]:
        headers = _cells(self.label) if self.label else ["", ""]
        headers += [""] * (2 - len(headers))
        grid = [(row + ["", ""])[:2] for row in self.rows()]
        rows = "".join(_merged_row(grid, index) for index in range(len(grid)))
        return [
            _raw(
                '<figure class="hb-auto-resume-composition">'
                '<table class="manual-table hb-auto-resume-table"><thead><tr>'
                f'<th class="head hb-auto-resume-left">{_inline_html(headers[0])}</th>'
                f'<th class="head hb-auto-resume-right">{_inline_html(headers[1])}</th>'
                f"</tr></thead><tbody>{rows}</tbody></table></figure>"
            )
        ]


class ManualTableDirective(_ManualDirective):
    """``{manual-table} LABEL`` — any-width table where a blank cell merges upward.

    The escape hatch for a shape with no dedicated component: keeps the manual's
    table styling and, unlike a pipe table, can express the row spans the source
    is asking for. ``:headers:`` supplies a header row.
    """

    option_spec = dict(_ManualDirective.option_spec, headers=directives.unchanged)

    def run(self) -> list[nodes.Node]:
        grid = self.rows()
        columns = max((len(row) for row in grid), default=0)
        body = "".join(
            _merged_row(grid, index, columns=columns) for index in range(len(grid))
        )
        head = ""
        if self.options.get("headers"):
            cells = _cells(self.options["headers"])
            head = (
                "<thead><tr>"
                + "".join(f'<th class="head">{_inline_html(cell)}</th>' for cell in cells)
                + "</tr></thead>"
            )
        return [
            _raw(
                f'<table class="manual-table"{self.aria()}>{head}<tbody>{body}</tbody></table>'
            )
        ]


class LcdModeDirective(_ManualDirective):
    """``{lcd-mode} ![alt](art.png)`` — screen art beside a state/action matrix.

    Rows are ``state | action | detail``; a blank state merges into the state
    above, which is how one display mode covers several actions.
    """

    def run(self) -> list[nodes.Node]:
        grid = [(row + ["", "", ""])[:3] for row in self.rows()]
        classes = ("hb-lcd-mode-state", "hb-lcd-mode-action", "hb-lcd-mode-detail")
        body = "".join(
            _merged_row(grid, index, columns=3, classes=classes) for index in range(len(grid))
        )
        art = ""
        if self.label:
            art = (
                '<div class="hb-lcd-mode-art-panel">'
                f'{_image_html(self.label, css_class="hb-lcd-mode-art")}</div>'
            )
        return [
            _raw(
                '<figure class="hb-lcd-mode-composition">'
                f"{art}"
                '<div class="hb-lcd-mode-table-panel">'
                '<table class="manual-table hb-lcd-mode-table">'
                f"<tbody>{body}</tbody></table></div></figure>"
            )
        ]


DIRECTIVES = {
    "callout": CalloutDirective,
    "spec-table": SpecTableDirective,
    "troubleshooting": TroubleshootingDirective,
    "lcd-icons": LcdIconsDirective,
    "symbols": SymbolsDirective,
    "comparison": ComparisonDirective,
    "manual-table": ManualTableDirective,
    "lcd-mode": LcdModeDirective,
}


def setup(app: Any) -> dict[str, Any]:
    for name, directive in DIRECTIVES.items():
        app.add_directive(name, directive)
    return {"version": "1.0", "parallel_read_safe": True, "parallel_write_safe": True}
