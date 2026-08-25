"""V2.0 FCC + Inbox page composition."""
from __future__ import annotations

from pathlib import Path

from .components.fcc_inbox_panel import FccInboxPanel, FccInboxPanelData
from .params import IDPKG
from .symbols_page import SymbolOverflow


FIXED_PANEL_X = 26.5
FIXED_PANEL_WIDTH = 311.0


def _spread_page(writer, spread_id: str, page_no: int) -> str:
    return (
        f'  <Page Self="{spread_id}_pg" Name="{page_no}" '
        'AppliedMaster="n" OverrideList="" TabOrder="" '
        'GridStartingPoint="TopOutside" '
        f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
        f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} '
        f'{-writer.page_h / 2:g}">\n'
        '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
        f'Top="{writer.m_t:g}" Bottom="{writer.m_b:g}" '
        f'Left="{writer.m_l:g}" Right="{writer.m_r:g}"/>\n'
        '  </Page>\n'
    )


def add_fcc_inbox_page(
    writer,
    sid: str,
    fcc_blocks: list[tuple[str, str]],
    inbox_blocks: list[tuple[str, str]],
    bundle_root: Path,
    page_index: int,
    *,
    symbol_overflow: SymbolOverflow | None = None,
    lang: str = "en",
    reference_profile: dict | None = None,
) -> str:
    """Place the complete standard FCC/Inbox component on one page."""

    panel = FccInboxPanel(
        writer,
        sid=sid,
        data=FccInboxPanelData.from_blocks(
            fcc_blocks=fcc_blocks,
            inbox_blocks=inbox_blocks,
            sid=sid,
            language=lang,
            density="standard",
            symbol_overflow=symbol_overflow,
            reference_profile=reference_profile,
        ),
        bundle_root=bundle_root,
        language=lang,
        density="standard",
    ).render(
        x=FIXED_PANEL_X,
        y=0.0,
        width=FIXED_PANEL_WIDTH,
        available_height=writer.page_h,
    )

    spread_id = f"sp_{page_index}"
    page_no = page_index + 1
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" '
        'ShowMasterItems="true">\n'
        + _spread_page(writer, spread_id, page_no)
        + "".join(panel.frames)
        + '</Spread>\n'
        '</idPkg:Spread>\n'
    )
    writer.spreads.append((spread_id, xml))
    return spread_id


__all__ = ["add_fcc_inbox_page"]
