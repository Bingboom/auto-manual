"""Natural flow buffering for ordinary IDML prose pages."""
from __future__ import annotations

import json
import re
from collections.abc import Collection
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .asset_contracts import (
    APP_PAIRING_PANEL_ASSET_URI,
    is_je1000f_us_app_reference_plan_page,
)
from .control_labels import (
    approved_app_control_labels,
    matches_base_label_block,
)

Block = tuple[str, str]
EmitProse = Callable[[str, str, list[Block], int], None]
SlugStem = Callable[[str], str]
EstimatePages = Callable[[list[Block], int], int]


@dataclass
class ProseFlowBuffer:
    """Collect consecutive prose pages until a hard layout boundary appears."""

    items: list[tuple[str, list[Block], int]] = field(default_factory=list)

    def add(self, stem: str, blocks: list[Block], columns: int = 1) -> None:
        self.items.append((stem, blocks, columns))

    def flush(self, emit: EmitProse, slug_stem: SlugStem,
              page_plan: dict | None = None,
              estimate_pages: EstimatePages | None = None,
              dedicated_stems: Collection[str] = (),
              *,
              respect_page_plan: bool = True) -> bool:
        if not self.items:
            return False
        items = self._items_with_approved_splits(page_plan)
        planned_starts = {
            Path(entry["source_path"]).stem: entry.get("latex_start_page")
            for entry in (page_plan or {}).get("pages", [])
        }
        planned_groups = {
            Path(entry["source_path"]).stem: (
                entry.get("composition_id") or entry.get("latex_start_page")
            )
            for entry in (page_plan or {}).get("pages", [])
        }
        explicit_plan = (page_plan or {}).get("plan_source") == "approved-reference"
        batches: list[list[tuple[str, list[Block], int]]] = []
        for item in items:
            key = planned_groups.get(item[0]) if respect_page_plan else None
            dedicated_boundary = (
                item[0] in dedicated_stems
                or bool(batches and batches[-1][-1][0] in dedicated_stems)
            )
            if (not batches or dedicated_boundary
                    or (respect_page_plan and page_plan is not None
                        and planned_groups.get(batches[-1][0][0]) != key)):
                batches.append([])
            batches[-1].append(item)
        index = 0
        while estimate_pages and not explicit_plan and index + 1 < len(batches):
            if any(
                stem in dedicated_stems
                for batch in batches[index:index + 2]
                for stem, _, _ in batch
            ):
                index += 1
                continue
            start = (
                planned_starts.get(batches[index][0][0])
                if respect_page_plan else None
            )
            next_start = (
                planned_starts.get(batches[index + 1][0][0])
                if respect_page_plan else None
            )
            blocks, columns = self._batch_content(batches[index])
            if start and next_start and estimate_pages(blocks, columns) > next_start - start:
                batches[index].extend(batches.pop(index + 1))
            else:
                index += 1
        for batch in batches:
            self._emit_batch(batch, emit, slug_stem)
        self.items.clear()
        return True

    def _items_with_approved_splits(
        self,
        page_plan: dict | None,
    ) -> list[tuple[str, list[Block], int]]:
        items = [(stem, list(blocks), columns) for stem, blocks, columns in self.items]
        if (page_plan or {}).get("plan_source") != "approved-reference":
            return items
        entries = {
            Path(entry["source_path"]).stem: entry
            for entry in (page_plan or {}).get("pages", [])
        }
        items = [
            (
                stem,
                align_app_second_page(blocks, page_plan, stem),
                columns,
            )
            for stem, blocks, columns in items
        ]
        items = [
            (
                stem,
                promote_reference_figures(blocks, page_plan, stem),
                columns,
            )
            for stem, blocks, columns in items
        ]
        items = [
            (
                stem,
                align_troubleshooting_heading(
                    blocks,
                    _planned_page_language(page_plan, stem),
                ),
                columns,
            )
            for stem, blocks, columns in items
        ]
        for index in range(len(items)):
            stem, blocks, columns = items[index]
            rule = entries.get(stem, {}).get("flow_split")
            if not isinstance(rule, dict):
                continue
            at_kind = rule["at_kind"]
            occurrence = int(rule["occurrence"])
            tail_composition = rule["tail_composition_id"]
            seen = 0
            split_at = None
            for block_index, (kind, _payload) in enumerate(blocks):
                if kind == at_kind:
                    seen += 1
                    if seen == occurrence:
                        split_at = block_index
                        break
            target_index = next((
                candidate for candidate in range(index + 1, len(items))
                if entries.get(items[candidate][0], {}).get("composition_id")
                == tail_composition
            ), None)
            if split_at is None or target_index is None:
                raise ValueError(f"approved flow split cannot be applied for {stem}")
            items[index] = (stem, blocks[:split_at], columns)
            target_stem, target_blocks, target_columns = items[target_index]
            items[target_index] = (
                target_stem,
                blocks[split_at:] + target_blocks,
                target_columns,
            )
        items = _apply_single_page_fr_ups_callout_widths(items, entries)
        return _move_car_notice_to_storage(items, page_plan)

    @staticmethod
    def _batch_content(items: list[tuple[str, list[Block], int]]) -> tuple[list[Block], int]:
        from . import oppanel as _oppanel
        return (_oppanel.transform(
            [block for _, page_blocks, _ in items for block in page_blocks]), items[0][2])

    @staticmethod
    def _emit_batch(items: list[tuple[str, list[Block], int]],
                    emit: EmitProse, slug_stem: SlugStem) -> None:
        stems = [stem for stem, _, _ in items]
        blocks, columns = ProseFlowBuffer._batch_content(items)
        if len(stems) == 1:
            sid = "st_" + slug_stem(stems[0])
            title = stems[0]
        else:
            sid = "st_flow_" + slug_stem("_".join(stems[:2]))
            title = " + ".join(stems)
        emit(sid, title, blocks, columns)


def idml_page_estimator(writer_cls, params, bundle_root) -> EstimatePages:
    """Build a side-effect-isolated estimator with the production story renderer."""
    def estimate(blocks: list[Block], columns: int) -> int:
        probe = writer_cls(params)
        _, height = probe.add_prose_story("st_probe", "probe", blocks, bundle_root)
        return probe.pages_for_height(height / max(1, columns))
    return estimate


def _language_code(value: object) -> str:
    """Normalize an IETF/underscore locale to its primary language subtag."""
    normalized = str(value or "").strip().lower().replace("_", "-")
    return normalized.split("-", 1)[0]


def _planned_page_language(
    page_plan: dict | None,
    stem: str | None,
) -> str | None:
    """Return approved page metadata language for an exact source stem."""
    if (
        (page_plan or {}).get("plan_source") != "approved-reference"
        or not stem
    ):
        return None
    target_stem = Path(stem).stem
    for entry in (page_plan or {}).get("pages", []):
        source_path = entry.get("source_path")
        if not source_path or Path(str(source_path)).stem != target_stem:
            continue
        language = _language_code(entry.get("language"))
        return language if language in {"en", "fr", "es"} else None
    return None


def operation_language(
    blocks: list[Block],
    page_plan: dict | None = None,
    stem: str | None = None,
) -> str | None:
    """Resolve EN/FR/ES from page metadata, then legacy table headers.

    Approved page-plan metadata is the authoritative locale contract and does
    not change when an editor revises visible table headings. Header inference
    remains as a compatibility fallback for unapproved and older call sites.
    """
    planned = _planned_page_language(page_plan, stem)
    if planned is not None:
        return planned
    headers = {
        ("buttons", "operation", "function"): "en",
        ("boutons", "utilisation", "fonction"): "fr",
        ("botones", "operación", "función"): "es",
    }
    for kind, payload in blocks:
        if kind != "table":
            continue
        try:
            rows = json.loads(payload) if isinstance(payload, str) else payload
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(rows, list) or not rows or len(rows[0]) < 3:
            continue
        header = tuple(
            str(cell).replace("**", "").strip().casefold()
            for cell in rows[0][:3]
        )
        if header in headers:
            return headers[header]
    return None


_OPERATION_FINAL_FRAME_X_OFFSETS = {
    "en": -6.82,
    "fr": -2.57,
    "es": -6.18,
}


def operation_final_frame_x_offset(language: str | None) -> float:
    """Return the approved final operation-page host-frame translation."""
    return _OPERATION_FINAL_FRAME_X_OFFSETS.get(language or "", 0.0)


def align_trouble_table(blocks: list[Block], page_plan: dict | None,
                        stem: str) -> list[Block]:
    """Start a long troubleshooting table on its second reference page."""
    from .latex_page_plan import planned_span
    if planned_span(page_plan, [stem], 1) <= 1:
        return blocks
    aligned = list(blocks)
    table_index = next((i for i, block in enumerate(aligned) if block[0] == "table"), None)
    if table_index is not None:
        aligned.insert(table_index, ("layout", "table_next_page"))
    return aligned


def align_troubleshooting_heading(
    blocks: list[Block],
    language: str | None,
) -> list[Block]:
    """Apply the approved locale rhythm before a troubleshooting section.

    The storage copy immediately before the shared table has different depth
    in EN, FR, and ES.  A semantic layout marker keeps that reviewed spacing
    out of translated headings and lets the story renderer consume the same
    component token for all three languages.
    """
    if language not in {"en", "fr", "es"}:
        return blocks
    header = ""
    for kind, payload in blocks:
        if kind != "table":
            continue
        try:
            rows = json.loads(payload) if isinstance(payload, str) else payload
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(rows, list) and rows and rows[0]:
            header = str(rows[0][0]).strip().casefold()
            break
    trouble_headers = {
        "error code", "code d'erreur", "code d’erreur",
        "código de fallo", "codigo de fallo",
        "código de error", "codigo de error",
    }
    if header not in trouble_headers:
        return blocks
    aligned = list(blocks)
    heading_index = next((
        index for index, (kind, _payload) in enumerate(aligned)
        if kind == "h1"
    ), None)
    if heading_index is not None:
        aligned.insert(
            heading_index,
            ("layout", f"trouble_h1_before:{language}"),
        )
    return aligned


def apply_troubleshooting_h1_rhythm(
    xml: str,
    params: dict[str, tuple[str, str]],
    language: str,
) -> str:
    """Apply the locale token carried by a semantic troubleshooting marker."""
    from .params import param_pt

    before = param_pt(
        params,
        f"lang_{language}_idml_trouble_heading_space_before",
        0.0,
    )
    return xml.replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange SpaceBefore="{before:g}" ',
        1,
    )


def align_operation_tail(blocks: list[Block], page_plan: dict | None,
                         stem: str) -> list[Block]:
    """Apply the approved four-page operation section boundaries."""
    from .latex_page_plan import planned_span
    if "operation_guide" not in stem or planned_span(page_plan, [stem], 1) < 4:
        return blocks
    aligned = list(blocks)
    h2_indices = [index for index, block in enumerate(aligned) if block[0] == "h2"]
    if (page_plan or {}).get("plan_source") == "approved-reference":
        # Reference pages: POWER+AC | DC/USB | Energy+LED | Resume+LCD+Keys.
        language = operation_language(blocks, page_plan, stem) or "en"
        resume_top_gap = {"en": 15.7, "fr": 8.1, "es": 9.3}[language]
        for ordinal in reversed((3, 4, 6)):
            if len(h2_indices) >= ordinal:
                marker = (
                    f"page_break:{resume_top_gap:g}"
                    if ordinal == 6 else "page_break"
                )
                aligned.insert(h2_indices[ordinal - 1], ("layout", marker))
    elif h2_indices:
        # Legacy measured plans only guaranteed that the final section started
        # on page four; preserve that behavior for unapproved targets.
        aligned.insert(h2_indices[-1], ("layout", "page_break"))
    return aligned


def align_charging_car_page(blocks: list[Block], page_plan: dict | None,
                            stem: str) -> list[Block]:
    """Start page two at the second solar figure in approved methods.

    The reference's first methods page contains AC charging plus the first
    solar figure.  Its second page continues with the adapter figure and then
    the car section; forcing the car heading itself to a new page would make
    the enlarged, reference-scale solar art overset the two-page composition.
    """
    from .latex_page_plan import planned_span
    if (
        "charging_methods" not in stem
        or (page_plan or {}).get("plan_source") != "approved-reference"
        or planned_span(page_plan, [stem], 1) < 2
    ):
        return blocks
    aligned = list(blocks)
    image_indices = [index for index, block in enumerate(aligned) if block[0] == "image"]
    if len(image_indices) >= 2:
        split_at = image_indices[1]
        marker = ("layout", "page_break:14.4")
        if split_at == 0 or aligned[split_at - 1] != marker:
            aligned.insert(split_at, marker)
    return aligned


def align_app_second_page(blocks: list[Block], page_plan: dict | None,
                          stem: str) -> list[Block]:
    """Start every approved localized App composition at the post-pairing note.

    English, French, and Spanish share the same physical reference split:
    page one ends after the pairing step and page two starts at its note.  The
    copy itself remains localized and editable; only the page boundary is
    governed here so longer translations cannot pull the note back onto the
    first page.
    """
    from .latex_page_plan import planned_span
    if (
        not is_je1000f_us_app_reference_plan_page(page_plan, stem)
        or planned_span(page_plan, [stem], 1) < 2
    ):
        return blocks
    device_image = next((
        index for index, (kind, payload) in enumerate(blocks)
        if kind == "image"
        and Path(payload).stem.casefold().startswith("add_device")
    ), None)
    if device_image is None:
        return blocks
    notice_index = next((
        index for index in range(device_image + 1, len(blocks))
        if blocks[index][0] == "component"
        and _component_kind(blocks[index][1]) == "notice"
    ), None)
    if notice_index is None:
        return blocks
    aligned = list(blocks)
    marker = ("layout", "page_break:15.1")
    existing_break = next((
        index for index in range(device_image + 1, notice_index)
        if aligned[index][0] == "layout"
        and aligned[index][1].startswith("page_break")
    ), None)
    if existing_break is None:
        aligned.insert(notice_index, marker)
    else:
        aligned[existing_break] = marker
    return aligned


def _component_kind(payload: str) -> str:
    try:
        spec = json.loads(payload)
    except (TypeError, json.JSONDecodeError):
        return ""
    return str(spec.get("kind") or "") if isinstance(spec, dict) else ""


def _referencefigure_block(layout: str, image: str, **values: object) -> Block:
    spec = {
        "kind": "referencefigure",
        "layout": layout,
        "image": image,
        **values,
    }
    return "component", json.dumps(spec, ensure_ascii=False)


def _step_number(text: str) -> str:
    import re

    match = re.match(r"\s*(\d+(?:\.\d+)*)\b", text)
    return match.group(1) if match else ""


def promote_reference_figures(
    blocks: list[Block],
    page_plan: dict | None,
    stem: str,
) -> list[Block]:
    """Promote governed art plus adjacent copy into editable composites.

    Routing uses the approved plan, source-page role, asset basename, and
    neighbouring block shape.  It never matches translated headings or copy.
    """
    if (page_plan or {}).get("plan_source") != "approved-reference":
        return blocks
    is_charging = re.fullmatch(
        r"(?:p\d+_)?08_charging_methods",
        stem.casefold(),
    ) is not None
    is_app = is_je1000f_us_app_reference_plan_page(page_plan, stem)
    if not is_charging and not is_app:
        return blocks

    aligned = list(blocks)
    if is_app:
        # Physical page 21 uses three differently sized callout panels, all
        # inset 10.943 pt from the ordinary story frame.  Apply them by
        # structural notice order so localization never affects routing.
        notice_layouts = (
            {
                "panel_height": 44.737,
                "body_size": 5.8,
                "body_leading": 5.997,
                "pad_tb": 3.1,
                "label_size": 10.0,
                "label_leading": 10.8,
                "body_inset": 3.917,
                "paragraph_space_after": 2.0,
                "unbulleted_first": True,
            },
            {
                "panel_height": 16.221,
                "body_size": 6.0,
                "body_leading": 6.0,
                "pad_tb": 1.5,
                "label_size": 10.0,
                "label_leading": 10.8,
                "body_inset": 5.683,
                "unbulleted_first": True,
            },
            {
                "panel_height": 24.869,
                "body_size": 5.8,
                "body_leading": 5.997,
                "pad_tb": 2.2,
                "label_size": 9.0,
                "label_leading": 9.8,
                "body_inset": 5.42,
            },
        )
        notice_ordinal = 0
        for block_index, (block_kind, block_payload) in enumerate(aligned):
            if block_kind != "component" or _component_kind(block_payload) != "notice":
                continue
            try:
                notice_spec = json.loads(block_payload)
            except (TypeError, json.JSONDecodeError):
                continue
            if notice_ordinal >= len(notice_layouts):
                break
            notice_spec.update({
                "body_width": 300.516,
                "inline_x_offset": 10.943,
                "app_text_frame_safety": True,
                "plate_left": 1.418,
                "label_width": 48.939,
                **notice_layouts[notice_ordinal],
            })
            aligned[block_index] = (
                "component", json.dumps(notice_spec, ensure_ascii=False),
            )
            notice_ordinal += 1
    index = 0
    while index < len(aligned):
        kind, payload = aligned[index]
        if kind != "image":
            index += 1
            continue
        asset_stem = Path(payload).stem.casefold()

        if (
            is_charging
            and asset_stem == "ac_wall"
            and index > 0
            and aligned[index - 1][0] == "body"
        ):
            caption = aligned[index - 1][1]
            aligned[index - 1:index + 1] = [
                _referencefigure_block(
                    "charging_ac", payload, caption=caption,
                )
            ]
            continue

        if (
            is_charging
            and asset_stem == "car_charge"
            and index + 1 < len(aligned)
            and aligned[index + 1][0] == "body"
        ):
            labels = [
                line.strip()
                for line in aligned[index + 1][1].splitlines()
                if line.strip()
            ]
            aligned[index:index + 2] = [
                _referencefigure_block(
                    "charging_car",
                    payload,
                    vehicle=labels[0] if labels else "",
                    note=" ".join(labels[1:]),
                )
            ]
            index += 1
            continue

        if (
            is_app
            and asset_stem == "download"
            and index + 1 < len(aligned)
            and aligned[index + 1][0] == "body"
        ):
            aligned[index:index + 2] = [
                _referencefigure_block(
                    "app_download", payload, copy=aligned[index + 1][1],
                )
            ]
            index += 1
            continue

        if is_app and asset_stem.startswith("add_device"):
            prior_steps = [
                _step_number(text)
                for prior_kind, text in aligned[:index]
                if prior_kind == "body" and _step_number(text)
            ][-2:]
            language = _planned_page_language(page_plan, stem)
            if language is None:
                raise ValueError(
                    f"approved App figure {stem} has no governed page language"
                )
            base_labels, render_labels = approved_app_control_labels(
                page_plan,
                language,
            )
            consume = 1
            if (
                index + 1 < len(aligned)
                and aligned[index + 1][0] == "body"
                and matches_base_label_block(
                    aligned[index + 1][1],
                    base_labels,
                )
            ):
                consume += 1
            aligned[index:index + consume] = [
                _referencefigure_block(
                    "app_add_device",
                    payload,
                    labels_by_role=render_labels,
                    step_labels=prior_steps,
                    control_image=APP_PAIRING_PANEL_ASSET_URI,
                )
            ]
            index += 1
            continue

        if (
            is_app
            and asset_stem.startswith("connect_result")
            and index + 1 < len(aligned)
            and aligned[index + 1][0] == "body"
        ):
            prior_steps = [
                _step_number(text)
                for prior_kind, text in aligned[:index]
                if prior_kind == "body" and _step_number(text)
            ][-3:]
            aligned[index:index + 2] = [
                _referencefigure_block(
                    "app_connect_result",
                    payload,
                    step_labels=prior_steps,
                    reference_note=aligned[index + 1][1],
                )
            ]
            index += 1
            continue
        index += 1
    return aligned


def _apply_single_page_fr_ups_callout_widths(
    items: list[tuple[str, list[Block], int]],
    entries: dict[str, dict],
) -> list[tuple[str, list[Block], int]]:
    """Use natural glyph width for the approved one-page FR UPS composition.

    The governed callout type remains at its contracted point size and
    leading.  Only the legacy 106.9% horizontal expansion is neutralized for
    this dense, single-page French UPS + charging composition.  The source
    and approved plan provide all routing metadata, so EN/ES and unapproved
    flows retain their existing layout.
    """
    grouped: dict[object, list[int]] = {}
    for index, (stem, _blocks, _columns) in enumerate(items):
        composition = entries.get(stem, {}).get("composition_id")
        if composition is not None:
            grouped.setdefault(composition, []).append(index)

    target_indices: set[int] = set()
    for indices in grouped.values():
        group_entries = [entries.get(items[index][0], {}) for index in indices]
        languages = {
            str(entry.get("language") or "").strip().lower()
            for entry in group_entries
        }
        stems = [items[index][0] for index in indices]
        page_counts = {
            int(entry.get("planned_page_count") or entry.get("page_count") or 0)
            for entry in group_entries
        }
        has_ups = any("ups_mode" in stem for stem in stems)
        has_charging_intro = any(
            "charging" in stem and "charging_methods" not in stem
            for stem in stems
        )
        if (
            languages == {"fr"}
            and page_counts == {1}
            and has_ups
            and has_charging_intro
        ):
            target_indices.update(indices)

    adjusted = list(items)
    for index in target_indices:
        stem, blocks, columns = adjusted[index]
        next_blocks: list[Block] = []
        for kind, payload in blocks:
            if kind != "component":
                next_blocks.append((kind, payload))
                continue
            try:
                spec = json.loads(payload)
            except (TypeError, json.JSONDecodeError):
                next_blocks.append((kind, payload))
                continue
            if (
                isinstance(spec, dict)
                and spec.get("kind") == "notice"
                and spec.get("list")
            ):
                spec["body_horizontal_scale"] = 1.0
                payload = json.dumps(spec, ensure_ascii=False)
            next_blocks.append((kind, payload))
        adjusted[index] = (stem, next_blocks, columns)
    return adjusted


def _move_car_notice_to_storage(
    items: list[tuple[str, list[Block], int]],
    page_plan: dict | None,
) -> list[tuple[str, list[Block], int]]:
    """Flow the final car CAUTION into the following storage composition."""
    if (page_plan or {}).get("plan_source") != "approved-reference":
        return items
    methods_index = next((
        index for index, (stem, _blocks, _columns) in enumerate(items)
        if "charging_methods" in stem
    ), None)
    storage_index = next((
        index for index, (stem, _blocks, _columns) in enumerate(items)
        if methods_index is not None
        and index > methods_index
        and "storage_and_maintenance" in stem
    ), None)
    if methods_index is None or storage_index is None:
        return items
    method_stem, method_blocks, method_columns = items[methods_index]
    from .latex_page_plan import planned_span
    if planned_span(page_plan, [method_stem], 1) < 2:
        return items
    h2_indices = [
        index for index, (kind, _payload) in enumerate(method_blocks)
        if kind == "h2"
    ]
    if len(h2_indices) < 2:
        return items
    last_h2 = h2_indices[-1]
    notice_indices = [
        index for index in range(last_h2 + 1, len(method_blocks))
        if method_blocks[index][0] == "component"
        and _component_kind(method_blocks[index][1]) == "notice"
    ]
    if not notice_indices:
        return items
    notice_index = notice_indices[-1]
    if not any(
        kind == "image"
        or (
            kind == "component"
            and _component_kind(payload) == "referencefigure"
        )
        for kind, payload in method_blocks[last_h2:notice_index]
    ):
        return items
    notice = method_blocks[notice_index]
    items[methods_index] = (
        method_stem,
        method_blocks[:notice_index] + method_blocks[notice_index + 1:],
        method_columns,
    )
    storage_stem, storage_blocks, storage_columns = items[storage_index]
    items[storage_index] = (
        storage_stem,
        [notice] + storage_blocks,
        storage_columns,
    )
    return items


def warranty_starts_new_flow(page_plan: dict | None) -> bool:
    """Keep the natural-flow boundary unless a plan owns shared-page grouping.

    A measured plan may deliberately put warranty and App content at the same
    start page.  In that case the plan-aware buffer must group the sources so
    their shared physical span is counted once.
    """
    return page_plan is None


def align_table_xml(xml: str, blocks: list[Block], index: int) -> str:
    """Apply the render-only page-start marker to its following table."""
    if index and blocks[index - 1] == ("layout", "table_next_page"):
        return start_next_page(xml)
    return xml


def start_next_page(xml: str) -> str:
    return xml.replace(
        "<ParagraphStyleRange ", '<ParagraphStyleRange StartParagraph="NextPage" ', 1)


def split_safety_first_page(blocks: list[Block]) -> tuple[list[Block], list[Block]]:
    """Split the V2.0 safety page after the second two-column section."""
    ends = 0
    for idx, (kind, text) in enumerate(blocks):
        if kind == "layout" and text == "twocol_end":
            ends += 1
            if ends == 2:
                return blocks[:idx + 1], blocks[idx + 1:]
    return blocks, []
