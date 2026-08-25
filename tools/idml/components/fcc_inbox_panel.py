"""Public fixed-page FCC and Inbox composition boundary."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..params import param_pt
from .fcc_panel import FccPanel, FccPanelContract, FccPanelData
from .fixed_panel_contract import FixedPanelDensity, normalize_language
from .inbox_panel import InboxPanel, InboxPanelContract, InboxPanelData
from .symbols_panel import SymbolsPanel


@dataclass(frozen=True)
class FccInboxPanelData:
    fcc: FccPanelData
    inbox: InboxPanelData
    symbol_overflow: object | None = None

    @classmethod
    def from_blocks(
        cls,
        *,
        fcc_blocks: list[tuple[str, str]],
        inbox_blocks: list[tuple[str, str]],
        sid: str,
        language: str,
        density: FixedPanelDensity,
        symbol_overflow: object | None = None,
        reference_profile: dict | None = None,
    ) -> "FccInboxPanelData":
        inbox = InboxPanelData.from_blocks(
            inbox_blocks,
            sid=sid,
            language=language,
            density=density,
            reference_profile=reference_profile,
        )
        if density == "compact" and not inbox.has_inbox:
            raise ValueError(
                "shared FCC/inbox/overview composition requires inbox data"
            )
        return cls(
            fcc=FccPanelData.from_blocks(
                fcc_blocks,
                sid=sid,
                language=language,
            ),
            inbox=inbox,
            symbol_overflow=symbol_overflow,
        )


@dataclass(frozen=True)
class FccInboxPanelContract:
    density: FixedPanelDensity
    language: str
    fcc: FccPanelContract
    inbox: InboxPanelContract
    has_symbol_continuation: bool


@dataclass(frozen=True)
class FccInboxPanelRender:
    story_ids: tuple[str, ...]
    frames: tuple[str, ...]
    contract: FccInboxPanelContract


class FccInboxPanel:
    """Own the complete fixed-page stack; callers assign only its rectangle."""

    def __init__(
        self,
        writer,
        *,
        sid: str,
        data: FccInboxPanelData,
        bundle_root: Path,
        language: str,
        density: FixedPanelDensity,
    ) -> None:
        if density not in {"standard", "compact"}:
            raise ValueError(f"unsupported FCC/Inbox density: {density}")
        self.writer = writer
        self.sid = sid
        self.data = data
        self.bundle_root = bundle_root
        self.language = normalize_language(language)
        self.density = density

    def _standard_geometry(
        self,
        y: float,
    ) -> tuple[float, float, float, bool]:
        has_overflow = bool(
            self.data.symbol_overflow is not None
            and getattr(self.data.symbol_overflow, "has_rows")()
        )
        if has_overflow:
            fcc_offset = 98.0 if self.language == "es" else 95.0
            fcc_height = 148.0 if self.language == "es" else 145.0
            inbox_offset = param_pt(
                self.writer.params,
                f"lang_{self.language}_idml_fcc_inbox_overflow_title_y",
                param_pt(
                    self.writer.params,
                    "idml_fcc_inbox_overflow_title_y",
                    245.0,
                ),
            )
        else:
            fcc_offset = 28.0
            fcc_height = 130.0
            inbox_offset = 245.0
        return y + fcc_offset, fcc_height, y + inbox_offset, has_overflow

    def _compact_geometry(
        self,
        y: float,
    ) -> tuple[float, float, float]:
        baseline_y = param_pt(
            self.writer.params,
            "idml_shared_page_top",
            27.7,
        )
        fcc_height = param_pt(
            self.writer.params,
            "idml_compact_fcc_inbox_overview_fcc_height",
            116.0,
        )
        inbox_baseline = param_pt(
            self.writer.params,
            "idml_compact_inbox_title_y",
            baseline_y + fcc_height + 7.0,
        )
        return y, fcc_height, y + inbox_baseline - baseline_y

    def render(
        self,
        *,
        x: float,
        y: float,
        width: float,
        available_height: float,
    ) -> FccInboxPanelRender:
        fcc = FccPanel(
            self.writer,
            sid=self.sid,
            data=self.data.fcc,
            language=self.language,
            density=self.density,
        )
        inbox = InboxPanel(
            self.writer,
            sid=self.sid,
            data=self.data.inbox,
            bundle_root=self.bundle_root,
            language=self.language,
            density=self.density,
            overflow_profile=False,
        )
        symbol_story_ids: tuple[str, ...] = ()
        symbol_frames: tuple[str, ...] = ()
        if self.density == "standard":
            inbox.add_title_story()
            fcc_y, fcc_height, inbox_y, has_overflow = (
                self._standard_geometry(y)
            )
            inbox.overflow_profile = has_overflow
            if has_overflow:
                stories, frames = SymbolsPanel.render_continuation(
                    self.writer,
                    sid=self.sid,
                    overflow=self.data.symbol_overflow,
                    language=self.language,
                    density="standard",
                    x=x,
                    y=y + (25.0 if self.language == "es" else 20.0),
                    width=width,
                    available_height=68.0,
                )
                symbol_story_ids = tuple(stories)
                symbol_frames = tuple(frames)
        else:
            fcc_y, fcc_height, inbox_y = self._compact_geometry(y)
            has_overflow = False

        fcc_render = fcc.render(
            x=x,
            y=fcc_y,
            width=width,
            available_height=fcc_height,
        )
        inbox_render = inbox.render(
            x=x,
            y=inbox_y,
            width=width,
            available_height=max(0.0, available_height - (inbox_y - y)),
        )
        return FccInboxPanelRender(
            story_ids=(
                *symbol_story_ids,
                *fcc_render.story_ids,
                *inbox_render.story_ids,
            ),
            frames=(
                *symbol_frames,
                *fcc_render.frames,
                *inbox_render.frames,
            ),
            contract=FccInboxPanelContract(
                density=self.density,
                language=self.language,
                fcc=fcc_render.contract,
                inbox=inbox_render.contract,
                has_symbol_continuation=has_overflow,
            ),
        )


__all__ = [
    "FccInboxPanel",
    "FccInboxPanelContract",
    "FccInboxPanelData",
    "FccInboxPanelRender",
]
