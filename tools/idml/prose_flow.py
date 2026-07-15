"""Natural flow buffering for ordinary IDML prose pages."""
from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

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
        planned_starts = {
            Path(entry["source_path"]).stem: entry.get("latex_start_page")
            for entry in (page_plan or {}).get("pages", [])
        }
        batches: list[list[tuple[str, list[Block], int]]] = []
        for item in self.items:
            key = planned_starts.get(item[0]) if respect_page_plan else None
            dedicated_boundary = (
                item[0] in dedicated_stems
                or bool(batches and batches[-1][-1][0] in dedicated_stems)
            )
            if (not batches or dedicated_boundary
                    or (respect_page_plan and page_plan is not None
                        and planned_starts.get(batches[-1][0][0]) != key)):
                batches.append([])
            batches[-1].append(item)
        index = 0
        while estimate_pages and index + 1 < len(batches):
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


def align_operation_tail(blocks: list[Block], page_plan: dict | None,
                         stem: str) -> list[Block]:
    """Keep the final operation-guide section on its fourth reference page."""
    from .latex_page_plan import planned_span
    if "operation_guide" not in stem or planned_span(page_plan, [stem], 1) < 4:
        return blocks
    aligned = list(blocks)
    last_h2 = next((i for i in range(len(aligned) - 1, -1, -1)
                    if aligned[i][0] == "h2"), None)
    if last_h2 is not None:
        aligned.insert(last_h2, ("layout", "page_break"))
    return aligned


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
