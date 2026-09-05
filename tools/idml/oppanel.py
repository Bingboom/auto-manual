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
import warnings
from pathlib import Path

Block = tuple[str, str]


class WarrantyGroupingWarning(UserWarning):
    """A recognized warranty-years block could not enter page grouping."""

_LABELS = {
    "on", "off", "on/off", "marche", "arrêt", "arret", "marche/arrêt",
    "encender", "apagar", "encendido", "apagado",
    "オン", "オフ", "开", "关", "开启", "关闭",
    "켜기", "끄기", "켜짐", "꺼짐",
}
_PREREQ = re.compile(
    r"^\*{0,2}(prerequisite|prérequis|prerequis|requisito previo|前提|사전 조건)\*{0,2}\s*[::]",
    re.I,
)
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
# De-templated preface language tags: the shared template uses
# \HBLangTagLine{FR}{IMPORTANT}; flattened review pages carry
# "**FR IMPORTANT**" (first block may omit the language prefix).
_FLAT_LANGTAG = re.compile(r"^\*\*(?:([A-Z]{2})\s+)?(IMPORTANT\w*)\*\*$")
# Warranty-period cells: "**3 YEARS** **Standard Warranty** <copy>".
# The shared semantic container is language-neutral, while the visible unit is
# deliberately retained for editable IDML copy.  Keep the accepted unit set in
# one place so every shared warranty language follows the same fail-closed path.
_WARRANTY_UNIT = r"YEARS?|ANS|AÑOS|JAHRE|ANNI|РОКИ|년|ANOS"
_WARRANTY_SPLIT_CELL = re.compile(
    rf"^\*\*(\d+)\s*({_WARRANTY_UNIT})\*\*\s*\*\*([^*]+)\*\*\s*(.+)$",
    re.IGNORECASE | re.S,
)
_WARRANTY_COMBINED_CELL = re.compile(
    rf"^\*\*(\d+)\s*({_WARRANTY_UNIT})\s+([^*]+)\*\*\s*(.+)$",
    re.IGNORECASE | re.S,
)

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
        return 'SpaceAfter="7"', 7.0
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
        r"(?:\b(\d+)\s*(?:seconds?|secondes?|segundos?|s)\b|(\d+)\s*초)",
        text,
        re.I,
    )
    return f"{match.group(1) or match.group(2)}s" if match else ""


def _special_operation_panel(
    out: list[Block],
    blocks: list[Block],
    index: int,
    operation_copy: dict[str, dict],
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

    # The copy-key clauses admit targets whose art uses non-governed stems
    # (the KR line). A governed stem must never enter the OTHER panel's
    # fuzzy branch: with both semantics registered (the US template order),
    # the LED image would fail the energy shape check and return None,
    # demoting the approved led_light component to a raw image.
    if stem in _ENERGY_SAVING_ART or (
        "energy_saving" in operation_copy and stem not in _LED_LIGHT_ART
    ):
        # h2, intro, then one combined or two separate guidance paragraphs,
        # followed by image + action. Spanish review copy combines its
        # disable/low-power guidance in one paragraph while EN/FR keep two.
        trailing_kinds = [item[0] for item in out[-4:]]
        if trailing_kinds == ["h2", "body", "body", "body"]:
            heading_index = len(out) - 4
        elif [item[0] for item in out[-3:]] == ["h2", "body", "body"]:
            heading_index = len(out) - 3
        else:
            heading_index = -1
        if heading_index < 0 or blocks[index + 1][0] != "body":
            return None
        out[heading_index] = (
            "h2_operation_energy", out[heading_index][1],
        )
        out[heading_index + 1] = (
            "body_operation_energy_intro", out[heading_index + 1][1],
        )
        guidance = [payload for _kind, payload in out[heading_index + 2:]]
        # The approved operation composition starts the Energy + LED page
        # 10.5pt lower than the ordinary continuation-frame top.  Upgrade the
        # governed page break immediately before this localized section; the
        # story renderer turns the suffix into paragraph space after the
        # forced break.  Matching the structural page boundary keeps this
        # language-neutral and avoids title-text contracts.
        for position in range(heading_index - 1, -1, -1):
            if out[position] == ("layout", "page_break"):
                out[position] = ("layout", "page_break:10.5")
                break
        del out[heading_index + 2:]
        action = blocks[index + 1][1].strip()
        source_copy = operation_copy.get("energy_saving", {})
        return (
            "component",
            json.dumps(
                {
                    "kind": "oppanel",
                    "layout": "energy_saving",
                    "image": ref,
                    "guidance": guidance,
                    "action": action,
                    "mode_label": source_copy.get("mode_label", ""),
                    "duration": _duration_label(action),
                },
                ensure_ascii=False,
            ),
        ), 2

    if stem in _LED_LIGHT_ART or (
        "led_light" in operation_copy and stem not in _ENERGY_SAVING_ART
    ):
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
        source_copy = operation_copy.get("led_light", {})
        return (
            "component",
            json.dumps(
                {
                    "kind": "oppanel",
                    "layout": "led_light",
                    "image": ref,
                    "lead": lead,
                    "steps": steps,
                    "sos_label": source_copy.get("sos_label", ""),
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


def _paired_notice_items(notice: dict) -> list[str]:
    """Recover the final list-item boundary collapsed by RST table parsing."""

    texts = [
        str(text).strip()
        for text in notice.get("texts", [])
        if str(text).strip()
    ]
    if len(texts) != 1:
        return texts
    first, separator, final = texts[0].rpartition(". ")
    if not separator or not first.strip() or not final.strip():
        return texts
    return [first.strip() + ".", final.strip()]


def promote_paired_operation_cards(blocks: list[Block]) -> list[Block]:
    """Promote structurally paired operation content into shared cards.

    The target assembly opts into this semantic variant. Detection uses only
    the source block boundary, never a localized heading or caption string.
    """

    promoted: list[Block] = []
    index = 0
    while index < len(blocks):
        kind, payload = blocks[index]
        if kind == "component" and index + 1 < len(blocks):
            next_kind, next_payload = blocks[index + 1]
            try:
                panel = json.loads(payload)
                notice = json.loads(next_payload) if next_kind == "component" else {}
            except (TypeError, json.JSONDecodeError):
                panel, notice = {}, {}
            if (
                isinstance(panel, dict)
                and panel.get("kind") == "oppanel"
                and not panel.get("layout")
                and isinstance(notice, dict)
                and notice.get("kind") == "notice"
            ):
                promoted.append(("component", json.dumps({
                    **panel,
                    "layout": "image_notice",
                    "notice": {
                        **notice,
                        "list": True,
                        "texts": _paired_notice_items(notice),
                    },
                }, ensure_ascii=False)))
                index += 2
                continue
        if (
            kind == "image"
            and index + 1 < len(blocks)
            and blocks[index + 1][0] == "body"
        ):
            promoted.append(("component", json.dumps({
                "kind": "oppanel",
                "layout": "image_caption",
                "image": payload,
                "caption": blocks[index + 1][1],
            }, ensure_ascii=False)))
            index += 2
            continue
        promoted.append((kind, payload))
        index += 1
    return promoted


def promote_image_caption_panels(blocks: list[Block]) -> list[Block]:
    """Compatibility wrapper for the former target-assembly helper."""
    return promote_paired_operation_cards(blocks)


def promote_operation_guidance_stack(
    blocks: list[Block],
    *,
    require_match: bool = False,
) -> list[Block]:
    """Group one complete operation guidance run into the shared outer card.

    The target assembly selects the variant, while the promotion itself uses
    only stable block/component kinds.  Visible copy, language, model, page
    number, and localized headings never participate in routing.
    """

    promoted: list[Block] = []
    index = 0
    matches = 0
    while index < len(blocks):
        run = blocks[index:index + 4]
        if len(run) == 4:
            panel_kind, panel_payload = run[0]
            first_kind, first_payload = run[1]
            body_kind, body_text = run[2]
            second_kind, second_payload = run[3]
            try:
                panel = json.loads(panel_payload) if panel_kind == "component" else {}
                first_notice = (
                    json.loads(first_payload) if first_kind == "component" else {}
                )
                second_notice = (
                    json.loads(second_payload) if second_kind == "component" else {}
                )
            except (TypeError, json.JSONDecodeError):
                panel, first_notice, second_notice = {}, {}, {}
            if (
                isinstance(panel, dict)
                and panel.get("kind") == "oppanel"
                and not str(panel.get("layout") or "").strip()
                and isinstance(first_notice, dict)
                and first_notice.get("kind") == "notice"
                and body_kind in {"body", "body_operation_inter_section"}
                and str(body_text).strip()
                and isinstance(second_notice, dict)
                and second_notice.get("kind") == "notice"
            ):
                promoted.append(("component", json.dumps({
                    **panel,
                    "layout": "image_guidance_stack",
                    "guidance": [
                        {"kind": "notice", "spec": first_notice},
                        {"kind": "body", "text": str(body_text)},
                        {"kind": "notice", "spec": second_notice},
                    ],
                }, ensure_ascii=False)))
                matches += 1
                index += 4
                continue
        promoted.append(blocks[index])
        index += 1
    if require_match and matches == 0:
        raise ValueError(
            "operation guidance_stack requires oppanel + notice + body + notice"
        )
    return promoted


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


def _explicit_warranty_section(
    payload: dict,
    *,
    section_index: int,
) -> Block:
    roles = payload.get("roles")
    blocks = payload.get("blocks")
    if not isinstance(roles, list) or not isinstance(blocks, list):
        raise ValueError("explicit warranty section requires roles and blocks")
    title = ""
    children: list[dict] = []
    years_seen = False
    for block in blocks:
        if not isinstance(block, dict):
            raise ValueError("explicit warranty section block must be an object")
        kind = str(block.get("kind") or "")
        text = str(block.get("payload") or "")
        if kind == "h2" and not title:
            title = text
            continue
        if kind == "table" and "warranty_years" in roles:
            try:
                rows = json.loads(text)
            except (TypeError, json.JSONDecodeError) as exc:
                raise ValueError(
                    "explicit warranty-years table must contain valid rows"
                ) from exc
            if not rows or len(rows) != 1 or len(rows[0]) < 2:
                raise ValueError(
                    "explicit warranty-years table must contain one multi-cell row"
                )
            items = [_parse_warranty_cell(str(cell)) for cell in rows[0]]
            if not all(item is not None for item in items):
                raise ValueError(
                    "explicit warranty-years cells must contain number, unit, "
                    "label, and copy"
                )
            children.append({
                "kind": "component",
                "spec": {"kind": "warrantyyears", "items": items},
            })
            years_seen = True
            continue
        if kind == "component":
            children.append({"kind": "component", "spec": json.loads(text)})
        else:
            children.append({"kind": kind, "text": text})
    if not title:
        raise ValueError("explicit warranty section requires an h2 title")
    if "warranty_years" in roles and not years_seen:
        raise ValueError("explicit warranty-years section requires a marked table")
    return ("component", json.dumps({
        "kind": "warrantysection",
        "title": title,
        "index": section_index,
        "blocks": children,
    }, ensure_ascii=False))


def transform(
    blocks: list[Block],
    *,
    default_langtag_language: str | None = None,
) -> list[Block]:
    out: list[Block] = []
    i = 0
    explicit_warranty_note_pending = False
    explicit_warranty_section_index = 0
    operation_copy: dict[str, dict] = {}
    while i < len(blocks):
        kind, text = blocks[i]
        if kind == "semantic":
            try:
                semantic = json.loads(text)
            except (TypeError, json.JSONDecodeError) as exc:
                raise ValueError("semantic block must contain valid JSON") from exc
            semantic_kind = semantic.get("kind")
            semantic_blocks = semantic.get("blocks")
            if semantic_kind == "operation_panel_copy":
                layout = str(semantic.get("layout") or "").strip()
                if layout not in {"energy_saving", "led_light"}:
                    raise ValueError(
                        "operation_panel_copy requires a supported layout"
                    )
                operation_copy[layout] = semantic
                i += 1
                continue
            if semantic_kind == "warranty_lead":
                if not isinstance(semantic_blocks, list):
                    raise ValueError("explicit warranty lead requires blocks")
                texts = [
                    str(block.get("payload") or "")
                    for block in semantic_blocks
                    if isinstance(block, dict) and block.get("kind") == "body"
                ]
                if not texts:
                    raise ValueError("explicit warranty lead requires body copy")
                out.append(("component", json.dumps({
                    "kind": "warrantylead",
                    "texts": texts,
                }, ensure_ascii=False)))
                explicit_warranty_note_pending = True
                i += 1
                continue
            if semantic_kind == "warranty_section":
                explicit_warranty_section_index += 1
                out.append(_explicit_warranty_section(
                    semantic,
                    section_index=explicit_warranty_section_index,
                ))
                explicit_warranty_note_pending = False
                i += 1
                continue
        if kind == "body" and explicit_warranty_note_pending:
            out.append(("warrantynote", text))
            explicit_warranty_note_pending = False
            i += 1
            continue
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
            language = tag.group(1) if tag else None
            if tag and (language or default_langtag_language):
                out.append(("component", json.dumps(
                    {"kind": "langtag",
                     "lang": language or default_langtag_language,
                     "texts": [tag.group(2)]}, ensure_ascii=False)))
                i += 1
                continue
        special = _special_operation_panel(out, blocks, i, operation_copy)
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
                    following_kind = (
                        "body_operation_inter_section"
                        if _image_stem(text) == "op_main_power"
                        else "body"
                    )
                    out.append((following_kind, following_body))
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
    if (
        has_period_component
        and (has_h1 or has_sections)
        and not (has_h1 and has_sections)
    ):
        missing = [
            marker
            for marker, present in (("h1", has_h1), ("h2", has_sections))
            if not present
        ]
        warnings.warn(
            "warranty grouping skipped: missing " + ", ".join(missing),
            WarrantyGroupingWarning,
            stacklevel=2,
        )
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
