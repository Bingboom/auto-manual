"""Detect the template's operation panels in extracted prose blocks.

The V2.0 master renders operations as bordered panels. Power / AC / DC-USB
use illustration + On/Off rows and an optional prerequisite pill; Energy
Saving and LED use dedicated grey-header and instruction-overlay layouts.
This pass identifies those source runs by governed image identity plus exact
neighbouring block structure and rewrites them into ``oppanel`` specs, without
matching localized section titles.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

Block = tuple[str, str]

_LABELS = {
    "on", "off", "on/off", "marche", "arrêt", "arret", "marche/arrêt",
    "encender", "apagar", "encendido", "apagado",
    "オン", "オフ", "开", "关", "开启", "关闭",
}
_PREREQ = re.compile(
    r"^\*{0,2}(prerequisite|prérequis|prerequis|requisito previo|前提)\*{0,2}\s*[::]",
    re.I,
)
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
# De-templated preface language tags: the shared template uses
# \HBLangTagLine{FR}{IMPORTANT}; flattened review pages carry
# "**FR IMPORTANT**" (first block may omit the language prefix).
_FLAT_LANGTAG = re.compile(r"^\*\*(?:([A-Z]{2})\s+)?(IMPORTANT\w*)\*\*$")
# Warranty-period cells: "**3 YEARS** **Standard Warranty** <copy>".
_WARRANTY_SPLIT_CELL = re.compile(
    r"^\*\*(\d+)\s+(YEARS?|ANS|AÑOS)\*\*\s*\*\*([^*]+)\*\*\s*(.*)$", re.S)
_WARRANTY_COMBINED_CELL = re.compile(
    r"^\*\*(\d+)\s+(YEARS?|ANS|AÑOS)\s+([^*]+)\*\*\s*(.*)$", re.S)

_ENERGY_SAVING_ART = {"op_energy_saving"}
_LED_LIGHT_ART = {"led_light", "op_led_light"}


def operation_story_rhythm(
    kind: str,
    *,
    intro_lines: int | None,
    energy_panel_height: float | None,
    baseline_panel_height: float,
) -> tuple[str | None, float | None]:
    """Return language-neutral paragraph attributes and estimated spacing."""
    if kind == "h2_operation_energy":
        return 'SpaceAfter="7.5"', 7.5
    if kind == "body_operation_energy_intro":
        return 'Leading="8.1" SpaceAfter="7"', 7.0
    if kind != "h2_operation_led":
        return None, None
    extra_intro = max(0, (intro_lines or 0) - 7) * 8.1
    extra_panel = max(
        0.0,
        (energy_panel_height or baseline_panel_height) - baseline_panel_height,
    )
    before = max(0.0, 22.0 - extra_intro - extra_panel)
    return f'SpaceBefore="{before:g}" SpaceAfter="6.5"', before + 6.5


def _image_stem(ref: str) -> str:
    """Return a normalized image stem for structure-first panel matching."""
    return Path(ref.replace("\\", "/")).stem.lower()


def _duration_label(text: str) -> str:
    """Derive the compact reference label from localized action copy."""
    match = re.search(
        r"\b(\d+)\s*(?:seconds?|secondes?|segundos?|s)\b", text, re.I,
    )
    return f"{match.group(1)}s" if match else "3s"


def _special_operation_panel(
    out: list[Block], blocks: list[Block], index: int,
) -> tuple[Block, int] | None:
    """Group Energy Saving / LED artwork with its editable source copy.

    These two V2.0 panels do not use the generic image + On/Off-row carrier.
    Match them by governed art basename and exact neighbouring block shape so
    localized headings never become part of the detection contract.
    """
    kind, ref = blocks[index]
    if kind != "image" or index + 1 >= len(blocks):
        return None
    stem = _image_stem(ref)

    if stem in _ENERGY_SAVING_ART:
        # h2, intro, disable guidance, low-power guidance, image, action.
        if (
            len(out) < 4
            or [item[0] for item in out[-4:]] != ["h2", "body", "body", "body"]
            or blocks[index + 1][0] != "body"
        ):
            return None
        out[-4] = ("h2_operation_energy", out[-4][1])
        out[-3] = ("body_operation_energy_intro", out[-3][1])
        guidance = [out[-2][1], out[-1][1]]
        # The approved operation composition starts the Energy + LED page
        # 10.5pt lower than the ordinary continuation-frame top.  Upgrade the
        # governed page break immediately before this localized section; the
        # story renderer turns the suffix into paragraph space after the
        # forced break.  Matching the structural page boundary keeps this
        # language-neutral and avoids title-text contracts.
        for position in range(len(out) - 5, -1, -1):
            if out[position] == ("layout", "page_break"):
                out[position] = ("layout", "page_break:10.5")
                break
        del out[-2:]
        action = blocks[index + 1][1].strip()
        return (
            "component",
            json.dumps(
                {
                    "kind": "oppanel",
                    "layout": "energy_saving",
                    "image": ref,
                    "guidance": guidance,
                    "action": action,
                    # Reference-layout decorations are language-neutral in
                    # the EN/FR/ES master; the full localized instruction is
                    # still sourced from the IR above.
                    "mode_label": "On/Off",
                    "duration": _duration_label(action),
                },
                ensure_ascii=False,
            ),
        ), 2

    if stem in _LED_LIGHT_ART:
        # h2, lead, image, exactly three newline-separated instructions.
        if (
            len(out) < 2
            or [item[0] for item in out[-2:]] != ["h2", "body"]
            or blocks[index + 1][0] != "body"
        ):
            return None
        steps = [line.strip() for line in blocks[index + 1][1].splitlines()
                 if line.strip()]
        if len(steps) != 3:
            return None
        out[-2] = ("h2_operation_led", out[-2][1])
        lead = out.pop()[1]
        return (
            "component",
            json.dumps(
                {
                    "kind": "oppanel",
                    "layout": "led_light",
                    "image": ref,
                    "lead": lead,
                    "steps": steps,
                },
                ensure_ascii=False,
            ),
        ), 2

    return None


def _label_of(line: str) -> tuple[str, str] | None:
    """Return (label, trailing instruction) when the line starts a row."""
    plain = _BOLD.sub(r"\1", line).strip()
    head, sep, tail = plain.partition(":")
    candidate = (head if sep else plain).strip().lower()
    if candidate in _LABELS:
        return (head if sep else plain).strip(), tail.strip()
    return None


def _parse_rows_and_tail(
    text: str,
) -> tuple[list[tuple[str, str]] | None, str]:
    """Parse operation rows and preserve a structurally marked prose tail.

    Localized RST line blocks are not guaranteed to keep the operation rows
    and the following standby copy as separate IR paragraphs.  Once two
    complete On/Off rows have been found, a new bold field starts ordinary
    full-width prose rather than extending the second row's narrow text
    column.  Continuation lines inside the two operation rows still work as
    before.
    """
    rows: list[tuple[str, str]] = []
    tail: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if tail:
            tail.append(line)
            continue
        started = _label_of(line)
        if started:
            rows.append(started)
        elif rows and not rows[-1][1]:
            rows[-1] = (rows[-1][0], line)
        elif len(rows) >= 2 and re.match(r"^\*\*[^*]+\*\*", line):
            tail.append(line)
        elif rows:
            rows[-1] = (rows[-1][0], rows[-1][1] + " " + line)
        else:
            return None, ""
    if len(rows) < 2:
        return None, ""
    return rows, "\n".join(tail)


def parse_rows(text: str) -> list[tuple[str, str]] | None:
    """Parse an On/Off body into [(label, instruction), ...] or None."""
    rows, _tail = _parse_rows_and_tail(text)
    return rows


def _split_panel_tail(text: str) -> tuple[str, str]:
    """Split the grey standby note from following full-width prose.

    The source line block marks the final line inside the grey note with a
    literal single-star lead.  Any following lines belong below the panel.
    This structural boundary is stable across localized wording and avoids
    squeezing the Energy Saving explanation into the operation artwork.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if re.match(r"^(?:\\\*|\*(?!\*))", line) and index + 1 < len(lines):
            return "\n".join(lines[:index + 1]), "\n".join(lines[index + 1:])
    return "\n".join(lines), ""


def _parse_warranty_cell(text: str) -> dict[str, str] | None:
    match = _WARRANTY_SPLIT_CELL.match(text.strip())
    if match is None:
        match = _WARRANTY_COMBINED_CELL.match(text.strip())
    if match is None:
        return None
    return {
        "number": match.group(1),
        "unit": match.group(2),
        "label": match.group(3).strip(),
        "text": match.group(4).strip(),
    }


def transform(blocks: list[Block]) -> list[Block]:
    out: list[Block] = []
    i = 0
    while i < len(blocks):
        kind, text = blocks[i]
        if kind == "table":
            try:
                rows = text if isinstance(text, list) else ast.literal_eval(text)
            except (ValueError, SyntaxError):
                rows = None
            if rows and len(rows) == 1 and len(rows[0]) >= 2:
                items = [_parse_warranty_cell(cell) for cell in rows[0]]
                if all(item is not None for item in items):
                    out.append(("component", json.dumps(
                        {"kind": "warrantyyears", "items": items},
                        ensure_ascii=False)))
                    i += 1
                    continue
        if kind == "body":
            tag = _FLAT_LANGTAG.match(text.strip())
            if tag:
                out.append(("component", json.dumps(
                    {"kind": "langtag", "lang": tag.group(1) or "EN",
                     "texts": [tag.group(2)]}, ensure_ascii=False)))
                i += 1
                continue
        special = _special_operation_panel(out, blocks, i)
        if special is not None:
            component, consumed = special
            out.append(component)
            i += consumed
            continue
        if kind == "image" and i + 1 < len(blocks) and blocks[i + 1][0] == "body":
            rows, tail = _parse_rows_and_tail(blocks[i + 1][1])
            if rows:
                prereq = ""
                if out and out[-1][0] == "body" and _PREREQ.match(out[-1][1].strip()):
                    prereq = _BOLD.sub(r"\1", out.pop()[1]).strip()
                consumed = 2
                # The prepared RST extractor may split the power panel's
                # standby copy into a second body block after the On/Off
                # rows.  A bold field lead is the structural marker used by
                # the shared templates; fold that block into the panel so
                # the editable grey tail pill stays inside the border.
                if not tail and i + 2 < len(blocks) and blocks[i + 2][0] == "body":
                    candidate = blocks[i + 2][1].strip()
                    if re.match(r"^\*{0,2}[^*\n]+\*{0,2}\s*:", candidate):
                        tail = candidate
                        consumed = 3
                panel_tail, following_body = _split_panel_tail(tail)
                out.append(("component", json.dumps(
                    {"kind": "oppanel", "image": text, "prereq": prereq,
                     "rows": rows, "tail": panel_tail}, ensure_ascii=False)))
                if following_body:
                    out.append(("body", following_body))
                i += consumed
                continue
        out.append((kind, text))
        i += 1
    return _group_warranty_page(_group_charging_emphasis(out))


def _group_charging_emphasis(blocks: list[Block]) -> list[Block]:
    """Preserve the source's standalone pre-charge emphasis semantically.

    The sentence is localized, so the carrier is detected by structure: a
    fully-strong paragraph after introductory body copy and immediately
    before a notice.  No rendered wording or language title is matched here.
    """
    grouped: list[Block] = []
    for index, (kind, text) in enumerate(blocks):
        next_kind = blocks[index + 1][0] if index + 1 < len(blocks) else ""
        previous_kind = blocks[index - 1][0] if index > 0 else ""
        full_strong = re.fullmatch(r"\*\*[^*]+\*\*", text.strip()) is not None
        if (
            kind == "body"
            and previous_kind == "body"
            and full_strong
            and next_kind == "component"
        ):
            try:
                next_spec = json.loads(blocks[index + 1][1])
            except (TypeError, json.JSONDecodeError):
                next_spec = {}
            if next_spec.get("kind") == "notice":
                grouped.append(("component", json.dumps({
                    "kind": "emphasispill",
                    "texts": [text.strip()[2:-2]],
                }, ensure_ascii=False)))
                continue
        grouped.append((kind, text))
    return grouped


def _group_warranty_page(blocks: list[Block]) -> list[Block]:
    """Turn structurally identified warranty prose into editable components."""
    has_h1 = any(kind == "h1" for kind, _text in blocks)
    has_sections = any(kind == "h2" for kind, _text in blocks)
    has_period_component = False
    for kind, payload in blocks:
        if kind != "component":
            continue
        try:
            spec = json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(spec, dict) and spec.get("kind") == "warrantyyears":
            has_period_component = True
            break
    if not (has_h1 and has_sections and has_period_component):
        return blocks

    grouped: list[Block] = []
    index = 0
    lead_seen = False
    i = 0
    while i < len(blocks):
        kind, text = blocks[i]
        if kind == "h1":
            grouped.append((kind, text))
            i += 1
            continue
        if kind == "body" and not lead_seen and text.strip().startswith("**"):
            grouped.append(("component", json.dumps({
                "kind": "warrantylead",
                "texts": [text],
            }, ensure_ascii=False)))
            lead_seen = True
            i += 1
            continue
        if kind == "h2":
            index += 1
            section_blocks: list[dict] = []
            i += 1
            while i < len(blocks) and blocks[i][0] not in {"h1", "h2"}:
                child_kind, child_text = blocks[i]
                if child_kind == "component":
                    spec = json.loads(child_text)
                    section_blocks.append({"kind": "component", "spec": spec})
                else:
                    section_blocks.append({"kind": child_kind, "text": child_text})
                i += 1
            grouped.append(("component", json.dumps({
                "kind": "warrantysection",
                "title": text,
                "index": index,
                "blocks": section_blocks,
            }, ensure_ascii=False)))
            continue
        grouped.append(("warrantynote" if lead_seen else kind, text))
        i += 1
    return grouped
