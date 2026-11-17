"""知识库首页's own data: the note beside the asset cards and 正在做.

Since step 12 of the 2026-11 redesign (REV-51) the home page opens with the four asset layers (产品信息, 内容与表现,
视觉媒体, 语言) and the main line. Their figures, status chips and wording come from the layer views
(``tools/rtd/asset_pages.py``), the same ones the layer pages render, so no figure is read a second way here.

This module keeps what is the home page's own: the note beside the cards (``workspace_home.yaml``) and 正在做, which
is 系统建设's own list (``focus.doing`` in ``system_workspace.yaml``), so both pages say the same thing.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

HOME_COPY = "workspace_home.yaml"
SCHEMA = "hello-docs-workspace-home/v2"


def load_home_copy(assets: Path) -> dict[str, Any]:
    """The note beside the asset cards; a malformed file raises ValueError.

    A ``doing`` list here is refused: 正在做 is kept once, in 系统建设's contract, for both pages.
    """
    data = yaml.safe_load((assets / HOME_COPY).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError(f"{HOME_COPY}: schema must be {SCHEMA}")
    if "doing" in data:
        raise ValueError(f"{HOME_COPY}: 正在做 lives in system_workspace.yaml (focus.doing), not here")
    note = str(data.get("assets_note") or "").strip()
    if not note:
        raise ValueError(f"{HOME_COPY}: needs assets_note")
    return {"assets_note": note}


def now_view(system: dict[str, Any] | None, copy: dict[str, Any]) -> dict[str, Any]:
    """正在做 (from 系统建设, so the two pages agree) and the asset note (from the home copy).

    Without the 系统建设 page 正在做 does not show.
    """
    focus = (system or {}).get("focus") or {}
    doing = [{"lead": item["lead"], "text": item["text"]} for item in focus.get("doing") or []]
    return {"doing": doing, "assets_note": copy["assets_note"], "system": system is not None}
