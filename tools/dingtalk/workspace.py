from __future__ import annotations

from .contracts import DingTalkFileReference


def attach_file(*, file_ref: DingTalkFileReference, workspace_id: str, parent_node_id: str) -> str:
    raise NotImplementedError(
        "Phase 0 placeholder: implement workspace attach only if the chosen DingTalk doc product supports it."
    )
