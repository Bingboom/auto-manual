"""Natural flow buffering for ordinary IDML prose pages."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

Block = tuple[str, str]
EmitProse = Callable[[str, str, list[Block], int], None]
SlugStem = Callable[[str], str]


@dataclass
class ProseFlowBuffer:
    """Collect consecutive prose pages until a hard layout boundary appears."""

    items: list[tuple[str, list[Block], int]] = field(default_factory=list)

    def add(self, stem: str, blocks: list[Block], columns: int = 1) -> None:
        self.items.append((stem, blocks, columns))

    def flush(self, emit: EmitProse, slug_stem: SlugStem) -> bool:
        if not self.items:
            return False
        stems = [stem for stem, _, _ in self.items]
        columns = self.items[0][2]
        from . import oppanel as _oppanel
        blocks = _oppanel.transform(
            [block for _, page_blocks, _ in self.items for block in page_blocks])
        if len(stems) == 1:
            sid = "st_" + slug_stem(stems[0])
            title = stems[0]
        else:
            sid = "st_flow_" + slug_stem("_".join(stems[:2]))
            title = " + ".join(stems)
        emit(sid, title, blocks, columns)
        self.items.clear()
        return True


def split_safety_first_page(blocks: list[Block]) -> tuple[list[Block], list[Block]]:
    """Split the V2.0 safety page after the second two-column section."""
    ends = 0
    for idx, (kind, text) in enumerate(blocks):
        if kind == "layout" and text == "twocol_end":
            ends += 1
            if ends == 2:
                return blocks[:idx + 1], blocks[idx + 1:]
    return blocks, []
