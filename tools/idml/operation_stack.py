"""Balanced vertical rhythm for dense operation image/callout stacks."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re

from .components.base import RenderContext
from .components.notice import notice_box_layout
from .params import param_pt
from .story_estimates import paragraph_estimate


@dataclass(frozen=True)
class OperationStackPlan:
    """One H2 + panel + callout/body/callout page rhythm group."""

    heading_index: int
    panel_index: int
    first_notice_index: int
    body_index: int
    second_notice_index: int
    gap: float


@dataclass(frozen=True)
class OperationTransitionPlan:
    """One visible gap owned by two adjacent semantic blocks."""

    before_index: int
    after_index: int
    gap: float
    owner_side: str = "after"


@dataclass(frozen=True)
class OperationCompensationPlan:
    """Keep a reference position while redistributing earlier whitespace."""

    start_index: int
    owner_index: int
    owner_side: str


@dataclass(frozen=True)
class OperationBlockSpacing:
    """Explicit story-level spacing overrides for one block."""

    space_before: float | None = None
    space_after: float | None = None


@dataclass(frozen=True)
class OperationSpacingPlan:
    """Shared transition gaps and their same-page compensation anchors."""

    gap: float
    transitions: tuple[OperationTransitionPlan, ...]
    compensations: tuple[OperationCompensationPlan, ...]

    def block_overrides(self) -> dict[int, OperationBlockSpacing]:
        """Convert semantic edges into paragraph-side spacing overrides."""
        values: dict[int, list[float | None]] = {}

        def set_side(index: int, side: int, value: float) -> None:
            current = values.setdefault(index, [None, None])[side]
            if current is not None and not math.isclose(current, value):
                raise ValueError(
                    f"conflicting operation spacing at block {index}: "
                    f"{current:g} vs {value:g}"
                )
            values[index][side] = value

        for transition in self.transitions:
            if transition.owner_side == "before":
                set_side(transition.before_index, 1, 0.0)
                set_side(transition.after_index, 0, transition.gap)
            elif transition.owner_side == "after":
                set_side(transition.before_index, 1, transition.gap)
                set_side(transition.after_index, 0, 0.0)
            else:
                raise ValueError(
                    "operation transition owner_side must be before or after"
                )
        for compensation in self.compensations:
            if compensation.owner_side == "before":
                # The compensation owner carries the complete visible gap;
                # clear the predecessor's legacy trailing fragment so the
                # result has one source of truth.
                set_side(compensation.owner_index - 1, 1, 0.0)
        return {
            index: OperationBlockSpacing(
                space_before=sides[0],
                space_after=sides[1],
            )
            for index, sides in values.items()
        }


@dataclass(frozen=True)
class AppliedOperationSpacing:
    """Result of applying a block override to its host paragraph."""

    xml: str
    old_total: float
    new_total: float

    @property
    def delta(self) -> float:
        return self.new_total - self.old_total


_PARAGRAPH_OPEN = re.compile(r"<ParagraphStyleRange(?P<attrs>[^>]*)>")
_SPACE_BEFORE = re.compile(r'\sSpaceBefore="(?P<value>[-+0-9.eE]+)"')
_SPACE_AFTER = re.compile(r'\sSpaceAfter="(?P<value>[-+0-9.eE]+)"')


def _space_value(pattern: re.Pattern[str], attrs: str) -> tuple[float, bool]:
    match = pattern.search(attrs)
    return (float(match.group("value")), True) if match else (0.0, False)


class OperationSpacingApplier:
    """Apply a structural plan while keeping compensation groups depth-neutral."""

    def __init__(self, plan: OperationSpacingPlan | None) -> None:
        self.plan = plan
        self.overrides = plan.block_overrides() if plan is not None else {}
        self._deltas = [0.0 for _item in (plan.compensations if plan else ())]
        self._completed: set[int] = set()

    def apply(self, index: int, xml: str) -> AppliedOperationSpacing:
        """Apply this block's before/after overrides to the first host PSR."""
        if self.plan is None:
            return AppliedOperationSpacing(xml, 0.0, 0.0)
        opening = _PARAGRAPH_OPEN.search(xml)
        if opening is None:
            return AppliedOperationSpacing(xml, 0.0, 0.0)

        attrs = opening.group("attrs")
        old_before, had_before = _space_value(_SPACE_BEFORE, attrs)
        old_after, had_after = _space_value(_SPACE_AFTER, attrs)
        override = self.overrides.get(index, OperationBlockSpacing())
        new_before = (
            old_before if override.space_before is None
            else override.space_before
        )
        new_after = (
            old_after if override.space_after is None
            else override.space_after
        )

        owner_compensations = [
            (position, compensation)
            for position, compensation in enumerate(self.plan.compensations)
            if compensation.owner_index == index
        ]
        for position, compensation in owner_compensations:
            if position in self._completed:
                raise RuntimeError("operation compensation was applied twice")
            provisional_delta = (
                new_before + new_after - old_before - old_after
            )
            correction = self._deltas[position] + provisional_delta
            if compensation.owner_side == "before":
                new_before -= correction
                had_before = True
            elif compensation.owner_side == "after":
                new_after -= correction
                had_after = True
            else:
                raise ValueError(
                    "operation compensation owner_side must be before or after"
                )

        emit_before = had_before or override.space_before is not None
        emit_after = had_after or override.space_after is not None
        stripped = _SPACE_AFTER.sub("", _SPACE_BEFORE.sub("", attrs))
        prefix = ""
        if emit_before:
            prefix += f' SpaceBefore="{new_before:g}"'
        if emit_after:
            prefix += f' SpaceAfter="{new_after:g}"'
        new_opening = f"<ParagraphStyleRange{prefix}{stripped}>"
        rendered = xml[:opening.start()] + new_opening + xml[opening.end():]

        result = AppliedOperationSpacing(
            rendered,
            old_before + old_after,
            new_before + new_after,
        )
        for position, compensation in enumerate(self.plan.compensations):
            if (
                position not in self._completed
                and compensation.start_index <= index <= compensation.owner_index
            ):
                self._deltas[position] += result.delta
                if index == compensation.owner_index:
                    if not math.isclose(self._deltas[position], 0.0, abs_tol=1e-7):
                        raise RuntimeError(
                            "operation spacing compensation did not preserve depth"
                        )
                    self._completed.add(position)
        return result

    def assert_complete(self) -> None:
        """Fail closed if a structural compensation owner was never rendered."""
        if self.plan is None:
            return
        expected = set(range(len(self.plan.compensations)))
        if self._completed != expected:
            raise RuntimeError("operation spacing compensation was not completed")


class OperationStorySpacing:
    """Keep Operation planning state out of the generic story emission loop."""

    def __init__(
        self,
        writer,
        blocks: list[tuple[str, str]],
        *,
        title: str,
        language: str | None,
        bundle_root,
        inline_origin_shift: float,
        text_measure: float,
    ) -> None:
        plan = operation_spacing_plan(
            blocks,
            title=title,
            language=language,
            params=writer.params,
            context=writer._render_context(
                bundle_root,
                language=language,
                inline_origin_shift=inline_origin_shift,
            ),
            frame_height=writer.frame_height(),
            body_width=text_measure,
        )
        self.writer = writer
        self.title = title
        self.language = language
        self.text_measure = text_measure
        self.applier = OperationSpacingApplier(plan)
        self.intro_lines: int | None = None
        self.energy_panel_height: float | None = None
        self.h2_seen = False

    def base_rhythm(
        self,
        kind: str,
        next_block: tuple[str, str],
        *,
        is_h2: bool,
    ) -> tuple[str | None, float | None]:
        """Return established paragraph rhythm before shared redistribution."""
        from .story_rhythm import operation_story_rhythm_for_next_block

        result = operation_story_rhythm_for_next_block(
            kind,
            next_block,
            self.language,
            title=self.title,
            intro_lines=self.intro_lines,
            energy_panel_height=self.energy_panel_height,
            baseline_panel_height=self.text_measure * 0.545 + 2.0,
            params=self.writer.params,
            first_operation_h2=(is_h2 and not self.h2_seen),
        )
        if is_h2:
            self.h2_seen = True
        return result

    def apply_component(
        self,
        index: int,
        spec: dict,
        xml: str,
        height: float,
    ) -> tuple[str, float]:
        """Apply host spacing and keep component estimates synchronized."""
        original_height = height
        if (
            str(spec.get("kind") or "").strip().lower() == "notice"
            and index in self.applier.overrides
        ):
            # Notice estimates historically reserve two generic table gaps
            # even though the host XML owns explicit spacing. Normalize to the
            # XML baseline before applying the shared transition delta.
            reserved = 2.0 * param_pt(
                self.writer.params,
                "comp_data_table_before",
                3.4,
            )
            panel_height = max(0.0, height - reserved)
            applied = self.applier.apply(index, xml)
            height = panel_height + applied.new_total
        else:
            applied = self.applier.apply(index, xml)
            height += applied.delta
        if str(spec.get("layout") or "").strip().lower() == "energy_saving":
            # LED compensation uses the original Energy carrier depth, before
            # the shared transition plan redistributes its whitespace.
            self.energy_panel_height = original_height
        return applied.xml, height

    def apply_block(self, index: int, xml: str, height: float) -> tuple[str, float]:
        """Apply shared spacing to a non-component figure/table host."""
        applied = self.applier.apply(index, xml)
        return applied.xml, height + applied.delta

    def apply_paragraph(
        self,
        index: int,
        paragraph: str,
        spacing: float | None,
    ) -> tuple[str, float | None]:
        """Apply shared spacing and return the matching estimate contribution."""
        applied = self.applier.apply(index, paragraph)
        if applied.delta:
            spacing = (spacing or 0.0) + applied.delta
        return applied.xml, spacing

    def record_estimate(self, kind: str, lines: int) -> None:
        if kind == "body_operation_energy_intro":
            self.intro_lines = lines

    def assert_complete(self) -> None:
        self.applier.assert_complete()


def _component_spec(block: tuple[str, str]) -> dict | None:
    kind, payload = block
    if kind != "component":
        return None
    try:
        spec = json.loads(payload)
    except (TypeError, json.JSONDecodeError):
        return None
    return spec if isinstance(spec, dict) else None


def _generic_panel_height(
    spec: dict,
    context: RenderContext,
    body_width: float,
) -> float | None:
    if str(spec.get("layout") or "").strip():
        return None
    ref = str(spec.get("image") or "").strip()
    asset = context.resolve_bundle_image(ref) if ref else None
    if asset is None or not asset.exists():
        return None
    _width, image_height = context.art_frame_size(
        asset,
        max_w=body_width * 0.945,
    )
    return image_height + 12.0


def _notice_height(spec: dict, params: dict, body_width: float) -> float:
    layout = notice_box_layout(
        params,
        body_width,
        str(spec.get("label") or ""),
        list(spec.get("texts") or []),
        variant=str(spec.get("variant") or ""),
        is_list=bool(spec.get("list")),
        body_horizontal_scale_override=spec.get("body_horizontal_scale"),
    )
    return layout.panel_height


def operation_stack_plans(
    blocks: list[tuple[str, str]],
    *,
    title: str,
    language: str | None,
    params: dict[str, tuple[str, str]],
    context: RenderContext,
    frame_height: float,
    body_width: float,
) -> tuple[OperationStackPlan, ...]:
    """Plan equal bounded gaps for operation panel/callout page stacks.

    The approved reference keeps the second callout near 84% of the usable
    text frame.  Localized copy changes the fixed content height, so the three
    inter-block gaps absorb the difference equally, bounded by shared design
    tokens.  Matching is structural and never depends on visible wording.
    """
    if "operation_guide" not in title:
        return ()

    minimum = param_pt(params, "idml_operation_stack_gap_min", 8.5)
    preferred = param_pt(params, "idml_operation_stack_gap_preferred", 11.34)
    maximum = param_pt(params, "idml_operation_stack_gap_max", 14.17)
    fill_ratio = param_pt(params, "idml_operation_stack_page_fill_ratio", 0.84)
    if not (0.0 <= minimum <= preferred <= maximum):
        raise ValueError(
            "operation stack gaps must satisfy 0 <= min <= preferred <= max"
        )
    if not (0.0 < fill_ratio <= 1.0):
        raise ValueError("operation stack page fill ratio must be in (0, 1]")

    plans: list[OperationStackPlan] = []
    normalized_language = (language or "en").split("-", 1)[0]
    for heading_index in range(len(blocks) - 4):
        panel_index = heading_index + 1
        first_notice_index = heading_index + 2
        body_index = heading_index + 3
        second_notice_index = heading_index + 4
        if blocks[heading_index][0] != "h2" or blocks[body_index][0] != "body":
            continue
        panel = _component_spec(blocks[panel_index])
        first_notice = _component_spec(blocks[first_notice_index])
        second_notice = _component_spec(blocks[second_notice_index])
        if (
            not panel
            or panel.get("kind") != "oppanel"
            or not first_notice
            or first_notice.get("kind") != "notice"
            or not second_notice
            or second_notice.get("kind") != "notice"
        ):
            continue
        panel_height = _generic_panel_height(panel, context, body_width)
        if panel_height is None:
            continue

        first_operation_h2 = not any(
            kind.startswith("h2") for kind, _payload in blocks[:heading_index]
        )
        heading_before = (
            param_pt(
                params,
                f"lang_{normalized_language}_idml_operation_first_h2_space_before",
                param_pt(params, "idml_operation_first_h2_space_before", 7.5),
            )
            if first_operation_h2
            else param_pt(params, "idml_title_l2_space_before", 5.67)
        )
        heading_after = param_pt(params, "idml_title_l2_space_after", 5.67)
        heading_height, _lines = paragraph_estimate(
            params,
            "h2",
            "h2",
            blocks[heading_index][1],
            body_width,
            is_preface=False,
            operation_spacing=heading_before + heading_after,
        )
        body_height, _lines = paragraph_estimate(
            params,
            "body",
            "body",
            blocks[body_index][1],
            body_width,
            is_preface=False,
            operation_spacing=None,
        )
        fixed_height = (
            heading_height
            + panel_height
            + _notice_height(first_notice, params, body_width)
            + body_height
            + _notice_height(second_notice, params, body_width)
        )
        candidate = (frame_height * fill_ratio - fixed_height) / 3.0
        if not math.isfinite(candidate):
            candidate = preferred
        gap = min(maximum, max(minimum, candidate))
        plans.append(OperationStackPlan(
            heading_index=heading_index,
            panel_index=panel_index,
            first_notice_index=first_notice_index,
            body_index=body_index,
            second_notice_index=second_notice_index,
            gap=gap,
        ))
    return tuple(plans)


def _is_operation_panel(
    block: tuple[str, str],
    *,
    layout: str | None = None,
) -> bool:
    spec = _component_spec(block)
    if spec is None or spec.get("kind") != "oppanel":
        return False
    if layout is None:
        return True
    return str(spec.get("layout") or "").strip().lower() == layout


def _is_notice(block: tuple[str, str]) -> bool:
    spec = _component_spec(block)
    return spec is not None and spec.get("kind") == "notice"


def operation_spacing_plan(
    blocks: list[tuple[str, str]],
    *,
    title: str,
    language: str | None,
    params: dict[str, tuple[str, str]],
    context: RenderContext,
    frame_height: float,
    body_width: float,
) -> OperationSpacingPlan | None:
    """Plan every governed Operation story transition from semantic structure.

    One dense panel/callout/body/callout stack establishes the bounded dynamic
    gap for the whole localized Operation story.  That same gap is reused for
    panel-to-body, panel-to-notice, notice-to-body, body-to-notice, and the
    Energy intro/panel/note stack.  H2-to-operation-panel remains a separate
    fixed title token.  Compensation groups reallocate existing whitespace on
    the same page so later approved panels do not move.
    """
    if "operation_guide" not in title:
        return None

    dense_stacks = operation_stack_plans(
        blocks,
        title=title,
        language=language,
        params=params,
        context=context,
        frame_height=frame_height,
        body_width=body_width,
    )
    minimum = param_pt(params, "idml_operation_stack_gap_min", 8.5)
    preferred = param_pt(params, "idml_operation_stack_gap_preferred", 11.34)
    maximum = param_pt(params, "idml_operation_stack_gap_max", 14.17)
    gap = dense_stacks[0].gap if dense_stacks else preferred
    gap = min(maximum, max(minimum, gap))
    heading_gap = param_pt(params, "idml_title_l2_space_after", 5.67)

    transitions: list[OperationTransitionPlan] = []
    compensations: list[OperationCompensationPlan] = []

    def add_transition(
        before_index: int,
        after_index: int,
        value: float,
        *,
        owner_side: str = "after",
    ) -> None:
        if after_index != before_index + 1:
            raise ValueError("operation transitions must join adjacent blocks")
        candidate = OperationTransitionPlan(
            before_index,
            after_index,
            value,
            owner_side,
        )
        if candidate not in transitions:
            transitions.append(candidate)

    # The title-to-panel rule is shared by ordinary and special LED panels.
    for index in range(len(blocks) - 1):
        if (
            blocks[index][0] in {"h2", "h2_operation_led"}
            and _is_operation_panel(blocks[index + 1])
        ):
            add_transition(index, index + 1, heading_gap)

    # First page: redistribute the panel/body gap inside the established
    # locale-specific inter-section budget; the second panel stays fixed.
    for index in range(len(blocks) - 4):
        if (
            blocks[index][0] == "h2"
            and _is_operation_panel(blocks[index + 1])
            and blocks[index + 2][0] == "body_operation_inter_section"
            and blocks[index + 3][0] == "h2"
            and _is_operation_panel(blocks[index + 4])
        ):
            add_transition(index + 1, index + 2, gap)
            compensations.append(OperationCompensationPlan(
                start_index=index,
                owner_index=index + 2,
                owner_side="after",
            ))

    # Dense panel/callout/body/callout page: all three content gaps are equal.
    for stack in dense_stacks:
        add_transition(stack.panel_index, stack.first_notice_index, gap)
        add_transition(stack.first_notice_index, stack.body_index, gap)
        add_transition(stack.body_index, stack.second_notice_index, gap)

    # Energy/LED page: the intro-to-panel and panel-to-note edges reuse the
    # same content gap.  The LED heading absorbs the equal-and-opposite delta,
    # including its 6.5pt-to-token title-after correction.
    for index in range(len(blocks) - 4):
        if (
            blocks[index][0] == "body_operation_energy_intro"
            and _is_operation_panel(blocks[index + 1], layout="energy_saving")
            and _is_notice(blocks[index + 2])
            and blocks[index + 3][0] == "h2_operation_led"
            and _is_operation_panel(blocks[index + 4], layout="led_light")
        ):
            add_transition(index, index + 1, gap)
            add_transition(index + 1, index + 2, gap)
            compensations.append(OperationCompensationPlan(
                start_index=index,
                owner_index=index + 3,
                owner_side="before",
            ))

    return OperationSpacingPlan(
        gap=gap,
        transitions=tuple(sorted(
            transitions,
            key=lambda item: (item.before_index, item.after_index),
        )),
        compensations=tuple(compensations),
    )
