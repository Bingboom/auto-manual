"""Storage section adapter that reuses the approved JE prose renderer."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..source_copy import source_text
from .fixed_panel_contract import normalize_language


@dataclass(frozen=True)
class StoragePanelData:
    title: str
    body_blocks: tuple[tuple[str, str], ...]

    @classmethod
    def from_blocks(
        cls,
        blocks: list[tuple[str, str]],
    ) -> "StoragePanelData":
        title = source_text(
            next((text for kind, text in blocks if kind == "h1"), ""),
            owner="Storage page title",
        )
        if not title:
            raise ValueError("storage_specifications requires a Storage H1")
        return cls(
            title=title,
            body_blocks=tuple(
                block for block in blocks if block[0] != "h1"
            ),
        )


@dataclass(frozen=True)
class StoragePanelContract:
    language: str
    renderer: str = "shared_prose"


@dataclass(frozen=True)
class StoragePanelRender:
    story_id: str
    contract: StoragePanelContract


class StoragePanel:
    """Render Storage through the exact prose/H1 path used by JE-1000F.

    The compact page composer owns only the outer story rectangle.  This
    adapter deliberately defines no fill, corner radius, inset, title-frame
    geometry, or model-specific paragraph treatment.
    """

    def __init__(
        self,
        writer,
        *,
        sid: str,
        data: StoragePanelData,
        bundle_root: Path,
        language: str,
    ) -> None:
        self.writer = writer
        self.sid = sid
        self.data = data
        self.bundle_root = bundle_root
        self.language = normalize_language(language)

    def render(self) -> StoragePanelRender:
        self.writer.add_prose_story(
            self.sid,
            self.data.title,
            [("h1", self.data.title), *self.data.body_blocks],
            self.bundle_root,
            language=self.language,
            disable_hyphenation=True,
        )
        return StoragePanelRender(
            story_id=self.sid,
            contract=StoragePanelContract(
                language=self.language,
            ),
        )


__all__ = [
    "StoragePanel",
    "StoragePanelContract",
    "StoragePanelData",
    "StoragePanelRender",
]
