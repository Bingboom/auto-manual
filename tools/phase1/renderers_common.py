#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re

VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_\-]+)\s*\}\}")


def apply_vars(text: str, vars_map: dict[str, str]) -> str:
    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        return vars_map.get(key, m.group(0))

    return VAR_PATTERN.sub(repl, text or "")


def rst_escape(s: str) -> str:
    return (s or "").replace("\u00a0", " ").strip()


def latex_arg_escape(text: str) -> str:
    text = rst_escape(text)
    # Keep escaping centralized: all user-provided CSV text must be safe in LaTeX args.
    mapping = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "%": r"\%",
        "_": r"\_",
        "#": r"\#",
        "&": r"\&",
        "$": r"\$",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(mapping.get(ch, ch) for ch in text)


def html_escape(text: str) -> str:
    import html as _html

    return _html.escape(rst_escape(text), quote=True)


def render_latex_cmd(cmd: str, text: str) -> str:
    text = latex_arg_escape(text)
    return "\n".join(
        [
            ".. raw:: latex",
            "",
            f"      \\{cmd}{{{text}}}",
            "",
        ]
    )


def render_bullet_rst(text: str) -> str:
    """
    Supports '\\n' in CSV.
    Sub-lines starting with '- ' become nested bullets.
    """
    text = rst_escape(text)
    parts = text.split("\\n")
    head = parts[0].strip()
    lines = [f"- {head}"]
    for p in parts[1:]:
        p = p.strip()
        if not p:
            continue
        if p.startswith("- "):
            lines.append(f"  {p}")
        else:
            lines.append(f"  {p}")
    return "\n".join(lines)


def build_list_block(rows: list[dict[str, str]]) -> str:
    lines = ("\n".join(render_bullet_rst(r["text"]) for r in rows)).splitlines()
    if not lines:
        return "\n"

    # The template already contributes three spaces before the placeholder.
    # Keep the first list line unindented here, then indent all following lines.
    first, *rest = lines
    normalized = [first]
    for line in rest:
        normalized.append(("   " + line) if line.strip() else line)
    return "\n".join(normalized) + "\n"


def render_lead_html(text: str) -> str:
    return f'<p class="hb-lead">{html_escape(text)}</p>'


def render_list_html(rows: list[dict[str, str]]) -> str:
    items: list[str] = []
    for r in rows:
        raw = rst_escape(r["text"])
        parts = raw.split("\\n")
        head = html_escape(parts[0])
        li_lines = [head]
        sub_items = []
        for p in parts[1:]:
            p = p.strip()
            if not p:
                continue
            if p.startswith("- "):
                sub_items.append(f"<li>{html_escape(p[2:])}</li>")
            else:
                li_lines.append(html_escape(p))
        li_html = "<br/>".join(li_lines)
        if sub_items:
            li_html += '<ul class="hb-sublist">' + "".join(sub_items) + "</ul>"
        items.append(f"<li>{li_html}</li>")
    return '<ul class="hb-list">' + "".join(items) + "</ul>"


def _enabled(v: str) -> bool:
    return (v or "1").strip().lower() in {"1", "true"}


def _scope_allows(scope: str, sku_id: str) -> bool:
    value = (scope or "").strip()
    if not (sku_id or "").strip():
        return True
    if not value or value.upper() == "ALL":
        return True
    allowed = {x.strip() for x in value.split("|") if x.strip()}
    return sku_id in allowed


def split_spec_lines(text: str) -> list[str]:
    raw = rst_escape(text).replace("\\n", "\n")
    parts = [rst_escape(x) for x in raw.splitlines() if rst_escape(x)]
    return parts or [""]


def spec_latex_escape(text: str) -> str:
    # Keep special glyphs renderable on environments where brand fonts miss unicode glyphs.
    special = {
        "\u2460": r"\HBSpecMarkerOne{}",
        "\u2461": r"\HBSpecMarkerTwo{}",
        "*": r"\HBSpecMarkerAsterisk{}",
    }
    base = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "%": r"\%",
        "_": r"\_",
        "#": r"\#",
        "&": r"\&",
        "$": r"\$",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    out: list[str] = []
    for ch in rst_escape(text):
        if ch in special:
            out.append(special[ch])
        else:
            out.append(base.get(ch, ch))
    return "".join(out)


def spec_latex_cell(text: str) -> str:
    parts = split_spec_lines(text)
    escaped = [spec_latex_escape(x) for x in parts if x]
    return r" \newline ".join(escaped) if escaped else ""


def raw_latex_block(lines: list[str]) -> str:
    body = "\n".join(f"   {x}" if x else "   " for x in lines)
    return f".. raw:: latex\n\n{body}\n\n"
